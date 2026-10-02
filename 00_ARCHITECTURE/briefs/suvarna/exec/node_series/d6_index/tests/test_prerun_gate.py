"""prerun_gate.py / run_gated.sh with gh and psql replaced by PATH shims (no network, no database, no credential)."""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

EXEC_DIR = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture()
def shims(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    home = tmp_path / "home"
    (home / ".config" / "suvarna").mkdir(parents=True)
    (home / ".config" / "suvarna" / "pgenv.sh").write_text("# shim env: nothing exported\n")
    log = tmp_path / "calls.log"
    for name in ("gh", "psql"):
        up = name.upper()
        sh = bindir / name
        sh.write_text('#!/bin/sh\necho "%s $*" >> "%s"\nprintf "%%s" "${FAKE_%s_OUT-}"\nexit "${FAKE_%s_RC:-0}"\n' % (name, log, up, up))
        sh.chmod(0o755)
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + "/usr/bin:/bin", HOME=str(home))
    for k in [k for k in env if k.startswith("FAKE_")]:
        del env[k]
    return env, log


def gate(env, **fake):
    e = dict(env)
    e.update({"FAKE_" + k: str(v) for k, v in fake.items()})
    return subprocess.run([sys.executable, str(EXEC_DIR / "prerun_gate.py")], capture_output=True, text=True, env=e)


GH0 = '[{"status":"completed"},{"status":"completed"}]'


def test_zero_and_zero_passes_and_prints_both_counts(shims):
    env, log = shims
    r = gate(env, GH_OUT=GH0, PSQL_OUT="0\n")
    assert r.returncode == 0, r.stdout
    assert "deploy_runs_not_completed=0" in r.stdout and "build_runs_in_flight=0" in r.stdout and "GATE PASS" in r.stdout
    calls = log.read_text()
    assert "gh run list --workflow deploy.yml --branch main --limit 20 --json status" in calls
    assert "state IN ('planned','running','paused')" in calls and "-X -A -t" in calls     # real state names, as the reader


def test_deploy_in_flight_blocks(shims):
    env, _ = shims
    r = gate(env, GH_OUT='[{"status":"in_progress"},{"status":"queued"},{"status":"completed"}]', PSQL_OUT="0")
    assert r.returncode == 1 and "deploy_runs_not_completed=2" in r.stdout and "build_runs_in_flight=0" in r.stdout


def test_build_in_flight_blocks(shims):
    env, _ = shims
    r = gate(env, GH_OUT=GH0, PSQL_OUT="1")
    assert r.returncode == 1 and "deploy_runs_not_completed=0" in r.stdout and "build_runs_in_flight=1" in r.stdout


def test_both_in_flight_blocks_and_prints_both(shims):
    env, _ = shims
    r = gate(env, GH_OUT='[{"status":"in_progress"}]', PSQL_OUT="3")
    assert r.returncode == 1 and "deploy_runs_not_completed=1" in r.stdout and "build_runs_in_flight=3" in r.stdout


