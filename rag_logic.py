"""rag_logic.py

Lightweight, Vercel-friendly retrieval engine (pure Python BM25-like).

Supports:
- JSONL KB (one JSON object per line) like kb/kb_current.jsonl
- JSON KB (a JSON array) like knowledge_base.json
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional


def _tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split(" ") if text else []


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # handles ...Z or +00:00
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).astimezone(timezone.utc)
    except Exception:
        return None


@dataclass
class _Index:
    doc_tf: List[Counter]
    doc_len: List[int]
    df: Counter
    N: int
    avgdl: float


class RAGPipeline:
    def __init__(self, data_source: str):
        self.data_source = data_source
        self.knowledge_base: List[Dict[str, Any]] = []
        self._last_mtime: Optional[float] = None
        self._index: Optional[_Index] = None
        self.reload()

    def _get_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self.data_source)
        except OSError:
            return None

    def _maybe_reload(self) -> None:
        mtime = self._get_mtime()
        if mtime and self._last_mtime and mtime != self._last_mtime:
            self.reload()

    def _normalize_item(self, d: Dict[str, Any]) -> Dict[str, Any]:
        # normalize content
        if "content" not in d:
            d["content"] = d.get("text", "") or ""

        # normalize source label
        if "sourceDocument" not in d:
            d["sourceDocument"] = d.get("doc_name") or d.get("title") or "FUUAST Website"

        # normalize page number (for PDFs)
        if "pageNumber" not in d:
            if "page" in d:
                d["pageNumber"] = d.get("page")

        return d

    def _load_data(self) -> List[Dict[str, Any]]:
        # If KB file exists but is empty, just return []
        try:
            if os.path.exists(self.data_source) and os.path.getsize(self.data_source) == 0:
                return []
        except Exception:
            pass

        # JSONL
        if self.data_source.endswith(".jsonl"):
            items: List[Dict[str, Any]] = []
            try:
                with open(self.data_source, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            items.append(self._normalize_item(obj))
                        elif isinstance(obj, list):
                            for x in obj:
                                if isinstance(x, dict):
                                    items.append(self._normalize_item(x))
                return items
            except FileNotFoundError:
                return []
            except Exception as e:
                # Bubble up to main.py so /api/health shows the error
                raise

        # JSON (array or {"items":[...]})
        try:
            with open(self.data_source, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "items" in data:
                data = data["items"]

            if isinstance(data, list):
                return [self._normalize_item(x) for x in data if isinstance(x, dict)]

            return []
        except FileNotFoundError:
            return []

    def reload(self) -> None:
        self.knowledge_base = self._load_data()
        self._last_mtime = self._get_mtime()
        self._index = self._build_index(self.knowledge_base)

    def _build_index(self, kb: List[Dict[str, Any]]) -> _Index:
        doc_tf: List[Counter] = []
        doc_len: List[int] = []
        df: Counter = Counter()
        N = len(kb)

        total_len = 0
        for doc in kb:
            tokens = _tokenize(doc.get("content", ""))
            tf = Counter(tokens)
            doc_tf.append(tf)
            dl = sum(tf.values())
            doc_len.append(dl)
            total_len += dl
            for term in tf.keys():
                df[term] += 1

        avgdl = (total_len / N) if N else 0.0
        return _Index(doc_tf=doc_tf, doc_len=doc_len, df=df, N=N, avgdl=avgdl)

    def _idf(self, term: str) -> float:
        idx = self._index
        if not idx or idx.N == 0:
            return 0.0
        df = idx.df.get(term, 0)
        return math.log((idx.N - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25_score(self, doc_index: int, query_terms: List[str], k1: float = 1.5, b: float = 0.75) -> float:
        idx = self._index
        if not idx:
            return 0.0

        tf = idx.doc_tf[doc_index]
        dl = idx.doc_len[doc_index]
        avgdl = idx.avgdl or 1.0

        score = 0.0
        for term in query_terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            idf = self._idf(term)
            denom = f + k1 * (1 - b + b * (dl / avgdl))
            score += idf * ((f * (k1 + 1)) / denom)
        return score

    def _recency_bonus(self, doc: Dict[str, Any]) -> float:
        # Prefer newer web chunks
        ts = doc.get("fetched_at") or doc.get("kb_build_date")
        dt = _parse_iso(ts)
        if not dt:
            return 0.0
        days = (datetime.now(timezone.utc) - dt).days
        if days <= 7:
            return 0.15
        if days <= 30:
            return 0.08
        return 0.0

    def _is_fee_query(self, query: str) -> bool:
        """Check if query is fee/cost related."""
        fee_words = ("fee", "tuition", "semester", "admission fee", "cost", "price", "structure", "charges")
        q_low = (query or "").lower()
        return any(word in q_low for word in fee_words)

    def _fee_bonus(self, doc: Dict[str, Any], is_fee_query: bool) -> float:
        """Add bonus if doc is PDF or has 'Fee Structure' in title, and query is fee-related."""
        if not is_fee_query:
            return 0.0

        source = (doc.get("sourceDocument") or "").lower()
        content = (doc.get("content") or "").lower()
        title = (doc.get("title") or "").lower()

        # Boost PDFs or Fee Structure pages
        is_pdf = (doc.get("source_type") == "pdf") or source.endswith(".pdf") or ("pdf" in source)
        has_fee_title = "fee structure" in title or "fee structure" in source

        if is_pdf or has_fee_title:
            return 0.25  # Significant boost for fee-relevant sources
        return 0.0

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        self._maybe_reload()

        if not self.knowledge_base or not self._index:
            return []

        q_terms = _tokenize(query)
        if not q_terms:
            return []

        # Detect fee-related queries for domain-aware ranking
        is_fee_query = self._is_fee_query(query)

        scores: List[Tuple[float, int]] = []
        for i, doc in enumerate(self.knowledge_base):
            base = self._bm25_score(i, q_terms)
            s = base + self._recency_bonus(doc) + self._fee_bonus(doc, is_fee_query)
            scores.append((s, i))

        scores.sort(reverse=True, key=lambda x: x[0])
        top = scores[: max(1, min(top_k * 2, 20))]  # Get 2x top_k to account for diversity filtering
        if not top:
            return []

        max_score = top[0][0] if top[0][0] > 0 else 1.0
        threshold = 0.10

        # Collect results with diversity constraint (max 2 chunks per source)
        results: List[Dict[str, Any]] = []
        source_counts: Dict[str, int] = {}

        for s, i in top:
            conf = float(s / max_score) if max_score else 0.0
            if conf < threshold:
                continue

            doc = dict(self.knowledge_base[i])
            source_key = doc.get("url") or doc.get("sourceDocument") or "unknown"

            # Skip if we already have 2 chunks from this source
            if source_counts.get(source_key, 0) >= 2:
                continue

            source_counts[source_key] = source_counts.get(source_key, 0) + 1
            doc["confidence_score"] = conf
            results.append(doc)

            # Stop once we have enough diverse results
            if len(results) >= top_k:
                break

        return results
