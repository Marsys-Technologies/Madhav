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
from services.kala_core.rehearsal import ASSETS, WAVES

ORDERED_ASSETS = ",".join(ASSETS)


def operations():
    assert importlib.util.find_spec('services.kala_core.publication') is not None, 'K9-23 entrypoint missing'
    return importlib.import_module('services.kala_core.publication')


@pytest.fixture
def db(kala_db_dsn, monkeypatch):
    schema = 'k923_' + uuid.uuid4().hex
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
        migration = (Path(__file__).resolve().parents[5] / 'migrations/1330_kala_layer_manifest_candidates.sql').read_text()
        conn.execute(migration.split('-- A separately dispatched verifier')[0].replace('public.', ''))
        conn.execute('''CREATE TABLE build_runs (
            id uuid PRIMARY KEY, chart_id uuid, scope text, scope_target text, action text,
            plan jsonb, state text, plan_manifest jsonb, plan_manifest_digest text)''')
        conn.execute('CREATE TABLE build_run_assets (run_id uuid, asset_id text, position integer, state text)')
        conn.execute('CREATE TABLE asset_provenance_receipts (build_id uuid, chart_id uuid, asset_id text, partition_key text, code_digest text, receipt_state text)')
        conn.execute('CREATE TABLE golden_values (grain text PRIMARY KEY, source integer, observed integer)')
        from services.kala_core import publication_checks
        monkeypatch.setattr(publication_checks, 'CHECKS', {
            writer: (publication_checks.GoldenCheck('independent-triple-v1', golden_triple),)
            for writer in ASSETS
        })
        conn.commit()
        yield conn
        conn.rollback()
        conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        conn.commit()


def prepare(conn, generation='candidate', *, chart=None, writers=ASSETS, plan=None):
    chart = chart or str(uuid.uuid4())
    build = str(uuid.uuid4())
    plan = plan if plan is not None else {w: [w + ':inputs'] for w in writers}
    c = open_candidate(conn, chart_id=chart, generation=generation, build_id=build,
                       model_digest='fixture', rule_registry_version='fixture',
                       conventions={'publication_grains': plan})
    manifest = dict(version='nirmana-run-manifest/v1', chart_id=chart, scope='layer', scope_target='L3',
                    action='rebuild', waves=[list(wave) for wave in WAVES] if tuple(writers)==ASSETS else [list(writers)], assets=[dict(asset_id=w, scope='chart',
                    depends_on=[], natural_key_partition=None, has_cowriters=False,
                    expected_code_digest='a'*64) for w in writers])
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    conn.execute('INSERT INTO build_runs VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s)',
                 (build, chart, 'layer', 'L3', 'rebuild', json.dumps(list(writers)), 'completed', json.dumps(manifest), digest))
    for position,writer in enumerate(writers):
        conn.execute("INSERT INTO build_run_assets VALUES (%s,%s,%s,'complete')", (build,writer,position))
        conn.execute("INSERT INTO asset_provenance_receipts VALUES (%s,%s,%s,'__whole_asset__',%s,'proven')", (build,chart,writer,'a'*64))
    for grain in [g for gs in plan.values() for g in gs]:
        attest_grain(conn, c, grain_key=grain, result_state='zero_rows', input_vector=grain+'-vector')
        conn.execute('INSERT INTO golden_values VALUES (%s,2,6) ON CONFLICT DO NOTHING', (grain,))
    conn.commit()
    return c


def independent_digest(c, conn):
    keys = conn.execute('SELECT grain_key FROM kala_layer_candidate_grain WHERE chart_id=%s AND generation=%s ORDER BY grain_key',
                        (c.chart_id, c.generation)).fetchall()
    return hashlib.sha256(json.dumps([(r[0],r[0]+'-vector') for r in keys], separators=(',', ':')).encode()).hexdigest()


def golden_triple(reader, candidate, grains):
    """Independent fixture oracle: real stored output vs recomputation from source."""
    result = {}
    for grain in grains:
        row = reader.execute('SELECT source, observed FROM golden_values WHERE grain=%s', (grain,)).fetchone()
        result[grain] = (None, None) if row is None else (row[0] * 3, row[1])
    return result


def source_pin():
    from services.kala_core.publication_checks import checks_digest
    return checks_digest()


