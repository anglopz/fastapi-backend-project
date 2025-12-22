"""
General utilities for the application
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.config import security_settings

# Reexportar funciones de core.security para compatibilidad
from app.core.security import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    get_password_context,
    oauth2_scheme
)

__all__ = [
    'create_access_token',
    'verify_token', 
    'hash_password',
    'verify_password',
    'get_password_context',
    'oauth2_scheme',
    'generate_access_token',
    'decode_access_token',
]


def generate_access_token(
    data: dict,
    expiry: timedelta = timedelta(days=7),
) -> str:
    """
    Generate a JWT access token with JTI for blacklisting.
    This is the new token generation function used by Section 16.
    """
    return jwt.encode(
        payload={
            **data,
            "jti": str(uuid4()),
            "exp": datetime.now(timezone.utc) + expiry,
        },
        algorithm=security_settings.JWT_ALGORITHM,
        key=security_settings.JWT_SECRET,
    )


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.
    This is the new token decoding function used by Section 16.
    """
    try:
        return jwt.decode(
            jwt=token,
            key=security_settings.JWT_SECRET,
            algorithms=[security_settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None


# Other general utilities
def generate_random_string(length: int = 10) -> str:
    """Generate a random string"""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
