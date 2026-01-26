"""groq_rest.py

Minimal Groq REST client (OpenAI-compatible API).

This avoids adding heavy SDK dependencies. It only needs `requests`.
"""

from __future__ import annotations

import os
from typing import Optional

import requests


def groq_chat_completion(user_text: str, context_text: str, sources_text: str) -> str:
    """Create a chat completion via Groq's OpenAI-compatible endpoint.

    Required env vars:
      - GROQ_API_KEY
    Optional:
      - GROQ_MODEL (default: llama-3.1-8b-instant)
      - GROQ_API_BASE (default: https://api.groq.com/openai/v1)
    """

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
    base = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1").strip()
    url = f"{base.rstrip('/')}/chat/completions"

    system = (
        "You are an official university website assistant for FUUAST. "
        "Answer in 1-3 short sentences. "
        "Use ONLY the provided context. "
        "If context is insufficient, say you don't have that information."
    )

    user = (
        f"Context (verified university sources):\n{context_text}\n\n"
        f"Sources list:\n{sources_text}\n\n"
        f"Question: {user_text}\n"
        "Answer (short, grounded):"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 220,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(f"Unexpected Groq response: {data}")

    return (text or "").strip()
