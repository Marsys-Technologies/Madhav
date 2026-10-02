"""prerun_gate.py GATE_V2 with gh and psql replaced by PATH shims (no network, no database, no credential)."""
import hashlib
import os
import re
import sys

import pytest

from gate_v2_helpers import GATE, GATE_DIR, run_gate, runs, staged, world  # noqa: F401

OK_LINE = "GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0 role=suvarna_reader OK"


def lines(r):
    return r.stderr.strip().split("\n")


# ------------------------------------------------------------------ the basic contract
def test_zero_zero_passes_prints_both_counts_on_stderr_and_one_final_ok_line(world):
    world.gh(history=runs(5))
    world.psql(count=0)
    r = run_gate(world.env())
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""                                                    # stdout is empty, always
    assert "deploy_runs_not_completed=0" in lines(r) and "build_runs_in_flight=0" in lines(r)
    assert lines(r)[-1] == OK_LINE
    assert sum(1 for l in lines(r) if l.endswith(" OK")) == 1


@pytest.mark.parametrize("hist,statuses,count,d,b", [
    (runs(3) + runs(1, "in_progress", 5000), {}, 0, 1, 0),
    (runs(3), {}, 1, 0, 1),
    (runs(3) + runs(2, "queued", 5000), {"queued": runs(2, "queued", 5000)}, 3, 2, 3),
], ids=["1/0", "0/1", "2/3"])
def test_nonzero_counts_fail_and_both_are_printed(world, hist, statuses, count, d, b):
    world.gh(history=hist, statuses=statuses)
    world.psql(count=count)
    r = run_gate(world.env())
    assert r.returncode == 1 and r.stdout == ""
    assert "deploy_runs_not_completed=%d" % d in lines(r) and "build_runs_in_flight=%d" % b in lines(r)
    assert lines(r)[-1].startswith("GATE_V2 FAIL") and "OK" not in lines(r)[-1].split()


def test_the_real_state_names_and_a_single_psql_call_with_current_user(world):
    run_gate(world.env())
    calls = world.calls()
    assert calls.count("psql ") == 1                                          # role and count in the SAME psql call
    assert "current_user" in calls and "count(*)" in calls
    assert "state IN ('planned','running','paused')" in calls and "public.build_runs" in calls and "-X -A -t" in calls
    assert "env PGUSER=suvarna_reader PGHOST=127.0.0.1 PGDATABASE=amjis" in calls    # came from the SOURCED file


def test_gh_queries_history_limit_100_and_one_query_per_non_completed_status(world):
    run_gate(world.env())
    gh_calls = [l for l in world.calls().split("\n") if l.startswith("gh ")]
    assert len(gh_calls) == 6
    for l in gh_calls:
        assert "run list --workflow deploy.yml --branch main --limit 100" in l and "--json databaseId,status" in l
    assert [l for l in gh_calls if "--status" not in l]
    for s in ("queued", "in_progress", "waiting", "pending", "requested"):
        assert any("--status %s" % s in l for l in gh_calls)


# ------------------------------------------------------------------ (b) all non-completed deploys, not the newest 20
def test_a_stuck_queued_run_beyond_position_20_in_the_history_is_counted(world):
    hist = runs(30) + runs(1, "queued", 7000) + runs(20, "completed", 8000)   # the queued run is #31 of the history
    world.gh(history=hist)                                                   # (the per-status queries return [])
    world.psql(count=0)
    r = run_gate(world.env())
    assert r.returncode == 1 and "deploy_runs_not_completed=1" in lines(r)


def test_a_stuck_queued_run_beyond_the_newest_100_is_found_by_its_status_query(world):
    world.gh(history=runs(150), statuses={"queued": runs(1, "queued", 99999)})
    r = run_gate(world.env())
    assert r.returncode == 1 and "deploy_runs_not_completed=1" in lines(r)


@pytest.mark.parametrize("status", ["queued", "in_progress", "waiting", "pending", "requested"])
def test_every_non_completed_status_query_is_counted(world, status):
    world.gh(history=runs(150), statuses={status: runs(2, status, 90000)})
    r = run_gate(world.env())
    assert r.returncode == 1 and "deploy_runs_not_completed=2" in lines(r)


