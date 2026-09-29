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


# ---- conductor_heartbeat ------------------------------------------------------------------------

def test_conductor_heartbeat_ok_when_never_emitted(tmp_path):
    c = cfg(tmp_path)
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok" and "no conductor yet" in r.detail


def test_conductor_heartbeat_ok_when_fresh(tmp_path):
    c = cfg(tmp_path)
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor", "detail": "queue: 1 running",
                           "ts": "2026-09-29T12:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T12:10:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok" and "10 min old" in r.detail


def test_conductor_heartbeat_warn_when_stale(tmp_path):
    c = cfg(tmp_path, conductor_stale_min=45)
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor", "detail": "queue: 1 running",
                           "ts": "2026-09-29T12:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")  # 60 min later
    r = M.check_conductor_heartbeat(c)
    assert r.status == "warn" and "60 min old" in r.detail and "45" in r.detail


def test_conductor_heartbeat_warn_never_block(tmp_path):
    """A stale Conductor is the watchdog's job (arch §5.5), not a dispatch gate: never block."""
    c = cfg(tmp_path, conductor_stale_min=1)
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor", "detail": "x",
                           "ts": "2020-01-01T00:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T13:00:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "warn"


def test_conductor_heartbeat_ignores_other_actors_and_kinds(tmp_path):
    c = cfg(tmp_path)
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "note", "actor": "conductor", "detail": "not a heartbeat"})
    append(c.events_path, {"kind": "heartbeat", "actor": "monitor", "detail": "not the conductor"})
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok" and "no conductor yet" in r.detail


def test_conductor_heartbeat_picks_the_newest_line(tmp_path):
    c = cfg(tmp_path)
    os.makedirs(c.run_dir, exist_ok=True)
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor", "detail": "old",
                           "ts": "2026-09-29T10:00:00+00:00"})
    append(c.events_path, {"kind": "heartbeat", "actor": "conductor", "detail": "new",
                           "ts": "2026-09-29T12:00:00+00:00"})
    c.now_fn = _fixed_now("2026-09-29T12:05:00+00:00")
    r = M.check_conductor_heartbeat(c)
    assert "5 min old" in r.detail


def test_conductor_heartbeat_tolerates_missing_file(tmp_path):
    c = cfg(tmp_path, events_path=str(tmp_path / "nonexistent" / "EVENTS.jsonl"))
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok"


def test_conductor_heartbeat_tolerates_malformed_lines(tmp_path):
    c = cfg(tmp_path)
    os.makedirs(c.run_dir, exist_ok=True)
    with open(c.events_path, "w", encoding="utf-8") as f:
        f.write("not json at all\n")
        f.write(json.dumps({"kind": "heartbeat", "actor": "conductor", "ts": "2026-09-29T12:00:00+00:00"}) + "\n")
    c.now_fn = _fixed_now("2026-09-29T12:00:30+00:00")
    r = M.check_conductor_heartbeat(c)
    assert r.status == "ok"


def test_conductor_heartbeat_is_in_check_names_and_run_checks(tmp_path):
    assert "conductor_heartbeat" in M.CHECK_NAMES
    results = M.run_checks(cfg(tmp_path))
    assert any(r.name == "conductor_heartbeat" for r in results)


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
