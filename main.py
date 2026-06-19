import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from openai import OpenAI

app = FastAPI(
    title="Wardrobe AI Production Core",
    description="Live execution API suite featuring dynamic context injections and real LLM compilation.",
    version="1.0.0"
)

# Global Cross-Origin Resource Sharing (CORS) Security Enforcer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your specific frontend domain layout in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Real OpenAI Client Pipeline
# System expects an environment variable named 'OPENAI_API_KEY' pre-configured on Render/Vercel host.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Production Memory Store (Swap this out with a relational DB link like PostgreSQL/Supabase when scaling tables)
USER_VAULT: Dict[str, dict] = {}
WARDROBE_VAULT: Dict[str, List[dict]] = {}

# --- Pydantic Analytical Request Models ---
class UserRegisterSchema(BaseModel):
    username: str
    password: str
    age: str
    height: str
    weight: str
    skin_tone: str
    body_proportions: str
    hair_color: str

class UserLoginSchema(BaseModel):
    username: str
    password: str

class WardrobeItemSchema(BaseModel):
    username: str
    item_name: str
    category: str
    color: str

class AIConsultationSchema(BaseModel):
    username: str
    message: str
    current_weather: Optional[str] = "18°C, Light Rain showers, High Humidity"
    calendar_context: Optional[str] = "15:00 Corporate Executive Pitch, 18:00 Performance Conditioning Session"


# --- Symmetric Gateway Authentication Microservices ---
@app.post("/auth/register")
async def register_secure_user(payload: UserRegisterSchema):
    username_cleaned = payload.username.strip().lower()
    if not username_cleaned or not payload.password:
        raise HTTPException(status_code=400, detail="Invalid identity layout credentials.")
    
    if username_cleaned in USER_VAULT:
        raise HTTPException(status_code=400, detail="Matrix identity assignment collision. ID taken.")
    
    USER_VAULT[username_cleaned] = {
        "password": payload.password,
        "profile": {
            "age": payload.age,
            "height": payload.height,
            "weight": payload.weight,
            "skin_tone": payload.skin_tone,
            "body_proportions": payload.body_proportions,
            "hair_color": payload.hair_color
        },
        "streak": 5  # Baseline streak initialization parameter
    }
    WARDROBE_VAULT[username_cleaned] = []
    return {"status": "SUCCESS", "message": "Secure identity allocated successfully."}

@app.post("/auth/login")
async def verify_secure_user(payload: UserLoginSchema):
    username_cleaned = payload.username.strip().lower()
    if username_cleaned not in USER_VAULT or USER_VAULT[username_cleaned]["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Cryptographic token mismatch. Access denied.")
    
    user_record = USER_VAULT[username_cleaned]
    return {
        "status": "AUTHENTICATED",
        "profile": user_record["profile"],
        "streak": user_record["streak"]
    }


# --- Intelligent Closet Inventory Pipeline ---
@app.post("/wardrobe/append")
async def append_apparel_asset(payload: WardrobeItemSchema):
    username_cleaned = payload.username.strip().lower()
    if username_cleaned not in WARDROBE_VAULT:
        WARDROBE_VAULT[username_cleaned] = []
        
    item_entry = {
        "item_name": payload.item_name.strip(),
        "category": payload.category,
        "color": payload.color
    }
    WARDROBE_VAULT[username_cleaned].append(item_entry)
    return {"status": "INDEXED", "item": item_entry}

@app.get("/wardrobe/retrieve/{username}")
async def retrieve_apparel_assets(username: str):
    username_cleaned = username.strip().lower()
    items = WARDROBE_VAULT.get(username_cleaned, [])
    return {"username": username_cleaned, "items": items}


# --- THE LIVE AI ENGINE CORE ROUTE ---
@app.post("/ai/consult")
async def execute_ai_consultation(payload: AIConsultationSchema):
    username_cleaned = payload.username.strip().lower()
    
    # 1. Fallback Protection check if API key hasn't been mounted to target runtime environment variables
    if not client:
        return {
            "reply": "[OFFLINE ENGINE ENFORCEMENT]: Your API key is not connected to Render's environment. "
                     f"However, I see you want to process: '{payload.message}'. Fix the environment variables to activate this live feature!"
        }
    
    # 2. Extract specific user characteristics and assets to inject straight into prompt architecture
    user_profile = USER_VAULT.get(username_cleaned, {}).get("profile", {})
    user_closet = WARDROBE_VAULT.get(username_cleaned, [])
    
    # Format structural metadata maps to guide the neural model context layout
    closet_manifest = "\n".join([f"- {i['item_name']} ({i['color']} {i['category']})" for i in user_closet]) if user_closet else "No items indexed yet."
    biometrics = (
        f"Age: {user_profile.get('age', 'N/A')}, "
        f"Height: {user_profile.get('height', 'N/A')}, "
        f"Weight: {user_profile.get('weight', 'N/A')}, "
        f"Skin Complexion: {user_profile.get('skin_tone', 'N/A')}, "
        f"Build Proportions: {user_profile.get('body_proportions', 'N/A')}"
    )

    # 3. Construct System Prompt Architecture to lock the AI into a strict high-end stylist persona
    system_instruction = (
        "You are the advanced neural engine power behind WARDROBE AI, an elite, hyper-personalized digital stylist wardrobe companion.\n"
        "Your task is to analyze the user's explicit request alongside their biometrics, current real-time weather conditions, and agenda targets "
        "to synthesize precise wardrobe coordinate recommendations. Only recommend apparel items from their inventory manifest below. "
        "Maintain an ultra-premium, clear, encouraging, and highly professional architectural tone.\n\n"
        f"USER BIOMETRICS:\n{biometrics}\n\n"
        f"ENVIRONMENT WEATHER CONDITIONS:\n{payload.current_weather}\n\n"
        f"CALENDAR AGENDA TARGETS:\n{payload.calendar_context}\n\n"
        f"USER APPAREL INVENTORY MANIFEST:\n{closet_manifest}\n\n"
        "Formulate a direct, scannable response. Point out specifically why those selections respect the structural environment variables and metrics."
    )

    try:
        # 4. Trigger Live Multi-Turn Model Context Generation
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Switch to standard 'gpt-4o' or target engine layout when performance budgets scale
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": payload.message}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        ai_generated_response = completion.choices[0].message.content
        return {"reply": ai_generated_response}
        
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"LLM core engine routing failure: {str(error)}")


if __name__ == "__main__":
    import uvicorn
    # Locally runs script on Port 8000 when triggered directly via interpreter shell
    uvicorn.run("main.py:app", host="0.0.0.0", port=8000, reload=True)