def accept(conn, c):
    ops = operations()
    _, binding = ops._candidate(conn, c.build_id, c.generation)
    from services.kala_core.publication_checks import semantic_evidence
    evidence = semantic_evidence(conn, c, binding, source_pin())
    conn.execute("INSERT INTO kala_layer_verification VALUES (%s,%s,'verifier_principal','accepted',%s::jsonb,now())",
                 (c.chart_id,c.generation,json.dumps({'input_digest':independent_digest(c,conn), 'semantic':evidence})))


def snapshot(conn):
    return conn.execute('''SELECT jsonb_build_object(
        'head',(SELECT jsonb_agg(to_jsonb(t) ORDER BY chart_id) FROM kala_layer_head t),
        'candidate',(SELECT jsonb_agg(to_jsonb(t) ORDER BY generation) FROM kala_layer_candidate t),
        'grain',(SELECT jsonb_agg(to_jsonb(t) ORDER BY generation,grain_key) FROM kala_layer_candidate_grain t),
        'verification',(SELECT jsonb_agg(to_jsonb(t) ORDER BY generation) FROM kala_layer_verification t))::text''').fetchone()[0].encode()


def test_absent_candidate_is_refused_without_mutation(db):
    ops = operations(); before = snapshot(db)
    with pytest.raises(ValueError, match='candidate'):
        ops.publish(db,run_id=str(uuid.uuid4()),generation='absent',expected_head=None,semantic_source=source_pin())
    assert snapshot(db) == before


@pytest.mark.parametrize('defect',['missing_writer','missing_grain','failed_grain','extra_grain','empty_plan','duplicate_grain','wrong_writer','bad_manifest'])
def test_incomplete_inventory_is_refused_before_publication(db,defect):
    ops = operations()
    c = prepare(db,plan={'ka_yojaka':['ka_yojaka:inputs']} if defect=='missing_writer' else None)
    valid_semantic = None
    if defect == 'extra_grain':
        accept(db,c)
        valid_semantic = db.execute('SELECT detail FROM kala_layer_verification').fetchone()[0]['semantic']
        db.execute('DELETE FROM kala_layer_verification')
    if defect=='missing_grain': db.execute("DELETE FROM kala_layer_candidate_grain WHERE grain_key='ka_sangam:inputs'")
    elif defect=='failed_grain': db.execute("UPDATE kala_layer_candidate_grain SET result_state='failed' WHERE grain_key='ka_sangam:inputs'")
    elif defect=='extra_grain': attest_grain(db,c,grain_key='ka_sangam:unplanned',result_state='rows',input_vector='ka_sangam:unplanned-vector')
    elif defect in ('empty_plan','duplicate_grain','wrong_writer'):
        plan = {} if defect=='empty_plan' else {'ka_yojaka':['ka_yojaka:inputs','ka_yojaka:inputs'],'ka_sangam':['ka_sangam:inputs']} if defect=='duplicate_grain' else {'ka_yojaka':['ka_sangam:inputs'],'ka_sangam':['other']}
        db.execute('UPDATE kala_layer_candidate SET conventions=%s::jsonb',(json.dumps({'publication_grains':plan}),))
    elif defect=='bad_manifest': db.execute('UPDATE build_runs SET plan_manifest_digest=%s',('b'*64,))
    db.execute("INSERT INTO kala_layer_verification VALUES (%s,%s,'verifier_principal','accepted',%s::jsonb,now())",
               (c.chart_id,c.generation,json.dumps({'input_digest':independent_digest(c,db), 'semantic':valid_semantic})))
    before = snapshot(db)
    with pytest.raises(ValueError): ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None,semantic_source=source_pin())
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
    with pytest.raises(ValueError,match='verif'): ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None,semantic_source=source_pin())
    assert snapshot(db)==before


def test_stale_expected_head_and_changed_build_pin_refuse(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None,semantic_source=source_pin())
    b=prepare(db,'b',chart=a.chart_id); accept(db,b); before=snapshot(db)
    with pytest.raises(ValueError,match='expected.head'): ops.publish(db,run_id=b.build_id,generation='b',expected_head='wrong',semantic_source=source_pin())
    assert snapshot(db)==before
    db.execute("UPDATE kala_layer_head SET generation='concurrent'"); before=snapshot(db)
    with pytest.raises(ValueError,match='head'): ops.publish(db,run_id=b.build_id,generation='b',expected_head='a',semantic_source=source_pin())
    assert snapshot(db)==before


