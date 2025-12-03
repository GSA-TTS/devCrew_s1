"""
Build Engine for Container Platform

Comprehensive container image build system with BuildKit integration,
multi-platform support, and advanced caching strategies.

Features:
- BuildKit backend integration
- Multi-platform builds (amd64, arm64)
- Build cache management
- Secret injection
- Progress tracking
- Parallel builds
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import tarfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from docker import APIClient, DockerClient
from docker.errors import BuildError, DockerException


class BuildBackend(Enum):
    """Build backend types."""

    DOCKER = "docker"
    BUILDKIT = "buildkit"
    PODMAN = "podman"


class BuildStatus(Enum):
    """Build status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Platform(Enum):
    """Supported build platforms."""

    AMD64 = "linux/amd64"
    ARM64 = "linux/arm64"
    ARM_V7 = "linux/arm/v7"
    PPC64LE = "linux/ppc64le"
    S390X = "linux/s390x"


@dataclass
class BuildMetrics:
    """Build execution metrics."""

    build_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    total_layers: int = 0
    image_size_bytes: int = 0
    platform: str = ""
    status: BuildStatus = BuildStatus.PENDING
    error_message: str = ""


@dataclass
class BuildContext:
    """Build context configuration."""

    dockerfile_path: Path
    context_path: Path
    tags: List[str] = field(default_factory=list)
    platforms: List[Platform] = field(default_factory=lambda: [Platform.AMD64])
    build_args: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    target: Optional[str] = None
    cache_from: List[str] = field(default_factory=list)
    cache_to: Optional[str] = None
    no_cache: bool = False
    pull: bool = True
    rm: bool = True
    network_mode: Optional[str] = None
    extra_hosts: Dict[str, str] = field(default_factory=dict)
    isolation: Optional[str] = None
    ssh_keys: Dict[str, str] = field(default_factory=dict)


