"""Suvarṇa decisions log — the ONE authoritative record of what the native decided.

Fix 1 (review: a decisions log split across two branches breaks "newest decision wins"). Before
this module, "decided" state lived only as an event in EVENTS.jsonl (any actor could write one) and
as a hand-maintained JSONL under the old Nirmāṇa control tree. Neither was authoritative on its own.
This module is the single log every native gate reads (see server.py's per-tick reload and
state.py's `decision_log_status`); `emit.py` decision events remain useful as workflow signals
("requested") but no longer decide an item `done` by themselves — see Fix 2.

    python -m suvarna_tracker.decide --id N-21 --state decided --source "Native, session 'X', 2026-09-29: '...'" \\
        --detail "what was decided" --writer strategic-suvarna [--supersedes <id>] [--delegated-to <session>]
    python -m suvarna_tracker.decide --seed-from /path/to/old/DECISIONS.jsonl
    python -m suvarna_tracker.decide --mirror-to /path/to/committed/copy/DECISIONS.jsonl

Design rules:
- **Append-only**, one line per call, written under an exclusive `fcntl.flock` on a sidecar lock
  file (`<path>.lock`) so concurrent writers never interleave or race a "read-then-write" gap.
- **Every field required**: `id`, `state` (decided|delegated|superseded|revoked), `source` (who said
  it, where, when — at least 12 characters, never a bare "native"), `detail` (what was decided),
  `writer` (strategic-suvarna|steward only — the two roles authorized to write this log).
- **Reader tolerates malformed lines** (counts them, never raises) and resolves "latest wins per
  id" — a later line for the same id supersedes an earlier one, so a correction is a new line, not
  an edit of the old one (never rewrite a written line).
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suvarna_tracker.events import now_iso  # noqa: E402

STATES = {"decided", "delegated", "superseded", "revoked"}
WRITERS = {"strategic-suvarna", "steward"}
MIN_SOURCE_LEN = 12

SCHEMA_LINE = {
    "_schema": "suvarna.decisions.v1",
    "fields": ["id", "state", "decided_on", "source", "detail", "writer", "supersedes", "delegated_to", "ts"],
    "rule": "append-only; a correction is a new line that supersedes the old one (charter §11)",
}


class DecisionError(ValueError):
    pass


def default_path() -> str:
    home = os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna")
    return os.environ.get("SUVARNA_DECISIONS", os.path.join(home, "run", "DECISIONS.jsonl"))


def validate(rec: dict) -> dict:
    """Return a normalised decision record or raise DecisionError."""
    if not isinstance(rec, dict):
        raise DecisionError("record must be an object")
    if not rec.get("id"):
        raise DecisionError("id is required")
    if rec.get("state") not in STATES:
        raise DecisionError(f"state must be one of {sorted(STATES)}")
    source = rec.get("source") or ""
    if len(source) < MIN_SOURCE_LEN:
        raise DecisionError(f"source is required and must be at least {MIN_SOURCE_LEN} characters "
                            "(the native's own words, where, when)")
    if not rec.get("detail"):
        raise DecisionError("detail is required (what was decided)")
    if rec.get("writer") not in WRITERS:
        raise DecisionError(f"writer must be one of {sorted(WRITERS)}")
    out = dict(rec)
    out["ts"] = rec.get("ts") or now_iso()
    out.setdefault("decided_on", out["ts"][:10])
    return out


def _lock_path(path: str) -> str:
    return path + ".lock"


def append_decision(path: str, rec: dict) -> dict:
    """Validate and append one decision record atomically under an exclusive lock."""
    rec = validate(rec)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lock_fd = os.open(_lock_path(path), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        is_new = not os.path.exists(path) or os.path.getsize(path) == 0
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            if is_new:
                header = (json.dumps(SCHEMA_LINE, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
                os.write(fd, header)
            line = (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            os.write(fd, line)
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    return rec


def load_decisions(path: str) -> dict:
    """Return {'latest': {id: record}, 'malformed': N}. A later line for an id supersedes an
    earlier one. Tolerant: malformed/unparseable lines are skipped and counted, never fatal. The
    schema header line (if present) is recognised and skipped, not counted as malformed."""
    latest: dict[str, dict] = {}
    malformed = 0
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    malformed += 1
                    continue
                if not isinstance(d, dict):
                    malformed += 1
                    continue
                if d.get("_schema"):
                    continue
                if not d.get("id") or d.get("state") not in STATES:
                    malformed += 1
                    continue
                latest[d["id"]] = d
    except FileNotFoundError:
        pass
    return {"latest": latest, "malformed": malformed}


def seed_from(source_path: str, target_path: str) -> dict:
    """One-off: copy existing decision records from an old-format DECISIONS.jsonl into the new
    authoritative log. Refuses if the target already holds any records (the schema header alone is
    fine). Adds `writer: strategic-suvarna` to any record missing it; keeps the source's own
    `decided_on` and `source`."""
    existing = load_decisions(target_path)
    if existing["latest"]:
        raise DecisionError(f"{target_path} already has {len(existing['latest'])} record(s); refusing to seed")
    copied = 0
    with open(source_path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("_schema"):
                continue
            rec = dict(d)
            rec.setdefault("writer", "strategic-suvarna")
            append_decision(target_path, rec)
            copied += 1
    return {"copied": copied, "target": target_path}


def mirror_to(path: str, dest: str) -> dict:
    """Write the current log (verbatim, header included) to `dest` atomically (tmp + rename), so a
    committed copy can be refreshed without ever exposing a partial write."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        data = b""
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    tmp = f"{dest}.tmp.{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dest)
    return {"bytes": len(data), "dest": dest}


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Append to / manage the Suvarṇa decisions log")
    ap.add_argument("--path", default=None,
                    help="override the decisions log path (default: $SUVARNA_DECISIONS or $SUVARNA_HOME/run/DECISIONS.jsonl)")
    ap.add_argument("--id")
    ap.add_argument("--state", choices=sorted(STATES))
    ap.add_argument("--source", help="the native's own words, where, when")
    ap.add_argument("--detail", help="what was decided")
    ap.add_argument("--writer", choices=sorted(WRITERS))
    ap.add_argument("--supersedes", help="id of a prior decision this one supersedes")
    ap.add_argument("--delegated-to", help="the session a 'delegated' decision is delegated to")
    ap.add_argument("--seed-from", metavar="PATH",
                    help="one-off: copy records from an existing (old-format) DECISIONS.jsonl; "
                         "refuses if the target already has records")
    ap.add_argument("--mirror-to", metavar="PATH",
                    help="write the current log to PATH atomically (tmp + rename)")
    return ap


def main(argv=None) -> int:
    a = build_arg_parser().parse_args(argv)
    path = a.path or default_path()

    if a.seed_from:
        try:
            result = seed_from(a.seed_from, path)
        except (DecisionError, OSError) as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if a.mirror_to:
        result = mirror_to(path, a.mirror_to)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    required = {"--id": a.id, "--state": a.state, "--source": a.source, "--detail": a.detail, "--writer": a.writer}
    missing = [name for name, v in required.items() if not v]
    if missing:
        print(f"rejected: missing required arguments: {', '.join(missing)}", file=sys.stderr)
        return 2

    rec = {"id": a.id, "state": a.state, "source": a.source, "detail": a.detail, "writer": a.writer}
    if a.supersedes:
        rec["supersedes"] = a.supersedes
    if a.delegated_to:
        rec["delegated_to"] = a.delegated_to
    try:
        out = append_decision(path, rec)
    except DecisionError as exc:
        print(f"rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