def test_rollback_restores_retained_head_and_payload_bytes(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None,semantic_source=source_pin())
    head_before=db.execute('SELECT to_jsonb(h)::text FROM kala_layer_head h').fetchone()[0].encode()
    b=prepare(db,'b',chart=a.chart_id); accept(db,b)
    ops.publish(db,run_id=b.build_id,generation='b',expected_head='a',semantic_source=source_pin())
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
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None,semantic_source=source_pin())
    prepare(db,'b',chart=a.chart_id)
    for target in ('b','absent'):
        before=snapshot(db)
        with pytest.raises(ValueError): ops.rollback(db,generation=target,expected_head='a',chart_id=a.chart_id)
        assert snapshot(db)==before


def test_verify_refuses_builder_without_receipt(db):
    ops=operations(); c=prepare(db)
    with pytest.raises(ValueError,match='verifier_principal'):
        ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest=independent_digest(c,db),semantic_source=source_pin())
    assert db.execute('SELECT * FROM kala_layer_verification').fetchall()==[]


def test_readonly_rebuild_inspection_does_not_run_or_mutate(db):
    ops=operations(); c=prepare(db); before=snapshot(db)
    result=ops.inspect_rebuild(db,run_id=c.build_id,assets=ORDERED_ASSETS)
    assert result['status']=='PLAN_ONLY' and result['dry_run_passed'] is None
    assert result['planned_assets']==list(ASSETS) and result['executed_assets']==[]
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
    db.execute('GRANT SELECT ON kala_layer_candidate_grain, golden_values TO verifier_principal')
    db.execute('GRANT INSERT ON kala_layer_verification TO verifier_principal')
    db.execute('GRANT SELECT(chart_id,generation) ON kala_layer_verification TO verifier_principal')
    db.execute((root/'1390_kala_layer_operation_verifier_reads.sql').read_text().replace('public.',''))
    with db.transaction():
        db.execute('SET LOCAL ROLE verifier_principal')
        with pytest.raises(ValueError,match='digest'):
            ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest='0'*64,semantic_source=source_pin())
        result=ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest=independent_digest(c,db),semantic_source=source_pin())
        assert result['verified_grains']==sorted(a+':inputs' for a in ASSETS)
        assert result['semantic_verification'] is True
        assert db.execute("SELECT has_table_privilege(current_user,'kala_layer_head','UPDATE')").fetchone()==(False,)
        with pytest.raises(ValueError,match='immutable receipt'):
            ops.verify(db,run_id=c.build_id,generation=c.generation,independently_derived_digest=independent_digest(c,db),semantic_source=source_pin())
    db.execute('RESET ROLE')
    assert db.execute('SELECT result FROM kala_layer_verification').fetchall()==[('accepted',)]
    result=ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None,semantic_source=source_pin())
    assert result['status']=='PUBLISHED'


def test_cli_transaction_rolls_back_refusal_and_reports_plan_only(db,monkeypatch,capsys):
    ops=operations(); c=prepare(db,chart=ops.CANONICAL_CHART)
    class Session:
        def __enter__(self): return db
        def __exit__(self,typ,value,tb):
            if typ: db.rollback()
            else: db.commit()
    monkeypatch.setenv('DATABASE_URL','local-fixture')
    monkeypatch.setattr(ops.psycopg,'connect',lambda *a,**k:Session())
    assert ops.main(['publish','--run-id',c.build_id,'--generation',c.generation,'--expected-head','NONE','--semantic-source',source_pin()])==2
    assert json.loads(capsys.readouterr().out)['status']=='REFUSED'
    assert db.execute('SELECT * FROM kala_layer_head').fetchall()==[]
    db.rollback()
    assert ops.main(['rebuild-dryrun','--run-id',c.build_id,'--assets',ORDERED_ASSETS])==0
    out=json.loads(capsys.readouterr().out)
    assert out['status']=='PLAN_ONLY' and out['dry_run_passed'] is None
    db.read_only=False


