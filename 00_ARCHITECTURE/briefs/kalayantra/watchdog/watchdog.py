#!/usr/bin/env python3
"""KĀLA-YANTRA cockpit watchdog — wake-only (Amendment A2, D-19).

One check per invocation (launchd runs it every 15 minutes). It wakes the cockpit Claude Code session
by resuming it in the background ONLY when every condition holds:

  * no global HOLD and no owner pause (an unknown pause state counts as paused);
  * no live process holds the cockpit session (Claude Code's session registry, pid verified);
  * campaign work is pending (a job running, a job finished after the session's last activity,
    or a `ready` tracker item);
  * the session has been silent for at least KY_WD_SILENT_MIN minutes;
  * fewer than KY_WD_MAX_FAILED consecutive wakes have gone unanswered, and fewer than KY_WD_MAX_DAILY
    wakes happened in the last 24 hours.

It never plans, launches jobs, merges, writes campaign state or reads credentials. Its only writes are its
own state file, log and nudge file under KY_WD_DIR. Every decision is logged as one JSON line.

A LIVE cockpit is never woken or copied. When it is live, idle for at least KY_WD_NUDGE_IDLE_MIN minutes and
work is waiting (finished jobs unread, a non-empty fast/BACKLOG.txt or fast/ARM_ORDER.txt), the watchdog leaves
ONE nudge at most every KY_WD_NUDGE_EVERY_MIN minutes: it writes the line to KY_WD_DIR/NUDGE.txt (the cockpit's
loop reads it) and logs action "nudge". No script-callable send into a running session exists (the SendMessage
tool is the model's, and `claude --resume` on a live session starts a copy), so the file is the channel.
"""
import datetime as dt
import glob
import json
import os
import subprocess
import sys
import urllib.request

UTC = dt.timezone.utc
WAKE_PROMPT = (
    "Watchdog wake (KĀLA-YANTRA Amendment A2, D-19). This cockpit session had stopped while campaign work was "
    "pending. Continue the campaign as cockpit and conductor per KALAYANTRA_V3_COCKPIT_PROMPT_v2_7.md, "
    "Amendment A1 and Amendment A2: read the finished jobs and act on them, restart your job monitor, launch the "
    "next work, keep the merge queue moving. Do not wait for the owner; anything that truly needs the owner "
    "becomes a tracked owner item while work continues."
)


class Config:
    def __init__(self, environ=None):
        e = environ if environ is not None else os.environ
        g = lambda k, d: e.get(k) if e.get(k) not in (None, "") else d
        home = os.path.expanduser("~")
        self.root = g("KY_ROOT", "/Users/Dev/kalayantra")
        self.run = g("KY_RUN", os.path.join(self.root, "run"))
        self.dir = g("KY_WD_DIR", os.path.join(self.run, "watchdog"))
        self.session_id = g("KY_WD_SESSION_ID", "")
        self.session_file = g("KY_WD_SESSION_FILE", os.path.join(self.dir, "SESSION_ID"))
        self.sessions_dir = g("KY_WD_SESSIONS_DIR", os.path.join(home, ".claude", "sessions"))
        self.projects_dir = g("KY_WD_PROJECTS_DIR", os.path.join(home, ".claude", "projects"))
        self.fast_jobs = g("KY_WD_FAST_JOBS",
                           "/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs")
        self.fleet_jobs = g("KY_WD_FLEET_JOBS", os.path.join(self.run, "jobs"))
        self.tracker_url = g("KY_WD_TRACKER_URL", "http://127.0.0.1:8767/api/state")
        self.fleet_code = g("KY_WD_FLEET_CODE", os.path.join(self.root, "fleet_live"))
        self.claude = g("KY_WD_CLAUDE", os.path.join(home, ".local", "bin", "claude"))
        self.workdir = g("KY_WD_WORKDIR", "/Users/Dev/Vibe-Coding/Apps/Madhav")
        self.silent_min = float(g("KY_WD_SILENT_MIN", "20"))
        self.verify_min = float(g("KY_WD_VERIFY_MIN", "10"))
        self.max_failed = int(g("KY_WD_MAX_FAILED", "3"))
        self.max_daily = int(g("KY_WD_MAX_DAILY", "12"))
        self.running_max_h = float(g("KY_WD_RUNNING_MAX_H", "8"))
        self.fast_dir = g("KY_WD_FAST_DIR", os.path.dirname(self.fast_jobs.rstrip("/")))
        self.nudge_idle_min = float(g("KY_WD_NUDGE_IDLE_MIN", "20"))
        self.nudge_every_min = float(g("KY_WD_NUDGE_EVERY_MIN", "30"))
        self.dry_run = g("KY_WD_DRY_RUN", "0") == "1"
        self.notify = g("KY_WD_NOTIFY", "1") == "1"


