from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib
import os

app = FastAPI()

# Password Security: Hashing a password
def hash_password(password: str) -> str:
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

# Password Security: Verifying a password
def verify_password(stored_password: str, provided_password: str) -> bool:
    salt_hex, hash_hex = stored_password.split(":")
    salt = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwd_hash.hex() == hash_hex


# --- REQUEST BODIES ---
class UserAuth(BaseModel):
    username: str
    password: str

class ClothingItem(BaseModel):
    user_id: int
    image_url: str = "https://placeholder.com/cloth.jpg"  # Default placeholder for now
    category: str  # e.g., "Top", "Bottom", "Shoes", "Outerwear"
    color: str     # e.g., "Black", "White", "Navy"
    formality: int # 1 = Casual, 2 = Smart Casual, 3 = Formal
    weather_tags: str # e.g., "Summer,Spring"


# --- AUTH ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Welcome to the Wardrobe AI Backend API!"}

@app.post("/register")
def register_user(user: UserAuth):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    hashed_pwd = hash_password(user.password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user.username, hashed_pwd))
        conn.commit()
        return {"status": "success", "message": f"User '{user.username}' created successfully!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists.")
    finally:
        conn.close()

@app.post("/login")
def login_user(user: UserAuth):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(row[1], user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password.")
        
    return {"status": "success", "message": "Login successful!", "user_id": row[0], "username": user.username}


# --- CLOSET ENDPOINTS ---

@app.post("/clothes/add")
def add_clothing_item(item: ClothingItem):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Check if user exists first
    cursor.execute("SELECT id FROM users WHERE id = ?", (item.user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")

    cursor.execute("""
        INSERT INTO clothes (user_id, image_url, category, color, formality, weather_tags)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (item.user_id, item.image_url, item.category, item.color, item.formality, item.weather_tags))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"{item.color} {item.category} added to your closet!"}

@app.get("/clothes/{user_id}")
def get_user_closet(user_id: int):
    conn = sqlite3.connect("database.db")
    # This magic line formats our database results into clean Python dictionaries
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM clothes WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Convert database rows to a clean list to send to the frontend
    closet = [dict(row) for row in rows]
    return {"user_id": user_id, "total_items": len(closet), "closet": closet}