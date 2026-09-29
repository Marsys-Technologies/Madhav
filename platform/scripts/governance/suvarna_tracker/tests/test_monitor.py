"""Suvarṇa Monitor: each check's ok/warn/block paths, overall status + exit code, --emit dedupe,
--repair's conservative gating, and exception isolation. No network beyond 127.0.0.1, no real
cloud-sql-proxy/caffeinate/run_tracker.sh launches, no sleep over ~2s total."""
import http.server
import json
import os
import socket
import threading

import pytest

from suvarna_tracker import monitor as M
from suvarna_tracker.events import EventLog


def cfg(tmp_path, **kw):
    home = kw.pop("home", str(tmp_path / "home"))
    c = M.Config(home=home, **kw)
    return c


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# ---- db_proxy -----------------------------------------------------------------------------------

def test_db_proxy_ok_when_port_listening(tmp_path):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        r = M.check_db_proxy(cfg(tmp_path, db_port=port))
        assert r.status == "ok"
    finally:
        s.close()


def test_db_proxy_block_when_nothing_listening(tmp_path):
    port = free_port()  # bound-and-released: nothing listens on it now
    r = M.check_db_proxy(cfg(tmp_path, db_port=port))
    assert r.status == "block"


# ---- credential ----------------------------------------------------------------------------------

def test_credential_block_when_env_unset(tmp_path):
    r = M.check_credential(cfg(tmp_path, pgenv=None))
    assert r.status == "block"


def test_credential_block_when_file_missing(tmp_path):
    r = M.check_credential(cfg(tmp_path, pgenv=str(tmp_path / "nope.env")))
    assert r.status == "block"


def test_credential_ok_when_unreadable_but_correctly_permissioned(tmp_path):
    p = tmp_path / "pg.env"
    p.write_text("secret=do-not-read-me")
    os.chmod(p, 0o000)  # can't even be opened by us, but existence + permission check must not need to
    try:
        r = M.check_credential(cfg(tmp_path, pgenv=str(p)))
        assert r.status == "ok"
    finally:
        os.chmod(p, 0o600)  # restore so tmp_path cleanup can remove it


def test_credential_warn_when_too_open(tmp_path):
    p = tmp_path / "pg.env"
    p.write_text("secret=x")
    os.chmod(p, 0o644)
    r = M.check_credential(cfg(tmp_path, pgenv=str(p)))
    assert r.status == "warn"


def test_credential_ok_when_restricted(tmp_path):
    p = tmp_path / "pg.env"
    p.write_text("secret=x")
    os.chmod(p, 0o600)
    r = M.check_credential(cfg(tmp_path, pgenv=str(p)))
    assert r.status == "ok"


def test_credential_never_opens_the_file(tmp_path, monkeypatch):
    p = tmp_path / "pg.env"
    p.write_text("secret=x")
    os.chmod(p, 0o600)
    real_open = open

    def _guarded_open(path, *a, **kw):
        if str(path) == str(p):
            raise AssertionError("credential check must never open the file")
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", _guarded_open)
    r = M.check_credential(cfg(tmp_path, pgenv=str(p)))
    assert r.status == "ok"


# ---- credential_readonly (Fix 3, review #16) ------------------------------------------------------

def _cred_file(tmp_path):
    p = tmp_path / "pg.env"
    p.write_text("secret=do-not-read-me")
    os.chmod(p, 0o600)
    return str(p)


def test_credential_readonly_ok_when_readonly_and_no_write_grants(tmp_path):
    p = _cred_file(tmp_path)

    def q(pgenv, sql, timeout=10):
        assert pgenv == p
        if "default_transaction_read_only" in sql:
            return 0, "on\n", ""
        return 0, "0\n", ""

    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p, credential_query_fn=q))
    assert r.status == "ok"


def test_credential_readonly_blocks_when_writes_are_possible(tmp_path):
    p = _cred_file(tmp_path)

    def q(pgenv, sql, timeout=10):
        if "default_transaction_read_only" in sql:
            return 0, "off\n", ""
        return 0, "3\n", ""

    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p, credential_query_fn=q))
    assert r.status == "block" and "3" in r.detail


