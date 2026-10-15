"""Tests for the wake-only cockpit watchdog (Amendment A2, D-19). Every fixture lives under pytest's tmp_path."""
import datetime as dt
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import watchdog as wd  # noqa: E402

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 15, 3, 0, tzinfo=UTC)
SID = "94345d41-9ed0-4758-a26e-121ac8553ca0"


def set_mtime(path, when):
    ts = when.timestamp()
    os.utime(path, (ts, ts))


@pytest.fixture
def box(tmp_path):
    root = tmp_path / "ky"
    (root / "run").mkdir(parents=True)
    fleet = tmp_path / "fleet"
    fleet.mkdir()
    (fleet / "kycommands.py").write_text(
        "import os\n"
        "def owner_paused(run):\n"
        "    p = os.path.join(run, 'PAUSE_TEST')\n"
        "    if os.path.exists(os.path.join(run, 'PAUSE_UNKNOWN')): raise RuntimeError('x')\n"
        "    return os.path.exists(p)\n")
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    projects = tmp_path / "projects" / "-Users-Dev-Vibe-Coding-Apps-Madhav"
    projects.mkdir(parents=True)
    transcript = projects / (SID + ".jsonl")
    transcript.write_text("{}\n")
    set_mtime(transcript, NOW - dt.timedelta(minutes=60))
    fast = tmp_path / "fast"
    fast.mkdir()
    environ = {
        "KY_ROOT": str(root), "KY_WD_SESSION_ID": SID, "KY_WD_SESSIONS_DIR": str(sessions),
        "KY_WD_PROJECTS_DIR": str(tmp_path / "projects"), "KY_WD_FAST_JOBS": str(fast),
        "KY_WD_FLEET_JOBS": str(root / "run" / "jobs"), "KY_WD_TRACKER_URL": "http://127.0.0.1:9/none",
        "KY_WD_FLEET_CODE": str(fleet), "KY_WD_NOTIFY": "0",
    }
    sys.modules.pop("kycommands", None)
    return {"root": root, "sessions": sessions, "transcript": transcript, "fast": fast,
            "cfg": wd.Config(environ), "environ": environ}


def add_job(box, name, finished_at=None, started_at=None):
    job = box["fast"] / name
    job.mkdir()
    if finished_at:
        (job / "DONE").write_text("")
        set_mtime(job / "DONE", finished_at)
    set_mtime(job, started_at or NOW - dt.timedelta(minutes=30))
    return job


def add_session(box, pid, status="idle", proc_start="Thu Oct 15 07:37:15 2026"):
    (box["sessions"] / ("%d.json" % pid)).write_text(json.dumps(
        {"pid": pid, "sessionId": SID, "procStart": proc_start, "status": status}))


def answer(box, when, role="assistant"):
    """Append one transcript message (the model's reply by default) timestamped at `when`."""
    with open(box["transcript"], "a") as fh:
        fh.write(json.dumps({"timestamp": when.isoformat().replace("+00:00", "Z"),
                             "message": {"role": role, "content": [{"type": "text", "text": "ok"}]}}) + "\n")
    set_mtime(box["transcript"], when)


class Waker:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or {"exit": 0}

    def __call__(self, cfg, sid):
        self.calls.append(sid)
        return dict(self.result)


def run(box, waker, now=NOW, ps=lambda pid: "Thu Oct 15 07:37:15 2026"):
    sys.modules.pop("kycommands", None)
    return wd.tick(box["cfg"], now=now, ps_start=ps, waker=waker)


def test_wakes_when_session_dead_work_pending_and_silent(box):
    add_job(box, "X-running")
    w = Waker()
    rec = run(box, w)
    assert rec["action"] == "wake" and w.calls == [SID]
    assert rec["session_state"] == "absent"


def test_no_wake_under_global_hold(box):
    (box["root"] / "HOLD").write_text("")
    add_job(box, "X-running")
    w = Waker()
    assert run(box, w)["reason"] == "global HOLD present" and not w.calls


def test_no_wake_when_owner_paused_or_pause_unknown(box):
    add_job(box, "X-running")
    (box["root"] / "run" / "PAUSE_TEST").write_text("")
    w = Waker()
    assert "owner pause in force" == run(box, w)["reason"]
    os.remove(box["root"] / "run" / "PAUSE_TEST")
    (box["root"] / "run" / "PAUSE_UNKNOWN").write_text("")
    assert run(box, w)["reason"].startswith("owner pause unknown") and not w.calls


def test_no_wake_when_session_live(box):
    add_job(box, "X-running")
    add_session(box, os.getpid())
    w = Waker()
    rec = run(box, w)
    assert rec["session_state"] == "live" and not w.calls


def test_stale_registry_record_with_reused_pid_counts_as_absent(box):
    add_job(box, "X-running")
    add_session(box, os.getpid(), proc_start="Mon Oct 12 01:00:00 2026")
    w = Waker()
    assert run(box, w)["action"] == "wake"


def test_registry_utc_start_matches_local_time_ps_output(box):
    """The registry stores procStart in UTC; ps may print local time. Either form proves the same process."""
    add_job(box, "X-running")
    add_session(box, os.getpid(), proc_start="Thu Oct 15 07:37:15 2026")
    w = Waker()
    rec = run(box, w, ps=lambda pid: {"Thu Oct 15 07:37:15 2026", "Thu Oct 15 13:07:15 2026"})
    assert rec["session_state"] == "live" and not w.calls


