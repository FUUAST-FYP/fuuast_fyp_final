import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_logic import RAGPipeline

try:
    import google.generativeai as genai
except Exception:
    genai = None

APP_NAME = "FUUAST UniBot API"

app = FastAPI(title=APP_NAME)

allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KB_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base.json")
rag = RAGPipeline(KB_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "guest_session"
    top_k: int = 3


def _is_smalltalk(msg: str) -> Optional[str]:
    m = msg.strip().lower()
    if m in {"hi", "hello", "hey", "assalam", "assalamualaikum", "salam"}:
        return "Hello! How can I help you with FUUAST information today?"
    if m in {"thanks", "thank you", "thx"}:
        return "You're welcome."
    return None


def _build_sources(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    for d in docs:
        label = d.get("sourceDocument") or d.get("category") or "University Source"
        page = d.get("pageNumber")
        if page is not None:
            label = f"{label} (p.{page})"
        sources.append(
            {
                "label": label,
                "url": d.get("url"),
                "sourceDocument": d.get("sourceDocument"),
                "pageNumber": d.get("pageNumber"),
            }
        )
    return sources


def _generate_answer(question: str, docs: List[Dict[str, Any]]) -> str:
    if not docs:
        return (
            "I could not find this in the current verified sources. "
            "Please check the official FUUAST website 확인, or ask a more specific question."
        )

    context_lines = []
    for d in docs:
        content = (d.get("content") or "").strip()
        if content:
            context_lines.append(f"- {content}")

    context = "\n".join(context_lines)

    if not (genai and GEMINI_API_KEY):
        # Fallback: return extracted context only
        return context_lines[0] if context_lines else "Information not available."

    prompt = f"""You are an official university website assistant for FUUAST.
Rules:
- Answer in 1-3 short sentences.
- Use ONLY the context below. Do not invent facts.
- If the context is insufficient, say you don't have that information.
Context:
{context}

Question: {question}
Answer:"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(prompt)
        return (resp.text or "").strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}


@app.post("/api/v1/chat")
def chat(req: ChatRequest):
    smalltalk = _is_smalltalk(req.message)
    if smalltalk:
        return {
            "status": "ok",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "answer": smalltalk,
            "sources": [],
        }

    docs = rag.search(req.message, top_k=max(1, min(req.top_k, 8)))
    answer = _generate_answer(req.message, docs)
    sources = _build_sources(docs)

    return {
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "answer": answer,
        "sources": sources,
    }


# Backward compatible endpoint
@app.post("/api/v1/query")
def query(req: ChatRequest):
    return chat(req)
