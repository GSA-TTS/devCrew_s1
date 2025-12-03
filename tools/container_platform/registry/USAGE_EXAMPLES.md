# Registry Client Usage Examples

Comprehensive examples for using the Container Platform Registry Client.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Docker Hub](#docker-hub)
3. [Amazon ECR](#amazon-ecr)
4. [Google GCR](#google-gcr)
5. [Azure ACR](#azure-acr)
6. [Harbor Registry](#harbor-registry)
7. [Image Operations](#image-operations)
8. [Cross-Registry Sync](#cross-registry-sync)
9. [Image Promotion](#image-promotion)
10. [Advanced Features](#advanced-features)

## Basic Setup

```python
from container_platform.registry import (
    RegistryClient,
    RegistryConfig,
    RegistryType,
    ImagePromotionStage,
)

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
```

## Docker Hub

### Authentication with Username/Password

```python
config = RegistryConfig(
    registry_type=RegistryType.DOCKER_HUB,
    url="index.docker.io",
    username="your_username",
    password="your_password",
)

client = RegistryClient(config)

# Push image
image_info = client.push_image("myorg/myapp", "v1.0.0")
print(f"Pushed: {image_info.full_name}")

# Pull image
image_info = client.pull_image("myorg/myapp", "v1.0.0")
print(f"Pulled: {image_info.full_name}")
```

### Using Docker Config Credentials

```python
# If credentials exist in ~/.docker/config.json
config = RegistryConfig(
    registry_type=RegistryType.DOCKER_HUB,
    url="index.docker.io",
)

client = RegistryClient(config)
# Client will automatically use stored credentials
```

## Amazon ECR

### Basic ECR Setup

```python
config = RegistryConfig(
    registry_type=RegistryType.ECR,
    url="123456789012.dkr.ecr.us-east-1.amazonaws.com",
    region="us-east-1",
)

client = RegistryClient(config)

# ECR authentication is automatic via boto3
# Requires AWS credentials configured (env vars, ~/.aws/credentials, IAM role)

# List repositories
repos = client.list_repositories()
print(f"Found {len(repos)} repositories")

# Push to ECR
image_info = client.push_image("my-service", "latest")
print(f"Image digest: {image_info.digest}")
```

### Multi-Region ECR

```python
# East region
east_config = RegistryConfig(
    registry_type=RegistryType.ECR,
    url="123456789012.dkr.ecr.us-east-1.amazonaws.com",
    region="us-east-1",
)
east_client = RegistryClient(east_config)

# West region
west_config = RegistryConfig(
    registry_type=RegistryType.ECR,
    url="123456789012.dkr.ecr.us-west-2.amazonaws.com",
    region="us-west-2",
)
west_client = RegistryClient(west_config)

# Sync image between regions
east_client.sync_image(
    source_registry=west_client,
    image_name="my-service",
    tag="v1.0.0",
)
```

## Google GCR

### GCR with gcloud Authentication

```python
config = RegistryConfig(
    registry_type=RegistryType.GCR,
    url="gcr.io",
    project_id="my-project",
)

client = RegistryClient(config)

# Requires gcloud CLI to be installed and authenticated
# Client will automatically use: gcloud auth print-access-token

# Push to GCR
image_info = client.push_image("my-project/my-service", "v1.0.0")
```

### GCR with Service Account

```python
import os

# Set service account key path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/service-account.json"

config = RegistryConfig(
    registry_type=RegistryType.GCR,
    url="gcr.io",
    project_id="my-project",
)

client = RegistryClient(config)

# List all tags for an image
tags = client.list_tags("my-project/my-service")
print(f"Available tags: {tags}")
```

## Azure ACR

### ACR with Default Credentials

```python
config = RegistryConfig(
    registry_type=RegistryType.ACR,
    url="myregistry.azurecr.io",
    subscription_id="your-subscription-id",
)

client = RegistryClient(config)

# Uses DefaultAzureCredential (environment vars, managed identity, CLI)

# Get registry info
info = client.get_registry_info()
print(f"Registry status: {info['status']}")

# Push image
image_info = client.push_image("my-service", "v1.0.0")
```

### ACR with Service Principal

```python
import os

# Set Azure credentials
os.environ["AZURE_CLIENT_ID"] = "your-client-id"
os.environ["AZURE_CLIENT_SECRET"] = "your-client-secret"
os.environ["AZURE_TENANT_ID"] = "your-tenant-id"

config = RegistryConfig(
    registry_type=RegistryType.ACR,
    url="myregistry.azurecr.io",
)

client = RegistryClient(config)
```

## Harbor Registry

### Harbor with Basic Auth

```python
config = RegistryConfig(
    registry_type=RegistryType.HARBOR,
    url="harbor.example.com",
    username="admin",
    password="Harbor12345",
)

client = RegistryClient(config)

# List all repositories
repos = client.list_repositories()

# Search for images
results = client.search_images("nginx", limit=10)
for result in results:
    print(f"Found: {result['name']}")
```

### Harbor with Insecure Registry

```python
config = RegistryConfig(
    registry_type=RegistryType.HARBOR,
    url="harbor.local:8080",
    username="admin",
    password="password",
    insecure=True,  # Allow HTTP
)

client = RegistryClient(config)
```

## Image Operations

### Push with Progress Tracking

```python
def progress_callback(progress):
    print(
        f"Status: {progress.status} - "
        f"{progress.layers_completed}/{progress.layers_total} layers - "
        f"{progress.percentage:.1f}%"
    )

image_info = client.push_image(
    "my-service",
    "v1.0.0",
    callback=progress_callback
)
```

### Pull with Progress Tracking

```python
def progress_callback(progress):
    if progress.current_layer:
        print(f"Current: {progress.current_layer}")

image_info = client.pull_image(
    "my-service",
    "v1.0.0",
    callback=progress_callback
)

print(f"Architecture: {image_info.architecture}")
print(f"OS: {image_info.os}")
print(f"Size: {image_info.size} bytes")
print(f"Created: {image_info.created}")
```

### Get Image Information

```python
# Get detailed image info
image_info = client.get_image_info("my-service", "v1.0.0")

print(f"Full name: {image_info.full_name}")
print(f"Digest: {image_info.digest}")
print(f"Size: {image_info.size / (1024 * 1024):.2f} MB")
print(f"Labels: {image_info.labels}")

# Get manifest
manifest = client.get_manifest("my-service", "v1.0.0")
print(f"Layers: {len(manifest['layers'])}")
```

### Tag Management

```python
# Create new tag
client.tag_image("my-service", "v1.0.0", "latest")
client.tag_image("my-service", "v1.0.0", "stable")

# List all tags
tags = client.list_tags("my-service")
print(f"Tags: {', '.join(tags)}")

# Delete specific tag
client.delete_image("my-service", "old-tag")
```

### Cleanup Old Images

```python
# Keep only the 5 most recent tags
deleted_tags = client.cleanup_old_images("my-service", keep_count=5)
print(f"Deleted tags: {deleted_tags}")
```

## Cross-Registry Sync

### Sync Between Different Registry Types

```python
# Source: Docker Hub
source_config = RegistryConfig(
    registry_type=RegistryType.DOCKER_HUB,
    url="index.docker.io",
    username="source_user",
    password="source_pass",
)
source_client = RegistryClient(source_config)

# Target: Harbor
target_config = RegistryConfig(
    registry_type=RegistryType.HARBOR,
    url="harbor.company.com",
    username="admin",
    password="harbor_pass",
)
target_client = RegistryClient(target_config)

# Sync image
image_info = target_client.sync_image(
    source_registry=source_client,
    image_name="myorg/myapp",
    tag="v1.0.0",
    target_image_name="internal/myapp",
    target_tag="v1.0.0",
)
```

### Batch Sync Multiple Images

```python
images_to_sync = [
    ("nginx", "1.21"),
    ("nginx", "1.22"),
    ("redis", "7.0"),
    ("postgres", "14"),
]

for image, tag in images_to_sync:
    try:
        target_client.sync_image(
            source_registry=source_client,
            image_name=image,
            tag=tag,
        )
        print(f"Synced: {image}:{tag}")
    except Exception as e:
        print(f"Failed to sync {image}:{tag}: {e}")
```

## Image Promotion

### Promote Through Environments

```python
config = RegistryConfig(
    registry_type=RegistryType.HARBOR,
    url="harbor.company.com",
    username="admin",
    password="password",
)

client = RegistryClient(config)

# Promote from dev to staging
image_info = client.promote_image(
    image_name="my-service",
    current_stage=ImagePromotionStage.DEV,
    target_stage=ImagePromotionStage.STAGING,
    version="1.0.0",
)
print(f"Promoted to staging: {image_info.full_name}")

# Promote from staging to production
image_info = client.promote_image(
    image_name="my-service",
    current_stage=ImagePromotionStage.STAGING,
    target_stage=ImagePromotionStage.PROD,
    version="1.0.0",
)
print(f"Promoted to production: {image_info.full_name}")
```

### Multi-Stage Promotion Pipeline

```python
def promote_pipeline(client, image_name, version):
    """Complete promotion pipeline."""
    stages = [
        (ImagePromotionStage.DEV, ImagePromotionStage.STAGING),
        (ImagePromotionStage.STAGING, ImagePromotionStage.PROD),
    ]

    for current, target in stages:
        print(f"Promoting from {current.value} to {target.value}...")

        try:
            image_info = client.promote_image(
                image_name=image_name,
                current_stage=current,
                target_stage=target,
                version=version,
            )

            # Verify image
            if client.verify_image_signature(image_name, f"{target.value}-{version}"):
                print(f"✓ Signature verified for {target.value}")

            print(f"✓ Promoted to {target.value}: {image_info.digest}")

        except Exception as e:
            print(f"✗ Promotion failed: {e}")
            return False

    return True

# Run promotion
success = promote_pipeline(client, "my-service", "1.0.0")
```

## Advanced Features

### Image Signature Verification

```python
# Verify Docker Content Trust signature
is_valid = client.verify_image_signature("my-service", "v1.0.0")

if is_valid:
    print("Image signature is valid")
else:
    print("Warning: Image signature invalid or not found")
```

### Search Images

```python
# Search Docker Hub
results = client.search_images("nginx", limit=25)

for result in results:
    print(f"{result['name']} - {result.get('description', 'N/A')}")
```

### Catalog Browsing

```python
# List all repositories
repos = client.list_repositories()

# Get details for each repository
for repo in repos:
    tags = client.list_tags(repo)
    print(f"{repo}: {len(tags)} tags")

    # Get info for latest tag
    if "latest" in tags:
        info = client.get_image_info(repo, "latest")
        print(f"  Latest size: {info.size / (1024 * 1024):.2f} MB")
```

### Custom Retry Configuration

```python
config = RegistryConfig(
    registry_type=RegistryType.HARBOR,
    url="harbor.company.com",
    username="admin",
    password="password",
)

client = RegistryClient(
    config,
    timeout=600,  # 10 minutes
    max_retries=5,
)
```

### Context Manager Usage

```python
from contextlib import closing

with closing(RegistryClient(config)) as client:
    # Perform operations
    repos = client.list_repositories()

    for repo in repos:
        tags = client.list_tags(repo)
        print(f"{repo}: {tags}")

# Client automatically closed
```

### Error Handling

```python
from container_platform.registry import (
    RegistryAuthenticationError,
    RegistryOperationError,
    ImageNotFoundError,
)

try:
    client = RegistryClient(config)
    image_info = client.get_image_info("nonexistent", "tag")

except RegistryAuthenticationError as e:
    print(f"Authentication failed: {e}")

except ImageNotFoundError as e:
    print(f"Image not found: {e}")

except RegistryOperationError as e:
    print(f"Operation failed: {e}")

finally:
    if client:
        client.close()
```

## Complete Example: CI/CD Integration

```python
#!/usr/bin/env python3
"""CI/CD pipeline example with registry client."""

from container_platform.registry import (
    RegistryClient,
    RegistryConfig,
    RegistryType,
    ImagePromotionStage,
)
import os
import sys


def build_and_push(version):
    """Build and push image to dev environment."""
    config = RegistryConfig(
        registry_type=RegistryType.HARBOR,
        url=os.getenv("HARBOR_URL"),
        username=os.getenv("HARBOR_USER"),
        password=os.getenv("HARBOR_PASS"),
    )

    client = RegistryClient(config)

    # Push to dev
    print(f"Pushing to dev environment: v{version}")
    image_info = client.push_image(
        "my-service",
        f"dev-{version}"
    )

    print(f"✓ Image pushed: {image_info.digest}")
    return client


def run_tests(client, version):
    """Run tests on dev image."""
    print("Running tests...")

    # Pull image for testing
    client.pull_image("my-service", f"dev-{version}")

    # Run tests (placeholder)
    # ... test execution ...

    print("✓ Tests passed")
    return True


def promote_to_production(client, version):
    """Promote image to production."""
    print("Promoting to production...")

    # Dev -> Staging
    client.promote_image(
        image_name="my-service",
        current_stage=ImagePromotionStage.DEV,
        target_stage=ImagePromotionStage.STAGING,
        version=version,
    )
    print("✓ Promoted to staging")

    # Staging -> Production
    image_info = client.promote_image(
        image_name="my-service",
        current_stage=ImagePromotionStage.STAGING,
        target_stage=ImagePromotionStage.PROD,
        version=version,
    )
    print(f"✓ Promoted to production: {image_info.full_name}")

    # Cleanup old images
    deleted = client.cleanup_old_images("my-service", keep_count=10)
    print(f"✓ Cleaned up {len(deleted)} old images")


def main():
    version = os.getenv("VERSION", "1.0.0")

    try:
        # Build and push
        client = build_and_push(version)

        # Test
        if not run_tests(client, version):
            print("✗ Tests failed")
            sys.exit(1)

        # Promote
        promote_to_production(client, version)

        print(f"✓ Pipeline complete for v{version}")

    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
```

## Environment Variables

Commonly used environment variables:

```bash
# Docker Hub
export DOCKER_USERNAME="username"
export DOCKER_PASSWORD="password"

# AWS ECR
export AWS_ACCESS_KEY_ID="key"
export AWS_SECRET_ACCESS_KEY="secret"
export AWS_DEFAULT_REGION="us-east-1"

# Google GCR
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Azure ACR
export AZURE_CLIENT_ID="client-id"
export AZURE_CLIENT_SECRET="client-secret"
export AZURE_TENANT_ID="tenant-id"

# Harbor
export HARBOR_URL="harbor.company.com"
export HARBOR_USER="admin"
export HARBOR_PASS="password"
```

## Best Practices

1. **Use environment variables for credentials** - Never hardcode credentials
2. **Implement progress callbacks** - Provide feedback for long-running operations
3. **Handle errors gracefully** - Use specific exception types
4. **Close clients** - Always close clients when done
5. **Use image digests** - Reference images by digest for immutability
6. **Verify signatures** - Check image signatures in production
7. **Cleanup regularly** - Remove old images to save storage
8. **Tag semantically** - Use semantic versioning for tags
9. **Test promotions** - Verify images at each stage
10. **Monitor operations** - Log all registry operations