def test_union_by_database_id_does_not_double_count(world):
    stuck = runs(2, "in_progress", 5000)
    world.gh(history=runs(3) + stuck, statuses={"in_progress": stuck})
    r = run_gate(world.env())
    assert "deploy_runs_not_completed=2" in lines(r)


def test_a_run_seen_non_completed_in_any_query_counts_even_if_the_history_says_completed(world):
    world.gh(history=[{"databaseId": 1, "status": "completed"}], statuses={"queued": [{"databaseId": 1, "status": "queued"}]})
    assert "deploy_runs_not_completed=1" in lines(run_gate(world.env()))


def test_empty_per_status_lists_are_fine(world):
    world.gh(history=runs(2), statuses={})
    assert run_gate(world.env()).returncode == 0


def test_empty_history_list_fails_closed(world):
    world.gh(history=[])
    r = run_gate(world.env())
    assert r.returncode == 2 and "deploy_runs_not_completed=n/a" in lines(r) and "EMPTY" in r.stderr


# ------------------------------------------------------------------ fail closed on every read failure
GH_FAILURES = {
    "history-empty-output": dict(raw=""),
    "history-not-json": dict(raw="not json"),
    "history-not-a-list": dict(raw='{"databaseId": 1, "status": "completed"}'),
    "history-no-status-key": dict(raw='[{"databaseId": 1}]'),
    "history-no-id": dict(raw='[{"status": "completed"}]'),
    "history-empty-status": dict(raw='[{"databaseId": 1, "status": ""}]'),
    "history-bool-id": dict(raw='[{"databaseId": true, "status": "completed"}]'),
    "history-nonzero-exit": dict(history=runs(3), rc={"history": 1}),
    "queued-empty-output": dict(history=runs(3), raw_status={"queued": ""}),
    "queued-not-json": dict(history=runs(3), raw_status={"queued": "<html>"}),
    "queued-not-a-list": dict(history=runs(3), raw_status={"queued": "{}"}),
    "waiting-nonzero-exit": dict(history=runs(3), rc={"status_waiting": 4}),
    "requested-not-json": dict(history=runs(3), raw_status={"requested": "nope"}),
}


@pytest.mark.parametrize("kw", list(GH_FAILURES.values()), ids=list(GH_FAILURES))
def test_gh_read_failures_fail_closed(world, kw):
    world.gh(**kw)
    world.psql(count=0)
    r = run_gate(world.env())
    assert r.returncode == 2, r.stderr
    assert "deploy_runs_not_completed=n/a" in lines(r) and "build_runs_in_flight=0" in lines(r)
    assert "GATE_V2 FAIL" in lines(r)[-1] and r.stdout == "" and " OK" not in r.stderr


PSQL_FAILURES = {
    "empty": dict(raw=""),
    "no-pipe": dict(raw="0\n"),
    "word-count": dict(raw="suvarna_reader|zero\n"),
    "two-lines": dict(raw="suvarna_reader|0\nsuvarna_reader|0\n"),
    "negative": dict(raw="suvarna_reader|-1\n"),
    "error-text": dict(raw="ERROR: permission denied for table build_runs\n"),
    "empty-role": dict(raw="|0\n"),
    "nonzero-exit": dict(count=0, rc=2),
}


@pytest.mark.parametrize("kw", list(PSQL_FAILURES.values()), ids=list(PSQL_FAILURES))
def test_psql_read_failures_fail_closed(world, kw):
    world.psql(**kw)
    r = run_gate(world.env())
    assert r.returncode == 2, r.stderr
    assert "build_runs_in_flight=n/a" in lines(r) and "deploy_runs_not_completed=0" in lines(r)


