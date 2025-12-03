"""
Container Manager module for Docker/Podman container lifecycle management.

Implements comprehensive container management operations including:
- Container lifecycle management (create, start, stop, remove, restart)
- Container logs streaming and inspection
- Network and volume management
- Resource limits and health check configuration
- Container exec operations for debugging
- Container statistics and monitoring

Supports the following protocols:
- P-DOCKER-CLEANUP: Container and image cleanup automation
- P-INFRASTRUCTURE-SETUP: Container-based infrastructure deployment

Author: DevCrew Team
"""

import logging
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator

try:
    import docker
    from docker.errors import (APIError, ContainerError, DockerException,
                               ImageNotFound, NotFound)
    from docker.models.containers import Container
    from docker.types import Mount

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    # Define placeholder types for type checking
    Container = Any  # type: ignore
    DockerException = Exception  # type: ignore
    APIError = Exception  # type: ignore
    NotFound = Exception  # type: ignore
    ContainerError = Exception  # type: ignore

logger = logging.getLogger(__name__)


# ============================================================================
# Exception Hierarchy
# ============================================================================


class ContainerManagerError(Exception):
    """Base exception for all container manager errors."""

    pass


class ContainerNotFoundError(ContainerManagerError):
    """Raised when a container cannot be found."""

    pass


class ContainerOperationError(ContainerManagerError):
    """Raised when a container operation fails."""

    pass


class ContainerConnectionError(ContainerManagerError):
    """Raised when connection to Docker daemon fails."""

    pass


class ContainerConfigurationError(ContainerManagerError):
    """Raised when container configuration is invalid."""

    pass


class ContainerNetworkError(ContainerManagerError):
    """Raised when network operations fail."""

    pass


class ContainerVolumeError(ContainerManagerError):
    """Raised when volume operations fail."""

    pass


# ============================================================================
# Enumerations
# ============================================================================


