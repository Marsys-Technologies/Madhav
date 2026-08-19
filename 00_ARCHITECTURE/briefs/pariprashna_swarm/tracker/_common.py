"""Shared constants + pure functions for the Paripraśna Execution Observatory. Stdlib only."""
import json
import os
import subprocess

RUNTIME_DIR = os.path.expanduser("~/.pariprashna-tracker")
EVENTS_DIR = os.path.join(RUNTIME_DIR, "events")
LOGS_DIR = os.path.join(RUNTIME_DIR, "logs")
STATE_JSON = os.path.join(RUNTIME_DIR, "state.json")
TRACKER_DATA_JS = os.path.join(RUNTIME_DIR, "tracker_data.js")
HEARTBEAT_JSON = os.path.join(RUNTIME_DIR, "heartbeat.json")
COLLECTOR_SNAPSHOT_JSON = os.path.join(RUNTIME_DIR, "collector_snapshot.json")
PIDFILE = os.path.join(RUNTIME_DIR, "trackerd.pid")
SERVE_TOKEN_FILE = os.path.join(RUNTIME_DIR, "serve_token")

# Repo root: this file lives at 00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/_common.py
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PLAN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PLAN.yaml")

STALE_AMBER_S = 45
STALE_RED_S = 120
STALL_MINUTES = 20
HEARTBEAT_INTERVAL_FRESH_S = 20
HEARTBEAT_INTERVAL_IDLE_S = 60
IDLE_CYCLES_BEFORE_BACKOFF = 10
WATCHDOG_STALE_THRESHOLD_S = 90


def staleness_class(age_seconds):
    """Pure function: age (seconds, float/int) -> 'green' | 'amber' | 'red'.
    Mirrored byte-for-byte in tracker.html's JS stalenessClass()."""
    if age_seconds <= STALE_AMBER_S:
        return "green"
    if age_seconds <= STALE_RED_S:
        return "amber"
    return "red"


def load_plan():
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def atomic_write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def run(cmd, cwd=None, timeout=20):
    """Run a command, never raise. Returns (ok, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd or REPO_ROOT, timeout=timeout,
            capture_output=True, text=True,
        )
        return (r.returncode == 0, r.stdout, r.stderr)
    except Exception as e:  # noqa: BLE001 — collector signals must never raise
        return (False, "", str(e))


def ensure_runtime_dirs():
    os.makedirs(EVENTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
