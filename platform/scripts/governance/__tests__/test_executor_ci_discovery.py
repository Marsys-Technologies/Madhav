"""FU-SEED-N01: the required governance job must run executor regressions.

PR #3588 supplies the discovery runner before this stacked change lands.
"""
import importlib.util
import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[4]
TOOL = ROOT / "platform/scripts/governance/ci_discovery.py"
SUITE = "governance-tool-tests-shard-5-0"
EXECUTOR_TEST = "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_executor_table.py"


@pytest.fixture
def discovery():
    if not TOOL.is_file():
        pytest.skip("requires PR #3588 discovery infrastructure before stacked landing")
    spec = importlib.util.spec_from_file_location("executor_ci_discovery", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_required_governance_step_discovers_executor_regressions(discovery):
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]
    job = jobs["governance-tool-tests-shard"]
    steps = [step for step in job["steps"]
             if f'ci_discovery.py" pytest {SUITE} --' in step.get("run", "")]
    assert len(steps) == 1
    assert steps[0].get("if") == "matrix.shard == 1"
    assert 1 in job["strategy"]["matrix"]["shard"]
    assert not steps[0].get("continue-on-error", False)
    assert not job.get("continue-on-error", False)
    assert "governance-tool-tests-shard" in jobs["governance-tool-tests"]["needs"]
    profile = discovery.profiles()[SUITE]
    assert profile["cwd"] == "." and profile["engine"] == "pytest"
    selected = discovery.discover(ROOT, profile)
    assert EXECUTOR_TEST in selected, "required CI omits the executor scratch regressions"
    assert "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_operation_adapters.py" in selected
    assert "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_operation_dryrun.py" in selected


def test_executor_profile_discovers_new_family_files(discovery, tmp_path):
    profile = json.loads(TOOL.with_name("ci_test_suites.json").read_text())["suites"][SUITE]
    directory = tmp_path / "00_ARCHITECTURE/briefs/kalayantra/fleet/tests"
    directory.mkdir(parents=True)
    for name in ("test_operation_future.py", "test_executor_future.py", "test_unrelated.py"):
        (directory / name).write_text("def test_example(): pass\n")
    assert discovery.discover(tmp_path, profile) == [
        "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_executor_future.py",
        "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_operation_future.py",
    ]
