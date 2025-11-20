"""
Issue #41: Rate Limiter Module
Implements Redis-based rate limiting for API endpoints.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field
from redis import Redis
from redis.asyncio import Redis as AsyncRedis


class RateLimitConfig(BaseModel):
    """Rate limit configuration."""

    max_requests: int = Field(..., gt=0, description="Maximum requests allowed")
    window_seconds: int = Field(..., gt=0, description="Time window in seconds")
    block_duration_seconds: int = Field(
        default=300, description="Block duration on limit exceeded"
    )


class RateLimitInfo(BaseModel):
    """Rate limit information."""

    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None


class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        async_redis_client: Optional[AsyncRedis] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_client: Synchronous Redis client
            async_redis_client: Asynchronous Redis client
        """
        self.redis_client = redis_client
        self.async_redis_client = async_redis_client

    def _get_key(self, identifier: str, limit_type: str) -> str:
        """
        Generate Redis key for rate limiting.

        Args:
            identifier: User ID, IP address, or API key
            limit_type: Type of rate limit

        Returns:
            Redis key
        """
        return f"ratelimit:{limit_type}:{identifier}"

    def _get_block_key(self, identifier: str, limit_type: str) -> str:
        """
        Generate Redis key for blocked identifiers.

        Args:
            identifier: User ID, IP address, or API key
            limit_type: Type of rate limit

        Returns:
            Redis block key
        """
        return f"ratelimit:blocked:{limit_type}:{identifier}"

    def check_rate_limit(
        self, identifier: str, config: RateLimitConfig, limit_type: str = "default"
    ) -> Tuple[bool, RateLimitInfo]:
        """
        Check if request is within rate limit (synchronous).

        Args:
            identifier: User ID, IP address, or API key
            config: Rate limit configuration
            limit_type: Type of rate limit

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        if not self.redis_client:
            # No Redis client, allow request
            return True, RateLimitInfo(
                limit=config.max_requests,
                remaining=config.max_requests,
                reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            )

        key = self._get_key(identifier, limit_type)
        block_key = self._get_block_key(identifier, limit_type)

        # Check if identifier is blocked
        if self.redis_client.exists(block_key):
            ttl = self.redis_client.ttl(block_key)
            return False, RateLimitInfo(
                limit=config.max_requests,
                remaining=0,
                reset_at=datetime.utcnow() + timedelta(seconds=ttl),
                retry_after=ttl,
            )

        # Increment request count
        current = self.redis_client.incr(key)

        # Set expiration on first request
        if current == 1:
            self.redis_client.expire(key, config.window_seconds)

        # Get TTL for reset time
        ttl = self.redis_client.ttl(key)
        reset_at = datetime.utcnow() + timedelta(seconds=ttl)

        remaining = max(0, config.max_requests - current)

        # Check if limit exceeded
        if current > config.max_requests:
            # Block the identifier
            self.redis_client.setex(
                block_key, config.block_duration_seconds, "blocked"
            )
            return False, RateLimitInfo(
                limit=config.max_requests,
                remaining=0,
                reset_at=reset_at,
                retry_after=config.block_duration_seconds,
            )

        return True, RateLimitInfo(
            limit=config.max_requests, remaining=remaining, reset_at=reset_at
        )

    async def acheck_rate_limit(
        self, identifier: str, config: RateLimitConfig, limit_type: str = "default"
    ) -> Tuple[bool, RateLimitInfo]:
        """
        Check if request is within rate limit (asynchronous).

        Args:
            identifier: User ID, IP address, or API key
            config: Rate limit configuration
            limit_type: Type of rate limit

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        if not self.async_redis_client:
            # No Redis client, allow request
            return True, RateLimitInfo(
                limit=config.max_requests,
                remaining=config.max_requests,
                reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            )

        key = self._get_key(identifier, limit_type)
        block_key = self._get_block_key(identifier, limit_type)

        # Check if identifier is blocked
        if await self.async_redis_client.exists(block_key):
            ttl = await self.async_redis_client.ttl(block_key)
            return False, RateLimitInfo(
                limit=config.max_requests,
                remaining=0,
                reset_at=datetime.utcnow() + timedelta(seconds=ttl),
                retry_after=ttl,
            )

        # Increment request count
        current = await self.async_redis_client.incr(key)

        # Set expiration on first request
        if current == 1:
            await self.async_redis_client.expire(key, config.window_seconds)

        # Get TTL for reset time
        ttl = await self.async_redis_client.ttl(key)
        reset_at = datetime.utcnow() + timedelta(seconds=ttl)

        remaining = max(0, config.max_requests - current)

        # Check if limit exceeded
        if current > config.max_requests:
            # Block the identifier
            await self.async_redis_client.setex(
                block_key, config.block_duration_seconds, "blocked"
            )
            return False, RateLimitInfo(
                limit=config.max_requests,
                remaining=0,
                reset_at=reset_at,
                retry_after=config.block_duration_seconds,
            )

        return True, RateLimitInfo(
            limit=config.max_requests, remaining=remaining, reset_at=reset_at
        )

    def reset_rate_limit(self, identifier: str, limit_type: str = "default") -> bool:
        """
        Reset rate limit for an identifier.

        Args:
            identifier: User ID, IP address, or API key
            limit_type: Type of rate limit

        Returns:
            True if reset, False otherwise
        """
        if not self.redis_client:
            return False

        key = self._get_key(identifier, limit_type)
        block_key = self._get_block_key(identifier, limit_type)

        deleted = 0
        deleted += self.redis_client.delete(key)
        deleted += self.redis_client.delete(block_key)

        return deleted > 0

    async def areset_rate_limit(
        self, identifier: str, limit_type: str = "default"
    ) -> bool:
        """
        Reset rate limit for an identifier (async).

        Args:
            identifier: User ID, IP address, or API key
            limit_type: Type of rate limit

        Returns:
            True if reset, False otherwise
        """
        if not self.async_redis_client:
            return False

        key = self._get_key(identifier, limit_type)
        block_key = self._get_block_key(identifier, limit_type)

        deleted = 0
        deleted += await self.async_redis_client.delete(key)
        deleted += await self.async_redis_client.delete(block_key)

        return deleted > 0


