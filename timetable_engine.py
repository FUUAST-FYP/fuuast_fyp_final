# timetable_engine.py
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import difflib

DAY_ALIASES = {
    "mon": "Monday", "monday": "Monday",
    "tue": "Tuesday", "tues": "Tuesday", "tuesday": "Tuesday",
    "wed": "Wednesday", "wednesday": "Wednesday",
    "thu": "Thursday", "thurs": "Thursday", "thursday": "Thursday",
    "fri": "Friday", "friday": "Friday",
    "sat": "Saturday", "saturday": "Saturday",
    "sun": "Sunday", "sunday": "Sunday",
}

TIME_RE = re.compile(r"\b(\d{1,2})[:\.](\d{2})\b")
SECTION_RE = re.compile(r"\bBS\s*\d+\s*[A-Z]\b", re.IGNORECASE)

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\s\.:]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _extract_day(text: str) -> Optional[str]:
    t = _norm(text)
    for k, v in DAY_ALIASES.items():
        if re.search(rf"\b{k}\b", t):
            return v
    return None

def _extract_time(text: str) -> Optional[str]:
    m = TIME_RE.search(text or "")
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    if hh > 23 or mm > 59:
        return None
    return f"{hh:02d}:{mm:02d}"

def _extract_section(text: str) -> Optional[str]:
    m = SECTION_RE.search(text or "")
    if not m:
        return None
    s = m.group(0).upper().replace(" ", "")
    return s

def _extract_teacher_candidate(text: str) -> Optional[str]:
    # supports: Dr, Mr, Ms, Mrs, Miss, Prof, Sir, Madam
    t = re.sub(r"\s+", " ", (text or "")).strip()

    STOP_AFTER = {"on", "at", "in", "from", "to", "for", "of", "by", "with"}
    DAY_WORDS = set(DAY_ALIASES.keys()) | {v.lower() for v in DAY_ALIASES.values()}

    def _trim(name: str) -> str:
        words = name.strip().split()
        cleaned = []
        for w in words:
            wl = w.lower().strip(".,")
            if wl in STOP_AFTER or wl in DAY_WORDS:
                break
            cleaned.append(w)
        return " ".join(cleaned).strip()

    m = re.search(
        r"\b(Dr|Mr|Ms|Mrs|Miss|Prof|Sir|Madam)\.?\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,4})\b",
        t, re.IGNORECASE
    )
    if m:
        title = m.group(1).replace(".", "")
        name = _trim(m.group(2))
        cand = f"{title} {name}".strip()
        return cand if len(name) >= 2 else cand  # keep even single-name

    m2 = re.search(r"\b(timetable|schedule)\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,4})\b", t, re.IGNORECASE)
    if m2:
        return _trim(m2.group(2))

    return None


@dataclass
class TTEntry:
    day: str
    section: str
    capacity: Optional[int]
    start: str
    end: str
    course: Optional[str]
    teacher: Optional[str]
    room: Optional[str]

