"""K9-23-N2 real stored-run delegation; no actual orchestrator execution."""
import hashlib
import importlib
import importlib.util
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from psycopg.pq import TransactionStatus

from pipeline.orchestrator import runner as frozen_runner
from services.kala_core.rehearsal import ASSETS, WAVES
from tests.l3.kala_db.manifest.test_publication_lifecycle import publication_connections

CANONICAL = '482012f1-710e-4a25-994a-93821f5871aa'


def operations():
    assert importlib.util.find_spec('services.kala_core.publication'), 'accepted K9 publication entrypoint must be present'
    return importlib.import_module('services.kala_core.publication')


@pytest.fixture
def planned_run(publication_connections):
    caller, executor = publication_connections
    run_id = str(uuid4())
    # K9-23 (K923B): publication._run requires the complete ordered replaceable roster, so the fixture freezes all of it.
    writers = list(ASSETS)
    manifest = dict(version='nirmana-run-manifest/v1',chart_id=CANONICAL,scope='layer',scope_target='L3',
        action='rebuild',waves=[list(wave) for wave in WAVES],assets=[dict(asset_id=w,scope='chart',depends_on=[],
        natural_key_partition=None,has_cowriters=False,expected_code_digest='a'*64) for w in writers])
    digest = hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    caller.execute('CREATE TABLE build_runs (id uuid PRIMARY KEY,chart_id uuid,scope text,scope_target text,'
        'action text,plan jsonb,state text,plan_manifest jsonb,plan_manifest_digest text)')
    caller.execute('INSERT INTO build_runs VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s)',
        (run_id,CANONICAL,'layer','L3','rebuild',json.dumps(writers),'planned',json.dumps(manifest),digest))
    caller.commit()
    return SimpleNamespace(caller=caller,executor=executor,run_id=run_id,assets=','.join(writers))


def session(conn):
    class Session:
        def __enter__(self): return conn
        def __exit__(self,typ,value,tb):
            if typ: conn.rollback()
            else: conn.commit()
    return Session()


@pytest.mark.parametrize('readback', ['completed','planned','failed',None])
def test_rebuild_delegates_the_exact_planned_run_and_requires_completed_readback(planned_run, monkeypatch, capsys, readback):
    ops = operations(); fixture = planned_run; calls = []
    assert fixture.caller.execute('SELECT state FROM build_runs WHERE id=%s',(fixture.run_id,)).fetchone() == ('planned',)
    fixture.caller.commit()
    def execute(run_id):
        calls.append(run_id)
        assert run_id == fixture.run_id
        assert fixture.caller.info.transaction_status == TransactionStatus.IDLE
        assert fixture.executor.execute('SELECT state FROM build_runs WHERE id=%s',(run_id,)).fetchone() == ('planned',)
        if readback is None:
            fixture.executor.execute('DELETE FROM build_runs WHERE id=%s',(run_id,))
        else:
            fixture.executor.execute('UPDATE build_runs SET state=%s WHERE id=%s',(readback,run_id))
        fixture.executor.commit()
    monkeypatch.setattr(frozen_runner,'execute_run',execute)
    monkeypatch.setenv('DATABASE_URL','guarded-local-publication-fixture')
    monkeypatch.setattr(ops.psycopg,'connect',lambda *a,**k:session(fixture.caller))
    result = ops.main(['rebuild','--run-id',fixture.run_id,'--assets',fixture.assets])
    output = json.loads(capsys.readouterr().out)
    assert calls == [fixture.run_id], 'rebuild must delegate exactly once with its frozen run ID'
    if readback == 'completed':
        assert result == 0
        assert output == {'status':'BUILD_COMPLETED','run_id':fixture.run_id}
    else:
        assert result == 2
        assert output['status'] == 'REFUSED'
        assert 'did not complete' in output['reason']
    assert fixture.caller.execute('SELECT generation FROM kala_layer_head').fetchall() == []


def test_rebuild_dryrun_remains_plan_only_without_delegation(planned_run,monkeypatch,capsys):
    ops = operations(); fixture = planned_run; calls = []
    monkeypatch.setattr(frozen_runner,'execute_run',lambda run_id:calls.append(run_id))
    monkeypatch.setenv('DATABASE_URL','guarded-local-publication-fixture')
    monkeypatch.setattr(ops.psycopg,'connect',lambda *a,**k:session(fixture.caller))
    try:
        assert ops.main(['rebuild-dryrun','--run-id',fixture.run_id,'--assets',fixture.assets]) == 0
        output = json.loads(capsys.readouterr().out)
        assert calls == [] and output['status'] == 'PLAN_ONLY' and output['dry_run_passed'] is None
        assert fixture.caller.execute('SELECT state FROM build_runs WHERE id=%s',(fixture.run_id,)).fetchone() == ('planned',)
        fixture.caller.commit()
    finally:
        fixture.caller.rollback()
        fixture.caller.read_only = False
