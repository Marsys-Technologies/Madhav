"""run_gated.sh: gate first, exec the target only on exit 0, args intact, counts on stderr, launch marker only after the gate."""
import json
import os
import subprocess

import pytest

from gate_v2_helpers import runs

ARGS = ["--note", "it's a \"quoted\" arg", "two  words", "*", "$HOME", "`id`", "", "-n", "a;b", "--k=v w"]
OK_LINE = "GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0 role=suvarna_reader OK"


def run_gated(staged, env, args=ARGS, target=None):
    target = target or str(staged / "stub_target.py")
    return subprocess.run(["bash", str(staged / "run_gated.sh"), target] + list(args), capture_output=True, text=True, env=env, timeout=120)


def test_success_execs_the_target_with_args_intact_and_stdout_is_only_the_targets(staged, world):
    r = run_gated(staged, world.env())
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == ARGS                                       # stdout = the executor's JSON, nothing from the gate
    assert json.loads((staged / "ran.json").read_text())["argv"] == ARGS


def test_count_lines_and_the_ok_line_go_to_stderr_and_binaries_are_printed(staged, world):
    r = run_gated(staged, world.env())
    err = r.stderr.split("\n")
    assert "deploy_runs_not_completed=0" in err and "build_runs_in_flight=0" in err and OK_LINE in err
    assert "deploy_runs_not_completed" not in r.stdout
    line = [l for l in err if l.startswith("run_gated: python3=")]
    assert len(line) == 1 and all(("%s=/" % n) in line[0] for n in ("python3", "gh", "psql", "bash"))
    assert err.index(OK_LINE) < [i for i, l in enumerate(err) if "starting target" in l][0]    # gate line precedes the target start


def test_the_binaries_the_gate_uses_are_the_ones_the_wrapper_printed(staged, world):
    r = run_gated(staged, world.env())
    gh = [l for l in r.stderr.split("\n") if l.startswith("run_gated: python3=")][0].split(" gh=")[1].split(" ")[0]
    assert gh == str(world.bin / "gh")


@pytest.mark.parametrize("setup", [
    lambda w: w.gh(history=runs(3) + runs(1, "in_progress", 9000)),
    lambda w: w.psql(count=1),
    lambda w: w.psql(raw="postgres|0\n"),
    lambda w: w.pgenv.unlink(),
    lambda w: w.gh(history=[]),
    lambda w: w.psql(raw="garbage"),
], ids=["deploy-in-flight", "build-in-flight", "wrong-role", "pgenv-missing", "empty-history", "psql-garbage"])
def test_target_is_not_started_on_any_gate_failure_and_the_exit_is_non_zero(staged, world, setup):
    setup(world)
    r = run_gated(staged, world.env())
    assert r.returncode != 0 and "target NOT started" in r.stderr and "GATE_V2 FAIL" in r.stderr
    assert not (staged / "ran.json").exists() and r.stdout == ""


def test_the_gate_exit_code_class_passes_through(staged, world):
    world.pgenv.unlink()
    assert run_gated(staged, world.env()).returncode == 97
    world.pgenv.write_text("export PGUSER=suvarna_reader\n")
    world.psql(raw="postgres|0\n")
    assert run_gated(staged, world.env()).returncode == 96


def test_refuses_the_test_evidence_root_outside_the_harness(staged, world, tmp_path):
    for var in ("ORPH_TEST_EVIDENCE_ROOT", "PYTEST_CURRENT_TEST"):
        r = run_gated(staged, world.operator_env(**{var: str(tmp_path)}))
        assert r.returncode == 95 and "test_env_refused (run_gated.sh)" in r.stderr and var in r.stderr
        assert not (staged / "ran.json").exists()
        assert "gh " not in world.calls()


def test_the_test_flag_bypasses_only_the_env_refusal(staged, world, tmp_path):
    r = run_gated(staged, world.env(ORPH_TEST_EVIDENCE_ROOT=str(tmp_path)))
    assert r.returncode == 0
    world.psql(count=2)
    assert run_gated(staged, world.env(ORPH_TEST_EVIDENCE_ROOT=str(tmp_path))).returncode != 0


def test_no_target_is_a_usage_error(staged, world):
    r = subprocess.run(["bash", str(staged / "run_gated.sh")], capture_output=True, text=True, env=world.env())
    assert r.returncode == 64 and "usage" in r.stderr


def test_a_missing_binary_stops_the_wrapper_before_the_gate_runs(staged, world):
    (world.bin / "gh").unlink()
    env = world.env(PATH=os.pathsep.join([str(world.bin), os.path.dirname(os.sys.executable), "/usr/bin", "/bin"]))
    r = run_gated(staged, env)
    assert r.returncode == 94 and "missing_binary: gh" in r.stderr and not (staged / "ran.json").exists()


# ---------------------------------------------------------------- launch marker
def test_launch_marker_is_set_only_after_the_gate_passes(staged, world):
    r = run_gated(staged, world.env(GATE_V2_LAUNCH="forged"))
    ran = json.loads((staged / "ran.json").read_text())
    assert ran["launch"] and ran["launch"] != "forged" and ran["launch"].startswith("v1.")
    import sys
    sys.path.insert(0, str(staged))
    import importlib
    es = importlib.import_module("executor_standards")
    assert es.verify_marker(ran["launch"], gate_dir=str(staged)) == (True, "ok")


def test_a_pre_set_marker_cannot_survive_a_failed_gate(staged, world):
    world.psql(count=1)
    r = run_gated(staged, world.env(GATE_V2_LAUNCH="forged"))
    assert r.returncode != 0 and not (staged / "ran.json").exists()


def test_args_are_not_word_split_when_the_target_is_a_shell_script(staged, world, tmp_path):
    t = tmp_path / "count_args.sh"
    t.write_text('#!/bin/sh\nprintf "%s" "$#"\n')
    t.chmod(0o755)
    r = run_gated(staged, world.env(), args=["a b", "c  d", "", "e'f"], target=str(t))
    assert r.returncode == 0 and r.stdout == "4"
