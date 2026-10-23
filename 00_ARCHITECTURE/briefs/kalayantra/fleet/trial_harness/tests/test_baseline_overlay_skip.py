"""SR-BASELINE-OVERLAY-SKIP — BASELINE mode (make_baseline.sh) skips a mandatory overlay migration BY NAME only when the checkout also lacks the code that requires it; every trial run still
refuses.  One oracle per distinct claim; the single planted reversion that fails each is named in its docstring.  Evidence of the premise at origin/main c23cda8ab: its
`platform/python-sidecar/services` has no file matching the 1402 probe (job X-20261023T121013Z-baseline-overlay-skip), while the SR-OD1 head cb0c67bcf has several (p1_operands.py, g6_plan.py, ...)."""
import json
import os
import subprocess
from pathlib import Path

import pytest

import trial_slice as ts

HARNESS = Path(__file__).resolve().parents[1]
M1402 = "1402_gochara_qualification_provenance_certificate.sql"
M1403 = "1403_ka_gochara_v5_depends_on_l0_dignity.sql"


def checkout(tmp_path, *, with_1402=False, services=None):
    """A minimal checkout: the migration files (250, 1401 and optionally 1402) and the given production python files under services/."""
    mig = tmp_path / "platform" / "migrations"
    mig.mkdir(parents=True)
    for f, _m, _t in ts.OVERLAY_MIGRATIONS:
        if f in (M1402, M1403) and not (f == M1402 and with_1402):
            continue
        (mig / f).write_text("-- stub\n")
    svc = tmp_path / "platform" / "python-sidecar" / "services" / "gochara_kernel"
    svc.mkdir(parents=True)
    for name, text in (services or {}).items():
        (svc / name).write_text(text)
    return tmp_path


MAIN_LIKE = {"window_sweep.py": "def qualification():\n    return {'policy': 'x'}\n"}                          # origin/main: no writer of the 1402 keys
P1_CODE = {"p1_operands.py": "def combustion_inheritance(table):\n    return {'orb_digest': 'x'}\n"}          # the R-4 writer of `combustion_inheritance`


# ── claim 1: baseline mode, 1402 missing AND its requiring code absent → skipped by name, and the skip is recorded in the baseline ────────────────────────────────────────────────────

def test_baseline_mode_skips_1402_by_name_when_its_requiring_code_is_absent(tmp_path):
    """Reversion: drop the skip branch in plan_overlay (raise Refused for a mandatory file whatever the mode) → Refused here."""
    co = checkout(tmp_path, services=MAIN_LIKE)
    todo, skipped = ts.plan_overlay(co / "platform" / "migrations", lambda t: True, baseline_checkout=co)
    assert [f.split("_", 1)[0] for f in todo] == ["250", "1401"]
    assert M1402 in skipped and "baseline mode" in skipped[M1402] and "no code that requires it" in skipped[M1402]
    assert skipped[M1403] == "absent in the checkout"


def test_the_baseline_file_records_each_skipped_overlay_with_its_reason(tmp_path):
    """Reversion: omit `overlay_skipped` from the baseline written by cmd_baseline → KeyError/None here."""
    from test_driver import full_report
    rep = full_report()
    rep["config"]["baseline_mode"] = True
    rep["lane"] = {"overlay_skipped": {M1402: "baseline mode: absent in the checkout, and the checkout has no code that requires it (SR-BASELINE-OVERLAY-SKIP)"}}
    rp = tmp_path / "rep.json"
    rp.write_text(json.dumps(rep))
    out = tmp_path / "baseline_12.json"
    assert ts.cmd_baseline(ts.build_parser().parse_args(["baseline", "--report", str(rp), "--out", str(out)])) == 0
    b = json.loads(out.read_text())
    assert b["baseline_mode"] is True and list(b["overlay_skipped"]) == [M1402] and "SR-BASELINE-OVERLAY-SKIP" in b["overlay_skipped"][M1402]


# ── claim 2: baseline mode, 1402 missing but the checkout HAS the code that requires it → refuses (the skip is never a blanket) ──────────────────────────────────────────────────