# Rate limit configurations
RATE_LIMITS = {
    "per_user": RateLimitConfig(max_requests=1000, window_seconds=3600),  # 1000/hour
    "per_ip": RateLimitConfig(max_requests=100, window_seconds=60),  # 100/minute
    "global": RateLimitConfig(
        max_requests=10000, window_seconds=60
    ),  # 10000/minute
    "auth": RateLimitConfig(max_requests=5, window_seconds=300),  # 5/5min
    "write": RateLimitConfig(max_requests=100, window_seconds=3600),  # 100/hour
    "read": RateLimitConfig(max_requests=1000, window_seconds=3600),  # 1000/hour
}


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier from request.

    Args:
        request: FastAPI request

    Returns:
        Client identifier (IP address or user ID)
    """
    # Try to get user ID from request state
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"

    # Fall back to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        config: RateLimitConfig,
        limit_type: str = "default",
    ):
        """
        Initialize rate limit middleware.

        Args:
            rate_limiter: RateLimiter instance
            config: Rate limit configuration
            limit_type: Type of rate limit
        """
        self.rate_limiter = rate_limiter
        self.config = config
        self.limit_type = limit_type

    async def __call__(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware

        Returns:
            Response

        Raises:
            HTTPException: If rate limit exceeded
        """
        identifier = get_client_identifier(request)

        allowed, info = await self.rate_limiter.acheck_rate_limit(
            identifier, self.config, self.limit_type
        )

        # Add rate limit headers
        request.state.rate_limit_info = info

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info.limit),
                    "X-RateLimit-Remaining": str(info.remaining),
                    "X-RateLimit-Reset": str(int(info.reset_at.timestamp())),
                    "Retry-After": str(info.retry_after or 0),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(info.limit)
        response.headers["X-RateLimit-Remaining"] = str(info.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(info.reset_at.timestamp()))

        return response


# Decorator for rate limiting endpoints
def rate_limit(
    config: RateLimitConfig,
    limit_type: str = "default",
    rate_limiter: Optional[RateLimiter] = None,
):
    """
    Decorator for rate limiting specific endpoints.

    Args:
        config: Rate limit configuration
        limit_type: Type of rate limit
        rate_limiter: RateLimiter instance

    Returns:
        Decorator function
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if rate_limiter:
                identifier = get_client_identifier(request)
                allowed, info = await rate_limiter.acheck_rate_limit(
                    identifier, config, limit_type
                )

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={
                            "X-RateLimit-Limit": str(info.limit),
                            "X-RateLimit-Remaining": str(info.remaining),
                            "X-RateLimit-Reset": str(int(info.reset_at.timestamp())),
                            "Retry-After": str(info.retry_after or 0),
                        },
                    )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# Quota management
class QuotaManager:
    """Manage API quotas."""

    def __init__(self, redis_client: Optional[AsyncRedis] = None):
        """
        Initialize quota manager.

        Args:
            redis_client: Asynchronous Redis client
        """
        self.redis_client = redis_client

    async def get_quota(self, user_id: int) -> Dict[str, Any]:
        """
        Get user quota information.

        Args:
            user_id: User ID

        Returns:
            Quota information
        """
        if not self.redis_client:
            return {"requests": 0, "limit": 10000, "reset_at": None}

        key = f"quota:{user_id}"
        requests = await self.redis_client.get(key)

        return {
            "requests": int(requests) if requests else 0,
            "limit": 10000,
            "reset_at": datetime.utcnow() + timedelta(days=30),
        }

    async def increment_quota(self, user_id: int) -> int:
        """
        Increment user quota.

        Args:
            user_id: User ID

        Returns:
            Current quota usage
        """
        if not self.redis_client:
            return 0

        key = f"quota:{user_id}"
        current = await self.redis_client.incr(key)

        # Set expiration to 30 days
        if current == 1:
            await self.redis_client.expire(key, 30 * 24 * 3600)

        return current

    async def reset_quota(self, user_id: int) -> bool:
        """
        Reset user quota.

        Args:
            user_id: User ID

        Returns:
            True if reset, False otherwise
        """
        if not self.redis_client:
            return False

        key = f"quota:{user_id}"
        return await self.redis_client.delete(key) > 0
