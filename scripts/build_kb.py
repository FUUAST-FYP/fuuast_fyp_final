import json, os
from datetime import datetime

RAW_WEB = "kb/snapshots/web_raw.jsonl"
OUT_KB  = "kb/kb_current.jsonl"

def chunk_text(text: str, chunk_size=750, overlap=120):
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        j = min(len(text), i + chunk_size)
        chunks.append(text[i:j])
        i = max(j - overlap, j)
    return chunks

def build():
    os.makedirs("kb", exist_ok=True)
    build_date = datetime.utcnow().strftime("%Y-%m-%d")

    out_count = 0
    with open(OUT_KB, "w", encoding="utf-8") as out:
        # WEB
        if os.path.exists(RAW_WEB):
            with open(RAW_WEB, "r", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    chunks = chunk_text(rec["text"])
                    for idx, ch in enumerate(chunks):
                        item = {
                            "id": f"web::{rec['hash'][:12]}::{idx}",
                            "source_type": "web",
                            "url": rec["url"],
                            "title": rec.get("title", ""),
                            "fetched_at": rec["fetched_at"],
                            "text": ch,
                            "kb_build_date": build_date
                        }
                        out.write(json.dumps(item, ensure_ascii=False) + "\n")
                        out_count += 1

        # PDFs can be appended here later the same way (source_type="pdf", doc_name, page)

    print("KB chunks:", out_count)
    print("Wrote:", OUT_KB)

if __name__ == "__main__":
    build()
