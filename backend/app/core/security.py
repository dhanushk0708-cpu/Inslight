from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import bcrypt
import jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# ━━━ Fernet Token Encryption at Rest ━━━
import base64
import hashlib
from cryptography.fernet import Fernet


def get_fernet() -> Fernet:
    """Derive a URL-safe 32-byte Fernet key from ENCRYPTION_KEY or SECRET_KEY."""
    raw = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    derived = hashlib.sha256(raw.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(derived)
    return Fernet(key)


def encrypt_secret(secret_text: str) -> str:
    """Encrypt sensitive string (e.g. OAuth tokens) at rest."""
    if not secret_text:
        return ""
    f = get_fernet()
    return f.encrypt(secret_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    """Decrypt sensitive string from rest."""
    if not encrypted_text:
        return ""
    f = get_fernet()
    return f.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
