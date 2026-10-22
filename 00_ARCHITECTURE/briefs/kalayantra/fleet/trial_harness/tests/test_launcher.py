"""The launcher passes `--gate-entry` / `--budget-s` as SEPARATE arguments under bash AND zsh (the v1 launcher's `${VAR:+--flag $VAR}` stayed one word in zsh, so
argparse saw an unknown option), and the driver's parser knows every option the launcher can pass."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1]
LAUNCHER = Path(os.environ.get("KY_LAUNCHER", HARNESS / "run_trial.sh"))


def dry(shell, **env):
    e = {**os.environ, "TRIAL_DRY_RUN": "1", **env}
    r = subprocess.run([shell, str(LAUNCHER), "/x/checkout", "/x/out"], capture_output=True, text=True, env=e, timeout=30)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


@pytest.mark.parametrize("shell", [s for s in ("bash", "zsh") if shutil.which(s)])
def test_gate_entry_and_budget_are_separate_arguments(shell):
    argv = dry(shell, TRIAL_GATE_ENTRY="pkg.mod:fn", TRIAL_BUDGET_S="300", TRIAL_VERIFY="1", TRIAL_CROSSCHECK="1")
    assert argv[argv.index("--gate-entry") + 1] == "pkg.mod:fn"
    assert argv[argv.index("--budget-s") + 1] == "300"
    assert "--verify" in argv and "--crosscheck" in argv
    assert not any(" " in a for a in argv if a.startswith("--") or a in ("pkg.mod:fn", "300"))


def test_every_launcher_option_is_accepted_by_the_driver_parser():
    import trial_slice
    argv = dry("bash", TRIAL_GATE_ENTRY="pkg.mod:fn", TRIAL_BUDGET_S="300", TRIAL_VERIFY="1", TRIAL_CROSSCHECK="1", TRIAL_CROSSCHECK_SEED="5", TRIAL_PROFILE="/p.json",
               TRIAL_CODE_HEAD="a" * 40, TRIAL_CLASSES="bereavement,major_loss", TRIAL_KEEP_DB="1", TRIAL_DISPATCH_MODULES="/m.json", TRIAL_SOLVER_MODULE="a.b")
    ns = trial_slice.build_parser().parse_args(argv[argv.index("run"):])
    assert ns.gate_entry == "pkg.mod:fn" and ns.budget_s == 300.0 and ns.verify and ns.crosscheck and ns.keep_db
    assert ns.solver_module == "a.b" and ns.crosscheck_seed == 5 and ns.classes == "bereavement,major_loss" and ns.result_policy == "window_qualification/1"


def test_default_classes_are_the_twelve():
    import trial_slice
    assert len(trial_slice.CLASSES) == 12 and len(set(trial_slice.CLASSES)) == 12 and set(trial_slice.ORIGINAL_4) < set(trial_slice.CLASSES)
