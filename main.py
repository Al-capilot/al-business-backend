import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") or GEMINI_API_KEY
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

class RunRequest(BaseModel):
    prompt: str = "Maliyyə və AI trendlərini araşdır."

@app.get("/")
def home():
    return {"status": "ok", "message": "al-business-backend is running on Render"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run_model(payload: RunRequest):
    if not OPENAI_API_KEY and not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY or GEMINI_API_KEY not found in Render env")

    return {
        "status": "ok",
        "message": "Backend is connected and ready.",
        "prompt": payload.prompt,
        "gemini_key_present": bool(GOOGLE_API_KEY),
        "openai_key_present": bool(OPENAI_API_KEY),
        "serper_key_present": bool(SERPER_API_KEY),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