# ───────────────────────────── observations (each fails safe: unknown never causes a wake) ─────────────────────────────

def held(cfg):
    """(True, reason) when the global HOLD exists or an owner pause is in force or cannot be read."""
    if os.path.lexists(os.path.join(cfg.root, "HOLD")):
        return True, "global HOLD present"
    try:
        sys.path.insert(0, cfg.fleet_code)
        import kycommands  # the fleet's own pause reader; read-only
        paused = kycommands.owner_paused(cfg.run)
    except Exception as exc:  # unknown counts as paused, as in the dispatcher
        return True, "owner pause unknown (%s)" % type(exc).__name__
    finally:
        if sys.path and sys.path[0] == cfg.fleet_code:
            sys.path.pop(0)
    if paused is not False:
        return True, "owner pause in force"
    return False, None


def session_id(cfg):
    if cfg.session_id:
        return cfg.session_id.strip()
    try:
        with open(cfg.session_file) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def proc_start(pid):
    """The process start time as `ps` prints it, in UTC and in local time (a set), or None if unknown.

    Claude Code's registry records procStart in UTC; `ps` prints local time unless TZ says otherwise. A
    comparison in one zone only would call a live cockpit stale and wake a duplicate (found in the first live
    dry run, 2026-10-15)."""
    seen = set()
    for tz in ("UTC", None):
        environ = dict(os.environ)
        if tz:
            environ["TZ"] = tz
        try:
            out = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True,
                                 timeout=10, env=environ)
        except Exception:
            return None
        text = " ".join(out.stdout.split())
        if not text:
            return None
        seen.add(text)
    return seen


def session_live(cfg, sid, ps_start=proc_start):
    """'live' | 'absent' | 'unknown'. Live = a registry record for sid whose pid is alive with a matching start."""
    try:
        paths = glob.glob(os.path.join(cfg.sessions_dir, "*.json"))
    except Exception:
        return "unknown", None
    for path in paths:
        try:
            with open(path) as fh:
                rec = json.load(fh)
        except Exception:
            continue
        if rec.get("sessionId") != sid:
            continue
        pid = rec.get("pid")
        if not isinstance(pid, int):
            return "unknown", rec
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue  # stale record: process gone
        except PermissionError:
            return "live", rec
        started = ps_start(pid)
        want = " ".join(str(rec.get("procStart", "")).split())
        if started is None or not want:
            return "unknown", rec
        if want in ({started} if isinstance(started, str) else started):
            return "live", rec
        # pid reused by another process: stale record
    return "absent", None


def last_activity(cfg, sid):
    paths = glob.glob(os.path.join(cfg.projects_dir, "*", sid + ".jsonl"))
    if not paths:
        return None
    return max(dt.datetime.fromtimestamp(os.path.getmtime(p), UTC) for p in paths)


def answered_after(cfg, sid, when, tail_bytes=4 * 1024 * 1024):
    """True when the cockpit's transcript holds an ASSISTANT message timestamped after `when`.

    The wake itself appends the wake prompt (a user message) to the transcript, so the file's modification
    time alone would call every wake "answered" even when the session died at once (found on re-review,
    2026-10-15). Only the model replying counts. Reads the tail of the transcript; a parse problem is "no"."""
    for path in glob.glob(os.path.join(cfg.projects_dir, "*", sid + ".jsonl")):
        try:
            with open(path, "rb") as fh:
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                fh.seek(max(0, size - tail_bytes))
                chunk = fh.read()
        except OSError:
            continue
        for line in chunk.split(b"\n")[1:] if size > tail_bytes else chunk.split(b"\n"):
            if b'"assistant"' not in line:
                continue
            try:
                event = json.loads(line)
                if (event.get("message") or {}).get("role") != "assistant":
                    continue
                ts = dt.datetime.fromisoformat(str(event.get("timestamp")).replace("Z", "+00:00"))
            except Exception:
                continue
            if ts > when:
                return True
    return False


