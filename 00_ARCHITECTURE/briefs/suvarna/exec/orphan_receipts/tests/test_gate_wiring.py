"""v3 wiring: the GATE_V2 files next to the executor, the launch marker, the plan-hash binding and the full run_gated.sh -> executor chain.

No database and no credential: the executor is only ever started with arguments that are refused BEFORE any connection
(an --apply with a wrong --expect-plan), with PATH shims for gh / psql / python3, and with a minimal environment (no gcloud on PATH).
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

import pytest

import fixture_schema as fx

EXEC_DIR = pathlib.Path(__file__).resolve().parent.parent
CANON = fx.CANON
GATE_V2_SHAS = {      # gate_v2 (PR #2938) README, verbatim
    "prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
    "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
    "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135",
}
WRONG_HASH_APPLY = ["--asset", "ga_positions", "--chart", CANON, "--apply", "--expect-plan", "0" * 64, "--expect-evidence", "0" * 64,
                    "--min-build-after", "2026-10-05T09:00:00Z"]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------------ the three gate files
def test_the_gate_files_are_the_byte_identical_gate_v2_files_and_the_executor_pins_them(mod):
    for name, want in GATE_V2_SHAS.items():
        assert sha(EXEC_DIR / name) == want, name
        assert mod.GATE_PINS[name] == want, name
    assert mod.gate_shas() == GATE_V2_SHAS
    assert mod.es.fingerprint() == {"gate_sha256": GATE_V2_SHAS["prerun_gate.py"], "run_gated_sha256": GATE_V2_SHAS["run_gated.sh"]}
    assert os.access(EXEC_DIR / "run_gated.sh", os.X_OK) and os.access(EXEC_DIR / "prerun_gate.py", os.X_OK)
    assert 'GATE_VERSION = "GATE_V2"' in (EXEC_DIR / "prerun_gate.py").read_text()
    assert not (EXEC_DIR / "tests" / "test_prerun_gate.py").exists()           # the v1 gate and its tests are gone


def test_the_executor_loads_the_standards_that_sit_next_to_it(mod):
    assert pathlib.Path(mod.es.__file__).resolve() == (EXEC_DIR / "executor_standards.py").resolve()
    assert mod.es.HERE == str(EXEC_DIR) or pathlib.Path(mod.es.HERE).resolve() == EXEC_DIR.resolve()


# ------------------------------------------------------------------------------------------------ plan hash binds the gate
def test_changing_any_gate_file_sha_changes_the_plan_hash(mod):
    base = mod.plan_hash("ga_positions", CANON)
    for name in GATE_V2_SHAS:
        other = dict(GATE_V2_SHAS, **{name: "0" * 64})
        assert mod.plan_hash("ga_positions", CANON, gate=other) != base, name
    # the two files bind_gate_into_plan_hash() folds in: also when the plan text were left alone
    unbound = mod.plan_hash_unbound("ga_positions", CANON)
    fp = mod.es.fingerprint()
    assert mod.es.bind_gate_into_plan_hash(unbound, fp) == base
    assert mod.es.bind_gate_into_plan_hash(unbound, dict(fp, gate_sha256="1" * 64)) != base
    assert mod.es.bind_gate_into_plan_hash(unbound, dict(fp, run_gated_sha256="1" * 64)) != base


def test_plan_text_names_the_three_gate_shas_and_the_binding(mod):
    text = (EXEC_DIR / "plan.txt").read_text()
    for name, h in GATE_V2_SHAS.items():
        assert "%s sha256 %s" % (name, h) in text
    assert "bind_gate_into_plan_hash" in text and "GATE_V2_LAUNCH" in text and "outcome.json" in text and "exit 93" in text


def test_plan_md_and_readme_quote_the_gate_shas_and_the_v3_hashes(mod):
    md = (EXEC_DIR / "PLAN.md").read_text()
    readme = (EXEC_DIR / "README.md").read_text()
    for h in GATE_V2_SHAS.values():
        assert h in md and h in readme
    assert mod.exec_sha() in md and mod.plan_hash("ga_positions", CANON) in md
    assert "29a9e1e5d08a006c1f58255a61cf8c7f6c1e0d0138279268500b33250d3e9967" in md           # v1.1 kept as history
    assert "de4aad0cdec65ed91c2f1569a658008c0fa1b8eae24b1fd0849c19f656aef9d2" in md


# ------------------------------------------------------------------------------------------------ launch_gate(): marker verification
def marker(now=None, gate_dir=EXEC_DIR):
    return mod_es().make_marker(str(gate_dir / "prerun_gate.py"), str(gate_dir / "run_gated.sh"), now=now)


def mod_es():
    import conftest
    return conftest.load_exec().es


def refused_with(mod, capsys, environ, reason):
    with pytest.raises(SystemExit) as e:
        mod.launch_gate(environ)
    assert e.value.code == 93
    err = capsys.readouterr().err
    assert "REFUSED" in err and reason in err
    return err


def test_launch_gate_refuses_without_a_marker(mod, capsys):
    refused_with(mod, capsys, {}, "no_marker")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": ""}, "no_marker")


def test_launch_gate_accepts_a_marker_made_by_the_launcher_for_the_live_files(mod):
    fp = mod.launch_gate({"GATE_V2_LAUNCH": marker()})
    assert fp == {"gate_sha256": GATE_V2_SHAS["prerun_gate.py"], "run_gated_sha256": GATE_V2_SHAS["run_gated.sh"], "under_test": False}


def test_launch_gate_refuses_a_forged_or_tampered_marker(mod, capsys):
    m = marker()
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": m[:-1] + ("0" if m[-1] != "0" else "1")}, "marker_check_mismatch")   # check digit
    parts = m.split(".")
    parts[3] = str(int(parts[3]) + 1)                                          # epoch edited, check not recomputed
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": ".".join(parts)}, "marker_check_mismatch")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": "garbage"}, "malformed_marker")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": "v2.a.b.c.d.e.f"}, "malformed_marker")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": "v1." + "0." * 4 + "0"}, "malformed_marker")                   # the old marker format


def test_launch_gate_refuses_an_under_test_marker_outside_the_harness_and_records_it_inside(mod, capsys):
    ut = mod_es().make_marker(str(EXEC_DIR / "prerun_gate.py"), str(EXEC_DIR / "run_gated.sh"), under_test=True)
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": ut}, "under_test_marker_refused_outside_tests")
    for env in ({"GATE_V2_UNDER_TEST": "1"}, {"PYTEST_CURRENT_TEST": "x"}):
        assert mod.launch_gate(dict(env, GATE_V2_LAUNCH=ut))["under_test"] is True
    forged = ut.split(".")
    forged[5] = "0"                                                            # replayed as a production marker: the check no longer matches
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": ".".join(forged)}, "marker_check_mismatch")


def test_launch_gate_refuses_a_stale_or_future_marker(mod, capsys):
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": marker(now=time.time() - 7 * 3600)}, "marker_stale")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": marker(now=time.time() + 600)}, "marker_from_the_future")


def test_launch_gate_refuses_a_marker_for_a_different_gate_file(mod, capsys, tmp_path):
    """A marker made over an EDITED copy of the gate verifies in itself but not against the live file next to the executor."""
    d = tmp_path / "edited"
    d.mkdir()
    for n in ("prerun_gate.py", "run_gated.sh"):
        shutil.copy(EXEC_DIR / n, d / n)
    (d / "prerun_gate.py").write_text((d / "prerun_gate.py").read_text() + "\n# edited\n")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": marker(gate_dir=d)}, "gate_sha_differs_from_live_gate_file")
    shutil.copy(EXEC_DIR / "prerun_gate.py", d / "prerun_gate.py")
    (d / "run_gated.sh").write_text((d / "run_gated.sh").read_text() + "\n# edited\n")
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": marker(gate_dir=d)}, "launcher_sha_differs_from_live_run_gated")


def test_launch_gate_refuses_when_the_live_files_differ_from_the_pins(mod, capsys, monkeypatch):
    """The executor pins the sha256 of the gate files it was reviewed with (and the plan hash binds them): a gate replaced
    after review is refused even by a marker that verifies against the live files."""
    m = marker()
    monkeypatch.setitem(mod.GATE_PINS, "prerun_gate.py", "0" * 64)
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": m}, "gate_sha_differs_from_plan")
    monkeypatch.setitem(mod.GATE_PINS, "prerun_gate.py", GATE_V2_SHAS["prerun_gate.py"])
    monkeypatch.setitem(mod.GATE_PINS, "run_gated.sh", "0" * 64)
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": m}, "launcher_sha_differs_from_plan")
    monkeypatch.setitem(mod.GATE_PINS, "run_gated.sh", GATE_V2_SHAS["run_gated.sh"])
    monkeypatch.setitem(mod.GATE_PINS, "executor_standards.py", "0" * 64)
    refused_with(mod, capsys, {"GATE_V2_LAUNCH": m}, "executor_standards.py differs from the version pinned")


# ------------------------------------------------------------------------------------------------ the real CLI, as a subprocess
def clean_env(tmp_path, **extra):
    """Minimal environment: python via an absolute path, NO gcloud/gh/psql on PATH, HOME inside tmp (no ~/.config)."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1"}
    env.update(extra)
    return env


