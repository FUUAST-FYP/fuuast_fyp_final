import json
<<<<<<< HEAD
import math
import os
import re
from collections import Counter
from typing import List, Dict, Any


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return text.split(" ")


class RAGPipeline:
    """
    Lightweight BM25-like retrieval in pure Python
    - No numpy/scipy/sklearn (keeps Vercel function small)
    """

    def __init__(self, data_source: str):
        self.data_source = data_source
        self.knowledge_base: List[Dict[str, Any]] = []
        self._last_mtime = None

        # BM25 stats
        self._doc_tf: List[Counter] = []
        self._doc_len: List[int] = []
        self._df: Counter = Counter()
        self._N = 0
        self._avgdl = 0.0

        self.reload()

=======
import os
import re
from typing import List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGPipeline:
    def __init__(self, data_source: str):
        self.data_source = data_source
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.knowledge_base: List[Dict[str, Any]] = []
        self.doc_vectors = None
        self._last_mtime = None
        self.reload()

    def reload(self) -> None:
        self.knowledge_base = self._load_data()
        self._fit_vectorizer()
        self._last_mtime = self._get_mtime()

>>>>>>> 25f0622 (Initial commit)
    def _get_mtime(self):
        try:
            return os.path.getmtime(self.data_source)
        except OSError:
            return None

    def _maybe_reload(self):
        mtime = self._get_mtime()
        if mtime and self._last_mtime and mtime != self._last_mtime:
            self.reload()

    def _load_data(self) -> List[Dict[str, Any]]:
        try:
            with open(self.data_source, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

<<<<<<< HEAD
    def reload(self) -> None:
        self.knowledge_base = self._load_data()
        self._last_mtime = self._get_mtime()
        self._build_index()

    def _build_index(self):
        self._doc_tf = []
        self._doc_len = []
        self._df = Counter()
        self._N = len(self.knowledge_base)

        total_len = 0
        for doc in self.knowledge_base:
            tokens = _tokenize(doc.get("content", ""))
            tf = Counter(tokens)
            self._doc_tf.append(tf)
            dl = sum(tf.values())
            self._doc_len.append(dl)
            total_len += dl

            # document frequency
            for term in tf.keys():
                self._df[term] += 1

        self._avgdl = (total_len / self._N) if self._N else 0.0

    def _idf(self, term: str) -> float:
        # BM25-style IDF (smoothed)
        df = self._df.get(term, 0)
        if self._N == 0:
            return 0.0
        return math.log((self._N - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25_score(self, doc_index: int, query_terms: List[str], k1: float = 1.5, b: float = 0.75) -> float:
        tf = self._doc_tf[doc_index]
        dl = self._doc_len[doc_index]
        avgdl = self._avgdl or 1.0

        score = 0.0
        for term in query_terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            idf = self._idf(term)
            denom = f + k1 * (1 - b + b * (dl / avgdl))
            score += idf * ((f * (k1 + 1)) / denom)
        return score
=======
    @staticmethod
    def _clean(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _fit_vectorizer(self) -> None:
        if not self.knowledge_base:
            self.doc_vectors = None
            return
        corpus = [self._clean(x.get("content", "")) for x in self.knowledge_base]
        self.doc_vectors = self.vectorizer.fit_transform(corpus)
>>>>>>> 25f0622 (Initial commit)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        self._maybe_reload()

<<<<<<< HEAD
        if not self.knowledge_base:
            return []

        q_terms = _tokenize(query)
        if not q_terms:
            return []

        scores = []
        for i in range(len(self.knowledge_base)):
            s = self._bm25_score(i, q_terms)
            scores.append((s, i))

        scores.sort(reverse=True, key=lambda x: x[0])
        top = scores[:max(1, min(top_k, 10))]

        max_score = top[0][0] if top and top[0][0] > 0 else 1.0
        threshold = 0.10  # tune if needed

        results = []
        for s, i in top:
            norm = float(s / max_score) if max_score else 0.0
            if norm < threshold:
                continue
            doc = dict(self.knowledge_base[i])
            doc["confidence_score"] = norm
            results.append(doc)
=======
        if not self.knowledge_base or self.doc_vectors is None:
            return []

        clean_query = self._clean(query)
        q_vec = self.vectorizer.transform([clean_query])
        sims = cosine_similarity(q_vec, self.doc_vectors).flatten()

        threshold = 0.10
        top_indices = sims.argsort()[-top_k:][::-1]

        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            score = float(sims[idx])
            if score >= threshold:
                doc = dict(self.knowledge_base[idx])
                doc["confidence_score"] = score
                results.append(doc)
>>>>>>> 25f0622 (Initial commit)

        return results
