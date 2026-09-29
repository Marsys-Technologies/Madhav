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


# ---- credential_readonly (Fix 3, review #16; D6 self-privilege checks) ------------------------------

def _cred_file(tmp_path):
    p = tmp_path / "pg.env"
    p.write_text("secret=do-not-read-me")
    os.chmod(p, 0o600)
    return str(p)


_CLEAN = {
    "current_user": "suvarna_reader", "read_only": "on", "elevated": "false",
    "table_write": "0", "column_write": "0", "sequence_write": "0",
    "database_create": "false", "database_temp": "true", "schema_create": "0",
    "member_of": "0", "members_of_me": "0", "owned_objects": "0",
    "auth_schema_usage": "false", "auth_dependent_views": "0",
}


def _facts(secdef=(), drop=(), end=True, **over):
    """psql -tAX output of the self-privilege query: one key|value row per fact, end|ok last."""
    facts = {**_CLEAN, **{k: str(v) for k, v in over.items()}}
    rows = [f"{k}|{v}" for k, v in facts.items() if k not in drop] + [f"secdef|{s}" for s in secdef]
    if end:
        rows.append("end|ok")
    return "\n".join(rows) + "\n"


def _fake(output, rc=0, err=""):
    calls = []

    def q(pgenv, sql, timeout=10):
        calls.append((pgenv, sql))
        return rc, output, err
    q.calls = calls
    return q


def _ro(tmp_path, output, **kw):
    p = _cred_file(tmp_path)
    q = _fake(output)
    return M.check_credential_readonly(cfg(tmp_path, pgenv=p, credential_query_fn=q, **kw)), q, p


def test_credential_readonly_ok_when_readonly_and_no_write_grants(tmp_path):
    r, q, p = _ro(tmp_path, _facts())
    assert r.status == "ok"
    assert "suvarna_reader" in r.detail and "no write path" in r.detail
    assert [pgenv for pgenv, _ in q.calls] == [p]  # one round trip, with the configured file


def test_credential_readonly_blocks_when_writes_are_possible(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(current_user="amjis_app", read_only="off", table_write=3))
    assert r.status == "block" and "3" in r.detail


def test_credential_readonly_blocks_when_flag_on_but_grants_exist(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(table_write=1))
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
                                        credential_query_fn=lambda pgenv, sql, timeout=10: (0, _facts(), "")))
    assert r.status == "ok"


def test_credential_readonly_is_part_of_run_checks(tmp_path):
    results = M.run_checks(cfg(tmp_path))
    assert "credential_readonly" in {r.name for r in results}


@pytest.mark.parametrize("over,needle", [
    ({"column_write": 2}, "column"),
    ({"sequence_write": 1}, "sequences"),
    ({"schema_create": 1}, "schemas with CREATE"),
    ({"database_create": "true"}, "database CREATE"),
    ({"member_of": 1}, "memberships"),
    ({"owned_objects": 4}, "owned objects"),
    ({"elevated": "true"}, "elevated"),
    ({"auth_schema_usage": "true"}, "schema auth"),
    ({"auth_dependent_views": 1}, "views over schema auth"),
])
def test_credential_readonly_blocks_on_every_write_path(tmp_path, over, needle):
    r, _, _ = _ro(tmp_path, _facts(**over))
    assert r.status == "block" and needle in r.detail


def test_credential_readonly_blocks_on_reachable_security_definer(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(secdef=["public.grant_everything(text)"]), secdef_allowlist=frozenset())
    assert r.status == "block" and "SECURITY DEFINER" in r.detail and "public.grant_everything(text)" in r.detail


def test_credential_readonly_accepts_allowlisted_security_definer(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(secdef=["public.safe_lookup(integer, text)"]),
                  secdef_allowlist=frozenset({"public.safe_lookup(integer, text)"}))
    assert r.status == "ok" and "1 accepted" in r.detail


def test_credential_readonly_reads_secdef_allowlist_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv(M.SECDEF_ALLOW_ENV, "public.a(integer, text); public.b()")
    r, _, _ = _ro(tmp_path, _facts(secdef=["public.a(integer, text)", "public.b()"]))
    assert r.status == "ok"
    monkeypatch.setenv(M.SECDEF_ALLOW_ENV, "public.b()")
    r2, _, _ = _ro(tmp_path, _facts(secdef=["public.a(integer, text)", "public.b()"]))
    assert r2.status == "block"


def test_credential_readonly_warns_when_login_is_not_the_reader(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(current_user="retrieval_census_ro"))
    assert r.status == "warn" and "retrieval_census_ro" in r.detail and "suvarna_reader" in r.detail


def test_credential_readonly_warns_when_another_role_can_assume_the_login(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(members_of_me=1))
    assert r.status == "warn" and "assume" in r.detail


def test_credential_readonly_warns_when_session_flag_off_without_write_path(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(read_only="off"))
    assert r.status == "warn" and "default_transaction_read_only=off" in r.detail


@pytest.mark.parametrize("output", [
    _facts(end=False),                         # truncated: no terminator
    _facts(drop=("sequence_write",)),          # a fact missing
    _facts(table_write="lots"),                # count not numeric
    _facts(database_create="yes"),             # flag not boolean
    "garbage-without-separator\nend|ok\n",     # unparseable row
    "",                                        # nothing at all
])
def test_credential_readonly_never_passes_untrustworthy_output(tmp_path, output):
    r, _, _ = _ro(tmp_path, output)
    assert r.status == "warn"


def test_credential_readonly_sanitizes_login_in_detail(tmp_path):
    r, _, _ = _ro(tmp_path, _facts(current_user="someone@host"))
    assert r.status == "warn" and "@" not in r.detail


def test_self_privilege_sql_evaluates_the_login_itself():
    sql = M._SELF_PRIVILEGE_SQL
    for fragment in ("has_table_privilege(current_user", "has_any_column_privilege(current_user",
                     "has_sequence_privilege(current_user", "has_database_privilege(current_user",
                     "has_schema_privilege(current_user", "has_function_privilege(current_user",
                     "pg_auth_members", "pg_shdepend", "prosecdef", "nspname = 'auth'", "'end', 'ok'"):
        assert fragment in sql, fragment
    for priv in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"):
        assert priv in sql


def test_self_privilege_sql_is_shell_safe():
    sql = M._SELF_PRIVILEGE_SQL
    for ch in ("$", "!", "`", "\\", '"', "\n"):
        assert ch not in sql, repr(ch)


def test_default_query_fn_passes_the_sql_through_bash_intact(tmp_path):
    """The real helper sources the file in bash and runs psql -c "<sql>"; a stand-in psql on PATH
    records its -c argument so the quoting is proven without any database."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    record = tmp_path / "psql_arg.txt"
    fake_psql = bindir / "psql"
    fake_psql.write_text(f'#!/bin/bash\nprintf %s "$3" > {record}\necho "end|ok"\n')
    os.chmod(fake_psql, 0o755)
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text(f'export PATH="{bindir}:$PATH"\n')
    os.chmod(pgenv, 0o600)
    rc, out, _ = M._default_credential_query_fn(str(pgenv), M._SELF_PRIVILEGE_SQL, 10)
    assert rc == 0 and out.strip() == "end|ok"
    assert record.read_text() == M._SELF_PRIVILEGE_SQL


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
