"""K6-4 SQL-backed oracles; all numbers are synthetic, never chart facts.

Source shape: K5-G1a migration 1385 sibling field/snapshot tables; base
migration 492 defines the log-linear coefficients and integral units.
"""
import json
import math
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest
from psycopg.types.json import Jsonb

from pipeline.orchestrator.writers.ka_taranga import KaTarangaWriter

PLATFORM = Path(__file__).resolve().parents[5]
CHART = '00000000-0000-0000-0000-000000000641'
OTHER = '00000000-0000-0000-0000-000000000642'
BUILD = '00000000-0000-0000-0000-000000000643'
GEN = 'candidate:k6-4'
MIGRATION = PLATFORM / 'migrations/1389_k6_taranga_candidate.sql'


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute('''CREATE TABLE kala_layer_candidate(chart_id uuid,generation text,build_id uuid,
            state text,conventions jsonb,PRIMARY KEY(chart_id,generation));
            CREATE TABLE kala_layer_head(chart_id uuid,generation text);
            CREATE TABLE build_runs(id uuid,chart_id uuid,state text,created_at timestamptz);
            CREATE TABLE asset_registry(asset_id text PRIMARY KEY,count_sql text,integrity_check_sql text);
            CREATE TABLE kala_taranga(chart_id uuid,month date,scope_kind text,scope_id text,activation numeric,components jsonb);
            CREATE TABLE kala_field_candidate(chart_id uuid,generation text,event_class text,segment_index int,
                t_start float8,t_end float8,alpha float8,gamma float8,integral_days float8,field_snapshot_id text);
            CREATE TABLE kala_field_snapshots_candidate(chart_id uuid,generation text,field_snapshot_id text,
                field_content_hash text,config_pin jsonb,event_classes text[],skipped_classes jsonb);
            CREATE TABLE ka_gochara_eval_window(window_id uuid,chart_id uuid,generation text,event_class text,interval tstzrange);''')
        conn.execute("INSERT INTO asset_registry VALUES ('ka_taranga','SELECT 0','SELECT false')")
        conn.execute("INSERT INTO build_runs VALUES (%s,%s,'completed','2000-01-01')", (BUILD,CHART))
        conn.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,'building','{}')", (CHART,GEN,BUILD))
        conn.execute("INSERT INTO kala_taranga VALUES (%s,'1999-01-01','domain','fixture',0.75,'{\"legacy\":true}')", (CHART,))
        conn.execute(MIGRATION.read_text())
        conn.execute(MIGRATION.read_text())  # migration reapplication must be harmless
        yield conn
        conn.rollback()


def context(db, **config):
    return SimpleNamespace(db_conn=db, build_id=BUILD, dry_run=False,
        config={'chart_id': CHART, 'taranga_candidate': True, **config})


def snapshot(db, **extra):
    # Non-midnight UTC origin tests that day 0 is not coerced to a date.
    pin = dict(birth_utc='2000-01-31T12:00:00+00:00',
               axis='days_since_birth_UT; ephemeris_daily_noon_UT', **extra)
    db.execute('INSERT INTO kala_field_snapshots_candidate VALUES (%s,%s,\'snap\',\'content\',%s,ARRAY[\'gain\'],\'[]\')',
               (CHART,GEN,Jsonb(pin)))


def segment(db, *, event='gain', index=0, start=0., end=2., alpha=0., gamma=0.):
    integral = math.exp(alpha) * (end-start) if gamma == 0 else math.exp(alpha)*math.expm1(gamma*(end-start))/gamma
    db.execute('INSERT INTO kala_field_candidate VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,\'snap\')',
               (CHART,GEN,event,index,start,end,alpha,gamma,integral))


def rows(db):
    return db.execute('SELECT month::text,scope_kind,scope_id,integral,units,risk_set,risk_set_null_reason,'
        'judge_window_count,judge_count_null_reason,overlap_flag,source_refs '
        'FROM kala_taranga_candidate WHERE chart_id=%s AND generation=%s ORDER BY month,scope_kind,scope_id',
        (CHART,GEN)).fetchall()


def test_month_clips_exact_integrals_units_and_honest_nulls(db):
    snapshot(db); segment(db)
    result = KaTarangaWriter().run(context(db))
    assert result.rows_inserted == 2
    data = rows(db)
    assert [(r[0],r[1],r[2],r[3],r[4]) for r in data] == [
        ('2000-01-01','event_class','gain',0.5,'expected_events'),
        ('2000-02-01','event_class','gain',1.5,'expected_events')]
    assert all(r[5] is None and r[6] == 'upstream_risk_set_unavailable' for r in data)
    assert all(r[7] is None and r[8] == 'judge_generation_unpinned' for r in data)
    assert all(r[10]['field_snapshot_ids'] == ['snap'] for r in data)


