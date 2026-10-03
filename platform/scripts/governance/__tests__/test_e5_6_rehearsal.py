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
import socket
import stat
import subprocess
import sys
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
            "intersecting_assets": ["ka_x"], "exit_code": 4, "refusal_codes": ["FAMILY_ASSET"], "connect_calls": 0,
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
            "opened": [{"host": "127.0.0.1", "port": 40001, "database": "suvarna_disposable", "policy": "disposable"}],
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


def rehearsal_doc(mod=sr, *, result_of: dict | None = None) -> dict:
    cases = []
    for cid in sr.REQUIRED_CASES:
        c = mod.case_result(cid, measured=good_measured(cid), basis="rehearsal_db", fingerprints={"fp": H},
                            evidence=[{"path": f"E5.6/{cid}.txt", "sha256": H}])
        cases.append(c)
    env = {"cluster": {"kind": "rehearsal", "host": "127.0.0.1", "port": 55432, "data_directory": "/Users/Dev/suvarna/rehearsal/pg",
                       "pg_version": "15.17"},
           "schema_replay": {"files_applied": 757, "files_failed": 0, "report_sha256": H},
           "seed": {"manifest_sha256": H2, "tables": ["asset_registry"]}}
    return mod.build_evidence(mode="rehearsal", commit=SHA40, cases=cases, environment=env, orchestrator_commit=SHA40,
                              job_image_commit=SHA40)


# ═════════════════════════ 1. connection policy ═════════════════════════

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
    sr.connect_checked(REHEARSAL_URL + "?application_name=e56", "rehearsal", log, connect=lambda u: dialled.append(u) or "conn")
    assert dialled == ["postgresql://Dev@127.0.0.1:55432/rehearsal?application_name=e56"]
    assert log.opened == [{"host": "127.0.0.1", "port": 55432, "database": "rehearsal", "policy": "rehearsal"}]


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
    sr.connect_checked(DISPOSABLE_URL, "disposable", log, connect=lambda u: "c")
    assert log.opened[0]["port"] == 40123


def test_unknown_policy_refused():
    with pytest.raises(sr.EndpointRefused):
        sr.connect_checked(REHEARSAL_URL, "anything", sr.ConnectionLog(), connect=lambda *a: "c")


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
    import shutil
    import tempfile
    base = pathlib.Path(os.path.realpath(tempfile.mkdtemp(prefix="e56r", dir="/tmp")))
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture()
def root(short_base):
    return short_base / "rehearsal"


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