def test_credential_readonly_blocks_when_flag_on_but_grants_exist(tmp_path):
    p = _cred_file(tmp_path)

    def q(pgenv, sql, timeout=10):
        if "default_transaction_read_only" in sql:
            return 0, "on\n", ""
        return 0, "1\n", ""

    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p, credential_query_fn=q))
    assert r.status == "block"


def test_credential_readonly_warns_when_query_cannot_run(tmp_path):
    p = _cred_file(tmp_path)
    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p,
                                        credential_query_fn=lambda pgenv, sql, timeout=10: (1, "", "connection refused")))
    assert r.status == "warn"


def test_credential_readonly_warns_when_pgenv_unset(tmp_path):
    r = M.check_credential_readonly(cfg(tmp_path, pgenv=None))
    assert r.status == "warn"


def test_credential_readonly_warns_when_file_missing(tmp_path):
    r = M.check_credential_readonly(cfg(tmp_path, pgenv=str(tmp_path / "nope.env")))
    assert r.status == "warn"


def test_credential_readonly_warns_when_query_raises(tmp_path):
    p = _cred_file(tmp_path)

    def q(pgenv, sql, timeout=10):
        raise TimeoutError("psql hung")

    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p, credential_query_fn=q))
    assert r.status == "warn" and "TimeoutError" in r.detail


def test_credential_readonly_sanitizes_secret_looking_output(tmp_path):
    p = _cred_file(tmp_path)

    def q(pgenv, sql, timeout=10):
        return 1, "", "connection to postgres://user:hunter2@10.0.0.5:5432/db failed (password auth)"

    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p, credential_query_fn=q))
    assert r.status == "warn"
    assert "postgres://" not in r.detail and "password" not in r.detail and "@" not in r.detail


def test_credential_readonly_never_opens_the_file(tmp_path, monkeypatch):
    p = _cred_file(tmp_path)
    real_open = open

    def _guarded_open(path, *a, **kw):
        if str(path) == p:
            raise AssertionError("credential_readonly must never open the credential file itself")
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", _guarded_open)
    r = M.check_credential_readonly(cfg(tmp_path, pgenv=p,
                                        credential_query_fn=lambda pgenv, sql, timeout=10: (0, "on\n" if "read_only" in sql else "0\n", "")))
    assert r.status == "ok"


def test_credential_readonly_is_part_of_run_checks(tmp_path):
    results = M.run_checks(cfg(tmp_path))
    assert "credential_readonly" in {r.name for r in results}


# ---- power ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("src,status", [
    ("ac", "ok"),
    ("battery 75%", "warn"),
    ("battery 50%", "warn"),
    ("battery 49%", "block"),
    ("battery 5%", "block"),
    ("battery", "warn"),      # no percent found
    ("unknown", "warn"),
])
def test_power_statuses(tmp_path, src, status):
    c = cfg(tmp_path, power_source_fn=lambda: src)
    assert M.check_power(c).status == status


def test_power_check_raising_is_isolated_to_warn_via_run_checks(tmp_path):
    def boom():
        raise RuntimeError("pmset exploded")
    c = cfg(tmp_path, power_source_fn=boom)
    results = M.run_checks(c)
    power = next(r for r in results if r.name == "power")
    assert power.status == "warn" and "pmset exploded" in power.detail


# ---- sleep_prevented -------------------------------------------------------------------------------

def test_sleep_ok_when_caffeinate_running(tmp_path):
    def fake_run(cmd, timeout=5):
        if cmd[0] == "pgrep":
            return 0, "1234\n"
        raise AssertionError("should not need pmset when caffeinate is already running")
    r = M.check_sleep_prevented(cfg(tmp_path, run_fn=fake_run))
    assert r.status == "ok"