@pytest.mark.parametrize('gamma', [math.log(2), 1e-10, -math.log(2)])
def test_nonflat_segments_use_shared_exact_integrator(db, gamma):
    snapshot(db); segment(db, gamma=gamma)
    KaTarangaWriter().run(context(db))
    data = rows(db)
    expected_jan = math.expm1(gamma*.5)/gamma
    expected_feb = math.exp(gamma*.5)*math.expm1(gamma*1.5)/gamma
    assert [r[3] for r in data] == pytest.approx([expected_jan,expected_feb], rel=1e-12)


def test_duplicate_segments_and_mapping_labels_do_not_multiply_counts(db):
    snapshot(db); segment(db); segment(db)  # duplicate source join label
    for domain,source in [('money','source-1'),('money','source-2'),('work','source-1')]:
        db.execute('INSERT INTO kala_taranga_class_domain VALUES (%s,%s,\'gain\',%s,%s)', (CHART,GEN,domain,source))
    KaTarangaWriter().run(context(db))
    data = rows(db)
    assert len(data) == 6
    assert [r[3] for r in data] == [0.5]*3+[1.5]*3
    assert all(r[9] for r in data)
    assert all(len(r[10]['class_domain_sources']) >= 1 for r in data if r[1]=='domain')


def test_utc_leap_month_boundary_and_disjoint_segments(db):
    snapshot(db)
    segment(db,start=.5,end=29.5)  # exactly February in leap year 2000
    segment(db,index=1,start=29.5,end=30.5,alpha=math.log(2))
    KaTarangaWriter().run(context(db))
    assert [(r[0],r[3]) for r in rows(db)] == [('2000-02-01',29.0),('2000-03-01',2.0)]


def test_judge_count_is_distinct_pinned_and_separate_from_integral(db):
    snapshot(db); segment(db)
    db.execute("UPDATE kala_layer_candidate SET conventions='{\"taranga_judge_generation\":\"5.fixture\"}'")
    for identity,gen,start,end in [('00000000-0000-0000-0000-000000000650','5.fixture','2000-02-01','2000-03-01'),
                                   ('00000000-0000-0000-0000-000000000651','wrong','2000-01-01','2000-03-01')]:
        for _ in range(2):
            db.execute('INSERT INTO ka_gochara_eval_window VALUES (%s,%s,%s,\'gain\',tstzrange(%s,%s,\'[)\'))',
                       (identity,CHART,gen,start+'T00:00:00+00:00',end+'T00:00:00+00:00'))
    KaTarangaWriter().run(context(db))
    assert [(r[3],r[7],r[8]) for r in rows(db)] == [(0.5,0,None),(1.5,1,None)]


def test_rebuild_duplicate_insertion_and_unbound_dispatch_preserve_legacy(db):
    snapshot(db); segment(db)
    legacy = db.execute('SELECT to_jsonb(t) FROM kala_taranga t').fetchall()
    KaTarangaWriter().run(context(db)); first = rows(db)
    KaTarangaWriter().run(context(db)); assert rows(db) == first
    unbound = context(db); unbound.build_id = OTHER
    assert KaTarangaWriter().run(unbound).rows_inserted == 0
    assert rows(db) == first
    assert db.execute('SELECT to_jsonb(t) FROM kala_taranga t').fetchall() == legacy


@pytest.mark.parametrize('change', ["UPDATE kala_layer_candidate SET state='published'",
    "INSERT INTO kala_layer_head VALUES ('"+CHART+"','"+GEN+"')",
    "UPDATE build_runs SET chart_id='"+OTHER+"'"])
def test_wrong_build_and_published_candidates_cannot_be_replaced(db,change):
    snapshot(db); segment(db)
    db.execute(change)
    with pytest.raises(ValueError,match='candidate|build|published'):
        KaTarangaWriter().run(context(db))
    assert not rows(db)


@pytest.mark.parametrize('invalid', ['overlap','conflicting_duplicate','missing_origin','unfinalized','nonfinite'])
def test_invalid_source_is_rejected_before_replacement(db,invalid):
    snapshot(db); segment(db)
    KaTarangaWriter().run(context(db)); before = rows(db)
    if invalid=='overlap': segment(db,index=1,start=1,end=3)
    if invalid=='conflicting_duplicate': segment(db,alpha=1)
    if invalid=='missing_origin': db.execute("UPDATE kala_field_snapshots_candidate SET config_pin='{}'")
    if invalid=='unfinalized': db.execute('UPDATE kala_field_snapshots_candidate SET field_content_hash=NULL')
    if invalid=='nonfinite': db.execute("UPDATE kala_field_candidate SET alpha='NaN'")
    with pytest.raises(ValueError): KaTarangaWriter().run(context(db))
    assert rows(db) == before


