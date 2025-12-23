"""Authentication utilities"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from backend.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        # Convert to bytes if needed
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        # Truncate password to 72 bytes (bcrypt limit)
        plain_password = plain_password[:72]
        
        result = bcrypt.checkpw(plain_password, hashed_password)
        print(f"DEBUG: Password verification - result: {result}, hash length: {len(hashed_password)}")
        return result
    except (ValueError, Exception) as e:
        # Log error for debugging
        print(f"Password verification error: {e}, hash: {hashed_password[:50] if isinstance(hashed_password, bytes) else str(hashed_password)[:50]}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Truncate to 72 bytes (bcrypt limit)
    password = password[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