def test_sleep_ok_when_pmset_assertion_active(tmp_path):
    def fake_run(cmd, timeout=5):
        if cmd[0] == "pgrep":
            return 1, ""
        return 0, "   PreventUserIdleSystemSleep    1\n   PreventSystemSleep    0\n"
    r = M.check_sleep_prevented(cfg(tmp_path, run_fn=fake_run))
    assert r.status == "ok"


def test_sleep_warn_when_nothing_prevents_it(tmp_path):
    def fake_run(cmd, timeout=5):
        if cmd[0] == "pgrep":
            return 1, ""
        return 0, "   PreventUserIdleSystemSleep    0\n   PreventSystemSleep    0\n"
    r = M.check_sleep_prevented(cfg(tmp_path, run_fn=fake_run))
    assert r.status == "warn"


# ---- hold ------------------------------------------------------------------------------------------

def test_hold_ok_when_absent(tmp_path):
    c = cfg(tmp_path)
    assert M.check_hold(c).status == "ok"


def test_hold_block_when_present(tmp_path):
    c = cfg(tmp_path)
    os.makedirs(c.run_dir, exist_ok=True)
    open(c.hold_path, "w").close()
    assert M.check_hold(c).status == "block"


# ---- disk ------------------------------------------------------------------------------------------

GB = 1024 ** 3


@pytest.mark.parametrize("free_bytes,status", [
    (2 * GB, "block"),
    (10 * GB, "warn"),
    (100 * GB, "ok"),
])
def test_disk_statuses(tmp_path, free_bytes, status):
    c = cfg(tmp_path, disk_free_fn=lambda path: free_bytes)
    assert M.check_disk(c).status == status


# ---- tracker ---------------------------------------------------------------------------------------

def test_tracker_ok(tmp_path):
    c = cfg(tmp_path, http_get_fn=lambda url, timeout: (200, json.dumps({"ok": True}), None))
    assert M.check_tracker(c).status == "ok"


def test_tracker_warn_on_ok_false(tmp_path):
    c = cfg(tmp_path, http_get_fn=lambda url, timeout: (503, json.dumps({"ok": False}), None))
    assert M.check_tracker(c).status == "warn"


def test_tracker_warn_when_unreachable(tmp_path):
    c = cfg(tmp_path, http_get_fn=lambda url, timeout: (None, "", "connection refused"))
    assert M.check_tracker(c).status == "warn"


