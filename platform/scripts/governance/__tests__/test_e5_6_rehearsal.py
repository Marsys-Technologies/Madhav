"""test_e5_6_rehearsal.py -- the E5.6/E5.7 rehearsal harness (`suvarna_rehearsal.py`), tests-first and mutation-checked.

No production database, credential or network is touched. PostgreSQL appears ONLY through the repo's disposable fixture
(`_disposable_pg`): a throw-away loopback cluster in a temp dir. Cluster-lifecycle tests use STUB `initdb`/`pg_ctl` scripts in a
temp dir (they record argv and environment), so no real cluster is ever created by them.

Layout
  1. connection policy        refusals open no socket; the log is what `no_production_write` is judged on
  2. cluster lifecycle        marker, flock lockfile, loopback-only config, env -i, process identity, reap confirmation
  3. evidence                 closed schema, derived results (a hand-edited PASS fails), NEEDS_* = UNMEASURED, self_test never PASS
  4. E5.7 comparison          an unexplained difference fails; an empty comparison is not PASS
  5. self-test cases          real SQL on the disposable cluster / the real `suvarna_level_wave.run_cli`; each case also run
                              against a broken variant that must flip it to FAIL
  6. source mutants           one textual mutation per verdict-deciding line of the harness; the invariant suite must catch each
"""
from __future__ import annotations

import copy
import json
import os
import pathlib
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import textwrap
import types
from collections.abc import Callable

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
sys.path.insert(0, str(GOV))
sys.path.insert(0, str(HERE))

import suvarna_rehearsal as sr  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture must be importable here)

SRC = (GOV / "suvarna_rehearsal.py").read_text(encoding="utf-8")
H = "ab" * 32            # a sha256-shaped value
H2 = "cd" * 32
SHA40 = "1" * 40


# ───────────────────────────── helpers: good measurements for every case ─────────────────────────────

def good_measured(case_id: str) -> dict:
    return copy.deepcopy({
        "idempotent_rebuild_fingerprint_unchanged": {
            "fingerprint_before": H, "fingerprint_after_rebuild": H, "fingerprint_after_material_change": H2,
            "other_chart_before": H2, "other_chart_after": H2, "rows_before": 40, "rows_after": 40,
            "volatile_columns_changed": True},
        "family_dispatch_refused": {
            "intersecting_assets": ["ka_x", "ka_gochara_y"], "refused_assets": ["ka_gochara_y", "ka_x"],
            "refused_via": ["family_set", "name_pattern"], "exit_code": 4, "refusal_codes": ["FAMILY_ASSET"], "connect_calls": 0,
            "dispatch_calls": 0, "control_exit_code": 4, "control_refusal_codes": ["DEPLOYED_JOB_SHA_REQUIRED"],
            "control_connect_calls": 0, "missing_file_committing_codes": ["FAMILY_FILE_MISSING"]},
        "hold_refuses_dispatch": {
            "hold_guard_sha256": H, "command": "python3 x/suvarna_level_wave.py --assets a", "blocked_with_hold": True,
            "blocked_without_hold": False, "reason_with_hold": "hold is set", "non_dispatch_blocked_with_hold": False},
        "canary_triggers_reversal": {
            "baseline_canary_passed": True, "injected_difference_failed_canary": True, "reversal_triggered": True,
            "fingerprint_pre": H, "fingerprint_post_reversal": H},
        "f3_proof": {
            "referencing_tables_populated": {f"t{i}": 3 for i in range(7)}, "msr_replace_refused": False,
            "dangling_after_change": 10, "dangling_tool": "msr_dangling_signal_refs.py",
            "dangling_after_downstream_rebuild": 0, "referencing_rows_restored": {f"t{i}": True for i in range(7)}, "downstream_waves": [["ka_a"], ["ph_b"]], "fk_state": {"kala": 0, "l2": 3}},
        "find_fix_rebuild_certify": {
            "finding_id": "R-1", "census_run_id": "run-9", "stale_after_fix_detected": True, "fingerprint_before": H,
            "fingerprint_after_rebuild": H2, "certificate_current_after_certify": True, "certificate_detector_not_none": True,
            "orchestrator_commit": SHA40, "evidence_commit": SHA40},
        "no_production_write": {
            "opened": [{"host": "127.0.0.1", "port": 40001, "database": "suvarna_disposable", "policy": "disposable",
                        "data_directory": "/tmp/x/data", "verified": True}],
            "refused_count": 2, "probe_refused_without_socket": True},
    }[case_id])


def self_test_doc(mod=sr, *, measured: dict | None = None, unmeasured: dict | None = None) -> dict:
    """A self_test document: the 4 offline-measurable cases measured, the other 3 UNMEASURED."""
    cases = []
    for cid in ("idempotent_rebuild_fingerprint_unchanged", "family_dispatch_refused", "hold_refuses_dispatch", "no_production_write"):
        m = (measured or {}).get(cid, good_measured(cid))
        cases.append(mod.case_result(cid, measured=m, basis="synthetic_fixture"))
    for cid, reason in {"find_fix_rebuild_certify": "NEEDS_REHEARSAL_ORCHESTRATOR_RUN", "f3_proof": "NEEDS_REHEARSAL_SCHEMA_WITH_1036",
                        "canary_triggers_reversal": "NEEDS_CANARY_REVERSAL_MECHANISM"}.items():
        cases.append(mod.unmeasured_case(cid, reason))
    env = {"cluster": {"kind": "disposable", "host": "127.0.0.1", "port": 40001, "data_directory": "/tmp/x/data", "pg_version": "15.17"},
           "schema_replay": None, "seed": None}
    return mod.build_evidence(mode="self_test", commit=SHA40, cases=cases, environment=env)


def rehearsal_measured(case_id: str) -> dict:
    m = good_measured(case_id)
    if case_id == "no_production_write":            # a rehearsal document may only hold rehearsal-policy connections
        m["opened"] = [{"host": "127.0.0.1", "port": 55432, "database": "rehearsal", "policy": "rehearsal",
                        "data_directory": f"{sr.DEFAULT_ROOT}/pg", "verified": True}]
    return m


def rehearsal_doc(mod=sr, *, result_of: dict | None = None) -> dict:
    cases = []
    for cid in sr.REQUIRED_CASES:
        c = mod.case_result(cid, measured=rehearsal_measured(cid), basis="rehearsal_db", fingerprints={"fp": H},
                            evidence=[{"path": f"E5.6/{cid}.txt", "sha256": H}])
        cases.append(c)
    env = {"cluster": {"kind": "rehearsal", "host": "127.0.0.1", "port": 55432, "data_directory": f"{sr.DEFAULT_ROOT}/pg",
                       "pg_version": "15.17"},
           "schema_replay": {"files_applied": 757, "files_failed": 0, "report_sha256": H},
           "seed": {"manifest_sha256": H2, "tables": ["asset_registry"]}}
    return mod.build_evidence(mode="rehearsal", commit=SHA40, cases=cases, environment=env, orchestrator_commit=SHA40,
                              job_image_commit=SHA40)


# ═════════════════════════ 1. connection policy ═════════════════════════

class FakeConn:
    """A stand-in connection that answers the identity query like a server would (or lies, for the refusal tests)."""

    def __init__(self, data_directory: str, host: str = "127.0.0.1", port: int = 55432, database: str = "rehearsal", fail: bool = False):
        self.row, self.closed, self.fail = (data_directory, host, port, database), False, fail

    def execute(self, sql, *a):
        if self.fail:
            raise RuntimeError("no answer")
        row = self.row
        return types.SimpleNamespace(fetchone=lambda: row)

    def close(self):
        self.closed = True


def rehearsal_conn(**kw) -> FakeConn:
    return FakeConn(f"{sr.DEFAULT_ROOT}/pg", **kw)


REHEARSAL_URL = "postgresql://" + "Dev" + "@127.0.0.1:55432/rehearsal"
DISPOSABLE_URL = "postgresql://" + "suvarna_disposable" + "@127.0.0.1:40123/suvarna_disposable"


@pytest.mark.parametrize("url", [
    "postgresql://u@10.0.0.5:5432/rehearsal", "postgresql://u@localhost:55432/rehearsal", "postgresql://u@127.0.0.1:5432/rehearsal",
    "postgresql://u@127.0.0.1:55432/postgres", "postgresql://u:" + "pw" + "@127.0.0.1:55432/rehearsal",
    "postgresql://u@127.0.0.1:55432/rehearsal?host=10.0.0.5", "", None,
    "postgresql://u@127.0.0.1:55432/rehearsal_prod_amjis",
])
def test_rehearsal_policy_refuses_and_opens_no_socket(url):
    log, calls = sr.ConnectionLog(), []
    with pytest.raises(sr.EndpointRefused):
        sr.connect_checked(url, "rehearsal", log, connect=lambda *a, **k: calls.append(a))
    assert calls == [] and log.opened == [] and len(log.refused) == 1


def test_rehearsal_policy_accepts_only_the_guard_url_and_dials_the_normalised_value():
    log, dialled = sr.ConnectionLog(), []
    sr.connect_checked(REHEARSAL_URL + "?application_name=e56", "rehearsal", log, connect=lambda u: dialled.append(u) or rehearsal_conn())
    assert dialled == ["postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=e56"]
    assert log.opened == [{"host": "127.0.0.1", "port": 55432, "database": "rehearsal", "policy": "rehearsal",
                           "data_directory": f"{sr.DEFAULT_ROOT}/pg", "verified": True}]


def test_the_NORMALISED_url_is_what_is_dialled_not_the_raw_one(monkeypatch):
    monkeypatch.setitem(sr.POLICIES, "rehearsal", lambda u: "postgresql://Dev@127.0.0.1:55432/rehearsal")
    dialled = []
    sr.connect_checked("postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=raw", "rehearsal", sr.ConnectionLog(),
                       connect=lambda u: dialled.append(u) or rehearsal_conn())
    assert dialled == ["postgresql://Dev@127.0.0.1:55432/rehearsal"]


def test_the_pg_environment_is_scrubbed_around_the_dial_and_restored_after(monkeypatch):
    for k, v in (("PGHOSTADDR", "::1"), ("PGSERVICE", "x"), ("PGPASSFILE", "/x"), ("PGHOST", "evil"), ("DATABASE_URL", "u"),
                 ("POSTGRES_URL", "u"), ("KEEP_ME", "1")):
        monkeypatch.setenv(k, v)
    seen = {}

    def dial(u):
        seen.update({k: os.environ.get(k) for k in ("PGHOSTADDR", "PGSERVICE", "PGPASSFILE", "PGHOST", "DATABASE_URL", "POSTGRES_URL", "KEEP_ME")})
        return rehearsal_conn()
    sr.connect_checked(REHEARSAL_URL, "rehearsal", sr.ConnectionLog(), connect=dial)
    assert seen == {"PGHOSTADDR": None, "PGSERVICE": None, "PGPASSFILE": None, "PGHOST": None, "DATABASE_URL": None,
                    "POSTGRES_URL": None, "KEEP_ME": "1"}
    assert os.environ["PGHOSTADDR"] == "::1" and os.environ["DATABASE_URL"] == "u" and os.environ["PGHOST"] == "evil"


@pytest.mark.parametrize("conn,why", [
    (lambda: rehearsal_conn(host="::1"), "127.0.0.1"), (lambda: rehearsal_conn(host="10.0.0.5"), "127.0.0.1"),
    (lambda: rehearsal_conn(port=5432), "forbidden"), (lambda: rehearsal_conn(port=55433), "rehearsal port"),
    (lambda: rehearsal_conn(database="postgres"), "rehearsal port"),
    (lambda: FakeConn("/somewhere/else/pg"), "data_directory"), (lambda: rehearsal_conn(fail=True), "could not verify"),
])
def test_the_answering_server_is_verified_before_the_connection_is_logged_or_returned(conn, why):
    log, made = sr.ConnectionLog(), []
    with pytest.raises(sr.EndpointRefused, match=why):
        sr.connect_checked(REHEARSAL_URL, "rehearsal", log, connect=lambda u: made.append(conn()) or made[-1])
    assert log.opened == [] and len(log.refused) == 1 and made[0].closed is True


def test_disposable_policy_verifies_the_fixtures_own_identity():
    log = sr.ConnectionLog()
    good = FakeConn("/tmp/x/data", port=40123, database="suvarna_disposable")
    sr.connect_checked(DISPOSABLE_URL, "disposable", log, connect=lambda u: good, expect={"data_directory": "/tmp/x/data", "port": 40123})
    assert log.opened[0]["data_directory"] == "/tmp/x/data" and log.opened[0]["verified"] is True
    for conn, expect in ((FakeConn("/tmp/y/data", port=40123, database="suvarna_disposable"), {"data_directory": "/tmp/x/data", "port": 40123}),
                         (FakeConn("/tmp/x/data", port=40124, database="suvarna_disposable"), {"data_directory": "/tmp/x/data", "port": 40123}),
                         (FakeConn("/tmp/x/data", port=40123, database="postgres"), {"data_directory": "/tmp/x/data", "port": 40123}),
                         (FakeConn("/tmp/x/data", port=40123, database="suvarna_disposable"), None)):
        with pytest.raises(sr.EndpointRefused):
            sr.connect_checked(DISPOSABLE_URL, "disposable", sr.ConnectionLog(), connect=lambda u, c=conn: c, expect=expect)
        assert conn.closed


def test_a_real_connection_is_not_redirected_by_a_poisoned_libpq_environment(needs_psycopg, disposable_pg, monkeypatch):
    for k, v in (("PGHOSTADDR", "::1"), ("PGSERVICE", "nope"), ("PGPASSFILE", "/x"), ("PGHOST", "10.9.9.9"), ("PGPORT", "1")):
        monkeypatch.setenv(k, v)
    log = sr.ConnectionLog()
    conn = sr.connect_checked(disposable_pg.url, "disposable", log, expect={"data_directory": str(disposable_pg.data_dir), "port": disposable_pg.port})
    conn.close()
    assert log.opened[0]["port"] == disposable_pg.port and log.opened[0]["verified"] is True


@pytest.mark.parametrize("url", [
    "postgresql://suvarna_disposable@127.0.0.1:55432/suvarna_disposable", "postgresql://suvarna_disposable@127.0.0.1:5432/suvarna_disposable",
    "postgresql://suvarna_disposable@10.1.1.1:40123/suvarna_disposable", "postgresql://suvarna_disposable@localhost:40123/suvarna_disposable",
    "postgresql://suvarna_disposable@127.0.0.1:40123/postgres", "postgresql://suvarna_disposable@127.0.0.1:40123/suvarna_disposable?sslmode=disable",
    "postgresql://suvarna_disposable:" + "pw" + "@127.0.0.1:40123/suvarna_disposable", "postgresql://suvarna_disposable@127.0.0.1/suvarna_disposable",
    "postgresql://x@evil.com:" + "40123" + "@127.0.0.1:40123/suvarna_disposable",
])
def test_disposable_policy_refuses(url):
    with pytest.raises(sr.EndpointRefused):
        sr.connect_checked(url, "disposable", sr.ConnectionLog(), connect=lambda *a, **k: pytest.fail("a refused endpoint was dialled"))


def test_disposable_policy_accepts_a_loopback_random_port():
    log = sr.ConnectionLog()
    sr.connect_checked(DISPOSABLE_URL, "disposable", log, connect=lambda u: FakeConn("/tmp/x/data", port=40123, database="suvarna_disposable"),
                       expect={"data_directory": "/tmp/x/data", "port": 40123})
    assert log.opened[0]["port"] == 40123


def test_unknown_policy_refused():
    with pytest.raises(sr.EndpointRefused):
        sr.connect_checked(REHEARSAL_URL, "anything", sr.ConnectionLog(), connect=lambda *a: rehearsal_conn())


def test_the_final_loopback_check_stands_even_if_a_policy_were_permissive(monkeypatch):
    monkeypatch.setitem(sr.POLICIES, "permissive", lambda u: u)
    with pytest.raises(sr.EndpointRefused):
        sr.connect_checked("postgresql://u@10.0.0.5:40123/d", "permissive", sr.ConnectionLog(), connect=lambda *a: pytest.fail("dialled"))
    with pytest.raises(sr.EndpointRefused):
        sr.connect_checked("postgresql://u@127.0.0.1:5432/d", "permissive", sr.ConnectionLog(), connect=lambda *a: pytest.fail("dialled"))


# ═════════════════════════ 2. cluster lifecycle (stub binaries) ═════════════════════════

