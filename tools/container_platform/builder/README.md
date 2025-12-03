# Build Engine Module

Comprehensive container image build system with BuildKit integration, multi-platform support, and advanced caching strategies.

## Features

### Core Capabilities
- **BuildKit Integration**: Advanced build features with BuildKit backend
- **Multi-Platform Builds**: Build for amd64, arm64, and other architectures
- **Build Cache Management**: Intelligent caching with registry and local cache support
- **Secret Injection**: Secure secret handling without leaking into image layers
- **Progress Tracking**: Real-time build progress monitoring
- **Parallel Builds**: Execute multiple builds concurrently
- **Build Metrics**: Comprehensive metrics collection and analysis

### BuildKit Features
- Layer caching optimization
- Multi-stage build support
- Secret mounts (`RUN --mount=type=secret`)
- SSH agent forwarding
- Build argument templating
- Cache import/export
- Cross-platform compilation

### Build Options
- Custom network modes
- Extra host entries
- Build isolation modes
- Target stage selection
- .dockerignore support
- Dockerfile validation

## Installation

```bash
pip install docker docker-py
```

## Quick Start

### Basic Build

```python
from pathlib import Path
from build_engine import BuildEngine, BuildContext, Platform

# Initialize engine
engine = BuildEngine()

# Configure build
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:latest", "myapp:v1.0.0"],
    platforms=[Platform.AMD64],
    build_args={
        "PYTHON_VERSION": "3.11",
        "APP_ENV": "production"
    }
)

# Build image
image_id, metrics = engine.build(context)

print(f"Built image: {image_id}")
print(f"Build time: {metrics.duration_seconds}s")
print(f"Cache hits: {metrics.cache_hits}")
```

## Advanced Usage

### Multi-Platform Builds

Build images for multiple architectures:

```python
from build_engine import Platform

context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:latest-multiarch"],
    platforms=[
        Platform.AMD64,
        Platform.ARM64,
        Platform.ARM_V7
    ]
)

image_id, metrics = engine.build(context)
```

### Build with Cache Configuration

Optimize builds with registry and local caching:

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:cached"],
    cache_from=[
        "type=registry,ref=myregistry.io/myapp:buildcache",
        "type=local,src=/tmp/buildkit-cache"
    ],
    cache_to="type=local,dest=/tmp/buildkit-cache,mode=max",
    pull=True
)

image_id, metrics = engine.build(context)
```

### Secret Injection

Securely inject secrets during build without storing in layers:

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:secure"],
    secrets={
        "github_token": "ghp_xxxxxxxxxxxx",
        "npm_token": "npm_xxxxxxxxxxxx"
    },
    ssh_keys={
        "default": str(Path.home() / ".ssh/id_rsa")
    }
)

image_id, metrics = engine.build(context)
```

**Dockerfile with secrets:**

```dockerfile
# syntax=docker/dockerfile:1.4
FROM node:18-alpine

# Use secret mount to access token
RUN --mount=type=secret,id=npm_token \
    echo "//registry.npmjs.org/:_authToken=$(cat /run/secrets/npm_token)" > .npmrc && \
    npm ci --only=production && \
    rm -f .npmrc

COPY . .
CMD ["node", "server.js"]
```

### Multi-Stage Builds

Build only specific stages:

```python
context = BuildContext(
    dockerfile_path=Path("./Dockerfile"),
    context_path=Path("."),
    tags=["myapp:production"],
    target="production",  # Build only production stage
    build_args={
        "BUILD_ENV": "production",
        "OPTIMIZE": "true"
    }
)

image_id, metrics = engine.build(context)
```

**Multi-stage Dockerfile:**

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS development
COPY . .
CMD ["python", "-m", "debugpy", "app.py"]

FROM base AS production
COPY . .
RUN useradd -m appuser
USER appuser
CMD ["gunicorn", "-w", "4", "app:app"]
```

### Parallel Batch Builds

Build multiple images concurrently:

```python
import asyncio

