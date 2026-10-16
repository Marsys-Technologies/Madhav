"""A green suite counts only when the required CI job actually collects it."""
from pathlib import Path
import shlex

import yaml


def test_mandatory_kala_db_job_collects_each_adapter_regression():
    root=Path(__file__).resolve().parents[5]
    workflow=_ci_load((root/'.github/workflows/ci.yml').read_text())
    job=workflow['jobs']['kala-db-tests']
    collected=set()
    for step in job['steps']:
        if step.get('env',{}).get('KALA_REQUIRE_DB')!='1': continue
        run=step.get('run','')
        if 'pytest' not in run: continue
        for token in shlex.split(run):
            if not token.startswith('tests/'): continue
            p=root/'platform/python-sidecar'/token
            collected.update(p.rglob('test_*.py') if p.is_dir() else [p])
    own=Path(__file__).parent
    assert {p.resolve() for p in own.glob('test_*.py')} <= {p.resolve() for p in collected}, 'mandatory CI misses KA-3b adapter tests'


def test_migration_is_protected_from_routine_deploy():
    root=Path(__file__).resolve().parents[5]
    entries=(root/'platform/scripts/kala_protected_migrations.txt').read_text().splitlines()
    names={line.strip() for line in entries if line.strip() and not line.startswith('#')}
    assert '1384_ka_3b_contested_candidates.sql' in names

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[5] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow as _ci_expanded

def _ci_load(text):
    import yaml
    data = yaml.safe_load(text)
    data['jobs'] = _ci_expanded(data['jobs'])
    return data
