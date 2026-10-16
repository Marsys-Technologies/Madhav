"""The required aggregate must actually fail when the layer DB proof fails."""
from pathlib import Path
import os
import subprocess
import sys

import pytest
import yaml

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow


def jobs():
    return expanded_workflow(yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs'])


@pytest.mark.parametrize('db,docs,exit_code', [('success','false',0),('failure','false',1),('cancelled','false',1),('skipped','false',1),('skipped','true',0)])
def test_required_aggregate_earns_its_kala_db_status(db,docs,exit_code):
    gate=jobs()['governance-tool-tests']
    assert 'kala-db-tests' in gate['needs']
    step=gate['steps'][0]
    run=subprocess.run(['bash','-c',step['run']], env={**os.environ,'KALA_DB_RESULT':db,'DOCS_ONLY':docs,
                        'READBACK_RESULT':'success','SHARDS_RESULT':'success'},capture_output=True,text=True,timeout=5)
    assert run.returncode==exit_code,run.stdout+run.stderr


def test_required_shard_selects_bindings_and_database_job_collects_publication():
    all_jobs=jobs()
    steps=all_jobs['governance-tool-tests-shard']['steps']
    assert any('test_k9_publication_bindings.py' in s.get('run','') and not s.get('continue-on-error') for s in steps)
    db=all_jobs['kala-db-tests']
    assert not db.get('continue-on-error')
    steps=[s for s in db['steps'] if 'pytest tests/l3/kala_db ' in s.get('run','')]
    assert len(steps)==1 and str(steps[0]['env']['KALA_REQUIRE_DB'])=='1'
