# UniBot — FUUAST AI Help Chatbot (FYP)

UniBot is a **Retrieval‑Augmented Generation (RAG)** chatbot for **FUUAST (Gulshan Campus, Karachi)**.  
It answers student questions using **grounded sources** (official website pages + PDFs) and shows **citations** instead of guessing.

## Key Features
- **Grounded answers with sources** (links + page numbers when available)
- **RAG pipeline** over:
  - Crawled FUUAST website content (HTML → clean text)
  - University PDFs (Prospectus / Notices / Fee tables, etc.)
- **Timetable Q&A** (sections / days / time / teacher availability) using `timetable_engine.py`
- **Safety behavior**
  - If no relevant source is found, UniBot asks for clarification or says it cannot verify, rather than hallucinating.

## Tech Stack
- **Frontend:** React + TypeScript (Vite)
- **Backend:** FastAPI (Python)
- **Deploy:** Vercel (Python Serverless for API + Static build for UI)

---

## Run Locally

### 1) Frontend
```bash
npm install
npm run dev
```

### 2) Backend (FastAPI)
Create environment variables (recommended):
- `GROQ_API_KEY` (primary LLM)
- `GEMINI_API_KEY` (optional fallback)

Run:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
- UI: Vite will show a local URL
- API health: `/api/health`

---

## Build / Update Knowledge Base
The backend reads the KB from:
- `kb/kb_current.jsonl` (preferred)
- `knowledge_base.json` (fallback only)

Generate the KB:
```bash
python scripts/build_kb.py
python scripts/rotate_kb.py
```

Timetable:
```bash
python scripts/parse_timetable.py
```

---

## Deploy (Vercel)
- API entry: `api/index.py` → imports `main.app`
- `vercel.json` includes the KB + timetable in `includeFiles`

---

## Demo Script (Viva‑Friendly)
Try these live:
1) “BSCS fee structure morning 2026”
2) “Admission Morning 2026 warning about agents”
3) “Contact FUUAST email and phone”
4) “BS1A Monday schedule”
5) “Is <Teacher Name> free on Monday 09:00?”

If sources conflict, UniBot should show both sources instead of choosing one without evidence.

---

## Notes for Examiners
- This project is **RAG**, not a plain “ChatGPT wrapper”:
  - Retrieval selects relevant context from the KB
  - The LLM answers using only that context
  - Citations are displayed so results can be verified
