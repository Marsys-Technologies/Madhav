#!/usr/bin/env python3
"""
Background daemon that auto-reconciles state.json from session_queue.yaml whenever
the queue changes, and pushes to production GCS.

Run once, runs forever:
    nohup python3 /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/tracker_sync_daemon.py > /tmp/tracker_sync.log 2>&1 &

Stop:
    pkill -f tracker_sync_daemon.py

What it does, every 5 seconds:
  1. Check mtime of session_queue.yaml. If unchanged → sleep 5s.
  2. If changed → load queue, load state.json, compute target impl-status per item,
     update only items whose status would advance (never downgrade).
  3. Atomic write state.json + append a "RECONCILE" activity row.
  4. Run deploy_to_gcs.sh state (silent unless fails).
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = "/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_orchestrator"
QUEUE = f"{ROOT}/session_queue.yaml"
STATE = f"{ROOT}/tracker/state.json"
DEPLOY = f"{ROOT}/tracker/deploy_to_gcs.sh"
POLL_SEC = 5

RANK = {
    "not_started": 0,
    "in_progress": 1,
    "merged_branch": 2,
    "in_review": 3,
    "merged_main": 4,
    "deployed": 5,
    "verified": 6,
}

def log(msg: str) -> None:
    print(f"[{datetime.now().isoformat()}] {msg}", flush=True)

def reconcile() -> int:
    """Return number of items updated."""
    try:
        with open(QUEUE) as f:
            queue = yaml.safe_load(f)
        with open(STATE) as f:
            state = json.load(f)
    except Exception as e:
        log(f"load error: {e}")
        return 0

    # Aggregate target status per item from completed sessions
    target_by_item: dict[str, dict] = {}
    for s in queue.get("sessions", []) or []:
        if s.get("status") != "complete":
            continue
        tu = s.get("tracker_update", {}) or {}
        iid = tu.get("item")
        if not iid:
            continue
        impl = tu.get("impl", "merged_main")
        rank = RANK.get(impl, 0)
        cur = target_by_item.get(iid)
        if cur is None or rank > cur["rank"]:
            target_by_item[iid] = {
                "impl": impl,
                "brief": tu.get("brief", "locked"),
                "rank": rank,
                "session_id": s.get("id"),
                "branch": s.get("branch", "feature/build-orch/" + (s.get("stream") or "?").lower()),
            }

    # Apply, only advancing (never downgrading)
    updated: list[tuple[str, str, str, str]] = []
    now = datetime.now(timezone.utc).isoformat()
    for track in state.get("tracks", []):
        for item in track.get("items", []):
            iid = item["id"]
            t = target_by_item.get(iid)
            if not t:
                continue
            cur_impl = (item.get("impl") or {}).get("status", "not_started")
            if RANK.get(cur_impl, 0) >= t["rank"]:
                continue
            item.setdefault("impl", {})
            item["impl"]["status"] = t["impl"]
            item["impl"]["session_id"] = t["session_id"]
            item["impl"]["branch"] = t["branch"]
            item["impl"]["completed_at"] = now
            updated.append((iid, cur_impl, t["impl"], t["session_id"]))

    if not updated:
        return 0

    state["meta"]["last_updated"] = now[:10]
    state.setdefault("activity", []).insert(0, {
        "time": now,
        "text": f"AUTO-SYNC: {len(updated)} items advanced (" + ", ".join(u[0] for u in updated) + ")",
    })
    state["activity"] = state["activity"][:200]

    # Atomic write
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE)

    for u in updated:
        log(f"  → {u[0]:8s} {u[1]:14s} -> {u[2]:14s} ({u[3]})")
    return len(updated)

def push_gcs() -> bool:
    try:
        r = subprocess.run(
            ["bash", DEPLOY, "state"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            log(f"gcs push failed: {r.stderr.strip()[:200]}")
            return False
        return True
    except Exception as e:
        log(f"gcs push error: {e}")
        return False

def main() -> None:
    log(f"tracker_sync_daemon started (poll every {POLL_SEC}s)")
    log(f"queue:  {QUEUE}")
    log(f"state:  {STATE}")
    log(f"deploy: {DEPLOY}")
    last_mtime = 0.0
    while True:
        try:
            mtime = os.path.getmtime(QUEUE)
        except FileNotFoundError:
            log("session_queue.yaml not found; retrying in 30s")
            time.sleep(30)
            continue
        if mtime != last_mtime:
            last_mtime = mtime
            n = reconcile()
            if n > 0:
                log(f"reconciled {n} items; pushing to GCS")
                if push_gcs():
                    log("GCS push OK")
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("interrupted; exiting")