@dataclass
class BuildProgress:
    """Real-time build progress information."""

    build_id: str
    current_step: int
    total_steps: int
    current_layer: str
    status: str
    progress_percent: float = 0.0
    logs: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class BuildEngine:
    """
    Advanced container image build engine with BuildKit support.

    Provides comprehensive build capabilities including multi-platform builds,
    cache optimization, secret injection, and parallel build execution.
    """

    def __init__(
        self,
        backend: BuildBackend = BuildBackend.BUILDKIT,
        base_url: Optional[str] = None,
        timeout: int = 600,
        max_parallel_builds: int = 4,
    ):
        """
        Initialize the build engine.

        Args:
            backend: Build backend to use
            base_url: Docker daemon socket URL
            timeout: Build timeout in seconds
            max_parallel_builds: Maximum concurrent builds
        """
        self.logger = logging.getLogger(__name__)
        self.backend = backend
        self.timeout = timeout
        self.max_parallel_builds = max_parallel_builds

        # Initialize Docker clients
        try:
            self.client = DockerClient(base_url=base_url)
            self.api_client = APIClient(base_url=base_url)
        except DockerException as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise

        # Build tracking
        self.active_builds: Dict[str, BuildMetrics] = {}
        self.build_history: List[BuildMetrics] = []
        self.build_semaphore = asyncio.Semaphore(max_parallel_builds)

        # BuildKit configuration
        self._setup_buildkit()

    def _setup_buildkit(self) -> None:
        """Configure BuildKit backend."""
        if self.backend == BuildBackend.BUILDKIT:
            # Enable BuildKit via environment variable
            os.environ["DOCKER_BUILDKIT"] = "1"

            # Check BuildKit availability
            try:
                info = self.client.info()
                if not info.get("BuilderVersion", "").startswith("BuildKit"):
                    self.logger.warning(
                        "BuildKit not detected, falling back to legacy builder"
                    )
                    self.backend = BuildBackend.DOCKER
            except Exception as e:
                self.logger.warning(f"BuildKit check failed: {e}")

    def build(
        self,
        context: BuildContext,
        progress_callback: Optional[Callable[[BuildProgress], None]] = None,
    ) -> Tuple[str, BuildMetrics]:
        """
        Build a container image.

        Args:
            context: Build context configuration
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (image_id, build_metrics)

        Raises:
            BuildError: If build fails
        """
        build_id = self._generate_build_id(context)
        metrics = BuildMetrics(
            build_id=build_id,
            start_time=datetime.now(),
            status=BuildStatus.RUNNING,
        )
        self.active_builds[build_id] = metrics

        try:
            self.logger.info(f"Starting build {build_id}")

            # Prepare build context
            build_context_tar = self._prepare_build_context(context)

            # Build for each platform
            if len(context.platforms) > 1:
                image_id = self._build_multiplatform(
                    context, build_context_tar, metrics, progress_callback
                )
            else:
                image_id = self._build_single_platform(
                    context,
                    build_context_tar,
                    context.platforms[0],
                    metrics,
                    progress_callback,
                )

            # Update metrics
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()
            metrics.status = BuildStatus.SUCCESS

            # Get image size
            try:
                image_info = self.client.images.get(image_id)
                metrics.image_size_bytes = image_info.attrs.get("Size", 0)
            except Exception as e:
                self.logger.warning(f"Failed to get image size: {e}")

            self.logger.info(
                f"Build {build_id} completed in " f"{metrics.duration_seconds:.2f}s"
            )

            return image_id, metrics

        except Exception as e:
            metrics.status = BuildStatus.FAILED
            metrics.error_message = str(e)
            metrics.end_time = datetime.now()
            self.logger.error(f"Build {build_id} failed: {e}")
            raise

        finally:
            # Clean up
            self.build_history.append(metrics)
            if build_id in self.active_builds:
                del self.active_builds[build_id]

    def _build_single_platform(
        self,
        context: BuildContext,
        build_context_tar: BytesIO,
        platform: Platform,
        metrics: BuildMetrics,
        progress_callback: Optional[Callable[[BuildProgress], None]] = None,
    ) -> str:
        """
        Build image for a single platform.

        Args:
            context: Build context
            build_context_tar: Prepared build context tarball
            platform: Target platform
            metrics: Build metrics to update
            progress_callback: Progress callback

        Returns:
            Image ID
        """
        metrics.platform = platform.value

        # Prepare build arguments
        buildargs = context.build_args.copy()

        # BuildKit-specific options
        if self.backend == BuildBackend.BUILDKIT:
            build_options = self._prepare_buildkit_options(context, platform)
        else:
            build_options = {}

        # Execute build
        dockerfile_path = str(context.dockerfile_path.relative_to(context.context_path))

        try:
            response = self.api_client.build(
                fileobj=build_context_tar,
                custom_context=True,
                encoding="gzip",
                tag=context.tags[0] if context.tags else None,
                dockerfile=dockerfile_path,
                buildargs=buildargs,
                nocache=context.no_cache,
                pull=context.pull,
                rm=context.rm,
                target=context.target,
                platform=platform.value,
                network_mode=context.network_mode,
                extra_hosts=context.extra_hosts,
                labels=context.labels,
                **build_options,
            )

            # Process build output
            image_id = self._process_build_output(response, metrics, progress_callback)

            # Tag additional tags
            for tag in context.tags[1:]:
                self.client.images.get(image_id).tag(tag)

            return image_id

        except BuildError as e:
            self.logger.error(f"Build failed: {e}")
            raise

    def _build_multiplatform(
        self,
        context: BuildContext,
        build_context_tar: BytesIO,
        metrics: BuildMetrics,
        progress_callback: Optional[Callable[[BuildProgress], None]] = None,
    ) -> str:
        """
        Build image for multiple platforms using BuildKit.

        Args:
            context: Build context
            build_context_tar: Prepared build context tarball
            metrics: Build metrics
            progress_callback: Progress callback

        Returns:
            Manifest list ID
        """
        if self.backend != BuildBackend.BUILDKIT:
            raise ValueError("Multi-platform builds require BuildKit")

        metrics.platform = ",".join(p.value for p in context.platforms)

        # Use docker buildx for multi-platform builds
        # This requires buildx CLI integration
        self.logger.info(
            f"Building for platforms: "
            f"{', '.join(p.value for p in context.platforms)}"
        )

        # For now, build each platform separately and create manifest
        image_ids = []
        for platform in context.platforms:
            build_context_tar.seek(0)
            image_id = self._build_single_platform(
                context,
                build_context_tar,
                platform,
                metrics,
                progress_callback,
            )
            image_ids.append(image_id)

        # Return first image ID (manifest creation would be done separately)
        return image_ids[0]

    def _prepare_build_context(self, context: BuildContext) -> BytesIO:
        """
        Prepare build context as tarball.

        Args:
            context: Build context

        Returns:
            BytesIO containing context tarball
        """
        self.logger.debug(f"Preparing build context from {context.context_path}")

        # Read .dockerignore if exists
        dockerignore_path = context.context_path / ".dockerignore"
        exclude_patterns = []
        if dockerignore_path.exists():
            with open(dockerignore_path, "r", encoding="utf-8") as f:
                exclude_patterns = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

        # Create tarball
        context_tar = BytesIO()
        with tarfile.open(fileobj=context_tar, mode="w:gz") as tar:
            for root, dirs, files in os.walk(context.context_path):
                # Filter out excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._should_exclude(
                        Path(root) / d, context.context_path, exclude_patterns
                    )
                ]

                for file in files:
                    file_path = Path(root) / file
                    if not self._should_exclude(
                        file_path, context.context_path, exclude_patterns
                    ):
                        arcname = file_path.relative_to(context.context_path)
                        tar.add(file_path, arcname=arcname)

        context_tar.seek(0)
        return context_tar

    def _should_exclude(self, path: Path, base_path: Path, patterns: List[str]) -> bool:
        """
        Check if path should be excluded based on .dockerignore patterns.

        Args:
            path: Path to check
            base_path: Base context path
            patterns: Exclusion patterns

        Returns:
            True if path should be excluded
        """
        try:
            rel_path = path.relative_to(base_path)
        except ValueError:
            return False

        rel_path_str = str(rel_path)

        for pattern in patterns:
            # Convert dockerignore pattern to regex
            pattern = pattern.strip()
            if not pattern or pattern.startswith("#"):
                continue

            # Handle negation
            if pattern.startswith("!"):
                continue

            # Convert to regex
            regex_pattern = pattern.replace(".", r"\.")
            regex_pattern = regex_pattern.replace("*", ".*")
            regex_pattern = regex_pattern.replace("?", ".")

            if re.match(f"^{regex_pattern}$", rel_path_str):
                return True

        return False

    def _prepare_buildkit_options(
        self, context: BuildContext, platform: Platform
    ) -> Dict[str, Any]:
        """
        Prepare BuildKit-specific build options.

        Args:
            context: Build context
            platform: Target platform

        Returns:
            BuildKit options dictionary
        """
        options: Dict[str, Any] = {}

        # Cache configuration
        if context.cache_from:
            options["cache_from"] = context.cache_from

        if context.cache_to:
            options["cache_to"] = context.cache_to

        # Secrets
        if context.secrets and self.backend == BuildBackend.BUILDKIT:
            # BuildKit secrets need to be passed as build args
            # In production, use BuildKit secret mounts
            for secret_id, secret_value in context.secrets.items():
                options.setdefault("buildargs", {})[
                    f"SECRET_{secret_id.upper()}"
                ] = secret_value

        # SSH keys
        if context.ssh_keys:
            # BuildKit SSH forwarding
            options["ssh"] = list(context.ssh_keys.keys())

        return options

    def _process_build_output(
        self,
        response: Any,
        metrics: BuildMetrics,
        progress_callback: Optional[Callable[[BuildProgress], None]] = None,
    ) -> str:
        """
        Process build output stream and extract image ID.

        Args:
            response: Build response stream
            metrics: Metrics to update
            progress_callback: Progress callback

        Returns:
            Built image ID
        """
        image_id = None
        current_step = 0
        total_steps = 0

        for line in response:
            try:
                if isinstance(line, bytes):
                    line = line.decode("utf-8")

                data = json.loads(line)

                # Extract step information
                if "stream" in data:
                    stream = data["stream"].strip()
                    if stream:
                        self.logger.debug(stream)

                        # Parse step information
                        if stream.startswith("Step "):
                            match = re.match(r"Step (\d+)/(\d+)", stream)
                            if match:
                                current_step = int(match.group(1))
                                total_steps = int(match.group(2))
                                metrics.total_layers = total_steps

                        # Track cache usage
                        if "Using cache" in stream:
                            metrics.cache_hits += 1
                        elif (
                            "Running in" in stream or "Removing intermediate" in stream
                        ):
                            metrics.cache_misses += 1

                        # Progress callback
                        if progress_callback and total_steps > 0:
                            progress = BuildProgress(
                                build_id=metrics.build_id,
                                current_step=current_step,
                                total_steps=total_steps,
                                current_layer=stream,
                                status="building",
                                progress_percent=(current_step / total_steps) * 100,
                            )
                            progress_callback(progress)

                # Extract image ID
                if "aux" in data and "ID" in data["aux"]:
                    image_id = data["aux"]["ID"]

                # Check for errors
                if "error" in data:
                    raise BuildError(data["error"], None)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing build output: {e}")
                raise

        if not image_id:
            raise BuildError("Failed to extract image ID from build output", None)

        return image_id

    def _generate_build_id(self, context: BuildContext) -> str:
        """
        Generate unique build ID.

        Args:
            context: Build context

        Returns:
            Build ID
        """
        content = (
            f"{context.dockerfile_path}"
            f"{context.context_path}"
            f"{','.join(context.tags)}"
            f"{time.time()}"
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def build_async(
        self,
        context: BuildContext,
        progress_callback: Optional[Callable[[BuildProgress], None]] = None,
    ) -> Tuple[str, BuildMetrics]:
        """
        Build image asynchronously.

        Args:
            context: Build context
            progress_callback: Progress callback

        Returns:
            Tuple of (image_id, metrics)
        """
        async with self.build_semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.build, context, progress_callback
            )

    async def build_batch(
        self,
        contexts: List[BuildContext],
        progress_callback: Optional[Callable[[BuildProgress], None]] = None,
    ) -> List[Tuple[str, BuildMetrics]]:
        """
        Build multiple images in parallel.

        Args:
            contexts: List of build contexts
            progress_callback: Progress callback

        Returns:
            List of (image_id, metrics) tuples
        """
        self.logger.info(f"Starting batch build of {len(contexts)} images")

        tasks = [self.build_async(context, progress_callback) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_builds: List[Tuple[str, BuildMetrics]] = []
        failed_builds = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Build {i} failed: {result}")
                failed_builds.append((contexts[i], result))
            else:
                # Type assertion since we know non-exception results match
                successful_builds.append(result)  # type: ignore[arg-type]

        self.logger.info(
            f"Batch build completed: "
            f"{len(successful_builds)} succeeded, "
            f"{len(failed_builds)} failed"
        )

        return successful_builds

    def prune_build_cache(
        self,
        all_cache: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prune build cache.

        Args:
            all_cache: Remove all cache, not just dangling
            filters: Filters to apply

        Returns:
            Prune results
        """
        self.logger.info("Pruning build cache")

        try:
            result = self.client.api.prune_builds(filters=filters)

            space_reclaimed = result.get("SpaceReclaimed", 0)
            self.logger.info(
                f"Reclaimed {space_reclaimed / (1024**3):.2f} GB " f"of build cache"
            )

            return result

        except Exception as e:
            self.logger.error(f"Failed to prune build cache: {e}")
            raise

    def get_build_history(self, limit: Optional[int] = None) -> List[BuildMetrics]:
        """
        Get build history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of build metrics
        """
        history = sorted(self.build_history, key=lambda x: x.start_time, reverse=True)

        if limit:
            return history[:limit]

        return history

    def get_active_builds(self) -> List[BuildMetrics]:
        """
        Get currently active builds.

        Returns:
            List of active build metrics
        """
        return list(self.active_builds.values())

    def cancel_build(self, build_id: str) -> bool:
        """
        Cancel an active build.

        Args:
            build_id: Build ID to cancel

        Returns:
            True if cancelled successfully
        """
        if build_id not in self.active_builds:
            self.logger.warning(f"Build {build_id} not found in active builds")
            return False

        # Note: Docker doesn't provide a direct way to cancel builds
        # This would require additional implementation
        self.logger.warning("Build cancellation not fully implemented")

        metrics = self.active_builds[build_id]
        metrics.status = BuildStatus.CANCELLED
        metrics.end_time = datetime.now()

        return True

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get build cache statistics.

        Returns:
            Cache statistics
        """
        total_builds = len(self.build_history)
        if total_builds == 0:
            return {
                "total_builds": 0,
                "total_cache_hits": 0,
                "total_cache_misses": 0,
                "cache_hit_rate": 0.0,
            }

        total_hits = sum(m.cache_hits for m in self.build_history)
        total_misses = sum(m.cache_misses for m in self.build_history)
        total_requests = total_hits + total_misses

        cache_hit_rate = (
            (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        )

        return {
            "total_builds": total_builds,
            "total_cache_hits": total_hits,
            "total_cache_misses": total_misses,
            "cache_hit_rate": cache_hit_rate,
            "average_build_time": sum(m.duration_seconds for m in self.build_history)
            / total_builds,
        }

    def export_build_context(self, context: BuildContext, output_path: Path) -> None:
        """
        Export build context to tarball for inspection.

        Args:
            context: Build context
            output_path: Output tarball path
        """
        self.logger.info(f"Exporting build context to {output_path}")

        context_tar = self._prepare_build_context(context)

        with open(output_path, "wb") as f:
            f.write(context_tar.getvalue())

        self.logger.info(f"Build context exported to {output_path}")

    def validate_dockerfile(self, dockerfile_path: Path) -> List[str]:
        """
        Validate Dockerfile syntax.

        Args:
            dockerfile_path: Path to Dockerfile

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            with open(dockerfile_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Check for common issues
                if line.startswith("FROM") and i > 1:
                    # Check if there's a valid stage name
                    if " as " not in line.lower():
                        errors.append(f"Line {i}: Multi-stage FROM without 'AS' name")

                if line.startswith("COPY") or line.startswith("ADD"):
                    if ".." in line:
                        errors.append(
                            f"Line {i}: Suspicious parent directory reference"
                        )

                if line.startswith("RUN") and "sudo" in line:
                    errors.append(
                        f"Line {i}: Use of 'sudo' in RUN command (unnecessary)"
                    )

        except Exception as e:
            errors.append(f"Failed to read Dockerfile: {e}")

        return errors

    def close(self) -> None:
        """Close Docker client connections."""
        try:
            self.client.close()
        except Exception as e:
            self.logger.error(f"Error closing Docker client: {e}")
