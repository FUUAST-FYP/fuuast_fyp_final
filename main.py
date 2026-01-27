import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rag_logic import RAGPipeline

# Optional Gemini SDK (keep optional)
try:
    import google.generativeai as genai
except Exception:
    genai = None

# Optional Groq REST client (recommended)
try:
    from groq_rest import groq_chat_completion  # (user_text, context_text, sources_text) -> str
except Exception:
    groq_chat_completion = None

APP_NAME = "FUUAST UniBot API"
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title=APP_NAME)

# ---------------------------
# CORS (local dev friendly)
# ---------------------------
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# LLM Config
# ---------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

# ---------------------------
# Lazy-loaded RAG (IMPORTANT for Vercel)
# ---------------------------
_rag: Optional[RAGPipeline] = None
_rag_error: Optional[str] = None
_kb_path_used: Optional[str] = None


def _resolve_kb_path() -> Optional[str]:
    """
    Try multiple candidate paths. This avoids crashes if KB file
    isn't present on Vercel due to ignore rules.
    """
    kb_name = os.getenv("KNOWLEDGE_BASE_PATH", "kb/kb_current.jsonl")

    # NOTE: On Vercel (and sometimes locally), the current working directory
    # can be different depending on how the function is invoked. We'll search
    # both CWD and the directory of this file.
    try:
        from pathlib import Path

        base_dir = str(Path(__file__).resolve().parent)
    except Exception:
        base_dir = os.getcwd()

    candidates = [
        # Relative (works if CWD is repo root)
        kb_name,
        "kb_current.json",
        "knowledge_base.json",

        # CWD-based
        os.path.join(os.getcwd(), kb_name),
        os.path.join(os.getcwd(), "kb_current.json"),
        os.path.join(os.getcwd(), "knowledge_base.json"),

        # File-location based (works even if CWD is /api)
        os.path.join(base_dir, kb_name),
        os.path.join(base_dir, "kb_current.json"),
        os.path.join(base_dir, "knowledge_base.json"),
    ]

    for p in candidates:
        try:
            if p and os.path.exists(p):
                return p
        except Exception:
            continue
    return None


def get_rag() -> Optional[RAGPipeline]:
    """
    Initialize RAG only when needed. Never crash the function at import time.
    """
    global _rag, _rag_error, _kb_path_used

    if _rag is not None:
        return _rag

    kb_path = _resolve_kb_path()
    if not kb_path:
        _rag_error = "KB file not found on server (kb_current.json / knowledge_base.json missing)."
        logger.error(_rag_error)
        return None

    try:
        _rag = RAGPipeline(kb_path)
        _kb_path_used = kb_path
        return _rag
    except Exception as e:
        _rag_error = f"Failed to load KB at {kb_path}: {e}"
        logger.exception(_rag_error)
        return None


# ---------------------------
# Request model
# ---------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str = "guest_session"
    top_k: int = 3


# ---------------------------
# Helpers
# ---------------------------
def normalize_query(q: str) -> str:
    low = (q or "").strip().lower()
    low = low.replace("bscs", "bs computer science bscs")
    low = low.replace("bsse", "bs software engineering bsse")
    low = low.replace("bba", "bachelor of business administration bba")
    low = low.replace("mba", "master of business administration mba")
    return low


def _is_smalltalk(msg: str) -> Optional[str]:
    m = (msg or "").strip().lower()
    if m in {"hi", "hello", "hey", "assalam", "assalamualaikum", "salam"}:
        return "Hello! How can I help you with verified FUUAST information today?"
    if m.startswith("how are you"):
        return "I’m doing well—thanks! What would you like to know about FUUAST?"
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


def _make_context(docs: List[Dict[str, Any]], max_chunks: int = 6):
    chunks: List[str] = []
    for d in docs:
        content = (d.get("content") or "").strip()
        if content:
            chunks.append(content)
    chunks = chunks[:max_chunks]
    context_text = "\n\n".join(chunks)

    sources_labels: List[str] = []
    for d in docs[:max_chunks]:
        label = d.get("sourceDocument") or d.get("category") or "University Source"
        page = d.get("pageNumber")
        if page is not None:
            label = f"{label} (p.{page})"
        sources_labels.append(label)

    sources_text = "\n".join(sources_labels)
    return chunks, context_text, sources_text


def _answer_with_llm(question: str, docs: List[Dict[str, Any]]) -> str:
    """
    Priority:
    1) Groq (recommended)
    2) Gemini (optional)
    3) No LLM -> return top retrieved chunk
    """
    if not docs:
        return (
            "I could not find this in the current verified sources. "
            "Try: “BSCS fee”, “BS Computer Science admission requirements”, or “BSCS program details”."
        )

    chunks, context_text, sources_text = _make_context(docs, max_chunks=6)

    # 1) Groq
    if GROQ_API_KEY and groq_chat_completion is not None:
        try:
            return groq_chat_completion(question, context_text, sources_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error (Groq): {e}") from e

    # 2) Gemini
    if genai and GEMINI_API_KEY:
        prompt = f"""You are an official university website assistant for FUUAST.
Rules:
- Answer in 1-3 short sentences.
- Use ONLY the context below. Do not invent facts.
- If the context is insufficient, say you don't have that information.
Context:
{context_text}

Question: {question}
Answer:"""
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            resp = model.generate_content(prompt)
            return (resp.text or "").strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error (Gemini): {e}") from e

    # 3) No LLM configured: return top chunk
    return chunks[0] if chunks else "Information not available."


# ---------------------------
# Error handler (better Vercel debugging)
# ---------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())[:8]
    logger.exception(f"[{error_id}] Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": "INTERNAL_SERVER_ERROR", "error_id": error_id},
    )


# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def root():
    return {"status": "ok", "service": APP_NAME, "endpoints": ["/health", "/api/health", "/api/v1/chat"]}


@app.get("/health")
def health():
    rag = get_rag()
    kb_items = len(rag.knowledge_base) if rag else 0
    return {
        "status": "ok",
        "service": APP_NAME,
        "kb_loaded": rag is not None,
        "kb_path": _kb_path_used,
        "kb_items": kb_items,
        "kb_error": _rag_error,
    }



# IMPORTANT: this matches your deployed check URL: /api/health
@app.get("/api/health")
def api_health():
    return health()


@app.post("/api/v1/chat")
def chat(req: ChatRequest):
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message is required")

    # Small talk -> no RAG, no sources
    smalltalk = _is_smalltalk(msg)
    if smalltalk:
        return {
            "status": "ok",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "answer": smalltalk,
            "sources": [],
        }

    rag = get_rag()
    if not rag:
        # Do not crash: return a controlled message
        return {
            "status": "error",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "answer": "Knowledge base is not available on the server yet. Please try again later.",
            "sources": [],
            "kb_error": _rag_error,
        }

    search_q = normalize_query(msg)
    docs = rag.search(search_q, top_k=max(1, min(req.top_k, 8)))

    answer = _answer_with_llm(msg, docs)
    sources = _build_sources(docs)

    # Optional polish
    answer = answer.replace("BS CSc", "BSCS")

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
