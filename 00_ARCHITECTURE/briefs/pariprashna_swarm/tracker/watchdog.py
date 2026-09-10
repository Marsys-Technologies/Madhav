#!/usr/bin/env python3
"""Watchdog (T2, second tap tier): if heartbeat.json is older than the stale threshold,
restart trackerd and RECORD the resurrection as an event -- never swallowed. Invoked every
60s by launchd StartInterval. Stdlib only.

It restarts the daemon by asking LAUNCHD to restart its own job (`launchctl kickstart -k`),
never by spawning its own copy. Spawning was a real, observed defect: subprocess.Popen with
start_new_session=True produces an orphan (PPID 1) that launchd does not manage but which
DOES hold trackerd's flock -- so launchd's own KeepAlive copy could never start again. It
retried and exited(1) in a loop indefinitely (581 logged attempts before this fix), leaving
`launchctl list` permanently reporting the job as failing while an unsupervised orphan did
the actual work. Two supervisors competing for one job is worse than either alone.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    ALIVE_JSON, ALIVE_STALE_THRESHOLD_S, HEARTBEAT_JSON, LOGS_DIR, PIDFILE,
    STOPPED_INTENTIONALLY_JSON, WATCHDOG_STALE_THRESHOLD_S, ensure_runtime_dirs,
)
from tracker_emit import emit  # noqa: E402

WRITER_ID = "watchdog"
TRACKERD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackerd.py")


def _age_of(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            hb = json.load(f)
        ts = hb.get("ts")
        import datetime
        t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds()
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def liveness_age_seconds():
    """Age of the LIVENESS beat -- not of heartbeat.json.

    heartbeat.json is only written when a cycle completes, so judging life by it kills
    daemons for being slow. alive.json is stamped at cycle start and between collector
    steps, so a busy process keeps proving it is alive while a dead one stops within
    seconds. Falls back to heartbeat.json only when alive.json does not exist yet (an
    older daemon build), so an upgrade cannot leave the watchdog blind."""
    age = _age_of(ALIVE_JSON)
    if age is not None:
        return age, "alive.json"
    return _age_of(HEARTBEAT_JSON), "heartbeat.json (fallback: no alive.json)"


LABEL_PREFIX = os.environ.get("LABEL_PREFIX", "com.marsys.pariprashna")


def restart_daemon():
    """Ask launchd to restart ITS OWN job. `kickstart -k` stops the current instance (if
    any) and starts a fresh one under launchd's supervision, so the restarted daemon is the
    managed one -- no orphan, no flock lockout, no duelling supervisors. Never Popen a
    private copy here; see this module's docstring for what that cost."""
    ensure_runtime_dirs()
    label = f"gui/{os.getuid()}/{LABEL_PREFIX}-trackerd"
    r = subprocess.run(["launchctl", "kickstart", "-k", label],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return ("launchctl kickstart -k", True, "")
    # The job is not loaded at all (e.g. never bootstrapped, or booted out). kickstart
    # cannot start what launchd does not know about; bootstrapping is tracker-start's job
    # and it is reported honestly rather than papered over with a private spawn.
    return ("launchctl kickstart -k", False,
            (r.stderr or r.stdout or "").strip()[:200])


def main():
    # An operator stop is not an outage. T4 (tracker-cron-watchdog) has always honoured
    # this marker; T2 did not, so `tracker-stop` was silently fought and undone within 90s
    # -- the tracker could not actually be stopped on purpose. Same rule, both tiers.
    if os.path.exists(STOPPED_INTENTIONALLY_JSON):
        return

    age, source = liveness_age_seconds()
    threshold = ALIVE_STALE_THRESHOLD_S if source == "alive.json" else WATCHDOG_STALE_THRESHOLD_S
    if age is None:
        # No heartbeat at all yet (first boot) -- nothing to resurrect, no event.
        restart_daemon()
        return
    if age <= threshold:
        return
    method, ok, err = restart_daemon()
    emit(WRITER_ID, "daemon", {
        "event": "resurrection", "observed_gap_seconds": age,
        "threshold_s": threshold, "liveness_source": source,
        "restart_method": method, "restart_ok": ok, "restart_error": err or None,
    }, evidence_class="DERIVED", provenance="watchdog.py: heartbeat.json age exceeded threshold")
    print(f"RESURRECTION: {source} was {age:.0f}s stale (threshold {threshold}s); "
          f"{method} -> {'ok' if ok else 'FAILED: ' + err}", file=sys.stderr)


if __name__ == "__main__":
    main()
