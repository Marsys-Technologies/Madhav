#!/usr/bin/env python3
"""Watchdog (T2, second tap tier): if heartbeat.json is older than the stale threshold,
kill the stale pid and restart trackerd, and RECORD the resurrection as an event -- never
swallowed. Invoked every 60s by launchd StartInterval. Stdlib only.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import HEARTBEAT_JSON, LOGS_DIR, PIDFILE, WATCHDOG_STALE_THRESHOLD_S, ensure_runtime_dirs  # noqa: E402
from tracker_emit import emit  # noqa: E402

WRITER_ID = "watchdog"
TRACKERD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackerd.py")


def heartbeat_age_seconds():
    if not os.path.exists(HEARTBEAT_JSON):
        return None
    try:
        with open(HEARTBEAT_JSON, encoding="utf-8") as f:
            hb = json.load(f)
        ts = hb.get("ts")
        import datetime
        t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds()
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def kill_stale_pid():
    if not os.path.exists(PIDFILE):
        return None
    try:
        with open(PIDFILE, encoding="utf-8") as f:
            pid = int(f.read().strip())
        os.kill(pid, 9)
        return pid
    except (ValueError, ProcessLookupError, PermissionError, OSError):
        return None


def restart_daemon():
    ensure_runtime_dirs()
    log_path = os.path.join(LOGS_DIR, "trackerd.out.log")
    err_path = os.path.join(LOGS_DIR, "trackerd.err.log")
    with open(log_path, "a", encoding="utf-8") as out, open(err_path, "a", encoding="utf-8") as err:
        subprocess.Popen([sys.executable, TRACKERD_PATH], stdout=out, stderr=err, start_new_session=True)


def main():
    age = heartbeat_age_seconds()
    if age is None:
        # No heartbeat at all yet (first boot) -- start it, no resurrection event (nothing to resurrect).
        restart_daemon()
        return
    if age <= WATCHDOG_STALE_THRESHOLD_S:
        return
    killed_pid = kill_stale_pid()
    restart_daemon()
    emit(WRITER_ID, "daemon", {
        "event": "resurrection", "observed_gap_seconds": age, "killed_pid": killed_pid,
        "threshold_s": WATCHDOG_STALE_THRESHOLD_S,
    }, evidence_class="DERIVED", provenance="watchdog.py: heartbeat.json age exceeded threshold")
    print(f"RESURRECTION: heartbeat was {age:.0f}s stale (threshold {WATCHDOG_STALE_THRESHOLD_S}s); "
          f"killed pid={killed_pid}, restarted trackerd.", file=sys.stderr)


if __name__ == "__main__":
    main()
