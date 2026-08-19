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

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALLED_FROM_JSON = os.path.join(CODE_DIR, "INSTALLED_FROM.json")

# The daemon's OWN private mirror clone -- see collect.py's mirror_fetch(). Every origin/*
# ref read (lane branches, ahead/behind, main's tip, campaign-coordination, code
# staleness) comes from here, fetched on the daemon's own cadence, so ref freshness is
# something THIS process controls and can report on -- never a hope that some unrelated
# process fetched the shared checkout recently. `git clone --mirror` maps the remote's
# refs/heads/* and refs/tags/* verbatim into this bare repo's own refs (NOT
# refs/remotes/origin/*) -- so "origin/main" there is just this mirror's own `main`.
MIRROR_DIR = os.path.join(RUNTIME_DIR, "mirror.git")
GIT_REMOTE_URL = "https://github.com/Marsys-Technologies/Madhav.git"

# Repo root for the tracker's own read-only git operations (for-each-ref, campaign-
# coordination reads, merge-base staleness checks). In SNAPSHOT installs (see install.sh
# --install-from-ref) this code directory is an immutable `git archive` extraction with NO
# .git of its own -- it cannot be its own repo root. TRACKER_GIT_REPO (set in the launchd
# plist's EnvironmentVariables by install.sh) points at a separate, ideally-permanent
# checkout to read from instead. Falls back to the old relative-path guess (this file lives
# at 00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/_common.py) only for IN-PLACE/dev runs
# where the code dir genuinely is inside a live checkout and the env var isn't set.
REPO_ROOT = os.environ.get("TRACKER_GIT_REPO") or os.path.abspath(
    os.path.join(CODE_DIR, "..", "..", "..", "..")
)
PLAN_PATH = os.path.join(CODE_DIR, "PLAN.yaml")

STALE_AMBER_S = 45
STALE_RED_S = 120
REF_AMBER_S = 60
REF_RED_S = 180
STALL_MINUTES = 20
HEARTBEAT_INTERVAL_FRESH_S = 20
HEARTBEAT_INTERVAL_IDLE_S = 60
IDLE_CYCLES_BEFORE_BACKOFF = 10
WATCHDOG_STALE_THRESHOLD_S = 90

# Runtime state used ONLY to track consecutive mirror-fetch failures across daemon cycles
# (a plain counter, not part of the event-log/pure-fold state -- it exists purely so the
# next cycle knows whether the PREVIOUS one failed, without re-deriving it from a log scan
# every cycle). Not read by the projector; collect.py owns it exclusively.
MIRROR_FETCH_STATE_JSON = os.path.join(RUNTIME_DIR, "mirror_fetch_state.json")


def _class_for_thresholds(age_seconds, amber_max, red_max):
    if age_seconds <= amber_max:
        return "green"
    if age_seconds <= red_max:
        return "amber"
    return "red"


def staleness_class(age_seconds):
    """Pure function: age (seconds, float/int) -> 'green' | 'amber' | 'red'.
    Mirrored byte-for-byte in tracker.html's JS stalenessClass()."""
    return _class_for_thresholds(age_seconds, STALE_AMBER_S, STALE_RED_S)


def ref_freshness_class(age_seconds):
    """Pure function for the THIRD liveness axis (ref freshness -- distinct from observer
    freshness and subject progress; the observatory can be alive, the swarm can be moving,
    and the refs can still be stale, independently). Mirrored byte-for-byte in
    tracker.html's JS refFreshnessClass()."""
    return _class_for_thresholds(age_seconds, REF_AMBER_S, REF_RED_S)


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


def run_mirror(args, timeout=20):
    """Run a read-only git command against the daemon's OWN mirror (MIRROR_DIR) -- never
    against REPO_ROOT (the shared checkout). Ref names inside the mirror have no
    `refs/remotes/origin/` prefix: use `main`, `pariprashna/p0`, `campaign-coordination`,
    never `origin/main` etc. Never raises; returns (ok, stdout, stderr) like run()."""
    return run(["git", "--git-dir", MIRROR_DIR, "--no-optional-locks"] + args,
                cwd=RUNTIME_DIR, timeout=timeout)
