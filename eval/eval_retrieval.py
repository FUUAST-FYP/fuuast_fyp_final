#!/usr/bin/env python3
"""
UniBot Retrieval Evaluation (viva-friendly)

Fixes included:
1) Robustly loads rag_logic.py even if you run from eval/ or rag_logic isn't importable as a package.
2) Registers the dynamically-loaded module in sys.modules BEFORE executing it (Python 3.13+/3.14 dataclasses fix).
3) Supports your RAGPipeline signature variants, including:
   - RAGPipeline(data_source: str)   <-- your current project
   - RAGPipeline(kb_path=...), kb_jsonl_path=..., etc.

Run:
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
from typing import Any, Dict, List
import importlib.util


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[1]  # parent of eval/


def _find_rag_logic(repo: Path) -> Path:
    direct = repo / "rag_logic.py"
    if direct.exists():
        return direct

    candidates = [
        repo / "api" / "rag_logic.py",
        repo / "backend" / "rag_logic.py",
        repo / "server" / "rag_logic.py",
        repo / "src" / "rag_logic.py",
    ]
    for c in candidates:
        if c.exists():
            return c

    matches = list(repo.rglob("rag_logic.py"))
    if matches:
        matches.sort(key=lambda p: len(p.parts))
        return matches[0]

    raise FileNotFoundError(f"Could not find rag_logic.py under: {repo}")


def _load_module_from_path(py_path: Path, module_name: str = "rag_logic_loaded"):
    spec = importlib.util.spec_from_file_location(module_name, str(py_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for: {py_path}")

    mod = importlib.util.module_from_spec(spec)

    # IMPORTANT: register before exec_module (dataclasses needs sys.modules[__module__])
    sys.modules[module_name] = mod

    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _init_rag(kb_path: str):
    repo = _repo_root()

    # Ensure repo root is importable for any local imports inside rag_logic.py
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    rag_logic_path = _find_rag_logic(repo)
    rag_mod = _load_module_from_path(rag_logic_path)

    if not hasattr(rag_mod, "RAGPipeline"):
        raise AttributeError(f"RAGPipeline not found in {rag_logic_path}")

    RAGPipeline = getattr(rag_mod, "RAGPipeline")
    sig = inspect.signature(RAGPipeline)

    kwargs: Dict[str, Any] = {}

    # Your project: RAGPipeline(data_source: str)
    if "data_source" in sig.parameters:
        kwargs["data_source"] = kb_path

    # Other common variants
    for name in ("kb_path", "kb_jsonl_path", "kb_json_path", "kb_file", "kb"):
        if name in sig.parameters:
            kwargs[name] = kb_path
            break

    # Optional params if your class supports them
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
        print("RAGPipeline signature was:", sig, file=sys.stderr)
        raise e


def _call_search(rag: Any, query: str, k: int):
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
    srcs: List[str] = []

    def add_one(x: Any):
        if not x:
            return
        if isinstance(x, str):
            srcs.append(x)
        elif isinstance(x, dict):
            for key in ("url", "source_url", "source", "source_id", "sourceDocument", "title"):
                v = x.get(key)
                if isinstance(v, str) and v.strip():
                    srcs.append(v.strip())
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

    # de-dup preserve order
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
    parser.add_argument("--kb", default="kb/kb_current.jsonl")
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--questions", default="eval/questions.json")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    if not Path(args.questions).exists():
        print(f"ERROR: Questions file not found: {args.questions}", file=sys.stderr)
        sys.exit(1)

    rag = _init_rag(args.kb)
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))

    results_out: Dict[str, Any] = {
        "kb": args.kb,
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
            err = ""
        except Exception as e:
            ok = False
            sources = []
            err = str(e)

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
