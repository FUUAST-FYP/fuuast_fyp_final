#!/usr/bin/env python3
"""
rotate_kb.py

Keeps a small history of previous KB builds under kb/snapshots/ as:
kb/snapshots/kb_YYYY-MM-DD.jsonl

Usage:
  python scripts/rotate_kb.py --keep 7
"""

from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timezone

KB_PATH = os.path.join("kb", "kb_current.jsonl")
SNAP_DIR = os.path.join("kb", "snapshots")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=int, default=7)
    args = ap.parse_args()

    os.makedirs(SNAP_DIR, exist_ok=True)
    if not os.path.exists(KB_PATH):
        print("No KB file found:", KB_PATH)
        return

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snap_path = os.path.join(SNAP_DIR, f"kb_{stamp}.jsonl")
    shutil.copyfile(KB_PATH, snap_path)
    print("Snapshot saved:", snap_path)

    # Cleanup
    files = sorted([f for f in os.listdir(SNAP_DIR) if f.startswith("kb_") and f.endswith(".jsonl")])
    if len(files) <= args.keep:
        return
    to_delete = files[: len(files) - args.keep]
    for f in to_delete:
        try:
            os.remove(os.path.join(SNAP_DIR, f))
        except Exception:
            pass

    print("Rotation complete. Keeping:", args.keep)

if __name__ == "__main__":
    main()
