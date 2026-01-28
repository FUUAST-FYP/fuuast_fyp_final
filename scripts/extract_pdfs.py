import os, io, json, re, time, hashlib
from urllib.parse import urlparse
import requests
from pypdf import PdfReader
from datetime import datetime, timezone

PDF_LINKS = "kb/snapshots/pdf_links.jsonl"
OUT_PDF_RAW = "kb/snapshots/pdf_raw.jsonl"

HEADERS = {"User-Agent": "FUUAST-Academic-Assistant/1.0"}

def safe_name(url: str) -> str:
    p = urlparse(url)
    name = os.path.basename(p.path) or "document.pdf"
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)

def sha1(x: str) -> str:
    return hashlib.sha1(x.encode("utf-8")).hexdigest()

def main(max_pdfs=200, timeout=40, sleep_s=0.2, max_mb=25):
    if not os.path.exists(PDF_LINKS):
        print("No PDF links file found:", PDF_LINKS)
        return

    os.makedirs("kb/snapshots", exist_ok=True)

    seen = set()
    count = 0

    with open(OUT_PDF_RAW, "w", encoding="utf-8") as out:
        with open(PDF_LINKS, "r", encoding="utf-8") as f:
            for line in f:
                if count >= max_pdfs:
                    break
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                url = rec.get("url")
                if not url or url in seen:
                    continue
                seen.add(url)

                try:
                    r = requests.get(url, headers=HEADERS, timeout=timeout)
                    if r.status_code != 200:
                        continue

                    size_mb = len(r.content) / (1024 * 1024)
                    if size_mb > max_mb:
                        continue

                    reader = PdfReader(io.BytesIO(r.content))
                    fname = safe_name(url)
                    fetched_at = datetime.now(timezone.utc).isoformat()

                    for i, page in enumerate(reader.pages, start=1):
                        text = (page.extract_text() or "").strip()
                        if len(text) < 50:
                            continue
                        out.write(json.dumps({
                            "id": f"pdfweb::{sha1(url)[:12]}::{i}",
                            "source_type": "pdf",
                            "url": url,
                            "sourceDocument": fname,
                            "pageNumber": i,
                            "fetched_at": fetched_at,
                            "text": text
                        }, ensure_ascii=False) + "\n")

                    count += 1
                    time.sleep(sleep_s)

                except Exception:
                    continue

    print("Wrote:", OUT_PDF_RAW)

if __name__ == "__main__":
    main()
