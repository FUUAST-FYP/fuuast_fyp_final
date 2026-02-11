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
        return cand if cand else None

    m2 = re.search(r"\b(timetable|schedule)\s+of\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,4})\b", t, re.IGNORECASE)
    if m2:
        return _trim(m2.group(2)) or None

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
    """
    Timetable Q&A for timetable.json

    Fixes implemented:
    - Merge room-only duplicate rows that were mistakenly parsed as separate "courses"
    - Cleaner, non-boxy output formatting (no pipes/brackets)
    - Correct intent routing so "What class does BS1B have..." does NOT trigger teacher availability mode
    - Better teacher "did you mean" suggestions (no markdown)
    """
    HONORIFICS = {"dr", "mr", "ms", "mrs", "miss", "prof", "sir", "madam"}
    STOPWORDS = {
        "on","at","in","from","to","for","of","by","with",
        "availability","available","free","busy","khali","schedule","timetable","routine","classes","class","lecture",
    }

    def __init__(self, json_path: str):
        p = Path(json_path)
        data = json.loads(p.read_text(encoding="utf-8"))
        self.meta = data.get("meta", {})

        raw_entries: List[TTEntry] = []
        for e in data.get("entries", []):
            raw_entries.append(TTEntry(
                day=str(e.get("day") or "").strip(),
                section=str(e.get("section") or "").strip(),
                capacity=e.get("capacity"),
                start=str(e.get("start") or "").strip(),
                end=str(e.get("end") or "").strip(),
                course=e.get("course"),
                teacher=e.get("teacher"),
                room=e.get("room"),
            ))

        # Normalize to remove duplicates (Option A safety)
        self.entries: List[TTEntry] = self._normalize_entries(raw_entries)

        # Indexes
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
            self.slots_by_day.setdefault(x.day, set()).add(x.start)  # type: ignore[arg-type]
        self.slots_by_day = {d: sorted(v) for d, v in self.slots_by_day.items()}  # type: ignore[assignment]

    # --------------------
    # Normalization helpers
    # --------------------
    @staticmethod
    def _looks_like_room_token(s: Optional[str]) -> bool:
        if not s:
            return False
        x = (s or "").strip()
        if not x:
            return False
        xl = x.lower().strip()
        if xl in {"hall", "library"}:
            return True
        if re.fullmatch(r"(lab|room)\s*\d+", xl):
            return True
        if re.fullmatch(r"(lab|room)\s*[a-z]\d*", xl):
            return True
        # short single tokens that often represent room names
        if len(xl) <= 10 and any(k in xl for k in ["lab", "room"]):
            return True
        return False

    @classmethod
    def _normalize_entries(cls, entries: List[TTEntry]) -> List[TTEntry]:
        """
        Many timetable.json versions mistakenly include an extra row per slot:
          - real course row
          - room row stored in `course` with teacher=None
        We merge those into a single TTEntry with a real room value.
        """
        by_key: Dict[Tuple[str, str, str, str], List[TTEntry]] = {}
        for e in entries:
            key = (e.day, e.section, e.start, e.end)
            by_key.setdefault(key, []).append(e)

        out: List[TTEntry] = []

        for key, items in by_key.items():
            # identify "room-only" rows
            room_only = [i for i in items if (not i.teacher) and cls._looks_like_room_token(i.course) and not i.room]
            non_room = [i for i in items if i not in room_only]

            # choose a room value from any available source
            def pick_room() -> Optional[str]:
                for i in items:
                    if i.room and str(i.room).strip():
                        return str(i.room).strip()
                for i in room_only:
                    if i.course and str(i.course).strip():
                        return str(i.course).strip()
                return None

            room_value = pick_room()

            if non_room:
                for i in non_room:
                    out.append(TTEntry(
                        day=i.day,
                        section=i.section,
                        capacity=i.capacity,
                        start=i.start,
                        end=i.end,
                        course=i.course,
                        teacher=i.teacher,
                        room=(i.room or room_value),
                    ))
            else:
                # If we ONLY have room rows (rare), keep one as an empty class with room populated
                ro = room_only[0] if room_only else items[0]
                out.append(TTEntry(
                    day=ro.day,
                    section=ro.section,
                    capacity=ro.capacity,
                    start=ro.start,
                    end=ro.end,
                    course=ro.course if (ro.course and not cls._looks_like_room_token(ro.course)) else None,
                    teacher=ro.teacher,
                    room=room_value,
                ))

        # stable ordering
        out.sort(key=lambda z: (z.day, z.section, z.start, (z.course or "")))
        return out

    # --------------------
    # Matching helpers
    # --------------------
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

        overlap_candidates: List[str] = []
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

        # Fallback: near-token match (typos)
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

        return best if best and best_tok_score >= 0.85 else None

    def _teacher_from_history(self, history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        if not history:
            return None
        for turn in reversed(history[-12:]):
            txt = turn.get("text") or ""
            t = self._best_match_teacher(txt)
            if t:
                return t
        return None

    # --------------------
    # Formatting helpers
    # --------------------
    @staticmethod
    def _fmt_section_line(c: TTEntry) -> str:
        course = (c.course or "—").strip()
        teacher = (c.teacher or "").strip()
        room = (c.room or "").strip()

        line = f"- {c.start}–{c.end}: {course}"
        if teacher:
            line += f" — {teacher}"
        if room:
            line += f", {room}"
        return line

    @staticmethod
    def _fmt_teacher_line(c: TTEntry) -> str:
        course = (c.course or "—").strip()
        section = (c.section or "—").strip()
        room = (c.room or "—").strip()
        line = f"- {c.start}–{c.end}: {course}, {section}"
        if room and room != "—":
            line += f", {room}"
        return line

    # --------------------
    # Main answer
    # --------------------
    def answer(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        msg = message or ""
        low = _norm(msg)

        day = _extract_day(msg)
        time = _extract_time(msg)
        section = _extract_section(msg)

        # Intent keywords
        is_avail = any(k in low for k in ["available", "availability", "free", "busy", "khali"])
        is_sched = any(k in low for k in ["timetable", "time table", "schedule", "classes", "class", "lecture", "routine"])
        is_room = "room" in low or "lab" in low

        # Did user explicitly mention a teacher name in THIS message?
        teacher_candidate = _extract_teacher_candidate(msg)

        # First try direct match (safe matching)
        teacher = self._best_match_teacher(msg)

        timetable_intent = is_avail or is_sched or is_room or ("timetable" in low) or ("schedule" in low) or ("bs" in low)

        # Teacher mentioned but not found -> suggestions (no markdown)
        if timetable_intent and teacher_candidate and not teacher:
            # Suggest close matches (including cases like: "miss uzma")
            suggestions = difflib.get_close_matches(teacher_candidate, self.teacher_names, n=4, cutoff=0.55)
            if not suggestions:
                # also try without honorifics, but map back to full names
                stripped = self._strip_honorifics(teacher_candidate)
                stripped_map = {self._strip_honorifics(t): t for t in self.teacher_names}
                stripped_list = list(stripped_map.keys())
                stripped_sugs = difflib.get_close_matches(stripped, stripped_list, n=4, cutoff=0.55)
                suggestions = [stripped_map.get(s, s) for s in stripped_sugs]
            if suggestions:
                sug_lines = "\n".join(f"- {s}" for s in suggestions[:4])
                return {
                    "answer": f'I couldn’t find "{teacher_candidate}" in the uploaded timetable.\nDid you mean:\n{sug_lines}',
                    "sources": [self._source()],
                }
            return {
                "answer": f'I couldn’t find "{teacher_candidate}" in the uploaded timetable. Try using the exact name as written in the timetable.',
                "sources": [self._source()],
            }

        # Only use history teacher if user did NOT mention a teacher AND user did NOT mention a section
        if not teacher and is_avail and not teacher_candidate and not section:
            teacher = self._teacher_from_history(history)

        # If timetable intent exists but still no teacher/section
        if timetable_intent and not teacher and not section:
            return {
                "answer": (
                    'I couldn’t detect a teacher or section.\n'
                    'Try: "BS1A timetable Monday" or "Is Dr Uzma Afzal free on Monday?"'
                ),
                "sources": [self._source()],
            }

        # 1) Teacher availability / schedule
        if teacher and (is_avail or is_sched) and not section:
            if not day:
                return {
                    "answer": (
                        f"Please mention the day (Mon/Tue/...) so I can check {teacher}.\n"
                        f'Example: "Is {teacher} free on Monday?"'
                    ),
                    "sources": [self._source()],
                }

            classes = self.by_teacher.get(teacher, {}).get(day, [])
            if time:
                hit = next((c for c in classes if c.start == time), None)
                if hit:
                    details = self._fmt_teacher_line(hit).lstrip("- ").strip()
                    return {
                        "answer": f"{teacher} is BUSY on {day} at {time}–{hit.end}.\n{details}",
                        "sources": [self._source()],
                    }
                return {
                    "answer": f"{teacher} is FREE on {day} at {time} (no class in timetable at that slot).",
                    "sources": [self._source()],
                }

            # Full schedule
            if not classes:
                return {
                    "answer": f"{teacher} has no classes listed on {day}.",
                    "sources": [self._source()],
                }

            lines = [self._fmt_teacher_line(c) for c in classes]

            # Free slots list (optional, but useful)
            busy_slots = {c.start for c in classes}
            all_slots = self.slots_by_day.get(day, [])
            free_slots = [s for s in all_slots if s not in busy_slots]
            if free_slots:
                lines.append("")
                lines.append("Free slots: " + ", ".join(free_slots))

            return {"answer": "\n".join(lines), "sources": [self._source()]}

        # 2) Section schedule / room query
        if section and (is_sched or is_room or "bs" in low):
            # if user asked a specific day
            if day:
                classes = self.by_section.get(section, {}).get(day, [])
                if not classes:
                    return {"answer": f"No classes found for {section} on {day}.", "sources": [self._source()]}

                # if user asked a specific time
                if time:
                    hit = next((c for c in classes if c.start == time), None)
                    if not hit:
                        return {"answer": f"No class found for {section} on {day} at {time}.", "sources": [self._source()]}
                    if is_room:
                        room = (hit.room or "—").strip()
                        return {"answer": f"- {hit.start}–{hit.end}: {room}", "sources": [self._source()]}
                    return {"answer": self._fmt_section_line(hit), "sources": [self._source()]}

                # full day view
                if is_room:
                    lines = []
                    for c in classes:
                        room = (c.room or "—").strip()
                        course = (c.course or "—").strip()
                        teacher2 = (c.teacher or "—").strip()
                        lines.append(f"- {c.start}–{c.end}: {room} — {course}, {teacher2}")
                    return {"answer": "\n".join(lines), "sources": [self._source()]}

                lines = [self._fmt_section_line(c) for c in classes]
                return {"answer": "\n".join(lines), "sources": [self._source()]}

            # weekly summary
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            out_lines: List[str] = []
            for d in days:
                classes = self.by_section.get(section, {}).get(d, [])
                if not classes:
                    continue
                out_lines.append(f"{d}:")
                out_lines.extend(self._fmt_section_line(c) for c in classes)
                out_lines.append("")

            if not out_lines:
                return {"answer": f"No classes found for {section}.", "sources": [self._source()]}

            return {"answer": "\n".join(out_lines).rstrip(), "sources": [self._source()]}

        return None

    def _source(self) -> Dict[str, Any]:
        src = self.meta.get("source_file", "Timetable")
        return {"label": f"Timetable ({src})", "sourceDocument": "Timetable", "pageNumber": None}