def test_real_ps_recognises_this_live_process(box):
    """End to end with the real `ps`: a registry record written in UTC for this very process reads live."""
    add_job(box, "X-running")
    utc = os.popen("TZ=UTC ps -o lstart= -p %d" % os.getpid()).read()
    add_session(box, os.getpid(), proc_start=" ".join(utc.split()))
    w = Waker()
    sys.modules.pop("kycommands", None)
    rec = wd.tick(box["cfg"], now=NOW, waker=w)
    assert rec["session_state"] == "live" and not w.calls


def test_unknown_process_start_never_wakes(box):
    add_job(box, "X-running")
    add_session(box, os.getpid())
    w = Waker()
    rec = run(box, w, ps=lambda pid: None)
    assert rec["session_state"] == "unknown" and not w.calls


def test_no_wake_without_pending_work(box):
    add_job(box, "X-old", finished_at=NOW - dt.timedelta(hours=3))  # read before the last activity
    w = Waker()
    assert run(box, w)["reason"] == "no pending work" and not w.calls


def test_finished_job_after_last_activity_is_pending(box):
    add_job(box, "X-fresh", finished_at=NOW - dt.timedelta(minutes=30))
    w = Waker()
    rec = run(box, w)
    assert rec["action"] == "wake"
    assert any("finished after last activity" in r for r in rec["pending"])


def test_abandoned_job_folder_is_not_pending(box):
    add_job(box, "X-abandoned", started_at=NOW - dt.timedelta(hours=20))
    w = Waker()
    assert run(box, w)["reason"] == "no pending work"


def test_not_silent_long_enough(box):
    add_job(box, "X-running")
    set_mtime(box["transcript"], NOW - dt.timedelta(minutes=5))
    w = Waker()
    assert run(box, w)["reason"].startswith("silent only") and not w.calls


def test_waits_for_previous_wake_then_counts_unanswered_and_stops_at_budget(box):
    add_job(box, "X-running")
    w = Waker()
    t = NOW
    assert run(box, w, now=t)["action"] == "wake"
    assert run(box, w, now=t + dt.timedelta(minutes=5))["reason"].startswith("waiting for the previous wake")
    # three unanswered wakes, each checked after the verification window
    for i in range(1, 3):
        t = t + dt.timedelta(minutes=15)
        assert run(box, w, now=t)["action"] == "wake"
    t = t + dt.timedelta(minutes=15)
    rec = run(box, w, now=t)
    assert rec["action"] == "none" and rec["reason"].startswith("wake budget exhausted")
    assert len(w.calls) == 3


def test_answered_wake_resets_failure_count(box):
    add_job(box, "X-running")
    w = Waker()
    t = NOW
    run(box, w, now=t)
    t2 = t + dt.timedelta(minutes=15)
    run(box, w, now=t2)  # first wake unanswered → counted
    state = json.loads((box["root"] / "run" / "watchdog" / "state.json").read_text())
    assert state["failed_wakes"] == 1
    answer(box, t2 + dt.timedelta(minutes=1))  # the model replied after the wake
    run(box, w, now=t2 + dt.timedelta(minutes=40))
    state = json.loads((box["root"] / "run" / "watchdog" / "state.json").read_text())
    assert state["failed_wakes"] == 0


def test_wake_prompt_alone_does_not_count_as_answered(box):
    """The wake writes a USER line into the transcript; only an ASSISTANT reply resets the failure count."""
    add_job(box, "X-running")
    w = Waker()
    t = NOW
    run(box, w, now=t)
    answer(box, t + dt.timedelta(seconds=5), role="user")  # what a wake itself leaves behind
    run(box, w, now=t + dt.timedelta(minutes=15))
    state = json.loads((box["root"] / "run" / "watchdog" / "state.json").read_text())
    assert state["failed_wakes"] == 1


def test_daily_ceiling(box):
    add_job(box, "X-running")
    box["cfg"].max_daily = 2
    w = Waker()
    t = NOW
    for _ in range(2):
        # the session "answers" each wake, so only the daily ceiling can stop it
        run(box, w, now=t)
        answer(box, t + dt.timedelta(minutes=1))
        t = t + dt.timedelta(minutes=30)
    rec = run(box, w, now=t)
    assert rec["reason"].startswith("daily wake ceiling") and len(w.calls) == 2


def test_dry_run_never_executes(box):
    add_job(box, "X-running")
    box["cfg"].dry_run = True
    box["cfg"].claude = "/nonexistent/claude"
    rec = wd.tick(box["cfg"], now=NOW, ps_start=lambda pid: None)
    assert rec["action"] == "wake" and rec["result"]["dry_run"] is True


def test_no_session_id_configured(box):
    box["cfg"].session_id = ""
    box["cfg"].session_file = str(box["root"] / "missing")
    w = Waker()
    assert run(box, w)["reason"] == "no cockpit session id configured" and not w.calls


def test_every_tick_is_logged(box):
    w = Waker()
    run(box, w)
    run(box, w)
    lines = (box["root"] / "run" / "watchdog" / "watchdog.jsonl").read_text().splitlines()
    assert len(lines) == 2 and all(json.loads(x)["action"] for x in lines)
