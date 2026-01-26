import os, json, time
from collections import deque
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://fuuast.edu.pk"
START_URLS = [
    "https://fuuast.edu.pk/",
]

MAX_PAGES = 250          # keep reasonable; adjust if KB gets too big
DELAY_SEC = 0.35         # polite crawling
RETENTION_DAYS = 7
CHUNK_CHARS = 1200       # chunk size for RAG

ROOT = os.path.dirname(os.path.dirname(__file__))
SNAP_DIR = os.path.join(ROOT, "kb_snapshots")
CURRENT_KB = os.path.join(ROOT, "kb_current.json")
MANIFEST = os.path.join(ROOT, "kb_manifest.json")

os.makedirs(SNAP_DIR, exist_ok=True)

def is_internal(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.scheme in ("http", "https") and u.netloc.endswith("fuuast.edu.pk")
    except Exception:
        return False

def normalize(url: str) -> str:
    url = url.split("#")[0]
    return url.rstrip("/")

def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=25, headers={"User-Agent": "fuuast-fyp-bot/1.0"})
    r.raise_for_status()
    return r.text

def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text

def extract_links(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        full = normalize(urljoin(base_url, href))

        # Skip downloads/media
        if any(full.lower().endswith(ext) for ext in [".jpg",".png",".gif",".pdf",".zip",".mp4",".mp3",".doc",".docx",".xls",".xlsx"]):
            continue

        if is_internal(full):
            links.add(full)
    return links

def chunk_text(text: str, max_chars: int = CHUNK_CHARS):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+max_chars])
        i += max_chars
    return chunks

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # PKT date label (UTC+5)
    today_pkt = (datetime.now(timezone.utc) + timedelta(hours=5)).date().isoformat()
    fetched_at = datetime.now(timezone.utc).isoformat()

    visited = set()
    q = deque(normalize(u) for u in START_URLS)

    docs = []
    page_count = 0

    while q and page_count < MAX_PAGES:
        url = q.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            html = fetch_html(url)
        except Exception:
            continue

        text = clean_text(html)
        if len(text) < 200:
            continue

        chunks = chunk_text(text)
        for ci, c in enumerate(chunks):
            docs.append({
                "id": f"web-{today_pkt}-{page_count}-{ci}",
                "category": "Website",
                "content": c,
                "url": url,
                "snapshot_date": today_pkt,
                "fetched_at": fetched_at
            })

        for link in extract_links(html, url):
            if link not in visited:
                q.append(link)

        page_count += 1
        time.sleep(DELAY_SEC)

    # Save daily snapshot
    snap_path = os.path.join(SNAP_DIR, f"{today_pkt}.json")
    save_json(snap_path, docs)

    # Retention: keep last 7 snapshot files
    all_snaps = sorted([f for f in os.listdir(SNAP_DIR) if f.endswith(".json")])
    while len(all_snaps) > RETENTION_DAYS:
        old = all_snaps.pop(0)
        os.remove(os.path.join(SNAP_DIR, old))

    # Build kb_current.json = merged of last 7 snapshots
    merged = []
    for f in sorted([f for f in os.listdir(SNAP_DIR) if f.endswith(".json")]):
        merged.extend(load_json(os.path.join(SNAP_DIR, f)))

    save_json(CURRENT_KB, merged)

    manifest = {
        "current": today_pkt,
        "snapshots": sorted([f.replace(".json","") for f in os.listdir(SNAP_DIR) if f.endswith(".json")]),
        "updated_at_utc": datetime.now(timezone.utc).isoformat()
    }
    save_json(MANIFEST, manifest)

if __name__ == "__main__":
    main()
