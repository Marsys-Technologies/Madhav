"""Pravāha event log — the campaign's single source of real-time truth.

Every participant (Stream A, Stream B, the native, the steward, the tracker itself) appends one JSON
line per state change to ``$PRAVAHA_HOME/run/EVENTS.jsonl``. The dashboard is a pure function of
the plan model, this log and live detectors, so it is never more than one engine tick (1 s) behind
the last line written.

Design rules (carried from the Suvarṇa tracker, which proved them):
- **Append-only, atomic lines.** One ``os.write`` on an ``O_APPEND`` descriptor, then ``fsync``, so
  two streams writing at the same instant never interleave within a line.
- **Tolerant reader.** A malformed line is skipped and counted, never fatal; the count is shown.
- **Rotation-safe tail.** The reader tracks (inode, offset) and re-reads from the start if the file
  is replaced or truncated.

Added for Pravāha:
- **Model-aware validation at write time** (``validate_against_model``): an event naming an item or
  decision that is not in the plan model is refused, and an item event from a stream that does not
  own the item is refused. A typo can never make work invisible, and one stream can never move the
  other stream's items.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import threading
from dataclasses import dataclass, field

KINDS = {"item", "decision", "heartbeat", "note", "metric", "message", "ack", "claim", "verdict"}
# Message bus (autonomy, 2026-09-30): the steward and the streams talk through the event log, so no
# human relays messages. A message is addressed to one party; the addressee acks it once acted on.
PARTIES = {"A", "B", "C", "steward"}
ITEM_STATES = {"ready", "running", "review", "blocked", "parked", "failed", "done"}
DECISION_STATES = {"pending", "requested", "decided", "delegated"}
# Actors allowed to write item events for any item (the campaign steward and the native).
OVERRIDE_ACTORS = {"steward", "native"}


class EventError(ValueError):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def validate(ev: dict, *, allow_model_party: bool = False) -> dict:
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
        # Earned signal (CLAUDE.md §N.8): 'done' only with evidence behind it.
        if ev.get("state") == "done" and not ev.get("evidence"):
            raise EventError("an item may only be marked done with 'evidence'")
        if ev.get("state") in ("blocked", "failed", "parked") and not ev.get("detail"):
            raise EventError(f"a {ev.get('state')} item needs 'detail' (the reason)")
    if kind == "decision":
        if not ev.get("decision"):
            raise EventError("decision events need 'decision'")
        if ev.get("state") not in DECISION_STATES:
            raise EventError(f"decision state must be one of {sorted(DECISION_STATES)}")
        if ev.get("state") in ("decided", "delegated") and not ev.get("detail"):
            raise EventError("a decided decision needs 'detail' (what was decided)")
    if kind == "metric" and not ev.get("name"):
        raise EventError("metric events need 'name'")
    if kind == "claim":
        if ev.get("state") not in ("acquired", "renewed", "released", "expired"):
            raise EventError("invalid claim state")
        if not all(ev.get(key) for key in ("item", "worker_id", "claim_id", "expires_at")):
            raise EventError("claim needs item, worker_id, claim_id and expires_at")
        try:
            dt.datetime.fromisoformat(ev["expires_at"])
        except ValueError as exc:
            raise EventError("claim expiry must be ISO-8601") from exc
    if kind == "verdict":
        if not ev.get("item") or ev.get("result") not in ("ACCEPTED", "REJECTED"):
            raise EventError("verdict needs an item and ACCEPTED or REJECTED result")
        if ev.get("phase") not in ("pre_merge", "post_deploy", "artifact"):
            raise EventError("verdict phase must be pre_merge, post_deploy or artifact")
        if not ev.get("detail"):
            raise EventError("verdict needs measured detail")
        head, digest = ev.get("head"), ev.get("artifact_digest")
        if bool(head) == bool(digest):
            raise EventError("verdict needs exactly one head or artifact_digest")
        if head and not re.fullmatch(r"[0-9a-f]{40}", head):
            raise EventError("verdict head must be a full Git SHA")
        if digest and not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise EventError("verdict artifact_digest must be SHA-256")
        if ev["phase"] == "artifact" and not digest:
            raise EventError("artifact verdict needs artifact_digest")
        if ev["phase"] != "artifact" and not head:
            raise EventError("code verdict needs head")
    if kind == "message":
        if ev.get("to") not in PARTIES and not (allow_model_party and
                re.fullmatch(r"[A-Z][A-Z0-9_-]*", str(ev.get("to", "")))):
            raise EventError(f"message 'to' must be one of {sorted(PARTIES)}")
        if not ev.get("msg_id") or not ev.get("detail"):
            raise EventError("a message needs 'msg_id' and 'detail'")
    if kind == "ack" and not ev.get("msg_id"):
        raise EventError("an ack needs 'msg_id'")
    return out


def actor_stream(actor: str) -> str | None:
    """'stream-A' / 'stream-A:subtask' -> 'A'. None for non-stream actors."""
    a = (actor or "").strip()
    if a.lower().startswith("stream-"):
        return a[len("stream-"):].split(":", 1)[0].upper() or None
    return None


def validate_against_model(ev: dict, model: dict) -> None:
    """Refuse events that name unknown items/decisions, or that move another stream's item."""
    if ev.get("kind") == "item":
        items = {i["id"]: i for i in model.get("items", [])}
        it = items.get(ev["item"])
        if it is None:
            raise EventError(f"unknown item {ev['item']!r} — not in the plan model")
        if it.get("done_by") in ("decision", "join") and ev.get("state") == "done":
            raise EventError(f"item {ev['item']} is completed by its {it['done_by']}, not by an event")
        owner = str(it.get("owner", "")).upper()
        actor = ev.get("actor", "")
        if actor in OVERRIDE_ACTORS:
            return
        s = actor_stream(actor)
        if s is None:
            raise EventError(f"actor {actor!r} may not move items; use stream-A, stream-B, steward or native")
        if owner and owner != s:
            raise EventError(f"item {ev['item']} is owned by {owner}; {actor} may not change it")
    if ev.get("kind") == "verdict":
        item = next((row for row in model.get("items", []) if row["id"] == ev["item"]), None)
        if item is None:
            raise EventError(f"unknown verdict item {ev['item']!r}")
        expected = model.get("control_plane", {}).get("verdict_stream")
        if not expected or actor_stream(ev["actor"]) != expected:
            raise EventError("only the model's independent verdict stream may review")
    if ev.get("kind") in ("message", "ack"):
        actor = ev.get("actor", "")
        s = actor_stream(actor)
        if actor not in ("steward", "native") and s is None:
            raise EventError(f"actor {actor!r} may not send or ack messages")
        policy = model.get("control_plane", {}).get("message_policy")
        if ev.get("kind") == "message" and policy:
            parties = {row["id"] for row in model.get("streams", [])}
            parties.update(policy)
            if ev["to"] != "steward" and ev["to"] not in parties:
                raise EventError(f"unknown message party {ev['to']!r}")
            if s is not None and s not in parties:
                raise EventError(f"unknown message actor stream {s!r}")
            if s is not None and ev["to"] != "steward" and ev["to"] not in policy.get(s, []):
                raise EventError(f"message from {s} to {ev['to']} is not allowed by the model")
        elif ev.get("kind") == "message" and s is not None and ev.get("to") != "steward":
            raise EventError("a stream may only message the steward")
        if ev.get("kind") == "message" and actor in ("steward", "native") and ev.get("to") == "steward":
            raise EventError("the steward messages streams, not itself")
    if ev.get("kind") == "decision":
        ids = {d["id"] for d in model.get("decisions", [])}
        if ev["decision"] not in ids:
            raise EventError(f"unknown decision {ev['decision']!r} — not in the plan model")
        if ev.get("state") in ("decided", "delegated") and ev.get("actor") not in ("native", "steward"):
            raise EventError("only the native (or the steward recording the native's words) may decide")
        outcomes = model.get("control_plane", {}).get("decision_outcomes")
        if outcomes and ev.get("state") in ("decided", "delegated"):
            allowed = set(outcomes.get("final", [])) | set(outcomes.get("open", []))
            if ev.get("outcome") not in allowed:
                raise EventError(f"decision outcome must be one of {sorted(allowed)}")


def append(path: str, ev: dict, model: dict | None = None) -> dict:
    """Validate (and, with a model, check ownership) and append one event atomically."""
    ev = validate(ev, allow_model_party=bool(model and model.get("control_plane", {}).get("message_policy")))
    if model is not None:
        validate_against_model(ev, model)
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
            self._partial = lines.pop()
            before = (len(self.events), self.malformed)
            for raw in lines:
                if not raw.strip():
                    continue
                try:
                    self.events.append(validate(json.loads(raw.decode("utf-8")), allow_model_party=True))
                except (ValueError, UnicodeDecodeError, EventError):
                    self.malformed += 1
            return (len(self.events), self.malformed) != before
