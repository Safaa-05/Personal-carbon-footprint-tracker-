from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from typing import Optional
from pydantic import BaseModel
import os

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

class TokenData(BaseModel):
    user_id: Optional[int] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded

def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(user_id=payload.get("user_id"))
    except JWTError:
        return None

# Ensure the required package is installed
try:
    import jose
except ImportError:
    raise ImportError("The 'jose' package is not installed. Please install it by running 'pip install python-jose'")
