#!/usr/bin/env python3
"""Daemon: collect -> project -> write -> stamp heartbeat. Out of process, no relationship
to any agent's turn boundary. Single instance enforced by a pidfile with a liveness check.
Adaptive cadence: 20s while things are changing, backs off to 60s after 10 idle cycles,
snaps back to 20s the instant something changes. Stdlib only.
"""
import datetime
import fcntl
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    BLIND_WINDOW_JSON, HEARTBEAT_INTERVAL_FRESH_S, HEARTBEAT_INTERVAL_IDLE_S, HEARTBEAT_JSON,
    IDLE_CYCLES_BEFORE_BACKOFF, PIDFILE, RUNTIME_DIR, STOPPED_INTENTIONALLY_JSON,
    compute_blind_window, ensure_runtime_dirs, atomic_write_json,
)
import collect  # noqa: E402
import project  # noqa: E402
from tracker_emit import emit  # noqa: E402

WRITER_ID = "trackerd"


# Kept open (never closed) for the process's entire lifetime -- the flock it holds is what
# actually enforces single-instance, so the file descriptor must outlive acquire_pidfile().
# A module-level reference is required: without one, Python could garbage-collect the file
# object and close the fd (silently releasing the lock) at any point after the function
# returns.
_pidfile_handle = None


def deploy_static_dashboard():
    """serve.py serves ONLY ~/.pariprashna-tracker/ (never the repo checkout, per the
    'tracker only reads git, never writes into another surface' constraint on where code
    vs. runtime state lives) -- so the static tracker.html must be copied into the runtime
    dir for the LAN server to have anything to serve at all. Cheap; run once at daemon
    start (a redeploy of tracker.html means restarting the daemon anyway)."""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.html")
    dst = os.path.join(RUNTIME_DIR, "tracker.html")
    ensure_runtime_dirs()
    shutil.copyfile(src, dst)


def acquire_pidfile():
    """Single-instance enforcement via an exclusive, non-blocking flock() held on the
    pidfile for this process's entire lifetime -- NOT the read-check-then-write this used
    to be. That older version had a real, exploitable race: two processes starting within
    the same instant could both read the pidfile, both see the recorded pid as dead (or the
    file absent), and both proceed to write their own pid -- neither one re-checks after
    writing, so both keep running. This is exactly what happened in production on
    2026-08-20 (two independent resurrection paths -- launchd KeepAlive and a watchdog
    restart -- fired close together): two live trackerd processes, both writing
    heartbeat.json/state.json every cycle, racing each other, one crashing outright when its
    os.replace() target tmp file had already been consumed by the other (see
    atomic_write_json's hardening in _common.py for the other half of that fix).
    flock(LOCK_EX | LOCK_NB) is atomic at the kernel level: only one process can ever hold
    it, the loser fails immediately (EAGAIN/EWOULDBLOCK -> OSError) with no window for a
    race, and the OS releases the lock automatically on process exit -- including a bare
    SIGKILL, so a dead process never leaves a stale lock behind (unlike the pidfile's
    *contents*, which are just informational now, kept only for humans/other tooling to read
    "who is it").
    """
    global _pidfile_handle
    ensure_runtime_dirs()
    f = open(PIDFILE, "a+")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.seek(0)
        held_by = f.read().strip() or "unknown"
        f.close()
        print(f"trackerd already running (pidfile lock held, recorded pid: {held_by}); exiting.",
              file=sys.stderr)
        sys.exit(1)
    f.seek(0)
    f.truncate()
    f.write(str(os.getpid()))
    f.flush()
    _pidfile_handle = f  # must stay open (and thus locked) for the rest of this process's life