STUB_INITDB = """#!/bin/bash
# stub initdb: records argv + environment next to itself, creates a minimal data dir
d="$(cd "$(dirname "$0")" && pwd)"
{ echo "initdb $*"; env | sort; } >> "$d/calls.log"
while [ $# -gt 0 ]; do case "$1" in -D) D="$2"; shift 2;; *) shift;; esac; done
mkdir -p "$D"; echo 15 > "$D/PG_VERSION"
printf "#listen_addresses = 'localhost'\\n#port = 5432\\n#include_dir = 'conf.d'\\n" > "$D/postgresql.conf"
printf "# TYPE DATABASE USER ADDRESS METHOD\\nlocal all all trust\\nhost all all 127.0.0.1/32 trust\\n" > "$D/pg_hba.conf"
"""
STUB_PG_CTL = """#!/bin/bash
d="$(cd "$(dirname "$0")" && pwd)"
{ echo "pg_ctl $*"; env | sort; } >> "$d/calls.log"
while [ $# -gt 0 ]; do case "$1" in -D) D="$2"; shift 2;; start|stop) A="$1"; shift;; *) shift;; esac; done
if [ "$A" = start ]; then echo 4242 > "$D/postmaster.pid"; fi
if [ "$A" = stop ]; then rm -f "$D/postmaster.pid"; fi
exit 0
"""


