"""pravaha runner — keeps one stream's Kimi Code session alive, headless, for as long as there is work.

Each pass: if the HOLD file or this stream's STOP file exists, it pauses or exits. If an interactive Kimi session is
already working in the stream's worktree, it waits. If the stream has no READY or RUNNING item and an empty inbox,
it blocks on the inbox. Otherwise it starts `kimi -p` (non-interactive) with the stream prompt, the autonomy addendum and a
live context block (inbox, queue, recent events). When that session ends, for any reason, the next pass starts a
fresh one; the tracker, not the model's context, carries the state.

  python3 -m pravaha_tracker.runner A        (launchd: com.madhav.pravaha.runner.A)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "pravaha_tracker"

from pravaha_tracker import cli  # noqa: E402

HOME = os.environ.get("PRAVAHA_HOME", "/Users/Dev/pravaha")
BRIEFS = "/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/prompts"
KIMI = os.environ.get("PRAVAHA_KIMI", "/Users/Dev/.kimi-code/bin/kimi")
# Native, 2026-10-01: execution/coding = Kimi K3-256k at LOW effort; reviews = K3-256k at HIGH (kimi_review.py).
MODEL_ID = os.environ.get("PRAVAHA_KIMI_MODEL", "kimi-code/k3-256k")
SESSION_MAX_S = int(os.environ.get("PRAVAHA_SESSION_MAX_S", str(3 * 3600)))
IDLE_WAIT_S = 1500
STALL_S = int(os.environ.get("PRAVAHA_STALL_S", "1500"))   # > the 9-min inbox wait, with margin
QUOTA_FLAG = os.path.join(HOME, "run", "KIMI_QUOTA_EXHAUSTED")   # shared: both streams use one Kimi account
QUOTA_BACKOFF_S = int(os.environ.get("PRAVAHA_QUOTA_BACKOFF_S", "3600"))
QUOTA_MARKERS = ("usage limit", "quota will reset", "provider.auth_error: 403", "rate limit", "429")
STARTED_AT = time.time()
STREAMS = {
    "A": {"worktree": "/Users/Dev/madhav-l3/gochara-wp0-7", "prompt": "STREAM_A_KARMA_PROMPT_v1_0.md"},
    "B": {"worktree": "/Users/Dev/madhav-l3/pravaha", "prompt": "STREAM_B_SHASTRA_PROMPT_v1_0.md"},
    # Stream C (2026-10-02): the single Kimi stream. A and B are now run by Claude sessions, so the launchd runner is
    # installed for C only. C owns no plan-model items; it works from steward messages and reports back.
    "C": {"worktree": "/Users/Dev/madhav-l3/pravaha-c", "prompt": "STREAM_C_KIMI_PROMPT_v1_0.md"},
}
ADDENDUM = "STREAM_AUTONOMY_ADDENDUM_v1_0.md"


def log(stream: str, msg: str) -> None:
    line = f"{dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')} [{stream}] {msg}"
    print(line, flush=True)


def emit(stream: str, kind: str, detail: str) -> None:
    cli.main([kind, "--stream", stream, "--detail", f"runner: {detail}"])


KIMI_CONFIG = os.path.expanduser("~/.kimi-code/config.toml")
EFFORT = os.environ.get("PRAVAHA_KIMI_EFFORT", "low")   # native, 2026-09-30: K3 at LOW effort


CONFIG_LOCK = os.path.join(HOME, "run", "KIMI_CONFIG.lock")
EFFORT_SETTLE_S = 25   # how long a starting kimi process needs to have read config.toml


def set_effort(model_id: str, effort: str) -> str | None:
    """Set default_effort for one model block in the Kimi config. Returns the previous value (None if absent).
    The Kimi CLI has no effort flag: effort comes only from config.toml, and other tools rewrite that file."""
    lines = open(KIMI_CONFIG, encoding="utf-8").read().split("\n")
    header, inside, prev = f'[models."{model_id}"]', False, None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("["):
            inside = ln.strip() == header
        elif inside and ln.strip().startswith("default_effort"):
            prev = ln.split("=", 1)[1].strip().strip('"')
            lines[i] = f'default_effort = "{effort}"'
    if prev is not None and prev != effort:
        open(KIMI_CONFIG, "w", encoding="utf-8").write("\n".join(lines))
    return prev


def launch_with_effort(model_id: str, effort: str, argv: list[str], **popen_kwargs) -> subprocess.Popen:
    """Start a kimi process with the config pinned to `effort` for `model_id`, under an exclusive file lock held
    until the process has read its config — so a stream (low) and a review (high) can never start on each other's
    setting. The config is left at the execution default (EFFORT) afterwards."""
    import fcntl
    os.makedirs(os.path.dirname(CONFIG_LOCK), exist_ok=True)
    with open(CONFIG_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prev = set_effort(model_id, effort)
        if prev is None:
            raise RuntimeError(f"Kimi config has no default_effort for {model_id}; refusing to start at an unknown effort")
        proc = subprocess.Popen(argv, **popen_kwargs)
        time.sleep(EFFORT_SETTLE_S)
        set_effort(model_id, EFFORT)
    return proc


def interactive_session_in(worktree: str, own_pid: int | None = None) -> bool:
    """True if some other kimi process has its cwd inside the worktree (a human-driven session)."""
    try:
        out = subprocess.run(["pgrep", "-x", "kimi"], capture_output=True, text=True).stdout.split()
    except OSError:
        return False
    for pid in out:
        if own_pid and int(pid) == own_pid:
            continue
        cwd = subprocess.run(["lsof", "-a", "-d", "cwd", "-p", pid, "-Fn"], capture_output=True, text=True).stdout
        for ln in cwd.splitlines():
            if ln.startswith("n") and os.path.realpath(ln[1:]).startswith(os.path.realpath(worktree)):
                return True
    return False


def queue(stream: str) -> dict:
    res, via = cli.get(f"/api/next?stream={stream}")
    if not res or via != "live":
        return {"running": [], "ready": [], "blocked": [], "_via": via}
    return res


def recent_events(stream: str, n: int = 25) -> list[dict]:
    evs = [e for e in cli._read_events()
           if e.get("actor", "").upper().endswith(stream) or e.get("to") == stream or e.get("kind") == "decision"]
    return evs[-n:]


def build_prompt(stream: str) -> str:
    cfg = STREAMS[stream]
    with open(os.path.join(BRIEFS, cfg["prompt"]), encoding="utf-8") as f:
        base = f.read()
    with open(os.path.join(BRIEFS, ADDENDUM), encoding="utf-8") as f:
        addendum = f.read()
    ctx = {
        "now_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stream": stream,
        "inbox_unacked": cli._unacked(stream),
        "queue": queue(stream),
        "recent_events": recent_events(stream),
    }
    return (base + "\n\n---\n\n" + addendum + "\n\n---\n\n# Live context at session start (from the tracker)\n\n"
            "```json\n" + json.dumps(ctx, ensure_ascii=False, indent=1)[:60000] + "\n```\n\n"
            f"Begin now: `export PRAVAHA_STREAM={stream}; P=/Users/Dev/pravaha/bin/pravaha; cd {cfg['worktree']}; "
            "$P preflight; $P inbox`.\n")


def has_work(stream: str) -> bool:
    q = queue(stream)
    return bool(q.get("ready") or q.get("running") or cli._unacked(stream))


def quota_hit(path: str) -> bool:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 4000))
            tail = f.read().lower()
    except OSError:
        return False
    return any(m in tail for m in QUOTA_MARKERS)


def quota_wait_left() -> float:
    try:
        return QUOTA_BACKOFF_S - (time.time() - os.path.getmtime(QUOTA_FLAG))
    except OSError:
        return 0.0


def run(stream: str) -> int:
    cfg = STREAMS[stream]
    os.environ["PRAVAHA_STREAM"] = stream
    logdir = os.path.join(HOME, "run", "runner", stream)
    os.makedirs(logdir, exist_ok=True)
    fast_fails = 0
    while True:
        stop = os.path.join(HOME, "run", f"RUNNER_STOP_{stream}")
        if os.path.exists(stop) and os.path.getmtime(stop) > STARTED_AT:
            log(stream, "STOP file present — exiting")
            return 0
        left = quota_wait_left()
        if left > 0:
            log(stream, f"Kimi quota exhausted — backing off {int(left)}s")
            time.sleep(min(left, 600))
            continue
        if os.path.exists(os.environ.get("PRAVAHA_HOLD") or os.path.join(HOME, "run", "PRAVAHA_HOLD")):
            log(stream, "HOLD — paused")
            time.sleep(60)
            continue
        if interactive_session_in(cfg["worktree"]):
            log(stream, "an interactive kimi session is working in the worktree — waiting")
            time.sleep(120)
            continue
        if not has_work(stream):
            log(stream, "no work and empty inbox — waiting on the inbox")
            subprocess.run([sys.executable, "-m", "pravaha_tracker.cli", "inbox", "--stream", stream,
                            "--wait", str(IDLE_WAIT_S)], capture_output=True,
                           cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            continue
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = os.path.join(logdir, f"session-{stamp}.log")
        prompt = build_prompt(stream)
        emit(stream, "heartbeat", f"session start {stamp} (log {out_path})")
        log(stream, f"session start → {out_path}")
        t0 = time.time()
        with open(out_path, "w", encoding="utf-8") as out:
            proc = launch_with_effort(MODEL_ID, EFFORT, [KIMI, "-m", MODEL_ID, "-p", prompt],
                                      cwd=cfg["worktree"], stdout=out, stderr=subprocess.STDOUT)
            last_size, last_beat = 0, time.time()
            last_grew = time.time()
            rc = None
            while rc is None:
                try:
                    rc = proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    if time.time() - t0 > SESSION_MAX_S:
                        proc.terminate()
                        try:
                            proc.wait(timeout=60)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                        rc = "timeout"
                        break
                    # Liveness from a real detector: the session's own output grew since the last beat.
                    if time.time() - last_beat >= 300:
                        size = os.path.getsize(out_path)
                        if size > last_size:
                            emit(stream, "heartbeat", f"session {stamp} alive (log +{size - last_size} bytes in {int(time.time() - last_beat)}s)")
                            last_grew = time.time()
                        else:
                            emit(stream, "heartbeat", f"session {stamp} running but its log has not grown for {int(time.time() - last_grew)}s")
                        last_size, last_beat = size, time.time()
                        # A session whose log is flat for STALL_S is hung (observed 2026-09-30: a
                        # session froze mid-sentence for 40 min). End it; the next pass starts fresh.
                        if time.time() - last_grew > STALL_S:
                            emit(stream, "note", f"session {stamp} log flat for {int(time.time() - last_grew)}s — "
                                 "treated as hung; terminating so a fresh session resumes from the tracker")
                            proc.terminate()
                            try:
                                proc.wait(timeout=30)
                            except subprocess.TimeoutExpired:
                                proc.kill()
                            rc = "stalled"
                            break
        took = int(time.time() - t0)
        log(stream, f"session end rc={rc} after {took}s")
        emit(stream, "heartbeat", f"session end {stamp} rc={rc} after {took}s")
        if quota_hit(out_path):
            first = not os.path.exists(QUOTA_FLAG)
            open(QUOTA_FLAG, "w").write(f"{stamp} stream {stream}\n")   # (re)arms the shared backoff
            if first:
                cli.main(["report", "--stream", stream, "--detail",
                          f"runner: KIMI QUOTA EXHAUSTED (5-hour window) in session {stamp}; both streams back off "
                          f"{QUOTA_BACKOFF_S // 60} min, then retry. Steward: pick up urgent work meanwhile."])
            fast_fails = 0
            continue
        if os.path.exists(QUOTA_FLAG) and took >= 120:
            os.remove(QUOTA_FLAG)
            cli.main(["report", "--stream", stream, "--detail", "runner: Kimi quota available again — streams resumed."])
        if took < 120:
            fast_fails += 1
            if fast_fails >= 3:
                emit(stream, "note", f"3 sessions in a row ended within 2 min (last rc={rc}); backing off 15 min — see {out_path}")
                time.sleep(900)
                fast_fails = 0
            else:
                time.sleep(30)
        else:
            fast_fails = 0
            time.sleep(10)


if __name__ == "__main__":
    s = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PRAVAHA_STREAM", "")).upper()
    if s not in STREAMS:
        raise SystemExit("usage: python3 -m pravaha_tracker.runner A|B|C")
    raise SystemExit(run(s))
