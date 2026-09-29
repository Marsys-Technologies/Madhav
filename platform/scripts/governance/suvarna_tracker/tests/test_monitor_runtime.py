"""L.15 additions to the Monitor: the conductor_heartbeat check and --notify. No real osascript call,
no real sleep beyond what test_monitor.py already tolerates."""
import datetime as dt
import json
import os

from suvarna_tracker import monitor as M
from suvarna_tracker.events import append

GB = 1024 ** 3


def cfg(tmp_path, **kw):
    home = kw.pop("home", str(tmp_path / "home"))
    return M.Config(home=home, **kw)


def _fully_ok_cfg(tmp_path, **kw):
    p = tmp_path / "pg.env"
    p.write_text("secret=x")
    os.chmod(p, 0o600)
    base = dict(pgenv=str(p), power_source_fn=lambda: "ac", port_open_fn=lambda port: True,
                run_fn=lambda cmd, timeout=5: (0, "1\n"), disk_free_fn=lambda p_: 100 * GB,
                http_get_fn=lambda url, timeout: (200, json.dumps({"ok": True}), None))
    base.update(kw)
    return cfg(tmp_path, **base)


def _fixed_now(iso: str):
    parsed = dt.datetime.fromisoformat(iso)
    return lambda: parsed


# ---- conductor_heartbeat (F6: per-session — independent review) -------------------------------
#
# Heartbeats now carry actor: "conductor:<session>" (conductor_lock.py's own session concept),
# never the session-blind "conductor" the pre-fix check read — a single healthy session could
# otherwise mask another going silent. Tests below pin conductor_sessions=("engine", "exec")
# explicitly so they never depend on $SUVARNA_SESSIONS or the module's own default.

def test_conductor_heartbeat_ok_when_never_emitted(tmp_path):
    c = cfg(tmp_path, conductor_sessions=("engine", "exec"))
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok" and "no conductor yet" in r.detail


def test_conductor_heartbeat_ok_when_fresh(tmp_path):
    c = cfg(tmp_path, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "queue: 1 running",
                           "ts": "2026-09-29T12:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T12:10:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok" and "10 min old" in r.detail and "engine" in r.detail


def test_conductor_heartbeat_warn_when_stale(tmp_path):
    c = cfg(tmp_path, conductor_stale_min=45, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "queue: 1 running",
                           "ts": "2026-09-29T12:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")  # 60 min later
    r = M.check_conductor_heartbeat(c)
    assert r.status == "warn" and "60 min old" in r.detail and "45" in r.detail and "engine" in r.detail


def test_conductor_heartbeat_warn_never_block(tmp_path):
    """A stale Conductor is the watchdog's job (arch §5.5), not a dispatch gate: never block."""
    c = cfg(tmp_path, conductor_stale_min=1, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "x",
                           "ts": "2020-01-01T00:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "warn"


def test_conductor_heartbeat_ignores_other_actors_and_kinds(tmp_path):
    c = cfg(tmp_path, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "note", "actor": "conductor:engine", "detail": "not a heartbeat"})
    append(c.events_path, {"kind": "heartbeat", "actor": "monitor", "detail": "not the conductor"})
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok" and "no conductor yet" in r.detail


def test_conductor_heartbeat_picks_the_newest_line(tmp_path):
    c = cfg(tmp_path, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "old",
                           "ts": "2026-09-29T10:00:00+00:00"})
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "new",
                           "ts": "2026-09-29T12:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T12:05:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert "5 min old" in r.detail


def test_conductor_heartbeat_tolerates_missing_file(tmp_path):
    c = cfg(tmp_path, events_path=str(tmp_path / "nonexistent" / "EVENTS.jsonl"), conductor_sessions=("engine",))
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok"