@pytest.fixture()
def stubs(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    for name, body in (("initdb", STUB_INITDB), ("pg_ctl", STUB_PG_CTL)):
        (b / name).write_text(body)
        (b / name).chmod(0o755)
    return b


@pytest.fixture()
def short_base():
    """A SHORT real directory: a unix-socket path must stay under ~100 bytes and pytest's tmp_path can be longer."""
    base = pathlib.Path(os.path.realpath(tempfile.mkdtemp(prefix="e56r", dir="/tmp")))
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture()
def root(short_base, monkeypatch):
    r = short_base / "rehearsal"
    monkeypatch.setattr(sr, "DEFAULT_ROOT", str(r))        # `reap --remove-data` only ever deletes under DEFAULT_ROOT
    return r


@pytest.fixture()
def needs_psycopg():
    """Listed BEFORE `disposable_pg` so a missing driver skips (CI's governance shard installs only pyyaml + pytest)."""
    return pytest.importorskip("psycopg")


def EXPECT(cl) -> dict:
    return {"data_directory": str(cl.data_dir), "port": cl.port}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _calls(stubs) -> str:
    f = stubs / "calls.log"
    return f.read_text() if f.exists() else ""


def test_init_creates_a_marked_loopback_cluster_and_is_idempotent(root, stubs):
    port = _free_port()
    r1 = sr.init_cluster(root, port=port, pg_bin=str(stubs))
    assert r1["result"] == "initialised"
    marker = sr.read_marker(root)
    assert marker["port"] == port and marker["host"] == "127.0.0.1" and marker["uid"] == os.getuid()
    assert stat.S_IMODE(root.stat().st_mode) == 0o700 and stat.S_IMODE((root / "sock").stat().st_mode) == 0o700
    conf = (root / "pg" / "postgresql.conf").read_text()
    assert "listen_addresses = '127.0.0.1'" in conf and f"port = {port}" in conf and "unix_socket_permissions = 0700" in conf
    assert (root / "pg" / "pg_hba.conf").read_text().count("trust") == 2
    n = _calls(stubs).count("initdb ")
    assert sr.init_cluster(root, port=port, pg_bin=str(stubs))["result"] == "already_initialised"
    assert _calls(stubs).count("initdb ") == n                         # initdb was NOT run again


@pytest.mark.parametrize("port", [5432, 6432, 6543, 80, 70000, True, "55432"])
def test_init_refuses_forbidden_or_malformed_ports(root, stubs, port):
    with pytest.raises(sr.LifecycleError):
        sr.init_cluster(root, port=port, pg_bin=str(stubs))
    assert not root.exists()


def test_init_refuses_a_non_empty_data_dir_without_a_marker(root, stubs):
    (root / "pg").mkdir(parents=True)
    os.chmod(root, 0o700)
    (root / "pg" / "somebody_elses_file").write_text("x")
    with pytest.raises(sr.LifecycleError, match="no ownership marker"):
        sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    assert (root / "pg" / "somebody_elses_file").exists() and not (root / sr.MARKER_NAME).exists()


def test_init_refuses_an_invalid_marker_and_a_port_change(root, stubs):
    port = _free_port()
    sr.init_cluster(root, port=port, pg_bin=str(stubs))
    with pytest.raises(sr.LifecycleError, match="marker says port"):
        sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    (root / sr.MARKER_NAME).write_text("{not json")
    with pytest.raises(sr.LifecycleError, match="invalid marker"):
        sr.init_cluster(root, port=port, pg_bin=str(stubs))


@pytest.mark.parametrize("edit", [
    lambda m: m.update(kind="other"), lambda m: m.update(v=2), lambda m: m.update(root="/elsewhere"), lambda m: m.update(host="0.0.0.0"),
    lambda m: m.update(port=5432), lambda m: m.update(port="55432"), lambda m: m.update(port=True), lambda m: m.update(uid=os.getuid() + 1),
])
def test_marker_must_be_exactly_ours(root, stubs, edit):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    m = sr.read_marker(root)
    edit(m)
    (root / sr.MARKER_NAME).write_text(json.dumps(m))
    assert sr.read_marker(root) is None
    with pytest.raises(sr.LifecycleError):
        sr.start_cluster(root, pg_bin=str(stubs))


def test_root_must_be_private_unsymlinked_and_absolute(short_base, stubs):
    real = short_base
    loose = real / "loose"
    loose.mkdir(mode=0o755)
    os.chmod(loose, 0o755)
    with pytest.raises(sr.LifecycleError, match="chmod 700"):
        sr.init_cluster(loose, port=_free_port(), pg_bin=str(stubs))
    target = real / "target"
    target.mkdir(mode=0o700)
    link = real / "link"
    link.symlink_to(target)
    with pytest.raises(sr.LifecycleError, match="symlink"):
        sr.init_cluster(link, port=_free_port(), pg_bin=str(stubs))
    with pytest.raises(sr.LifecycleError, match="absolute"):
        sr.init_cluster("relative/dir", port=_free_port(), pg_bin=str(stubs))
    with pytest.raises(sr.LifecycleError, match="normalised"):
        sr.init_cluster(str(real / "a" / ".." / "b"), port=_free_port(), pg_bin=str(stubs))


def test_missing_binary_is_a_refusal_not_a_crash(root, tmp_path):
    with pytest.raises(sr.LifecycleError, match="not found"):
        sr.init_cluster(root, port=_free_port(), pg_bin=str(tmp_path / "nope"))


def _patch_running(monkeypatch, root, state):
    data = root / "pg"
    monkeypatch.setattr(sr, "_proc_command", {"running": lambda pid: f"/opt/pg/bin/postgres -D {data} -p 1",
                                              "foreign": lambda pid: "/usr/sbin/cron -f", "gone": lambda pid: "",
                                              "unknown": lambda pid: None}[state])


def test_start_passes_loopback_and_socket_overrides_under_env_i(root, stubs, monkeypatch):
    monkeypatch.setenv("PGHOST", "prod.example.invalid")
    monkeypatch.setenv("DATABASE_URL", "postgresql://x@prod.example.invalid/db")
    monkeypatch.setenv("PGPASSWORD", "secret-should-never-reach-a-child")
    port = _free_port()
    sr.init_cluster(root, port=port, pg_bin=str(stubs))
    monkeypatch.setattr(sr, "_proc_command", lambda pid: "")           # nothing running before the start
    assert sr.start_cluster(root, pg_bin=str(stubs))["result"] == "started"
    calls = _calls(stubs)
    assert f"-c listen_addresses=127.0.0.1 -p {port} -c unix_socket_directories={root}/sock -c unix_socket_permissions=0700" in calls
    for leaked in ("PGHOST", "DATABASE_URL", "PGPASSWORD", "prod.example.invalid", "secret-should-never"):
        assert leaked not in calls, f"{leaked} reached a child process"
    assert "PGPASSFILE=" in calls and "HOME=" in calls


@pytest.mark.parametrize("line", ["listen_addresses = '*'", "listen_addresses = '0.0.0.0'", "listen_addresses = ''",
                                  "listen_addresses = 'localhost'", "listen_addresses = '127.0.0.1,10.0.0.5'", "include = 'x.conf'",
                                  "include_dir = 'conf.d'", "include_if_exists = 'x'"])
def test_start_refuses_a_config_that_could_listen_beyond_loopback(root, stubs, monkeypatch, line):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    with open(root / "pg" / "postgresql.conf", "a") as f:
        f.write(f"\n{line}\n")
    monkeypatch.setattr(sr, "_proc_command", lambda pid: "")
    with pytest.raises(sr.LifecycleError, match="refusing"):
        sr.start_cluster(root, pg_bin=str(stubs))
    assert "pg_ctl" not in _calls(stubs)


def test_start_refuses_a_listen_addresses_set_through_alter_system(root, stubs, monkeypatch):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    (root / "pg" / "postgresql.auto.conf").write_text("listen_addresses = '*'\n")
    with pytest.raises(sr.LifecycleError, match="listen_addresses"):
        sr.start_cluster(root, pg_bin=str(stubs))


@pytest.mark.parametrize("rule", ["host all all 0.0.0.0/0 trust", "host all all ::1/128 trust", "host all all 10.0.0.0/8 md5",
                                  "hostssl all all 192.168.0.0/16 scram-sha-256", "host all all all trust", "include_dir hba.d", "host all all"])
def test_start_refuses_a_hba_rule_beyond_127_0_0_1(root, stubs, rule):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    with open(root / "pg" / "pg_hba.conf", "a") as f:
        f.write(rule + "\n")
    with pytest.raises(sr.LifecycleError, match="pg_hba"):
        sr.start_cluster(root, pg_bin=str(stubs))


def test_start_refuses_a_port_held_by_someone_else(root, stubs, monkeypatch):
    port = _free_port()
    sr.init_cluster(root, port=port, pg_bin=str(stubs))
    monkeypatch.setattr(sr, "_proc_command", lambda pid: "")
    with socket.socket() as s:
        s.bind(("127.0.0.1", port))
        s.listen(1)
        with pytest.raises(sr.LifecycleError, match="in use"):
            sr.start_cluster(root, pg_bin=str(stubs))
    assert "pg_ctl" not in _calls(stubs)


def test_start_refuses_to_start_over_a_foreign_or_unknown_pid_file(root, stubs, monkeypatch):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    (root / "pg" / "postmaster.pid").write_text("999\n")
    for state in ("foreign", "unknown"):
        _patch_running(monkeypatch, root, state)
        with pytest.raises(sr.LifecycleError, match=state):
            sr.start_cluster(root, pg_bin=str(stubs))
    assert "pg_ctl" not in _calls(stubs)


def test_status_reads_process_identity_token_wise(root, stubs, monkeypatch):
    real_ps = sr._proc_command                                           # before any patch
    assert sr.status_cluster(root)["state"] == "not_initialised"
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    assert sr.status_cluster(root)["state"] == "stopped"                 # no pid file
    (root / "pg" / "postmaster.pid").write_text("999\n")
    for state, want in (("running", "running"), ("foreign", "foreign"), ("gone", "stopped"), ("unknown", "unknown")):
        _patch_running(monkeypatch, root, state)
        assert sr.status_cluster(root)["state"] == want
    # a command line that merely CONTAINS the data dir is not a postmaster for it
    monkeypatch.setattr(sr, "_proc_command", lambda pid: f"/bin/vim {root}/pg/postgresql.conf")
    assert sr.status_cluster(root)["state"] == "foreign"
    monkeypatch.setattr(sr, "_proc_command", lambda pid: f"/opt/pg/bin/postgres -D {root}/pg_other -p 1")
    assert sr.status_cluster(root)["state"] == "foreign"
    for bad in ("1", "0", "-5", str(2**40), "abc"):
        (root / "pg" / "postmaster.pid").write_text(bad + "\n")
        assert sr.status_cluster(root)["state"] in ("foreign", "stopped")
    # the real `ps` answers for our own pid and for a pid that cannot exist
    assert isinstance(real_ps(os.getpid()), str) and real_ps(os.getpid())
    assert real_ps(2**22 - 3) in ("", None)


def test_stop_only_signals_a_verified_postmaster(root, stubs, monkeypatch):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    (root / "pg" / "postmaster.pid").write_text("4242\n")
    _patch_running(monkeypatch, root, "foreign")
    with pytest.raises(sr.LifecycleError, match="refusing to signal"):
        sr.stop_cluster(root, pg_bin=str(stubs))
    assert "pg_ctl" not in _calls(stubs)
    _patch_running(monkeypatch, root, "running")
    assert sr.stop_cluster(root, pg_bin=str(stubs))["result"] in ("stopped", "not_running")
    assert "stop" in _calls(stubs)


def test_a_held_lock_blocks_every_mutating_action(root, stubs):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    lay = sr._Layout(root)
    with sr._locked(lay):
        for action in (lambda: sr.start_cluster(root, pg_bin=str(stubs)), lambda: sr.stop_cluster(root, pg_bin=str(stubs)),
                       lambda: sr.init_cluster(root, port=sr.read_marker(root)["port"], pg_bin=str(stubs)),
                       lambda: sr.reap_cluster(root, pg_bin=str(stubs)), lambda: sr.adopt_cluster(root)):
            with pytest.raises(sr.LifecycleError, match="lock"):
                action()
    # a SECOND process really cannot take it while we hold it, and can once we let go
    code = "import sys; sys.path.insert(0, %r); import suvarna_rehearsal as s; s._locked(s._Layout(%r)).__enter__()" % (str(GOV), str(root))
    with sr._locked(lay):
        assert subprocess.run([sys.executable, "-c", code], capture_output=True).returncode != 0
    assert subprocess.run([sys.executable, "-c", code], capture_output=True).returncode == 0


def test_reap_needs_a_marker_and_an_exact_confirmation_and_never_follows_a_symlink(root, stubs, monkeypatch, tmp_path):
    port = _free_port()
    sr.init_cluster(root, port=port, pg_bin=str(stubs))
    monkeypatch.setattr(sr, "_proc_command", lambda pid: "")
    with pytest.raises(sr.LifecycleError, match="--confirm"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True)
    with pytest.raises(sr.LifecycleError, match="--confirm"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root) + "/")
    assert (root / "pg" / "PG_VERSION").exists()
    assert sr.reap_cluster(root, pg_bin=str(stubs))["removed"] == []      # stop only: the data dir stays
    assert (root / "pg").exists()
    out = sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert str(root / "pg") in out["removed"] and not (root / "pg").exists()
    assert (root / sr.MARKER_NAME).exists() and (root / sr.LOCK_NAME).exists()    # root, marker, lock are never removed
    # a data dir that is a symlink to somebody else's directory is never deleted
    victim = pathlib.Path(os.path.realpath(tmp_path)) / "victim"
    victim.mkdir()
    (victim / "keep").write_text("x")
    (victim / "PG_VERSION").write_text("15")
    (root / "pg").symlink_to(victim)
    with pytest.raises(sr.LifecycleError, match="symlink"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert (victim / "keep").exists()


def test_reap_refuses_an_unmarked_root(root, stubs):
    root.mkdir(parents=True)
    os.chmod(root, 0o700)
    (root / "pg").mkdir()
    (root / "pg" / "PG_VERSION").write_text("15")
    with pytest.raises(sr.LifecycleError, match="no valid ownership marker"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert (root / "pg" / "PG_VERSION").exists()


def test_reap_refuses_while_the_cluster_is_alive(root, stubs, monkeypatch):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    (root / "pg" / "postmaster.pid").write_text("4242\n")
    _patch_running(monkeypatch, root, "unknown")
    with pytest.raises(sr.LifecycleError):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert (root / "pg").exists()


def test_adopt_marks_a_phase1_cluster_only_if_it_is_loopback_and_on_the_port(root):
    (root / "pg").mkdir(parents=True)
    os.chmod(root, 0o700)
    (root / "pg" / "PG_VERSION").write_text("15")
    (root / "pg" / "postgresql.conf").write_text("listen_addresses = '127.0.0.1'\nport = 55432\n")
    (root / "pg" / "pg_hba.conf").write_text("local all all trust\nhost all all 127.0.0.1/32 trust\n")
    assert sr.adopt_cluster(root)["result"] == "marked" and sr.read_marker(root)["port"] == 55432
    assert sr.adopt_cluster(root)["result"] == "already_marked"
    (root / sr.MARKER_NAME).unlink()
    (root / "pg" / "pg_hba.conf").write_text("host all all 0.0.0.0/0 trust\n")
    with pytest.raises(sr.LifecycleError):
        sr.adopt_cluster(root)
    (root / "pg" / "pg_hba.conf").write_text("host all all 127.0.0.1/32 trust\n")
    (root / "pg" / "postgresql.conf").write_text("listen_addresses = '127.0.0.1'\nport = 55433\n")
    with pytest.raises(sr.LifecycleError, match="port"):
        sr.adopt_cluster(root)
    assert not (root / sr.MARKER_NAME).exists()


def test_cluster_cli_refuses_with_exit_2(root, stubs, capsys):
    rc = sr.main(["cluster", "start", "--root", str(root), "--pg-bin", str(stubs)])
    assert rc == 2 and "REFUSED" in capsys.readouterr().err


@pytest.mark.parametrize("line", ["LISTEN_ADDRESSES = '*'", "Listen_Addresses '*'", "listen_addresses '0.0.0.0'", "listen_addresses=*",
                                  "listen_addresses = *  # all", "listen_addresses = \"10.0.0.5\"", "INCLUDE 'x.conf'", "Include_Dir 'c'",
                                  "include_if_exists 'x'", "hba_file = '/etc/x'", "HBA_FILE '/x'"])
def test_loopback_config_check_is_case_insensitive_with_optional_equals(root, stubs, line):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    with open(root / "pg" / "postgresql.conf", "a") as f:
        f.write(f"\n{line}\n")
    with pytest.raises(sr.LifecycleError, match="refusing"):
        sr.check_loopback_config(root / "pg")


@pytest.mark.parametrize("line", ["listen_addresses = '127.0.0.1'", "LISTEN_ADDRESSES '127.0.0.1'", "listen_addresses=127.0.0.1",
                                  "listen_addresses = \"127.0.0.1\"  # only loopback", "#listen_addresses = '*'", "# include 'x'"])
def test_loopback_config_check_accepts_the_loopback_spellings(tmp_path, line):
    d = tmp_path / "d"
    d.mkdir()
    (d / "postgresql.conf").write_text(line + "\n")
    (d / "pg_hba.conf").write_text("local all all trust\nhost all all 127.0.0.1/32 trust\n")
    assert sr.check_loopback_config(d) is None


@pytest.mark.parametrize("rule", ["HOST all all 0.0.0.0/0 trust", "Hostssl all all 10.0.0.0/8 md5", "HOSTNOSSL all all ::1/128 trust"])
def test_hba_uppercase_type_keywords_are_refused(tmp_path, rule):
    d = tmp_path / "d"
    d.mkdir()
    (d / "postgresql.conf").write_text("listen_addresses = '127.0.0.1'\n")
    (d / "pg_hba.conf").write_text(rule + "\n")
    with pytest.raises(sr.LifecycleError, match="pg_hba"):
        sr.check_loopback_config(d)


def test_adopt_validates_the_port_before_writing_any_marker(root):
    (root / "pg").mkdir(parents=True)
    os.chmod(root, 0o700)
    (root / "pg" / "PG_VERSION").write_text("15")
    (root / "pg" / "postgresql.conf").write_text("listen_addresses = '127.0.0.1'\nport = 5432\n")
    (root / "pg" / "pg_hba.conf").write_text("host all all 127.0.0.1/32 trust\n")
    for bad in (5432, 6432, 80, True, "55432"):
        with pytest.raises(sr.LifecycleError, match="not allowed"):
            sr.adopt_cluster(root, port=bad)
        assert not (root / sr.MARKER_NAME).exists()


def test_reap_remove_data_is_pinned_to_the_rehearsal_root_and_an_initialised_data_dir(root, stubs, monkeypatch):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    monkeypatch.setattr(sr, "_proc_command", lambda pid: "")
    monkeypatch.setattr(sr, "DEFAULT_ROOT", "/Users/Dev/suvarna/not-this-root")
    with pytest.raises(sr.LifecycleError, match="only ever deletes under the rehearsal root"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert (root / "pg" / "PG_VERSION").exists()
    monkeypatch.setattr(sr, "DEFAULT_ROOT", str(root))
    (root / "pg" / "PG_VERSION").unlink()
    with pytest.raises(sr.LifecycleError, match="PG_VERSION"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert (root / "pg").exists()


def test_reap_refuses_to_delete_while_the_postmaster_is_still_alive_after_the_stop(root, stubs, monkeypatch):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    (stubs / "pg_ctl").write_text("#!/bin/bash\nexit 0\n")             # a pg_ctl whose stop does nothing
    (root / "pg" / "postmaster.pid").write_text("4242\n")
    _patch_running(monkeypatch, root, "running")
    with pytest.raises(sr.LifecycleError, match="still alive"):
        sr.reap_cluster(root, pg_bin=str(stubs), remove_data=True, confirm=str(root))
    assert (root / "pg" / "PG_VERSION").exists()


def test_start_refuses_a_data_dir_that_is_a_symlink(root, stubs, monkeypatch, short_base):
    sr.init_cluster(root, port=_free_port(), pg_bin=str(stubs))
    monkeypatch.setattr(sr, "_proc_command", lambda pid: "")
    os.rename(root / "pg", short_base / "elsewhere")
    (root / "pg").symlink_to(short_base / "elsewhere")
    with pytest.raises(sr.LifecycleError, match="symlink"):
        sr.start_cluster(root, pg_bin=str(stubs))
    assert "pg_ctl" not in _calls(stubs)


def test_git_env_is_scrubbed_of_the_callers_environment(monkeypatch):
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_SSH_COMMAND", "HOME", "XDG_CONFIG_HOME", "LANG", "SOME_SECRET"):
        monkeypatch.setenv(k, "x")
    env = sr._git_env()
    assert not {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_SSH_COMMAND", "XDG_CONFIG_HOME", "LANG", "SOME_SECRET"} & set(env)
    assert env["HOME"] == "/nonexistent" and env["GIT_TERMINAL_PROMPT"] == "0" and env["GIT_CONFIG_GLOBAL"] == os.devnull


# ═════════════════════════ 3. evidence: closed schema, derived results ═════════════════════════

def test_every_catalog_case_has_a_judge_and_a_detector_that_can_fail():
    assert set(sr.JUDGES) == set(sr.CASE_CATALOG) and len(sr.REQUIRED_CASES) == 7
    for cid in sr.CASE_CATALOG:
        assert sr.judge_case(cid, good_measured(cid)) == ("PASS", [])
        assert sr.judge_case(cid, {})[0] == "FAIL"                        # an empty measurement is never a pass
        extra = dict(good_measured(cid), surplus=1)
        assert sr.judge_case(cid, extra)[0] == "FAIL"                     # the measured schema is closed too
        spec = sr.CASE_CATALOG[cid]
        assert spec["detector"] and spec["claim"]


GOOD_ENTRY = {"host": "127.0.0.1", "port": 40001, "database": "suvarna_disposable", "policy": "disposable", "data_directory": "/tmp/x/data", "verified": True}

BREAKS = {
    "idempotent_rebuild_fingerprint_unchanged": [
        ("fingerprint_after_rebuild", H2), ("fingerprint_after_material_change", H), ("other_chart_after", H), ("rows_after", 39),
        ("rows_before", 0), ("volatile_columns_changed", False), ("fingerprint_before", "short")],
    "family_dispatch_refused": [
        ("exit_code", 0), ("exit_code", 4.0), ("exit_code", True), ("refusal_codes", []), ("connect_calls", 1), ("connect_calls", False),
        ("connect_calls", 0.0), ("dispatch_calls", 1), ("dispatch_calls", False), ("intersecting_assets", []),
        ("refused_assets", ["ka_x"]), ("refused_via", ["family_set"]), ("refused_via", ["name_pattern"]), ("refused_via", []),
        ("refusal_codes", "FAMILY_ASSET"),
        ("control_refusal_codes", ["FAMILY_ASSET"]), ("control_refusal_codes", ["SPLITS_FAMILY"]), ("missing_file_committing_codes", [])],
    "hold_refuses_dispatch": [
        ("blocked_with_hold", False), ("blocked_without_hold", True), ("non_dispatch_blocked_with_hold", True),
        ("command", "git status"), ("hold_guard_sha256", "x")],
    "canary_triggers_reversal": [
        ("baseline_canary_passed", False), ("injected_difference_failed_canary", False), ("reversal_triggered", False),
        ("fingerprint_post_reversal", H2)],
    "f3_proof": [
        ("msr_replace_refused", True), ("dangling_after_change", 0), ("dangling_after_downstream_rebuild", 1),
        ("dangling_after_downstream_rebuild", False), ("dangling_after_downstream_rebuild", 0.0), ("dangling_after_change", True),
        ("downstream_waves", []),
        ("referencing_tables_populated", {f"t{i}": 3 for i in range(6)}), ("referencing_tables_populated", {**{f"t{i}": 3 for i in range(6)}, "t6": 0}),
        ("fk_state", None), ("referencing_rows_restored", {f"t{i}": True for i in range(6)}),
        ("referencing_rows_restored", {**{f"t{i}": True for i in range(6)}, "t6": False}),
        ("referencing_rows_restored", {f"u{i}": True for i in range(7)})],
    "find_fix_rebuild_certify": [
        ("stale_after_fix_detected", False), ("fingerprint_after_rebuild", H), ("certificate_current_after_certify", False),
        ("certificate_detector_not_none", False), ("orchestrator_commit", "2" * 40), ("census_run_id", "")],
    "no_production_write": [
        ("opened", []), ("probe_refused_without_socket", False), ("refused_count", "2"),
        ("opened", [{**GOOD_ENTRY, "host": "10.0.0.5"}]),                                     # not loopback (port itself allowed)
        ("opened", [{**GOOD_ENTRY, "host": "10.0.0.5", "port": 5432}]),
        ("opened", [{**GOOD_ENTRY, "port": 5432}]), ("opened", [{**GOOD_ENTRY, "policy": "nope"}]),
        ("opened", [{**GOOD_ENTRY, "verified": False}]), ("opened", [{**GOOD_ENTRY, "data_directory": ""}]),
        ("opened", [{**GOOD_ENTRY, "port": 15432, "database": "anything"}]),                  # disposable policy, wrong database
        ("opened", [{**GOOD_ENTRY, "port": 55432}]),                                           # disposable policy on the rehearsal port
        ("opened", [{**GOOD_ENTRY, "policy": "rehearsal"}]),                                   # rehearsal policy on a random port
        ("opened", [{**GOOD_ENTRY, "policy": "rehearsal", "port": 55432, "database": "suvarna_disposable"}]),
        ("opened", [{**GOOD_ENTRY, "policy": "rehearsal", "port": 55432, "database": "rehearsal", "data_directory": "/elsewhere/pg"}]),
        ("opened", [{k: v for k, v in GOOD_ENTRY.items() if k != "verified"}]), ("opened", [{**GOOD_ENTRY, "extra": 1}]),
        ("opened", ["not an object"])],
}


@pytest.mark.parametrize("cid,key,value", [(c, k, v) for c, items in BREAKS.items() for k, v in items])
def test_each_judge_fails_on_each_broken_measurement(cid, key, value):
    m = good_measured(cid)
    m[key] = value
    result, problems = sr.judge_case(cid, m)
    assert result == "FAIL" and problems, f"{cid}: breaking {key} still judged PASS"


def test_a_hand_edited_pass_over_failing_measurements_is_rejected():
    doc = self_test_doc()
    case = next(c for c in doc["cases"] if c["id"] == "idempotent_rebuild_fingerprint_unchanged")
    case["measured"]["fingerprint_after_rebuild"] = H2                   # the measurement now says "fingerprint moved"
    assert case["result"] == "PASS"
    problems = sr.validate_evidence(doc)
    assert any("recorded result PASS but the recorded measurements judge FAIL" in p for p in problems)


def test_case_result_derives_fail_from_the_measurements_and_cannot_be_forced():
    m = good_measured("hold_refuses_dispatch")
    m["blocked_with_hold"] = False
    assert sr.case_result("hold_refuses_dispatch", measured=m, basis="synthetic_fixture")["result"] == "FAIL"
    assert sr.derive_result("self_test", sr.derive_summary(self_test_doc(measured={"hold_refuses_dispatch": m})["cases"])) == "FAIL"


def test_a_valid_self_test_document_validates_and_reads_unmeasured_never_pass():
    doc = self_test_doc()
    assert sr.validate_evidence(doc) == []
    assert doc["result"] == "UNMEASURED" and doc["summary"] == {"required": 7, "pass": 4, "fail": 0, "unmeasured": 3}
    # even if every required case were PASS, a self_test document can not read PASS
    assert sr.derive_result("self_test", {"required": 7, "pass": 7, "fail": 0, "unmeasured": 0}) == "UNMEASURED"
    doc["result"] = "PASS"
    assert any("differs from the derived" in p for p in sr.validate_evidence(doc))


def test_a_rehearsal_document_is_the_only_way_to_read_pass():
    doc = rehearsal_doc()
    assert sr.validate_evidence(doc) == [] and doc["result"] == "PASS" and doc["summary"]["pass"] == 7
    one_unmeasured = copy.deepcopy(doc)
    i = next(n for n, c in enumerate(one_unmeasured["cases"]) if c["id"] == "canary_triggers_reversal")
    one_unmeasured["cases"][i] = sr.unmeasured_case("canary_triggers_reversal", "NEEDS_CANARY_REVERSAL_MECHANISM")
    one_unmeasured["summary"] = sr.derive_summary(one_unmeasured["cases"])
    one_unmeasured["result"] = sr.derive_result("rehearsal", one_unmeasured["summary"])
    assert one_unmeasured["result"] == "UNMEASURED" and sr.validate_evidence(one_unmeasured) == []
    forged = copy.deepcopy(one_unmeasured)
    forged["result"] = "PASS"
    assert any("derived" in p for p in sr.validate_evidence(forged))


def _extra_pointers(doc, ev):
    """The record files first, then one extra pointer file per case (index 1 of each evidence list)."""
    sr.write_measured_records(doc, ev)
    for c in doc["cases"]:
        f = ev / "E5.6" / f"{c['id']}.txt"
        f.write_text(c["id"])
        c["evidence"][1] = {"path": f"E5.6/{c['id']}.txt", "sha256": sr.sha256_file(f)}


def test_the_detector_reads_the_written_rehearsal_file_as_done(tmp_path):
    """The plan item's detector: result == PASS and `cases` present and non-null (suvarna_tracker.detectors.d_evidence_verified)."""
    doc = rehearsal_doc()
    ev = tmp_path / "evidence"
    (ev / "E5.6").mkdir(parents=True)
    _extra_pointers(doc, ev)
    sr.write_evidence(doc, ev / "E5.6" / "REHEARSAL.json", evidence_root=ev)
    got = json.loads((ev / "E5.6" / "REHEARSAL.json").read_text())
    assert got["result"] == "PASS" and got["cases"] is not None                # expect={"result":"PASS"}, required=["cases"]
    assert sr.main(["validate", str(ev / "E5.6" / "REHEARSAL.json"), "--evidence-root", str(ev)]) == 0


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d.update(extra=1), "closed schema"), (lambda d: d.pop("cases"), "closed schema"),
    (lambda d: d.update(schema="x"), "schema/item"), (lambda d: d.update(item="E5.7"), "schema/item"),
    (lambda d: d.update(mode="prod"), "mode"), (lambda d: d.update(required_cases=[]), "required_cases"),
    (lambda d: d["generated_by"].update(tool="other.py"), "generated_by"), (lambda d: d["generated_by"].update(tool_sha256="x"), "generated_by"),
    (lambda d: d["cases"].pop(), "absent"), (lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])), "twice"),
    (lambda d: d["summary"].update(**{"pass": 99}), "summary"),
    (lambda d: d["environment"].update(extra=1), "environment"),
    (lambda d: d["environment"]["cluster"].update(host="10.0.0.5"), "cluster"),
    (lambda d: d["environment"]["cluster"].update(port=5432), "cluster"),
    (lambda d: d["environment"]["cluster"].update(kind="rehearsal"), "disposable"),
    (lambda d: d.update(orchestrator_commit=SHA40), "no orchestrator_commit"),
    (lambda d: d.update(commit="not-a-sha"), "40-hex"),
])
def test_self_test_document_closed_schema_refusals(mutate, needle):
    doc = self_test_doc()
    mutate(doc)
    problems = sr.validate_evidence(doc)
    assert problems and any(needle in p for p in problems), problems


