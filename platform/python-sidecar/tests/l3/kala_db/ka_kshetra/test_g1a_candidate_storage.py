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
IDENTITY_REPAIR=ROOT/'migrations/1393_k5_g1a_candidate_identity.sql'


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
        # Current legacy window shape before the candidate LIKE copy (migration 571).
        body=(ROOT/'supabase/migrations/571_p3a_shape_only_tier.sql').read_text()
        conn.execute(re.search(r'ALTER TABLE kala_field_windows\s+ADD COLUMN[^;]*;',body)[0])
        conn.execute(MIGRATION.read_text())
        conn.execute(MIGRATION.read_text())  # reapplication must remain safe
        if IDENTITY_REPAIR.exists():
            conn.execute(IDENTITY_REPAIR.read_text())
            conn.execute(IDENTITY_REPAIR.read_text())
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


@pytest.mark.parametrize('identity', ['generation','chart_id'])
def test_candidate_identity_cannot_move_between_two_mutable_partitions(data, identity):
    """K5-G1a compatibility: an UPDATE cannot relabel an existing row.

    Both destinations are otherwise writable; a published-state guard alone
    cannot detect this transfer (migration_identity_immutable).
    """
    conn,chart,build = data
    insert_field(CandidateConnection(conn,'candidate:g1'),chart)
    destination = 'candidate:g2'
    if identity == 'chart_id':
        destination = str(uuid4()); target_build = str(uuid4())
        conn.execute('INSERT INTO build_runs VALUES(%s,%s)',(target_build,destination))
        conn.execute('INSERT INTO kala_layer_candidate VALUES(%s,%s,%s,%s,%s)',
                     (destination,'candidate:g1',target_build,'building',Jsonb({})))
    before = conn.execute('SELECT row_to_json(r)::text FROM kala_field_candidate r').fetchall()
    with pytest.raises(psycopg.errors.RaiseException,match='identity is immutable'):
        with conn.transaction():
            conn.execute(f'UPDATE kala_field_candidate SET {identity}=%s WHERE chart_id=%s',
                         (destination,chart))
    assert conn.execute('SELECT row_to_json(r)::text FROM kala_field_candidate r').fetchall() == before


def test_serving_head_rejects_writes_even_if_candidate_state_is_building(data):
    """Compatibility contract: the head wins over a stale building flag.

    Direct SQL bypasses bind_candidate so only the actual DB trigger can
    protect the already served rows (migration_serving_head_guard).
    """
    conn,chart,build = data
    scoped = CandidateConnection(conn,'candidate:g1'); insert_field(scoped,chart)
    conn.execute("UPDATE kala_layer_head SET generation='candidate:g1' WHERE chart_id=%s",(chart,))
    before = conn.execute('SELECT row_to_json(r)::text FROM kala_field_candidate r').fetchall()
    operations = [lambda:insert_field(scoped,chart,2.),
        lambda:conn.execute('UPDATE kala_field_candidate SET alpha=3 WHERE chart_id=%s',(chart,)),
        lambda:conn.execute('DELETE FROM kala_field_candidate WHERE chart_id=%s',(chart,))]
    for operation in operations:
        with pytest.raises(psycopg.errors.RaiseException,match='building candidate'):
            with conn.transaction(): operation()
    assert conn.execute('SELECT row_to_json(r)::text FROM kala_field_candidate r').fetchall() == before


