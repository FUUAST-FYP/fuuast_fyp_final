#!/usr/bin/env python3
"""
UniBot Retrieval Evaluation (tiny but viva-friendly)

What it measures:
- Recall@K for retrieval (did the expected page appear in top-K sources?)

How to run (from repo root):
  python eval/eval_retrieval.py --kb kb/kb_current.jsonl --k 6

Optional:
  python eval/eval_retrieval.py --kb kb/kb_current.jsonl --k 6 --out eval/results.json
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


def _init_rag(kb_path: str):
    """
    Initializes your project's RAGPipeline with best-effort signature matching.
    This avoids breaking if your RAGPipeline __init__ params change.
    """
    try:
        from rag_logic import RAGPipeline  # type: ignore
    except Exception as e:
        print("ERROR: Could not import rag_logic.RAGPipeline:", e, file=sys.stderr)
        raise

    sig = inspect.signature(RAGPipeline)
    kwargs = {}

    # Common parameter name variants
    for name in ("kb_path", "kb_jsonl_path", "kb_json_path", "kb_file", "kb"):
        if name in sig.parameters:
            kwargs[name] = kb_path
            break

    # Optional params - keep safe defaults if present
    if "cache_dir" in sig.parameters:
        kwargs["cache_dir"] = os.environ.get("RAG_CACHE_DIR", ".cache")
    if "embed_cache_path" in sig.parameters:
        kwargs["embed_cache_path"] = os.environ.get("EMBED_CACHE_PATH", ".cache/embed_cache.json")
    if "top_k" in sig.parameters:
        kwargs["top_k"] = 6

    try:
        return RAGPipeline(**kwargs)
    except TypeError as e:
        print("ERROR: Failed to initialize RAGPipeline with kwargs:", kwargs, file=sys.stderr)
        print("Signature was:", sig, file=sys.stderr)
        raise e


def _call_search(rag: Any, query: str, k: int):
    """
    Calls your pipeline retrieval method in a robust way.
    """
    if hasattr(rag, "search"):
        try:
            return rag.search(query, top_k=k)
        except TypeError:
            return rag.search(query, k)
    if hasattr(rag, "retrieve"):
        try:
            return rag.retrieve(query, top_k=k)
        except TypeError:
            return rag.retrieve(query, k)
    raise AttributeError("RAGPipeline has no .search() or .retrieve() method")


def _extract_source_strings(results: Any) -> List[str]:
    """
    Normalizes retrieval output into a list of source strings (urls/source ids).
    Supports list[dict], list[str], dict{results:...}, etc.
    """
    srcs: List[str] = []

    def add_one(x: Any):
        if not x:
            return
        if isinstance(x, str):
            srcs.append(x)
        elif isinstance(x, dict):
            # Most common keys across pipelines
            for key in ("url", "source_url", "source", "source_id", "sourceDocument", "title"):
                v = x.get(key)
                if isinstance(v, str) and v.strip():
                    srcs.append(v.strip())
            # Also handle nested source fields
            if "meta" in x and isinstance(x["meta"], dict):
                mv = x["meta"].get("url") or x["meta"].get("source")
                if isinstance(mv, str) and mv.strip():
                    srcs.append(mv.strip())

    if isinstance(results, dict):
        if "results" in results:
            for r in results["results"]:
                add_one(r)
        else:
            add_one(results)
    elif isinstance(results, list):
        for r in results:
            add_one(r)
    else:
        add_one(results)

    # de-dup while preserving order
    seen = set()
    out = []
    for s in srcs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _is_pass(expected_contains: List[str], sources: List[str]) -> bool:
    expected = [e.lower() for e in expected_contains]
    for s in sources:
        sl = s.lower()
        if any(e in sl for e in expected):
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", default="kb/kb_current.jsonl", help="Path to KB jsonl (default: kb/kb_current.jsonl)")
    parser.add_argument("--k", type=int, default=6, help="Top-K to evaluate (default: 6)")
    parser.add_argument("--questions", default="eval/questions.json", help="Questions JSON (default: eval/questions.json)")
    parser.add_argument("--out", default="", help="Optional output JSON path, e.g. eval/results.json")
    args = parser.parse_args()

    kb_path = args.kb
    q_path = args.questions

    if not Path(q_path).exists():
        print(f"ERROR: Questions file not found: {q_path}", file=sys.stderr)
        sys.exit(1)

    rag = _init_rag(kb_path)

    with open(q_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    results_out: Dict[str, Any] = {
        "kb": kb_path,
        "k": args.k,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(questions),
        "passed": 0,
        "failed": 0,
        "items": []
    }

    passed = 0
    for item in questions:
        qid = item.get("id", "")
        q = item["question"]
        expected_contains = item.get("expected_source_contains", [])
        t0 = time.time()
        try:
            retrieved = _call_search(rag, q, args.k)
            sources = _extract_source_strings(retrieved)
            ok = _is_pass(expected_contains, sources[:args.k])
        except Exception as e:
            ok = False
            sources = []
            retrieved = None
            err = str(e)
        else:
            err = ""

        dt = round((time.time() - t0) * 1000, 1)
        passed += 1 if ok else 0

        results_out["items"].append({
            "id": qid,
            "question": q,
            "pass": ok,
            "ms": dt,
            "expected_source_contains": expected_contains,
            "top_sources": sources[:args.k],
            "error": err,
        })

        status = "PASS" if ok else "FAIL"
        print(f"{status} {qid} ({dt} ms) — {q}")

    results_out["passed"] = passed
    results_out["failed"] = len(questions) - passed
    results_out["recall_at_k"] = round(passed / max(1, len(questions)), 4)

    print("\n=== Summary ===")
    print("Total:", results_out["total"])
    print("Passed:", results_out["passed"])
    print("Failed:", results_out["failed"])
    print(f"Recall@{args.k}:", results_out["recall_at_k"])

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results_out, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Saved:", str(out_path))


if __name__ == "__main__":
    main()