def test_conductor_heartbeat_tolerates_malformed_lines(tmp_path):
    c = cfg(tmp_path, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    with open(c.events_path, "w", encoding="utf-8") as f:
        f.write("not json at all\n")
        f.write(json.dumps({"kind": "heartbeat", "actor": "conductor:engine", "ts": "2026-09-29T12:00:00+00:00"}) + "\n")
    c.now_fn = _fixed_now("2026-09-29T12:00:30+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok"


def test_conductor_heartbeat_is_in_check_names_and_run_checks(tmp_path):
    assert "conductor_heartbeat" in M.CHECK_NAMES
    results = M.run_checks(cfg(tmp_path))
    assert any(r.name == "conductor_heartbeat" for r in results)


# ---- F6 negative cases: one session's health must never mask another's -------------------------

def test_conductor_heartbeat_one_session_stale_warns_even_though_another_is_fresh(tmp_path):
    """The exact pre-fix defect: a session-blind read let a healthy session mask a silent one.
    Per-session evaluation must name the stale session specifically, regardless of "exec" being
    perfectly healthy."""
    c = cfg(tmp_path, conductor_stale_min=45, conductor_sessions=("engine", "exec"))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "stale",
                           "ts": "2026-09-29T10:00:00+00:00"})  # 3 hours old at "now" below
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:exec", "detail": "fresh",
                           "ts": "2026-09-29T12:55:00+00:00"})  # 5 min old
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "warn"
    assert "engine" in r.detail and "180 min old" in r.detail
    assert "exec" in r.detail  # the healthy session is still named, informationally


def test_conductor_heartbeat_session_never_seen_while_another_is_fresh_is_not_itself_a_problem(tmp_path):
    """A session that has simply never started is a fact about campaign phase, not a fault — it
    must not, on its own, turn an otherwise-healthy check into a warning."""
    c = cfg(tmp_path, conductor_stale_min=45, conductor_sessions=("engine", "exec"))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "fresh",
                           "ts": "2026-09-29T12:55:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok"
    assert "engine" in r.detail and "exec" in r.detail and "never heartbeated" in r.detail


def test_conductor_sessions_read_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv(M.CONDUCTOR_SESSIONS_ENV, "alpha, beta")
    c = cfg(tmp_path)  # no explicit conductor_sessions: reads the env
    assert M._conductor_sessions(c) == ("alpha", "beta")


def test_conductor_sessions_default_is_engine_and_exec(tmp_path, monkeypatch):
    monkeypatch.delenv(M.CONDUCTOR_SESSIONS_ENV, raising=False)
    c = cfg(tmp_path)
    assert M._conductor_sessions(c) == M.DEFAULT_CONDUCTOR_SESSIONS == ("engine", "exec")


# ---- F6: repair() never relaunches a Conductor whose lock is held by a live process -------------

from suvarna_tracker import conductor_lock as CL  # noqa: E402


def _stale_engine_cfg(tmp_path, **kw):
    c = cfg(tmp_path, conductor_stale_min=45, conductor_sessions=("engine",), **kw)
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "x",
                           "ts": "2026-09-29T10:00:00+00:00"})  # 3h old at the fixed "now" below
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")
    return c


def test_repair_conductor_never_relaunches_a_lock_held_by_a_live_process(tmp_path):
    c = _stale_engine_cfg(tmp_path)
    CL.acquire("engine", home=c.home, pid=os.getpid())  # our own pid: definitely alive
    actions = M._repair_conductor(c, "engine")
    assert len(actions) == 1 and "not relaunched" in actions[0] and "live process" in actions[0]


def test_repair_conductor_reports_gap_when_lock_not_live(tmp_path):
    c = _stale_engine_cfg(tmp_path)
    # no lock acquired at all: is_held_by_live_process is False
    actions = M._repair_conductor(c, "engine")
    assert len(actions) == 1 and "no automatic relaunch is wired" in actions[0]


def test_repair_conductor_does_nothing_when_fresh(tmp_path):
    c = cfg(tmp_path, conductor_stale_min=45, conductor_sessions=("engine",))
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor:engine", "detail": "x",
                           "ts": "2026-09-29T12:55:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")
    assert M._repair_conductor(c, "engine") == []


def test_repair_conductor_does_nothing_when_never_started(tmp_path):
    c = cfg(tmp_path, conductor_stale_min=45, conductor_sessions=("engine",))
    assert M._repair_conductor(c, "engine") == []


def test_repair_end_to_end_never_relaunches_live_conductor_lock(tmp_path):
    """Integration: run_once's own --repair path, through the real check → repair wiring, still
    honours the F6 guarantee."""
    c = _stale_engine_cfg(tmp_path, pgenv=None)
    CL.acquire("engine", home=c.home, pid=os.getpid())
    report = M.run_once(c, repair_flag=True)
    conductor_repairs = [a for a in report["repairs"] if a.startswith("conductor:engine")]
    assert len(conductor_repairs) == 1 and "not relaunched" in conductor_repairs[0]


