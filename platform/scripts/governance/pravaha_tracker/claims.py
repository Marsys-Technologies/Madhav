"""Exclusive worker claims backed by the current event log, never a cached snapshot."""
from __future__ import annotations

import copy
import datetime as dt
import fcntl
import json
import os
import uuid

from .events import validate
from .state import build_snapshot


class ClaimError(ValueError):
    pass


def _timestamp(value: dt.datetime) -> str:
    if value.tzinfo is None:
        raise ClaimError("claim time must include a timezone")
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _read(fd: int) -> list[dict]:
    os.lseek(fd, 0, os.SEEK_SET)
    data = b""
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        data += chunk
    events = []
    for line in data.splitlines():
        try:
            events.append(validate(json.loads(line)))
        except (ValueError, UnicodeDecodeError):
            continue
    return events


def _append(fd: int, event: dict) -> dict:
    event = validate(event)
    os.lseek(fd, 0, os.SEEK_END)
    os.write(fd, (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode())
    os.fsync(fd)
    return event


def _latest(events: list[dict], item_id: str) -> dict | None:
    return next((e for e in reversed(events) if e.get("kind") == "claim" and e.get("item") == item_id), None)


def _claim_status(model: dict, events: list[dict], item_id: str, now: dt.datetime) -> str:
    """Use the current event log for dependency and decision eligibility.

    Detectors are completion evidence, not claim prerequisites.  The candidate's
    detector is omitted so an unmeasured, unstarted item can still be claimed;
    dependency detectors retain their normal guarded-event semantics.
    """
    view_model = copy.deepcopy(model)
    for item in view_model["items"]:
        item.setdefault("track", "_claims")
        item.setdefault("title", item["id"])
        if item["id"] == item_id:
            item.pop("detector", None)
    if not view_model.get("tracks"):
        view_model["tracks"] = [{"id": "_claims", "title": "Claims"}]
    view_model.setdefault("decisions", [])
    view_model.setdefault("streams", [])
    snapshot = build_snapshot(view_model, events, {}, {}, {}, now=now)
    return next(row["status"] for track in snapshot["tracks"]
                for row in track["items"] if row["id"] == item_id)


def _record(path: str, event: dict) -> None:
    directory = os.path.join(os.path.dirname(path), "claims")
    os.makedirs(directory, exist_ok=True)
    target = os.path.join(directory, event["worker_id"] + ".json")
    temporary = target + ".tmp." + uuid.uuid4().hex
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(event, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)


def _locked(path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def _close(fd: int) -> None:
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


def claim_item(path: str, model: dict, item_id: str, stream: str, worker_id: str,
               lease_s: int, *, now: dt.datetime | None = None, branch: str | None = None,
               head: str | None = None, step: str | None = None) -> dict:
    """Claim a ready item under the event-log lock; recover expired work in the same transaction."""
    now = now or dt.datetime.now(dt.timezone.utc)
    ts = _timestamp(now)
    config = model.get("control_plane", {}).get("claims", {})
    if stream not in config.get("streams", []):
        raise ClaimError(f"stream {stream} does not use worker claims")
    if not worker_id or os.path.basename(worker_id) != worker_id or worker_id in (".", ".."):
        raise ClaimError("invalid worker_id")
    if lease_s <= 0 or lease_s > int(config.get("lease_s", 5400)):
        raise ClaimError("lease outside model limit")
    item = next((row for row in model["items"] if row["id"] == item_id), None)
    if item is None or item.get("owner") != stream:
        raise ClaimError("item is unknown or owned by another stream")
    fd = _locked(path)
    try:
        events = _read(fd)
        last = _latest(events, item_id)
        if last and last["state"] in ("acquired", "renewed"):
            expires = dt.datetime.fromisoformat(last["expires_at"])
            if now < expires:
                raise ClaimError(f"item is claimed by {last['worker_id']} until {last['expires_at']}")
            expired = _append(fd, {**last, "state": "expired", "ts": ts})
            _record(path, expired)
        else:
            expired = None
        status = _claim_status(model, events, item_id, now)
        # an item whose last claim ended (expired now, expired earlier, or released) keeps its running/review
        # state from its step events; the next claimant RECOVERS it rather than being refused (owner reset 2026-10-07)
        ended = bool(last) and last["state"] in ("expired", "released")
        if status != "ready" and not ((expired or ended) and status in ("running", "review")):
            raise ClaimError(f"item is not claimable: {status}")
        # amendment §3: a worker holds at most one active claim on an item still being built, plus one on an item that
        # is only WAITING (its last step event registered a review — the PR is open and the lane owes nothing until a
        # verdict, a merge or a ruling arrives). Two active claims is the ceiling.
        active = []
        for other in model["items"]:
            held = _latest(events, other["id"])
            if held and held.get("worker_id") == worker_id and held["state"] in ("acquired", "renewed"):
                if now < dt.datetime.fromisoformat(held["expires_at"]):
                    active.append(other["id"])
        if active:
            waiting = [i for i in active if _claim_status(model, events, i, now) == "review"]
            if len(active) >= 2 or len(waiting) != len(active):
                raise ClaimError("worker already holds an active claim on an item that is not waiting")
        expires_at = _timestamp(now + dt.timedelta(seconds=lease_s))
        claim = _append(fd, {"kind": "claim", "actor": f"stream-{stream}:{worker_id}",
                             "item": item_id, "state": "acquired", "worker_id": worker_id,
                             "claim_id": uuid.uuid4().hex, "lease_s": lease_s,
                             "expires_at": expires_at, "ts": ts,
                             "branch": branch or (expired or {}).get("branch"),
                             "head": head or (expired or {}).get("head"),
                             "step": step or (expired or {}).get("step")})
        _record(path, claim)
        return claim
    finally:
        _close(fd)


def renew_claim(path: str, model: dict, item_id: str, worker_id: str, claim_id: str,
                lease_s: int, *, now: dt.datetime | None = None, branch: str | None = None,
                head: str | None = None, step: str | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    ts = _timestamp(now)
    if lease_s <= 0 or lease_s > int(model.get("control_plane", {}).get("claims", {}).get("lease_s", 5400)):
        raise ClaimError("lease outside model limit")
    fd = _locked(path)
    try:
        last = _latest(_read(fd), item_id)
        if not last or last.get("claim_id") != claim_id or last.get("worker_id") != worker_id or last["state"] not in ("acquired", "renewed"):
            raise ClaimError("claim is not active for this worker")
        if now >= dt.datetime.fromisoformat(last["expires_at"]):
            raise ClaimError("claim has expired")
        event = _append(fd, {**last, "state": "renewed", "ts": ts,
                             "expires_at": _timestamp(now + dt.timedelta(seconds=lease_s)),
                             "lease_s": lease_s, "branch": branch or last.get("branch"),
                             "head": head or last.get("head"), "step": step or last.get("step")})
        _record(path, event)
        return event
    finally:
        _close(fd)


def release_claim(path: str, item_id: str, worker_id: str, claim_id: str) -> dict:
    fd = _locked(path)
    try:
        last = _latest(_read(fd), item_id)
        if not last or last.get("claim_id") != claim_id or last.get("worker_id") != worker_id or last["state"] not in ("acquired", "renewed"):
            raise ClaimError("claim is not active for this worker")
        event = _append(fd, {**last, "state": "released", "ts": _timestamp(dt.datetime.now(dt.timezone.utc))})
        _record(path, event)
        return event
    finally:
        _close(fd)