def cli(tmp_path, argv=None, **env):
    return subprocess.run([sys.executable, str(EXEC_DIR / "orphan_receipts_exec.py")] + (argv or WRONG_HASH_APPLY), capture_output=True,
                          text=True, env=clean_env(tmp_path, **env), timeout=60)


def test_cli_started_directly_is_refused_93_and_creates_nothing(tmp_path):
    ev = tmp_path / "ev"
    r = cli(tmp_path, ORPH_TEST_EVIDENCE_ROOT=str(ev), PYTEST_CURRENT_TEST="x")
    assert r.returncode == 93, r.stderr
    assert "not launched by run_gated.sh" in r.stderr and "no_marker" in r.stderr
    assert r.stdout == "" and not ev.exists()
    r = cli(tmp_path, ["--help"])                                                # even --help: the launch check is FIRST
    assert r.returncode == 93


def test_cli_with_a_valid_marker_proceeds_past_the_launch_check_and_records_the_refusal(tmp_path):
    ev = tmp_path / "ev"
    r = cli(tmp_path, GATE_V2_LAUNCH=marker(), ORPH_TEST_EVIDENCE_ROOT=str(ev), PYTEST_CURRENT_TEST="x")
    assert r.returncode == 1 and "REFUSED: --expect-plan does not equal the plan hash" in r.stderr, r.stderr
    (d,) = list(ev.iterdir())
    o = json.loads((d / "outcome.json").read_text())
    assert o["status"] == "failed" and o["failed_checks"] == ["args_expect_plan_mismatch"]
    assert o["gate_sha256"] == GATE_V2_SHAS["prerun_gate.py"] and o["run_gated_sha256"] == GATE_V2_SHAS["run_gated.sh"]
    assert o["under_test"] is False and o["warnings"] == []


