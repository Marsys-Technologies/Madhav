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
    ci = _ci_text((ROOT / '.github/workflows/ci.yml').read_text())
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
        assert ops[name]['script'] == 'platform/python-sidecar/scripts/kala_gochara_cutover/authority_operation.py'
        assert ops[name + '_dryrun']['enabled'] is False
    # The rejected P09 helper was deferred on main. Do not recreate the B1
    # readiness-only mutation path during this admission-only prebuild.
    assert not (ROOT / 'platform/python-sidecar/services/gochara_kernel/authority_head.py').exists()


from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[5] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow_text as _ci_text


def test_j6mr1_specifies_runner_idempotency_without_changing_applied_sql_or_activation():
    import hashlib
    import yaml

    contract = ROOT / '00_ARCHITECTURE/briefs/kalayantra/J6M_R1_REPLAY_CONTRACT_v1_0.md'
    assert contract.is_file(), 'J6M-R1 needs an explicit replay contract, not an inferred runner exemption'
    metadata = yaml.safe_load(contract.read_text().split('---', 2)[1])
    assert metadata['version'] == '1.0'
    assert metadata['status'] == 'PREBUILD_WAITING_ON_GATE'
    assert metadata['item'] == 'J6M-R1'
    assert metadata['idempotency'] == 'runner_ledger'
    assert metadata['raw_replay_sqlstate'] == '42710'
    assert metadata['requires_catalog_readback'] is True
    assert metadata['activation'] is False
    assert metadata['migration'] == MIGRATION
    assert metadata['migration_sha256'] == hashlib.sha256((ROOT / 'platform/migrations' / MIGRATION).read_bytes()).hexdigest()
