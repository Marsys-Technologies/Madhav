"""J-6m protected deployment and mandatory regression coverage boundaries."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MIGRATION = '1382_gochara_authority_no_truncate.sql'
SUITES = ('test_j6m_authority_admission_db.py', 'test_j6m_prebuild_static.py')


def test_authority_followup_is_protected_and_has_no_pointer_dml():
    sql = (ROOT / 'platform/migrations' / MIGRATION).read_text()
    protected = (ROOT / 'platform/scripts/kala_protected_migrations.txt').read_text().splitlines()
    assert protected.count(MIGRATION) == 1
    # DDL-only followup: reuse the family guard, with runner-owned transaction.
    code = '\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
    assert 'BEFORE TRUNCATE ON public.kala_gochara_authority' in code
    assert 'ENABLE ALWAYS TRIGGER kala_gochara_authority_no_truncate' in code
    import re
    assert not re.search(r'\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(public\.)?kala_gochara_authority\b', code, re.I)
    assert not re.search(r'^\s*(BEGIN|COMMIT)\s*;', code, re.M)


def test_both_j6m_suites_run_in_mandatory_fail_closed_db_step():
    ci = (ROOT / '.github/workflows/ci.yml').read_text()
    step = ci.split('- name: Pravāha A5.3 —', 1)[1].split('\n      - name:', 1)[0]
    assert "GOCHARA_A53_REQUIRE_DB: '1'" in step
    assert 'continue-on-error' not in step
    command = next(line for line in step.splitlines() if 'python -m pytest ' in line)
    for suite in SUITES:
        assert f'tests/l3/gochara/{suite}' in command
    assert '-p no:cacheprovider' in command


def test_prebuild_preserves_disabled_authority_operations_and_deferred_helper():
    ops = json.loads((ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json').read_text())['ops']
    for name in ('publish_head', 'rollback_head'):
        assert ops[name]['enabled'] is False
        assert ops[name]['script'].startswith('TO_BE_SET_')
    # The rejected P09 helper was deferred on main. Do not recreate the B1
    # readiness-only mutation path during this admission-only prebuild.
    assert not (ROOT / 'platform/python-sidecar/services/gochara_kernel/authority_head.py').exists()