BREAKS = {
    "idempotent_rebuild_fingerprint_unchanged": [
        ("fingerprint_after_rebuild", H2), ("fingerprint_after_material_change", H), ("other_chart_after", H), ("rows_after", 39),
        ("rows_before", 0), ("volatile_columns_changed", False), ("fingerprint_before", "short")],
    "family_dispatch_refused": [
        ("exit_code", 0), ("refusal_codes", []), ("connect_calls", 1), ("dispatch_calls", 1), ("intersecting_assets", []),
        ("control_refusal_codes", ["FAMILY_ASSET"]), ("control_refusal_codes", ["SPLITS_FAMILY"]), ("missing_file_committing_codes", [])],
    "hold_refuses_dispatch": [
        ("blocked_with_hold", False), ("blocked_without_hold", True), ("non_dispatch_blocked_with_hold", True),
        ("command", "git status"), ("hold_guard_sha256", "x")],
    "canary_triggers_reversal": [
        ("baseline_canary_passed", False), ("injected_difference_failed_canary", False), ("reversal_triggered", False),
        ("fingerprint_post_reversal", H2)],
    "f3_proof": [
        ("msr_replace_refused", True), ("dangling_after_change", 0), ("dangling_after_downstream_rebuild", 1), ("downstream_waves", []),
        ("referencing_tables_populated", {f"t{i}": 3 for i in range(6)}), ("referencing_tables_populated", {**{f"t{i}": 3 for i in range(6)}, "t6": 0}),
        ("fk_state", None), ("referencing_rows_restored", {f"t{i}": True for i in range(6)}),
        ("referencing_rows_restored", {**{f"t{i}": True for i in range(6)}, "t6": False}),
        ("referencing_rows_restored", {f"u{i}": True for i in range(7)})],
    "find_fix_rebuild_certify": [
        ("stale_after_fix_detected", False), ("fingerprint_after_rebuild", H), ("certificate_current_after_certify", False),
        ("certificate_detector_not_none", False), ("orchestrator_commit", "2" * 40), ("census_run_id", "")],
    "no_production_write": [
        ("opened", []), ("probe_refused_without_socket", False),
        ("opened", [{"host": "10.0.0.5", "port": 5432, "database": "x", "policy": "rehearsal"}]),
        ("opened", [{"host": "127.0.0.1", "port": 5432, "database": "x", "policy": "rehearsal"}]),
        ("opened", [{"host": "127.0.0.1", "port": 40001, "database": "x", "policy": "nope"}])],
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


def test_the_detector_reads_the_written_rehearsal_file_as_done(tmp_path):
    """The plan item's detector: result == PASS and `cases` present and non-null (suvarna_tracker.detectors.d_evidence_verified)."""
    doc = rehearsal_doc()
    ev = tmp_path / "evidence"
    for c in doc["cases"]:
        (ev / "E5.6").mkdir(parents=True, exist_ok=True)
        (ev / "E5.6" / f"{c['id']}.txt").write_text("x")
        c["evidence"] = [{"path": f"E5.6/{c['id']}.txt", "sha256": sr.sha256_file(ev / "E5.6" / f"{c['id']}.txt")}]
    sr.write_evidence(doc, ev / "E5.6" / "REHEARSAL.json", evidence_root=ev)
    got = json.loads((ev / "E5.6" / "REHEARSAL.json").read_text())
    assert got["result"] == "PASS" and got["cases"] is not None                # expect={"result":"PASS"}, required=["cases"]


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
    (lambda d: d["cases"][0].update(evidence=[]), "evidence pointers"),
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
    for c in doc["cases"]:
        f = ev / "E5.6" / f"{c['id']}.txt"
        f.write_text(c["id"])
        c["evidence"] = [{"path": f"E5.6/{c['id']}.txt", "sha256": sr.sha256_file(f)}]
    assert sr.check_pointers(doc, ev) == []
    (ev / "E5.6" / "f3_proof.txt").write_text("tampered")
    assert any("does not match" in p for p in sr.check_pointers(doc, ev))
    (ev / "E5.6" / "hold_refuses_dispatch.txt").unlink()
    assert any("missing" in p for p in sr.check_pointers(doc, ev))
    (ev / "E5.6" / "no_production_write.txt").unlink()
    (ev / "E5.6" / "no_production_write.txt").symlink_to(ev / "E5.6" / "f3_proof.txt")
    assert any("symlink" in p for p in sr.check_pointers(doc, ev))


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


# ═════════════════════════ 4. E5.7: pre/post fingerprint comparison ═════════════════════════

def fp(n: int) -> str:
    return f"{n:064x}"


def test_compare_equal_sets_pass_and_empty_is_not_pass():
    r = sr.compare_fingerprint_sets({"bg_a": fp(1), "bg_b": fp(2)}, {"bg_a": fp(1), "bg_b": fp(2)})
    assert r["result"] == "PASS" and r["equal"] == ["bg_a", "bg_b"] and r["differences"] == []
    assert sr.compare_fingerprint_sets({}, {})["result"] == "UNMEASURED"


def test_compare_difference_is_a_failure_until_explained_with_a_closed_reason():
    prod, reh = {"bg_a": fp(1), "bg_b": fp(2)}, {"bg_a": fp(1), "bg_b": fp(3)}
    r = sr.compare_fingerprint_sets(prod, reh)
    assert r["result"] == "FAIL" and r["unexplained"] == ["bg_b"] and r["differences"][0]["kind"] == "fingerprint_differs"
    good = {"bg_b": {"reason_code": "rolling_horizon", "detail": "muhurta lattice today..+5y, pinned as-of differs"}}
    ok = sr.compare_fingerprint_sets(prod, reh, good)
    assert ok["result"] == "PASS" and ok["differences"][0]["explained"] == good["bg_b"]
    for bad in ({"reason_code": "because", "detail": "x"}, {"reason_code": "rolling_horizon", "detail": "  "},
                {"reason_code": "rolling_horizon"}, {"reason_code": "rolling_horizon", "detail": "d", "extra": 1}, "text", None):
        assert sr.compare_fingerprint_sets(prod, reh, {"bg_b": bad})["result"] == "FAIL"


def test_compare_one_sided_assets_and_stray_explanations_fail():
    r = sr.compare_fingerprint_sets({"bg_a": fp(1), "bg_x": fp(9)}, {"bg_a": fp(1), "bg_y": fp(8)})
    kinds = {d["asset"]: d["kind"] for d in r["differences"]}
    assert r["result"] == "FAIL" and kinds == {"bg_x": "missing_in_rehearsal", "bg_y": "missing_in_production"}
    exp = {"reason_code": "seeded_not_rebuilt", "detail": "d"}
    assert sr.compare_fingerprint_sets({"bg_a": fp(1)}, {"bg_a": fp(1)}, {"bg_a": exp})["result"] == "FAIL"   # explains nothing
    both = sr.compare_fingerprint_sets({"bg_x": fp(9)}, {"bg_y": fp(8)}, {"bg_x": exp, "bg_y": exp})
    assert both["result"] == "PASS"


def test_compare_refuses_malformed_fingerprints_and_cli(tmp_path, capsys):
    for bad in ({"bg_a": "short"}, {"bg_a": 5}, [("bg_a", fp(1))], None):
        with pytest.raises(sr.RehearsalError):
            sr.compare_fingerprint_sets(bad, {"bg_a": fp(1)})
    (tmp_path / "pre.json").write_text(json.dumps({"bg_a": fp(1)}))
    (tmp_path / "post.json").write_text(json.dumps({"bg_a": fp(2)}))
    assert sr.main(["compare-fingerprints", "--pre", str(tmp_path / "pre.json"), "--post", str(tmp_path / "post.json")]) == 4
    (tmp_path / "post.json").write_text(json.dumps({"bg_a": fp(1)}))
    assert sr.main(["compare-fingerprints", "--pre", str(tmp_path / "pre.json"), "--post", str(tmp_path / "post.json")]) == 0


def test_e57_uses_the_e55_fingerprint_definition_not_a_second_one():
    """One definition: the harness measures through nikasha_stale_certs, and defines no fingerprint function of its own."""
    import nikasha_stale_certs as nsc
    assert "nsc.table_fingerprint" in SRC and "def fingerprint_rows" not in SRC and "hashlib.sha256(canonical" not in SRC
    assert callable(nsc.fingerprint_rows) and callable(nsc.table_fingerprint)


# ═════════════════════════ 5. self-test cases (real SQL / real run_cli) ═════════════════════════

def test_idempotent_rebuild_case_on_the_disposable_cluster(disposable_pg):
    log = sr.ConnectionLog()
    conn = sr.connect_checked(disposable_pg.url, "disposable", log)
    try:
        m = sr.measure_idempotent_rebuild(conn)
    finally:
        conn.close()
    assert sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m) == ("PASS", [])
    assert m["fingerprint_before"] == m["fingerprint_after_rebuild"] != m["fingerprint_after_material_change"]
    assert log.opened[0]["host"] == "127.0.0.1" and log.opened[0]["port"] == disposable_pg.port