class _FailingHealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"ok": False}).encode()
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_tracker_warn_against_a_real_failing_local_server(tmp_path):
    httpd = http.server.HTTPServer(("127.0.0.1", 0), _FailingHealthHandler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    try:
        c = cfg(tmp_path, tracker_port=port)
        r = M.check_tracker(c)
        assert r.status == "warn"
    finally:
        httpd.shutdown()
        httpd.server_close()


# ---- overall + exit code --------------------------------------------------------------------------

def test_overall_status_is_the_worst():
    results = [M.CheckResult("a", "ok", ""), M.CheckResult("b", "warn", ""), M.CheckResult("c", "ok", "")]
    assert M.overall_status(results) == "warn"
    results.append(M.CheckResult("d", "block", ""))
    assert M.overall_status(results) == "block"


@pytest.mark.parametrize("status,code", [("ok", 0), ("warn", 1), ("block", 2)])
def test_exit_code_mapping(status, code):
    assert M.exit_code(status) == code


def test_run_checks_never_raises_when_a_check_is_broken(tmp_path, monkeypatch):
    monkeypatch.setitem(M._CHECK_FNS, "disk", lambda c: (_ for _ in ()).throw(RuntimeError("kaboom")))
    results = M.run_checks(cfg(tmp_path))
    disk = next(r for r in results if r.name == "disk")
    assert disk.status == "warn" and "kaboom" in disk.detail
    # every other check still ran normally
    assert {r.name for r in results} == set(M.CHECK_NAMES)


# ---- --emit: heartbeat every run, note only on change ------------------------------------------------

def notes_and_heartbeats(events_path):
    log = EventLog(events_path)
    log.refresh()
    notes = [e for e in log.events if e["kind"] == "note" and e["actor"] == "monitor"]
    heartbeats = [e for e in log.events if e["kind"] == "heartbeat" and e["actor"] == "monitor"]
    return notes, heartbeats


def _fully_ok_cfg(tmp_path):
    p = tmp_path / "pg.env"
    p.write_text("secret=x")
    os.chmod(p, 0o600)
    return cfg(tmp_path, pgenv=str(p), power_source_fn=lambda: "ac",
               port_open_fn=lambda port: True,
               run_fn=lambda cmd, timeout=5: (0, "1\n"), disk_free_fn=lambda p: 100 * GB,
               http_get_fn=lambda url, timeout: (200, json.dumps({"ok": True}), None))


def test_emit_writes_one_heartbeat_per_run_and_dedupes_notes(tmp_path):
    c = _fully_ok_cfg(tmp_path)

    M.run_once(c, emit_flag=True)
    notes, hbs = notes_and_heartbeats(c.events_path)
    assert len(hbs) == 1 and len(notes) == 1          # baseline note on the very first run

    M.run_once(c, emit_flag=True)                     # same state again
    notes, hbs = notes_and_heartbeats(c.events_path)
    assert len(hbs) == 2 and len(notes) == 1           # no new note: nothing changed

    # now change state: hold switch goes on
    os.makedirs(c.run_dir, exist_ok=True)
    open(c.hold_path, "w").close()
    M.run_once(c, emit_flag=True)
    notes, hbs = notes_and_heartbeats(c.events_path)
    assert len(hbs) == 3 and len(notes) == 2           # exactly one new note for the state change


def test_emit_failure_is_reported_not_raised(tmp_path):
    c = cfg(tmp_path, power_source_fn=lambda: "ac", db_port=free_port(),
            run_fn=lambda cmd, timeout=5: (0, "1\n"), disk_free_fn=lambda p: 100 * GB,
            http_get_fn=lambda url, timeout: (200, json.dumps({"ok": True}), None))
    # events_path points at a directory, so append() will fail — must be reported, not raised
    bad_dir = tmp_path / "events_is_a_dir"
    bad_dir.mkdir()
    c.events_path = str(bad_dir)
    report = M.run_once(c, emit_flag=True)
    assert report["emit_errors"], "an append failure into a directory path must surface as an error"


# ---- --repair --------------------------------------------------------------------------------------

class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, argv, cwd=None, log_path=None, env=None):
        self.calls.append({"argv": list(argv), "cwd": cwd, "log_path": log_path})


def test_repair_starts_tracker_when_down_and_not_stopped(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (1, ""))  # nothing already running
    by_name = {"tracker": M.CheckResult("tracker", "warn", "unreachable")}
    actions = M.repair(c, by_name)
    assert len(rec.calls) == 1
    assert "run_tracker.sh" in rec.calls[0]["argv"][-1]
    assert actions and "tracker" in actions[0]


def test_repair_skips_tracker_when_stop_file_present(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (1, ""))
    os.makedirs(c.run_dir, exist_ok=True)
    open(c.tracker_stop_path, "w").close()
    by_name = {"tracker": M.CheckResult("tracker", "warn", "unreachable")}
    actions = M.repair(c, by_name)
    assert rec.calls == []
    assert actions == []


def test_repair_does_nothing_when_hold_is_on(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (1, ""))
    os.makedirs(c.run_dir, exist_ok=True)
    open(c.hold_path, "w").close()
    by_name = {"tracker": M.CheckResult("tracker", "warn", "unreachable"),
               "db_proxy": M.CheckResult("db_proxy", "block", "down"),
               "sleep_prevented": M.CheckResult("sleep_prevented", "warn", "not prevented")}
    actions = M.repair(c, by_name)
    assert rec.calls == [] and actions == []


def test_repair_does_not_double_start_tracker_when_already_running(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (0, "9999\n"))  # pgrep finds it
    by_name = {"tracker": M.CheckResult("tracker", "warn", "unreachable")}
    actions = M.repair(c, by_name)
    assert rec.calls == []
    assert "already running" in actions[0]


