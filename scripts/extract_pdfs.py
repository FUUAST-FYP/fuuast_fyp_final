#!/usr/bin/env python3
"""
extract_pdfs.py

Reads kb/snapshots/pdf_links.jsonl and downloads PDFs, extracting text per page.
Outputs kb/snapshots/pdf_raw.jsonl (one JSON object per page with extracted text).

Run locally for the big bootstrap KB (recommended).
GitHub Actions can run it with smaller limits.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

HEADERS = {"User-Agent": "FUUAST-Academic-Assistant/1.0 (pdf extractor)"}

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def safe_name(url: str) -> str:
    p = urlparse(url)
    name = os.path.basename(p.path) or "document.pdf"
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

def iter_pdf_urls(pdf_links_path: str) -> List[str]:
    urls = []
    seen = set()
    if not os.path.exists(pdf_links_path):
        return urls
    with open(pdf_links_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
                u = (obj.get("url") or "").strip()
                if not u or u in seen:
                    continue
                seen.add(u)
                urls.append(u)
            except Exception:
                continue
    return urls

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-links", default=os.path.join("kb", "snapshots", "pdf_links.jsonl"))
    ap.add_argument("--out", default=os.path.join("kb", "snapshots", "pdf_raw.jsonl"))
    ap.add_argument("--max-pdfs", type=int, default=200)
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--sleep", type=float, default=0.25)
    ap.add_argument("--max-mb", type=float, default=25.0)
    ap.add_argument("--min-text-chars", type=int, default=50)
    args = ap.parse_args()

    urls = iter_pdf_urls(args.pdf_links)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    written = 0
    processed = 0

    with open(args.out, "w", encoding="utf-8") as out:
        for url in urls:
            if processed >= args.max_pdfs:
                break
            processed += 1
            try:
                r = requests.get(url, headers=HEADERS, timeout=args.timeout)
                if r.status_code != 200:
                    continue

                size_mb = len(r.content) / (1024 * 1024)
                if size_mb > args.max_mb:
                    continue

                reader = PdfReader(io.BytesIO(r.content))
                fname = safe_name(url)
                fetched_at = datetime.now(timezone.utc).isoformat()

                for i, page in enumerate(reader.pages, start=1):
                    text = (page.extract_text() or "").strip()
                    if len(text) < args.min_text_chars:
                        continue

                    out.write(json.dumps({
                        "id": f"pdfweb::{sha1(url)[:12]}::{i}",
                        "source_type": "pdf",
                        "url": url,
                        "sourceDocument": fname,
                        "pageNumber": i,
                        "fetched_at": fetched_at,
                        "text": text,
                    }, ensure_ascii=False) + "\n")
                    written += 1

                time.sleep(args.sleep)

            except Exception:
                continue

    print(f"Wrote {written} PDF page records -> {args.out}")

if __name__ == "__main__":
    main()
