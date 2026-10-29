import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI(title="Al Business Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

class ChatRequest(BaseModel):
    prompt: str

@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "status": "running",
        "service": "al-business-agent",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.post("/api/chat")
async def chat(req: ChatRequest):
    prompt = req.prompt.strip()

    if not prompt:
        return {
            "status": "error",
            "message": "Prompt is empty."
        }

    if not os.getenv("GEMINI_API_KEY"):
        return {
            "status": "error",
            "message": "GEMINI_API_KEY not configured on server."
        }

    try:
        response = model.generate_content(prompt)
        answer = response.text if hasattr(response, "text") else str(response)

        return {
            "status": "ok",
            "message": "Task accepted.",
            "prompt": prompt,
            "response": answer
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Gemini request failed: {str(e)}"
        }

@app.get("/")
async def root():
    return {
        "message": "Al Business Agent API is running.",
        "health": "/api/health",
        "chat": "/api/chat"
    }