@pytest.mark.parametrize("mutate,needle", [
    (lambda c: c.update(extra=1), "closed case schema"), (lambda c: c.update(title="renamed"), "catalog"),
    (lambda c: c["detector"].update(claim="a weaker claim"), "catalog"), (lambda c: c.update(result="MAYBE"), "PASS/FAIL/UNMEASURED"),
    (lambda c: c.update(basis="prod"), "basis"), (lambda c: c.update(measured={}), "non-empty"),
    (lambda c: c.update(fingerprints={"a": "x"}), "sha256"), (lambda c: c.update(evidence=[{"path": "/abs", "sha256": H}]), "evidence"),
    (lambda c: c.update(evidence=[{"path": "../x", "sha256": H}]), "evidence"), (lambda c: c.update(unmeasured_reason="NEEDS_X_Y_Z"), "unmeasured_reason"),
    (lambda c: c.update(basis="rehearsal_db"), "self_test document cannot claim"),
])
def test_case_level_closed_schema_refusals(mutate, needle):
    doc = self_test_doc()
    mutate(next(c for c in doc["cases"] if c["id"] == "idempotent_rebuild_fingerprint_unchanged"))
    problems = sr.validate_evidence(doc)
    assert any(needle in p for p in problems), problems


@pytest.mark.parametrize("mutate,needle", [
    (lambda c: c.update(result="PASS", measured={"a": 1}), "unmeasured_reason"),
    (lambda c: c.update(unmeasured_reason="whatever"), "NEEDS_"),
    (lambda c: c.update(unmeasured_reason=None), "NEEDS_"),
    (lambda c: c.update(measured={"x": 1}), "no measurement"),
    (lambda c: c.update(basis="synthetic_fixture"), "no measurement"),
    (lambda c: c.update(evidence=[{"path": "a", "sha256": H}]), "no measurement"),
])
def test_an_unmeasured_case_is_only_ever_unmeasured(mutate, needle):
    doc = self_test_doc()
    case = next(c for c in doc["cases"] if c["id"] == "f3_proof")
    mutate(case)
    problems = sr.validate_evidence(doc)
    assert problems and any(needle in p for p in problems), problems


def test_unmeasured_case_needs_a_NEEDS_reason():
    for bad in ("", "done", "needs_x", "NEEDS_", "NEEDS_ lower", "PASS"):
        with pytest.raises(sr.RehearsalError):
            sr.unmeasured_case("f3_proof", bad)
    assert sr.unmeasured_case("f3_proof", "NEEDS_REHEARSAL_SCHEMA_WITH_1036")["result"] == "UNMEASURED"


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d.update(commit="2" * 40), "commit must equal"),
    (lambda d: d.update(job_image_commit="2" * 40), "orchestrator_commit must equal job_image_commit"),
    (lambda d: d.update(job_image_commit=None), "40-hex job_image_commit"),
    (lambda d: d["environment"].update(schema_replay=None), "schema_replay"),
    (lambda d: d["environment"].update(seed=None), "seed"),
    (lambda d: d["environment"]["cluster"].update(port=55999), "rehearsal cluster"),
    (lambda d: d["environment"]["cluster"].update(data_directory="/tmp/x"), "rehearsal cluster"),
    (lambda d: d["cases"][0].update(basis="synthetic_fixture"), "rehearsal_db"),
    (lambda d: d["cases"][0].update(evidence=[]), "measurement-record pointer"),
])
def test_rehearsal_document_requirements(mutate, needle):
    doc = rehearsal_doc()
    mutate(doc)
    doc["summary"] = sr.derive_summary(doc["cases"])
    doc["result"] = sr.derive_result("rehearsal", doc["summary"])
    problems = sr.validate_evidence(doc)
    assert problems and any(needle in p for p in problems), problems


def test_certify_case_evidence_commit_must_be_the_document_commit():
    doc = rehearsal_doc()
    case = next(c for c in doc["cases"] if c["id"] == "find_fix_rebuild_certify")
    case["measured"]["evidence_commit"] = "3" * 40
    case["measured"]["orchestrator_commit"] = "3" * 40
    assert any("evidence_commit differs" in p for p in sr.validate_evidence(doc))


def test_writer_refuses_invalid_self_test_at_the_detector_path_and_unverified_pointers(tmp_path):
    bad = self_test_doc()
    bad["result"] = "PASS"
    with pytest.raises(sr.RehearsalError, match="invalid"):
        sr.write_evidence(bad, tmp_path / "x.json")
    assert not (tmp_path / "x.json").exists()
    good = self_test_doc()
    with pytest.raises(sr.RehearsalError, match="detector's path"):
        sr.write_evidence(good, tmp_path / "evidence" / "E5.6" / "REHEARSAL.json")
    assert not (tmp_path / "evidence").exists()
    for spelling in ("evidence/E5.6/rehearsal.json", "EVIDENCE/e5.6/REHEARSAL.JSON", "x/Rehearsal.Json", "elsewhere/E5.6/REHEARSAL.json"):
        with pytest.raises(sr.RehearsalError, match="detector's path"):
            sr.write_evidence(good, tmp_path / spelling)
    (tmp_path / "real" / "E5.6").mkdir(parents=True)
    (tmp_path / "link.json").symlink_to(tmp_path / "real" / "E5.6" / "REHEARSAL.json")
    with pytest.raises(sr.RehearsalError, match="detector's path"):
        sr.write_evidence(good, tmp_path / "link.json")
    sr.write_evidence(good, tmp_path / "elsewhere" / "selftest.json")
    reh = rehearsal_doc()
    with pytest.raises(sr.RehearsalError, match="evidence-root"):
        sr.write_evidence(reh, tmp_path / "r.json")
    with pytest.raises(sr.RehearsalError, match="do not verify"):
        sr.write_evidence(reh, tmp_path / "r.json", evidence_root=tmp_path)           # the pointed-at files do not exist
    assert not (tmp_path / "r.json").exists()


def test_pointer_verification_catches_missing_changed_and_symlinked_files(tmp_path):
    doc = rehearsal_doc()
    ev = tmp_path
    (ev / "E5.6").mkdir()
    _extra_pointers(doc, ev)
    assert sr.check_pointers(doc, ev) == []
    (ev / "E5.6" / "f3_proof.txt").write_text("tampered")
    assert any("does not match" in p for p in sr.check_pointers(doc, ev))
    (ev / "E5.6" / "hold_refuses_dispatch.txt").unlink()
    assert any("missing" in p for p in sr.check_pointers(doc, ev))
    (ev / "E5.6" / "no_production_write.txt").unlink()
    (ev / "E5.6" / "no_production_write.txt").symlink_to(ev / "E5.6" / "f3_proof.txt")
    assert any("symlink" in p for p in sr.check_pointers(doc, ev))
    rec = ev / "E5.6" / sr.measured_record_path("f3_proof").split("/")[-1]
    rec.write_text(rec.read_text().replace('"dangling_after_change": 10', '"dangling_after_change": 11'))
    assert any("does not match" in p for p in sr.check_pointers(doc, ev))


def test_the_measurement_record_pointer_is_tied_to_the_measured_values():
    doc = rehearsal_doc()
    assert sr.validate_evidence(doc) == []
    case = next(c for c in doc["cases"] if c["id"] == "f3_proof")
    case["measured"]["dangling_after_change"] = 99                      # still judges PASS, but is no longer what was hashed
    assert sr.judge_case("f3_proof", case["measured"])[0] == "PASS"
    assert any("measurement-record pointer" in p for p in sr.validate_evidence(doc))
    doc = rehearsal_doc()
    case = next(c for c in doc["cases"] if c["id"] == "f3_proof")
    case["evidence"] = [e for e in case["evidence"] if not e["path"].endswith(".measured.json")]
    assert any("measurement-record pointer" in p for p in sr.validate_evidence(doc))