def test_rollback_refuses_a_retained_generation_that_is_not_the_previous_head(db):
    ops=operations(); a=prepare(db,'a'); accept(db,a)
    ops.publish(db,run_id=a.build_id,generation='a',expected_head=None,semantic_source=source_pin())
    b=prepare(db,'b',chart=a.chart_id); accept(db,b)
    ops.publish(db,run_id=b.build_id,generation='b',expected_head='a',semantic_source=source_pin())
    c=prepare(db,'c',chart=a.chart_id); accept(db,c)
    ops.publish(db,run_id=c.build_id,generation='c',expected_head='b',semantic_source=source_pin())
    before=snapshot(db)
    with pytest.raises(ValueError,match='previous'):
        ops.rollback(db,generation='a',expected_head='c',chart_id=a.chart_id)
    assert snapshot(db)==before


@pytest.mark.parametrize('outcome', ['completed', 'planned', 'failed', 'absent'])
def test_rebuild_delegates_once_from_planned_and_requires_completed_readback(db, monkeypatch, capsys, outcome):
    ops = operations()
    c = prepare(db, chart=ops.CANONICAL_CHART)
    db.execute("UPDATE build_runs SET state='planned'")
    db.commit()
    calls = []
    from pipeline.orchestrator import runner
    def execute_run(run_id):
        calls.append(run_id)
        if outcome == 'absent':
            db.execute('DELETE FROM build_runs WHERE id=%s', (run_id,))
        else:
            db.execute('UPDATE build_runs SET state=%s WHERE id=%s', (outcome, run_id))
        db.commit()
    monkeypatch.setattr(runner, 'execute_run', execute_run)
    class Session:
        def __enter__(self): return db
        def __exit__(self, typ, value, tb):
            db.rollback() if typ else db.commit()
    monkeypatch.setenv('DATABASE_URL', 'local-fixture')
    monkeypatch.setattr(ops.psycopg, 'connect', lambda *a, **k: Session())
    code = ops.main(['rebuild', '--run-id', c.build_id, '--assets', ORDERED_ASSETS])
    assert calls == [c.build_id]
    assert code == (0 if outcome == 'completed' else 2)
    assert json.loads(capsys.readouterr().out)['status'] == ('BUILD_COMPLETED' if outcome == 'completed' else 'REFUSED')


@pytest.mark.parametrize('defect', ['wrong_output','missing_writer_check','missing_grain_check','wrong_source_pin','input_only_receipt','changed_writer_code','changed_grain_input','wrong_build_id','missing_comparison','mismatched_comparison','malformed_detail','changed_grain_state'])
def test_semantic_acceptance_is_per_writer_source_build_and_grain_bound(db, monkeypatch, defect):
    ops = operations(); c = prepare(db)
    from services.kala_core import publication_checks as checks
    if defect == 'wrong_output': db.execute("UPDATE golden_values SET observed=7 WHERE grain='ka_sangam:inputs'")
    elif defect == 'missing_writer_check': monkeypatch.delitem(checks.CHECKS, 'ka_sangam')
    elif defect == 'missing_grain_check':
        monkeypatch.setitem(checks.CHECKS, 'ka_sangam', (checks.GoldenCheck('empty', lambda *args: {}),))
    if defect in {'wrong_output','missing_writer_check','missing_grain_check','wrong_source_pin'}:
        _, binding = ops._candidate(db, c.build_id, c.generation)
        with pytest.raises(ValueError):
            checks.semantic_evidence(db, c, binding, '0'*64 if defect == 'wrong_source_pin' else source_pin())
        assert db.execute('SELECT * FROM kala_layer_verification').fetchall() == []
        return
    accept(db, c)
    if defect == 'input_only_receipt':
        db.execute("UPDATE kala_layer_verification SET detail=detail-'semantic'")
    elif defect == 'changed_writer_code':
        row=db.execute('SELECT plan_manifest FROM build_runs').fetchone()[0]
        row['assets'][0]['expected_code_digest']='b'*64
        digest=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        db.execute('UPDATE build_runs SET plan_manifest=%s::jsonb,plan_manifest_digest=%s',(json.dumps(row),digest))
    elif defect == 'changed_grain_state': db.execute("UPDATE kala_layer_candidate_grain SET result_state='rows'")
    elif defect == 'changed_grain_input': db.execute("UPDATE kala_layer_candidate_grain SET input_vector='changed'")
    else:
        evidence=db.execute('SELECT detail FROM kala_layer_verification').fetchone()[0]
        if defect == 'wrong_build_id': evidence['semantic']['binding']['build_id']=str(uuid.uuid4())
        elif defect == 'missing_comparison': evidence['semantic']['comparisons'].pop()
        elif defect == 'mismatched_comparison': evidence['semantic']['comparisons'][0]['observed_sha256']='0'*64
        else: evidence=[]
        db.execute('UPDATE kala_layer_verification SET detail=%s::jsonb',(json.dumps(evidence),))
    before = snapshot(db)
    with pytest.raises(ValueError):
        ops.publish(db, run_id=c.build_id, generation=c.generation, expected_head=None, semantic_source=source_pin())
    assert snapshot(db) == before