async def build_services():
    engine = BuildEngine(max_parallel_builds=4)

    contexts = [
        BuildContext(
            dockerfile_path=Path(f"./{service}/Dockerfile"),
            context_path=Path(f"./{service}"),
            tags=[f"{service}:latest"]
        )
        for service in ["api", "worker", "scheduler", "frontend"]
    ]

    results = await engine.build_batch(contexts)

    for image_id, metrics in results:
        print(f"Built: {image_id} in {metrics.duration_seconds}s")

asyncio.run(build_services())
```

### Progress Tracking

Monitor build progress in real-time:

```python
def progress_callback(progress: BuildProgress):
    print(
        f"Step {progress.current_step}/{progress.total_steps} "
        f"({progress.progress_percent:.1f}%): {progress.current_layer}"
    )

image_id, metrics = engine.build(context, progress_callback=progress_callback)
```

### Build Validation

Validate Dockerfile before building:

```python
dockerfile_path = Path("./Dockerfile")
errors = engine.validate_dockerfile(dockerfile_path)

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Dockerfile is valid")
    image_id, metrics = engine.build(context)
```

## Build Metrics

The `BuildMetrics` dataclass provides comprehensive build information:

```python
@dataclass
class BuildMetrics:
    build_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    cache_hits: int
    cache_misses: int
    total_layers: int
    image_size_bytes: int
    platform: str
    status: BuildStatus
    error_message: str
```

### Cache Statistics

Get aggregate cache statistics:

```python
stats = engine.get_cache_stats()