def test_the_record_file_must_contain_the_measured_values_not_merely_hash_right(tmp_path):
    doc = rehearsal_doc()
    (tmp_path / "E5.6").mkdir()
    _extra_pointers(doc, tmp_path)
    case = next(c for c in doc["cases"] if c["id"] == "f3_proof")
    other = {"case": "f3_proof", "measured": {"something": "else"}, "fingerprints": {}}
    text = json.dumps(other, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    (tmp_path / sr.measured_record_path("f3_proof")).write_text(text)
    case["evidence"][0] = {"path": sr.measured_record_path("f3_proof"), "sha256": sr.sha256_text(text)}
    assert any("does not contain this case's measured values" in p for p in sr.check_pointers(doc, tmp_path))


def test_evidence_bytes_are_deterministic_and_canonical(tmp_path):
    a, b = self_test_doc(), self_test_doc()
    ha = sr.write_evidence(a, tmp_path / "a.json")
    hb = sr.write_evidence(copy.deepcopy(b), tmp_path / "b.json")
    assert ha == hb and (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()
    text = (tmp_path / "a.json").read_text()
    assert text.endswith("\n") and json.loads(text) == a
    assert list(json.loads(text)) == sorted(json.loads(text))                    # sorted keys
    case_order = [c["id"] for c in a["cases"]]
    assert case_order == list(sr.CASE_CATALOG)                                    # catalog order, whatever the input order
    shuffled = self_test_doc()
    shuffled["cases"].reverse()
    rebuilt = sr.build_evidence(mode="self_test", commit=SHA40, cases=shuffled["cases"], environment=a["environment"])
    assert rebuilt == a


def test_validate_cli_exit_codes(tmp_path, capsys):
    good = tmp_path / "g.json"
    sr.write_evidence(self_test_doc(), good)
    assert sr.main(["validate", str(good)]) == 0
    bad = json.loads(good.read_text())
    bad["result"] = "PASS"
    (tmp_path / "b.json").write_text(json.dumps(bad))
    assert sr.main(["validate", str(tmp_path / "b.json")]) == 2
    reh = tmp_path / "r.json"
    reh.write_text(json.dumps(rehearsal_doc()))
    capsys.readouterr()
    assert sr.main(["validate", str(reh)]) == 2 and "evidence-root" in capsys.readouterr().out


def test_the_validator_refuses_malformed_documents_cleanly_and_never_raises(tmp_path, capsys):
    base = self_test_doc()

    def with_case(edit):
        d = copy.deepcopy(base)
        edit(d)
        return d
    certify_no_measured = rehearsal_doc()
    next(c for c in certify_no_measured["cases"] if c["id"] == "find_fix_rebuild_certify").pop("measured")
    bad = [None, 5, "x", [], {}, certify_no_measured,
           with_case(lambda d: d["cases"][0].update(id=["unhashable"])), with_case(lambda d: d["cases"][0].update(id={"a": 1})),
           with_case(lambda d: d["cases"].append(None)), with_case(lambda d: d["cases"].append(5)),
           with_case(lambda d: d.update(cases={"a": 1})), with_case(lambda d: d.update(cases=None)),
           with_case(lambda d: d["cases"][2].update(measured=[1, 2])), with_case(lambda d: d["cases"][2].update(measured="x")),
           with_case(lambda d: d["cases"][2].update(measured=None)), with_case(lambda d: d.update(environment=None)),
           with_case(lambda d: d.update(environment={"cluster": None, "schema_replay": None, "seed": None})),
           with_case(lambda d: d.update(summary=None)), with_case(lambda d: d.update(generated_by=None)),
           with_case(lambda d: d.update(mode=["rehearsal"])), with_case(lambda d: d.update(required_cases=None)),
           with_case(lambda d: d["cases"][0]["detector"].update(name=["x"]))]
    for doc in bad:
        problems = sr.validate_evidence(doc)
        assert isinstance(problems, list) and problems, doc
    rm = rehearsal_doc()
    next(c for c in rm["cases"] if c["id"] == "find_fix_rebuild_certify")["measured"] = [1]
    assert sr.validate_evidence(rm)
    for text, name in (("not json", "a.json"), ("[1, 2]", "b.json"), ("null", "c.json")):
        (tmp_path / name).write_text(text)
        assert sr.main(["validate", str(tmp_path / name)]) == 2
    assert sr.main(["validate", str(tmp_path / "missing.json")]) == 2
    assert sr.main(["validate-drill", str(tmp_path / "missing.json")]) == 2
    capsys.readouterr()


def test_the_tool_hash_in_the_document_must_be_the_repo_tools():
    doc = self_test_doc()
    assert doc["generated_by"]["tool_sha256"] == sr.tool_sha256() == sr.sha256_file(GOV / "suvarna_rehearsal.py")
    assert sr.validate_evidence(doc) == []
    forged = copy.deepcopy(doc)
    forged["generated_by"]["tool_sha256"] = H                                    # hex-shaped, but not this tool
    assert any("not the sha256 of the repo tool" in p for p in sr.validate_evidence(forged))
    assert sr.validate_evidence(forged, tool_sha=H) == []                          # the caller names the tool version it trusts
    assert sr.validate_evidence(doc, tool_sha=H)


def test_tool_hash_at_a_commit_reads_the_committed_file_or_none():
    head = subprocess.run(["git", "-C", str(GOV), "rev-parse", "HEAD"], capture_output=True, text=True, env=sr._git_env()).stdout.strip()
    assert sr.tool_sha256_at_commit(GOV, "not-a-sha") is None and sr.tool_sha256_at_commit(GOV, "0" * 40) is None
    at_head = sr.tool_sha256_at_commit(GOV, head)
    assert at_head is None or sr._h64(at_head)


def test_a_rehearsal_document_may_only_hold_rehearsal_policy_connections():
    doc = rehearsal_doc()
    case = next(c for c in doc["cases"] if c["id"] == "no_production_write")
    assert sr.validate_evidence(doc) == []
    forged_entry = {"host": "127.0.0.1", "port": 15432, "database": "anything", "policy": "disposable", "data_directory": "/x", "verified": True}
    case["measured"]["opened"] = [forged_entry]
    assert sr.judge_case("no_production_write", case["measured"])[0] == "FAIL"
    assert sr.validate_evidence(doc), "a rehearsal doc with a disposable-policy 'anything' endpoint must not validate"
    good_disposable = {**forged_entry, "database": "suvarna_disposable"}
    case["measured"]["opened"] = [good_disposable]
    assert sr.judge_case("no_production_write", case["measured"])[0] == "PASS"            # fine for a self-test...
    case["evidence"][0] = sr.measured_record_pointer(case)
    assert any("only contain rehearsal-policy connections" in p for p in sr.validate_evidence(doc))     # ...never for the rehearsal


def test_a_forged_but_tool_built_rehearsal_document_still_needs_matching_record_files(tmp_path):
    """The reviewer's case: a document built through case_result/build_evidence validates structurally, but cannot be written
    or validated against an evidence root that does not hold the matching measurement-record files."""
    doc = rehearsal_doc()
    assert sr.validate_evidence(doc) == []
    with pytest.raises(sr.RehearsalError, match="do not verify"):
        sr.write_evidence(doc, tmp_path / "out.json", evidence_root=tmp_path)


# ═════════════════════════ 4. E5.7: pre/post fingerprint comparison ═════════════════════════

def fp(n: int) -> str:
    return f"{n:064x}"


ASSETS = ["bg_a", "bg_b", "bg_c", "bg_d", "bg_e", "bg_f", "bg_g", "bg_h", "bg_i", "bg_j"]
DETAIL = "the muhurta lattice horizon was pinned at a different as-of date than production's run (see drill log)"


def env_(d: dict) -> dict:
    return sr.fingerprint_set(d)


def same_sets(n: int = 10) -> dict:
    return {a: fp(i + 1) for i, a in enumerate(ASSETS[:n])}


def cmp_(prod, reh, explained=None, **kw):
    kw.setdefault("expected_assets", ASSETS)
    kw.setdefault("commit", SHA40)
    return sr.compare_fingerprint_sets(prod if "definition" in prod else env_(prod), reh if "definition" in reh else env_(reh),
                                       explained, **kw)


def explain(code="rolling_horizon", n=0, decision="N-77"):
    e = {"reason_code": code, "detail": f"{DETAIL} [asset {n}]"}
    if decision:
        e["decision"] = decision
    return e


def test_compare_equal_sets_pass_and_embeds_everything():
    r = cmp_(same_sets(), same_sets())
    assert r["result"] == "PASS" and r["equal"] == ASSETS and r["differences"] == [] and r["commit"] == SHA40
    assert r["tool_sha256"] == sr.tool_sha256() and r["definition"] == sr.FINGERPRINT_DEFINITION
    assert r["production"]["fingerprints"] == same_sets() and r["rehearsal"]["fingerprints"] == same_sets()
    assert set(r["inputs"]) == {"production_sha256", "rehearsal_sha256", "explained_sha256"} and all(sr._h64(v) for v in r["inputs"].values())
    assert sr.validate_drill(r) == []


def test_compare_difference_needs_a_valid_explained_decided_reason():
    prod, reh = same_sets(), {**same_sets(), "bg_b": fp(99)}
    r = cmp_(prod, reh)
    assert r["result"] == "FAIL" and r["unexplained"] == ["bg_b"] and r["differences"][0]["kind"] == "fingerprint_differs"
    ok = cmp_(prod, reh, {"bg_b": explain()})
    assert ok["result"] == "PASS" and ok["differences"][0]["explained"]["decision"] == "N-77" and sr.validate_drill(ok) == []
    undecided = cmp_(prod, reh, {"bg_b": explain(decision=None)})
    assert undecided["result"] == "FAIL" and any("no decision id" in x for x in undecided["problems"])
    assert cmp_(prod, reh, {"bg_b": explain(decision=None)}, max_undecided_share=0.2)["result"] == "PASS"
    for bad in ({"reason_code": "because", "detail": DETAIL}, {"reason_code": "rolling_horizon", "detail": "x"},
                {"reason_code": "rolling_horizon", "detail": "  " + "x" * 10 + "  "}, {"reason_code": "rolling_horizon"},
                {**explain(), "extra": 1}, {**explain(), "decision": "SS-1"}, {**explain(), "decision": "n-5"}, "text", None, 7, [explain()],
                {"reason_code": "source_unavailable_offline", "detail": DETAIL + "!", "decision": "N-1"}):
        assert cmp_(prod, reh, {"bg_b": bad})["result"] == "FAIL", bad


def test_the_reviewers_wave_through_cases_now_fail():
    prod = same_sets()
    reh = {a: fp(1000 + i) for i, a in enumerate(ASSETS)}                    # all 10 differ
    boiler = {a: {"reason_code": "seeded_not_rebuilt", "detail": "x"} for a in ASSETS}
    assert cmp_(prod, reh, boiler)["result"] == "FAIL"                           # one-character detail
    same_long = {a: {"reason_code": "seeded_not_rebuilt", "detail": DETAIL, "decision": "N-1"} for a in ASSETS}
    r = cmp_(prod, reh, same_long)
    assert r["result"] == "FAIL" and sum("repeats" in x for x in r["problems"]) == 9          # an explanation is per asset
    distinct = {a: explain("seeded_not_rebuilt", i) for i, a in enumerate(ASSETS)}
    r = cmp_(prod, reh, distinct)
    assert r["result"] == "FAIL" and any("over the allowed share" in x for x in r["problems"])  # 10/10 assets differ: share cap
    assert cmp_(prod, reh, distinct, max_difference_share=1.0)["result"] == "PASS"             # only a deliberate override
    one = cmp_({"bg_a": fp(1)}, {"bg_a": fp(1)})                                                # one asset of ten compared
    assert one["result"] == "FAIL" and one["uncovered"] == ASSETS[1:]


def test_compare_coverage_unexpected_assets_and_kinds():
    full = same_sets()
    r = cmp_({**full, "bg_zzz": fp(5)}, {**full, "bg_zzz": fp(5)})
    assert r["result"] == "FAIL" and r["unexpected"] == ["bg_zzz"]
    miss = {k: v for k, v in full.items() if k != "bg_j"}
    r = cmp_(miss, full)
    assert r["differences"][0]["kind"] == "missing_in_production" and r["result"] == "FAIL"
    assert cmp_(miss, full, {"bg_j": explain("asset_new_at_commit", 1)})["result"] == "PASS"
    assert cmp_(miss, full, {"bg_j": explain("rolling_horizon", 1)})["result"] == "FAIL"          # code not valid for this kind
    r = cmp_(full, miss)
    assert r["differences"][0]["kind"] == "missing_in_rehearsal"
    assert cmp_(full, miss, {"bg_j": explain("source_unavailable_offline", 1)})["result"] == "PASS"
    assert cmp_(full, miss, {"bg_j": explain("asset_new_at_commit", 1)})["result"] == "FAIL"
    both_missing = cmp_(miss, miss)
    assert both_missing["result"] == "FAIL" and both_missing["uncovered"] == ["bg_j"]              # in neither set: never explainable
    diff = {**full, "bg_c": fp(77)}
    assert cmp_(full, diff, {"bg_c": explain("seeded_not_rebuilt", 2)})["result"] == "PASS"
    assert cmp_(full, diff, {"bg_c": explain("source_unavailable_offline", 2)})["result"] == "FAIL"
    stray = cmp_(full, full, {"bg_a": explain()})
    assert stray["result"] == "FAIL" and stray["explanations_without_difference"] == ["bg_a"]


def test_compare_refuses_malformed_inputs_instead_of_raising_type_errors():
    ok = env_(same_sets())
    for bad_expl in ([], "x", 5, [("bg_a", {})], set()):
        with pytest.raises(sr.RehearsalError, match="explained"):
            sr.compare_fingerprint_sets(ok, ok, bad_expl, expected_assets=ASSETS, commit=SHA40)
    for bad in ({"bg_a": fp(1)}, {"definition": "other/1", "fingerprints": {}}, {"definition": sr.FINGERPRINT_DEFINITION},
                {"definition": sr.FINGERPRINT_DEFINITION, "fingerprints": {"bg_a": "short"}},
                {"definition": sr.FINGERPRINT_DEFINITION, "fingerprints": {"Bad Id": fp(1)}},
                {"definition": sr.FINGERPRINT_DEFINITION, "fingerprints": [("bg_a", fp(1))]}, None, [], "x"):
        with pytest.raises(sr.RehearsalError):
            sr.compare_fingerprint_sets(bad, ok, expected_assets=ASSETS, commit=SHA40)
        with pytest.raises(sr.RehearsalError):
            sr.compare_fingerprint_sets(ok, bad, expected_assets=ASSETS, commit=SHA40)
    for bad_exp in (None, [], "bg_a", {"bg_a": 1}, ["bg_a", "bg_a"], ["Bad"], [1], b"x"):
        with pytest.raises(sr.RehearsalError, match="expected_assets"):
            sr.compare_fingerprint_sets(ok, ok, expected_assets=bad_exp, commit=SHA40)
    for bad_commit in (None, "abc", "G" * 40, 5):
        with pytest.raises(sr.RehearsalError, match="commit"):
            sr.compare_fingerprint_sets(ok, ok, expected_assets=ASSETS, commit=bad_commit)
    for share in (-0.1, 1.5, True, "0.2", None):
        with pytest.raises(sr.RehearsalError, match="share"):
            sr.compare_fingerprint_sets(ok, ok, expected_assets=ASSETS, commit=SHA40, max_difference_share=share)
        with pytest.raises(sr.RehearsalError, match="share"):
            sr.compare_fingerprint_sets(ok, ok, expected_assets=ASSETS, commit=SHA40, max_undecided_share=share)


def test_the_drill_document_validates_and_every_edit_is_caught():
    prod, reh = same_sets(), {**same_sets(), "bg_b": fp(99)}
    r = cmp_(prod, reh, {"bg_b": explain()})
    assert sr.validate_drill(r) == []
    for edit in (lambda d: d.update(result="FAIL"), lambda d: d["rehearsal"]["fingerprints"].update(bg_b=fp(1)),
                 lambda d: d["production"]["fingerprints"].update(bg_a=fp(500)), lambda d: d["explained_input"].clear(),
                 lambda d: d.update(tool_sha256=H), lambda d: d.update(extra=1),
                 lambda d: d.pop("inputs"), lambda d: d["inputs"].update(production_sha256=H),
                 lambda d: d["limits"].update(max_difference_share=1.0), lambda d: d["limits"].update(min_detail_chars=1),
                 lambda d: d.update(expected_assets=ASSETS[:5]), lambda d: d.update(definition="x"),
                 lambda d: d.update(differences=[]), lambda d: d.update(problems=["made up"]), lambda d: d.update(limits=None),
                 lambda d: d.update(production=None), lambda d: d.update(explained_input=[1])):
        d = copy.deepcopy(r)
        edit(d)
        assert sr.validate_drill(d), edit
    for junk in (None, 5, "x", [], {}):
        assert sr.validate_drill(junk)
    assert sr.validate_drill(r, tool_sha=H)                                                    # not the trusted tool version


def test_compare_cli_requires_expected_and_commit_and_writes_a_valid_drill(tmp_path, capsys):
    (tmp_path / "pre.json").write_text(json.dumps(env_(same_sets())))
    (tmp_path / "post.json").write_text(json.dumps(env_({**same_sets(), "bg_a": fp(900)})))
    (tmp_path / "exp.json").write_text(json.dumps(ASSETS))
    base = ["compare-fingerprints", "--pre", str(tmp_path / "pre.json"), "--post", str(tmp_path / "post.json"),
            "--expected", str(tmp_path / "exp.json"), "--commit", SHA40, "--out", str(tmp_path / "drill.json")]
    assert sr.main(base) == 4
    assert sr.main(["validate-drill", str(tmp_path / "drill.json")]) == 0
    (tmp_path / "ex.json").write_text(json.dumps({"bg_a": explain(n=3)}))
    assert sr.main(base + ["--explained", str(tmp_path / "ex.json")]) == 0
    assert sr.main(["validate-drill", str(tmp_path / "drill.json")]) == 0
    doc = json.loads((tmp_path / "drill.json").read_text())
    doc["result"] = "FAIL"
    (tmp_path / "bad.json").write_text(json.dumps(doc))
    assert sr.main(["validate-drill", str(tmp_path / "bad.json")]) == 2
    assert sr.main(base[:-4] + ["--commit", "nope"]) == 2
    capsys.readouterr()


def test_e57_uses_the_e55_fingerprint_definition_not_a_second_one():
    """One definition: the harness measures through nikasha_stale_certs, and defines no fingerprint function of its own."""
    import nikasha_stale_certs as nsc
    assert "nsc.table_fingerprint" in SRC and "def fingerprint_rows" not in SRC and "hashlib.sha256(canonical" not in SRC
    assert callable(nsc.fingerprint_rows) and callable(nsc.table_fingerprint)
    assert sr.FINGERPRINT_DEFINITION.startswith("nikasha_stale_certs.table_fingerprint/")


# ═════════════════════════ 5. self-test cases (real SQL / real run_cli) ═════════════════════════

def test_idempotent_rebuild_case_on_the_disposable_cluster(needs_psycopg, disposable_pg):
    log = sr.ConnectionLog()
    conn = sr.connect_checked(disposable_pg.url, "disposable", log, expect=EXPECT(disposable_pg))
    try:
        m = sr.measure_idempotent_rebuild(conn)
    finally:
        conn.close()
    assert sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m) == ("PASS", [])
    assert m["fingerprint_before"] == m["fingerprint_after_rebuild"] != m["fingerprint_after_material_change"]
    assert log.opened[0]["host"] == "127.0.0.1" and log.opened[0]["port"] == disposable_pg.port


def test_idempotent_case_flips_to_fail_when_the_declaration_leaks_a_volatile_column(needs_psycopg, disposable_pg, monkeypatch):
    """Broken variant: the declaration forgets to exclude build_id/created_at, so a rebuild MOVES the fingerprint."""
    monkeypatch.setattr(sr, "SYNTH_DECL", {**sr.SYNTH_DECL, "volatile_columns": ["id"]})
    conn = sr.connect_checked(disposable_pg.url, "disposable", sr.ConnectionLog(), expect=EXPECT(disposable_pg))
    try:
        m = sr.measure_idempotent_rebuild(conn)
    finally:
        conn.close()
    result, problems = sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m)
    assert result == "FAIL" and any("moved" in p for p in problems)


def test_idempotent_case_flips_to_fail_when_the_fingerprint_is_blind(needs_psycopg, disposable_pg, monkeypatch):
    import nikasha_stale_certs as nsc
    monkeypatch.setattr(nsc, "fingerprint_rows", lambda rows, decl: H)
    conn = sr.connect_checked(disposable_pg.url, "disposable", sr.ConnectionLog(), expect=EXPECT(disposable_pg))
    try:
        m = sr.measure_idempotent_rebuild(conn)
    finally:
        conn.close()
    result, problems = sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m)
    assert result == "FAIL" and any("blind" in p for p in problems)


def test_family_case_runs_the_real_run_cli_and_never_touches_the_database():
    m = sr.measure_family_refusal()
    assert sr.judge_case("family_dispatch_refused", m) == ("PASS", [])
    assert m["exit_code"] == 4 and m["refusal_codes"] == ["FAMILY_ASSET"] and m["connect_calls"] == 0 and m["dispatch_calls"] == 0
    assert "FAMILY_FILE_MISSING" in m["missing_file_committing_codes"]


def test_family_case_flips_to_fail_when_the_family_refusal_is_broken(monkeypatch):
    import suvarna_level_wave as slw
    monkeypatch.setattr(slw, "family_refusals", lambda assets, family, *, committing: [])
    m = sr.measure_family_refusal()
    result, problems = sr.judge_case("family_dispatch_refused", m)
    assert result == "FAIL" and any("FAMILY_ASSET" in p for p in problems)


def test_family_case_flips_to_fail_when_the_name_pattern_refusal_is_off(monkeypatch):
    """The name pattern (ka_gochara*, ...) is enforced even with no family file: switching it off must flip the case."""
    import re
    import suvarna_level_wave as slw
    monkeypatch.setattr(slw, "FAMILY_NAME_PATTERN", re.compile(r"^never-matches$"))
    result, problems = sr.judge_case("family_dispatch_refused", sr.measure_family_refusal())
    assert result == "FAIL" and any("name pattern" in p or "was not refused" in p for p in problems)


def test_family_case_flips_to_fail_when_the_family_set_refusal_is_off(monkeypatch):
    import suvarna_level_wave as slw
    real = slw.family_refusals
    monkeypatch.setattr(slw, "family_refusals", lambda assets, family, *, committing: [r for r in real(assets, family, committing=committing)
                                                                                      if r.get("via") != "family_set"])
    assert sr.judge_case("family_dispatch_refused", sr.measure_family_refusal())[0] == "FAIL"


def test_idempotent_judge_needs_positive_row_counts_even_when_equal():
    m = good_measured("idempotent_rebuild_fingerprint_unchanged")
    m["rows_before"] = m["rows_after"] = 0
    result, problems = sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m)
    assert result == "FAIL" and any("positive" in p for p in problems)
    m["rows_before"] = m["rows_after"] = True
    assert sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m)[0] == "FAIL"


def test_family_case_flips_to_fail_when_a_missing_family_file_fails_open(monkeypatch):
    import suvarna_level_wave as slw
    real = slw.family_refusals
    monkeypatch.setattr(slw, "family_refusals", lambda assets, family, *, committing: [r for r in real(assets, family, committing=committing)
                                                                                      if r["code"] != "FAMILY_FILE_MISSING"])
    result, problems = sr.judge_case("family_dispatch_refused", sr.measure_family_refusal())
    assert result == "FAIL" and any("fail-open" in p for p in problems)


GUARD_OK = textwrap.dedent('''
    import os
    def hold_present(home=None):
        return os.path.exists(os.path.join(home, "run", "SUVARNA_HOLD"))
    def evaluate(tool_name, tool_input, home=None):
        cmd = (tool_input or {}).get("command", "")
        if hold_present(home) and "suvarna_level_wave" in cmd:
            return True, "hold is set"
        return False, ""
''')


def _stub_tracker(tmp_path, body: str) -> pathlib.Path:
    pkg = tmp_path / "trk" / "suvarna_tracker"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "hold_guard.py").write_text(body)
    return tmp_path / "trk"


def test_hold_case_plumbing_with_a_stub_tracker_and_restores_sys_state(tmp_path):
    before_path, before_mods = list(sys.path), {k for k in sys.modules if k.startswith("suvarna_tracker")}
    m = sr.measure_hold(_stub_tracker(tmp_path, GUARD_OK))
    assert sr.judge_case("hold_refuses_dispatch", m) == ("PASS", [])
    assert m["hold_guard_sha256"] == sr.sha256_file(tmp_path / "trk" / "suvarna_tracker" / "hold_guard.py")
    assert sys.path == before_path and {k for k in sys.modules if k.startswith("suvarna_tracker")} == before_mods


@pytest.mark.parametrize("body,needle", [
    (GUARD_OK.replace("return True, \"hold is set\"", "return False, \"\""), "not blocked with the hold"),
    (GUARD_OK.replace("hold_present(home) and", ""), "without a hold"),
    (GUARD_OK.replace('"suvarna_level_wave" in cmd', "True"), "over-refuses"),
])
def test_hold_case_flips_to_fail_for_a_broken_guard(tmp_path, body, needle):
    result, problems = sr.judge_case("hold_refuses_dispatch", sr.measure_hold(_stub_tracker(tmp_path, body)))
    assert result == "FAIL" and any(needle in p for p in problems)


