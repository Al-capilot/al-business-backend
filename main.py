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


def call_openai(prompt: str):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenAI error: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_gemini(prompt: str):
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY / GEMINI_API_KEY is not configured")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini error: {response.text}")
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def plan_prompt(prompt: str):
    return (
        "You are a project planner. Break the user's request into clear steps and list the required outputs.\n"
        f"Request: {prompt}"
    )


def researcher(plan: str):
    if not SERPER_API_KEY:
        return "No external search configured. Proceed with general reasoning."

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": plan, "num": 3}
    response = requests.post(
        "https://google.serper.dev/search",
        headers=headers,
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        return f"Search unavailable: {response.text}"

    data = response.json()
    results = data.get("organic", [])
    if not results:
        return "No search results returned."

    snippets = []
    for item in results[:3]:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        snippets.append(f"- {title}: {snippet} ({link})")
    return "\n".join(snippets)


def writer(plan: str, research: str):
    return (
        "Draft response:\n"
        f"Plan:\n{plan}\n\nResearch:\n{research}"
    )


def validator(draft: str):
    cleaned = draft.strip()
    if not cleaned:
        raise ValueError("Generated response is empty")
    return cleaned


@app.post("/run")
def single_agent(payload: RunRequest):
    if not OPENAI_API_KEY and not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY or GOOGLE_API_KEY not found")

    try:
        if OPENAI_API_KEY:
            answer = call_openai(payload.prompt)
        else:
            answer = call_gemini(payload.prompt)

        return {
            "status": "ok",
            "prompt": payload.prompt,
            "answer": answer,
            "mode": "single-agent",
            "openai_key_present": bool(OPENAI_API_KEY),
            "google_key_present": bool(GOOGLE_API_KEY),
            "serper_key_present": bool(SERPER_API_KEY),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/run-multi")
def multi_agent(payload: RunRequest):
    try:
        plan = call_openai(plan_prompt(payload.prompt)) if OPENAI_API_KEY else call_gemini(plan_prompt(payload.prompt))
        research = researcher(plan)
        draft = writer(plan, research)
        final = validator(draft)
        return {
            "status": "ok",
            "prompt": payload.prompt,
            "answer": final,
            "mode": "multi-agent",
            "plan": plan,
            "research": research,
            "openai_key_present": bool(OPENAI_API_KEY),
            "google_key_present": bool(GOOGLE_API_KEY),
            "serper_key_present": bool(SERPER_API_KEY),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
