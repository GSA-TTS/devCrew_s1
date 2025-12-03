"""
Example usage of Build Engine module.

Demonstrates various build scenarios and configurations.
"""

import asyncio
import logging
from pathlib import Path

from build_engine import (
    BuildBackend,
    BuildContext,
    BuildEngine,
    BuildProgress,
    Platform,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def progress_callback(progress: BuildProgress) -> None:
    """Handle build progress updates."""
    print(
        f"[{progress.build_id[:8]}] Step {progress.current_step}/"
        f"{progress.total_steps} ({progress.progress_percent:.1f}%): "
        f"{progress.current_layer[:60]}"
    )


def example_basic_build():
    """Example: Basic single-platform build."""
    print("\n=== Example 1: Basic Build ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile"),
        context_path=Path("./examples/app"),
        tags=["myapp:latest", "myapp:v1.0.0"],
        build_args={
            "PYTHON_VERSION": "3.11",
            "APP_ENV": "production",
        },
        labels={
            "maintainer": "devops@example.com",
            "version": "1.0.0",
            "description": "Production application",
        },
    )

    try:
        image_id, metrics = engine.build(context, progress_callback=progress_callback)

        print(f"\n✓ Build completed successfully!")
        print(f"  Image ID: {image_id}")
        print(f"  Duration: {metrics.duration_seconds:.2f}s")
        print(f"  Cache hits: {metrics.cache_hits}")
        print(f"  Cache misses: {metrics.cache_misses}")
        print(f"  Image size: {metrics.image_size_bytes / (1024**2):.2f} MB")

    finally:
        engine.close()


def example_multiplatform_build():
    """Example: Multi-platform build for amd64 and arm64."""
    print("\n=== Example 2: Multi-Platform Build ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile"),
        context_path=Path("./examples/app"),
        tags=["myapp:latest-multiarch"],
        platforms=[Platform.AMD64, Platform.ARM64],
        build_args={"TARGETPLATFORM": "linux/amd64,linux/arm64"},
    )

    try:
        image_id, metrics = engine.build(context, progress_callback=progress_callback)

        print(f"\n✓ Multi-platform build completed!")
        print(f"  Platforms: {metrics.platform}")
        print(f"  Duration: {metrics.duration_seconds:.2f}s")

    finally:
        engine.close()


def example_cached_build():
    """Example: Build with cache configuration."""
    print("\n=== Example 3: Cached Build ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile"),
        context_path=Path("./examples/app"),
        tags=["myapp:cached"],
        cache_from=[
            "type=registry,ref=myregistry.io/myapp:buildcache",
            "type=local,src=/tmp/buildkit-cache",
        ],
        cache_to="type=local,dest=/tmp/buildkit-cache,mode=max",
        pull=True,  # Pull base images to get latest
    )

    try:
        image_id, metrics = engine.build(context, progress_callback=progress_callback)

        print(f"\n✓ Cached build completed!")
        print(
            f"  Cache hit rate: "
            f"{metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100:.1f}%"
        )

    finally:
        engine.close()


def example_secret_injection():
    """Example: Build with secrets (API tokens, SSH keys)."""
    print("\n=== Example 4: Build with Secrets ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile.secure"),
        context_path=Path("./examples/app"),
        tags=["myapp:secure"],
        secrets={
            "github_token": "ghp_xxxxxxxxxxxx",
            "npm_token": "npm_xxxxxxxxxxxx",
        },
        ssh_keys={
            "default": str(Path.home() / ".ssh/id_rsa"),
        },
        build_args={
            "USE_PRIVATE_REPOS": "true",
        },
    )

    try:
        image_id, metrics = engine.build(context)

        print(f"\n✓ Secure build completed!")
        print(f"  Image ID: {image_id}")
        print("  Secrets were injected securely (not in image layers)")

    finally:
        engine.close()


def example_multistage_optimized():
    """Example: Multi-stage build with optimization."""
    print("\n=== Example 5: Multi-Stage Optimized Build ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    # Build only the production stage
    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile.multistage"),
        context_path=Path("./examples/app"),
        tags=["myapp:optimized"],
        target="production",  # Build only production stage
        build_args={
            "BUILD_ENV": "production",
            "OPTIMIZE": "true",
        },
    )

    try:
        image_id, metrics = engine.build(context, progress_callback=progress_callback)

        print(f"\n✓ Optimized build completed!")
        print(f"  Target stage: production")
        print(f"  Final image size: {metrics.image_size_bytes / (1024**2):.2f} MB")

    finally:
        engine.close()


