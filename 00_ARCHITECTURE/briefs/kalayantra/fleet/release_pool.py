#!/usr/bin/env python3
"""Release the initial four builders only after the reviewed B-7 gates hold."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import urlopen

ROOT = Path("/Users/Dev/kalayantra")
TRACKER = "http://127.0.0.1:8767/api/state"
BOOTSTRAP = ("B-0", "B-1", "B-1v", "B-2", "B-3", "B-3b", "B-4", "B-5", "B-6", "B-7p", "B-7")
SOURCES = {
    "charter_sha256": "00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md",
    "model_sha256": "00_ARCHITECTURE/control/kalayantra/plan_model.json",
    "fleet_sha256": "00_ARCHITECTURE/briefs/kalayantra/fleet/kalayantra_fleet.sh",
    "executor_sha256": "00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py",
}


class Refused(Exception):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise Refused(f"{path.name} is not an object")
    return value


def lane_lock_held(run: Path, lane: str) -> bool:
    with (run / f"{lane}.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(lock, fcntl.LOCK_UN)
        return False


def validate(root: Path, state: dict, *, audit_ok: bool, verifier_held: dict[str, bool]) -> None:
    run = root / "run"
    if (root / "HOLD").exists() or any((run / f"STOP_{lane}").exists() for lane in ("sutradhara", "v1", "v2")):
        raise Refused("HOLD or lane STOP is present")
    if (run / "KY_VERIFIERS").read_text().strip() != "2" or not all(verifier_held.get(lane) for lane in ("v1", "v2")):
        raise Refused("both verifier supervisor lanes must be available")
    if not audit_ok:
        raise Refused("campaign audit is not clean")
    backoff = run / "KY_QUOTA_BACKOFF"
    if backoff.exists():
        import time
        try:
            if int(backoff.read_text().strip()) > time.time():
                raise Refused("quota backoff is active")
        except ValueError as exc:
            raise Refused("quota backoff is malformed") from exc
    statuses = {item["id"]: item["status"] for track in state.get("tracks", []) for item in track.get("items", [])}
    missing = [item for item in BOOTSTRAP if statuses.get(item) != "done"]
    if missing:
        raise Refused(f"bootstrap items not guarded done: {', '.join(missing)}")
    install = read_json(run / "TRACKER_INSTALL_RECEIPT.json")
    if install.get("accepted") is not True or install.get("audit_available") is not True:
        raise Refused("atomic-claim control plane is not installed")
    receipt_path = run / "LAUNCH_RECEIPT.json"
    receipt = read_json(receipt_path)
    if receipt.get("mode") != "launch" or not receipt.get("checks") or any(not c.startswith("ok:") and not c.startswith("warn:") for c in receipt["checks"]):
        raise Refused("launch preflight receipt failed")
    camp = root / "wt/campaign"
    head = subprocess.run(["git", "-C", str(camp), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    if receipt.get("campaign_head") != head:
        raise Refused("launch receipt names an older campaign head")
    for field, source in SOURCES.items():
        if receipt.get(field) != digest(camp / source):
            raise Refused(f"launch receipt has stale {field}")
    verdict = read_json(run / "LAUNCH_ACCEPTED.json")
    if verdict.get("result") != "ACCEPTED" or verdict.get("by") not in ("v1", "v2"):
        raise Refused("independent launch verdict is absent or rejected")
    if verdict.get("launch_receipt_sha256") != digest(receipt_path):
        raise Refused("launch verdict does not bind the current receipt")


def release(root: Path = ROOT) -> None:
    run = root / "run"
    # A second invocation cannot interleave with the final recheck and atomic write.
    with (run / "KY_WORKERS.release.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with urlopen(TRACKER, timeout=5) as response:
            state = json.load(response)
        audit = subprocess.run([str(root / "bin/ky"), "audit", "--since", "kickoff"],
                               env={**os.environ, "KY_STREAM": "S"}, capture_output=True, text=True, timeout=30)
        validate(root, state, audit_ok=audit.returncode == 0,
                 verifier_held={lane: lane_lock_held(run, lane) for lane in ("v1", "v2")})
        workers = run / "KY_WORKERS"
        current = workers.read_text().strip() if workers.exists() else "0"
        if current not in ("0", "4"):
            raise Refused(f"unexpected initial pool size {current!r}")
        if (root / "HOLD").exists() or any((run / f"STOP_{lane}").exists() for lane in ("sutradhara", "v1", "v2")):
            raise Refused("HOLD or lane STOP appeared before release")
        if current == "4":
            print("ALREADY RELEASED: 4")
            return
        with tempfile.NamedTemporaryFile(mode="w", dir=run, prefix="KY_WORKERS.", delete=False) as out:
            out.write("4\n")
            temp = Path(out.name)
        os.replace(temp, workers)
        print("RELEASED: 4")


if __name__ == "__main__":
    try:
        release()
    except (Refused, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(1)
