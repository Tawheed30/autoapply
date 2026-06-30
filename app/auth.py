"""User authentication and JWT token management."""
import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from pydantic import BaseModel, EmailStr

class UserCredentials(BaseModel):
    email: EmailStr
    password: str

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class TokenData(BaseModel):
    user_id: str
    email: str
    exp: datetime

class AuthManager:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expire_hours = 24

    def hash_password(self, password: str) -> tuple[str, str]:
        """Hash password with salt. Returns (hash, salt)."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
        return pwd_hash, salt

    def verify_password(self, password: str, pwd_hash: str, salt: str) -> bool:
        """Verify password against hash."""
        test_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
        return test_hash == pwd_hash

    def create_token(self, user_id: str, email: str) -> str:
        """Create JWT token."""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
            )
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            return None

    def extract_token_from_header(self, auth_header: Optional[str]) -> Optional[str]:
        """Extract token from Authorization header."""
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None
