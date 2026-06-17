import os
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

class UserRegister(BaseModel):
    username: str
    password: str
    age: str          # <-- Added Age Field
    height: str
    weight: str
    skin_tone: str
    body_proportions: str
    hair_color: str

class UserLogin(BaseModel):
    username: str
    password: str

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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_v4 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age TEXT,
            height TEXT,
            weight TEXT,
            skin_tone TEXT,
            body_proportions TEXT,
            hair_color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def home():
    return {"status": "online", "message": "Wardrobe AI Engine V4 Live"}

@app.post("/auth/register")
def register_user(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users_v4 WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    
    try:
        cursor.execute("""
            INSERT INTO users_v4 (username, password_hash, age, height, weight, skin_tone, body_proportions, hair_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user.username, hashed_password, user.age, user.height, user.weight, user.skin_tone, user.body_proportions, user.hair_color))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    conn.close()
    token = create_access_token({"sub": user.username})
    return {"message": "Vault created successfully", "token": token, "username": user.username}

@app.post("/auth/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, password_hash, age, height, weight, skin_tone, body_proportions, hair_color FROM users_v4 WHERE username = ?", (user.username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not verify_password(user.password, result[1]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token = create_access_token({"sub": user.username})
    return {
        "message": "Welcome back", 
        "token": token, 
        "username": user.username,
        "profile": {
            "age": result[2],
            "height": result[3],
            "weight": result[4],
            "skin_tone": result[5],
            "body_proportions": result[6],
            "hair_color": result[7]
        }
    }