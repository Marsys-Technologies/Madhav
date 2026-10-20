"""J-6r code-only preparation must not grant production execution authority."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def test_j6r_suites_are_mandatory_fail_closed_and_keep_existing_j6m_paths():
    ci = _ci_text((ROOT / '.github/workflows/ci.yml').read_text())
    step = ci.split('- name: Pravāha A5.3 —', 1)[1].split('\n      - name:', 1)[0]
    assert "GOCHARA_A53_REQUIRE_DB: '1'" in step
    assert 'continue-on-error' not in step
    command = next(line for line in step.splitlines() if 'python -m pytest ' in line)
    for name in ('test_j6r_rehearsal_db.py', 'test_j6r_prebuild_static.py',
                 'test_j6m_authority_admission_db.py', 'test_j6m_prebuild_static.py'):
        assert f'tests/l3/gochara/{name}' in command
    assert '-p no:cacheprovider' in command


def test_enabled_head_kinds_run_only_the_policy_and_nothing_forges_real_rehearsal_acceptance():
    # SR-HEAD-POLICY-KEEP: was "never_enables_executor". Enabled through head_operation.py's policy; the J-6r artifact below is still
    # produced by the real rehearsal, never by this change.
    ops = json.loads((ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json').read_text())['ops']
    for name in ('publish_head', 'rollback_head'):
        assert ops[name]['enabled'] is True
        assert ops[name]['script'] == '00_ARCHITECTURE/briefs/kalayantra/fleet/head_operation.py'
        assert ops[name + '_dryrun']['enabled'] is True
    model = json.loads((ROOT / '00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())
    item = next(row for row in model['items'] if row['id'] == 'J-6r')
    assert item['completion_kind'] == 'artifact'
    assert item['detector']['path'] == '/Users/Dev/kalayantra/run/J6R_REHEARSAL.json'

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[5] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow_text as _ci_text