def test_hold_case_refuses_a_missing_tracker(tmp_path):
    with pytest.raises(sr.RehearsalError, match="not found"):
        sr.measure_hold(tmp_path)


def test_connections_case_probes_refusal_and_flips_when_a_probe_would_connect(monkeypatch):
    log = sr.ConnectionLog()
    log.opened.append(dict(GOOD_ENTRY))
    m = sr.measure_connections(log)
    assert m["probe_refused_without_socket"] is True and m["refused_count"] == 2
    assert sr.judge_case("no_production_write", m) == ("PASS", [])
    monkeypatch.setitem(sr.POLICIES, "rehearsal", lambda u: u)               # a policy that accepts anything...
    monkeypatch.setattr(sr, "connect_checked", lambda *a, **k: "connected")  # ...and a connect that never refuses
    m2 = sr.measure_connections(sr.ConnectionLog())
    assert m2["probe_refused_without_socket"] is False and sr.judge_case("no_production_write", m2)[0] == "FAIL"


def test_run_self_test_end_to_end_on_the_disposable_cluster(needs_psycopg, disposable_pg, tmp_path):
    doc = sr.run_self_test(tracker_dir=_stub_tracker(tmp_path, GUARD_OK), connect_url=disposable_pg.url,
                           pg_info={"port": disposable_pg.port, "data_directory": str(disposable_pg.data_dir), "pg_version": "x"})
    assert sr.validate_evidence(doc) == []
    got = {c["id"]: (c["result"], c["unmeasured_reason"]) for c in doc["cases"]}
    assert got == {
        "find_fix_rebuild_certify": ("UNMEASURED", "NEEDS_REHEARSAL_ORCHESTRATOR_RUN"),
        "f3_proof": ("UNMEASURED", "NEEDS_REHEARSAL_SCHEMA_WITH_1036"),
        "family_dispatch_refused": ("PASS", None), "hold_refuses_dispatch": ("PASS", None),
        "canary_triggers_reversal": ("UNMEASURED", "NEEDS_CANARY_REVERSAL_MECHANISM"),
        "idempotent_rebuild_fingerprint_unchanged": ("PASS", None), "no_production_write": ("PASS", None)}
    assert doc["mode"] == "self_test" and doc["result"] == "UNMEASURED"
    conns = next(c for c in doc["cases"] if c["id"] == "no_production_write")["measured"]["opened"]
    assert [c["host"] for c in conns] == ["127.0.0.1"] and conns[0]["port"] == disposable_pg.port


def test_run_self_test_without_a_database_or_tracker_is_unmeasured_not_pass():
    doc = sr.run_self_test(tracker_dir=None, connect_url=None)
    assert sr.validate_evidence(doc) == []
    got = {c["id"]: c["unmeasured_reason"] for c in doc["cases"] if c["result"] == "UNMEASURED"}
    assert got["idempotent_rebuild_fingerprint_unchanged"] == "NEEDS_DISPOSABLE_PG" and got["no_production_write"] == "NEEDS_DISPOSABLE_PG"
    assert got["hold_refuses_dispatch"] == "NEEDS_TRACKER_HOLD_GUARD" and doc["result"] == "UNMEASURED"


def test_self_test_cli_without_psycopg_is_unmeasured_with_a_reason_not_an_error(tmp_path, monkeypatch, capsys):
    """CI's governance shard installs only pyyaml + pytest: the driver may be absent."""
    monkeypatch.setattr(sr, "_psycopg_available", lambda: False)
    monkeypatch.setattr(sr, "_disposable_cluster", lambda: pytest.fail("the cluster must not be started without the driver"))
    assert sr.main(["self-test", "--out", str(tmp_path / "st.json")]) == 0
    doc = json.loads((tmp_path / "st.json").read_text())
    got = {c["id"]: c["unmeasured_reason"] for c in doc["cases"] if c["result"] == "UNMEASURED"}
    assert got["idempotent_rebuild_fingerprint_unchanged"] == "NEEDS_PSYCOPG" and got["no_production_write"] == "NEEDS_PSYCOPG"
    assert doc["result"] == "UNMEASURED" and sr.validate_evidence(doc) == []
    capsys.readouterr()


def test_self_test_in_a_subprocess_without_the_driver_exits_0(tmp_path):
    """The real CLI with `import psycopg` blocked (a sitecustomize that raises ImportError)."""
    block = tmp_path / "block"
    block.mkdir()
    (block / "sitecustomize.py").write_text("import sys\nclass _B:\n    def find_spec(self, name, path=None, target=None):\n"
                                            "        if name == 'psycopg' or name.startswith('psycopg.'):\n"
                                            "            raise ImportError('blocked')\nsys.meta_path.insert(0, _B())\n")
    env = {"PATH": os.environ["PATH"], "PYTHONPATH": str(block), "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1",
           "TMPDIR": os.environ.get("TMPDIR", "/tmp")}
    r = subprocess.run([sys.executable, str(GOV / "suvarna_rehearsal.py"), "self-test", "--out", str(tmp_path / "o.json")], env=env,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-500:]
    doc = json.loads((tmp_path / "o.json").read_text())
    assert next(c for c in doc["cases"] if c["id"] == "idempotent_rebuild_fingerprint_unchanged")["unmeasured_reason"] == "NEEDS_PSYCOPG"


def test_self_test_never_connects_to_anything_but_the_disposable_cluster(monkeypatch):
    seen = []
    monkeypatch.setattr(sr, "connect_checked", lambda url, policy, log, **k: seen.append((url, policy)) or pytest.fail("no connection expected"))
    sr.run_self_test(tracker_dir=None, connect_url=None)
    assert seen == []


def test_self_test_cli_writes_a_self_test_document_never_at_the_detector_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sr, "_disposable_cluster", lambda: None)
    assert sr.main(["self-test", "--out", str(tmp_path / "evidence" / "E5.6" / "REHEARSAL.json")]) == 2
    assert not (tmp_path / "evidence").exists()
    assert sr.main(["self-test", "--out", str(tmp_path / "st.json")]) == 0
    assert json.loads((tmp_path / "st.json").read_text())["mode"] == "self_test"


# ═════════════════════════ 6. source mutants ═════════════════════════

def load_module(src: str, name: str = "sr_mutant") -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(GOV / "suvarna_rehearsal.py")
    sys.modules[name] = mod
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)         # noqa: S102 - the repo's own source, one mutation applied
    return mod


def _lifecycle_dir(tmp: pathlib.Path, conf: str, hba: str) -> pathlib.Path:
    d = tmp / f"d{abs(hash((conf, hba))) % 10**8}"
    d.mkdir()
    (d / "postgresql.conf").write_text(conf)
    (d / "pg_hba.conf").write_text(hba)
    return d


def with_id_list(doc: dict) -> dict:
    d = copy.deepcopy(doc)
    d["cases"][0]["id"] = ["unhashable"]
    return d


def with_measured_list(doc: dict) -> dict:
    d = copy.deepcopy(doc)
    next(c for c in d["cases"] if c["id"] == "find_fix_rebuild_certify")["measured"] = [1]
    return d


