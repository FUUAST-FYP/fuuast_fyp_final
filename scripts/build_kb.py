#!/usr/bin/env python3
"""
build_kb.py

Compiles a production KB JSONL at kb/kb_current.jsonl from:
- kb/snapshots/web_raw.jsonl   (HTML pages)
- kb/snapshots/pdf_raw.jsonl   (PDF pages extracted from website)
- knowledge_base.json          (your curated verified PDF KB)

Output format (one JSON object per line) is compatible with rag_logic.py
(which normalizes "text" -> "content", and uses sourceDocument/pageNumber).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

RAW_WEB = os.path.join("kb", "snapshots", "web_raw.jsonl")
RAW_PDF = os.path.join("kb", "snapshots", "pdf_raw.jsonl")
STATIC_JSON = "knowledge_base.json"

OUT_KB = os.path.join("kb", "kb_current.jsonl")

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + chunk_size)
        chunks.append(text[i:j])
        if j >= n:
            break
        i = max(0, j - overlap)
    return chunks

def iter_jsonl(path: str) -> Iterable[Dict]:
    if not os.path.exists(path):
        return []
    def gen():
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    yield json.loads(ln)
                except Exception:
                    continue
    return gen()

def iter_static_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict) and isinstance(obj.get("items"), list):
        return [x for x in obj["items"] if isinstance(x, dict)]
    return []

def write_kb(records: Iterable[Dict], out_path: str) -> int:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    count = 0
    seen_ids = set()

    with open(out_path, "w", encoding="utf-8") as out:
        for r in records:
            rid = r.get("id")
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += 1
    return count

def build(out_path: str = OUT_KB) -> int:
    now = datetime.now(timezone.utc).isoformat()
    out_records: List[Dict] = []

    # 1) Curated static KB (knowledge_base.json)
    for item in iter_static_json(STATIC_JSON):
        base_id = item.get("id") or f"static::{sha1(json.dumps(item, sort_keys=True))[:12]}"
        content = (item.get("content") or item.get("text") or "").strip()
        if not content:
            continue
        for idx, ch in enumerate(chunk_text(content), start=1):
            out_records.append({
                "id": f"{base_id}::c{idx}",
                "source_type": item.get("source_type") or "pdf",
                "sourceDocument": item.get("sourceDocument") or item.get("category") or "Verified PDF",
                "pageNumber": item.get("pageNumber"),
                "url": item.get("url"),
                "fetched_at": item.get("fetched_at") or now,
                "text": ch,
            })

    # 2) Website HTML crawl
    for item in iter_jsonl(RAW_WEB):
        url = item.get("url")
        base_id = item.get("id") or (f"web::{sha1(url)[:12]}" if url else f"web::{sha1(json.dumps(item, sort_keys=True))[:12]}")
        text = (item.get("text") or "").strip()
        if not text:
            continue
        title = (item.get("title") or "").strip()
        doc = title or url or "FUUAST Website"
        for idx, ch in enumerate(chunk_text(text), start=1):
            out_records.append({
                "id": f"{base_id}::c{idx}",
                "source_type": "web",
                "sourceDocument": doc,
                "pageNumber": None,
                "url": url,
                "fetched_at": item.get("fetched_at") or now,
                "text": ch,
            })

    # 3) PDF pages extracted from discovered website PDFs
    for item in iter_jsonl(RAW_PDF):
        url = item.get("url")
        base_id = item.get("id") or (f"pdfweb::{sha1(url)[:12]}" if url else f"pdfweb::{sha1(json.dumps(item, sort_keys=True))[:12]}")
        text = (item.get("text") or "").strip()
        if not text:
            continue
        doc = item.get("sourceDocument") or "Website PDF"
        page = item.get("pageNumber")
        for idx, ch in enumerate(chunk_text(text), start=1):
            out_records.append({
                "id": f"{base_id}::c{idx}",
                "source_type": "pdf",
                "sourceDocument": doc,
                "pageNumber": page,
                "url": url,
                "fetched_at": item.get("fetched_at") or now,
                "text": ch,
            })

    # Write final KB
    count = write_kb(out_records, out_path)
    print(f"Wrote {count} KB chunks -> {out_path}")
    return count

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_KB)
    args = ap.parse_args()
    build(args.out)

if __name__ == "__main__":
    main()
