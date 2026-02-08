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

    # Title + name (up to 4 words)
    m = re.search(r"\b(Dr|Mr|Ms|Mrs|Miss|Prof|Sir|Madam)\.?\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})\b", t, re.IGNORECASE)
    if m:
        title = m.group(1)
        name = m.group(2)
        cand = f"{title} {name}".replace(".", "")
        return cand.strip()

    # If user says "timetable of X" or "schedule of X"
    m2 = re.search(r"\b(timetable|schedule)\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})\b", t, re.IGNORECASE)
    if m2:
        return m2.group(2).strip()

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

        self.slots_by_day: Dict[str, List[str]] = {}
        for x in self.entries:
            self.slots_by_day.setdefault(x.day, set()).add(x.start)
        self.slots_by_day = {d: sorted(list(v)) for d, v in self.slots_by_day.items()}

    HONORIFICS = {"dr", "mr", "ms", "mrs", "miss", "prof", "sir", "madam"}

    @staticmethod
    def _strip_honorifics(s: str) -> str:
        parts = _norm(s).split()
        parts = [p for p in parts if p not in TimetableEngine.HONORIFICS]
        return " ".join(parts).strip()

    @staticmethod
    def _tokens(s: str) -> set[str]:
        return set(TimetableEngine._strip_honorifics(s).split())

    def _best_match_teacher(self, query: str) -> Optional[str]:
        cand = _extract_teacher_candidate(query)
        q_raw = cand or query
        q_clean = self._strip_honorifics(q_raw)

        q_tokens = self._tokens(q_raw)
        if not q_clean or len(q_tokens) == 0:
            return None

        # Only consider teachers that share at least 1 real name token
        candidates = []
        for t in self.teacher_names:
            t_tokens = self._tokens(t)
            if q_tokens & t_tokens:
                candidates.append(t)

        if not candidates:
            return None

        # Fuzzy match only among the safe candidates
        best = None
        best_score = 0.0
        for t in candidates:
            score = difflib.SequenceMatcher(None, q_clean, self._strip_honorifics(t)).ratio()
            if score > best_score:
                best_score = score
                best = t

        return best if best_score >= 0.65 else None

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
        day = _extract_day(msg)
        time = _extract_time(msg)
        section = _extract_section(msg)

        # Determine intent keywords
        low = _norm(msg)
        is_avail = any(k in low for k in ["available", "availability", "free", "busy", "khali", "class", "lecture"])
        is_sched = any(k in low for k in ["timetable", "schedule", "classes", "routine"])
        is_room = "room" in low or "lab" in low

        teacher = self._best_match_teacher(msg)
        if not teacher and is_avail:
            teacher = self._teacher_from_history(history)

        timetable_intent = is_avail or is_sched or ("timetable" in low) or ("schedule" in low)

        if timetable_intent and not teacher and not section:
            return {
                "answer": (
                    "I couldn't find that teacher name in the timetable.\n"
                    "Try the full name as written in the timetable (e.g., 'Dr FirstName LastName')."
                ),
                "sources": [self._source()],
            }

        # 1) Teacher availability
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
                # check if teacher has a class starting at that time
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

            # no time: show schedule + free slots
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

            # no day: week summary
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

        # Not a timetable-related question
        return None

    def _source(self) -> Dict[str, Any]:
        src = self.meta.get("source_file", "Timetable")
        return {"label": f"Timetable ({src})", "sourceDocument": "Timetable", "pageNumber": None}