def pending_work(cfg, since, now):
    """Reasons work is pending (list of strings); empty list = nothing pending."""
    reasons = []
    try:
        for job in glob.glob(os.path.join(cfg.fast_jobs, "X-*")):
            done = os.path.join(job, "DONE")
            if os.path.exists(done):
                if since is not None and dt.datetime.fromtimestamp(os.path.getmtime(done), UTC) > since:
                    reasons.append("finished after last activity: " + os.path.basename(job))
            else:
                age_h = (now - dt.datetime.fromtimestamp(os.path.getmtime(job), UTC)).total_seconds() / 3600
                if age_h <= cfg.running_max_h:
                    reasons.append("running: " + os.path.basename(job))
    except Exception as exc:
        reasons.append("fast-lane jobs unreadable (%s)" % type(exc).__name__)
    try:
        for state_path in glob.glob(os.path.join(cfg.fleet_jobs, "J-*", "state.json")):
            with open(state_path) as fh:
                phase = json.load(fh).get("phase")
            if phase in ("live", "running", "prepared", "terminating"):
                reasons.append("fleet job %s: %s" % (phase, os.path.basename(os.path.dirname(state_path))))
    except Exception:
        pass
    try:
        with urllib.request.urlopen(cfg.tracker_url, timeout=5) as resp:
            state = json.load(resp)
        ready = state.get("overall", {}).get("ready")
        if isinstance(ready, int) and ready > 0:
            reasons.append("tracker ready items: %d" % ready)
    except Exception:
        pass  # tracker down is not, by itself, a reason to wake
    return reasons


def queue_depth(path):
    """Entries in a fast-lane queue file: non-blank lines that are not '#' comments. Missing/unreadable = 0."""
    try:
        with open(path) as fh:
            return sum(1 for line in fh if line.strip() and not line.lstrip().startswith("#"))
    except OSError:
        return 0


def nudge_text(unread, backlog, arm_order):
    return "%d finished jobs unread; backlog %d; arm-order %d; act" % (unread, backlog, arm_order)


# ───────────────────────────── state, log, actions ─────────────────────────────

def load_state(cfg):
    try:
        with open(os.path.join(cfg.dir, "state.json")) as fh:
            return json.load(fh)
    except Exception:
        return {"failed_wakes": 0, "last_wake": None, "notified": {}}


def save_state(cfg, state):
    os.makedirs(cfg.dir, exist_ok=True)
    tmp = os.path.join(cfg.dir, "state.json.tmp")
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=1)
    os.replace(tmp, os.path.join(cfg.dir, "state.json"))


def log(cfg, record):
    os.makedirs(cfg.dir, exist_ok=True)
    with open(os.path.join(cfg.dir, "watchdog.jsonl"), "a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def notify(cfg, state, key, text, now, every_h=1.0):
    last = state.setdefault("notified", {}).get(key)
    if last and (now - dt.datetime.fromisoformat(last)).total_seconds() < every_h * 3600:
        return False
    state["notified"][key] = now.isoformat()
    if cfg.notify and not cfg.dry_run:
        script = 'display notification "%s" with title "Kāla watchdog"' % text.replace('"', "'")
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=20)
    return True


def nudge(cfg, state, rec, unread, backlog, arm_order, now):
    """Leave ONE nudge for a live, idle cockpit; at most one per cfg.nudge_every_min. True when one was left.

    The only write is KY_WD_DIR/NUDGE.txt (overwritten, one line). It never resumes, flags or copies a session."""
    last = state.get("last_nudge")
    if last and (now - dt.datetime.fromisoformat(last)).total_seconds() < cfg.nudge_every_min * 60:
        return False
    text = nudge_text(unread, backlog, arm_order)
    if not cfg.dry_run:
        os.makedirs(cfg.dir, exist_ok=True)
        with open(os.path.join(cfg.dir, "NUDGE.txt"), "w") as fh:
            fh.write("%s %s\n" % (now.isoformat(), text))
    state["last_nudge"] = now.isoformat()
    rec.update(action="nudge", reason="session live and idle; " + text, nudge=text)
    return True


def wake(cfg, sid):
    # No other flags: resuming with any flag starts a COPY of the session instead of continuing it
    # (verified 2026-10-15 against Claude Code 2.1.296). The session keeps its own saved options.
    cmd = [cfg.claude, "--bg", "--resume", sid, WAKE_PROMPT]
    if cfg.dry_run:
        return {"dry_run": True, "cmd": cmd[:4]}
    out = subprocess.run(cmd, cwd=cfg.workdir, capture_output=True, text=True, timeout=120)
    text = (out.stdout + "\n" + out.stderr).strip()
    return {"exit": out.returncode, "output": text[-600:],
            "copy_started": "copy" in text.lower()}


