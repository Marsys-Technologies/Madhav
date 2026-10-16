"""Keep the J-GOCHARA-TIMEOUT real-SQL oracles in mandatory CI."""
from _ci_gate_test_support import runs_in_full_gate

import copy
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
SUITE = "tests/l3/kala_db/test_gochara_materializer_timeout.py"


def problems(job):
    errors = []
    if "changes" not in ([job.get("needs")] if isinstance(job.get("needs"), str) else job.get("needs", [])) or not runs_in_full_gate(job):
        errors.append("changed job gate")
    if job.get("continue-on-error"):
        errors.append("optional job")
    if not job.get("services", {}).get("postgres"):
        errors.append("no postgres")
    matching = []
    for step in job.get("steps", []):
        args = shlex.split(str(step.get("run", "")))
        if "pytest" not in args:
            continue
        selected = args[args.index("pytest") + 1:]
        if SUITE not in selected and "tests/l3/kala_db" not in selected:
            continue
        matching.append(step)
        if not runs_in_full_gate(step) or step.get("continue-on-error"):
            errors.append("optional step")
        if step.get("working-directory") != "platform/python-sidecar":
            errors.append("wrong working directory")
        env = step.get("env", {})
        if str(env.get("KALA_REQUIRE_DB")) != "1" or not env.get("KALA_ADMIN_DSN"):
            errors.append("DB not required")
        forbidden = {"-k", "-m", "--ignore", "--ignore-glob", "--deselect", "||", "|", ";"}
        if any(arg.split("=")[0] in forbidden or "::" in arg for arg in selected):
            errors.append("filtered or suppressed oracle")
    if not matching:
        errors.append("suite absent")
    return errors


def job():
    return _ci_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]["kala-db-tests"]


def test_timeout_sql_suite_is_in_the_required_database_job():
    assert (ROOT / "platform/python-sidecar" / SUITE).is_file()
    assert not problems(job())


@pytest.mark.parametrize("mutation", ["suite", "require", "dsn", "step", "job", "job-if", "postgres", "filter", "suppress"])
def test_guard_detects_weakened_ci(mutation):
    changed = copy.deepcopy(job())
    step = next(s for s in changed["steps"] if "tests/l3/kala_db" in s.get("run", ""))
    if mutation == "suite":
        step["run"] = step["run"].replace("tests/l3/kala_db", "tests/something_else")
    elif mutation == "require":
        step["env"]["KALA_REQUIRE_DB"] = "0"
    elif mutation == "dsn":
        step["env"].pop("KALA_ADMIN_DSN")
    elif mutation == "step":
        step["if"] = "false"
    elif mutation == "job":
        changed["continue-on-error"] = True
    elif mutation == "job-if":
        changed["if"] = "false"
    elif mutation == "postgres":
        changed["services"].pop("postgres")
    elif mutation == "filter":
        step["run"] += " -k skip_timeout"
    else:
        step["run"] += " || true"
    assert problems(changed), mutation

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[4] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow as _ci_expanded

def _ci_load(text):
    import yaml
    data = yaml.safe_load(text)
    data['jobs'] = _ci_expanded(data['jobs'])
    return data
