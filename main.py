import os
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 1. Enable CORS for local file execution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

# Pydantic Schemas for validation
class UserRegister(BaseModel):
    username: str
    password: str
    height: int
    weight: int
    skin_tone: str
    body_proportions: str

class UserLogin(BaseModel):
    username: str
    password: str

# Helper Functions using native bcrypt instead of broken passlib
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, "SUPER_SECRET_KEY_123", algorithm="HS256")

# Database Setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            height INTEGER,
            weight INTEGER,
            skin_tone TEXT,
            body_proportions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def home():
    return {"status": "online", "message": "Wardrobe AI Engine is Running"}

@app.post("/auth/register")
def register_user(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Securely hash password natively
    hashed_password = get_password_hash(user.password)
    
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, height, weight, skin_tone, body_proportions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user.username, hashed_password, user.height, user.weight, user.skin_tone, user.body_proportions))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    conn.close()
    
    token = create_access_token({"sub": user.username})
    return {"message": "Vault profile created successfully", "token": token, "username": user.username}

@app.post("/auth/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (user.username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not verify_password(user.password, result[0]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token = create_access_token({"sub": user.username})
    return {"message": "Welcome back to your vault", "token": token, "username": user.username}