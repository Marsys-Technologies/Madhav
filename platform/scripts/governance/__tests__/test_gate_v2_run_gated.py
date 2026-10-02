"""run_gated.sh: gate first, exec the target only on exit 0, args intact, counts on stderr, launch marker only after the gate."""
import json
import os
import pathlib
import subprocess

import pytest

from gate_v2_helpers import runs, staged, world  # noqa: F401

ARGS = ["--note", "it's a \"quoted\" arg", "two  words", "*", "$HOME", "`id`", "", "-n", "a;b", "--k=v w"]
OK_LINE = "GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0 role=suvarna_reader OK"


def run_gated(staged, env, args=ARGS, target=None):
    target = str(staged / "stub_target.py") if target is None else target
    return subprocess.run(["/bin/bash", str(staged / "run_gated.sh"), target] + list(args), capture_output=True, text=True, env=env, timeout=120)


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
    lambda w: w.psql(raw="postgres|amjis|0\n"),
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
    world.pgenv.write_text("export PGUSER=suvarna_reader\nexport PGDATABASE=amjis\n")
    world.psql(raw="postgres|amjis|0\n")
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
    r = subprocess.run(["/bin/bash", str(staged / "run_gated.sh")], capture_output=True, text=True, env=world.env())
    assert r.returncode == 64 and "usage" in r.stderr


def test_a_missing_binary_stops_the_wrapper_before_the_gate_runs(staged, world):
    (world.bin / "gh").unlink()
    env = world.env(PATH=os.pathsep.join([str(world.bin), str(world.tools)]))      # no runner-provided gh anywhere on PATH
    r = run_gated(staged, env)
    assert r.returncode == 94 and "missing_binary: gh" in r.stderr and not (staged / "ran.json").exists()


# ---------------------------------------------------------------- launch marker
def test_launch_marker_is_set_only_after_the_gate_passes(staged, world):
    r = run_gated(staged, world.env(GATE_V2_LAUNCH="forged"))
    ran = json.loads((staged / "ran.json").read_text())
    assert ran["launch"] and ran["launch"] != "forged" and ran["launch"].startswith("v2.")
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


# ---------------------------------------------------------------- the target must be executable (exit 98), and `--` protects a dash-named target
def stub_env_bin(tmp_path, name, body="#!/bin/sh\nprintf '%s' \"$#\"\n"):
    d = tmp_path / "extra_bin"
    d.mkdir(exist_ok=True)
    (d / name).write_text(body)
    (d / name).chmod(0o755)
    return d


def test_a_target_whose_name_starts_with_a_dash_is_not_taken_for_an_exec_option(staged, world, tmp_path):
    d = stub_env_bin(tmp_path, "-dashcmd")
    env = world.env(PATH=os.pathsep.join([str(d), world.env()["PATH"]]))
    r = run_gated(staged, env, args=["a", "b"], target="-dashcmd")
    assert r.returncode == 0 and r.stdout == "2", r.stderr


@pytest.mark.parametrize("make", [
    lambda t: str(t / "no_such_file"),                                        # missing path
    lambda t: "no_such_command_xyz",                                          # missing name (not in PATH)
    lambda t: str(t),                                                         # a directory
    lambda t: "",                                                             # empty string
], ids=["missing-path", "missing-name", "directory", "empty"])
def test_a_missing_or_non_executable_target_exits_98_before_the_gate_and_before_any_ok_line(staged, world, tmp_path, make):
    r = run_gated(staged, world.env(), args=["x"], target=make(tmp_path))
    assert r.returncode == 98, r.stderr
    assert "GATE_V2 FAIL target_not_executable" in r.stderr.split("\n")
    assert "gate OK" not in r.stderr and "starting target" not in r.stderr and "OK" not in r.stderr.replace("NOT", "")
    assert world.calls() == ""                                                # no gh / psql call: refused before the gate


def test_a_file_without_the_execute_bit_exits_98(staged, world, tmp_path):
    f = tmp_path / "plain.sh"
    f.write_text("#!/bin/sh\necho hi\n")
    f.chmod(0o644)
    r = run_gated(staged, world.env(), args=[], target=str(f))
    assert r.returncode == 98 and "GATE_V2 FAIL target_not_executable" in r.stderr


def test_a_target_that_cannot_be_exec_ed_after_the_check_exits_98_not_1(staged, world, tmp_path):
    f = tmp_path / "badshebang.sh"
    f.write_text("#!/nonexistent/interpreter\necho hi\n")
    f.chmod(0o755)
    r = run_gated(staged, world.env(), args=[], target=str(f))
    assert r.returncode == 98 and r.stderr.strip().split("\n")[-1] == "GATE_V2 FAIL target_not_executable"


def test_a_target_given_by_name_in_path_runs(staged, world, tmp_path):
    r = run_gated(staged, world.env(), args=[str(staged / "stub_target.py"), "x y"], target="python3")   # python3 = symlink in the tools dir on PATH
    assert r.returncode == 0 and json.loads(r.stdout) == ["x y"], r.stderr


def test_exit_code_98_is_documented_and_distinct_from_the_gate_codes(staged, world):
    readme = (pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/suvarna/exec/gate_v2/README.md").read_text()
    assert "| 98 |" in readme and "target_not_executable" in readme
    assert 98 not in (0, 1, 2, 64, 93, 94, 95, 96, 97)


# ---------------------------------------------------------------- the under_test flag is in the launch marker
def marker_parts(staged):
    return json.loads((staged / "ran.json").read_text())["launch"].split(".")


def test_an_under_test_launch_marks_the_marker_under_test_and_a_production_verifier_refuses_it(staged, world):
    import sys
    sys.path.insert(0, str(staged))
    import importlib
    es = importlib.import_module("executor_standards")
    run_gated(staged, world.env())                                            # GATE_V2_UNDER_TEST=1 in world.env()
    p = marker_parts(staged)
    assert len(p) == 7 and p[0] == "v2" and p[5] == "1"
    m = ".".join(p)
    assert es.verify_marker(m, gate_dir=str(staged), environ={"GATE_V2_UNDER_TEST": "1"}) == (True, "ok")
    assert es.verify_marker(m, gate_dir=str(staged), environ={}) == (False, "under_test_marker_refused_outside_tests")


def test_a_production_launch_marks_the_marker_not_under_test(staged, world):
    import sys
    sys.path.insert(0, str(staged))
    import importlib
    es = importlib.import_module("executor_standards")
    (world.home / ".config" / "suvarna" / "pgenv.sh").write_text(world.pgenv.read_text())      # the production pgenv path under HOME
    r = run_gated(staged, world.operator_env())
    assert r.returncode == 0, r.stderr
    assert "WARNING under_test" not in r.stderr
    p = marker_parts(staged)
    assert len(p) == 7 and p[5] == "0"
    assert es.verify_marker(".".join(p), gate_dir=str(staged), environ={}) == (True, "ok")