class ContainerStatus(str, Enum):
    """Container status states."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"


class RestartPolicy(str, Enum):
    """Container restart policy options."""

    NO = "no"
    ON_FAILURE = "on-failure"
    ALWAYS = "always"
    UNLESS_STOPPED = "unless-stopped"


class LogDriver(str, Enum):
    """Logging driver options."""

    JSON_FILE = "json-file"
    SYSLOG = "syslog"
    JOURNALD = "journald"
    GELF = "gelf"
    FLUENTD = "fluentd"
    AWSLOGS = "awslogs"
    SPLUNK = "splunk"
    NONE = "none"


# ============================================================================
# Configuration Models
# ============================================================================


class ResourceLimits(BaseModel):
    """Container resource limits configuration."""

    cpu_shares: Optional[int] = Field(
        None, ge=0, description="CPU shares (relative weight)"
    )
    cpu_period: Optional[int] = Field(
        None, ge=1000, le=1000000, description="CPU CFS period in microseconds"
    )
    cpu_quota: Optional[int] = Field(
        None, ge=1000, description="CPU CFS quota in microseconds"
    )
    cpuset_cpus: Optional[str] = Field(
        None, description="CPUs to use (e.g., '0-3', '0,1')"
    )
    cpuset_mems: Optional[str] = Field(
        None, description="Memory nodes to use (e.g., '0-3', '0,1')"
    )
    memory: Optional[int] = Field(None, ge=4194304, description="Memory limit in bytes")
    memory_reservation: Optional[int] = Field(
        None, ge=0, description="Memory soft limit in bytes"
    )
    memory_swap: Optional[int] = Field(
        None,
        ge=-1,
        description="Total memory + swap limit (-1 for unlimited)",
    )
    memory_swappiness: Optional[int] = Field(
        None, ge=0, le=100, description="Memory swappiness (0-100)"
    )
    oom_kill_disable: bool = Field(
        False, description="Disable OOM killer for container"
    )
    pids_limit: Optional[int] = Field(None, ge=-1, description="PIDs limit")
    blkio_weight: Optional[int] = Field(
        None, ge=10, le=1000, description="Block IO weight (10-1000)"
    )

    @field_validator("memory")
    @classmethod
    def validate_memory(cls, v: Optional[int]) -> Optional[int]:
        """Validate memory is at least 4MB."""
        if v is not None and v < 4194304:  # 4MB minimum
            raise ValueError("Memory limit must be at least 4MB (4194304 bytes)")
        return v


class HealthCheckConfig(BaseModel):
    """Container health check configuration."""

    test: Union[str, List[str]] = Field(..., description="Health check command")
    interval: int = Field(30, ge=1, description="Time between health checks (seconds)")
    timeout: int = Field(30, ge=1, description="Health check timeout (seconds)")
    retries: int = Field(3, ge=1, description="Consecutive failures before unhealthy")
    start_period: int = Field(
        0, ge=0, description="Grace period before health checks start (seconds)"
    )

    @field_validator("test")
    @classmethod
    def validate_test(cls, v: Union[str, List[str]]) -> Union[str, List[str]]:
        """Validate health check test command."""
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("Health check test cannot be empty")
        elif isinstance(v, list):
            if not v or not v[0]:
                raise ValueError("Health check test list cannot be empty")
        return v


class VolumeMount(BaseModel):
    """Volume mount configuration."""

    source: str = Field(..., description="Source path on host or volume name")
    target: str = Field(..., description="Target path in container")
    type: str = Field("bind", description="Mount type (bind, volume, tmpfs)")
    read_only: bool = Field(False, description="Mount as read-only")
    consistency: Optional[str] = Field(
        None, description="Consistency requirement (consistent, cached, delegated)"
    )


class PortMapping(BaseModel):
    """Port mapping configuration."""

    container_port: int = Field(..., ge=1, le=65535, description="Container port")
    host_port: Optional[int] = Field(
        None, ge=1, le=65535, description="Host port (None for random)"
    )
    protocol: str = Field("tcp", description="Protocol (tcp, udp)")
    host_ip: str = Field("0.0.0.0", description="Host IP to bind to")


class ContainerConfig(BaseModel):
    """Comprehensive container configuration."""

    image: str = Field(..., description="Container image name")
    name: Optional[str] = Field(None, description="Container name")
    command: Optional[Union[str, List[str]]] = Field(None, description="Command to run")
    entrypoint: Optional[Union[str, List[str]]] = Field(
        None, description="Entrypoint override"
    )
    environment: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    volumes: List[VolumeMount] = Field(
        default_factory=list, description="Volume mounts"
    )
    ports: List[PortMapping] = Field(default_factory=list, description="Port mappings")
    network_mode: Optional[str] = Field(
        None, description="Network mode (bridge, host, none, container:<id>)"
    )
    networks: List[str] = Field(
        default_factory=list, description="Networks to connect to"
    )
    hostname: Optional[str] = Field(None, description="Container hostname")
    user: Optional[str] = Field(None, description="User to run as (user:group)")
    working_dir: Optional[str] = Field(None, description="Working directory")
    labels: Dict[str, str] = Field(default_factory=dict, description="Container labels")
    restart_policy: RestartPolicy = Field(
        RestartPolicy.NO, description="Restart policy"
    )
    restart_max_retries: int = Field(
        0, ge=0, description="Max retries for on-failure policy"
    )
    resources: Optional[ResourceLimits] = Field(
        None, description="Resource limits configuration"
    )
    health_check: Optional[HealthCheckConfig] = Field(
        None, description="Health check configuration"
    )
    privileged: bool = Field(False, description="Run in privileged mode")
    cap_add: List[str] = Field(default_factory=list, description="Capabilities to add")
    cap_drop: List[str] = Field(
        default_factory=list, description="Capabilities to drop"
    )
    devices: List[str] = Field(default_factory=list, description="Device mappings")
    dns: List[str] = Field(default_factory=list, description="DNS servers")
    dns_search: List[str] = Field(
        default_factory=list, description="DNS search domains"
    )
    extra_hosts: Dict[str, str] = Field(
        default_factory=dict, description="Extra host mappings"
    )
    log_driver: LogDriver = Field(
        LogDriver.JSON_FILE, description="Logging driver to use"
    )
    log_options: Dict[str, str] = Field(
        default_factory=dict, description="Logging driver options"
    )
    auto_remove: bool = Field(
        False, description="Automatically remove container when it exits"
    )
    detach: bool = Field(True, description="Run container in detached mode")
    stdin_open: bool = Field(False, description="Keep STDIN open")
    tty: bool = Field(False, description="Allocate a pseudo-TTY")

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Validate image name is not empty."""
        if not v or not v.strip():
            raise ValueError("Image name cannot be empty")
        return v.strip()


class ContainerInfo(BaseModel):
    """Container information model."""

    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    short_id: str = Field(..., description="Short container ID (first 12 chars)")
    status: str = Field(..., description="Container status")
    state: str = Field(..., description="Container state")
    image: str = Field(..., description="Image name")
    created: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(
        None, description="Container start timestamp"
    )
    finished_at: Optional[datetime] = Field(
        None, description="Container finish timestamp"
    )
    exit_code: Optional[int] = Field(None, description="Exit code if stopped")
    labels: Dict[str, Any] = Field(default_factory=dict, description="Container labels")
    networks: List[str] = Field(default_factory=list, description="Connected networks")
    ports: Dict[str, Any] = Field(
        default_factory=dict, description="Port mappings (internal -> external)"
    )
    mounts: List[Dict[str, Any]] = Field(default_factory=list, description="Mounts")
    platform: str = Field(..., description="Platform (linux/amd64, etc.)")


class ContainerStats(BaseModel):
    """Container resource usage statistics."""

    container_id: str = Field(..., description="Container ID")
    container_name: str = Field(..., description="Container name")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    memory_limit_mb: float = Field(..., description="Memory limit in MB")
    memory_percent: float = Field(..., description="Memory usage percentage")
    network_rx_mb: float = Field(..., description="Network received in MB")
    network_tx_mb: float = Field(..., description="Network transmitted in MB")
    block_read_mb: float = Field(..., description="Block IO read in MB")
    block_write_mb: float = Field(..., description="Block IO write in MB")
    pids: int = Field(..., description="Number of PIDs")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Statistics timestamp"
    )


# ============================================================================
# Container Manager
# ============================================================================


