"""CI-SCOPE-EXECUTOR: an executor / ops-table / kyd_kinds change runs the p01 smalltest-operations suite on the PR.

Oracle: the repo's own PR resolver (ci_gate.select_db over the real ci.yml jobs and the real profiles), not a
re-implementation. Rule source: surrogate loop-gap ruling after PR #3722, which changed fleet/executor.py yet ran
test_p01_smalltest_operations.py only in the merge queue.
"""
from pathlib import Path
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
import ci_discovery  # noqa: E402
import ci_gate  # noqa: E402

P01 = 'scripts/__tests__/test_p01_smalltest_operations.py'
FLEET = '00_ARCHITECTURE/briefs/kalayantra/fleet'


def jobs():
    return yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']


def p01_profile():
    owners = [name for name, spec in ci_discovery.profiles().items()
              if spec['engine'] == 'pytest' and spec['cwd'] == 'platform'
              and P01 in ci_discovery.discover(ROOT, spec)
              and name in ci_gate.db_profile_owners(jobs())]
    assert len(owners) == 1, owners
    return owners[0]


@pytest.mark.parametrize('changed', [
    f'{FLEET}/executor.py',
    f'{FLEET}/executor_ops.json',
    f'{FLEET}/kyd_kinds_ops.py',
])
def test_executor_family_change_selects_the_p01_suite_on_a_pull_request(changed):
    selected_jobs, selected_profiles = ci_gate.select_db(ROOT, jobs(), [changed])
    profile = p01_profile()
    assert profile in selected_profiles
    assert set(ci_gate.db_profile_owners(jobs())[profile]) <= set(selected_jobs)


def test_unrelated_fleet_file_does_not_select_the_p01_suite():
    _, selected_profiles = ci_gate.select_db(ROOT, jobs(), [f'{FLEET}/executor.env.example.sh'])
    assert p01_profile() not in selected_profiles