def test_cli_refuses_an_under_test_marker_in_an_operators_environment(tmp_path):
    ut = mod_es().make_marker(str(EXEC_DIR / "prerun_gate.py"), str(EXEC_DIR / "run_gated.sh"), under_test=True)
    ev = tmp_path / "ev"
    r = cli(tmp_path, GATE_V2_LAUNCH=ut)                                        # no GATE_V2_UNDER_TEST, no PYTEST_CURRENT_TEST
    assert r.returncode == 93 and "under_test_marker_refused_outside_tests" in r.stderr and not ev.exists()


def test_cli_refuses_an_under_test_launch_outside_pytest_even_with_a_marker_the_verifier_accepts(tmp_path):
    """GATE_V2_UNDER_TEST=1 in the operator's shell makes the verifier accept an under_test marker; the executor still refuses it
    (no PYTEST_CURRENT_TEST): exit 93 before the arguments are parsed, no evidence directory, no database."""
    ut = mod_es().make_marker(str(EXEC_DIR / "prerun_gate.py"), str(EXEC_DIR / "run_gated.sh"), under_test=True)
    ev = tmp_path / "ev"
    r = cli(tmp_path, GATE_V2_LAUNCH=ut, GATE_V2_UNDER_TEST="1", GATE_V2_PGENV="/nonexistent")
    assert r.returncode == 93 and "ran under test" in r.stderr and r.stdout == "" and not ev.exists()
    for argv in (["--asset", "ga_positions", "--chart", CANON, "--dry-run"], WRONG_HASH_APPLY):
        assert cli(tmp_path, argv, GATE_V2_LAUNCH=ut, GATE_V2_UNDER_TEST="1").returncode == 93


def test_cli_refuses_the_stray_evidence_root_variable_with_exit_95(tmp_path):
    ev = tmp_path / "stray"
    r = cli(tmp_path, GATE_V2_LAUNCH=marker(), ORPH_TEST_EVIDENCE_ROOT=str(ev))        # no PYTEST_CURRENT_TEST: an operator's shell
    assert r.returncode == 95, r.stderr
    assert "ORPH_TEST_EVIDENCE_ROOT is set outside a pytest run" in r.stderr and not ev.exists()
    r = cli(tmp_path, GATE_V2_LAUNCH=marker(), ORPH_TEST_EVIDENCE_ROOT="")              # set but empty is refused too
    assert r.returncode == 95


def staged_copy(tmp_path):
    d = tmp_path / "copy"
    shutil.copytree(EXEC_DIR, d, ignore=shutil.ignore_patterns("__pycache__", "tests", ".pytest_cache"))
    return d


def test_cli_refuses_an_edited_executor_standards_file_even_with_a_marker_for_it(tmp_path):
    d = staged_copy(tmp_path)
    (d / "executor_standards.py").write_text((d / "executor_standards.py").read_text() + "\n# edited after review\n")
    m = mod_es().make_marker(str(d / "prerun_gate.py"), str(d / "run_gated.sh"))
    r = subprocess.run([sys.executable, str(d / "orphan_receipts_exec.py")] + WRONG_HASH_APPLY, capture_output=True, text=True, timeout=60,
                       env=clean_env(tmp_path, GATE_V2_LAUNCH=m, ORPH_TEST_EVIDENCE_ROOT=str(tmp_path / "ev"), PYTEST_CURRENT_TEST="x"))
    assert r.returncode == 93 and "executor_standards.py differs from the version pinned" in r.stderr and not (tmp_path / "ev").exists()


