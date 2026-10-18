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


class _Ctx:
    """Attribute view over a dict, so a workflow expression can be evaluated with its own names."""
    def __init__(self, d): self._d = d
    def __getattr__(self, k): return self._d.get(k)


def _evaluate(expr, event, ref, full_gate, db_jobs):
    """Evaluate the `${{ ... }}` subset ci.yml uses (==, &&, ||, contains, fromJSON) on given inputs."""
    import json
    body = expr.strip()[3:-2].strip()
    py = body.replace('&&', ' and ').replace('||', ' or ')
    ctx = {
        'github': _Ctx({'event_name': event, 'ref': ref}),
        'inputs': _Ctx({'full_gate': full_gate}),
        'needs': _Ctx({'changes': _Ctx({'outputs': _Ctx({'db_jobs': json.dumps(db_jobs)})})}),
        'contains': lambda hay, needle: needle in hay,
        'fromJSON': json.loads,
    }
    return bool(eval(py, {'__builtins__': {}}, ctx))


@pytest.mark.parametrize('event,ref,db_jobs,runs', [
    ('merge_group', 'refs/heads/gh-readonly-queue/main/x', ['kala-db-tests'], True),
    ('merge_group', 'refs/heads/gh-readonly-queue/main/x', ['other-job'], False),
    ('pull_request', 'refs/pull/1/merge', ['kala-db-tests'], True),
    ('pull_request', 'refs/pull/1/merge', [], False),
    ('push', 'refs/heads/main', [], True),
])
def test_kala_db_expected_mirrors_the_jobs_own_run_condition(event, ref, db_jobs, runs):
    """The aggregate expects Kala DB Tests exactly when the job's own `if` runs it (B-1: a queue entry
    that does not select the job must not turn the required aggregate red)."""
    all_jobs = yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
    expected = all_jobs['governance-tool-tests']['steps'][0]['env']['KALA_DB_EXPECTED']
    job_if = all_jobs['kala-db-tests']['if'].replace('!cancelled() && ', '', 1)
    assert _evaluate(expected, event, ref, False, db_jobs) is runs
    assert _evaluate(job_if, event, ref, False, db_jobs) is runs