def test_timeouts_fail_closed_for_gh_history_gh_status_and_psql(world):
    for gh_kw, ps_kw, shown in [
        (dict(history=runs(3), sleep={"history": 30}), dict(count=0), "deploy_runs_not_completed=n/a"),
        (dict(history=runs(3), sleep={"status_pending": 30}), dict(count=0), "deploy_runs_not_completed=n/a"),
        (dict(history=runs(3)), dict(sleep=30), "build_runs_in_flight=n/a"),
    ]:
        world.gh(**gh_kw)
        world.psql(**ps_kw)
        r = run_gate(world.env(GATE_V2_TIMEOUT_S="1"))
        assert r.returncode == 2 and shown in lines(r) and "timed out" in r.stderr


def test_the_timeout_is_60_seconds_and_cannot_be_raised_even_in_test(world):
    src = GATE.read_text()
    assert "TIMEOUT_S = 60" in src and "min(TIMEOUT_S," in src


@pytest.mark.parametrize("missing", ["gh", "psql", "bash"])
def test_missing_binary_fails_closed(world, missing):
    # PATH holds ONLY the shim dir (+ the python/bash symlink dir for the two that exist): no runner-provided gh/psql can leak in
    path = [str(world.bin)]
    env = world.env(PATH=os.pathsep.join(path))
    if missing == "bash":
        pass                                                                  # no bash on PATH at all
    else:
        (world.bin / missing).unlink()
        env["GATE_V2_BASH"] = "/bin/bash"                                     # bash is available, only gh/psql is missing
    r = run_gate(env)
    assert r.returncode == 94 and "missing binary: %s" % missing in r.stderr and r.stdout == ""
    assert "GATE_V2 FAIL" in lines(r)[-1]


def test_an_override_binary_path_that_does_not_exist_fails_closed_without_falling_back(world):
    r = run_gate(world.env(GATE_V2_GH="/nonexistent/gh"))
    assert r.returncode == 94 and "missing binary: gh" in r.stderr


# ------------------------------------------------------------------ (a) pgenv.sh MUST source; role MUST be suvarna_reader
def test_pgenv_file_missing_fails_closed_with_exit_97(world):
    world.pgenv.unlink()
    r = run_gate(world.env())
    assert r.returncode == 97 and "sourcing pgenv.sh failed" in r.stderr and "build_runs_in_flight=n/a" in lines(r)
    assert "psql " not in world.calls()                                      # psql never ran on ambient PG*


@pytest.mark.parametrize("content", ["export PGUSER=suvarna_reader\nfalse\n", "return 3\n", "export PGUSER=suvarna_reader\nnonexistent_cmd_xyz\n"],
                         ids=["last-command-false", "return-3", "unknown-command-last"])
def test_pgenv_nonzero_status_when_sourced_fails_closed_with_exit_97(world, content):
    world.pgenv.write_text(content)
    r = run_gate(world.env())
    assert r.returncode == 97 and r.stdout == "" and "psql " not in world.calls()


def test_ambient_pg_variables_are_never_used_when_pgenv_does_not_set_them(world):
    world.pgenv.write_text("# sourced fine, exports nothing\n")
    r = run_gate(world.env(PGUSER="suvarna_reader", PGHOST="ambient-host", PGPASSWORD="ambient"))
    assert r.returncode == 96 and "role is 'none'" in r.stderr                # PGUSER did not survive into the subshell
    assert "PGHOST=unset" in world.calls() and "ambient" not in r.stderr


def test_bash_env_hook_is_not_honoured(world, tmp_path):
    hook = tmp_path / "hook.sh"
    hook.write_text("echo HOOKED >> %s\n" % (tmp_path / "hooked.txt"))
    run_gate(world.env(BASH_ENV=str(hook)))
    assert not (tmp_path / "hooked.txt").exists()


@pytest.mark.parametrize("role", ["postgres", "amjis_app", "Suvarna_Reader", "suvarna_reader2"])
def test_a_role_other_than_suvarna_reader_fails_closed_naming_only_the_role(world, role):
    world.psql(raw="%s|0\n" % role)
    r = run_gate(world.env())
    assert r.returncode == 96 and ("role is '%s'" % role) in r.stderr
    assert "build_runs_in_flight=n/a" in lines(r) and "sekrit" not in r.stderr
    assert " OK" not in r.stderr