def test_cli_refuses_an_edited_gate_file_even_with_a_marker_for_it(tmp_path):
    d = staged_copy(tmp_path)
    (d / "prerun_gate.py").write_text((d / "prerun_gate.py").read_text() + "\n# edited after review\n")
    m = mod_es().make_marker(str(d / "prerun_gate.py"), str(d / "run_gated.sh"))
    r = subprocess.run([sys.executable, str(d / "orphan_receipts_exec.py")] + WRONG_HASH_APPLY, capture_output=True, text=True, timeout=60,
                       env=clean_env(tmp_path, GATE_V2_LAUNCH=m, ORPH_TEST_EVIDENCE_ROOT=str(tmp_path / "ev"), PYTEST_CURRENT_TEST="x"))
    assert r.returncode == 93 and "gate_sha_differs_from_plan" in r.stderr and not (tmp_path / "ev").exists()


# ------------------------------------------------------------------------------------------------ run_gated.sh -> executor, end to end (PATH shims)
@pytest.fixture()
def shims(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    (b / "python3").write_text('#!/bin/sh\nexec "%s" "$@"\n' % sys.executable)
    for name, default in (("gh", '[{"databaseId":1,"status":"completed","event":"workflow_run"}]'), ("psql", "suvarna_reader|amjis|0")):
        (b / name).write_text("#!/bin/sh\nout='%s'\nprintf '%%s\\n' \"${FAKE_%s_OUT:-$out}\"\n" % (default, name.upper()))
    for f in b.iterdir():
        f.chmod(0o755)
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("# fake: nothing exported\n")
    return b, pgenv


def run_gated(tmp_path, shims, target_args, **extra):
    b, pgenv = shims
    env = {"PATH": "%s:/usr/bin:/bin" % b, "HOME": str(tmp_path / "home"), "GATE_V2_UNDER_TEST": "1", "GATE_V2_PGENV": str(pgenv),
           "ORPH_TEST_EVIDENCE_ROOT": str(tmp_path / "ev"), "PYTEST_CURRENT_TEST": "x", "PYTHONDONTWRITEBYTECODE": "1"}
    env.update(extra)
    return subprocess.run(["bash", str(EXEC_DIR / "run_gated.sh"), "python3", str(EXEC_DIR / "orphan_receipts_exec.py")] + target_args,
                          capture_output=True, text=True, env=env, timeout=120)


def test_run_gated_sets_the_marker_and_the_executor_accepts_it(tmp_path, shims):
    r = run_gated(tmp_path, shims, WRONG_HASH_APPLY)
    assert "gate OK; GATE_V2_LAUNCH set; starting target" in r.stderr and "GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0" in r.stderr
    assert r.returncode == 1 and "REFUSED: --expect-plan does not equal the plan hash" in r.stderr, r.stderr   # past the launch check, then refused
    (d,) = list((tmp_path / "ev").iterdir())
    o = json.loads((d / "outcome.json").read_text())
    assert o["failed_checks"] == ["args_expect_plan_mismatch"]
    assert o["under_test"] is True                                              # run_gated.sh ran with GATE_V2_UNDER_TEST=1: recorded via the marker


@pytest.mark.parametrize("fake,why", [(dict(FAKE_PSQL_OUT="suvarna_reader|amjis|1"), "in_flight"),
                                      (dict(FAKE_GH_OUT='[{"databaseId":1,"status":"in_progress","event":"workflow_run"}]'), "in_flight"),
                                      (dict(FAKE_PSQL_OUT="postgres|amjis|0"), "wrong_role_or_database")], ids=["build-in-flight", "deploy-in-flight", "wrong-role"])
def test_run_gated_does_not_start_the_executor_when_the_gate_blocks(tmp_path, shims, fake, why):
    r = run_gated(tmp_path, shims, WRONG_HASH_APPLY, **fake)
    assert r.returncode != 0 and "target NOT started" in r.stderr
    assert "GATE_V2 FAIL %s" % why in r.stderr, r.stderr                         # blocked for the RIGHT reason, not a broken shim
    assert not (tmp_path / "ev").exists()                                       # the executor never ran: no evidence dir, no outcome


def test_the_gate_refuses_the_test_evidence_variable_in_an_operators_shell(tmp_path, shims):
    r = run_gated(tmp_path, shims, WRONG_HASH_APPLY, GATE_V2_UNDER_TEST="0")
    assert r.returncode == 95 and "test_env_refused" in r.stderr and not (tmp_path / "ev").exists()
