"""rag_logic.py

Lightweight, Vercel-friendly retrieval engine.

Why this file matters:
- Your Vercel runtime was crashing with FUNCTION_INVOCATION_FAILED because the previous
  version imported scikit-learn at import-time (not installed on Vercel) and also had
  two conflicting RAGPipeline definitions.

This version is pure-Python (no numpy/scipy/sklearn) and safe to import in serverless.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


def _tokenize(text: str) -> List[str]:
    """Very small tokenizer good enough for short university KB chunks."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split(" ") if text else []


@dataclass
class _Index:
    doc_tf: List[Counter]
    doc_len: List[int]
    df: Counter
    N: int
    avgdl: float


class RAGPipeline:
    """BM25-like retrieval in pure Python.

    Expected KB format: a JSON array of dicts. Each dict should include:
      - content (str)
      - sourceDocument (str) and/or category
      - pageNumber (int) optional
      - url (str) optional
    """

    def __init__(self, data_source: str):
        self.data_source = data_source
        self.knowledge_base: List[Dict[str, Any]] = []
        self._last_mtime: float | None = None
        self._index: _Index | None = None
        self.reload()

    # -------------------------
    # Loading / reloading
    # -------------------------
    def _get_mtime(self) -> float | None:
        try:
            return os.path.getmtime(self.data_source)
        except OSError:
            return None

    def _maybe_reload(self) -> None:
        mtime = self._get_mtime()
        if mtime and self._last_mtime and mtime != self._last_mtime:
            self.reload()

    def _load_data(self) -> List[Dict[str, Any]]:
    try:
        # JSONL support
        if self.data_source.endswith(".jsonl"):
            items: List[Dict[str, Any]] = []
            with open(self.data_source, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)

                    # if someone accidentally wrote a JSON array on a line, flatten it
                    if isinstance(obj, list):
                        for x in obj:
                            if isinstance(x, dict):
                                items.append(x)
                    elif isinstance(obj, dict):
                        items.append(obj)

            # normalize keys so the rest of your code works
            for d in items:
                if "content" not in d:
                    d["content"] = d.get("text", "")  # your crawler uses "text"
                if "sourceDocument" not in d:
                    d["sourceDocument"] = d.get("title") or "FUUAST Website"
                if "pageNumber" not in d:
                    d["pageNumber"] = d.get("page")  # if you ever add pdf pages
            return items

        # JSON support (old knowledge_base.json)
        with open(self.data_source, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "items" in data:
                data = data["items"]
            if isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and "content" not in d:
                        d["content"] = d.get("text", "")
                return data
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

    # -------------------------
    # BM25 scoring
    # -------------------------
    def _idf(self, term: str) -> float:
        idx = self._index
        if not idx or idx.N == 0:
            return 0.0
        df = idx.df.get(term, 0)
        # BM25 smoothed IDF
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

    # -------------------------
    # Public search API
    # -------------------------
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Return top_k docs with confidence_score in [0..1]."""
        self._maybe_reload()

        if not self.knowledge_base or not self._index:
            return []

        q_terms = _tokenize(query)
        if not q_terms:
            return []

        scores: List[Tuple[float, int]] = []
        for i in range(len(self.knowledge_base)):
            s = self._bm25_score(i, q_terms)
            scores.append((s, i))

        scores.sort(reverse=True, key=lambda x: x[0])
        top = scores[: max(1, min(top_k, 10))]
        if not top:
            return []

        max_score = top[0][0] if top[0][0] > 0 else 1.0
        threshold = 0.10  # keep only meaningful matches

        results: List[Dict[str, Any]] = []
        for s, i in top:
            conf = float(s / max_score) if max_score else 0.0
            if conf < threshold:
                continue
            doc = dict(self.knowledge_base[i])
            doc["confidence_score"] = conf
            results.append(doc)
        return results