print(f"Total builds: {stats['total_builds']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
print(f"Average build time: {stats['average_build_time']:.2f}s")
```

### Build History

Access build history:

```python
# Get all builds
history = engine.get_build_history()

# Get last 10 builds
recent = engine.get_build_history(limit=10)

for metrics in recent:
    print(f"{metrics.build_id}: {metrics.status.value} "
          f"({metrics.duration_seconds:.2f}s)")
```

## Cache Management

### Prune Build Cache

Remove unused build cache:

```python
result = engine.prune_build_cache()

space_reclaimed = result.get("SpaceReclaimed", 0)
print(f"Reclaimed {space_reclaimed / (1024**3):.2f} GB")
```

### Export Build Context

Export build context for inspection:

```python
output_path = Path("./context.tar.gz")
engine.export_build_context(context, output_path)

# Inspect with: tar -tzf context.tar.gz
```

## Platform Support

Supported build platforms:

```python
class Platform(Enum):
    AMD64 = "linux/amd64"
    ARM64 = "linux/arm64"
    ARM_V7 = "linux/arm/v7"
    PPC64LE = "linux/ppc64le"
    S390X = "linux/s390x"
```

### Cross-Platform Dockerfile

```dockerfile
FROM --platform=$BUILDPLATFORM golang:1.21 AS builder
ARG TARGETOS TARGETARCH
WORKDIR /build
COPY . .
RUN GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o app .

FROM alpine:3.18
COPY --from=builder /build/app /app
ENTRYPOINT ["/app"]
```

## Configuration Options

### BuildContext Parameters

```python
@dataclass
class BuildContext:
    # Required
    dockerfile_path: Path
    context_path: Path

    # Optional
    tags: List[str] = []
    platforms: List[Platform] = [Platform.AMD64]
    build_args: Dict[str, str] = {}
    secrets: Dict[str, str] = {}
    labels: Dict[str, str] = {}
    target: Optional[str] = None
    cache_from: List[str] = []
    cache_to: Optional[str] = None
    no_cache: bool = False
    pull: bool = True
    rm: bool = True
    network_mode: Optional[str] = None
    extra_hosts: Dict[str, str] = {}
    isolation: Optional[str] = None
    ssh_keys: Dict[str, str] = {}
```

### BuildEngine Parameters

```python
engine = BuildEngine(
    backend=BuildBackend.BUILDKIT,  # DOCKER, BUILDKIT, PODMAN
    base_url=None,                  # Docker daemon URL
    timeout=600,                    # Build timeout (seconds)
    max_parallel_builds=4           # Max concurrent builds
)
```

## Best Practices

### 1. Use BuildKit

Always use BuildKit for modern build features:

```python
engine = BuildEngine(backend=BuildBackend.BUILDKIT)
```

### 2. Enable Build Cache

Configure cache for faster rebuilds:

```python
context = BuildContext(
    # ... other options ...
    cache_from=["type=registry,ref=myapp:buildcache"],
    cache_to="type=inline",
    pull=True
)
```

### 3. Multi-Stage Builds

Use multi-stage builds to minimize image size:

```dockerfile
FROM builder AS builder
# ... build steps ...

FROM scratch
COPY --from=builder /app /app
```

### 4. Secure Secrets

Never include secrets in build args or ENV:

```python
# Bad - secrets visible in image history
context = BuildContext(
    build_args={"API_KEY": "secret123"}
)

# Good - use BuildKit secrets
context = BuildContext(
    secrets={"api_key": "secret123"}
)
```

### 5. .dockerignore

Always use .dockerignore to exclude unnecessary files:

```
__pycache__
*.pyc
.git
.env
node_modules
venv/
*.log
```

### 6. Validate Before Building

Validate Dockerfiles to catch issues early:

```python
errors = engine.validate_dockerfile(dockerfile_path)
if errors:
    for error in errors:
        print(error)
    sys.exit(1)
```

### 7. Monitor Build Metrics

Track build performance:

```python
image_id, metrics = engine.build(context)

print(f"Build time: {metrics.duration_seconds}s")
print(f"Cache efficiency: {metrics.cache_hits / metrics.total_layers * 100:.1f}%")
print(f"Image size: {metrics.image_size_bytes / (1024**2):.2f} MB")
```

## Troubleshooting

### BuildKit Not Detected

```python
# Check BuildKit availability
info = engine.client.info()
print(info.get("BuilderVersion"))

# Enable BuildKit
import os
os.environ["DOCKER_BUILDKIT"] = "1"
```

### Build Timeout

Increase timeout for large builds:

```python
engine = BuildEngine(timeout=1800)  # 30 minutes
```

### Cache Issues

Clear build cache:

```python
engine.prune_build_cache(all_cache=True)
```

### Memory Issues

Limit concurrent builds:

```python
engine = BuildEngine(max_parallel_builds=2)
```

## Performance Tips

1. **Use Layer Caching**: Order Dockerfile commands from least to most frequently changing
2. **Minimize Context Size**: Use .dockerignore to exclude large files
3. **Multi-Stage Builds**: Separate build and runtime stages
4. **Parallel Builds**: Build independent images concurrently
5. **Registry Cache**: Use registry cache for shared builds
6. **BuildKit**: Always use BuildKit for better performance

## API Reference

### BuildEngine

```python
class BuildEngine:
    def build(context: BuildContext, progress_callback: Optional[callable]) -> Tuple[str, BuildMetrics]
    async def build_async(context: BuildContext, progress_callback: Optional[callable]) -> Tuple[str, BuildMetrics]
    async def build_batch(contexts: List[BuildContext], progress_callback: Optional[callable]) -> List[Tuple[str, BuildMetrics]]
    def prune_build_cache(all_cache: bool = False, filters: Optional[Dict] = None) -> Dict[str, Any]
    def get_build_history(limit: Optional[int] = None) -> List[BuildMetrics]
    def get_active_builds() -> List[BuildMetrics]
    def cancel_build(build_id: str) -> bool
    def get_cache_stats() -> Dict[str, Any]
    def export_build_context(context: BuildContext, output_path: Path) -> None
    def validate_dockerfile(dockerfile_path: Path) -> List[str]
```

## Examples

See `examples.py` for comprehensive usage examples:

1. Basic build
2. Multi-platform build
3. Cached build
4. Secret injection
5. Multi-stage optimized
6. Parallel builds
7. Custom network
8. Build validation
9. Cache management
10. Export context
11. Build monitoring

## Testing

Run tests:

```bash
pytest test_build_engine.py -v
```

Run with coverage:

```bash
pytest test_build_engine.py --cov=build_engine --cov-report=html
```

## License

Part of the Container Platform Management tool suite.