class TimetableEngine:
    def __init__(self, json_path: str):
        p = Path(json_path)
        data = json.loads(p.read_text(encoding="utf-8"))
        self.meta = data.get("meta", {})
        self.entries: List[TTEntry] = []
        for e in data.get("entries", []):
            self.entries.append(TTEntry(
                day=str(e.get("day") or "").strip(),
                section=str(e.get("section") or "").strip(),
                capacity=e.get("capacity"),
                start=str(e.get("start") or "").strip(),
                end=str(e.get("end") or "").strip(),
                course=e.get("course"),
                teacher=e.get("teacher"),
                room=e.get("room"),
            ))

        # Build indexes
        self.teacher_names: List[str] = sorted({x.teacher for x in self.entries if x.teacher})
        self.section_names: List[str] = sorted({x.section for x in self.entries if x.section})

        self.by_teacher: Dict[str, Dict[str, List[TTEntry]]] = {}
        self.by_section: Dict[str, Dict[str, List[TTEntry]]] = {}

        for x in self.entries:
            if x.teacher:
                self.by_teacher.setdefault(x.teacher, {}).setdefault(x.day, []).append(x)
            self.by_section.setdefault(x.section, {}).setdefault(x.day, []).append(x)

        for t in self.by_teacher:
            for d in self.by_teacher[t]:
                self.by_teacher[t][d].sort(key=lambda z: z.start)

        for s in self.by_section:
            for d in self.by_section[s]:
                self.by_section[s][d].sort(key=lambda z: z.start)

        self.slots_by_day: Dict[str, set[str]] = {}
        for x in self.entries:
            self.slots_by_day.setdefault(x.day, set()).add(x.start)
        self.slots_by_day = {d: sorted(v) for d, v in self.slots_by_day.items()}  # type: ignore[assignment]

    HONORIFICS = {"dr", "mr", "ms", "mrs", "miss", "prof", "sir", "madam"}
    STOPWORDS = {
        "on","at","in","from","to","for","of","by","with",
        "availability","available","free","busy","schedule","timetable","routine","classes","class","lecture",
    }



    @staticmethod
    def _strip_honorifics(s: str) -> str:
        parts = _norm(s).split()
        parts = [p for p in parts if p not in TimetableEngine.HONORIFICS]
        return " ".join(parts).strip()

    @staticmethod
    def _tokens(s: str) -> set[str]:
        day_words = set(DAY_ALIASES.keys()) | {v.lower() for v in DAY_ALIASES.values()}
        toks = TimetableEngine._strip_honorifics(s).split()
        toks = [t for t in toks if t not in TimetableEngine.STOPWORDS and t not in day_words]
        return set(toks)


    def _best_match_teacher(self, query: str) -> Optional[str]:
        cand = _extract_teacher_candidate(query)
        q_raw = cand or query

        q_tokens = list(self._tokens(q_raw))
        if not q_tokens:
            return None

        # 1) normal safe matching: token overlap
        overlap_candidates = []
        for t in self.teacher_names:
            t_tokens = self._tokens(t)
            if set(q_tokens) & t_tokens:
                overlap_candidates.append(t)

        def best_by_full_ratio(cands: List[str]) -> Tuple[Optional[str], float]:
            best = None
            best_score = 0.0
            q_str = " ".join(q_tokens)
            for t in cands:
                t_str = " ".join(self._tokens(t))
                score = difflib.SequenceMatcher(None, q_str, t_str).ratio()
                if score > best_score:
                    best_score = score
                    best = t
            return best, best_score

        if overlap_candidates:
            best, score = best_by_full_ratio(overlap_candidates)
            return best if best and score >= 0.65 else None

        # 2) fallback: near-token match (handles OCR typos like sarim vs sarlm)
        best = None
        best_tok_score = 0.0
        for t in self.teacher_names:
            t_tokens = list(self._tokens(t))
            if not t_tokens:
                continue
            for qt in q_tokens:
                if len(qt) < 4:
                    continue
                for tt in t_tokens:
                    tok_score = difflib.SequenceMatcher(None, qt, tt).ratio()
                    if tok_score > best_tok_score:
                        best_tok_score = tok_score
                        best = t

        # High threshold to avoid wrong teacher guesses
        return best if best and best_tok_score >= 0.85 else None

    def _teacher_from_history(self, history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        if not history:
            return None
        # scan last turns for a teacher name mention
        for turn in reversed(history[-12:]):
            txt = turn.get("text") or ""
            t = self._best_match_teacher(txt)
            if t:
                return t
        return None

    def answer(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        msg = message or ""
        low = _norm(msg)

        day = _extract_day(msg)
        time = _extract_time(msg)
        section = _extract_section(msg)

        # Intent keywords
        is_avail = any(k in low for k in ["available", "availability", "free", "busy", "khali", "class", "lecture"])
        is_sched = any(k in low for k in ["timetable", "time table", "schedule", "classes", "routine"])
        is_room = "room" in low or "lab" in low

        # Did user explicitly mention a teacher name in THIS message?
        teacher_candidate = _extract_teacher_candidate(msg)  # e.g., "Miss Shazia", "Dr Uzma Afzal"

        # First try direct match (safe matching)
        teacher = self._best_match_teacher(msg)

        #  NEW: Day/time-only follow-up handling (e.g., user replies "Monday" or "mon" after bot asked day)
        # If user message contains ONLY day/time (no intent words, no teacher, no section), treat it as follow-up.
        followup_day_time_only = (
            (day or time) and
            not teacher_candidate and
            not section and
            not (is_avail or is_sched or is_room) and
            len(low.split()) <= 3
        )
        if followup_day_time_only:
            t_hist = self._teacher_from_history(history)
            if t_hist:
                teacher = t_hist
                is_avail = True  # force timetable availability flow

        timetable_intent = is_avail or is_sched or is_room or ("timetable" in low) or ("schedule" in low)

        #  NEW: If user mentioned a teacher, but that teacher is NOT in timetable, DO NOT use history fallback.
        if timetable_intent and teacher_candidate and not teacher:
            known = ", ".join(self.teacher_names[:12])
            more = "..." if len(self.teacher_names) > 12 else ""
            return {
                "answer": (
                    f"I couldn’t find **{teacher_candidate}** in the uploaded timetable.\n\n"
                    f"Available teachers in this timetable include: {known}{more}\n\n"
                    "Tip: use the exact name as written in timetable.json (e.g., 'Dr Uzma Afzal')."
                ),
                "sources": [self._source()],
            }

        #  Only use history teacher if user did NOT mention a teacher in current message
        if not teacher and is_avail and not teacher_candidate:
            teacher = self._teacher_from_history(history)

        # If timetable intent exists but still no teacher/section
        if timetable_intent and not teacher and not section:
            return {
                "answer": (
                    "I couldn't detect a teacher or section for timetable.\n"
                    "Try: 'Is Dr Uzma Afzal free on Monday?' or 'BS1A timetable Monday'."
                ),
                "sources": [self._source()],
            }

        # 1) Teacher availability / schedule
        if teacher and (is_avail or is_sched):
            if not day:
                return {
                    "answer": (
                        f"Please mention the day (Mon/Tue/...) so I can check {teacher}'s availability.\n"
                        f"Example: “Is {teacher} free on Monday?”"
                    ),
                    "sources": [self._source()],
                }

            classes = self.by_teacher.get(teacher, {}).get(day, [])
            if time:
                hit = next((c for c in classes if c.start == time), None)
                if hit:
                    return {
                        "answer": (
                            f"{teacher} is BUSY on {day} at {time}–{hit.end}.\n"
                            f"Class: {hit.course or '—'} | Section: {hit.section} | Room: {hit.room or '—'}"
                        ),
                        "sources": [self._source()],
                    }
                else:
                    return {
                        "answer": f"{teacher} is FREE on {day} at {time} (no class in timetable at that slot).",
                        "sources": [self._source()],
                    }

            busy_slots = {c.start for c in classes}
            all_slots = self.slots_by_day.get(day, [])
            free_slots = [s for s in all_slots if s not in busy_slots]

            lines = [f"{teacher} schedule on {day}:"]
            if classes:
                for c in classes:
                    lines.append(f"- {c.start}–{c.end}: {c.course or '—'} (Section {c.section}, Room {c.room or '—'})")
            else:
                lines.append("- No classes found (free for all listed slots).")

            if free_slots:
                lines.append("\nFree slots:")
                lines.append(" - " + ", ".join(free_slots))

            return {"answer": "\n".join(lines), "sources": [self._source()]}

        # 2) Section schedule / room query
        if section and (is_sched or is_room or "bs" in low):
            if day:
                classes = self.by_section.get(section, {}).get(day, [])
                if not classes:
                    return {"answer": f"No classes found for {section} on {day}.", "sources": [self._source()]}
                lines = [f"{section} timetable on {day}:"]
                for c in classes:
                    if is_room:
                        lines.append(f"- {c.start}–{c.end}: Room {c.room or '—'} ({c.course or '—'} | {c.teacher or '—'})")
                    else:
                        lines.append(f"- {c.start}–{c.end}: {c.course or '—'} ({c.teacher or '—'}) | Room {c.room or '—'}")
                return {"answer": "\n".join(lines), "sources": [self._source()]}

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            lines = [f"{section} weekly timetable summary:"]
            for d in days:
                classes = self.by_section.get(section, {}).get(d, [])
                if not classes:
                    continue
                lines.append(f"\n{d}:")
                for c in classes:
                    lines.append(f"- {c.start}–{c.end}: {c.course or '—'} ({c.teacher or '—'}) | {c.room or '—'}")
            return {"answer": "\n".join(lines), "sources": [self._source()]}

        return None


    def _source(self) -> Dict[str, Any]:
        src = self.meta.get("source_file", "Timetable")
        return {"label": f"Timetable ({src})", "sourceDocument": "Timetable", "pageNumber": None}