@pytest.mark.parametrize("fake,shown", [
    (dict(GH_OUT=GH0, GH_RC=1, PSQL_OUT="0"), ["deploy_runs_not_completed=n/a", "build_runs_in_flight=0"]),
    (dict(GH_OUT=GH0, PSQL_OUT="", PSQL_RC=2), ["deploy_runs_not_completed=0", "build_runs_in_flight=n/a"]),
    (dict(GH_OUT="not json", PSQL_OUT="0"), ["deploy_runs_not_completed=n/a", "build_runs_in_flight=0"]),
    (dict(GH_OUT='{"status":"completed"}', PSQL_OUT="0"), ["deploy_runs_not_completed=n/a"]),            # not a list
    (dict(GH_OUT='[{"state":"completed"}]', PSQL_OUT="0"), ["deploy_runs_not_completed=n/a"]),            # no status key
    (dict(GH_OUT='[{"status":""}]', PSQL_OUT="0"), ["deploy_runs_not_completed=n/a"]),
    (dict(GH_OUT=GH0, PSQL_OUT="zero"), ["deploy_runs_not_completed=0", "build_runs_in_flight=n/a"]),
    (dict(GH_OUT=GH0, PSQL_OUT="0\n0\n"), ["build_runs_in_flight=n/a"]),
    (dict(GH_OUT=GH0, PSQL_OUT=""), ["build_runs_in_flight=n/a"]),
    (dict(GH_OUT=GH0, PSQL_OUT="-1"), ["build_runs_in_flight=n/a"]),
    (dict(GH_OUT=GH0, PSQL_OUT="ERROR: permission denied"), ["build_runs_in_flight=n/a"]),
    (dict(GH_OUT="", PSQL_OUT=""), ["deploy_runs_not_completed=n/a", "build_runs_in_flight=n/a"]),
], ids=["gh-fails", "psql-fails", "gh-not-json", "gh-not-list", "gh-no-status", "gh-empty-status", "psql-word", "psql-two-lines",
        "psql-empty", "psql-negative", "psql-error-text", "both-empty"])
def test_read_failure_or_malformed_output_fails_closed_and_prints_counts(shims, fake, shown):
    env, _ = shims
    r = gate(env, **fake)
    assert r.returncode == 2, r.stdout
    for s in shown:
        assert s in r.stdout
    assert "GATE FAIL" in r.stdout and "GATE PASS" not in r.stdout


def test_missing_gh_binary_fails_closed(shims, tmp_path):
    env, _ = shims
    (pathlib.Path(env["PATH"].split(os.pathsep)[0]) / "gh").unlink()
    env = dict(env, FAKE_PSQL_OUT="0")
    r = subprocess.run([sys.executable, str(EXEC_DIR / "prerun_gate.py")], capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "deploy_runs_not_completed=n/a" in r.stdout


def test_gate_never_prints_the_environment_or_command_output(shims):
    env, _ = shims
    r = gate(env, GH_OUT=GH0, PSQL_OUT="0", GH_RC=0)
    assert "pgenv" not in r.stdout + r.stderr and "PASSWORD" not in (r.stdout + r.stderr).upper()


# ---- run_gated.sh: copy the two scripts next to a STUB executor, so the real executor can never start in a test
@pytest.fixture()
def staged(tmp_path):
    d = tmp_path / "stage"
    d.mkdir()
    for f in ("run_gated.sh", "prerun_gate.py"):
        shutil.copy(EXEC_DIR / f, d / f)
    (d / "node_index_exec.py").write_text("import sys, pathlib\npathlib.Path(__file__).with_name('ran.txt').write_text(' '.join(sys.argv[1:]))\n")
    return d


def run_gated(staged, env, **fake):
    e = dict(env)
    e.update({"FAKE_" + k: str(v) for k, v in fake.items()})
    return subprocess.run(["bash", str(staged / "run_gated.sh"), "--dry-run"], capture_output=True, text=True, env=e)


def test_run_gated_execs_the_executor_with_the_args_only_when_the_gate_passes(staged, shims):
    env, _ = shims
    r = run_gated(staged, env, GH_OUT=GH0, PSQL_OUT="0")
    assert r.returncode == 0 and "GATE PASS" in r.stdout
    assert (staged / "ran.txt").read_text() == "--dry-run"


@pytest.mark.parametrize("fake", [dict(GH_OUT='[{"status":"in_progress"}]', PSQL_OUT="0"), dict(GH_OUT=GH0, PSQL_OUT="1"),
                                  dict(GH_OUT=GH0, PSQL_OUT="x"), dict(GH_OUT="", GH_RC=1, PSQL_OUT="0")])
def test_run_gated_does_not_start_the_executor_when_the_gate_fails(staged, shims, fake):
    env, _ = shims
    r = run_gated(staged, env, **fake)
    assert r.returncode != 0 and "executor NOT started" in r.stderr and "GATE FAIL" in r.stdout
    assert not (staged / "ran.txt").exists()
