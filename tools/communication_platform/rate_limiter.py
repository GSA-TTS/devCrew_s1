"""
Rate Limiter Module for Communication Platform.

Provides Redis-based distributed rate limiting with sliding window and token bucket
algorithms to prevent API rate limit violations across multiple channels.

Features:
    - Sliding window rate limiting for accurate request counting
    - Token bucket algorithm for burst allowance
    - Per-channel rate limits (Slack, Email, PagerDuty, etc.)
    - Lua scripts for atomic operations
    - Distributed rate limiting with Redis
    - Backpressure handling (queue or reject)
    - Automatic rate limit adjustment
    - Monitoring and alerting

Example:
    >>> from rate_limiter import RateLimiter, RateLimit
    >>> limiter = RateLimiter(redis_url="redis://localhost:6379/0")
    >>> limiter.set_limit("slack", 50, 60)  # 50 messages per minute
    >>> if limiter.check_rate_limit("slack"):
    ...     send_slack_message()
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional

import redis
from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


# Lua script for sliding window rate limiting
# Uses sorted sets to track requests within a time window
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local request_id = ARGV[4]

-- Remove old entries outside the window
local window_start = now - window
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- Count current requests in window
local current = redis.call('ZCARD', key)

-- Check if under limit
if current < limit then
    -- Add new request
    redis.call('ZADD', key, now, request_id)
    -- Set expiry on the key
    redis.call('EXPIRE', key, window)
    return {1, limit - current - 1, window}
else
    -- Get oldest request timestamp to calculate retry_after
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = math.ceil(oldest[2] + window - now)
    return {0, 0, retry_after}
end
"""

# Lua script for token bucket rate limiting
# Supports burst capacity with token replenishment
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill_rate = tonumber(ARGV[3])
local tokens_requested = tonumber(ARGV[4])

-- Get current state or initialize
local state = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(state[1]) or capacity
local last_refill = tonumber(state[2]) or now

-- Calculate tokens to add based on time elapsed
local time_elapsed = now - last_refill
local tokens_to_add = time_elapsed * refill_rate

-- Update token count (capped at capacity)
tokens = math.min(capacity, tokens + tokens_to_add)

-- Check if enough tokens available
if tokens >= tokens_requested then
    -- Consume tokens
    tokens = tokens - tokens_requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)  -- 1 hour expiry
    return {1, math.floor(tokens), 0}
else
    -- Calculate time until enough tokens available
    local tokens_needed = tokens_requested - tokens
    local retry_after = math.ceil(tokens_needed / refill_rate)
    return {0, math.floor(tokens), retry_after}
end
"""

# Lua script for atomic reset
RESET_SCRIPT = """
local key = KEYS[1]
redis.call('DEL', key)
return 1
"""


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class BackpressureStrategy(str, Enum):
    """Strategies for handling rate limit violations."""

    REJECT = "reject"  # Immediately reject the request
    WAIT = "wait"  # Wait until capacity available
    QUEUE = "queue"  # Queue for later processing


class RateLimit(BaseModel):
    """Rate limit configuration for a channel."""

    channel: str = Field(..., description="Channel identifier (e.g., 'slack', 'email')")
    limit: int = Field(..., gt=0, description="Maximum requests allowed")
    window_seconds: int = Field(..., gt=0, description="Time window in seconds")
    algorithm: RateLimitAlgorithm = Field(
        default=RateLimitAlgorithm.SLIDING_WINDOW,
        description="Rate limiting algorithm to use",
    )
    burst_capacity: Optional[int] = Field(
        default=None, description="Burst capacity for token bucket (defaults to limit)"
    )
    backpressure_strategy: BackpressureStrategy = Field(
        default=BackpressureStrategy.REJECT,
        description="Strategy for handling rate limit violations",
    )

    @field_validator("burst_capacity")
    @classmethod
    def validate_burst_capacity(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure burst capacity is not less than limit."""
        if v is not None and "limit" in info.data and v < info.data["limit"]:
            raise ValueError("burst_capacity must be >= limit")
        return v

    def get_burst_capacity(self) -> int:
        """Get burst capacity, defaulting to limit if not set."""
        return self.burst_capacity if self.burst_capacity is not None else self.limit


class RateLimitStatus(BaseModel):
    """Current rate limit status for a channel."""

    channel: str = Field(..., description="Channel identifier")
    allowed: bool = Field(..., description="Whether request is allowed")
    remaining: int = Field(..., ge=0, description="Remaining requests in window")
    retry_after: int = Field(..., ge=0, description="Seconds to wait before retry")
    limit: int = Field(..., gt=0, description="Total limit")
    window_seconds: int = Field(..., gt=0, description="Time window in seconds")
    reset_at: datetime = Field(..., description="When the window resets")


class RateLimiterError(Exception):
    """Base exception for rate limiter errors."""

    pass