async def example_parallel_builds():
    """Example: Parallel batch builds."""
    print("\n=== Example 6: Parallel Batch Builds ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT, max_parallel_builds=4)

    # Build multiple services
    contexts = [
        BuildContext(
            dockerfile_path=Path(f"./examples/{service}/Dockerfile"),
            context_path=Path(f"./examples/{service}"),
            tags=[f"{service}:latest"],
        )
        for service in ["api", "worker", "scheduler", "frontend"]
    ]

    try:
        results = await engine.build_batch(
            contexts, progress_callback=progress_callback
        )

        print(f"\n✓ Batch build completed!")
        print(f"  Total builds: {len(results)}")
        total_time = sum(m.duration_seconds for _, m in results)
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time per build: {total_time / len(results):.2f}s")

    finally:
        engine.close()


def example_custom_network():
    """Example: Build with custom network configuration."""
    print("\n=== Example 7: Build with Custom Network ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile"),
        context_path=Path("./examples/app"),
        tags=["myapp:networked"],
        network_mode="host",  # Use host network
        extra_hosts={
            "internal-registry": "192.168.1.100",
            "internal-api": "192.168.1.101",
        },
    )

    try:
        image_id, metrics = engine.build(context)

        print(f"\n✓ Network-aware build completed!")
        print(f"  Image ID: {image_id}")

    finally:
        engine.close()