def invariants(m: types.ModuleType, tmp: pathlib.Path) -> list[str]:
    """The verdict-deciding behaviours, checked against module `m`. Returns the names of the invariants that FAIL (the
    unmutated module must return [])."""
    bad: list[str] = []

    def check(name: str, cond: Callable[[], bool]) -> None:
        try:
            ok = bool(cond())
        except Exception:                                        # noqa: BLE001 - a crash is a failed invariant
            ok = False
        if not ok:
            bad.append(name)

    def raises(exc, fn) -> bool:
        try:
            fn()
        except exc:
            return True
        return False

    # evidence: judges
    gm = lambda cid: good_measured(cid)                          # noqa: E731
    for cid in m.CASE_CATALOG:
        check(f"judge_pass:{cid}", lambda cid=cid: m.judge_case(cid, gm(cid))[0] == "PASS")
    for cid, items in BREAKS.items():
        for k, v in items:
            def broken(cid=cid, k=k, v=v):
                mm = gm(cid)
                mm[k] = v
                return m.judge_case(cid, mm)[0] == "FAIL"
            check(f"judge_fail:{cid}:{k}", broken)
    check("judge_empty_fails", lambda: all(m.judge_case(c, {})[0] == "FAIL" for c in m.CASE_CATALOG))
    # evidence: validator re-derives
    st = self_test_doc(m)
    check("valid_self_test", lambda: m.validate_evidence(st) == [])
    forged = copy.deepcopy(st)
    next(c for c in forged["cases"] if c["id"] == "idempotent_rebuild_fingerprint_unchanged")["measured"]["fingerprint_after_rebuild"] = H2
    check("forged_case_pass_rejected", lambda: m.validate_evidence(forged) != [])
    f2 = copy.deepcopy(st)
    f2["result"] = "PASS"
    check("forged_top_result_rejected", lambda: m.validate_evidence(f2) != [])
    f3 = copy.deepcopy(st)
    f3["summary"]["pass"] = 99
    check("forged_summary_rejected", lambda: m.validate_evidence(f3) != [])
    f4 = copy.deepcopy(st)
    f4["extra"] = 1
    check("closed_top_schema", lambda: m.validate_evidence(f4) != [])
    f5 = copy.deepcopy(st)
    f5["cases"][0]["extra"] = 1
    check("closed_case_schema", lambda: m.validate_evidence(f5) != [])
    f6 = copy.deepcopy(st)
    next(c for c in f6["cases"] if c["id"] == "f3_proof")["measured"] = {"x": 1}
    check("unmeasured_carries_nothing", lambda: m.validate_evidence(f6) != [])
    f7 = copy.deepcopy(st)
    next(c for c in f7["cases"] if c["id"] == "f3_proof")["unmeasured_reason"] = "whatever"
    check("unmeasured_needs_NEEDS", lambda: m.validate_evidence(f7) != [])
    f8 = copy.deepcopy(st)
    f8["cases"][0]["detector"]["claim"] = "weaker"
    check("detector_cannot_be_redefined", lambda: m.validate_evidence(f8) != [])
    f9 = copy.deepcopy(st)
    f9["environment"]["cluster"]["host"] = "10.0.0.5"
    check("cluster_must_be_loopback", lambda: m.validate_evidence(f9) != [])
    f10 = copy.deepcopy(st)
    f10["environment"]["cluster"]["port"] = 5432
    check("cluster_port_not_forbidden", lambda: m.validate_evidence(f10) != [])
    f11 = copy.deepcopy(st)
    f11["environment"]["cluster"]["kind"] = "production"
    check("cluster_kind_closed", lambda: m.validate_evidence(f11) != [])
    shortfp = gm("idempotent_rebuild_fingerprint_unchanged")
    shortfp["fingerprint_before"] = shortfp["fingerprint_after_rebuild"] = "zz"
    check("idempotent_fingerprints_must_be_sha256", lambda: m.judge_case("idempotent_rebuild_fingerprint_unchanged", shortfp)[0] == "FAIL")
    check("self_test_never_pass", lambda: m.derive_result("self_test", {"required": 7, "pass": 7, "fail": 0, "unmeasured": 0}) != "PASS")
    check("fail_wins", lambda: m.derive_result("rehearsal", {"required": 7, "pass": 6, "fail": 1, "unmeasured": 0}) == "FAIL")
    check("rehearsal_all_pass_is_pass", lambda: m.derive_result("rehearsal", {"required": 7, "pass": 7, "fail": 0, "unmeasured": 0}) == "PASS")
    check("rehearsal_partial_is_unmeasured", lambda: m.derive_result("rehearsal", {"required": 7, "pass": 6, "fail": 0, "unmeasured": 1}) == "UNMEASURED")
    reh = rehearsal_doc(m)
    check("valid_rehearsal", lambda: m.validate_evidence(reh) == [])
    r1 = copy.deepcopy(reh)
    r1["job_image_commit"] = "2" * 40
    check("orchestrator_equals_job_image", lambda: m.validate_evidence(r1) != [])
    r2 = copy.deepcopy(reh)
    r2["cases"][0]["basis"] = "synthetic_fixture"
    check("rehearsal_pass_needs_rehearsal_basis", lambda: m.validate_evidence(r2) != [])
    r3 = copy.deepcopy(reh)
    r3["cases"][0]["evidence"] = []
    check("rehearsal_pass_needs_pointers", lambda: m.validate_evidence(r3) != [])
    check("write_refuses_self_test_at_detector_path",
          lambda: raises(m.RehearsalError, lambda: m.write_evidence(st, tmp / "ev" / "E5.6" / "REHEARSAL.json")))
    check("write_refuses_invalid", lambda: raises(m.RehearsalError, lambda: m.write_evidence(f2, tmp / "inv.json")))
    check("unmeasured_case_reason", lambda: raises(m.RehearsalError, lambda: m.unmeasured_case("f3_proof", "done")))
    # connection policy
    ('        conn = dial(normalised)', '        conn = dial(url)'),
    ('        ident = _server_identity(conn)\n        why = _identity_problem(policy, ident, expect)', '        ident, why = None, None'),
    ('    if why is not None:\n        with contextlib.suppress(Exception):\n            conn.close()', '    if False:\n        with contextlib.suppress(Exception):\n            conn.close()'),
    ('    with scrubbed_pg_env():\n        conn = dial(normalised)', '    if True:\n        conn = dial(normalised)'),
    ('            os.environ.update(saved)', '            pass'),
    ('if ident["host"] != LOOPBACK or ident["port"] in FORBIDDEN_PORTS:', 'if False:'),
    ('        if ident["port"] != DEFAULT_PORT or not rg.DB_NAME_RE.fullmatch(ident["database"]):', '        if False:'),
    ('        if not _same_path(ident["data_directory"], f"{DEFAULT_ROOT}/pg"):', '        if False:'),
    ('    if policy != "disposable":\n        return', '    if False:\n        return'),
    ('and ident["port"] == expect.get("port") and ident["database"].startswith("suvarna_disposable")):', 'and True):'),
    ('m["rows_before"] > 0 and', ''),
    class _Pol:
        called = 0
    def dial(*a):
        _Pol.called += 1
        return "c"
    m.POLICIES["permissive"] = lambda u: u
    check("final_loopback_check", lambda: raises(m.EndpointRefused, lambda: m.connect_checked("postgresql://u@10.0.0.5:40123/d", "permissive", m.ConnectionLog(), connect=dial)) and _Pol.called == 0)
    check("final_forbidden_port_check", lambda: raises(m.EndpointRefused, lambda: m.connect_checked("postgresql://u@127.0.0.1:5432/d", "permissive", m.ConnectionLog(), connect=dial)) and _Pol.called == 0)
    del m.POLICIES["permissive"]
    check("rehearsal_policy_direct", lambda: raises(ValueError, lambda: m.rehearsal_policy("postgresql://u@10.0.0.5:55432/rehearsal")))
    check("disposable_policy_direct_remote", lambda: raises(ValueError, lambda: m.disposable_policy("postgresql://suvarna_disposable@10.0.0.9:41000/suvarna_disposable")))
    check("disposable_policy_direct_port", lambda: raises(ValueError, lambda: m.disposable_policy("postgresql://suvarna_disposable@127.0.0.1:5432/suvarna_disposable")))
    check("rehearsal_policy_refuses_remote", lambda: raises(m.EndpointRefused, lambda: m.connect_checked("postgresql://u@10.0.0.5:55432/rehearsal", "rehearsal", m.ConnectionLog(), connect=dial)))
    check("disposable_refuses_rehearsal_port", lambda: raises(m.EndpointRefused, lambda: m.connect_checked("postgresql://suvarna_disposable@127.0.0.1:55432/suvarna_disposable", "disposable", m.ConnectionLog(), connect=dial)))
    check("disposable_refuses_prod_port", lambda: raises(m.EndpointRefused, lambda: m.connect_checked("postgresql://suvarna_disposable@127.0.0.1:5432/suvarna_disposable", "disposable", m.ConnectionLog(), connect=dial)))
    check("disposable_refuses_other_host", lambda: raises(m.EndpointRefused, lambda: m.connect_checked("postgresql://suvarna_disposable@10.0.0.9:41000/suvarna_disposable", "disposable", m.ConnectionLog(), connect=dial)))
    check("refusal_dials_nothing", lambda: _Pol.called == 0)
    # lifecycle: loopback-only config
    ok_hba = "local all all trust\nhost all all 127.0.0.1/32 trust\n"
    check("config_ok_accepted", lambda: m.check_loopback_config(_lifecycle_dir(tmp, "listen_addresses = '127.0.0.1'\n", ok_hba)) is None)
    check("config_star_refused", lambda: raises(m.LifecycleError, lambda: m.check_loopback_config(_lifecycle_dir(tmp, "listen_addresses = '*'\n", ok_hba))))
    check("config_localhost_refused", lambda: raises(m.LifecycleError, lambda: m.check_loopback_config(_lifecycle_dir(tmp, "listen_addresses = 'localhost'\n", ok_hba))))
    check("config_include_refused", lambda: raises(m.LifecycleError, lambda: m.check_loopback_config(_lifecycle_dir(tmp, "include = 'x'\n", ok_hba))))
    check("hba_open_refused", lambda: raises(m.LifecycleError, lambda: m.check_loopback_config(_lifecycle_dir(tmp, "listen_addresses = '127.0.0.1'\n", ok_hba + "host all all 0.0.0.0/0 trust\n"))))
    check("hba_nonrule_refused", lambda: raises(m.LifecycleError, lambda: m.check_loopback_config(_lifecycle_dir(tmp, "listen_addresses = '127.0.0.1'\n", ok_hba + "include_dir x\n"))))
    # lifecycle: marker + status + reap
    mk = tmp / "mk"
    mk.mkdir(mode=0o700)
    os.chmod(mk, 0o700)
    good_marker = {"kind": m.MARKER_KIND, "v": m.MARKER_VERSION, "root": str(mk), "host": "127.0.0.1", "port": 41001, "uid": os.getuid()}
    (mk / m.MARKER_NAME).write_text(json.dumps(good_marker))
    check("marker_valid", lambda: m.read_marker(mk) is not None)
    for label, edit in (("uid", {"uid": os.getuid() + 1}), ("host", {"host": "0.0.0.0"}), ("port_prod", {"port": 5432}),
                        ("kind", {"kind": "x"}), ("root", {"root": "/x"})):
        def bad_marker(edit=edit):
            (mk / m.MARKER_NAME).write_text(json.dumps({**good_marker, **edit}))
            r = m.read_marker(mk)
            (mk / m.MARKER_NAME).write_text(json.dumps(good_marker))
            return r is None
        check(f"marker_rejects:{label}", bad_marker)
    check("reap_needs_confirm", lambda: raises(m.LifecycleError, lambda: m.reap_cluster(mk, remove_data=True)))
    short = pathlib.Path(os.path.realpath(tempfile.mkdtemp(prefix="e56i", dir="/tmp")))      # short: a socket path has a length limit
    try:
        check("init_forbidden_port", lambda: raises(m.LifecycleError, lambda: m.init_cluster(short / "ip", port=5432, pg_bin=str(short / "nobin")))
              and not (short / "ip").exists())
    finally:
        shutil.rmtree(short, ignore_errors=True)
    sd = tmp / "st"
    (sd / "pg").mkdir(parents=True)
    os.chmod(sd, 0o700)
    (sd / "pg" / "PG_VERSION").write_text("15")
    (sd / "pg" / "postmaster.pid").write_text("4242\n")
    saved = m._proc_command
    m._proc_command = lambda pid: "/usr/sbin/cron -f"
    try:
        check("status_foreign_not_running", lambda: m.status_cluster(sd)["state"] == "foreign")
        m._proc_command = lambda pid: f"/opt/pg/bin/postgres -D {sd}/pg -p 1"
        check("status_running", lambda: m.status_cluster(sd)["state"] == "running")
        m._proc_command = lambda pid: None
        check("status_unknown_not_stopped", lambda: m.status_cluster(sd)["state"] == "unknown")
        m._proc_command = lambda pid: ""
        check("status_gone_is_stopped", lambda: m.status_cluster(sd)["state"] == "stopped")
    finally:
        m._proc_command = saved
    lay = m._Layout(mk)
    def second_lock():
        with m._locked(lay):
            return raises(m.LifecycleError, lambda: m._locked(lay).__enter__())
    check("lock_is_exclusive", second_lock)
    # connection: the answering server is verified, the environment scrubbed, the NORMALISED url dialled
    def rconn(**kw):
        return FakeConn(f"{m.DEFAULT_ROOT}/pg", **kw)

    def refused_and_closed(make, policy="rehearsal", url=REHEARSAL_URL, expect=None):
        log, box = m.ConnectionLog(), []
        ok = raises(m.EndpointRefused, lambda: m.connect_checked(url, policy, log, connect=lambda u: box.append(make()) or box[-1], expect=expect))
        return ok and log.opened == [] and box[0].closed is True
    check("ident_ok_logged_verified", lambda: (lambda lg: (m.connect_checked(REHEARSAL_URL, "rehearsal", lg, connect=lambda u: rconn()), lg.opened[0]["verified"])[1] is True)(m.ConnectionLog()))
    check("ident_wrong_data_dir", lambda: refused_and_closed(lambda: FakeConn("/else/pg")))
    check("ident_wrong_port", lambda: refused_and_closed(lambda: rconn(port=55433)))
    check("ident_forbidden_port", lambda: refused_and_closed(lambda: rconn(port=5432)))
    check("ident_wrong_db", lambda: refused_and_closed(lambda: rconn(database="postgres")))
    check("ident_wrong_host", lambda: refused_and_closed(lambda: rconn(host="::1")))
    check("ident_unreadable", lambda: refused_and_closed(lambda: rconn(fail=True)))
    exp = {"data_directory": "/tmp/x/data", "port": 40123}
    dis = lambda **kw: FakeConn("/tmp/x/data", **{"port": 40123, "database": "suvarna_disposable", **kw})  # noqa: E731
    check("disposable_ident_ok", lambda: m.connect_checked(DISPOSABLE_URL, "disposable", m.ConnectionLog(), connect=lambda u: dis(), expect=exp) is not None)
    check("disposable_ident_wrong_dir", lambda: refused_and_closed(lambda: FakeConn("/tmp/y/data", port=40123, database="suvarna_disposable"), "disposable", DISPOSABLE_URL, exp))
    check("disposable_ident_wrong_port", lambda: refused_and_closed(lambda: dis(port=40124), "disposable", DISPOSABLE_URL, exp))
    check("disposable_ident_wrong_db", lambda: refused_and_closed(lambda: dis(database="postgres"), "disposable", DISPOSABLE_URL, exp))
    check("disposable_ident_needs_expect", lambda: refused_and_closed(lambda: dis(), "disposable", DISPOSABLE_URL, None))
    real_pol = m.POLICIES["rehearsal"]
    m.POLICIES["rehearsal"] = lambda u: "postgresql://Dev@127.0.0.1:55432/rehearsal"
    dialled: list = []
    try:
        m.connect_checked("postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=raw", "rehearsal", m.ConnectionLog(),
                          connect=lambda u: dialled.append(u) or rconn())
    finally:
        m.POLICIES["rehearsal"] = real_pol
    check("dial_normalised_not_raw", lambda: dialled == ["postgresql://Dev@127.0.0.1:55432/rehearsal"])
    seen: dict = {}
    os.environ["PGHOSTADDR"], os.environ["DATABASE_URL"] = "::1", "u"
    try:
        m.connect_checked(REHEARSAL_URL, "rehearsal", m.ConnectionLog(), connect=lambda u: seen.update(h=os.environ.get("PGHOSTADDR"), d=os.environ.get("DATABASE_URL")) or rconn())
        restored = os.environ.get("PGHOSTADDR") == "::1" and os.environ.get("DATABASE_URL") == "u"
    finally:
        os.environ.pop("PGHOSTADDR", None)
        os.environ.pop("DATABASE_URL", None)
    check("env_scrubbed_around_dial", lambda: seen == {"h": None, "d": None})
    check("env_restored_after_dial", lambda: restored)
    # evidence: tool hash, pointer tie, rehearsal-only connections, malformed documents, write guard spellings
    tool_forged = copy.deepcopy(st)
    tool_forged["generated_by"]["tool_sha256"] = H
    check("tool_hash_must_match", lambda: m.validate_evidence(tool_forged) != [] and m.validate_evidence(tool_forged, tool_sha=H) == [])
    pt = copy.deepcopy(reh)
    next(c for c in pt["cases"] if c["id"] == "f3_proof")["measured"]["dangling_after_change"] = 99
    check("pointer_tied_to_measured", lambda: m.validate_evidence(pt) != [])
    pt2 = copy.deepcopy(reh)
    next(c for c in pt2["cases"] if c["id"] == "f3_proof")["evidence"] = []
    check("pointer_required", lambda: m.validate_evidence(pt2) != [])
    rp = copy.deepcopy(reh)
    cnp = next(c for c in rp["cases"] if c["id"] == "no_production_write")
    cnp["measured"]["opened"] = [{**GOOD_ENTRY}]
    cnp["evidence"][0] = m.measured_record_pointer(cnp)
    check("rehearsal_doc_rehearsal_policy_only", lambda: m.validate_evidence(rp) != [])
    junk = [None, 5, [], {}, with_id_list(st), with_measured_list(reh)]
    check("validator_never_raises", lambda: all(isinstance(r, list) and r for r in (m.validate_evidence(j) for j in junk)))
    for spelling in ("EV/e5.6/REHEARSAL.JSON", "x/Rehearsal.Json", "ev/E5.6/rehearsal.json"):
        check(f"write_guard:{spelling}", lambda sp=spelling: raises(m.RehearsalError, lambda: m.write_evidence(st, tmp / sp)))
    # lifecycle: spelling variants, adopt port, reap pins, start symlink
    def cfg_refused(conf_line, hba=ok_hba):
        return raises(m.LifecycleError, lambda: m.check_loopback_config(_lifecycle_dir(tmp, conf_line + "\n", hba)))
    for line in ("LISTEN_ADDRESSES '*'", "listen_addresses=*", "Listen_Addresses = 'localhost'", "Include 'x'", "include_if_exists = 'x'", "hba_file '/x'"):
        check(f"cfg_variant:{line}", lambda line=line: cfg_refused(line))
    check("cfg_variant_ok", lambda: m.check_loopback_config(_lifecycle_dir(tmp, "LISTEN_ADDRESSES '127.0.0.1'\n", ok_hba)) is None)
    check("hba_case_variant", lambda: cfg_refused("listen_addresses = '127.0.0.1'", "HOST all all 0.0.0.0/0 trust\n"))
    lc = pathlib.Path(os.path.realpath(tempfile.mkdtemp(prefix="e56l", dir="/tmp")))
    try:
        stubs_dir = lc / "bin"
        stubs_dir.mkdir()
        for name, body in (("initdb", STUB_INITDB), ("pg_ctl", STUB_PG_CTL)):
            (stubs_dir / name).write_text(body)
            (stubs_dir / name).chmod(0o755)
        rt = lc / "rehearsal"
        m.DEFAULT_ROOT = str(rt)
        m.init_cluster(rt, port=_free_port(), pg_bin=str(stubs_dir))
        saved_ps = m._proc_command
        m._proc_command = lambda pid: ""
        try:
            check("reap_needs_exact_confirm", lambda: all(raises(m.LifecycleError, lambda c=c: m.reap_cluster(rt, pg_bin=str(stubs_dir), remove_data=True, confirm=c)) for c in (None, "", str(rt) + "/", "/x")) and (rt / "pg").exists())
            m.DEFAULT_ROOT = "/Users/Dev/suvarna/not-this-root"
            check("reap_pinned_to_default_root", lambda: raises(m.LifecycleError, lambda: m.reap_cluster(rt, pg_bin=str(stubs_dir), remove_data=True, confirm=str(rt))) and (rt / "pg").exists())
            m.DEFAULT_ROOT = str(rt)
            (rt / "pg" / "PG_VERSION").rename(rt / "PG_VERSION.bak")
            check("reap_needs_pg_version", lambda: raises(m.LifecycleError, lambda: m.reap_cluster(rt, pg_bin=str(stubs_dir), remove_data=True, confirm=str(rt))) and (rt / "pg").exists())
            (rt / "PG_VERSION.bak").rename(rt / "pg" / "PG_VERSION")
            (stubs_dir / "pg_ctl").write_text("#!/bin/bash\nexit 0\n")
            (rt / "pg" / "postmaster.pid").write_text("4242\n")
            m._proc_command = lambda pid: f"/opt/pg/bin/postgres -D {rt}/pg -p 1"
            check("reap_refuses_when_still_alive", lambda: raises(m.LifecycleError, lambda: m.reap_cluster(rt, pg_bin=str(stubs_dir), remove_data=True, confirm=str(rt))) and (rt / "pg").exists())
            (rt / "pg" / "postmaster.pid").unlink()
            m._proc_command = lambda pid: ""
            os.rename(rt / "pg", lc / "real_pg")
            (rt / "pg").symlink_to(lc / "real_pg")
            check("start_refuses_symlinked_data_dir", lambda: raises(m.LifecycleError, lambda: m.start_cluster(rt, pg_bin=str(stubs_dir))))
        finally:
            m._proc_command = saved_ps
        ad = lc / "adopt"
        (ad / "pg").mkdir(parents=True)
        os.chmod(ad, 0o700)
        (ad / "pg" / "PG_VERSION").write_text("15")
        (ad / "pg" / "postgresql.conf").write_text("listen_addresses = '127.0.0.1'\nport = 5432\n")
        (ad / "pg" / "pg_hba.conf").write_text("host all all 127.0.0.1/32 trust\n")
        check("adopt_validates_port_first", lambda: raises(m.LifecycleError, lambda: m.adopt_cluster(ad, port=5432)) and not (ad / m.MARKER_NAME).exists())
    except Exception:                                          # noqa: BLE001 - a mutant that lets reap delete the data dir breaks the setup
        bad.append("lifecycle_block_crashed")
    finally:
        shutil.rmtree(lc, ignore_errors=True)
    # E5.7
    full = {a: fp(i + 1) for i, a in enumerate(ASSETS)}
    envl = m.fingerprint_set
    dtl = lambda n: f"{DETAIL} [asset {n}]"  # noqa: E731
    ex = lambda code, n, dec="N-77": {"reason_code": code, "detail": dtl(n), **({"decision": dec} if dec else {})}  # noqa: E731

    def cmp2(prod, reh, expl=None, **kw):
        return m.compare_fingerprint_sets(envl(prod), envl(reh), expl, **{"expected_assets": ASSETS, "commit": SHA40, **kw})
    diff = {**full, "bg_b": fp(99)}
    check("compare_equal_passes", lambda: cmp2(full, full)["result"] == "PASS")
    check("compare_unexplained_fails", lambda: cmp2(full, diff)["result"] == "FAIL")
    check("compare_explained_passes", lambda: cmp2(full, diff, {"bg_b": ex("rolling_horizon", 1)})["result"] == "PASS")
    check("compare_uncovered_fails", lambda: cmp2({"bg_a": fp(1)}, {"bg_a": fp(1)})["result"] == "FAIL")
    check("compare_unexpected_fails", lambda: cmp2({**full, "bg_zzz": fp(1)}, {**full, "bg_zzz": fp(1)})["result"] == "FAIL")
    check("compare_kind_restricted_codes", lambda: cmp2(full, diff, {"bg_b": ex("source_unavailable_offline", 1)})["result"] == "FAIL")
    miss = {k: v for k, v in full.items() if k != "bg_j"}
    check("compare_missing_kind_codes", lambda: cmp2(miss, full, {"bg_j": ex("asset_new_at_commit", 1)})["result"] == "PASS" and cmp2(miss, full, {"bg_j": ex("rolling_horizon", 1)})["result"] == "FAIL")
    check("compare_short_detail_fails", lambda: cmp2(full, diff, {"bg_b": {"reason_code": "rolling_horizon", "detail": "short", "decision": "N-1"}})["result"] == "FAIL")
    check("compare_bad_decision_fails", lambda: cmp2(full, diff, {"bg_b": ex("rolling_horizon", 1, "SS-1")})["result"] == "FAIL")
    check("compare_undecided_fails_by_default", lambda: cmp2(full, diff, {"bg_b": ex("rolling_horizon", 1, None)})["result"] == "FAIL")
    check("compare_undecided_allowed_by_share", lambda: cmp2(full, diff, {"bg_b": ex("rolling_horizon", 1, None)}, max_undecided_share=0.2)["result"] == "PASS")
    check("compare_stray_explanation_fails", lambda: cmp2(full, full, {"bg_a": ex("rolling_horizon", 1)})["result"] == "FAIL")
    alld = {a: fp(500 + i) for i, a in enumerate(ASSETS)}
    check("compare_difference_share_cap", lambda: cmp2(full, alld, {a: ex("seeded_not_rebuilt", i) for i, a in enumerate(ASSETS)})["result"] == "FAIL")
    rep_ = {a: {"reason_code": "seeded_not_rebuilt", "detail": dtl(0), "decision": "N-1"} for a in ASSETS[:3]}
    rep2 = {a: rep_[a] for a in ASSETS[:2]}
    two = {**full, **{a: fp(700 + i) for i, a in enumerate(ASSETS[:2])}}
    check("compare_repeated_detail_fails", lambda: cmp2(full, two, rep2)["result"] == "FAIL")
    check("compare_control_char_detail_fails", lambda: cmp2(full, diff, {"bg_b": {"reason_code": "rolling_horizon", "detail": dtl(1) + "\n", "decision": "N-1"}})["result"] == "FAIL")
    check("compare_neither_side_not_explainable", lambda: cmp2(miss, miss, {"bg_j": ex("source_unavailable_offline", 1)})["result"] == "FAIL")
    for label, bad_exp in (("empty", []), ("dup", ["bg_a", "bg_a"]), ("badid", ["Bad Id"])):
        check(f"compare_expected_{label}_refused", lambda b=bad_exp: raises(m.RehearsalError, lambda: m.compare_fingerprint_sets(envl(full), envl(full), expected_assets=b, commit=SHA40)))
    os.environ["GIT_DIR"] = "/x"
    try:
        genv = m._git_env()
    finally:
        os.environ.pop("GIT_DIR", None)
    check("git_env_scrubbed", lambda: "GIT_DIR" not in genv and genv["HOME"] == "/nonexistent")
    check("compare_explained_non_mapping_refused", lambda: raises(m.RehearsalError, lambda: cmp2(full, full, [1])))
    check("compare_marker_required", lambda: raises(m.RehearsalError, lambda: m.compare_fingerprint_sets(full, envl(full), expected_assets=ASSETS, commit=SHA40)))
    check("compare_wrong_marker_refused", lambda: raises(m.RehearsalError, lambda: m.compare_fingerprint_sets({"definition": "x/1", "fingerprints": full}, envl(full), expected_assets=ASSETS, commit=SHA40)))
    check("compare_expected_required", lambda: raises(m.RehearsalError, lambda: m.compare_fingerprint_sets(envl(full), envl(full), expected_assets=None, commit=SHA40)))
    check("compare_commit_required", lambda: raises(m.RehearsalError, lambda: m.compare_fingerprint_sets(envl(full), envl(full), expected_assets=ASSETS, commit="x")))
    drill = cmp2(full, diff, {"bg_b": ex("rolling_horizon", 1)})
    check("drill_valid", lambda: m.validate_drill(drill) == [])
    for label, edit in (("result", lambda d: d.update(result="FAIL")), ("tool", lambda d: d.update(tool_sha256=H)),
                        ("rehearsal", lambda d: d["rehearsal"]["fingerprints"].update(bg_b=fp(1))), ("limits", lambda d: d["limits"].update(max_difference_share=1.0)),
                        ("explained", lambda d: d["explained_input"].clear()), ("key", lambda d: d.update(extra=1))):
        def tampered(edit=edit):
            d = copy.deepcopy(drill)
            edit(d)
            return m.validate_drill(d) != []
        check(f"drill_tamper:{label}", tampered)
    check("drill_junk_never_raises", lambda: all(m.validate_drill(j) for j in (None, 5, [], {})))
    return bad


