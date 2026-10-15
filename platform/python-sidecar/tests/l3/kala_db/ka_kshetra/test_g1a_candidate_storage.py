"""Real stored isolation, mutability, idempotency and executable stage SQL."""
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
import re

import psycopg
from psycopg.types.json import Jsonb
import pytest

from services.ka_kshetra.candidate import CandidateConnection, TABLES, bind_candidate
from services.ka_kshetra import stage4_field as S4
from services.ka_kshetra.writer import KaKshetraWriter

ROOT=Path(__file__).resolve().parents[5]
MIGRATION=ROOT/'migrations/1385_k5_g1a_candidate_field.sql'


@pytest.fixture(scope='module')
def database(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as conn:
        conn.execute('CREATE TABLE build_runs(id uuid PRIMARY KEY,chart_id uuid NOT NULL)')
        conn.execute('CREATE TABLE kala_layer_candidate(chart_id uuid,generation text,build_id uuid,state text,conventions jsonb,PRIMARY KEY(chart_id,generation))')
        conn.execute('CREATE TABLE kala_layer_head(chart_id uuid PRIMARY KEY,generation text)')
        conn.execute('CREATE TABLE build_substep_progress(chart_id uuid,asset_id text,substep_key text,build_fingerprint text,rows_written int,completed_at timestamptz,PRIMARY KEY(chart_id,asset_id,substep_key))')
        # Execute real legacy DDL, including expression indexes. Do not import seed DML.
        for n in [488,489,490,492,493,494,495,496]:
            body=next((ROOT/'supabase/migrations').glob(f'{n}_*.sql')).read_text()
            body=re.sub(r'--[^\n]*','',body)
            for statement in re.findall(r'^CREATE (?:TABLE|(?:UNIQUE )?INDEX)[\s\S]*?;',body,re.M):
                conn.execute(statement)
        conn.execute(MIGRATION.read_text())
        conn.execute(MIGRATION.read_text())  # reapplication must remain safe
    return isolated_kala_db_dsn


@pytest.fixture
def data(database):
    with psycopg.connect(database) as conn:
        chart=str(uuid4()); build=str(uuid4())
        conn.execute('INSERT INTO build_runs VALUES(%s,%s)',(build,chart))
        for gen,state in [('candidate:g1','building'),('candidate:g2','building'),('candidate:old','published')]:
            conn.execute('INSERT INTO kala_layer_candidate VALUES(%s,%s,%s,%s,%s)',(chart,gen,build,state,Jsonb({})))
        conn.execute('INSERT INTO kala_layer_head VALUES(%s,%s)',(chart,'candidate:old'))
        yield conn,chart,build
        conn.rollback()


def insert_field(conn,chart,alpha=0.):
    # Same SQL and parameter shape as the production writer's batched insert.
    conn.execute(KaKshetraWriter._KALA_FIELD_INSERT_SQL,
      (chart,'career',0,0.,10.,alpha,0.,1.,1.,10.,1.,0.,0.,1.,0.,0,False,None,'v0','x12_v0','snap'))


def test_legacy_and_two_generations_are_isolated_and_retry_safe(data):
    conn,chart,build=data
    insert_field(conn,chart,9.)
    before=conn.execute('SELECT row_to_json(r)::text FROM kala_field r').fetchall()
    one=CandidateConnection(conn,'candidate:g1'); two=CandidateConnection(conn,'candidate:g2')
    insert_field(one,chart,1.); insert_field(two,chart,2.); insert_field(one,chart,3.)
    # Upsert really updates candidate coefficient fields (not only timestamps).
    assert one.execute('SELECT alpha FROM kala_field WHERE chart_id=%s',(chart,)).fetchone()==(3.,)
    assert two.execute('SELECT alpha FROM kala_field WHERE chart_id=%s',(chart,)).fetchone()==(2.,)
    one.execute('DELETE FROM kala_field WHERE chart_id=%s',(chart,))
    assert two.execute('SELECT count(*) FROM kala_field WHERE chart_id=%s',(chart,)).fetchone()==(1,)
    assert conn.execute('SELECT row_to_json(r)::text FROM kala_field r').fetchall()==before
    assert conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s',(chart,)).fetchone()==('candidate:old',)


def test_every_stage_table_and_progress_ledger_has_generation_key(data):
    conn,chart,build=data
    for table in TABLES:
        indexes=conn.execute('SELECT pg_get_indexdef(indexrelid) FROM pg_index WHERE indrelid=%s::regclass AND indisunique',(table+'_candidate',)).fetchall()
        assert indexes and all('(generation,' in row[0] for row in indexes)
    source_seq=conn.execute("SELECT pg_get_serial_sequence('kala_field','id')").fetchone()[0]
    target_seq=conn.execute("SELECT column_default FROM information_schema.columns WHERE table_name='kala_field_candidate' AND column_name='id'").fetchone()[0]
    assert source_seq.split('.')[-1] not in target_seq


def test_published_generation_rejects_insert_delete_and_update(data):
    conn,chart,build=data
    g=CandidateConnection(conn,'candidate:g1'); insert_field(g,chart)
    conn.execute("UPDATE kala_layer_candidate SET state='published' WHERE chart_id=%s AND generation='candidate:g1'",(chart,))
    for operation in [lambda:insert_field(g,chart),lambda:g.execute('DELETE FROM kala_field WHERE chart_id=%s',(chart,))]:
        with pytest.raises(psycopg.errors.RaiseException,match='building candidate'):
            with conn.transaction(): operation()
    # Even a caller bypassing the adapter cannot mutate an old generation.
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute("UPDATE kala_field_candidate SET alpha=5 WHERE chart_id=%s AND generation='candidate:g1'",(chart,))


def test_wrong_build_binding_is_refused_before_stage_work(data):
    conn,chart,build=data
    ctx=SimpleNamespace(db_conn=conn,build_id=str(uuid4()),config={'chart_id':chart,'kshetra_g1_candidate':'candidate:g1'})
    with pytest.raises(ValueError,match='bound'): bind_candidate(ctx)
    ctx.build_id=build
    scoped,record=bind_candidate(ctx,lock=True)
    assert scoped.generation=='candidate:g1'


def test_generation_scoped_plugin_upserts_and_named_cursor_loaders(data):
    conn,chart,build=data
    from services.ka_kshetra import stage0_kinematics as S0, stage1_symbolization as S1
    from datetime import datetime,timezone
    candidate=CandidateConnection(conn,'candidate:g1')
    origin=datetime(1984,2,5,tzinfo=timezone.utc)
    p=S1.PrimitiveRow(chart,'negative_space','a',1,2,[(1,1),(2,1)],'obstructive',source_kind='l3_row',source_table='kala_obstruction',source_pk='a')
    assert S1.write_primitive_rows(candidate,[p])==1
    assert len(S4.load_primitives(candidate,chart))==1
    assert not S4.load_primitives(CandidateConnection(conn,'candidate:g2'),chart)
    insert_field(candidate,chart)
    writer=KaKshetraWriter();writer._chart_id=chart;writer._snapshot_id='snap'
    segments=writer._load_segments(candidate,'career')
    assert len(segments)==1 and segments[0].t_start==0
    writer._event_classes=['career']; writer._dhara_sweep_version=None
    writer._record_substep(candidate,'stage1:run',1)
    assert writer._load_completed_substeps(candidate,chart,writer._fingerprint())=={'stage1:run'}
    assert writer._load_completed_substeps(CandidateConnection(conn,'candidate:g2'),chart,writer._fingerprint()) is None


def test_production_stage1_consumes_stored_adapters_and_effective_states(data):
    conn,chart,build=data
    conn.execute("UPDATE kala_layer_candidate SET conventions=%s WHERE chart_id=%s",(Jsonb({'fixture':True}),chart))
    conn.execute('CREATE TABLE kala_vedha_gochara_interval(chart_id uuid,generation text,ayanamsha_id text,vedha_kind text,graha text,state text,t_in timestamptz,t_out timestamptz,detail jsonb)')
    conn.execute('CREATE TABLE kala_moorti_nirnaya_candidate(chart_id uuid,generation text,ayanamsha_id text,payload jsonb,method_qualification text,upstream_fingerprint jsonb)')
    conn.execute('CREATE TABLE kala_obstruction(chart_id uuid,generation text,assertion_id text,effective_state text,interval_start timestamptz,interval_end timestamptz,event_class_id text,assertion jsonb)')
    from datetime import datetime,timedelta,timezone
    from services.ka_kshetra import stage1_symbolization as S1
    from services.ka_kshetra.g1_inputs import load_suppression
    birth=datetime(1984,2,5,5,13,tzinfo=timezone.utc)
    gen='candidate:g1'; ayan='lahiri_chitrapaksha'
    conn.execute('INSERT INTO kala_vedha_gochara_interval VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (chart,gen,ayan,'house_vedha','Saturn','active',birth+timedelta(days=10),birth+timedelta(days=20),Jsonb({'vedha_house':4})))
    for state in ('obstruction_in_force','obstruction_cancelled','obstruction_partly_cancelled','obstruction_contested'):
        conn.execute('INSERT INTO kala_obstruction VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
            (chart,gen,state,state,birth+timedelta(days=11),birth+timedelta(days=12),'career',Jsonb({'acceptance_scope':'fixture_only'})))
    scoped=CandidateConnection(conn,gen)
    conn.execute("SET LOCAL TimeZone='UTC'")
    first,_=load_suppression(scoped,chart,gen,birth)
    conn.execute("SET LOCAL TimeZone='Asia/Kolkata'")
    second,_=load_suppression(scoped,chart,gen,birth)
    assert [vars(p) for p in first]==[vars(p) for p in second]
    ctx=SimpleNamespace(db_conn=scoped,dry_run=False,build_id=build,config={'chart_id':chart,
        'kshetra_g1_candidate':gen,'birth_params':{'datetime_iso':birth.isoformat()},'as_of':birth.isoformat()})
    result=S1.run_substep(ctx,SimpleNamespace(key='stage1:run'))
    rows=S4.load_primitives(scoped,chart)
    assert result.rows_inserted==5
    assert {r.source_table for r in rows}=={'kala_vedha_gochara_interval','kala_obstruction'}
    assert S4.EnvelopeIndex(rows,100).obstructions_at(11.5)
    # The same stored rows are omitted honestly outside an explicit fixture candidate.
    conn.execute("UPDATE kala_layer_candidate SET conventions='{}'::jsonb WHERE chart_id=%s",(chart,))
    prims,gaps=load_suppression(scoped,chart,gen,birth)
    assert not any(p.primitive_kind=='negative_space' for p in prims)
    assert any(g['reason']=='negative_space_binding_not_admitted' for g in gaps)


def test_candidate_resume_refuses_changed_inputs(data):
    conn,chart,build=data
    scoped=CandidateConnection(conn,'candidate:g1')
    writer=KaKshetraWriter();writer._chart_id=chart;writer._generation='candidate:g1'
    writer._snapshot_id='snapshot-before';writer._dhara_sweep_version=None;writer._event_classes=['career']
    writer._record_substep(scoped,'prepare:replace',0)
    writer._snapshot_id='snapshot-after'
    with pytest.raises(ValueError,match='new candidate'):
        writer._load_completed_substeps(scoped,chart,writer._fingerprint())


def test_rarity_can_read_a_real_cohort_through_the_candidate_connection(data):
    conn,chart,build=data
    from services.ka_kshetra.cohort_client import cohort_base_rate
    conn.execute('CREATE TEMP TABLE bg_synthetic_cohort(synthetic_id int, sampling_method text,ayanamsha_key text,positions jsonb)')
    conn.execute('CREATE TEMP TABLE bg_synthetic_cohort_md(synthetic_id int,chain_version text,md_lord text,start_age_years float,end_age_years float)')
    conn.execute("INSERT INTO bg_synthetic_cohort SELECT k,'fixture','lahiri',jsonb_build_object('Lagna',jsonb_build_object('sign_id',CASE WHEN k<=5000 THEN 1 ELSE 2 END)) FROM generate_series(1,10000) k")
    rate=cohort_base_rate('lagna_sign',1,conn=CandidateConnection(conn,'candidate:g1'))
    assert rate.p==.5 and rate.n==5000 and rate.n_total==10000