def check_blind_window():
    """Item (d): on daemon start (real starts only -- never called from --selftest or
    --once in a way that could stamp a spurious record over a real one), decide whether
    this restart followed an unexplained gap and, if so, write a record that OUTLIVES this
    restart. STOPPED_INTENTIONALLY.json is read here but NEVER written or deleted by
    trackerd.py -- only tracker-stop writes it, only tracker-start clears it (see both)."""
    ensure_runtime_dirs()
    now = datetime.datetime.now(datetime.timezone.utc)
    last_heartbeat_ts = None
    if os.path.exists(HEARTBEAT_JSON):
        try:
            with open(HEARTBEAT_JSON, encoding="utf-8") as f:
                hb = json.load(f)
            last_heartbeat_ts = datetime.datetime.strptime(
                hb["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            last_heartbeat_ts = None
    marker_present = os.path.exists(STOPPED_INTENTIONALLY_JSON)

    blind = compute_blind_window(last_heartbeat_ts, now, marker_present)
    if blind is not None:
        atomic_write_json(BLIND_WINDOW_JSON, {
            **blind, "acknowledged": False,
            "detected_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        emit(WRITER_ID, "anomaly", {
            "event": "blind_window_detected",
            "message": f"{blind['duration_s']:.0f}s blind window ({blind['gap_start_ts']} -> "
                       f"{blind['gap_end_ts']}), no intentional-stop marker found",
            **blind,
        }, evidence_class="DERIVED", provenance="trackerd.py check_blind_window at daemon start")
        print(f"BLIND WINDOW: {blind['duration_s']:.0f}s gap with no intentional-stop marker "
              f"({blind['gap_start_ts']} -> {blind['gap_end_ts']}). Recorded to "
              f"{BLIND_WINDOW_JSON} -- will not clear on its own.", file=sys.stderr)
    elif marker_present and last_heartbeat_ts is not None:
        gap_s = (now - last_heartbeat_ts).total_seconds()
        if gap_s > 1:
            emit(WRITER_ID, "daemon", {"event": "resumed_from_intentional_stop", "gap_seconds": gap_s},
                 evidence_class="DERIVED",
                 provenance="trackerd.py check_blind_window: STOPPED_INTENTIONALLY.json present")


def one_cycle():
    t0 = time.time()
    signal_failures = []
    try:
        snapshot = collect.main()
        mf = snapshot.get("mirror_fetch") or {}
        if not mf.get("ok"):
            signal_failures.append({"signal": "mirror_fetch", "provenance": mf.get("error"),
                                     "consecutive_failures": mf.get("consecutive_failures")})
        for key in ("git_lane_branches", "git_worktrees", "github_prs", "github_rate_limit",
                    "recent_merged_prs", "code_provenance", "deploy"):
            sig = snapshot.get(key) or {}
            if sig.get("evidence_class") == "UNKNOWN":
                signal_failures.append({"signal": key, "provenance": sig.get("provenance")})
    except Exception as e:  # noqa: BLE001 -- one cycle failing must never kill the daemon
        signal_failures.append({"signal": "collect.main", "provenance": str(e)})

    changed = False
    try:
        state_before = None
        from _common import STATE_JSON
        if os.path.exists(STATE_JSON):
            with open(STATE_JSON, encoding="utf-8") as f:
                state_before = f.read()
        state = project.project()
        from _common import STATE_JSON as SJ
        with open(SJ, encoding="utf-8") as f:
            state_after = f.read()
        changed = state_before != state_after
    except Exception as e:  # noqa: BLE001
        signal_failures.append({"signal": "project.project", "provenance": str(e)})

    duration_ms = int((time.time() - t0) * 1000)
    for sf in signal_failures:
        emit(WRITER_ID, "daemon", {"event": "signal_failure", **sf}, evidence_class="DERIVED",
             provenance="trackerd.py one_cycle")
    return changed, duration_ms, signal_failures


def selftest():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import selftest as st  # noqa: E402
    result = st.run_all()
    return result


def main():
    if "--selftest" in sys.argv:
        result = selftest()
        ensure_runtime_dirs()
        payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "selftest_last": result}
        if os.path.exists(HEARTBEAT_JSON):
            try:
                with open(HEARTBEAT_JSON, encoding="utf-8") as f:
                    prev = json.load(f)
                prev["selftest_last"] = result
                atomic_write_json(HEARTBEAT_JSON, prev)
            except (json.JSONDecodeError, FileNotFoundError):
                atomic_write_json(HEARTBEAT_JSON, payload)
        else:
            atomic_write_json(HEARTBEAT_JSON, payload)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("all_passed") else 1)

    if "--check-blind-window-only" in sys.argv:
        # Item (d) testability: exercises exactly the "on daemon start" check without the
        # heavy collect/project machinery (network calls, mirror bootstrap) or entering the
        # loop -- so selftest can drive this fast, in an isolated HOME, at every daemon
        # start, not just manually.
        check_blind_window()
        sys.exit(0)

    deploy_static_dashboard()
    acquire_pidfile()
    check_blind_window()  # item (d): must run before this process's own first heartbeat write
    idle_cycles = 0
    interval = HEARTBEAT_INTERVAL_FRESH_S
    cycle = 0
    print(f"trackerd started, pid={os.getpid()}, runtime_dir=~/.pariprashna-tracker", file=sys.stderr)
    while True:
        cycle += 1
        changed, duration_ms, signal_failures = one_cycle()
        if changed:
            idle_cycles = 0
            interval = HEARTBEAT_INTERVAL_FRESH_S
        else:
            idle_cycles += 1
            if idle_cycles >= IDLE_CYCLES_BEFORE_BACKOFF:
                interval = HEARTBEAT_INTERVAL_IDLE_S

        selftest_last = None
        if os.path.exists(HEARTBEAT_JSON):
            try:
                with open(HEARTBEAT_JSON, encoding="utf-8") as f:
                    selftest_last = json.load(f).get("selftest_last")
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        heartbeat = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cycle": cycle, "duration_ms": duration_ms, "interval_s": interval,
            "changed": changed, "signal_failures": signal_failures,
            "selftest_last": selftest_last, "pid": os.getpid(),
        }
        atomic_write_json(HEARTBEAT_JSON, heartbeat)
        emit(WRITER_ID, "daemon", {"event": "cycle", "cycle": cycle, "duration_ms": duration_ms,
                                    "changed": changed, "interval_s": interval},
             evidence_class="DERIVED", provenance="trackerd.py main loop")

        if "--once" in sys.argv:
            break
        time.sleep(interval)


if __name__ == "__main__":
    main()