def test_invariant_suite_is_clean_on_the_unmutated_module(tmp_path):
    mod = load_module(SRC, "sr_clean")
    assert invariants(mod, tmp_path) == []


MUTANTS = [
    # judges
    ('if m["fingerprint_before"] != m["fingerprint_after_rebuild"]:\n        p.append("the fingerprint moved', 'if False:\n        p.append("the fingerprint moved'),
    ('if m["fingerprint_after_material_change"] == m["fingerprint_before"]:', 'if False:'),
    ('if m["other_chart_before"] != m["other_chart_after"]:', 'if False:'),
    ('if m["volatile_columns_changed"] is not True:', 'if False:'),
    ('if not (_is_int(m["exit_code"]) and m["exit_code"] == 4):', 'if False:'),
    ('if not (_is_int(m["exit_code"]) and m["exit_code"] == 4):', 'if m["exit_code"] != 4:'),
    ('if "FAMILY_ASSET" not in m["refusal_codes"]:', 'if False:'),
    ('if not set(m["intersecting_assets"]) <= set(m["refused_assets"]):', 'if False:'),
    ('if not {"name_pattern", "family_set"} <= set(m["refused_via"]):', 'if False:'),
    ('if not {"name_pattern", "family_set"} <= set(m["refused_via"]):', 'if not {"family_set"} <= set(m["refused_via"]):'),
    ('if not (_is_int(m["connect_calls"]) and _is_int(m["dispatch_calls"]) and m["connect_calls"] == 0 and m["dispatch_calls"] == 0):', 'if False:'),
    ('if not (_is_int(m["connect_calls"]) and _is_int(m["dispatch_calls"]) and m["connect_calls"] == 0 and m["dispatch_calls"] == 0):', 'if m["connect_calls"] != 0 or m["dispatch_calls"] != 0:'),
    ('if "FAMILY_FILE_MISSING" not in m["missing_file_committing_codes"]:', 'if False:'),
    ('if m["blocked_with_hold"] is not True:', 'if False:'),
    ('if m["blocked_without_hold"] is not False:', 'if False:'),
    ('if m["non_dispatch_blocked_with_hold"] is not False:', 'if False:'),
    ('if m["msr_replace_refused"] is not False:', 'if False:'),
    ('if not (_is_int(m["dangling_after_change"]) and m["dangling_after_change"] > 0):', 'if False:'),
    ('if not (_is_int(m["dangling_after_downstream_rebuild"]) and m["dangling_after_downstream_rebuild"] == 0):', 'if False:'),
    ('if not (_is_int(m["dangling_after_downstream_rebuild"]) and m["dangling_after_downstream_rebuild"] == 0):', 'if m["dangling_after_downstream_rebuild"] != 0:'),
    ('all(v is True for v in restored.values())', 'True'),
    ('if m["stale_after_fix_detected"] is not True:', 'if False:'),
    ('and m["fingerprint_before"] != m["fingerprint_after_rebuild"]):\n        p.append("the rebuild did not change', 'and True):\n        p.append("the rebuild did not change'),
    ('and m["orchestrator_commit"] == m["evidence_commit"]):', 'and True):'),
    ('if m["probe_refused_without_socket"] is not True:', 'if False:'),
    ('if e["host"] != LOOPBACK or not _is_int(e["port"]) or e["port"] in FORBIDDEN_PORTS or e["policy"] not in POLICIES:', 'if False:'),
    ('if e["host"] != LOOPBACK or not _is_int(e["port"])', 'if not _is_int(e["port"])'),
    ('if e["verified"] is not True or', 'if'),
    ('    elif e["port"] == DEFAULT_PORT or not e["database"].startswith("suvarna_disposable"):', '    elif False:'),
    ('        if e["port"] != DEFAULT_PORT or not rg.DB_NAME_RE.fullmatch(e["database"]) or not _same_path(e["data_directory"], f"{DEFAULT_ROOT}/pg"):', '        if False:'),
    ('if not (isinstance(e, Mapping) and set(e) == set(keys)):', 'if False:'),
    ('if any(isinstance(e, Mapping) and e.get("policy") != "rehearsal" for e in c["measured"].get("opened", [])):', 'if False:'),
    ('if not (isinstance(opened, list) and opened):', 'if False:'),
    ('return p + ["no connection was recorded: the log proves nothing"]', 'return p'),
    ('        return p\n    p = [f"{k} is not a sha256" for k in want[:5] if not _h64(m[k])]', '        return p\n    p = []'),
    # verdict derivation
    ('    if summary["fail"]:\n        return "FAIL"', '    if False:\n        return "FAIL"'),
    ('if mode == "rehearsal" and summary["pass"] == summary["required"]:', 'if summary["pass"] == summary["required"]:'),
    ('if mode == "rehearsal" and summary["pass"] == summary["required"]:', 'if mode == "rehearsal" and summary["pass"] >= 1:'),
    ('if derived != c["result"]:', 'if False:'),
    ('if doc["summary"] != summary:', 'if False:'),
    ('if doc["result"] != want:', 'if False:'),
    ('if set(doc) != set(TOP_KEYS):', 'if False:'),
    ('p = [f"{cid}: key set differs from the closed case schema"] if set(c) != set(CASE_KEYS) else []', 'p = []'),
    ('if c["title"] != spec["title"] or c["detector"] != {"name": spec["detector"], "claim": spec["claim"]}:', 'if False:'),
    ('if c["measured"] or c["fingerprints"] or c["evidence"] or c["basis"] is not None:', 'if False:'),
    ('if not (isinstance(c["unmeasured_reason"], str) and _NEEDS.fullmatch(c["unmeasured_reason"])):', 'if False:'),
    ('if not _NEEDS.fullmatch(reason):', 'if False:'),
    ('if doc["orchestrator_commit"] != doc["job_image_commit"]:', 'if False:'),
    ('if c["basis"] != "rehearsal_db":', 'if False:'),
    ('and _is_int(cl["port"]) and cl["port"] not in FORBIDDEN_PORTS and cl["kind"] in ("rehearsal", "disposable")):', 'and True):'),
    ('if doc["mode"] == "self_test" and _is_detector_path(target):', 'if False:'),
    ('    real = os.path.realpath(target).replace(os.sep, "/").lower()', '    real = str(target)'),
    ('return real.endswith("/" + DETECTOR_EVIDENCE_PATH.lower()) or os.path.basename(real) == "rehearsal.json"', 'return real.endswith("/" + DETECTOR_EVIDENCE_PATH)'),
    ('    problems = validate_evidence(doc)\n    if problems:\n        raise RehearsalError("refusing to write an invalid', '    problems = []\n    if problems:\n        raise RehearsalError("refusing to write an invalid'),
    # connection policy
    ('if ep["host"] != LOOPBACK or ep["port"] in FORBIDDEN_PORTS:', 'if False:'),
    ('if port is None or port in FORBIDDEN_PORTS or port == rg.REHEARSAL_PORT:', 'if port is None:'),
    ('if authority.rpartition("@")[2].rsplit(":", 1)[0] != LOOPBACK:', 'if False:'),
    ('    return rg.normalise_rehearsal_url(url)', '    return url'),
    # lifecycle
    ('and m.get("uid") == os.getuid())', 'and True)'),
    ('and 1024 <= m["port"] <= 65535 and m["port"] not in FORBIDDEN_PORTS', 'and True'),
    ('and m.get("root") == str(lay.root) and m.get("host") == LOOPBACK', 'and m.get("host") == LOOPBACK'),
    ('and m.get("root") == str(lay.root) and m.get("host") == LOOPBACK', 'and m.get("root") == str(lay.root)'),
    ('if remove_data and confirm != str(lay.root):', 'if False:'),
    ('if key == "listen_addresses" and _conf_value(m.group(2)) != LOOPBACK:', 'if False:'),
    ('        key = m.group(1).lower()', '        key = m.group(1)'),
    ('if key in _CONF_INCLUDES or key == "hba_file":', 'if key in _CONF_INCLUDES:'),
    ('if key in _CONF_INCLUDES or key == "hba_file":', 'if False:'),
    ('def _check_port(port: Any) -> None:\n    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535 or port in FORBIDDEN_PORTS:', 'def _check_port(port: Any) -> None:\n    if False:'),
    ('    _check_port(port)                                              # BEFORE anything is written: no poison marker\n', ''),
    ('if remove_data and str(lay.root) != DEFAULT_ROOT:', 'if False:'),
    ('if remove_data and not (lay.data / "PG_VERSION").is_file():', 'if False:'),
    ('if lay.data.is_symlink() or os.path.realpath(lay.data) != str(lay.data):', 'if False:'),
    ('            if status_cluster(root)["state"] not in ("not_initialised", "stopped"):\n                raise LifecycleError("the cluster is still alive', '            if False:\n                raise LifecycleError("the cluster is still alive'),
    ('"GIT_CONFIG_GLOBAL": os.devnull', '"GIT_CONFIG_GLOBAL": "/etc/gitconfig"') if False else ('    return {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": "/nonexistent",', '    return {**os.environ, "PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": "/nonexistent",'),
    ('if addr != f"{LOOPBACK}/32":', 'if False:'),
    ('        else:\n            raise LifecycleError(f"pg_hba.conf rule {ln.strip()!r} is not a local/host rule: refusing")', '        else:\n            pass'),
    ('    elif _is_postmaster_for(cmd, lay.data):', '    elif True:'),
    ('    if cmd is None:\n        out["state"] = "unknown"', '    if cmd is None:\n        out["state"] = "stopped"'),
    ('not 1024 <= port <= 65535 or port in FORBIDDEN_PORTS:', 'not 1024 <= port <= 65535:'),
    ('fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)', 'fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)'),
    # E5.7
    ('failed = bool(unexplained or stray or uncovered or unexpected or problems)', 'failed = bool(stray or uncovered or unexpected or problems)'),
    ('failed = bool(unexplained or stray or uncovered or unexpected or problems)', 'failed = bool(unexplained or uncovered or unexpected or problems)'),
    ('failed = bool(unexplained or stray or uncovered or unexpected or problems)', 'failed = bool(unexplained or stray or unexpected or problems)'),
    ('failed = bool(unexplained or stray or uncovered or unexpected or problems)', 'failed = bool(unexplained or stray or uncovered or problems)'),
    ('failed = bool(unexplained or stray or uncovered or unexpected or problems)', 'failed = bool(unexplained or stray or uncovered or unexpected)'),
    ('if e["reason_code"] not in EXPLAIN_CODES_BY_KIND[kind]:', 'if False:'),
    ('if "decision" in e and not (isinstance(e["decision"], str) and _DECISION_ID.fullmatch(e["decision"])):', 'if False:'),
    ('if norm in seen:', 'if False:'),
    ('if "decision" not in e:\n            undecided += 1', 'if False:\n            undecided += 1'),
    ('if expected and undecided / len(expected) > max_undecided_share:', 'if False:'),
    ('if expected and len(diffs) / len(expected) > max_difference_share:', 'if False:'),
    ('uncovered = [a for a in expected if a not in prod and a not in reh]', 'uncovered = []'),
    ('unexpected = sorted((set(prod) | set(reh)) - set(expected))', 'unexpected = []'),
    ('if env["definition"] != FINGERPRINT_DEFINITION:', 'if False:'),
    ('if not isinstance(explained, Mapping):', 'if False:'),
    ('if not exp or not all(isinstance(a, str) and _ASSET_ID.fullmatch(a) for a in exp) or len(set(exp)) != len(exp):', 'if False:'),
    ('if not (isinstance(commit, str) and HEX40.fullmatch(commit)):\n        raise RehearsalError("commit must be 40-hex")', 'if False:\n        raise RehearsalError("commit must be 40-hex")'),
    ('if again != dict(doc):', 'if False:'),
    ('if (lim["max_undecided_share"], lim["max_difference_share"]) != DEFAULT_LIMITS:', 'if False:'),
    ('p = [] if doc["tool_sha256"] == want_tool else', 'p = [] if True else'),
    ('isinstance(d, str) and len(d.strip()) >= MIN_DETAIL_CHARS', 'isinstance(d, str) and len(d.strip()) >= 1'),
    ('and not any(ord(ch) < 32 for ch in d)', 'and True'),
    ('if a in prod and a in reh and prod[a] == reh[a]:', 'if a in prod and a in reh:'),
    ('kind = "missing_in_rehearsal" if a not in reh else "missing_in_production" if a not in prod else "fingerprint_differs"', 'kind = "fingerprint_differs"'),
]


@pytest.mark.parametrize("old,new", MUTANTS, ids=[f"m{i:02d}" for i in range(len(MUTANTS))])
def test_every_source_mutant_is_caught(tmp_path, old, new):
    assert SRC.count(old) >= 1, f"the mutant target no longer exists in the source: {old!r}"
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    try:
        mod = load_module(mutated, "sr_mut_" + str(abs(hash(old + new)) % 10**8))
    except Exception:
        return                                                    # a mutant that does not even load is trivially dead
    failed = invariants(mod, tmp_path)
    assert failed, f"SURVIVING MUTANT: replacing {old!r} with {new!r} changed no invariant"