def tick(cfg, now=None, ps_start=proc_start, waker=wake):
    now = now or dt.datetime.now(UTC)
    state = load_state(cfg)
    rec = {"ts": now.isoformat(), "action": None}

    is_held, why = held(cfg)
    if is_held:
        rec.update(action="none", reason=why)
        return finish(cfg, state, rec)

    sid = session_id(cfg)
    if not sid:
        rec.update(action="none", reason="no cockpit session id configured")
        notify(cfg, state, "no_session", "Watchdog has no cockpit session id", now, every_h=12)
        return finish(cfg, state, rec)
    rec["session"] = sid

    liveness, srec = session_live(cfg, sid, ps_start)
    seen = last_activity(cfg, sid)
    rec["session_state"] = liveness
    rec["last_activity"] = seen.isoformat() if seen else None
    silent_min = (now - seen).total_seconds() / 60 if seen else None
    rec["silent_min"] = round(silent_min, 1) if silent_min is not None else None

    # A wake that was answered resets the failure count; an unanswered one counts once.
    last_wake = state.get("last_wake")
    if last_wake:
        lw = dt.datetime.fromisoformat(last_wake["ts"])
        if answered_after(cfg, sid, lw):
            state["failed_wakes"] = 0
            state["last_wake"] = None
        elif (now - lw).total_seconds() / 60 >= cfg.verify_min and not last_wake.get("counted"):
            state["failed_wakes"] = state.get("failed_wakes", 0) + 1
            last_wake["counted"] = True

    if liveness != "absent":
        rec.update(action="none", reason="session %s" % liveness)
        if liveness == "live" and srec and srec.get("status") == "idle" and silent_min:
            reasons = pending_work(cfg, seen, now)
            finished = [r for r in reasons if r.startswith("finished after")]
            if silent_min >= 45 and finished:
                rec["reason"] = "session live but idle with %d unread finished jobs" % len(finished)
                notify(cfg, state, "idle_unread", "Cockpit idle with finished jobs unread", now)
            backlog = queue_depth(os.path.join(cfg.fast_dir, "BACKLOG.txt"))
            arm_order = queue_depth(os.path.join(cfg.fast_dir, "ARM_ORDER.txt"))
            if silent_min >= cfg.nudge_idle_min and (finished or backlog or arm_order):
                nudge(cfg, state, rec, len(finished), backlog, arm_order, now)
        return finish(cfg, state, rec)

    if seen is None:
        rec.update(action="none", reason="cockpit transcript not found")
        return finish(cfg, state, rec)

    reasons = pending_work(cfg, seen, now)
    rec["pending"] = reasons[:12]
    if not reasons:
        rec.update(action="none", reason="no pending work")
        return finish(cfg, state, rec)
    if silent_min < cfg.silent_min:
        rec.update(action="none", reason="silent only %.0f min" % silent_min)
        return finish(cfg, state, rec)
    if state.get("failed_wakes", 0) >= cfg.max_failed:
        rec.update(action="none", reason="wake budget exhausted (%d unanswered)" % state["failed_wakes"])
        notify(cfg, state, "exhausted", "Cockpit did not answer %d wakes; please check it" % state["failed_wakes"],
               now, every_h=3)
        return finish(cfg, state, rec)
    recent = [t for t in state.get("wakes", []) if (now - dt.datetime.fromisoformat(t)).total_seconds() < 86400]
    state["wakes"] = recent
    if len(recent) >= cfg.max_daily:
        rec.update(action="none", reason="daily wake ceiling reached (%d in 24 h)" % len(recent))
        notify(cfg, state, "daily", "Cockpit needed %d wakes in a day; please check it" % len(recent), now, every_h=6)
        return finish(cfg, state, rec)
    if state.get("last_wake") and (now - dt.datetime.fromisoformat(state["last_wake"]["ts"])).total_seconds() / 60 < cfg.verify_min:
        rec.update(action="none", reason="waiting for the previous wake to take effect")
        return finish(cfg, state, rec)

    result = waker(cfg, sid)
    rec.update(action="wake", result=result)
    state["last_wake"] = {"ts": now.isoformat(), "counted": False}
    state.setdefault("wakes", []).append(now.isoformat())
    if result.get("copy_started"):
        notify(cfg, state, "copy", "Watchdog started a copy of the cockpit; check for two conductors", now, every_h=0)
    return finish(cfg, state, rec)


def finish(cfg, state, rec):
    rec["failed_wakes"] = state.get("failed_wakes", 0)
    save_state(cfg, state)
    log(cfg, rec)
    return rec


if __name__ == "__main__":
    out = tick(Config())
    print(json.dumps(out, sort_keys=True))