def test_count_and_integrity_are_chart_build_bound_after_completion(db):
    snapshot(db); segment(db)
    KaTarangaWriter().run(context(db))
    count, integrity = db.execute("SELECT count_sql,integrity_check_sql FROM asset_registry WHERE asset_id='ka_taranga'").fetchone()
    assert db.execute(count.replace('$1','%s'),(CHART,)*count.count('$1')).fetchone()[0] == 2
    assert db.execute(count.replace('$1','%s'),(OTHER,)*count.count('$1')).fetchone()[0] == 0
    assert db.execute(integrity).fetchone()[0] is True
    db.execute("SELECT set_config('kala.integrity_build_id',%s,true)",(OTHER,))
    assert db.execute(integrity).fetchone()[0] is False
    db.execute("SELECT set_config('kala.integrity_build_id',%s,true)",(BUILD,))
    db.execute("UPDATE kala_taranga_candidate SET source_refs='{}'")
    assert db.execute(integrity).fetchone()[0] is False


def test_storage_refuses_published_mutation_even_outside_writer(db):
    snapshot(db); segment(db)
    KaTarangaWriter().run(context(db))
    db.execute("UPDATE kala_layer_candidate SET state='published'")
    with pytest.raises(psycopg.Error,match='building|published'):
        with db.transaction(): db.execute('DELETE FROM kala_taranga_candidate')


@pytest.mark.parametrize('table', ['kala_taranga_candidate','kala_taranga_class_domain'])
def test_truncate_cannot_bypass_generation_immutability(db, table):
    snapshot(db); segment(db)
    KaTarangaWriter().run(context(db))
    db.execute("UPDATE kala_layer_candidate SET state='published'")
    with pytest.raises(psycopg.Error,match='TRUNCATE'):
        with db.transaction(): db.execute('TRUNCATE '+table)


def test_server_timezone_does_not_change_utc_months(db):
    snapshot(db); segment(db)
    db.execute("SET LOCAL TIME ZONE 'Pacific/Honolulu'")
    KaTarangaWriter().run(context(db)); first = rows(db)
    db.execute("SET LOCAL TIME ZONE 'Asia/Kolkata'")
    KaTarangaWriter().run(context(db))
    assert rows(db) == first


def test_source_and_replacement_are_scoped_to_chart_and_generation(db):
    snapshot(db); segment(db)
    # A foreign source with the same class/index must neither conflict nor add.
    db.execute('INSERT INTO kala_field_candidate SELECT chart_id,\'candidate:other\',event_class,segment_index,'
        't_start,t_end,alpha,gamma,integral_days,field_snapshot_id FROM kala_field_candidate')
    db.execute('INSERT INTO kala_field_candidate SELECT %s, generation,event_class,segment_index,'
        't_start,t_end,alpha,gamma,integral_days,field_snapshot_id FROM kala_field_candidate WHERE generation=%s', (OTHER,GEN))
    KaTarangaWriter().run(context(db))
    # Retain one old candidate's output as published, then rebuild this one.
    old_build='00000000-0000-0000-0000-000000000644'
    db.execute("INSERT INTO build_runs VALUES (%s,%s,'completed','1999-01-01')",(old_build,CHART))
    db.execute("INSERT INTO kala_layer_candidate VALUES (%s,'candidate:old',%s,'building','{}')", (CHART,old_build))
    db.execute('''INSERT INTO kala_taranga_candidate SELECT chart_id,'candidate:old',month,scope_kind,scope_id,
        integral,units,risk_set,risk_set_null_reason,judge_window_count,judge_count_null_reason,
        overlap_flag,source_refs,formula_version FROM kala_taranga_candidate''')
    db.execute("UPDATE kala_layer_candidate SET state='published' WHERE generation='candidate:old'")
    old=db.execute("SELECT to_jsonb(t) FROM kala_taranga_candidate t WHERE generation='candidate:old' ORDER BY month").fetchall()
    KaTarangaWriter().run(context(db))
    assert [(r[0],r[3]) for r in rows(db)] == [('2000-01-01',0.5),('2000-02-01',1.5)]
    assert db.execute("SELECT to_jsonb(t) FROM kala_taranga_candidate t WHERE generation='candidate:old' ORDER BY month").fetchall() == old


def test_two_classes_share_domain_without_blending(db):
    snapshot(db); segment(db); segment(db,event='work',alpha=math.log(2))
    for event in ('gain','work'):
        db.execute("INSERT INTO kala_taranga_class_domain VALUES (%s,%s,%s,'shared','fixture-source')", (CHART,GEN,event))
    KaTarangaWriter().run(context(db))
    data=rows(db)
    assert [(r[0],r[3],r[4]) for r in data if r[1]=='domain'] == [
        ('2000-01-01',1.5,'expected_events'),('2000-02-01',4.5,'expected_events')]
    assert all(not r[9] for r in data)
