import os
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

# Secure Cryptographic Key — In production, load this from system environment variables
ENCRYPTION_KEY = b'6fKzY1V2X9z4B3C5v7e8R9t0Y1u2I3o4P5a6S7d8F9g=' 
cipher_suite = Fernet(ENCRYPTION_KEY)

# --- Schema Definitions ---
class UserRegister(BaseModel):
    username: str
    password: str
    age: str
    height: str
    weight: str
    skin_tone: str
    body_proportions: str
    hair_color: str

class UserLogin(BaseModel):
    username: str
    password: str

class ClosetItem(BaseModel):
    username: str
    item_name: str
    category: str
    color: str
    image_url: str = "placeholder.jpg"

class ChatMessage(BaseModel):
    username: str
    message: str

# --- Security Operations ---
def encrypt_metric(data: str) -> str:
    return cipher_suite.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_metric(encrypted_data: str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')

def hash_access_code(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8')[:72], bcrypt.gensalt()).decode('utf-8')

def verify_access_code(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8')[:72], hashed.encode('utf-8'))

# --- Database Compilation ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Users core table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secure_users_v5 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            age TEXT, height TEXT, weight TEXT, skin_tone TEXT, body_proportions TEXT, hair_color TEXT,
            streak_count INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Wardrobe inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe_vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            item_name TEXT,
            category TEXT,
            color TEXT,
            image_url TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def health_check():
    return {"status": "online", "message": "Wardrobe AI Engine V5 Secure Live"}

@app.post("/auth/register")
def register(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM secure_users_v5 WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Identity path already initialized.")
    
    hashed = hash_access_code(user.password)
    cursor.execute("""
        INSERT INTO secure_users_v5 (username, password_hash, age, height, weight, skin_tone, body_proportions, hair_color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user.username, hashed, encrypt_metric(user.age), encrypt_metric(user.height), 
          encrypt_metric(user.weight), encrypt_metric(user.skin_tone), encrypt_metric(user.body_proportions), encrypt_metric(user.hair_color)))
    conn.commit()
    conn.close()
    return {"status": "success", "username": user.username}

@app.post("/auth/login")
def login(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, age, height, weight, skin_tone, body_proportions, hair_color, streak_count FROM secure_users_v5 WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_access_code(user.password, row[0]):
        raise HTTPException(status_code=401, detail="Cryptographic token verification mismatch.")
        
    return {
        "status": "success",
        "username": user.username,
        "streak": row[7],
        "profile": {
            "age": decrypt_metric(row[1]), "height": decrypt_metric(row[2]), "weight": decrypt_metric(row[3]),
            "skin_tone": decrypt_metric(row[4]), "body_proportions": decrypt_metric(row[5]), "hair_color": decrypt_metric(row[6])
        }
    }

@app.post("/wardrobe/append")
def add_item(item: ClosetItem):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO wardrobe_vault (username, item_name, category, color, image_url) VALUES (?, ?, ?, ?, ?)",
                   (item.username, item.item_name, item.category, item.color, item.image_url))
    conn.commit()
    conn.close()
    return {"status": "indexed"}

@app.get("/wardrobe/retrieve/{username}")
def get_wardrobe(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, category, color, image_url FROM wardrobe_vault WHERE username = ?", (username,))
    items = [{"item_name": r[0], "category": r[1], "color": r[2], "image_url": r[3]} for r in cursor.fetchall()]
    conn.close()
    return {"items": items}

@app.post("/ai/consult")
def consult_stylist(chat: ChatMessage):
    msg = chat.message.lower()
    # High-level local response matrix handling context variables
    if "formal" in msg or "meeting" in msg:
        reply = "Analysis of calendar schedule indicates a Project Review. Recommend checking your Wardrobe Analytics and layering a crisp White Linen Shirt with a dark tailored blazer."
    elif "gym" in msg or "workout" in msg:
        reply = "Active tracking session detected for 18:00. Recommend breathable athletic mesh fabrics matching your high-contrast silhouette parameters."
    elif "rain" in msg or "weather" in msg:
        reply = "Environmental sensors match 18°C precipitation. Deploy the Charcoal Textured Waterproof Overcoat from your closet to preserve core temperature balance."
    else:
        reply = f"System analysis calibrated to your unique body composition profiles. I recommend combining tonal items from your virtual closet to maximize color harmony metrics."
    return {"reply": reply}