def test_role_is_reported_in_the_ok_line_from_the_same_call(world):
    world.pgenv.write_text("export PGUSER=suvarna_reader\n")
    r = run_gate(world.env())
    assert r.returncode == 0 and "role=suvarna_reader OK" in lines(r)[-1]


def test_production_pgenv_path_is_the_real_home_file_and_overrides_are_ignored_without_the_test_flag(world):
    prod = world.home / ".config" / "suvarna" / "pgenv.sh"
    prod.write_text("export PGUSER=suvarna_reader\n")
    world.pgenv.write_text("return 1\n")                                     # a poisoned override that must NOT be read
    r = run_gate(world.operator_env(GATE_V2_PGENV=str(world.pgenv), GATE_V2_TIMEOUT_S="1"))
    assert r.returncode == 0, r.stderr                                       # GATE_V2_PGENV ignored: the HOME file was sourced
    prod.unlink()
    r = run_gate(world.operator_env())
    assert r.returncode == 97                                                # production file missing -> fail closed


# ------------------------------------------------------------------ (c) test environment is refused outside the harness
def test_orph_test_evidence_root_set_is_refused(world, tmp_path):
    r = run_gate(world.operator_env(ORPH_TEST_EVIDENCE_ROOT=str(tmp_path)))
    assert r.returncode == 95 and "ORPH_TEST_EVIDENCE_ROOT" in r.stderr and r.stdout == ""
    assert "gh " not in world.calls() and "psql " not in world.calls()       # refused before any read


def test_orph_test_evidence_root_set_to_empty_is_still_refused(world):
    assert run_gate(world.operator_env(ORPH_TEST_EVIDENCE_ROOT="")).returncode == 95


def test_pytest_current_test_set_is_refused(world):
    r = run_gate(world.operator_env(PYTEST_CURRENT_TEST="x::y (call)"))
    assert r.returncode == 95 and "PYTEST_CURRENT_TEST" in r.stderr


def test_the_under_test_flag_bypasses_only_the_env_refusal(world, tmp_path):
    r = run_gate(world.env(ORPH_TEST_EVIDENCE_ROOT=str(tmp_path), PYTEST_CURRENT_TEST="x"))
    assert r.returncode == 0 and "WARNING under_test=1" in r.stderr           # visible in the log
    world.psql(raw="postgres|0\n")
    assert run_gate(world.env(ORPH_TEST_EVIDENCE_ROOT=str(tmp_path))).returncode == 96   # the role check is NOT bypassed
    world.psql(count=1)
    assert run_gate(world.env(ORPH_TEST_EVIDENCE_ROOT=str(tmp_path))).returncode == 1    # nor the counts


def test_under_test_flag_must_be_exactly_1(world, tmp_path):
    assert run_gate(world.env(GATE_V2_UNDER_TEST="true", ORPH_TEST_EVIDENCE_ROOT=str(tmp_path))).returncode == 95


# ------------------------------------------------------------------ hygiene
def test_nothing_secret_or_child_output_is_ever_printed(world):
    world.psql(raw="suvarna_reader|0\nPASSWORD sekrit\n")
    r = run_gate(world.env())
    out = r.stdout + r.stderr
    assert r.returncode == 2 and "sekrit" not in out and "PASSWORD" not in out
    world.psql(count=0)
    r = run_gate(world.env())
    assert "sekrit" not in r.stdout + r.stderr and "PGPASSWORD" not in r.stdout + r.stderr


def test_the_gate_is_self_contained_stdlib_and_declares_its_version():
    src = GATE.read_text()
    assert 'GATE_VERSION = "GATE_V2"' in src
    import ast
    mods = {n.names[0].name.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import)}
    mods |= {n.module.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom) and n.module}
    assert mods <= set(sys.stdlib_module_names)


def test_readme_documents_the_current_sha256_of_every_bound_file():
    readme = (GATE_DIR / "README.md").read_text()
    for f in ("prerun_gate.py", "run_gated.sh", "executor_standards.py"):
        sha = hashlib.sha256((GATE_DIR / f).read_bytes()).hexdigest()
        assert re.search(r"`%s`.*%s" % (re.escape(f), sha), readme), "README must document the sha256 of %s (%s)" % (f, sha)
