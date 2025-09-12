# backend/auth.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sqlite3
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

auth_router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT secret key
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# DB init
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Routes
@auth_router.post("/signup")
def signup(user: User):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    hashed_pw = pwd_context.hash(user.password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()
    return {"message": "User created successfully"}

@auth_router.post("/login", response_model=Token)
def login(user: User):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not pwd_context.verify(user.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token({"sub": user.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}