def test_production_snapshot_and_timeline_store_the_actual_input_pins(data, monkeypatch):
    """ALGO §3.20(c,d,e), §N.4/N.8: pins must survive into stored outputs.

    Rarity references L1 in the declared ayanāṃśa; model coefficients and
    smoothing are engineering choices, never invented classical odds.
    Changing as_of or the suppression inputs must create a different snapshot.
    """
    from datetime import datetime,timezone,timedelta
    import hashlib, json
    from services.ka_kshetra import g1_inputs
    conn,chart,build = data
    # Main's G1b snapshot attestation consumes the manifest shape from migration
    # 1330; match its isolated DB oracle without weakening the production path.
    conn.execute("ALTER TABLE kala_layer_candidate ADD COLUMN model_digest text NOT NULL DEFAULT 'model', ADD COLUMN rule_registry_version text NOT NULL DEFAULT 'rules'")
    conn.execute('CREATE TABLE kala_layer_candidate_grain(chart_id uuid,generation text,grain_key text,result_state text,input_vector text,recorded_at timestamptz DEFAULT now(),PRIMARY KEY(chart_id,generation,grain_key))')
    birth = datetime(1984,2,5,5,13,tzinfo=timezone.utc)
    monkeypatch.setattr(S4,'resolve_weights_pin',lambda conn:('v0',{}))
    monkeypatch.setattr(KaKshetraWriter,'_corpus_pin',lambda *a:'test-corpus')
    monkeypatch.setattr(KaKshetraWriter,'_gochara_corpus_pin',lambda *a:{})
    monkeypatch.setattr(KaKshetraWriter,'_discover_event_classes',lambda *a:[])
    monkeypatch.setattr(KaKshetraWriter,'_load_completed_substeps',lambda *a:None)
    prims,gaps = g1_inputs.suppression_primitives(chart,birth,[{
        'graha':'Saturn','state':'active','t_in':birth+timedelta(days=10),
        't_out':birth+timedelta(days=20),'vedha_kind':'house_vedha','source_ref':'v1'}],[],[])
    snapshots = []
    for as_of,inputs in [('1994-02-05T23:00:00-04:00',prims),
                         ('1995-02-05T23:00:00-04:00',prims),
                         ('1994-02-05T23:00:00-04:00',[])]:
        monkeypatch.setattr(g1_inputs,'load_suppression',lambda *a:(inputs,gaps))
        ctx = SimpleNamespace(db_conn=conn,dry_run=False,build_id=build,config={
            'chart_id':chart,'kshetra_g1_candidate':'candidate:g1',
            'birth_params':{'datetime_iso':birth.isoformat()},'as_of':as_of})
        writer = KaKshetraWriter(); writer.plan_substeps(ctx)
        scoped = CandidateConnection(conn,'candidate:g1')
        writer._run_stage8(scoped,'now',SimpleNamespace(key='stage8:now'))
        writer._run_snapshot(scoped,SimpleNamespace(key='snapshot'))
        pin = conn.execute('SELECT config_pin FROM kala_field_snapshots_candidate WHERE field_snapshot_id=%s',
                           (writer._snapshot_id,)).fetchone()[0]
        # Independent digest of referenced input rows, not writer._suppression_pin.
        # §7.4 canonical operands encode floats as their round-trip strings.
        operands = json.loads(json.dumps([[vars(p) for p in inputs],gaps]),parse_float=str)
        encoded = json.dumps(operands,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        assert pin['suppression_input_digest'] == hashlib.sha256(encoded.encode()).hexdigest()
        expected_as_of = datetime.fromisoformat(as_of).astimezone(timezone.utc)
        assert pin['as_of'] == expected_as_of.isoformat()
        assert pin['birth_utc'] == '1984-02-05T05:13:00+00:00'
        assert pin['rarity_convention'] == {
            'ayanamsha_id':'lahiri_chitrapaksha','feature':'lagna_sign',
            'basis':'L1 longitude_sidereal','mapping':'floor(longitude_mod_360 / 30) + 1'}
        provenance = pin['constant_provenance']
        assert {'functional_form','coefficients','P_FLOOR','RHO_MAX','rho_default',
                'null','integrator','suppression_strength','moorti','time_units'} <= provenance.keys()
        assert all(isinstance(v,str) and v.strip() for v in provenance.values())
        assert 'engineering' in provenance['coefficients']
        assert 'no numeric bridge' in provenance['moorti']
        assert '1023 non-identity shifts' in provenance['null']
        assert pin['null_replicates'] == 1023
        spec = conn.execute('SELECT spec FROM kala_timeline_spec_candidate WHERE field_snapshot_id=%s',
                            (writer._snapshot_id,)).fetchone()[0]
        assert spec['now_marker'] == expected_as_of.date().isoformat()
        assert spec['now_marker'] != spec['t_zero'][:10]
        snapshots.append(writer._snapshot_id)
    assert len(set(snapshots)) == 3


@pytest.mark.parametrize('birth_iso,body', [
    ('1984-04-10T10:43:00+05:30','Sun'),
    ('2034-04-10T23:17:00-04:00','Moon'),
    ('1952-04-10T00:03:00+09:00','Sun'),
])
def test_stage0_dispatch_writes_birth_relative_roots_and_utc_timestamps(data, monkeypatch, birth_iso, body):
    """ALGO §3.20(d); W2 §3.1 sign = 30°, nakṣatra = 360°/27.

    Re-derive those angular-boundary rules from the stored roots, then check
    t_days=(event_ts-birth_UT)/86400 independently. Daily input positions use
    only the pinned real Swiss corpus; no alternate ephemeris or JH oracle.
    Exercises production dispatch, spline, root-finding and candidate storage.
    """
    from datetime import datetime,timedelta,timezone
    import os
    import swisseph as swe
    from services.ka_kshetra import stage0_kinematics as S0
    conn,chart,build = data
    birth = datetime.fromisoformat(birth_iso).astimezone(timezone.utc)
    conn.execute('CREATE TEMP TABLE ephemeris_daily(date date,body text,ayanamsha_id text,tropical_longitude float,latitude float,speed_dps float)')
    conn.execute('CREATE TEMP TABLE chart_facts(chart_id uuid,fact_id text,fact_subject text,fact_category text,fact_key text,ayanamsha_id text,fact_value_num float)')
    swe.set_ephe_path(os.environ['SE_EPHE_PATH'])
    for planet,code in [('Sun',swe.SUN),('Moon',swe.MOON)]:
        for day in range(-1,12):
            date = birth.date()+timedelta(days=day)
            jd = swe.julday(date.year,date.month,date.day,12.)
            pos,flags = swe.calc_ut(jd,code,swe.FLG_SWIEPH|swe.FLG_SPEED)
            assert flags & swe.FLG_SWIEPH, 'pinned Swiss files required; no fallback'
            conn.execute('INSERT INTO ephemeris_daily VALUES(%s,%s,%s,%s,%s,%s)',
                         (date,planet,'tropical',pos[0],pos[1],pos[3]))
    monkeypatch.setattr(S0,'HORIZON_DAYS',10.)
    scoped = CandidateConnection(conn,'candidate:g1')
    ctx = SimpleNamespace(db_conn=scoped,dry_run=False,config={
        'chart_id':chart,'birth_params':{'datetime_iso':birth_iso}})
    result = S0.run_substep(ctx,SimpleNamespace(key='stage0:'+body))
    rows = conn.execute('SELECT event_kind,t_days,event_ts,longitude_deg FROM kala_field_kinematics_candidate WHERE chart_id=%s',(chart,)).fetchall()
    assert result.rows_inserted == len(rows) > 0
    assert any(kind=='sign_ingress' for kind,*_ in rows)
    for kind,days,stamp,longitude in rows:
        assert -2 < days < 12
        assert days == pytest.approx((stamp-birth).total_seconds()/86400,abs=1e-9)
        assert birth-timedelta(days=2) < stamp < birth+timedelta(days=12)
        if kind in ('sign_ingress','nakshatra_ingress'):
            width = 30. if kind=='sign_ingress' else 360/27
            assert abs(float(longitude)/width-round(float(longitude)/width)) < 1e-6
            # Independently evaluate the real sky at the persisted UTC instant.
            # The daily Hermite representation has interpolation error; 0.002°
            # is well below a half-day epoch error even for the slow Sun.
            utc = stamp.astimezone(timezone.utc)
            hour = utc.hour+utc.minute/60+utc.second/3600+utc.microsecond/3.6e9
            jd = swe.julday(utc.year,utc.month,utc.day,hour)
            tropical,flags = swe.calc_ut(jd,swe.SUN if body=='Sun' else swe.MOON,
                                          swe.FLG_SWIEPH|swe.FLG_SPEED)
            assert flags & swe.FLG_SWIEPH
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            sidereal = (tropical[0]-swe.get_ayanamsa_ut(jd)) % 360
            angular_error = (sidereal-float(longitude)+180) % 360-180
            assert abs(angular_error) < .002



@pytest.mark.parametrize('table,columns,values', [
    ('kala_field_clocks', 'system_id,applicability_state,competence_class,seniority_rank,is_predictive',
     "'vimshottari','applicable','fruition',1,TRUE"),
    ('kala_field_boundaries', 'system_id,level,lord,t_boundary,period_days,sigma_t_days,interval_lo,interval_hi,precision_state,dominant_uncertainty_source,sigma_t_source,source_pk',
     "'vimshottari','MD','Jupiter',10,100,0,10,10,'instant','birth_time','fixture','d1'"),
    ('kala_timeline_spec', 'generated_for,field_snapshot_id,weights_version,spec,empty_reason',
     "'now','identity-fixture','v0','{}','honest_empty:fixture'"),
])
def test_forward_repair_preserves_rows_and_allocates_independent_identity(data, table, columns, values):
    """1385 LIKE loses IDENTITY. 1393 must repair populated candidates safely.

    Reconstruct the already-applied pre-repair state, preserving explicit IDs;
    then use the production no-id INSERT shape in both candidate partitions.
    Neither a legacy sequence nor the legacy rows may change.
    """
    conn,chart,build = data
    target = table+'_candidate'
    legacy = conn.execute(f'SELECT row_to_json(r)::text FROM {table} r').fetchall()
    source_seq = conn.execute("SELECT pg_get_serial_sequence(%s,'id')",(table,)).fetchone()[0]
    source_state = conn.execute(f'SELECT last_value,is_called FROM {source_seq}').fetchone()
    conn.execute(f'ALTER TABLE {target} ALTER COLUMN id DROP IDENTITY IF EXISTS')
    conn.execute(f"INSERT INTO {target}(id,chart_id,generation,{columns}) VALUES(700,%s,'candidate:g1',{values})",(chart,))
    if IDENTITY_REPAIR.exists():
        conn.execute(IDENTITY_REPAIR.read_text())
        conn.execute(IDENTITY_REPAIR.read_text())
    identity = conn.execute("SELECT identity_generation FROM information_schema.columns WHERE table_name=%s AND column_name='id'",(target,)).fetchone()[0]
    assert identity == 'ALWAYS'
    allocated = conn.execute(f"INSERT INTO {target}(chart_id,generation,{columns}) VALUES(%s,'candidate:g2',{values}) RETURNING id",(chart,)).fetchone()[0]
    assert allocated > 700
    assert conn.execute(f"SELECT id FROM {target} WHERE chart_id=%s AND generation='candidate:g1'",(chart,)).fetchone() == (700,)
    assert conn.execute("SELECT pg_get_serial_sequence(%s,'id')",(target,)).fetchone()[0] != source_seq
    assert conn.execute(f'SELECT last_value,is_called FROM {source_seq}').fetchone() == source_state
    assert conn.execute(f'SELECT row_to_json(r)::text FROM {table} r').fetchall() == legacy


def test_stage3_production_writers_allocate_candidate_ids_and_retry(data):
    """Legacy 490 identity contract survives candidate production upserts."""
    from services.ka_kshetra import stage3_clocks as S3
    from services.ka_kshetra.contracts import ClockApplicability
    conn,chart,build = data
    scoped = CandidateConnection(conn,'candidate:g1')
    clocks = [ClockApplicability('vimshottari','applicable','fruition',1,True,.9)]
    boundaries = [S3.BoundaryRow('vimshottari','MD','Jupiter',[],10.,100.,0.,10.,10.,
                               'instant','birth_time','fixture','d1')]
    for repeat in range(2):
        assert S3.write_clock_rows(chart,clocks,scoped) == 1
        assert S3.write_boundary_rows(chart,'vimshottari',boundaries,scoped) == 1
        for table in ('kala_field_clocks_candidate','kala_field_boundaries_candidate'):
            rows = conn.execute(f'SELECT id FROM {table} WHERE chart_id=%s',(chart,)).fetchall()
            assert len(rows) == 1 and isinstance(rows[0][0],int)