def test_baseline_mode_refuses_when_the_checkout_has_the_code_that_needs_1402(tmp_path):
    """Reversion: make requiring_code() return [] (or skip without probing) → the missing 1402 is skipped and no Refused is raised."""
    co = checkout(tmp_path, services=P1_CODE)
    with pytest.raises(ts.Refused):
        ts.plan_overlay(co / "platform" / "migrations", lambda t: True, baseline_checkout=co)


def test_the_probe_reads_production_python_only_not_tests_or_a_bare_function_name_in_a_test(tmp_path):
    """The 1402 function names appear in main's tests and fleet files (c23cda8ab) without any code needing the migration: a test file must not make the probe fire."""
    co = checkout(tmp_path, services={"test_x.py": "ka_gochara_solver_certificate_ok solver_certificate\n"})
    tdir = co / "platform" / "python-sidecar" / "services" / "tests"
    tdir.mkdir()
    (tdir / "helper.py").write_text("combustion_inheritance\n")
    assert ts.requiring_code(co, M1402) == []


# ── claim 3: a trial run (no baseline mode) still refuses a missing mandatory overlay, exactly as before; baseline mode is explicit and only for default policy + label baseline ──────

def test_a_trial_run_still_refuses_a_missing_1402_even_when_the_requiring_code_is_absent(tmp_path, capsys):
    """Reversion: let plan_overlay skip whenever the code is absent, with no mode argument → this trial-mode call is skipped instead of refused."""
    co = checkout(tmp_path, services=MAIN_LIKE)
    with pytest.raises(ts.Refused):
        ts.plan_overlay(co / "platform" / "migrations", lambda t: True)
    assert f"overlay migration file missing in the checkout: {M1402}" in capsys.readouterr().err


@pytest.mark.parametrize("policy,label", [("window_qualification/1", "baseline"), ("all_null_candidate/1", "baseline"), ("default", "trial")])
def test_baseline_mode_is_refused_outside_default_policy_and_label_baseline(policy, label):
    """Reversion: drop the policy/label guard in baseline_mode_requested → a trial-policy run could ask for the skip."""
    ns = ts.build_parser().parse_args(["run", "--checkout", "/x", "--result-policy", policy, "--out", "/y", "--label", label, "--baseline-mode"])
    with pytest.raises(ts.Refused):
        ts.baseline_mode_requested(ns)
    ok = ts.build_parser().parse_args(["run", "--checkout", "/x", "--result-policy", "default", "--out", "/y", "--label", "baseline", "--baseline-mode"])
    assert ts.baseline_mode_requested(ok) is True
    plain = ts.build_parser().parse_args(["run", "--checkout", "/x", "--result-policy", "default", "--out", "/y", "--label", "baseline"])
    assert ts.baseline_mode_requested(plain) is False


def test_only_make_baseline_sets_the_mode_for_the_launcher():
    """Reversion: remove TRIAL_BASELINE_MODE=1 from make_baseline.sh (or add --baseline-mode to run_trial.sh unconditionally)."""
    env = {**os.environ, "TRIAL_DRY_RUN": "1", "TRIAL_PYTHON": "echo", "TRIAL_CODE_HEAD": "a" * 40}
    env.pop("TRIAL_BASELINE_MODE", None)
    mb = subprocess.run(["bash", str(HARNESS / "make_baseline.sh"), "/x/co", "a" * 40, "/x/out", "/x/b.json"], capture_output=True, text=True, env=env, timeout=30)
    assert mb.returncode == 0, mb.stderr
    argv = mb.stdout.splitlines()
    assert "--baseline-mode" in argv and argv[argv.index("--result-policy") + 1] == "default" and argv[argv.index("--label") + 1] == "baseline"
    tr = subprocess.run(["bash", str(HARNESS / "run_trial.sh"), "/x/co", "/x/out"], capture_output=True, text=True, env=env, timeout=30)
    assert tr.returncode == 0 and "--baseline-mode" not in tr.stdout.splitlines()
