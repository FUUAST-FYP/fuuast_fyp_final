import re, json, hashlib, time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://fuuast.edu.pk/"
ALLOWED_DOMAIN = urlparse(BASE).netloc

HEADERS = {"User-Agent": "FUUAST-Academic-Assistant/1.0 (respectful crawler)"}

SKIP_EXT = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
            ".mp4", ".mp3", ".zip", ".rar", ".css", ".js")

def is_allowed(url: str) -> bool:
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        return False
    if u.netloc and u.netloc != ALLOWED_DOMAIN:
        return False
    path = (u.path or "").lower()
    return not any(path.endswith(ext) for ext in SKIP_EXT)

def clean_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")

    # remove obvious noise
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # optional: remove common layout blocks
    for selector in ["header", "footer", "nav", "aside"]:
        for tag in soup.select(selector):
            tag.decompose()

    title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
    text = soup.get_text("\n", strip=True)

    # normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    return title, text

def hash_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()

def crawl(seed_urls: list[str], max_pages=500, sleep_s=0.4):
    seen = set()
    queue = list(seed_urls)

    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        url = url.split("#")[0]
        if url in seen:
            continue
        if not is_allowed(url):
            continue

        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
                seen.add(url)
                continue

            title, text = clean_text(r.text)
            if len(text) < 200:  # ignore empty/low-content pages
                seen.add(url)
                continue

            fetched_at = datetime.now(timezone.utc).isoformat()
            record = {
                "source_type": "web",
                "url": url,
                "title": title,
                "fetched_at": fetched_at,
                "text": text,
                "hash": hash_text(text),
            }
            yield record

            # discover links
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select("a[href]"):
                href = a.get("href", "").strip()
                if not href:
                    continue
                nxt = urljoin(url, href)
                nxt = nxt.split("#")[0]
                if is_allowed(nxt) and nxt not in seen:
                    queue.append(nxt)

            seen.add(url)
            time.sleep(sleep_s)

        except Exception:
            seen.add(url)
            continue

if __name__ == "__main__":
    out = "kb/snapshots/web_raw.jsonl"
    seed = [BASE, urljoin(BASE, "/admissions/"), urljoin(BASE, "/fee-structure/")]
    import os
    os.makedirs("kb/snapshots", exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        for rec in crawl(seed_urls=seed, max_pages=800):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("Saved:", out)