def test_idempotent_case_flips_to_fail_when_the_declaration_leaks_a_volatile_column(disposable_pg, monkeypatch):
    """Broken variant: the declaration forgets to exclude build_id/created_at, so a rebuild MOVES the fingerprint."""
    monkeypatch.setattr(sr, "SYNTH_DECL", {**sr.SYNTH_DECL, "volatile_columns": ["id"]})
    conn = sr.connect_checked(disposable_pg.url, "disposable", sr.ConnectionLog())
    try:
        m = sr.measure_idempotent_rebuild(conn)
    finally:
        conn.close()
    result, problems = sr.judge_case("idempotent_rebuild_fingerprint_unchanged", m)
    assert result == "FAIL" and any("moved" in p for p in problems)


def test_idempotent_case_flips_to_fail_when_the_fingerprint_is_blind(disposable_pg, monkeypatch):
    import nikasha_stale_certs as nsc
    monkeypatch.setattr(nsc, "fingerprint_rows", lambda rows, decl: H)
    conn = sr.connect_checked(disposable_pg.url, "disposable", sr.ConnectionLog())
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
    log.opened.append({"host": "127.0.0.1", "port": 40001, "database": "suvarna_disposable", "policy": "disposable"})
    m = sr.measure_connections(log)
    assert m["probe_refused_without_socket"] is True and m["refused_count"] == 2
    assert sr.judge_case("no_production_write", m) == ("PASS", [])
    monkeypatch.setitem(sr.POLICIES, "rehearsal", lambda u: u)               # a policy that accepts anything...
    monkeypatch.setattr(sr, "connect_checked", lambda *a, **k: "connected")  # ...and a connect that never refuses
    m2 = sr.measure_connections(sr.ConnectionLog())
    assert m2["probe_refused_without_socket"] is False and sr.judge_case("no_production_write", m2)[0] == "FAIL"