def example_build_validation():
    """Example: Validate Dockerfile before building."""
    print("\n=== Example 8: Dockerfile Validation ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    dockerfile_path = Path("./examples/app/Dockerfile")

    # Validate Dockerfile
    errors = engine.validate_dockerfile(dockerfile_path)

    if errors:
        print("⚠ Dockerfile validation found issues:")
        for error in errors:
            print(f"  - {error}")
        return

    print("✓ Dockerfile validation passed")

    # Proceed with build
    context = BuildContext(
        dockerfile_path=dockerfile_path,
        context_path=Path("./examples/app"),
        tags=["myapp:validated"],
    )

    try:
        image_id, metrics = engine.build(context)
        print(f"\n✓ Build completed: {image_id}")

    finally:
        engine.close()


def example_cache_management():
    """Example: Build cache management and statistics."""
    print("\n=== Example 9: Cache Management ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    # Perform some builds...
    contexts = [
        BuildContext(
            dockerfile_path=Path(f"./examples/app{i}/Dockerfile"),
            context_path=Path(f"./examples/app{i}"),
            tags=[f"app{i}:latest"],
        )
        for i in range(1, 4)
    ]

    try:
        for context in contexts:
            try:
                engine.build(context)
            except Exception as e:
                print(f"Build failed: {e}")

        # Get cache statistics
        stats = engine.get_cache_stats()

        print("\n📊 Cache Statistics:")
        print(f"  Total builds: {stats['total_builds']}")
        print(f"  Cache hits: {stats['total_cache_hits']}")
        print(f"  Cache misses: {stats['total_cache_misses']}")
        print(f"  Hit rate: {stats['cache_hit_rate']:.1f}%")
        print(f"  Average build time: {stats['average_build_time']:.2f}s")

        # Prune old cache
        print("\n🧹 Pruning build cache...")
        result = engine.prune_build_cache()
        space_reclaimed = result.get("SpaceReclaimed", 0)
        print(f"  Reclaimed: {space_reclaimed / (1024**3):.2f} GB")

    finally:
        engine.close()


def example_export_context():
    """Example: Export build context for inspection."""
    print("\n=== Example 10: Export Build Context ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    context = BuildContext(
        dockerfile_path=Path("./examples/app/Dockerfile"),
        context_path=Path("./examples/app"),
    )

    try:
        output_path = Path("./build-context-export.tar.gz")
        engine.export_build_context(context, output_path)

        print(f"✓ Build context exported to: {output_path}")
        print(f"  Size: {output_path.stat().st_size / 1024:.2f} KB")
        print("\n  You can inspect the context with:")
        print(f"    tar -tzf {output_path}")

    finally:
        engine.close()


def example_build_monitoring():
    """Example: Monitor active builds."""
    print("\n=== Example 11: Build Monitoring ===\n")

    engine = BuildEngine(backend=BuildBackend.BUILDKIT)

    # Start some builds asynchronously
    async def monitor_builds():
        contexts = [
            BuildContext(
                dockerfile_path=Path(f"./examples/app{i}/Dockerfile"),
                context_path=Path(f"./examples/app{i}"),
                tags=[f"app{i}:latest"],
            )
            for i in range(1, 4)
        ]

        # Start builds
        tasks = [engine.build_async(context) for context in contexts]

        # Monitor while building
        while True:
            active = engine.get_active_builds()
            if not active:
                break

            print(f"\n📊 Active Builds: {len(active)}")
            for build_metrics in active:
                print(
                    f"  - {build_metrics.build_id[:8]}: "
                    f"{build_metrics.status.value} "
                    f"({build_metrics.cache_hits} cache hits)"
                )

            await asyncio.sleep(2)

        # Wait for completion
        results = await asyncio.gather(*tasks, return_exceptions=True)

        print("\n✓ All builds completed!")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  - Build {i+1}: FAILED - {result}")
            else:
                image_id, metrics = result
                print(f"  - Build {i+1}: SUCCESS - {image_id[:12]}")

    try:
        asyncio.run(monitor_builds())
    finally:
        engine.close()


def example_dockerfile_templates():
    """Example Dockerfile configurations for different scenarios."""
    print("\n=== Example Dockerfiles ===\n")

    # Basic Python application
    basic_dockerfile = """
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS development
COPY . .
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "app.py"]

FROM base AS production
COPY . .
RUN useradd -m appuser
USER appuser
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
"""

    # With BuildKit secrets
    secure_dockerfile = """
# syntax=docker/dockerfile:1.4
FROM node:18-alpine
WORKDIR /app

# Install dependencies using secrets
COPY package*.json ./
RUN --mount=type=secret,id=npm_token \\
    echo "//registry.npmjs.org/:_authToken=$(cat /run/secrets/npm_token)" > .npmrc && \\
    npm ci --only=production && \\
    rm -f .npmrc

COPY . .
CMD ["node", "server.js"]
"""

    # Multi-platform build
    multiplatform_dockerfile = """
FROM --platform=$BUILDPLATFORM golang:1.21 AS builder
ARG TARGETOS TARGETARCH
WORKDIR /build
COPY . .
RUN GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o app .

FROM alpine:3.18
COPY --from=builder /build/app /app
ENTRYPOINT ["/app"]
"""

    print("1. Basic Multi-Stage Dockerfile:")
    print(basic_dockerfile)

    print("\n2. Dockerfile with BuildKit Secrets:")
    print(secure_dockerfile)

    print("\n3. Multi-Platform Dockerfile:")
    print(multiplatform_dockerfile)


def main():
    """Run all examples."""
    print("=" * 70)
    print("Build Engine Examples")
    print("=" * 70)

    examples = [
        ("Basic Build", example_basic_build),
        ("Multi-Platform Build", example_multiplatform_build),
        ("Cached Build", example_cached_build),
        ("Secret Injection", example_secret_injection),
        ("Multi-Stage Optimized", example_multistage_optimized),
        ("Custom Network", example_custom_network),
        ("Build Validation", example_build_validation),
        ("Cache Management", example_cache_management),
        ("Export Context", example_export_context),
        ("Dockerfile Templates", example_dockerfile_templates),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nNote: These examples require Docker/BuildKit to be running")
    print("      and example directories to exist.")


if __name__ == "__main__":
    # Run specific examples or all
    import sys

    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_basic_build,
            example_multiplatform_build,
            example_cached_build,
            example_secret_injection,
            example_multistage_optimized,
            # example_parallel_builds,  # Async example
            example_custom_network,
            example_build_validation,
            example_cache_management,
            example_export_context,
            # example_build_monitoring,  # Async example
            example_dockerfile_templates,
        ]
        if 1 <= example_num <= len(examples):
            examples[example_num - 1]()
    else:
        main()
