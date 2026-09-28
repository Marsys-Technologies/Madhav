"""Suvarṇa event log — the campaign's single source of real-time truth.

Every role (conductor, builders, reviewers, scribe, build operator, monitor, and the strategic
session) appends one JSON line per state change to ``$SUVARNA_HOME/run/EVENTS.jsonl``. The
tracker's view is a pure function of the plan model, this log, and live detectors — so the view
is never more than one poll interval behind the last line written.

Design rules:
- **Append-only.** A line is written with a single ``os.write`` on an ``O_APPEND`` descriptor and
  fsync'd, so concurrent writers never interleave within a line.
- **Tolerant reader.** A malformed line is skipped and counted, never fatal; the count is shown on
  the dashboard so corruption is visible, not silent.
- **Rotation-safe tail.** The reader tracks (inode, offset). If the file shrinks or is replaced, it
  re-reads from the start.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import threading
from dataclasses import dataclass, field

KINDS = {"item", "decision", "heartbeat", "note", "metric"}
ITEM_STATES = {"ready", "running", "review", "blocked", "parked", "failed", "done"}
DECISION_STATES = {"pending", "requested", "decided", "delegated"}


class EventError(ValueError):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def validate(ev: dict) -> dict:
    """Return a normalised event or raise EventError. Used by writers and the reader alike."""
    if not isinstance(ev, dict):
        raise EventError("event must be an object")
    kind = ev.get("kind")
    if kind not in KINDS:
        raise EventError(f"kind must be one of {sorted(KINDS)}")
    if not ev.get("actor"):
        raise EventError("actor is required")
    ts = ev.get("ts") or now_iso()
    try:
        dt.datetime.fromisoformat(ts)
    except ValueError as exc:
        raise EventError(f"ts not ISO-8601: {ts!r}") from exc
    out = dict(ev, ts=ts)
    if kind == "item":
        if not ev.get("item"):
            raise EventError("item events need 'item'")
        if ev.get("state") not in ITEM_STATES:
            raise EventError(f"item state must be one of {sorted(ITEM_STATES)}")
        # Earned signal: an event may only claim 'done' with evidence behind it.
        if ev.get("state") == "done" and not ev.get("evidence"):
            raise EventError("an item may only be marked done with 'evidence'")
    if kind == "decision":
        if not ev.get("decision"):
            raise EventError("decision events need 'decision'")
        if ev.get("state") not in DECISION_STATES:
            raise EventError(f"decision state must be one of {sorted(DECISION_STATES)}")
        if ev.get("state") in ("decided", "delegated") and not ev.get("detail"):
            raise EventError("a decided decision needs 'detail' (what was decided)")
    return out


def append(path: str, ev: dict) -> dict:
    """Validate and append one event atomically. Creates the directory if needed."""
    ev = validate(ev)
    line = (json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)  # one write per line: POSIX append keeps lines whole
        os.fsync(fd)
    finally:
        os.close(fd)
    return ev


@dataclass
class EventLog:
    """Incremental, rotation-safe reader of the event log."""

    path: str
    events: list = field(default_factory=list)
    malformed: int = 0
    _inode: int | None = None
    _offset: int = 0
    _partial: bytes = b""
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def refresh(self) -> bool:
        """Read any new complete lines. Returns True if anything changed."""
        with self._lock:
            try:
                st = os.stat(self.path)
            except FileNotFoundError:
                changed = bool(self.events) or self.malformed
                self.events, self.malformed = [], 0
                self._inode, self._offset, self._partial = None, 0, b""
                return bool(changed)
            if self._inode != st.st_ino or st.st_size < self._offset:
                # new file, rotated, or truncated: start over
                self.events, self.malformed = [], 0
                self._inode, self._offset, self._partial = st.st_ino, 0, b""
            if st.st_size == self._offset:
                return False
            with open(self.path, "rb") as f:
                f.seek(self._offset)
                chunk = f.read()
            self._offset += len(chunk)
            data = self._partial + chunk
            lines = data.split(b"\n")
            self._partial = lines.pop()  # incomplete trailing line (no newline yet)
            before = (len(self.events), self.malformed)
            for raw in lines:
                if not raw.strip():
                    continue
                try:
                    self.events.append(validate(json.loads(raw.decode("utf-8"))))
                except (ValueError, UnicodeDecodeError, EventError):
                    self.malformed += 1
            return (len(self.events), self.malformed) != before
