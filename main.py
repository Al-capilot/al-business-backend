from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Al Business Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str

@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "status": "running",
        "service": "al-business-agent"
    }

@app.post("/api/chat")
async def chat(req: ChatRequest):
    prompt = req.prompt.strip()

    if not prompt:
        return {
            "status": "error",
            "message": "Prompt is empty."
        }

    response_text = (
        "B2B marketplace strategy hazırdır.\n\n"
        "1) Buyer and supplier onboarding\n"
        "2) Product catalog and RFQ flow\n"
        "3) Supplier verification and scoring\n"
        "4) Dashboard and analytics\n"
        "5) Pricing and subscription plan\n"
        "6) MVP roadmap and deployment guide\n\n"
        f"İstədiyiniz sorğu: {prompt}"
    )

    return {
        "status": "ok",
        "message": "Task qəbul edildi.",
        "prompt": prompt,
        "response": response_text
    }

@app.get("/")
async def root():
    return {
        "message": "Al Business Agent API is running.",
        "health": "/api/health",
        "chat": "/api/chat"
    }
