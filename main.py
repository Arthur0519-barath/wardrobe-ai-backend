from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import random

app = FastAPI()

# 🚨 FIXES THE ADD ITEM BUG: Allows your frontend to communicate with your cloud backend!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows connections from any browser window
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database.db"

class ClothingItem(BaseModel):
    user_id: int
    category: str
    color: str
    formality: int
    weather_tags: str
    image_url: str = "https://placeholder.com/cloth.jpg"

@app.get("/")
def home():
    return {"status": "Wardrobe AI Engine Online"}

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
        return {"message": "Item added successfully to cloud wardrobe!"}
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

# ==================== 🧠 UNIQUE AI RECOMMENDATION ENGINE ====================
@app.get("/outfit/generate/{user_id}")
def generate_outfit(user_id: int, occasion: str, weather: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clothes WHERE user_id = ?", (user_id,))
    all_items = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not all_items:
        raise HTTPException(status_code=400, detail="Closet is empty. Add items first!")

    # Convert formality string values to logic mapping
    formality_map = {"Casual": 1, "Work": 2, "Date Night": 2, "Meeting": 3}
    target_formality = formality_map.get(occasion, 1)

    # Filter items by category
    tops = [i for i in all_items if i['category'] == 'Top']
    bottoms = [i for i in all_items if i['category'] == 'Bottom']
    shoes = [i for i in all_items if i['category'] == 'Shoes']
    outerwear = [i for i in all_items if i['category'] == 'Outerwear']

    # AI Match Score scoring mechanism
    def calculate_match_score(item):
        score = 70 # Base structural score
        if item['formality'] == target_formality: score += 15
        if weather.lower() in item['weather_tags'].lower(): score += 15
        return min(score, 100)

    # Build recommendations
    outfits = []
    
    # Generate up to 3 variations based on available inventory
    for rotation in range(3):
        if not tops or not bottoms: break
        
        selected_top = random.choice(tops)
        selected_bottom = random.choice(bottoms)
        selected_shoe = random.choice(shoes) if shoes else {"category": "Shoes", "color": "Default", "weather_tags": "All", "image_url": ""}
        
        avg_score = int((calculate_match_score(selected_top) + calculate_match_score(selected_bottom)) / 2)

        outfits.append({
            "title": f"{weather} {occasion} Fit Combo #{rotation + 1}",
            "match_score": avg_score,
            "occasion": occasion,
            "weather": weather,
            "items": [selected_top, selected_bottom, selected_shoe]
        })

    return {"outfits": outfits}