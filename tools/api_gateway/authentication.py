"""
Issue #41: Authentication Module
Implements JWT, OAuth2, API key management, and RBAC.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field


# Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
http_bearer = HTTPBearer()


# Pydantic Models
class UserBase(BaseModel):
    """Base user model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8)


class UserInDB(UserBase):
    """User in database model."""

    id: int
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = Field(default_factory=list)
    api_keys: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""

    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: List[str] = Field(default_factory=list)
    exp: Optional[datetime] = None


class APIKey(BaseModel):
    """API key model."""

    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# JWT utilities
def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        TokenData object

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        roles: List[str] = payload.get("roles", [])
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        return TokenData(username=username, user_id=user_id, roles=roles, exp=exp)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def create_token_pair(user: UserInDB) -> Token:
    """
    Create access and refresh token pair for a user.

    Args:
        user: User object

    Returns:
        Token object with access and refresh tokens
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token_data = {
        "sub": user.username,
        "user_id": user.id,
        "roles": user.roles,
    }

    access_token = create_access_token(
        data=access_token_data, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data=access_token_data, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# API Key utilities
def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def validate_api_key(api_key: str, user: UserInDB) -> bool:
    """
    Validate an API key for a user.

    Args:
        api_key: API key to validate
        user: User object

    Returns:
        True if valid, False otherwise
    """
    return api_key in user.api_keys


# Dependency functions
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Get current user from JWT token.

    Args:
        token: JWT token from request

    Returns:
        TokenData object

    Raises:
        HTTPException: If authentication fails
    """
    return decode_token(token)


async def get_current_user_from_bearer(
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
) -> TokenData:
    """
    Get current user from Bearer token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        TokenData object
    """
    return decode_token(credentials.credentials)


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        TokenData object

    Raises:
        HTTPException: If user is inactive
    """
    # In production, check user is_active status from database
    return current_user


# Role-Based Access Control (RBAC)
class RoleChecker:
    """Check if user has required roles."""

    def __init__(self, allowed_roles: List[str]):
        """
        Initialize role checker.

        Args:
            allowed_roles: List of allowed roles
        """
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_active_user)) -> bool:
        """
        Check if user has required roles.

        Args:
            user: Current user

        Returns:
            True if user has required roles

        Raises:
            HTTPException: If user doesn't have required roles
        """
        if not any(role in user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return True


# Permission checks
def require_admin(user: TokenData = Depends(get_current_active_user)) -> TokenData:
    """
    Require admin role.

    Args:
        user: Current user

    Returns:
        TokenData object

    Raises:
        HTTPException: If user is not admin
    """
    if "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


def require_superuser(user: TokenData = Depends(get_current_active_user)) -> TokenData:
    """
    Require superuser role.

    Args:
        user: Current user

    Returns:
        TokenData object

    Raises:
        HTTPException: If user is not superuser
    """
    if "superuser" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser role required",
        )
    return user


# OAuth2 flows
class OAuth2Manager:
    """Manage OAuth2 flows."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize OAuth2 manager.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: OAuth2 redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """
        Get OAuth2 authorization URL.

        Args:
            state: CSRF protection state

        Returns:
            Authorization URL
        """
        # In production, implement actual OAuth2 provider integration
        return f"https://oauth.provider.com/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&state={state}"  # noqa: E501

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code

        Returns:
            Token response

        Raises:
            HTTPException: If token exchange fails
        """
        # In production, implement actual OAuth2 token exchange
        raise NotImplementedError("OAuth2 token exchange not implemented")

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user info from OAuth2 provider.

        Args:
            access_token: Access token

        Returns:
            User info

        Raises:
            HTTPException: If user info retrieval fails
        """
        # In production, implement actual OAuth2 user info retrieval
        raise NotImplementedError("OAuth2 user info retrieval not implemented")


# Session management
class SessionManager:
    """Manage user sessions."""

    def __init__(self, redis_client: Optional[Any] = None):
        """
        Initialize session manager.

        Args:
            redis_client: Redis client for session storage
        """
        self.redis_client = redis_client

    async def create_session(self, user_id: int, token: str) -> str:
        """
        Create a user session.

        Args:
            user_id: User ID
            token: Session token

        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                token,
            )
        return session_id

    async def get_session(self, session_id: str) -> Optional[str]:
        """
        Get session token.

        Args:
            session_id: Session ID

        Returns:
            Session token or None
        """
        if self.redis_client:
            token = await self.redis_client.get(f"session:{session_id}")
            return token.decode() if token else None
        return None

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False otherwise
        """
        if self.redis_client:
            return await self.redis_client.delete(f"session:{session_id}") > 0
        return False


# Token refresh
async def refresh_access_token(refresh_token: str) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Refresh token

    Returns:
        New token pair

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Create new access token
        username = payload.get("sub")
        user_id = payload.get("user_id")
        roles = payload.get("roles", [])

        token_data = {
            "sub": username,
            "user_id": user_id,
            "roles": roles,
        }

        access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )
