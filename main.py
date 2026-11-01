import os
import requests
from fastapi import FastAPI, HTTPException
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")


class RunRequest(BaseModel):
    prompt: str = "Maliyyə və AI trendlərini araşdır."


@app.get("/")
def home():
    return {"status": "ok", "message": "al-business-backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


def ask_openai(prompt: str):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenAI error: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"]


def ask_gemini(prompt: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini error: {response.text}")
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


@app.post("/run")
def run_model(payload: RunRequest):
    if not OPENAI_API_KEY and not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY or GOOGLE_API_KEY not found")

    try:
        if OPENAI_API_KEY:
            answer = ask_openai(payload.prompt)
        else:
            answer = ask_gemini(payload.prompt)
        return {
            "status": "ok",
            "prompt": payload.prompt,
            "answer": answer,
            "openai_key_present": bool(OPENAI_API_KEY),
            "google_key_present": bool(GOOGLE_API_KEY),
            "serper_key_present": bool(SERPER_API_KEY)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
