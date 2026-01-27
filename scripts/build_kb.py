import json, os
from datetime import datetime

RAW_WEB = "kb/snapshots/web_raw.jsonl"
PDF_KB  = "knowledge_base.json"   # existing verified PDF KB
OUT_KB  = "kb/kb_current.jsonl"

def chunk_text(text: str, chunk_size=750, overlap=120):
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + chunk_size)
        chunks.append(text[i:j])
        if j >= n:
            break
        i = max(0, j - overlap)
    return chunks


def _load_pdf_kb(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    return data if isinstance(data, list) else []

def build():
    os.makedirs("kb", exist_ok=True)
    build_date = datetime.utcnow().strftime("%Y-%m-%d")

    out_count = 0
    with open(OUT_KB, "w", encoding="utf-8") as out:

        # 1) WEB (daily snapshot)
        if os.path.exists(RAW_WEB):
            with open(RAW_WEB, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    chunks = chunk_text(rec.get("text", ""))
                    for idx, ch in enumerate(chunks):
                        item = {
                            "id": f"web::{rec.get('hash','')[:12]}::{idx}",
                            "source_type": "web",
                            "url": rec.get("url"),
                            "title": rec.get("title", ""),
                            "fetched_at": rec.get("fetched_at"),
                            "text": ch,
                            "kb_build_date": build_date
                        }
                        out.write(json.dumps(item, ensure_ascii=False) + "\n")
                        out_count += 1

        # 2) PDFs (existing verified KB)
        pdf_items = _load_pdf_kb(PDF_KB)
        for i, rec in enumerate(pdf_items):
            if not isinstance(rec, dict):
                continue
            content = rec.get("content") or rec.get("text") or ""
            if not content.strip():
                continue

            source_doc = rec.get("sourceDocument") or rec.get("category") or rec.get("doc_name") or "University PDF"
            page = rec.get("pageNumber") or rec.get("page")

            chunks = chunk_text(content)
            for idx, ch in enumerate(chunks):
                item = {
                    "id": f"pdf::{source_doc}::{page}::{i}::{idx}",
                    "source_type": "pdf",
                    "sourceDocument": source_doc,
                    "pageNumber": page,
                    "url": rec.get("url"),
                    "text": ch,
                    "kb_build_date": build_date
                }
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
                out_count += 1

    print("KB chunks:", out_count)
    print("Wrote:", OUT_KB)

if __name__ == "__main__":
    build()
