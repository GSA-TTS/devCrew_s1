"""
Unit tests for Build Engine module.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from build_engine import (
    BuildBackend,
    BuildContext,
    BuildEngine,
    BuildMetrics,
    BuildStatus,
    Platform,
)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client."""
    with patch("build_engine.DockerClient") as mock_client, patch(
        "build_engine.APIClient"
    ) as mock_api_client:
        mock_instance = Mock()
        mock_api_instance = Mock()

        mock_client.return_value = mock_instance
        mock_api_client.return_value = mock_api_instance

        mock_instance.info.return_value = {"BuilderVersion": "BuildKit 0.11.0"}
        mock_instance.images.get.return_value = Mock(attrs={"Size": 1024 * 1024 * 100})

        yield mock_instance, mock_api_instance


@pytest.fixture
def build_engine(mock_docker_client):
    """Create build engine instance."""
    return BuildEngine(backend=BuildBackend.BUILDKIT)


@pytest.fixture
def temp_build_context():
    """Create temporary build context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        context_path = Path(tmpdir)

        # Create a simple Dockerfile
        dockerfile = context_path / "Dockerfile"
        dockerfile.write_text(
            """
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
"""
        )

        # Create additional files
        (context_path / "requirements.txt").write_text("flask==3.0.0\n")
        (context_path / "app.py").write_text('print("Hello World")\n')

        # Create .dockerignore
        (context_path / ".dockerignore").write_text(
            """
__pycache__
*.pyc
.git
.env
"""
        )

        yield context_path


class TestBuildEngine:
    """Test BuildEngine class."""

    def test_initialization(self, mock_docker_client):
        """Test engine initialization."""
        engine = BuildEngine(backend=BuildBackend.BUILDKIT)

        assert engine.backend == BuildBackend.BUILDKIT
        assert engine.timeout == 600
        assert engine.max_parallel_builds == 4
        assert len(engine.active_builds) == 0

    def test_buildkit_setup(self, mock_docker_client):
        """Test BuildKit setup."""
        engine = BuildEngine(backend=BuildBackend.BUILDKIT)

        assert engine.backend == BuildBackend.BUILDKIT

    def test_prepare_build_context(self, build_engine, temp_build_context):
        """Test build context preparation."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
            tags=["test:latest"],
        )

        context_tar = build_engine._prepare_build_context(context)

        assert context_tar is not None
        assert context_tar.tell() > 0

    def test_dockerignore_exclusion(self, build_engine, temp_build_context):
        """Test .dockerignore pattern matching."""
        # Create files that should be excluded
        (temp_build_context / "__pycache__").mkdir()
        (temp_build_context / "__pycache__" / "test.pyc").touch()
        (temp_build_context / ".git").mkdir()
        (temp_build_context / ".git" / "config").touch()

        patterns = ["__pycache__", "*.pyc", ".git", ".env"]

        # Test exclusions
        assert build_engine._should_exclude(
            temp_build_context / "__pycache__", temp_build_context, patterns
        )
        assert build_engine._should_exclude(
            temp_build_context / "test.pyc", temp_build_context, patterns
        )
        assert build_engine._should_exclude(
            temp_build_context / ".git", temp_build_context, patterns
        )
        assert not build_engine._should_exclude(
            temp_build_context / "app.py", temp_build_context, patterns
        )

    def test_generate_build_id(self, build_engine, temp_build_context):
        """Test build ID generation."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
            tags=["test:latest"],
        )

        build_id = build_engine._generate_build_id(context)

        assert isinstance(build_id, str)
        assert len(build_id) == 16

    def test_validate_dockerfile(self, build_engine, temp_build_context):
        """Test Dockerfile validation."""
        dockerfile_path = temp_build_context / "Dockerfile"

        errors = build_engine.validate_dockerfile(dockerfile_path)

        # Valid Dockerfile should have no errors
        assert len(errors) == 0

    def test_validate_dockerfile_with_issues(self, build_engine, temp_build_context):
        """Test Dockerfile validation with issues."""
        bad_dockerfile = temp_build_context / "Dockerfile.bad"
        bad_dockerfile.write_text(
            """