def test_run_self_test_end_to_end_on_the_disposable_cluster(disposable_pg, tmp_path):
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
    import shutil
    import tempfile
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
    # E5.7
    pr, rh = {"a": fp(1), "b": fp(2)}, {"a": fp(1), "b": fp(3)}
    check("compare_diff_fails", lambda: m.compare_fingerprint_sets(pr, rh)["result"] == "FAIL")
    check("compare_equal_passes", lambda: m.compare_fingerprint_sets(pr, pr)["result"] == "PASS")
    check("compare_empty_not_pass", lambda: m.compare_fingerprint_sets({}, {})["result"] != "PASS")
    check("compare_bad_reason_fails", lambda: m.compare_fingerprint_sets(pr, rh, {"b": {"reason_code": "x", "detail": "d"}})["result"] == "FAIL")
    check("compare_good_reason_passes", lambda: m.compare_fingerprint_sets(pr, rh, {"b": {"reason_code": "rolling_horizon", "detail": "d"}})["result"] == "PASS")
    check("compare_missing_side_fails", lambda: m.compare_fingerprint_sets({"a": fp(1)}, {})["result"] == "FAIL")
    check("compare_blank_detail_fails", lambda: m.compare_fingerprint_sets(pr, rh, {"b": {"reason_code": "rolling_horizon", "detail": "  "}})["result"] == "FAIL")
    check("compare_stray_explanation_fails", lambda: m.compare_fingerprint_sets(pr, pr, {"a": {"reason_code": "rolling_horizon", "detail": "d"}})["result"] == "FAIL")
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
    ('if m["exit_code"] != 4:', 'if False:'),
    ('if "FAMILY_ASSET" not in (m["refusal_codes"] or []):', 'if False:'),
    ('if m["connect_calls"] != 0 or m["dispatch_calls"] != 0:', 'if False:'),
    ('if "FAMILY_FILE_MISSING" not in (m["missing_file_committing_codes"] or []):', 'if False:'),
    ('if m["blocked_with_hold"] is not True:', 'if False:'),
    ('if m["blocked_without_hold"] is not False:', 'if False:'),
    ('if m["non_dispatch_blocked_with_hold"] is not False:', 'if False:'),
    ('if m["msr_replace_refused"] is not False:', 'if False:'),
    ('if not (_is_int(m["dangling_after_change"]) and m["dangling_after_change"] > 0):', 'if False:'),
    ('if m["dangling_after_downstream_rebuild"] != 0:', 'if False:'),
    ('if m["stale_after_fix_detected"] is not True:', 'if False:'),
    ('and m["fingerprint_before"] != m["fingerprint_after_rebuild"]):\n        p.append("the rebuild did not change', 'and True):\n        p.append("the rebuild did not change'),
    ('and m["orchestrator_commit"] == m["evidence_commit"]):', 'and True):'),
    ('if m["probe_refused_without_socket"] is not True:', 'if False:'),
    ('e["port"] not in FORBIDDEN_PORTS and e.get("policy") in POLICIES', 'True'),
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
    ('        if not ev:\n            p.append(f"{cid}: a rehearsal PASS needs evidence pointers")', '        if False:\n            p.append(f"{cid}: a rehearsal PASS needs evidence pointers")'),
    ('and _is_int(cl["port"]) and cl["port"] not in FORBIDDEN_PORTS and cl["kind"] in ("rehearsal", "disposable")):', 'and True):'),
    ('if doc["mode"] == "self_test" and target.as_posix().endswith(DETECTOR_EVIDENCE_PATH):', 'if False:'),
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
    ('if m and not ln.lstrip().startswith("#") and m.group(1).strip("\'\\" ") != LOOPBACK:', 'if False:'),
    ('if re.match(r"^\\s*include(_if_exists|_dir)?\\s*=", ln):', 'if False:'),
    ('if addr != f"{LOOPBACK}/32":', 'if False:'),
    ('        else:\n            raise LifecycleError(f"pg_hba.conf rule {ln.strip()!r} is not a local/host rule: refusing")', '        else:\n            pass'),
    ('    elif _is_postmaster_for(cmd, lay.data):', '    elif True:'),
    ('    if cmd is None:\n        out["state"] = "unknown"', '    if cmd is None:\n        out["state"] = "stopped"'),
    ('not 1024 <= port <= 65535 or port in FORBIDDEN_PORTS:', 'not 1024 <= port <= 65535:'),
    ('fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)', 'fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)'),
    # E5.7
    ('result = "FAIL" if unexplained or stray else ("PASS" if assets else "UNMEASURED")', 'result = "FAIL" if stray else ("PASS" if assets else "UNMEASURED")'),
    ('result = "FAIL" if unexplained or stray else ("PASS" if assets else "UNMEASURED")', 'result = "FAIL" if unexplained else ("PASS" if assets else "UNMEASURED")'),
    ('result = "FAIL" if unexplained or stray else ("PASS" if assets else "UNMEASURED")', 'result = "FAIL" if unexplained or stray else "PASS"'),
    ('e["reason_code"] in EXPLAIN_CODES', 'True'),
    ('isinstance(e["detail"], str) and bool(e["detail"].strip())', 'True'),
    ('if a in production and a in rehearsal and production[a] == rehearsal[a]:', 'if a in production and a in rehearsal:'),
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
