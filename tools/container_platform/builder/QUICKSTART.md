# Build Engine Quick Start Guide

## Installation

```bash
pip install docker
```

## Basic Usage

### 1. Simple Build

```python
from pathlib import Path
from build_engine import BuildEngine, BuildContext

# Initialize engine
engine = BuildEngine()

# Configure build
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:latest"]
)

# Build
image_id, metrics = engine.build(context)
print(f"Built: {image_id}")
```

### 2. Multi-Platform Build

```python
from build_engine import Platform

context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:multiarch"],
    platforms=[Platform.AMD64, Platform.ARM64]
)

image_id, metrics = engine.build(context)
```

### 3. Build with Cache

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:cached"],
    cache_from=["type=registry,ref=myregistry/cache"],
    cache_to="type=inline"
)

image_id, metrics = engine.build(context)
print(f"Cache hit rate: {metrics.cache_hits / metrics.total_layers * 100:.1f}%")
```

### 4. Secure Build with Secrets

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:secure"],
    secrets={
        "github_token": "ghp_xxxxxxxxxxxx"
    }
)

image_id, metrics = engine.build(context)
```

**Dockerfile:**
```dockerfile
# syntax=docker/dockerfile:1.4
FROM node:18-alpine

RUN --mount=type=secret,id=github_token \
    TOKEN=$(cat /run/secrets/github_token) && \
    git clone https://$TOKEN@github.com/private/repo.git
```

### 5. Multi-Stage Build

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:production"],
    target="production"  # Build only production stage
)

image_id, metrics = engine.build(context)
```

**Dockerfile:**
```dockerfile
FROM python:3.11 AS builder
WORKDIR /build
COPY . .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim AS production
COPY --from=builder /root/.local /root/.local
COPY . /app
CMD ["python", "app.py"]
```

### 6. Progress Tracking

```python
def show_progress(progress):
    print(f"[{progress.progress_percent:.1f}%] {progress.current_layer}")

image_id, metrics = engine.build(context, progress_callback=show_progress)
```

### 7. Parallel Builds

```python
import asyncio

async def build_all():
    contexts = [
        BuildContext(
            dockerfile_path=Path(f"./{svc}/Dockerfile"),
            context_path=Path(f"./{svc}"),
            tags=[f"{svc}:latest"]
        )
        for svc in ["api", "worker", "frontend"]
    ]

    results = await engine.build_batch(contexts)
    print(f"Built {len(results)} images")

asyncio.run(build_all())
```

### 8. Build Arguments

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:latest"],
    build_args={
        "PYTHON_VERSION": "3.11",
        "APP_ENV": "production"
    },
    labels={
        "version": "1.0.0",
        "maintainer": "devops@example.com"
    }
)

image_id, metrics = engine.build(context)
```

### 9. Validate Before Building

```python
# Validate Dockerfile
errors = engine.validate_dockerfile(Path("./Dockerfile"))

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    # Proceed with build
    image_id, metrics = engine.build(context)
```

### 10. Cache Management

```python
# Get cache statistics
stats = engine.get_cache_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")

# Prune old cache
result = engine.prune_build_cache()
print(f"Reclaimed: {result['SpaceReclaimed'] / (1024**3):.2f} GB")
```

## Common Patterns

### Production Build

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:latest", f"myapp:{version}"],
    platforms=[Platform.AMD64, Platform.ARM64],
    build_args={"ENV": "production"},
    cache_from=["type=registry,ref=myregistry/cache"],
    cache_to="type=inline",
    pull=True,
    target="production",
    labels={
        "version": version,
        "commit": git_commit,
        "build_date": datetime.now().isoformat()
    }
)
```

### Development Build

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile.dev"),
    context_path=Path("."),
    tags=["myapp:dev"],
    target="development",
    network_mode="host",
    no_cache=False  # Use cache for faster iterations
)
```

### CI/CD Build

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=[f"myapp:{git_sha}", "myapp:latest"],
    platforms=[Platform.AMD64, Platform.ARM64],
    cache_from=[f"type=registry,ref=myregistry/myapp:cache"],
    cache_to=f"type=registry,ref=myregistry/myapp:cache,mode=max",
    pull=True,
    labels={
        "ci.pipeline": os.environ.get("CI_PIPELINE_ID"),
        "ci.commit": os.environ.get("CI_COMMIT_SHA"),
        "ci.branch": os.environ.get("CI_COMMIT_BRANCH")
    }
)
```

## Configuration Reference

### BuildEngine Options

```python
engine = BuildEngine(
    backend=BuildBackend.BUILDKIT,  # DOCKER, BUILDKIT, PODMAN
    base_url=None,                  # Docker daemon URL
    timeout=600,                    # Build timeout (seconds)
    max_parallel_builds=4           # Max concurrent builds
)
```

### BuildContext Options

```python
context = BuildContext(
    # Required
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),

    # Image tags
    tags=["myapp:latest", "myapp:v1.0"],

    # Platforms
    platforms=[Platform.AMD64, Platform.ARM64],

    # Build configuration
    build_args={"KEY": "value"},
    secrets={"token": "secret"},
    labels={"version": "1.0"},
    target="production",

    # Cache
    cache_from=["type=registry,ref=cache"],
    cache_to="type=inline",
    no_cache=False,
    pull=True,

    # Network
    network_mode="bridge",
    extra_hosts={"api": "192.168.1.100"},

    # Advanced
    rm=True,
    isolation=None,
    ssh_keys={"default": "/path/to/key"}
)
```

## Troubleshooting

### BuildKit Not Available

```python
# Check BuildKit
info = engine.client.info()
print(info.get("BuilderVersion"))

# Enable BuildKit
import os
os.environ["DOCKER_BUILDKIT"] = "1"
```

### Build Timeout

```python
# Increase timeout
engine = BuildEngine(timeout=1800)  # 30 minutes
```

### Out of Disk Space

```python
# Clean build cache
engine.prune_build_cache(all_cache=True)

# Check cache size
stats = engine.get_cache_stats()
```

### Slow Builds

```python
# Use cache
context = BuildContext(
    cache_from=["type=registry,ref=cache"],
    pull=False  # Don't pull if not needed
)

# Check cache hit rate
print(f"Cache hits: {metrics.cache_hits}/{metrics.total_layers}")
```

## Best Practices

1. **Always use BuildKit** for better performance
2. **Configure cache** for faster rebuilds
3. **Use multi-stage builds** to minimize image size
4. **Validate Dockerfiles** before building
5. **Track metrics** to optimize build times
6. **Use secrets** for sensitive data, not build args
7. **Tag appropriately** for version management
8. **Clean cache regularly** to free disk space

## Examples

See `examples.py` for comprehensive examples:
- Basic builds
- Multi-platform builds
- Cached builds
- Secret injection
- Parallel builds
- And more...

## Documentation

- **README.md**: Full documentation
- **IMPLEMENTATION_SUMMARY.md**: Technical details
- **examples.py**: Working examples
- **test_build_engine.py**: Test cases

## Support

For issues or questions, refer to the comprehensive documentation in README.md.
