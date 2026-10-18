"""The required aggregate must actually fail when the layer DB proof fails."""
from pathlib import Path
import json
import os
import subprocess

import pytest
import yaml

ROOT=Path(__file__).resolve().parents[4]


def jobs():
    return yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']


@pytest.mark.parametrize('db,docs,expected,exit_code', [('success','false','true',0),('failure','false','true',1),('cancelled','false','true',1),('skipped','false','true',1),
                         ('skipped','true','true',0),('skipped','false','false',0),('failure','false','false',1),('cancelled','false','false',1)])
def test_required_aggregate_earns_its_kala_db_status(db,docs,expected,exit_code):
    gate=jobs()['governance-tool-tests']
    assert 'kala-db-tests' in gate['needs']
    step=gate['steps'][0]
    run=subprocess.run(['bash','-c',step['run']], env={**os.environ,'KALA_DB_RESULT':db,'KALA_DB_EXPECTED':expected,'DOCS_ONLY':docs,
                        'READBACK_RESULT':'success','SHARDS_RESULT':'success','J5S_RESULT':'success','J5S_EXPECTED':'true'},capture_output=True,text=True,timeout=5)
    assert run.returncode==exit_code,run.stdout+run.stderr


def test_required_shard_selects_bindings_and_database_job_collects_publication():
    all_jobs=jobs()
    import importlib.util
    spec=importlib.util.spec_from_file_location('k923_ci_shard',ROOT/'platform/scripts/governance/ci_shard.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert ROOT/'platform/scripts/governance/__tests__/test_k923b_bindings.py' in mod.test_files()
    # Directory discovery collects the new DB tests. No explicit CI paths added.
    db=all_jobs['kala-db-tests']
    assert not db.get('continue-on-error')
    # Since the pattern-discovery CI (A5 D-33) the job runs profile kala-db-tests-5-0, whose directory list is what collects tests/l3/kala_db.
    steps=[s for s in db['steps'] if 'ci_discovery.py' in s.get('run','') and 'pytest kala-db-tests-5-0 ' in s.get('run','')]
    assert len(steps)==1 and str(steps[0]['env']['KALA_REQUIRE_DB'])=='1'
    profile=json.loads((ROOT/'platform/scripts/governance/ci_test_suites.json').read_text())['suites']['kala-db-tests-5-0']
    assert 'tests/l3/kala_db' in profile['directories'] and profile['cwd']=='platform/python-sidecar'


def test_expected_flag_is_the_same_selection_the_kala_db_job_runs_under():
    """B1 (review of #3645): a skip is only red when the job's own `if` would have run it; ci_gate selects it only for Kāla DB paths."""
    all_jobs=jobs()
    expected=str(all_jobs['governance-tool-tests']['steps'][0]['env']['KALA_DB_EXPECTED']).replace('${{','').replace('}}','')
    cond=str(all_jobs['kala-db-tests']['if']).replace('${{','').replace('}}','').replace('!cancelled() &&','')
    norm=lambda t:''.join(t.split()).replace('(','').replace(')','')  # grouping differs; the clauses must not
    assert norm(expected)==norm(cond)
