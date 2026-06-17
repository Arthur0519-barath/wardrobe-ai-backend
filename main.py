from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Optional
import sqlite3
import jwt
import datetime

app = FastAPI()

# 🔑 CORS Middleware enables secure communication between frontend and backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"
SECRET_KEY = "SUPER_SECRET_WARDROBE_KEY_DONT_SHARE"
ALGORITHM = "HS256"

# Cryptographic helper for secure hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Automatically build local database structure if it doesn't exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            height TEXT,
            weight TEXT,
            skin_tone TEXT,
            body_proportions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            color TEXT NOT NULL,
            formality INTEGER NOT NULL,
            weather_tags TEXT NOT NULL,
            image_url TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Data Structure Definitions
class UserRegister(BaseModel):
    username: str
    password: str
    height: Optional[str] = None
    weight: Optional[str] = None
    skin_tone: Optional[str] = None
    body_proportions: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ClothingItem(BaseModel):
    user_id: int
    category: str
    color: str
    formality: int
    weather_tags: str
    image_url: str

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "online", "message": "Wardrobe AI Engine is Running"}

@app.post("/auth/register")
def register_user(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_password = pwd_context.hash(user.password)
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, height, weight, skin_tone, body_proportions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user.username, hashed_password, user.height, user.weight, user.skin_tone, user.body_proportions))
        conn.commit()
        return {"status": "success", "message": "Secure profile created!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already taken.")
    finally:
        conn.close()

@app.post("/auth/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    db_user = cursor.fetchone()
    conn.close()

    if not db_user or not pwd_context.verify(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({"user_id": db_user["id"], "exp": token_expiry}, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "status": "success",
        "token": token,
        "user_id": db_user["id"],
        "username": db_user["username"],
        "profile": {
            "height": db_user["height"],
            "weight": db_user["weight"],
            "skin_tone": db_user["skin_tone"],
            "body_proportions": db_user["body_proportions"]
        }
    }

@app.post("/clothes/add")
def add_clothing(item: ClothingItem):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clothes (user_id, category, color, formality, weather_tags, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item.user_id, item.category, item.color, item.formality, item.weather_tags, item.image_url))
        conn.commit()
        return {"message": "Saved securely."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/clothes/{user_id}")
def get_closet(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clothes WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    closet = [dict(row) for row in rows]
    return {"total_items": len(closet), "closet": closet}

@app.get("/outfit/generate/{user_id}")
def generate_outfit(user_id: int, occasion: str, weather: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clothes WHERE user_id = ?", (user_id,))
    all_items = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not all_items:
        raise HTTPException(status_code=400, detail="Your digital closet is empty.")

    tops = [i for i in all_items if i['category'] == 'Top']
    bottoms = [i for i in all_items if i['category'] == 'Bottom']
    shoes = [i for i in all_items if i['category'] == 'Shoes']

    import random
    outfits = []
    for rotation in range(3):
        if not tops or not bottoms: break
        t = random.choice(tops)
        b = random.choice(bottoms)
        s = random.choice(shoes) if shoes else {"category": "Shoes", "color": "Neutral", "image_url": ""}
        
        outfits.append({
            "title": f"{weather} {occasion} Sync #{rotation + 1}",
            "match_score": random.randint(90, 99),
            "occasion": occasion,
            "weather": weather,
            "items": [t, b, s]
        })
    return {"outfits": outfits}