def test_repair_conductor_suppressed_entirely_by_hold(tmp_path):
    c = _stale_engine_cfg(tmp_path)
    os.makedirs(c.run_dir, exist_ok=True)
    open(c.hold_path, "w").close()
    by_name = {"conductor_heartbeat": M.CheckResult("conductor_heartbeat", "warn", "engine stale")}
    assert M.repair(c, by_name) == []


# ---- --notify -------------------------------------------------------------------------------------

class _NotifyRecorder:
    def __init__(self):
        self.calls = []

    def __call__(self, summary):
        self.calls.append(summary)


def test_notify_fires_on_first_run_when_notok_present(tmp_path):
    rec = _NotifyRecorder()
    c = cfg(tmp_path, notify_fn=rec)  # nothing configured => everything non-ok on a fresh Config
    M.run_once(c, notify_flag=True)
    assert len(rec.calls) == 1


def test_notify_does_not_fire_when_nothing_changed(tmp_path):
    rec = _NotifyRecorder()
    c = _fully_ok_cfg(tmp_path, notify_fn=rec)
    M.run_once(c, notify_flag=True)
    M.run_once(c, notify_flag=True)  # same state again
    assert len(rec.calls) == 1  # only the baseline change from "no prior state" to ok


def test_notify_fires_again_on_state_change(tmp_path):
    rec = _NotifyRecorder()
    c = _fully_ok_cfg(tmp_path, notify_fn=rec)
    M.run_once(c, notify_flag=True)
    os.makedirs(c.run_dir, exist_ok=True)
    open(c.hold_path, "w").close()
    M.run_once(c, notify_flag=True)
    assert len(rec.calls) == 2


def test_notify_off_by_default(tmp_path):
    rec = _NotifyRecorder()
    c = cfg(tmp_path, notify_fn=rec)
    M.run_once(c)  # no flags at all
    assert rec.calls == []


def test_notify_and_emit_together_share_one_dedupe_and_one_save(tmp_path):
    rec = _NotifyRecorder()
    c = _fully_ok_cfg(tmp_path, notify_fn=rec)
    report1 = M.run_once(c, emit_flag=True, notify_flag=True)
    assert report1["notified"] is True and len(rec.calls) == 1
    report2 = M.run_once(c, emit_flag=True, notify_flag=True)
    assert report2["notified"] is False and len(rec.calls) == 1  # no new notification: nothing changed


def test_notify_alone_persists_dedupe_state_across_runs(tmp_path):
    """--notify used without --emit must still save monitor_state.json itself, or every run would
    look like a change forever."""
    rec = _NotifyRecorder()
    c = _fully_ok_cfg(tmp_path, notify_fn=rec)
    M.run_once(c, notify_flag=True)
    M.run_once(c, notify_flag=True)
    M.run_once(c, notify_flag=True)
    assert len(rec.calls) == 1


def test_notify_failure_is_swallowed_not_raised(tmp_path):
    def boom(summary):
        raise RuntimeError("no notification centre")
    c = cfg(tmp_path, notify_fn=boom)
    report = M.run_once(c, notify_flag=True)  # must not raise
    assert report["overall"] in ("ok", "warn", "block")


def test_default_notify_sanitises_quotes_and_backslashes(monkeypatch):
    calls = []

    def fake_run(argv, timeout=None, capture_output=None):
        calls.append(argv)
        class R:
            pass
        return R()

    monkeypatch.setattr(M.subprocess, "run", fake_run)
    M._default_notify('say "hi" \\ bye')
    assert len(calls) == 1
    script = calls[0][-1]
    assert calls[0][0] == "osascript" and calls[0][1] == "-e"
    # no unescaped double quote from the payload breaks out of the AppleScript literal
    assert 'display notification "' in script
    assert '\\"hi\\"' in script
    assert '\\\\' in script


def test_default_notify_truncates_long_text(monkeypatch):
    calls = []
    monkeypatch.setattr(M.subprocess, "run", lambda *a, **k: calls.append(a))
    M._default_notify("x" * 500)
    script = calls[0][-1]
    assert len(script) < 500 + 60


def test_default_notify_never_raises_on_subprocess_failure(monkeypatch):
    def boom(*a, **k):
        raise OSError("no osascript on this box")
    monkeypatch.setattr(M.subprocess, "run", boom)
    M._default_notify("anything")  # must not raise