FROM ubuntu:22.04
RUN sudo apt-get update
COPY ../.env /app/.env
"""
        )

        errors = build_engine.validate_dockerfile(bad_dockerfile)

        assert len(errors) > 0
        assert any("sudo" in error for error in errors)
        assert any(".." in error for error in errors)

    @patch("build_engine.BuildEngine._build_single_platform")
    def test_build_single_platform(self, mock_build, build_engine, temp_build_context):
        """Test single platform build."""
        mock_build.return_value = "sha256:test123"

        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
            tags=["test:latest"],
            platforms=[Platform.AMD64],
        )

        # Mock the build process
        with patch.object(build_engine, "_prepare_build_context") as mock_prepare:
            mock_prepare.return_value = Mock()
            image_id, metrics = build_engine.build(context)

            assert image_id == "sha256:test123"
            assert metrics.status == BuildStatus.SUCCESS

    def test_prepare_buildkit_options(self, build_engine, temp_build_context):
        """Test BuildKit options preparation."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
            cache_from=["type=registry,ref=myrepo/cache"],
            secrets={"github_token": "ghp_test123"},
            ssh_keys={"default": "/root/.ssh/id_rsa"},
        )

        options = build_engine._prepare_buildkit_options(context, Platform.AMD64)

        assert "cache_from" in options
        assert options["cache_from"] == ["type=registry,ref=myrepo/cache"]
        assert "ssh" in options

    def test_get_cache_stats(self, build_engine):
        """Test cache statistics."""
        # Add some metrics
        for i in range(5):
            metrics = BuildMetrics(
                build_id=f"build_{i}",
                start_time=pytest.approx,
                cache_hits=10,
                cache_misses=5,
                duration_seconds=30.0,
            )
            build_engine.build_history.append(metrics)

        stats = build_engine.get_cache_stats()

        assert stats["total_builds"] == 5
        assert stats["total_cache_hits"] == 50
        assert stats["total_cache_misses"] == 25
        assert stats["cache_hit_rate"] > 0

    def test_prune_build_cache(self, build_engine):
        """Test cache pruning."""
        mock_result = {"SpaceReclaimed": 1024 * 1024 * 1024}

        with patch.object(
            build_engine.client.api, "prune_builds", return_value=mock_result
        ):
            result = build_engine.prune_build_cache()

            assert result["SpaceReclaimed"] == 1024 * 1024 * 1024

    def test_get_build_history(self, build_engine):
        """Test build history retrieval."""
        # Add some builds
        for i in range(10):
            metrics = BuildMetrics(build_id=f"build_{i}", start_time=pytest.approx)
            build_engine.build_history.append(metrics)

        # Get all history
        history = build_engine.get_build_history()
        assert len(history) == 10

        # Get limited history
        history = build_engine.get_build_history(limit=5)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_build_async(self, build_engine, temp_build_context):
        """Test asynchronous build."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
            tags=["test:latest"],
        )

        with patch.object(build_engine, "build") as mock_build:
            mock_build.return_value = (
                "sha256:test123",
                BuildMetrics(build_id="test", start_time=pytest.approx),
            )

            image_id, metrics = await build_engine.build_async(context)

            assert image_id == "sha256:test123"
            mock_build.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_batch(self, build_engine, temp_build_context):
        """Test batch parallel builds."""
        contexts = [
            BuildContext(
                dockerfile_path=temp_build_context / "Dockerfile",
                context_path=temp_build_context,
                tags=[f"test:v{i}"],
            )
            for i in range(3)
        ]

        with patch.object(build_engine, "build") as mock_build:
            mock_build.return_value = (
                "sha256:test123",
                BuildMetrics(build_id="test", start_time=pytest.approx),
            )

            results = await build_engine.build_batch(contexts)

            assert len(results) == 3
            assert mock_build.call_count == 3

    def test_export_build_context(self, build_engine, temp_build_context):
        """Test build context export."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
        )

        output_path = temp_build_context / "context.tar.gz"

        build_engine.export_build_context(context, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_cancel_build(self, build_engine):
        """Test build cancellation."""
        # Add an active build
        metrics = BuildMetrics(
            build_id="test_build",
            start_time=pytest.approx,
            status=BuildStatus.RUNNING,
        )
        build_engine.active_builds["test_build"] = metrics

        result = build_engine.cancel_build("test_build")

        assert result is True
        assert metrics.status == BuildStatus.CANCELLED

    def test_get_active_builds(self, build_engine):
        """Test getting active builds."""
        # Add some active builds
        for i in range(3):
            metrics = BuildMetrics(
                build_id=f"build_{i}",
                start_time=pytest.approx,
                status=BuildStatus.RUNNING,
            )
            build_engine.active_builds[f"build_{i}"] = metrics

        active = build_engine.get_active_builds()

        assert len(active) == 3


class TestBuildContext:
    """Test BuildContext dataclass."""

    def test_build_context_creation(self, temp_build_context):
        """Test BuildContext initialization."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
            tags=["test:latest", "test:v1.0"],
            platforms=[Platform.AMD64, Platform.ARM64],
            build_args={"VERSION": "1.0.0", "ENV": "production"},
            labels={"maintainer": "devops@example.com"},
        )

        assert context.dockerfile_path == temp_build_context / "Dockerfile"
        assert len(context.tags) == 2
        assert len(context.platforms) == 2
        assert context.build_args["VERSION"] == "1.0.0"

    def test_default_values(self, temp_build_context):
        """Test default values."""
        context = BuildContext(
            dockerfile_path=temp_build_context / "Dockerfile",
            context_path=temp_build_context,
        )

        assert len(context.tags) == 0
        assert len(context.platforms) == 1
        assert context.platforms[0] == Platform.AMD64
        assert context.pull is True
        assert context.rm is True
        assert context.no_cache is False


class TestBuildMetrics:
    """Test BuildMetrics dataclass."""

    def test_metrics_creation(self):
        """Test metrics initialization."""
        metrics = BuildMetrics(
            build_id="test123",
            start_time=pytest.approx,
        )

        assert metrics.build_id == "test123"
        assert metrics.status == BuildStatus.PENDING
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_metrics_update(self):
        """Test metrics updates."""
        metrics = BuildMetrics(
            build_id="test123",
            start_time=pytest.approx,
        )

        metrics.status = BuildStatus.SUCCESS
        metrics.cache_hits = 10
        metrics.total_layers = 15

        assert metrics.status == BuildStatus.SUCCESS
        assert metrics.cache_hits == 10
        assert metrics.total_layers == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