@pytest.mark.parametrize('generation', ['NONE','current','', 'bad generation'])
def test_reserved_generation_namespace_refuses_before_database_access(generation):
    ops = operations()
    with pytest.raises(ValueError, match='generation'):
        ops.publish(None, run_id=str(uuid.uuid4()), generation=generation, expected_head=None, semantic_source=source_pin())


def test_rebuild_refuses_a_digest_valid_partial_or_reordered_layer_plan(db):
    ops=operations()
    c=prepare(db,writers=('ka_yojaka',))
    with pytest.raises(ValueError,match='layer roster'):
        ops.inspect_rebuild(db,run_id=c.build_id,assets='ka_yojaka')


def test_initial_publication_cas_refuses_a_concurrent_first_head(db):
    ops=operations(); c=prepare(db); accept(db,c)
    db.execute('INSERT INTO kala_layer_head(chart_id,generation) VALUES (%s,%s)',(c.chart_id,'concurrent'))
    before=snapshot(db)
    with pytest.raises(ValueError,match='head'):
        ops.publish(db,run_id=c.build_id,generation=c.generation,expected_head=None,semantic_source=source_pin())
    assert snapshot(db)==before


def test_rebuild_refuses_digest_valid_stage_reordering(db):
    ops=operations(); c=prepare(db)
    manifest=db.execute('SELECT plan_manifest FROM build_runs').fetchone()[0]
    manifest['waves'].reverse()
    plan=[asset for wave in manifest['waves'] for asset in wave]
    by_id={asset['asset_id']:asset for asset in manifest['assets']}
    manifest['assets']=[by_id[asset] for asset in plan]
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    db.execute('UPDATE build_runs SET plan=%s::jsonb,plan_manifest=%s::jsonb,plan_manifest_digest=%s',
               (json.dumps(plan),json.dumps(manifest),digest))
    with pytest.raises(ValueError,match='stage order'):
        ops.inspect_rebuild(db,run_id=c.build_id,assets=','.join(plan))


@pytest.mark.parametrize('writers', [('ka_bhavishya_lekha',),('ga_positions',)])
def test_issued_forecasts_and_non_kala_writers_cannot_enter_replaceable_rebuild(db,writers):
    ops=operations(); c=prepare(db,writers=writers)
    with pytest.raises(ValueError): ops.inspect_rebuild(db,run_id=c.build_id,assets=','.join(writers))


def test_mismatched_golden_output_under_real_verifier_role_never_records_acceptance(db):
    ops=operations(); c=prepare(db)
    if not db.execute("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='verifier_principal')").fetchone()[0]:
        db.execute('CREATE ROLE verifier_principal NOLOGIN')
    schema=db.execute('SELECT current_schema()').fetchone()[0]
    db.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO verifier_principal').format(sql.Identifier(schema)))
    db.execute('GRANT SELECT ON kala_layer_candidate_grain, golden_values TO verifier_principal')
    db.execute('GRANT INSERT ON kala_layer_verification TO verifier_principal')
    db.execute('GRANT SELECT(chart_id,generation) ON kala_layer_verification TO verifier_principal')
    root=Path(__file__).resolve().parents[5]/'migrations'
    db.execute((root/'1390_kala_layer_operation_verifier_reads.sql').read_text().replace('public.',''))
    db.execute("UPDATE golden_values SET observed=7 WHERE grain='ka_sangam:inputs'")
    with db.transaction():
        db.execute('SET LOCAL ROLE verifier_principal')
        with pytest.raises(ValueError,match='golden comparison failed'):
            ops.verify(db,run_id=c.build_id,generation=c.generation,
                       independently_derived_digest=independent_digest(c,db),semantic_source=source_pin())
    db.execute('RESET ROLE')
    assert db.execute('SELECT * FROM kala_layer_verification').fetchall()==[]
