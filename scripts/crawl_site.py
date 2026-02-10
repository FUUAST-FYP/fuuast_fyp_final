#!/usr/bin/env python3
"""
crawl_site.py

Bootstrap crawler for https://fuuast.edu.pk

Outputs:
- kb/snapshots/web_raw.jsonl      (HTML pages -> cleaned text)
- kb/snapshots/pdf_links.jsonl    (discovered PDF URLs only; no PDF downloading here)

Design goals:
- Deterministic & safe: avoid infinite crawling loops
- Respectful: small delay between requests
- Practical: remove header/footer/nav noise for better KB quality
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

BASE = "https://fuuast.edu.pk/"
ALLOWED_DOMAIN = urlparse(BASE).netloc

HEADERS = {"User-Agent": "FUUAST-Academic-Assistant/1.0 (respectful crawler)"}

IMPORTANT_PATHS = (
    "/contact",
    "/under-graduate-program",
    "/university-organization",
    "/contact-detail-of-examination-office",
)


SKIP_EXT = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp4", ".mp3", ".zip", ".rar", ".css", ".js",
)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def normalize_url(u: str) -> str:
    """
    Normalize URL:
    - absolute
    - https scheme
    - strip fragments
    - drop query params (reduces duplicates / infinite loops)
    - strip trailing slash (except root)
    """
    u = (u or "").strip()
    if not u:
        return ""
    p = urlparse(u)
    scheme = "https"
    netloc = p.netloc
    path = p.path or "/"

    # remove fragment and query
    p2 = (scheme, netloc, path, "", "", "")
    out = urlunparse(p2)

    if out.endswith("/") and out != "https://%s/" % netloc:
        out = out[:-1]
    return out

def is_internal(u: str) -> bool:
    try:
        p = urlparse(u)
        return p.netloc == ALLOWED_DOMAIN
    except Exception:
        return False

def looks_like_pdf(u: str) -> bool:
    u_low = (u or "").lower()
    return (".pdf" in u_low) and (u_low.endswith(".pdf") or ".pdf/" in u_low or ".pdf?" in u_low)

def should_skip(u: str) -> bool:
    u_low = (u or "").lower()
    return any(u_low.endswith(ext) for ext in SKIP_EXT)

def clean_html_to_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # remove common layout blocks
    for selector in ["header", "footer", "nav", "aside"]:
        for tag in soup.select(selector):
            tag.decompose()

    title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
    text = soup.get_text("\n", strip=True)

    # normalize whitespace & drop tiny lines
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if len(ln) >= 3]
    text = "\n".join(lines)
    return title, text

def extract_links(html: str, page_url: str) -> Tuple[Set[str], Set[str]]:
    soup = BeautifulSoup(html, "lxml")
    page_links: Set[str] = set()
    pdf_links: Set[str] = set()

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue

        full = normalize_url(urljoin(page_url, href))
        if not full:
            continue

        if looks_like_pdf(full):
            pdf_links.add(full)
            continue

        if should_skip(full):
            continue

        if is_internal(full):
            page_links.add(full)

    return page_links, pdf_links

def load_seeds(seeds_file: Optional[str]) -> List[str]:
    seeds: List[str] = []
    if seeds_file and os.path.exists(seeds_file):
        with open(seeds_file, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                seeds.append(normalize_url(ln))
    if not seeds:
        seeds = [normalize_url(BASE)]
    # unique and keep order
    seen = set()
    out = []
    for u in seeds:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out

def crawl(
    seeds: List[str],
    out_web: str,
    out_pdfs: str,
    max_pages: int = 800,
    timeout_s: int = 20,
    delay_s: float = 0.25,
    min_text_chars: int = 300,
) -> Tuple[int, int]:
    os.makedirs(os.path.dirname(out_web), exist_ok=True)
    os.makedirs(os.path.dirname(out_pdfs), exist_ok=True)

    q = deque(seeds)
    seen: Set[str] = set()
    pdf_seen: Set[str] = set()

    pages_written = 0
    pdf_written = 0

    with open(out_web, "w", encoding="utf-8") as fweb, open(out_pdfs, "w", encoding="utf-8") as fpdf:
        while q and pages_written < max_pages:
            url = q.popleft()
            if not url or url in seen:
                continue
            seen.add(url)

            try:
                r = requests.get(url, headers=HEADERS, timeout=timeout_s, allow_redirects=True)
                ct = (r.headers.get("content-type") or "").lower()

                # If we landed on a PDF, record it and skip parsing as HTML
                if "application/pdf" in ct or looks_like_pdf(url):
                    if url not in pdf_seen:
                        pdf_seen.add(url)
                        fpdf.write(json.dumps({"url": url, "discovered_from": None}, ensure_ascii=False) + "\n")
                        pdf_written += 1
                    continue

                if r.status_code != 200 or "text/html" not in ct:
                    continue

                title, text = clean_html_to_text(r.text)
                page_links, pdf_links = extract_links(r.text, url)

                # Save short-but-important pages (e.g., /contact) even if below min_text_chars
                path = (urlparse(url).path or "/").rstrip("/")
                is_important = any(path == p.rstrip("/") for p in IMPORTANT_PATHS)

                if text and (len(text) >= min_text_chars or is_important):
                    rec = {
                        "id": f"web::{sha1(url)[:12]}",
                        "source_type": "web",
                        "url": url,
                        "title": title,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "text": text,
                    }
                    fweb.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    pages_written += 1

                for p in pdf_links:
                    if p not in pdf_seen:
                        pdf_seen.add(p)
                        fpdf.write(json.dumps({"url": p, "discovered_from": url}, ensure_ascii=False) + "\n")
                        pdf_written += 1

                for nxt in page_links:
                    if nxt not in seen:
                        q.append(nxt)

            except Exception:
                continue
            finally:
                time.sleep(delay_s)

    return pages_written, pdf_written

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default=os.path.join("scripts", "seeds.txt"), help="Seed URL list file")
    ap.add_argument("--out-web", default=os.path.join("kb", "snapshots", "web_raw.jsonl"))
    ap.add_argument("--out-pdfs", default=os.path.join("kb", "snapshots", "pdf_links.jsonl"))
    ap.add_argument("--max-pages", type=int, default=800)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--delay", type=float, default=0.25)
    ap.add_argument("--min-text-chars", type=int, default=300)
    args = ap.parse_args()

    seeds = load_seeds(args.seeds)
    pages, pdfs = crawl(
        seeds=seeds,
        out_web=args.out_web,
        out_pdfs=args.out_pdfs,
        max_pages=args.max_pages,
        timeout_s=args.timeout,
        delay_s=args.delay,
        min_text_chars=args.min_text_chars,
    )
    print(f"Saved web pages: {pages} -> {args.out_web}")
    print(f"Saved pdf links: {pdfs} -> {args.out_pdfs}")

if __name__ == "__main__":
    main()
