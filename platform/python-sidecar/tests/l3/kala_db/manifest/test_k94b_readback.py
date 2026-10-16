"""K9-4b request-prep SQL is one executable SELECT, with digest-bound bytes."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

import psycopg
import pytest

FLEET = Path(__file__).resolve().parents[6] / '00_ARCHITECTURE/briefs/kalayantra/fleet'


def prep():
    import importlib.util
    spec=importlib.util.spec_from_file_location('k94b_prep',FLEET/'k9_readback.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def request():
    return dict(item_id='K9-4b',kind='readback_sql',operation_id='k94b-readback',
                reviewed_commit='a'*40,args={'sql_file':'run/ops/sql/k94b.sql'})


def test_prep_binds_single_select_wrapper_into_request_digest():
    m=prep(); original=request()
    result=m.prepare_readback(original, readback_sql="SELECT jsonb_build_object('passed', true) AS evidence")
    expected="SELECT evidence::text AS evidence FROM (SELECT jsonb_build_object('passed', true) AS evidence) AS t"
    assert result['sql']==expected
    assert result['request']['args']['sql-sha256']==hashlib.sha256(expected.encode()).hexdigest()
    assert result['request_sha256'] != m.request_digest(original)
    assert original==request()
    altered=copy.deepcopy(result['request']); altered['args']['sql-sha256']='0'*64
    assert m.request_digest(altered)!=result['request_sha256']


@pytest.mark.parametrize('bad',["SELECT '{}'::jsonb AS evidence; SELECT 1", "WITH t AS (DELETE FROM x RETURNING *) SELECT * FROM t", "DELETE FROM x", "SELECT 1;", "SELECT '\\!'", "SELECT 1 -- comment"])
def test_unsafe_wrapper_input_is_refused(bad):
    with pytest.raises(ValueError): prep().prepare_readback(request(), readback_sql=bad)


@pytest.mark.parametrize('field,value',[('item_id','K9-4a'),('kind','layer_publish'),('operation_id',''),('reviewed_commit','not-a-sha')])
def test_readback_prep_requires_exact_request_identity(field,value):
    req=request(); req[field]=value
    with pytest.raises(ValueError): prep().prepare_readback(req,readback_sql="SELECT '{}'::jsonb AS evidence")


def test_single_select_jsonb_wrapper_runs_under_actual_readback_shell(kala_db_dsn, tmp_path):
    m=prep(); result=m.prepare_readback(request(),readback_sql="SELECT jsonb_build_object('run_id', 'fixture', 'passed', true) AS evidence")
    root=tmp_path/'runtime'; (root/'run/ops/sql').mkdir(parents=True); (root/'venv/bin').mkdir(parents=True)
    (root/'venv/bin/python').symlink_to(sys.executable)
    query=root/'run/ops/sql/k94b.sql'; query.write_text(result['sql'])
    # Guarded suite-owned local database only; no credentials read or copied.
    settings=psycopg.conninfo.conninfo_to_dict(kala_db_dsn)
    assert settings['host'] in {'127.0.0.1','localhost'}
    import os
    env={k:v for k,v in os.environ.items() if not k.startswith('PG') and k not in {'DATABASE_URL','KY_BUILDER_DATABASE_URL','KY_OWNER_DATABASE_URL','KY_LAYER_VERIFIER_DATABASE_URL'}}
    env.update(KY_ROOT=str(root),KY_READBACK_PGENV=str(tmp_path/'pgenv.sh'),PGHOST=settings['host'],PGPORT=settings['port'],PGUSER='postgres',PGDATABASE=settings['dbname'],PGPASSFILE='/dev/null')
    (tmp_path/'pgenv.sh').write_text('# test uses guarded fixture PG settings\n')
    argv=['bash',str(FLEET/'readback_sql.sh'),'--sql_file',str(query),'--sql-sha256',result['request']['args']['sql-sha256']]
    run=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=10)
    assert run.returncode==0,run.stderr
    import csv, io
    rows=list(csv.reader(io.StringIO(run.stdout),delimiter='\t'))
    assert rows[0]==['evidence'] and json.loads(rows[1][0])=={'run_id':'fixture','passed':True}
    query.write_text("SELECT '{}'::jsonb AS evidence")
    changed=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=10)
    assert changed.returncode != 0 and 'digest' in changed.stderr


def test_generated_queries_return_the_recorded_run_and_publication(db):
    from test_publication_ops import prepare, accept, operations, source_pin
    c=prepare(db); m=prep(); ops=operations()
    sql=m.writer_readback_sql(c.build_id,c.generation)
    wrapped=m.prepare_readback(request(),readback_sql=sql)['sql']
    data=json.loads(db.execute(wrapped,prepare=True).fetchone()[0])
    assert data['run']['id']==c.build_id
    assert data['candidate']['generation']==c.generation
    assert {r['grain_key'] for r in data['grains']}=={a+':inputs' for a in __import__('services.kala_core.rehearsal',fromlist=['ASSETS']).ASSETS}
    assert data['verification'] is None
    assert {row['asset_id'] for row in data['writers']}=={a for a in __import__('services.kala_core.rehearsal',fromlist=['ASSETS']).ASSETS}
    assert {row['asset_id'] for row in data['lineage']}=={row['asset_id'] for row in data['writers']}
    assert all(row['build_id']==c.build_id and row['code_digest']=='a'*64 for row in data['lineage'])
    accept(db,c); ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None,semantic_source=source_pin())
    sql=m.publication_readback_sql(c.build_id,c.generation)
    wrapped=m.prepare_readback(request(),readback_sql=sql)['sql']
    data=json.loads(db.execute(wrapped,prepare=True).fetchone()[0])
    assert data['head']['generation']==c.generation
    assert data['candidate']['state']=='published'
    assert data['verification']['detail']['semantic']['binding']['build_id']==c.build_id


# Pytest reuses the same guarded fixture; no alternative DB lifecycle.
from test_publication_ops import db