def test_repair_starts_db_proxy_when_down_and_not_running(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (1, ""), db_port=9999)
    by_name = {"db_proxy": M.CheckResult("db_proxy", "block", "down")}
    actions = M.repair(c, by_name)
    assert len(rec.calls) == 1
    assert rec.calls[0]["argv"][0] == "cloud-sql-proxy"
    assert "9999" in rec.calls[0]["argv"]
    assert actions and "db_proxy" in actions[0]


def test_repair_starts_caffeinate_when_sleep_not_prevented(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (1, ""))
    by_name = {"sleep_prevented": M.CheckResult("sleep_prevented", "warn", "not prevented")}
    actions = M.repair(c, by_name)
    assert len(rec.calls) == 1
    assert rec.calls[0]["argv"] == ["caffeinate", "-dimsu"]
    assert actions and "sleep_prevented" in actions[0]


def test_repair_never_touches_hold_credential_disk_power(tmp_path):
    rec = _Recorder()
    c = cfg(tmp_path, launch_fn=rec, run_fn=lambda cmd, timeout=5: (1, ""))
    by_name = {"hold": M.CheckResult("hold", "block", "on"),
               "credential": M.CheckResult("credential", "block", "missing"),
               "disk": M.CheckResult("disk", "block", "critical"),
               "power": M.CheckResult("power", "block", "low")}
    actions = M.repair(c, by_name)
    assert rec.calls == [] and actions == []


def test_repair_launch_failure_is_reported_not_raised(tmp_path):
    def boom(argv, cwd=None, log_path=None, env=None):
        raise OSError("no such binary")
    c = cfg(tmp_path, launch_fn=boom, run_fn=lambda cmd, timeout=5: (1, ""))
    by_name = {"sleep_prevented": M.CheckResult("sleep_prevented", "warn", "not prevented")}
    actions = M.repair(c, by_name)
    assert actions and "repair failed" in actions[0]


# ---- run_once wiring --------------------------------------------------------------------------------

def test_run_once_reports_overall_and_matching_exit_code(tmp_path):
    c = cfg(tmp_path, power_source_fn=lambda: "ac", db_port=free_port(),
            run_fn=lambda cmd, timeout=5: (0, "1\n"), disk_free_fn=lambda p: 100 * GB,
            http_get_fn=lambda url, timeout: (200, json.dumps({"ok": True}), None))
    report = M.run_once(c)
    assert report["overall"] == "block"                     # db_proxy port not actually listening
    assert M.exit_code(report["overall"]) == 2


def test_db_proxy_repair_is_not_blocked_by_another_workstreams_proxy(tmp_path):
    """A proxy on a different port (e.g. the Gochara lane's 55440) must not stop our repair; the guard
    looks for a proxy on our own port only."""
    import subprocess
    from suvarna_tracker import monitor as M
    launched, patterns = [], []

    def run_fn(cmd, timeout=5):
        if cmd[:2] == ["pgrep", "-f"]:
            patterns.append(cmd[2])
            # simulate what real pgrep would match against the running processes
            import re
            procs = ["cloud-sql-proxy --address 127.0.0.1 --port 55440 madhav-astrology:asia-south1:amjis-postgres"]
            hits = [p for p in procs if re.search(cmd[2], p)]
            return (0, "123\n") if hits else (1, "")
        return (1, "")

    cfg = M.Config(home=str(tmp_path), db_port=5433, run_fn=run_fn,
                   launch_fn=lambda argv, **kw: launched.append(argv))
    actions = M._repair_db_proxy(cfg)
    assert launched and "--port" in launched[0] and "5433" in launched[0], actions
    # and a proxy on our own port does block a second launch
    launched.clear()
    cfg2 = M.Config(home=str(tmp_path), db_port=55440, run_fn=run_fn,
                    launch_fn=lambda argv, **kw: launched.append(argv))
    M._repair_db_proxy(cfg2)
    assert not launched
