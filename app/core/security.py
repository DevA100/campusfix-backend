"""
Password hashing and JWT token creation/verification.

Uses bcrypt directly for password hashing to avoid passlib's backend detection issues.
"""

from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from app.config import settings


def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        plain_password: The password to hash

    Returns:
        str: The hashed password (bcrypt hash string)

    Example:
        >>> hash_password("my_password")
        '$2b$12$abcdefghijklmnopqrstuvwxyz...'
    """
    # Convert password to bytes
    password_bytes = plain_password.encode('utf-8')

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string (not bytes)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.

    Args:
        plain_password: The password to verify
        hashed_password: The stored bcrypt hash

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> verify_password("my_password", stored_hash)
        True
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        # Invalid hash format or other error
        return False


def create_access_token(subject: str, role: str) -> str:
    """
    Create a JWT access token.

    Args:
        subject: User identifier (email or ID)
        role: User role

    Returns:
        str: JWT token

    Example:
        >>> token = create_access_token("user@example.com", "ADMIN")
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        dict: Decoded payload

    Raises:
        jose.JWTError: On invalid or expired token

    Example:
        >>> payload = decode_access_token(token)
        >>> user_email = payload.get("sub")
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