class RateLimitExceeded(RateLimiterError):
    """Raised when rate limit is exceeded."""

    def __init__(self, channel: str, retry_after: int):
        """Initialize with channel and retry information."""
        self.channel = channel
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for channel '{channel}'. "
            f"Retry after {retry_after} seconds."
        )


class RateLimiter:
    """
    Redis-based distributed rate limiter.

    Supports multiple rate limiting algorithms and per-channel limits
    to prevent API rate limit violations.

    Attributes:
        redis_client: Redis client for distributed state
        limits: Dictionary of channel rate limit configurations
        default_limits: Default limits for common channels
    """

    # Default rate limits for common channels (requests per minute)
    DEFAULT_LIMITS = {
        "slack": RateLimit(
            channel="slack",
            limit=50,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            burst_capacity=60,
        ),
        "email": RateLimit(
            channel="email",
            limit=100,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_capacity=120,
        ),
        "pagerduty": RateLimit(
            channel="pagerduty",
            limit=60,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            burst_capacity=70,
        ),
        "teams": RateLimit(
            channel="teams",
            limit=40,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            burst_capacity=50,
        ),
    }

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "ratelimit",
        enable_monitoring: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for Redis keys
            enable_monitoring: Enable rate limit monitoring

        Raises:
            RateLimiterError: If Redis connection fails
        """
        self.key_prefix = key_prefix
        self.enable_monitoring = enable_monitoring
        self.limits: Dict[str, RateLimit] = self.DEFAULT_LIMITS.copy()

        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RateLimiterError(f"Redis connection failed: {e}") from e

        # Register Lua scripts
        try:
            self._sliding_window_sha = self.redis_client.script_load(
                SLIDING_WINDOW_SCRIPT
            )
            self._token_bucket_sha = self.redis_client.script_load(TOKEN_BUCKET_SCRIPT)
            self._reset_sha = self.redis_client.script_load(RESET_SCRIPT)
            logger.debug("Lua scripts loaded successfully")
        except redis.RedisError as e:
            logger.error(f"Failed to load Lua scripts: {e}")
            raise RateLimiterError(f"Failed to load Lua scripts: {e}") from e

    def _get_key(self, channel: str) -> str:
        """Get Redis key for a channel."""
        return f"{self.key_prefix}:{channel}"

    def set_limit(
        self,
        channel: str,
        limit: int,
        window_seconds: int,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        burst_capacity: Optional[int] = None,
        backpressure_strategy: BackpressureStrategy = BackpressureStrategy.REJECT,
    ) -> bool:
        """
        Configure rate limit for a channel.

        Args:
            channel: Channel identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            algorithm: Rate limiting algorithm
            burst_capacity: Burst capacity (for token bucket)
            backpressure_strategy: Strategy for handling violations

        Returns:
            True if limit was set successfully

        Raises:
            ValueError: If limit parameters are invalid
        """
        try:
            rate_limit = RateLimit(
                channel=channel,
                limit=limit,
                window_seconds=window_seconds,
                algorithm=algorithm,
                burst_capacity=burst_capacity,
                backpressure_strategy=backpressure_strategy,
            )
            self.limits[channel] = rate_limit
            logger.info(f"Set rate limit for {channel}: {limit}/{window_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Failed to set rate limit for {channel}: {e}")
            raise ValueError(f"Invalid rate limit parameters: {e}") from e

    def check_rate_limit(
        self,
        channel: str,
        tokens: int = 1,
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            channel: Channel identifier
            tokens: Number of tokens to consume (default: 1)
            request_id: Unique request identifier (generated if not provided)

        Returns:
            True if request is allowed, False otherwise

        Raises:
            RateLimiterError: If rate limit check fails
        """
        try:
            status = self.get_status(channel, tokens, request_id)
            return status.allowed
        except Exception as e:
            logger.error(f"Rate limit check failed for {channel}: {e}")
            raise RateLimiterError(f"Rate limit check failed for {channel}: {e}") from e

    def get_status(
        self,
        channel: str,
        tokens: int = 1,
        request_id: Optional[str] = None,
    ) -> RateLimitStatus:
        """
        Get current rate limit status and consume tokens if allowed.

        Args:
            channel: Channel identifier
            tokens: Number of tokens to consume
            request_id: Unique request identifier

        Returns:
            RateLimitStatus with current state

        Raises:
            RateLimiterError: If status check fails
        """
        # Get rate limit config
        if channel not in self.limits:
            logger.warning(f"No rate limit configured for {channel}, using default")
            # Create a default limit
            self.limits[channel] = RateLimit(
                channel=channel,
                limit=100,
                window_seconds=60,
            )

        limit_config = self.limits[channel]
        key = self._get_key(channel)
        now = time.time()
        request_id = request_id or f"{channel}:{now}"

        try:
            if limit_config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                result = self.redis_client.evalsha(
                    self._sliding_window_sha,
                    1,
                    key,
                    now,
                    limit_config.window_seconds,
                    limit_config.limit,
                    request_id,
                )
            else:  # TOKEN_BUCKET
                refill_rate = limit_config.limit / limit_config.window_seconds
                result = self.redis_client.evalsha(
                    self._token_bucket_sha,
                    1,
                    key,
                    now,
                    limit_config.get_burst_capacity(),
                    refill_rate,
                    tokens,
                )

            allowed = bool(result[0])
            remaining = int(result[1])
            retry_after = int(result[2])

            # Calculate reset time
            reset_at = datetime.now() + timedelta(
                seconds=retry_after if not allowed else limit_config.window_seconds
            )

            status = RateLimitStatus(
                channel=channel,
                allowed=allowed,
                remaining=remaining,
                retry_after=retry_after,
                limit=limit_config.limit,
                window_seconds=limit_config.window_seconds,
                reset_at=reset_at,
            )

            # Monitor rate limit usage
            if self.enable_monitoring:
                self._record_usage(channel, allowed, remaining)

            return status

        except redis.RedisError as e:
            logger.error(f"Redis error checking rate limit for {channel}: {e}")
            raise RateLimiterError(f"Redis error: {e}") from e

    def reset_limit(self, channel: str) -> bool:
        """
        Reset rate limit for a channel.

        Args:
            channel: Channel identifier

        Returns:
            True if reset successful

        Raises:
            RateLimiterError: If reset fails
        """
        key = self._get_key(channel)
        try:
            result = self.redis_client.evalsha(self._reset_sha, 1, key)
            logger.info(f"Reset rate limit for {channel}")
            return bool(result)
        except redis.RedisError as e:
            logger.error(f"Failed to reset rate limit for {channel}: {e}")
            raise RateLimiterError(f"Failed to reset: {e}") from e

    def wait_for_capacity(
        self,
        channel: str,
        timeout: int = 60,
        tokens: int = 1,
    ) -> bool:
        """
        Wait until capacity is available or timeout.

        Args:
            channel: Channel identifier
            timeout: Maximum seconds to wait
            tokens: Number of tokens needed

        Returns:
            True if capacity became available, False if timeout

        Raises:
            RateLimiterError: If wait operation fails
        """
        start_time = time.time()
        request_id = f"{channel}:{start_time}"

        while time.time() - start_time < timeout:
            try:
                status = self.get_status(channel, tokens, request_id)
                if status.allowed:
                    return True

                # Wait for the calculated retry_after time or 1 second minimum
                wait_time = min(max(status.retry_after, 1), timeout)
                logger.debug(f"Rate limit reached for {channel}, waiting {wait_time}s")
                time.sleep(wait_time)

            except RateLimiterError as e:
                logger.error(f"Error while waiting for capacity: {e}")
                raise

        logger.warning(f"Timeout waiting for capacity on {channel}")
        return False

    def get_limit_config(self, channel: str) -> Optional[RateLimit]:
        """
        Get rate limit configuration for a channel.

        Args:
            channel: Channel identifier

        Returns:
            RateLimit configuration or None if not configured
        """
        return self.limits.get(channel)

    def _record_usage(self, channel: str, allowed: bool, remaining: int) -> None:
        """
        Record rate limit usage for monitoring.

        Args:
            channel: Channel identifier
            allowed: Whether request was allowed
            remaining: Remaining capacity
        """
        try:
            # Store metrics in Redis with 24-hour expiry
            metrics_key = f"{self.key_prefix}:metrics:{channel}"
            now = datetime.now().isoformat()

            self.redis_client.hincrby(metrics_key, "total_requests", 1)
            if allowed:
                self.redis_client.hincrby(metrics_key, "allowed_requests", 1)
            else:
                self.redis_client.hincrby(metrics_key, "rejected_requests", 1)

            self.redis_client.hset(metrics_key, "last_check", now)
            self.redis_client.hset(metrics_key, "last_remaining", remaining)
            self.redis_client.expire(metrics_key, 86400)  # 24 hours

        except redis.RedisError as e:
            # Don't fail the rate limit check due to monitoring errors
            logger.warning(f"Failed to record usage metrics: {e}")

    def get_metrics(self, channel: str) -> Dict[str, int]:
        """
        Get usage metrics for a channel.

        Args:
            channel: Channel identifier

        Returns:
            Dictionary with usage metrics
        """
        metrics_key = f"{self.key_prefix}:metrics:{channel}"
        try:
            metrics = self.redis_client.hgetall(metrics_key)
            return {
                "total_requests": int(metrics.get("total_requests", 0)),
                "allowed_requests": int(metrics.get("allowed_requests", 0)),
                "rejected_requests": int(metrics.get("rejected_requests", 0)),
                "last_remaining": int(metrics.get("last_remaining", 0)),
            }
        except (redis.RedisError, ValueError) as e:
            logger.error(f"Failed to get metrics for {channel}: {e}")
            return {
                "total_requests": 0,
                "allowed_requests": 0,
                "rejected_requests": 0,
                "last_remaining": 0,
            }

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self.redis_client.close()
            logger.info("Redis connection closed")
        except redis.RedisError as e:
            logger.warning(f"Error closing Redis connection: {e}")
