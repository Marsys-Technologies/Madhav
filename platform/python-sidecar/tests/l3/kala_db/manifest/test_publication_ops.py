"""K9-23 real-DB refusal cases and retained-row byte proof."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
import pytest

from services.kala_core.manifest import open_candidate, attest_grain


def operations():
    assert importlib.util.find_spec('services.kala_core.publication') is not None, 'K9-23 entrypoint missing'
    return importlib.import_module('services.kala_core.publication')


@pytest.fixture
def db(kala_db_dsn, monkeypatch):
    # SR-K9-ADMITTED-ZERO: these lifecycle suites attest zero_rows for the STAND-IN name ka_sangam over a schema with no layer tables, so publication's zero-row
    # detector (kala_core/publication.py VACUOUS_ZERO_WRITERS) is switched off here. It has its own oracles: test_k9_zero_row_gate.py (every claim) and the
    # real-writer end-to-end cases in test_k9_publication_admits_writer_grains.py, which run it against real layer tables.
    monkeypatch.setattr(importlib.import_module('services.kala_core.publication'), 'VACUOUS_ZERO_WRITERS', ())
    schema = 'k923_' + uuid.uuid4().hex
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        migration = (Path(__file__).resolve().parents[5] / 'migrations/1330_kala_layer_manifest_candidates.sql').read_text()
        conn.execute(migration.split('-- A separately dispatched verifier')[0].replace('public.', ''))
        conn.execute('''CREATE TABLE build_runs (
            id uuid PRIMARY KEY, chart_id uuid, scope text, scope_target text, action text,
            plan jsonb, state text, plan_manifest jsonb, plan_manifest_digest text)''')
        conn.commit()
        yield conn
        conn.rollback()
        conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        conn.commit()


def prepare(conn, generation='candidate', *, chart=None, writers=('ka_yojaka', 'ka_sangam'), plan=None):
    chart = chart or str(uuid.uuid4())
    build = str(uuid.uuid4())
    plan = plan if plan is not None else {w: [w + ':inputs'] for w in writers}
    c = open_candidate(conn, chart_id=chart, generation=generation, build_id=build,
                       model_digest='fixture', rule_registry_version='fixture',
                       conventions={'publication_grains': plan})
    manifest = dict(version='nirmana-run-manifest/v1', chart_id=chart, scope='layer', scope_target='L3',
                    action='rebuild', waves=[list(writers)], assets=[dict(asset_id=w, scope='chart',
                    depends_on=[], natural_key_partition=None, has_cowriters=False,
                    expected_code_digest='a'*64) for w in writers])
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    conn.execute('INSERT INTO build_runs VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s)',
                 (build, chart, 'layer', 'L3', 'rebuild', json.dumps(list(writers)), 'completed', json.dumps(manifest), digest))
    for grain in [g for gs in plan.values() for g in gs]:
        attest_grain(conn, c, grain_key=grain, result_state='zero_rows', input_vector=grain+'-vector')
    conn.commit()
    return c


def independent_digest(c, conn):
    keys = conn.execute('SELECT grain_key FROM kala_layer_candidate_grain WHERE chart_id=%s AND generation=%s ORDER BY grain_key',
                        (c.chart_id, c.generation)).fetchall()
    return hashlib.sha256(json.dumps([(r[0],r[0]+'-vector') for r in keys], separators=(',', ':')).encode()).hexdigest()


def accept(conn, c):
    conn.execute("INSERT INTO kala_layer_verification VALUES (%s,%s,'verifier_principal','accepted',%s::jsonb,now())",
                 (c.chart_id,c.generation,json.dumps({'input_digest':independent_digest(c,conn)})))


def snapshot(conn):
    return conn.execute('''SELECT jsonb_build_object(
        'head',(SELECT jsonb_agg(to_jsonb(t) ORDER BY chart_id) FROM kala_layer_head t),
        'candidate',(SELECT jsonb_agg(to_jsonb(t) ORDER BY generation) FROM kala_layer_candidate t),
        'grain',(SELECT jsonb_agg(to_jsonb(t) ORDER BY generation,grain_key) FROM kala_layer_candidate_grain t),
        'verification',(SELECT jsonb_agg(to_jsonb(t) ORDER BY generation) FROM kala_layer_verification t))::text''').fetchone()[0].encode()


def test_absent_candidate_is_refused_without_mutation(db):
    ops = operations(); before = snapshot(db)
    with pytest.raises(ValueError, match='candidate'):
        ops.publish(db,run_id=str(uuid.uuid4()),generation='absent',expected_head=None)
    assert snapshot(db) == before


@pytest.mark.parametrize('defect',['missing_writer','missing_grain','failed_grain','extra_grain','empty_plan','duplicate_grain','wrong_writer','bad_manifest'])
def test_incomplete_inventory_is_refused_before_publication(db,defect):
    ops = operations()
    c = prepare(db,plan={'ka_yojaka':['ka_yojaka:inputs']} if defect=='missing_writer' else None)
    if defect=='missing_grain': db.execute("DELETE FROM kala_layer_candidate_grain WHERE grain_key='ka_sangam:inputs'")
    elif defect=='failed_grain': db.execute("UPDATE kala_layer_candidate_grain SET result_state='failed' WHERE grain_key='ka_sangam:inputs'")
    elif defect=='extra_grain': attest_grain(db,c,grain_key='ka_sangam:unplanned',result_state='rows',input_vector='extra')
    elif defect in ('empty_plan','duplicate_grain','wrong_writer'):
        plan = {} if defect=='empty_plan' else {'ka_yojaka':['ka_yojaka:inputs','ka_yojaka:inputs'],'ka_sangam':['ka_sangam:inputs']} if defect=='duplicate_grain' else {'ka_yojaka':['ka_sangam:inputs'],'ka_sangam':['other']}
        db.execute('UPDATE kala_layer_candidate SET conventions=%s::jsonb',(json.dumps({'publication_grains':plan}),))
    elif defect=='bad_manifest': db.execute('UPDATE build_runs SET plan_manifest_digest=%s',('b'*64,))
    accept(db,c); before = snapshot(db)
    with pytest.raises(ValueError): ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None)
    assert snapshot(db) == before


@pytest.mark.parametrize('receipt',['missing','rejected','stale','builder'])
def test_unearned_verification_cannot_publish(db,receipt):
    ops=operations(); c=prepare(db)
    if receipt!='missing':
        accept(db,c)
        if receipt=='rejected': db.execute("UPDATE kala_layer_verification SET result='rejected'")
        if receipt=='stale': db.execute("UPDATE kala_layer_verification SET detail='{}'")
        if receipt=='builder': db.execute("UPDATE kala_layer_verification SET verifier_principal='builder'")
    before=snapshot(db)
    with pytest.raises(ValueError,match='verif'): ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None)
    assert snapshot(db)==before


def test_stale_expected_head_and_changed_build_pin_refuse(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None)
    b=prepare(db,'b',chart=a.chart_id); accept(db,b); before=snapshot(db)
    with pytest.raises(ValueError,match='expected.head'): ops.publish(db,run_id=b.build_id,generation='b',expected_head='wrong')
    assert snapshot(db)==before
    db.execute("UPDATE kala_layer_head SET generation='concurrent'"); before=snapshot(db)
    with pytest.raises(ValueError,match='head'): ops.publish(db,run_id=b.build_id,generation='b',expected_head='a')
    assert snapshot(db)==before


def test_rollback_restores_retained_head_and_payload_bytes(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None)
    head_before=db.execute('SELECT to_jsonb(h)::text FROM kala_layer_head h').fetchone()[0].encode()
    b=prepare(db,'b',chart=a.chart_id); accept(db,b)
    ops.publish(db,run_id=b.build_id,generation='b',expected_head='a')
    query='SELECT jsonb_agg(to_jsonb(t) ORDER BY generation,grain_key)::text FROM kala_layer_candidate_grain t'
    payload_before=db.execute(query).fetchone()[0].encode()
    ops.rollback(db,generation='a',expected_head='b',chart_id=a.chart_id)
    assert db.execute('SELECT to_jsonb(h)::text FROM kala_layer_head h').fetchone()[0].encode()==head_before
    assert db.execute(query).fetchone()[0].encode()==payload_before
    before=snapshot(db)
    with pytest.raises(ValueError): ops.rollback(db,generation='a',expected_head='b',chart_id=a.chart_id)
    assert snapshot(db)==before


def test_rollback_refuses_building_or_absent_target(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None)
    prepare(db,'b',chart=a.chart_id)
    for target in ('b','absent'):
        before=snapshot(db)
        with pytest.raises(ValueError): ops.rollback(db,generation=target,expected_head='a',chart_id=a.chart_id)
        assert snapshot(db)==before


def test_verify_refuses_builder_without_receipt(db):
    ops=operations(); c=prepare(db)
    with pytest.raises(ValueError,match='verifier_principal'):
        ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest=independent_digest(c,db))
    assert db.execute('SELECT * FROM kala_layer_verification').fetchall()==[]


def test_readonly_rebuild_inspection_does_not_run_or_mutate(db):
    ops=operations(); c=prepare(db); before=snapshot(db)
    result=ops.inspect_rebuild(db,run_id=c.build_id,assets='ka_yojaka,ka_sangam')
    assert result['status']=='PLAN_ONLY' and result['dry_run_passed'] is None
    assert result['planned_assets']==['ka_yojaka','ka_sangam'] and result['executed_assets']==[]
    assert snapshot(db)==before
    for wrong in ('ka_yojaka','ga_positions,ka_yojaka','ka_sangam,ka_yojaka'):
        with pytest.raises(ValueError): ops.inspect_rebuild(db,run_id=c.build_id,assets=wrong)


def test_verifier_role_uses_narrow_grants_and_records_only_matching_inputs(db):
    ops=operations(); c=prepare(db)
    if not db.execute("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='verifier_principal')").fetchone()[0]:
        db.execute('CREATE ROLE verifier_principal NOLOGIN')
    schema=db.execute('SELECT current_schema()').fetchone()[0]
    db.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO verifier_principal').format(sql.Identifier(schema)))
    root=Path(__file__).resolve().parents[5]/'migrations'
    db.execute('GRANT SELECT ON kala_layer_candidate_grain TO verifier_principal')
    db.execute('GRANT INSERT ON kala_layer_verification TO verifier_principal')
    db.execute('GRANT SELECT(chart_id,generation) ON kala_layer_verification TO verifier_principal')
    db.execute((root/'1390_kala_layer_operation_verifier_reads.sql').read_text().replace('public.',''))
    with db.transaction():
        db.execute('SET LOCAL ROLE verifier_principal')
        with pytest.raises(ValueError,match='digest'):
            ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest='0'*64)
        result=ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest=independent_digest(c,db))
        assert result['verified_grains']==['ka_sangam:inputs','ka_yojaka:inputs']
        assert result['semantic_verification'] is None
        assert db.execute("SELECT has_table_privilege(current_user,'kala_layer_head','UPDATE')").fetchone()==(False,)
        with pytest.raises(ValueError,match='immutable receipt'):
            ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest=independent_digest(c,db))
    db.execute('RESET ROLE')
    assert db.execute('SELECT result FROM kala_layer_verification').fetchall()==[('accepted',)]


def test_cli_transaction_rolls_back_refusal_and_reports_plan_only(db,monkeypatch,capsys):
    ops=operations(); c=prepare(db,chart=ops.CANONICAL_CHART)
    class Session:
        def __enter__(self): return db
        def __exit__(self,typ,value,tb):
            if typ: db.rollback()
            else: db.commit()
    monkeypatch.setenv('DATABASE_URL','local-fixture')
    monkeypatch.setattr(ops.psycopg,'connect',lambda *a,**k:Session())
    assert ops.main(['publish','--run-id',c.build_id,'--generation',c.generation,'--expected-head','NONE'])==2
    assert json.loads(capsys.readouterr().out)['status']=='REFUSED'
    assert db.execute('SELECT * FROM kala_layer_head').fetchall()==[]
    db.rollback()
    assert ops.main(['rebuild-dryrun','--run-id',c.build_id,'--assets','ka_yojaka,ka_sangam'])==0
    out=json.loads(capsys.readouterr().out)
    assert out['status']=='PLAN_ONLY' and out['dry_run_passed'] is None
    db.read_only=False


def test_rollback_refuses_a_retained_generation_that_is_not_the_previous_head(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None)
    b=prepare(db,'b',chart=a.chart_id); accept(db,b)
    ops.publish(db,run_id=b.build_id,generation='b',expected_head='a')
    c=prepare(db,'c',chart=a.chart_id); accept(db,c)
    ops.publish(db,run_id=c.build_id,generation='c',expected_head='b')
    before=snapshot(db)
    with pytest.raises(ValueError,match='previous'):
        ops.rollback(db,generation='a',expected_head='c',chart_id=a.chart_id)
    assert snapshot(db)==before