class ContainerManager:
    """
    Manages Docker/Podman container lifecycle operations.

    Provides comprehensive container management including:
    - Container lifecycle (create, start, stop, remove, restart)
    - Logs streaming and inspection
    - Network and volume management
    - Resource limits and health checks
    - Container exec and debugging
    - Statistics and monitoring

    Examples:
        >>> # Initialize manager
        >>> manager = ContainerManager()
        >>>
        >>> # Create and start a container
        >>> config = ContainerConfig(
        ...     image="nginx:latest",
        ...     name="web-server",
        ...     ports=[PortMapping(container_port=80, host_port=8080)],
        ... )
        >>> container_id = manager.create_container(config)
        >>> manager.start_container(container_id)
        >>>
        >>> # Stream logs
        >>> for log_line in manager.stream_logs(container_id):
        ...     print(log_line)
        >>>
        >>> # Get statistics
        >>> stats = manager.get_container_stats(container_id)
        >>> print(f"CPU: {stats.cpu_percent}%, Memory: {stats.memory_usage_mb}MB")
        >>>
        >>> # Execute command in container
        >>> exit_code, output = manager.exec_run(container_id, ["ls", "-la"])
        >>>
        >>> # Stop and remove
        >>> manager.stop_container(container_id, timeout=10)
        >>> manager.remove_container(container_id)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        tls: bool = False,
        timeout: int = 60,
        max_pool_size: int = 10,
    ) -> None:
        """
        Initialize ContainerManager.

        Args:
            base_url: Docker daemon URL (default: unix:///var/run/docker.sock)
            tls: Enable TLS verification
            timeout: Default timeout for operations in seconds
            max_pool_size: Maximum connection pool size

        Raises:
            ContainerManagerError: If Docker is not available
            ContainerConnectionError: If connection to daemon fails
        """
        if not DOCKER_AVAILABLE:
            raise ContainerManagerError(
                "Docker SDK not available. Install with: pip install docker"
            )

        self.timeout = timeout
        try:
            self.client = docker.DockerClient(
                base_url=base_url,
                tls=tls,
                timeout=timeout,
                max_pool_size=max_pool_size,
            )
            # Verify connection
            self.client.ping()
            version_info = self.client.version()
            version = version_info.get("Version", "unknown")
            logger.info(f"Connected to Docker daemon (version: {version})")
        except DockerException as e:
            raise ContainerConnectionError(
                f"Failed to connect to Docker daemon: {e}"
            ) from e

    def __enter__(self) -> "ContainerManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close client."""
        self.close()

    def close(self) -> None:
        """Close Docker client connection."""
        try:
            self.client.close()
            logger.info("Closed Docker client connection")
        except Exception as e:
            logger.warning(f"Error closing Docker client: {e}")

    # ========================================================================
    # Container Lifecycle Operations
    # ========================================================================

    def create_container(self, config: ContainerConfig, pull: bool = True) -> str:
        """
        Create a new container from configuration.

        Args:
            config: Container configuration
            pull: Pull image if not available locally

        Returns:
            Container ID

        Raises:
            ContainerConfigurationError: If configuration is invalid
            ContainerOperationError: If creation fails

        Examples:
            >>> config = ContainerConfig(
            ...     image="python:3.11-slim",
            ...     name="app-container",
            ...     command=["python", "-m", "http.server"],
            ...     environment={"ENV": "production"},
            ...     resources=ResourceLimits(
            ...         memory=536870912,  # 512MB
            ...         cpu_shares=512
            ...     )
            ... )
            >>> container_id = manager.create_container(config)
        """
        try:
            # Pull image if needed
            if pull:
                logger.info(f"Pulling image: {config.image}")
                self.client.images.pull(config.image)

            # Build host configuration
            host_config_kwargs = self._build_host_config(config)

            # Build port bindings
            port_bindings: Dict[str, Any] = {}
            exposed_ports = []
            for port in config.ports:
                container_port = f"{port.container_port}/{port.protocol}"
                exposed_ports.append(container_port)
                if port.host_port:
                    port_bindings[container_port] = (
                        port.host_ip,
                        port.host_port,
                    )
                else:
                    # When no host port specified, Docker assigns random port
                    port_bindings[container_port] = None

            host_config_kwargs["port_bindings"] = port_bindings

            # Build networking configuration
            networking_config = None
            if config.networks:
                networking_config = {}
                for network in config.networks:
                    endpoint_cfg = self.client.api.create_endpoint_config()
                    networking_config[network] = endpoint_cfg

            # Create container
            container = self.client.containers.create(
                image=config.image,
                name=config.name,
                command=config.command,
                entrypoint=config.entrypoint,
                environment=config.environment,
                hostname=config.hostname,
                user=config.user,
                working_dir=config.working_dir,
                labels=config.labels,
                detach=config.detach,
                stdin_open=config.stdin_open,
                tty=config.tty,
                ports=exposed_ports if exposed_ports else None,
                host_config=self.client.api.create_host_config(**host_config_kwargs),
                networking_config=networking_config,
            )

            logger.info(
                f"Created container {container.short_id} " f"from image {config.image}"
            )
            return container.id

        except ImageNotFound as e:
            raise ContainerConfigurationError(f"Image not found: {config.image}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to create container: {e}") from e

    def _build_host_config(self, config: ContainerConfig) -> Dict[str, Any]:
        """Build host configuration dictionary from container config."""
        host_config: Dict[str, Any] = {
            "auto_remove": config.auto_remove,
            "privileged": config.privileged,
            "network_mode": config.network_mode,
        }

        # Restart policy
        restart_policy: Dict[str, Any] = {"Name": config.restart_policy.value}
        if config.restart_policy == RestartPolicy.ON_FAILURE:
            restart_policy["MaximumRetryCount"] = config.restart_max_retries
        host_config["restart_policy"] = restart_policy

        # Volume mounts
        if config.volumes:
            mounts = []
            for vol in config.volumes:
                mount_kwargs = {
                    "target": vol.target,
                    "source": vol.source,
                    "type": vol.type,
                    "read_only": vol.read_only,
                }
                if vol.consistency:
                    mount_kwargs["consistency"] = vol.consistency
                mounts.append(Mount(**mount_kwargs))
            host_config["mounts"] = mounts

        # Resource limits
        if config.resources:
            res = config.resources
            if res.cpu_shares:
                host_config["cpu_shares"] = res.cpu_shares
            if res.cpu_period:
                host_config["cpu_period"] = res.cpu_period
            if res.cpu_quota:
                host_config["cpu_quota"] = res.cpu_quota
            if res.cpuset_cpus:
                host_config["cpuset_cpus"] = res.cpuset_cpus
            if res.cpuset_mems:
                host_config["cpuset_mems"] = res.cpuset_mems
            if res.memory:
                host_config["mem_limit"] = res.memory
            if res.memory_reservation:
                host_config["mem_reservation"] = res.memory_reservation
            if res.memory_swap:
                host_config["memswap_limit"] = res.memory_swap
            if res.memory_swappiness is not None:
                host_config["mem_swappiness"] = res.memory_swappiness
            if res.oom_kill_disable:
                host_config["oom_kill_disable"] = res.oom_kill_disable
            if res.pids_limit:
                host_config["pids_limit"] = res.pids_limit
            if res.blkio_weight:
                host_config["blkio_weight"] = res.blkio_weight

        # Capabilities
        if config.cap_add:
            host_config["cap_add"] = config.cap_add
        if config.cap_drop:
            host_config["cap_drop"] = config.cap_drop

        # Devices
        if config.devices:
            host_config["devices"] = config.devices

        # DNS
        if config.dns:
            host_config["dns"] = config.dns
        if config.dns_search:
            host_config["dns_search"] = config.dns_search

        # Extra hosts
        if config.extra_hosts:
            extra_hosts = [f"{host}:{ip}" for host, ip in config.extra_hosts.items()]
            host_config["extra_hosts"] = extra_hosts

        # Logging
        log_config: Dict[str, Any] = {"Type": config.log_driver.value}
        if config.log_options:
            log_config["Config"] = config.log_options
        host_config["log_config"] = log_config

        return host_config

    def start_container(self, container_id: str) -> None:
        """
        Start a container.

        Args:
            container_id: Container ID or name

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If start fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container.short_id}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to start container: {e}") from e

    def stop_container(self, container_id: str, timeout: Optional[int] = None) -> None:
        """
        Stop a running container.

        Args:
            container_id: Container ID or name
            timeout: Seconds to wait before killing (default: 10)

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If stop fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout or 10)
            logger.info(f"Stopped container {container.short_id}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to stop container: {e}") from e

    def restart_container(
        self, container_id: str, timeout: Optional[int] = None
    ) -> None:
        """
        Restart a container.

        Args:
            container_id: Container ID or name
            timeout: Seconds to wait before killing (default: 10)

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If restart fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout or 10)
            logger.info(f"Restarted container {container.short_id}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to restart container: {e}") from e

    def pause_container(self, container_id: str) -> None:
        """
        Pause a running container.

        Args:
            container_id: Container ID or name

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If pause fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.pause()
            logger.info(f"Paused container {container.short_id}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to pause container: {e}") from e

    def unpause_container(self, container_id: str) -> None:
        """
        Unpause a paused container.

        Args:
            container_id: Container ID or name

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If unpause fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.unpause()
            logger.info(f"Unpaused container {container.short_id}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to unpause container: {e}") from e

    def kill_container(self, container_id: str, signal: str = "SIGKILL") -> None:
        """
        Kill a running container.

        Args:
            container_id: Container ID or name
            signal: Signal to send (default: SIGKILL)

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If kill fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.kill(signal=signal)
            logger.info(f"Killed container {container.short_id} with signal {signal}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to kill container: {e}") from e

    def remove_container(
        self, container_id: str, force: bool = False, v: bool = False
    ) -> None:
        """
        Remove a container.

        Args:
            container_id: Container ID or name
            force: Force removal even if running
            v: Remove associated volumes

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If removal fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force, v=v)
            logger.info(f"Removed container {container.short_id}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to remove container: {e}") from e

    def wait_container(self, container_id: str, timeout: Optional[int] = None) -> int:
        """
        Wait for a container to stop and return exit code.

        Args:
            container_id: Container ID or name
            timeout: Maximum time to wait in seconds

        Returns:
            Exit code of container

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If wait fails or times out
        """
        try:
            container = self.client.containers.get(container_id)
            result = container.wait(timeout=timeout)
            exit_code = result.get("StatusCode", -1)
            logger.info(f"Container {container.short_id} exited with code {exit_code}")
            return exit_code
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to wait for container: {e}") from e

    # ========================================================================
    # Container Information & Inspection
    # ========================================================================

    def get_container(self, container_id: str) -> ContainerInfo:
        """
        Get detailed container information.

        Args:
            container_id: Container ID or name

        Returns:
            Container information object

        Raises:
            ContainerNotFoundError: If container not found
        """
        try:
            container = self.client.containers.get(container_id)
            attrs = container.attrs

            # Parse timestamps
            created = datetime.fromisoformat(attrs["Created"].replace("Z", "+00:00"))

            state = attrs.get("State", {})
            started_at = None
            finished_at = None

            if state.get("StartedAt"):
                started_at = datetime.fromisoformat(
                    state["StartedAt"].replace("Z", "+00:00")
                )
            if state.get("FinishedAt"):
                finished_at = datetime.fromisoformat(
                    state["FinishedAt"].replace("Z", "+00:00")
                )

            # Extract network information
            networks = list(attrs.get("NetworkSettings", {}).get("Networks", {}).keys())

            # Extract port mappings
            ports = attrs.get("NetworkSettings", {}).get("Ports", {})

            # Extract mounts
            mounts = attrs.get("Mounts", [])

            return ContainerInfo(
                id=container.id,
                name=container.name.lstrip("/"),
                short_id=container.short_id,
                status=container.status,
                state=state.get("Status", "unknown"),
                image=attrs.get("Config", {}).get("Image", ""),
                created=created,
                started_at=started_at,
                finished_at=finished_at,
                exit_code=state.get("ExitCode"),
                labels=attrs.get("Config", {}).get("Labels", {}),
                networks=networks,
                ports=ports,
                mounts=mounts,
                platform=attrs.get("Platform", "unknown"),
            )
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e

    def list_containers(
        self,
        all: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[ContainerInfo]:
        """
        List containers with optional filtering.

        Args:
            all: Show all containers (default shows just running)
            filters: Filter containers (e.g., {"status": "running"})
            limit: Limit number of results

        Returns:
            List of container information objects

        Examples:
            >>> # List running containers
            >>> containers = manager.list_containers()
            >>>
            >>> # List all containers with label
            >>> containers = manager.list_containers(
            ...     all=True,
            ...     filters={"label": "env=production"}
            ... )
        """
        try:
            containers = self.client.containers.list(
                all=all,
                filters=filters,
                limit=limit,
            )
            return [self.get_container(c.id) for c in containers]
        except APIError as e:
            raise ContainerOperationError(f"Failed to list containers: {e}") from e

    def inspect_container(self, container_id: str) -> Dict[str, Any]:
        """
        Get raw container inspection data.

        Args:
            container_id: Container ID or name

        Returns:
            Raw container inspection dictionary

        Raises:
            ContainerNotFoundError: If container not found
        """
        try:
            container = self.client.containers.get(container_id)
            return container.attrs
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e

    # ========================================================================
    # Container Logs
    # ========================================================================

    def get_logs(
        self,
        container_id: str,
        stdout: bool = True,
        stderr: bool = True,
        timestamps: bool = False,
        tail: Optional[int] = None,
        since: Optional[Union[datetime, int]] = None,
        until: Optional[Union[datetime, int]] = None,
    ) -> str:
        """
        Get container logs.

        Args:
            container_id: Container ID or name
            stdout: Include stdout
            stderr: Include stderr
            timestamps: Include timestamps
            tail: Number of lines from end (None for all)
            since: Show logs since timestamp/seconds
            until: Show logs until timestamp/seconds

        Returns:
            Container logs as string

        Raises:
            ContainerNotFoundError: If container not found
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(
                stdout=stdout,
                stderr=stderr,
                timestamps=timestamps,
                tail=tail,
                since=since,
                until=until,
            )
            return logs.decode("utf-8")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to get logs: {e}") from e

    def stream_logs(
        self,
        container_id: str,
        follow: bool = True,
        stdout: bool = True,
        stderr: bool = True,
        timestamps: bool = False,
        tail: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """
        Stream container logs in real-time.

        Args:
            container_id: Container ID or name
            follow: Follow log output
            stdout: Include stdout
            stderr: Include stderr
            timestamps: Include timestamps
            tail: Number of lines from end to start with

        Yields:
            Log lines as strings

        Raises:
            ContainerNotFoundError: If container not found

        Examples:
            >>> for log_line in manager.stream_logs(container_id):
            ...     print(log_line, end='')
        """
        try:
            container = self.client.containers.get(container_id)
            for log_line in container.logs(
                stream=True,
                follow=follow,
                stdout=stdout,
                stderr=stderr,
                timestamps=timestamps,
                tail=tail,
            ):
                yield log_line.decode("utf-8")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to stream logs: {e}") from e

    # ========================================================================
    # Container Exec Operations
    # ========================================================================

    def exec_run(
        self,
        container_id: str,
        cmd: Union[str, List[str]],
        stdout: bool = True,
        stderr: bool = True,
        stdin: bool = False,
        tty: bool = False,
        privileged: bool = False,
        user: str = "",
        environment: Optional[Dict[str, str]] = None,
        workdir: Optional[str] = None,
        detach: bool = False,
    ) -> Tuple[int, str]:
        """
        Execute a command in a running container.

        Args:
            container_id: Container ID or name
            cmd: Command to execute
            stdout: Attach to stdout
            stderr: Attach to stderr
            stdin: Attach to stdin
            tty: Allocate pseudo-TTY
            privileged: Run as privileged
            user: User to run as
            environment: Environment variables
            workdir: Working directory
            detach: Detach from exec (return immediately)

        Returns:
            Tuple of (exit_code, output)

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If exec fails

        Examples:
            >>> exit_code, output = manager.exec_run(
            ...     container_id,
            ...     ["ls", "-la", "/app"],
            ...     user="root"
            ... )
            >>> print(f"Exit code: {exit_code}")
            >>> print(output)
        """
        try:
            container = self.client.containers.get(container_id)
            result = container.exec_run(
                cmd=cmd,
                stdout=stdout,
                stderr=stderr,
                stdin=stdin,
                tty=tty,
                privileged=privileged,
                user=user,
                environment=environment,
                workdir=workdir,
                detach=detach,
            )

            if detach:
                return 0, ""

            exit_code = result.exit_code
            output = result.output.decode("utf-8") if result.output else ""
            return exit_code, output
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to exec command: {e}") from e

    # ========================================================================
    # Container Statistics
    # ========================================================================

    def get_container_stats(
        self, container_id: str, stream: bool = False
    ) -> ContainerStats:
        """
        Get container resource usage statistics.

        Args:
            container_id: Container ID or name
            stream: Stream statistics (yields updates)

        Returns:
            Container statistics object

        Raises:
            ContainerNotFoundError: If container not found

        Examples:
            >>> stats = manager.get_container_stats(container_id)
            >>> print(f"CPU: {stats.cpu_percent:.2f}%")
            >>> print(f"Memory: {stats.memory_usage_mb:.2f}MB / "
            ...       f"{stats.memory_limit_mb:.2f}MB "
            ...       f"({stats.memory_percent:.2f}%)")
        """
        try:
            container = self.client.containers.get(container_id)
            stats_obj = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = (
                stats_obj["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats_obj["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats_obj["cpu_stats"]["system_cpu_usage"]
                - stats_obj["precpu_stats"]["system_cpu_usage"]
            )
            cpu_count = stats_obj["cpu_stats"]["online_cpus"]

            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0

            # Memory stats
            memory_stats = stats_obj["memory_stats"]
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit * 100.0) if memory_limit > 0 else 0.0
            )

            # Network stats
            networks = stats_obj.get("networks", {})
            network_rx = sum(net.get("rx_bytes", 0) for net in networks.values())
            network_tx = sum(net.get("tx_bytes", 0) for net in networks.values())

            # Block I/O stats
            blkio_stats = stats_obj.get("blkio_stats", {})
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])
            block_read = sum(
                entry.get("value", 0)
                for entry in io_service_bytes
                if entry.get("op") == "Read"
            )
            block_write = sum(
                entry.get("value", 0)
                for entry in io_service_bytes
                if entry.get("op") == "Write"
            )

            # PIDs
            pids = stats_obj.get("pids_stats", {}).get("current", 0)

            return ContainerStats(
                container_id=container.id,
                container_name=container.name.lstrip("/"),
                cpu_percent=round(cpu_percent, 2),
                memory_usage_mb=round(memory_usage / 1024 / 1024, 2),
                memory_limit_mb=round(memory_limit / 1024 / 1024, 2),
                memory_percent=round(memory_percent, 2),
                network_rx_mb=round(network_rx / 1024 / 1024, 2),
                network_tx_mb=round(network_tx / 1024 / 1024, 2),
                block_read_mb=round(block_read / 1024 / 1024, 2),
                block_write_mb=round(block_write / 1024 / 1024, 2),
                pids=pids,
            )
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except (APIError, KeyError) as e:
            raise ContainerOperationError(f"Failed to get stats: {e}") from e

    def stream_container_stats(
        self, container_id: str, interval: float = 1.0
    ) -> Generator[ContainerStats, None, None]:
        """
        Stream container statistics in real-time.

        Args:
            container_id: Container ID or name
            interval: Update interval in seconds

        Yields:
            ContainerStats objects

        Raises:
            ContainerNotFoundError: If container not found

        Examples:
            >>> for stats in manager.stream_container_stats(container_id):
            ...     print(f"CPU: {stats.cpu_percent}%, MEM: {stats.memory_usage_mb}MB")
            ...     if stats.cpu_percent > 80:
            ...         break
        """
        while True:
            try:
                stats = self.get_container_stats(container_id)
                yield stats
                time.sleep(interval)
            except ContainerNotFoundError:
                logger.warning(f"Container {container_id} no longer exists")
                break
            except Exception as e:
                logger.error(f"Error streaming stats: {e}")
                break

    # ========================================================================
    # Network Operations
    # ========================================================================

    def connect_network(
        self,
        container_id: str,
        network: str,
        aliases: Optional[List[str]] = None,
        ipv4_address: Optional[str] = None,
        ipv6_address: Optional[str] = None,
    ) -> None:
        """
        Connect container to a network.

        Args:
            container_id: Container ID or name
            network: Network name or ID
            aliases: Network aliases for container
            ipv4_address: Static IPv4 address
            ipv6_address: Static IPv6 address

        Raises:
            ContainerNotFoundError: If container not found
            ContainerNetworkError: If connection fails
        """
        try:
            net = self.client.networks.get(network)
            net.connect(
                container_id,
                aliases=aliases,
                ipv4_address=ipv4_address,
                ipv6_address=ipv6_address,
            )
            logger.info(f"Connected container {container_id} to network {network}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container or network not found: {e}") from e
        except APIError as e:
            raise ContainerNetworkError(f"Failed to connect to network: {e}") from e

    def disconnect_network(
        self, container_id: str, network: str, force: bool = False
    ) -> None:
        """
        Disconnect container from a network.

        Args:
            container_id: Container ID or name
            network: Network name or ID
            force: Force disconnection

        Raises:
            ContainerNotFoundError: If container not found
            ContainerNetworkError: If disconnection fails
        """
        try:
            net = self.client.networks.get(network)
            net.disconnect(container_id, force=force)
            logger.info(f"Disconnected container {container_id} from network {network}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container or network not found: {e}") from e
        except APIError as e:
            raise ContainerNetworkError(
                f"Failed to disconnect from network: {e}"
            ) from e

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def prune_containers(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Remove all stopped containers.

        Args:
            filters: Filters to apply (e.g., {"until": "24h"})

        Returns:
            Dictionary with pruning results (containers deleted, space reclaimed)

        Examples:
            >>> # Remove containers stopped more than 24 hours ago
            >>> result = manager.prune_containers(filters={"until": "24h"})
            >>> print(f"Removed {len(result['ContainersDeleted'])} containers")
            >>> print(f"Reclaimed {result['SpaceReclaimed']} bytes")
        """
        try:
            result = self.client.containers.prune(filters=filters)
            deleted = result.get("ContainersDeleted") or []
            space = result.get("SpaceReclaimed", 0)
            logger.info(
                f"Pruned {len(deleted)} containers, "
                f"reclaimed {space / 1024 / 1024:.2f}MB"
            )
            return result
        except APIError as e:
            raise ContainerOperationError(f"Failed to prune containers: {e}") from e

    def commit_container(
        self,
        container_id: str,
        repository: str,
        tag: str = "latest",
        message: str = "",
        author: str = "",
        changes: Optional[str] = None,
        pause: bool = True,
    ) -> str:
        """
        Create a new image from a container's changes.

        Args:
            container_id: Container ID or name
            repository: Repository name for new image
            tag: Tag for new image
            message: Commit message
            author: Author of commit
            changes: Dockerfile instructions to apply
            pause: Pause container during commit

        Returns:
            New image ID

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If commit fails
        """
        try:
            container = self.client.containers.get(container_id)
            image = container.commit(
                repository=repository,
                tag=tag,
                message=message,
                author=author,
                changes=changes,
                pause=pause,
            )
            logger.info(
                f"Committed container {container.short_id} to {repository}:{tag}"
            )
            return image.id
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to commit container: {e}") from e

    def export_container(
        self, container_id: str, output_path: Union[str, Path]
    ) -> None:
        """
        Export container filesystem as tar archive.

        Args:
            container_id: Container ID or name
            output_path: Path to save tar archive

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If export fails
        """
        try:
            container = self.client.containers.get(container_id)
            output_path = Path(output_path)

            with open(output_path, "wb") as f:
                for chunk in container.export():
                    f.write(chunk)

            logger.info(f"Exported container {container.short_id} to {output_path}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except (APIError, IOError) as e:
            raise ContainerOperationError(f"Failed to export container: {e}") from e

    def rename_container(self, container_id: str, new_name: str) -> None:
        """
        Rename a container.

        Args:
            container_id: Container ID or current name
            new_name: New container name

        Raises:
            ContainerNotFoundError: If container not found
            ContainerOperationError: If rename fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.rename(new_name)
            logger.info(f"Renamed container {container.short_id} to {new_name}")
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to rename container: {e}") from e

    def top_container(
        self, container_id: str, ps_args: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Display running processes in a container.

        Args:
            container_id: Container ID or name
            ps_args: Optional ps arguments (e.g., "aux")

        Returns:
            Dictionary with process information

        Raises:
            ContainerNotFoundError: If container not found

        Examples:
            >>> processes = manager.top_container(container_id)
            >>> for process in processes['Processes']:
            ...     print(f"PID: {process[1]}, CMD: {process[-1]}")
        """
        try:
            container = self.client.containers.get(container_id)
            return container.top(ps_args=ps_args)
        except NotFound as e:
            raise ContainerNotFoundError(f"Container not found: {container_id}") from e
        except APIError as e:
            raise ContainerOperationError(f"Failed to get process list: {e}") from e
