"""K8 registry-only correction: execute the shipped SQL, preserve every identity/row."""
from pathlib import Path
import json
import re

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[6]
MIGRATION = ROOT / 'platform/migrations/1392_k8_registry_truth.sql'


def sql():
    assert MIGRATION.exists(), 'K8 registry truth migration has not been built'
    return MIGRATION.read_text()


def rows():
    return json.loads(re.search(r'\$k8_rows\$(.*?)\$k8_rows\$', sql(), re.S)[1])


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute('''CREATE TABLE public.asset_registry (
          asset_id text PRIMARY KEY, depends_on text[], has_substeps boolean,
          count_sql text, integrity_check_sql text, is_active boolean,
          catalog_status text, superseded_by text, data_disposition text,
          has_writer boolean, target_table text, clear_tables text[], natural_key_partition text)''')
        conn.execute("""ALTER TABLE public.asset_registry
          ADD COLUMN layer text, ADD COLUMN sort_order int, ADD COLUMN sanskrit_name text,
          ADD COLUMN english_name text, ADD COLUMN english_description text,
          ADD COLUMN storage_type text, ADD COLUMN size_sql text, ADD COLUMN target_floor int,
          ADD COLUMN expected_volume_formula text, ADD COLUMN expected_volume_inputs jsonb,
          ADD COLUMN volume_explanation text, ADD COLUMN scope text,
          ADD COLUMN estimated_seconds int, ADD COLUMN asset_type text,
          ADD COLUMN layer_name text, ADD COLUMN layer_index text,
          ADD COLUMN provides_apis jsonb, ADD COLUMN health_probe jsonb,
          ADD COLUMN asset_kind text, ADD COLUMN writer_timeout_seconds int""")
        ids = re.findall(r"^    asset_id: '([^']+)'", (ROOT / 'platform/scripts/seed/asset_registry_seed.ts').read_text(), re.M)
        for aid in ids:
            conn.execute('''INSERT INTO public.asset_registry (asset_id,depends_on,has_substeps,count_sql,integrity_check_sql,is_active,catalog_status,superseded_by,data_disposition,has_writer,target_table,clear_tables,natural_key_partition) VALUES
              (%s, ARRAY['old'],false,'SELECT 17','SELECT false',false,
               'CURRENT',NULL,NULL,true,'kept',ARRAY['kept'],'kept')''', (aid,))
        conn.execute("UPDATE asset_registry SET catalog_status='RETIRED' WHERE asset_id='ka_gochara_sweep'")
        conn.execute('CREATE TABLE public.retained_payload (chart_id text,generation text,payload jsonb)')
        conn.execute('''INSERT INTO retained_payload VALUES ('A','legacy','{"value":1}'),
          ('A','candidate:a','{"value":2}'),('B','candidate:b','{"value":3}')''')
        yield conn
        conn.rollback()


def snapshot(conn, table):
    return conn.execute(f'SELECT to_jsonb(t) FROM {table} t ORDER BY to_jsonb(t)::text').fetchall()


def test_twice_applied_registry_correction_preserves_ids_foreign_rows_and_retained_data(db):
    before = snapshot(db, 'asset_registry')
    data = snapshot(db, 'retained_payload')
    db.execute(sql())
    once = snapshot(db, 'asset_registry')
    assert once != before, 'correction must change stale registry truth'
    db.execute(sql())
    assert snapshot(db, 'asset_registry') == once
    assert snapshot(db, 'retained_payload') == data
    old = {r[0]['asset_id']:r[0] for r in before}
    new = {r[0]['asset_id']:r[0] for r in once}
    assert old.keys() == new.keys()
    for aid, row in old.items():
        if not aid.startswith('ka_'):
            assert new[aid] == row
        for field in ('is_active','integrity_check_sql','target_table','clear_tables','natural_key_partition'):
            assert new[aid][field] == row[field], (aid, field)
    for row in rows():
        assert new[row['asset_id']]['depends_on'] == row['depends_on']
        assert new[row['asset_id']]['has_writer'] == row['has_writer']
        assert new[row['asset_id']]['has_substeps'] == row['has_substeps']
        if 'count_sql' in row:
            assert new[row['asset_id']]['count_sql'] == row['count_sql']
    assert new['ka_gochara_sweep']['data_disposition'] == 'RETAINED_AS_CAPITAL'


def test_missing_identity_refuses_atomically(db):
    db.execute("DELETE FROM asset_registry WHERE asset_id='ka_yojaka'")
    before = snapshot(db, 'asset_registry')
    with pytest.raises(psycopg.Error, match='missing.*ka_yojaka'):
        with db.transaction():
            db.execute(sql())
    assert snapshot(db, 'asset_registry') == before


def test_wrong_namespace_and_duplicate_identity_payloads_refuse(db):
    for original, mutant in [('"ka_yojaka"','"ga_positions"'), ('"ka_yojaka"','"ka_sangam"')]:
        with pytest.raises(psycopg.Error, match='K8'):
            with db.transaction():
                db.execute(sql().replace(original,mutant))


def test_only_chart_counters_are_assigned_and_services_keep_null(db):
    db.execute(sql())
    for row in rows():
        if 'count_sql' not in row:
            continue
        query = row['count_sql']
        assert '$1' in query and re.search(r'\bFROM\b',query,re.I)
        assert not re.search(r'\b(?:DELETE|UPDATE|INSERT)\b',query,re.I)
    for aid in ('ka_dasha_kala','ka_graha_sancara','ka_muhurta_seva','ka_tulana'):
        assert 'count_sql' not in next(r for r in rows() if r['asset_id']==aid)


def test_real_seed_upsert_cannot_restore_stale_edges_counters_or_retirements(db):
    db.execute(sql())
    seed=(ROOT/'platform/scripts/seed/asset_registry_seed.ts').read_text()
    upsert=seed.split('export const ASSET_REGISTRY_UPSERT_SQL = `',1)[1].split('`',1)[0]
    # Execute the real upsert, with numbered placeholders translated for psycopg.
    upsert=re.sub(r'\$\d+','%s',upsert)
    for aid in ('ka_gochara_sweep','ka_sangam','ka_avadhi'):
        before=db.execute('SELECT depends_on,count_sql,has_writer,has_substeps,catalog_status,data_disposition FROM asset_registry WHERE asset_id=%s',(aid,)).fetchone()
        values=[aid,'kala',1,'name','name','description','postgres_table','kept',
          'SELECT 999',None,None,None,None,None,['obsolete'],'per_chart',True,None,
          'data','Kāla','L3',None,None,'CURRENT','data',True,False,600]
        db.execute(upsert,values)
        assert db.execute('SELECT depends_on,count_sql,has_writer,has_substeps,catalog_status,data_disposition FROM asset_registry WHERE asset_id=%s',(aid,)).fetchone()==before
    assert db.execute("SELECT is_active FROM asset_registry WHERE asset_id='ka_gochara_sweep'").fetchone()==(False,)


def test_real_generation_counters_ignore_other_charts_and_retained_candidates_after_completion(db):
    a='00000000-0000-0000-0000-000000000001';b='00000000-0000-0000-0000-000000000002'
    run_a='10000000-0000-0000-0000-000000000001'
    run_b='10000000-0000-0000-0000-000000000002'
    db.execute('CREATE TABLE build_runs(id uuid,chart_id uuid,created_at timestamptz)')
    db.execute('CREATE TABLE kala_layer_candidate(chart_id uuid,build_id uuid,generation text,conventions jsonb)')
    db.execute('CREATE TABLE kala_layer_head(chart_id uuid,generation text)')
    for chart,run in ((a,run_a),(b,run_b)):
        db.execute("INSERT INTO build_runs VALUES (%s,%s,'2026-01-01Z')",(run,chart))
        db.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,'candidate:new','{\"fixture\":true}')",(chart,run))
    db.execute("INSERT INTO kala_layer_head VALUES (%s,'candidate:new')",(a,))
    for table in ('kala_activation','kala_darshana','kala_jivana_parva'):
        db.execute(f'CREATE TABLE {table}(chart_id uuid)')
        db.execute(f'CREATE TABLE {table}_candidate(chart_id uuid,generation text)')
        db.execute(f'INSERT INTO {table} VALUES (%s),(%s),(%s)',(a,a,b))
        for chart,generation,n in ((a,'candidate:old',3),(a,'candidate:new',1),(b,'candidate:new',4)):
            db.execute(f'INSERT INTO {table}_candidate SELECT %s,%s FROM generate_series(1,%s)',(chart,generation,n))
    db.execute('CREATE TABLE kala_avadhi(chart_id uuid,generation text)')
    db.execute("INSERT INTO kala_avadhi VALUES (%s,'legacy'),(%s,'candidate:new'),(%s,'candidate:old'),(%s,'candidate:new')",(a,a,a,b))
    db.execute(sql())
    assert {r['asset_id'] for r in rows() if 'count_sql' in r} == {'ka_avadhi','ka_kalasutra','ka_kala_darshana','ka_jivana_parva'}
    for row in rows():
        if 'count_sql' not in row:continue
        query=row['count_sql'];q=query.replace('$1','%s'); params=[a]*query.count('$1')
        assert db.execute(q,params).fetchone()==(1,),row['asset_id']
        if row['asset_id']=='ka_avadhi':continue
        table={'ka_kalasutra':'kala_activation','ka_kala_darshana':'kala_darshana','ka_jivana_parva':'kala_jivana_parva'}[row['asset_id']]
        db.execute(f"INSERT INTO {table}_candidate VALUES (%s,'candidate:new')",(a,))
        assert db.execute(q,params).fetchone()==(2,)
        db.execute(f"DELETE FROM {table}_candidate WHERE chart_id=%s AND generation='candidate:new'",(a,))
        assert db.execute(q,params).fetchone()==(0,)
        db.execute("UPDATE kala_layer_candidate SET conventions='{}' WHERE chart_id=%s",(a,))
        assert db.execute(q,params).fetchone()==(2,) # explicit legacy mode, not total rows
        db.execute("UPDATE kala_layer_candidate SET conventions='{\"fixture\":true}' WHERE chart_id=%s",(a,))


def test_bad_boolean_shape_and_unknown_dependency_refuse_before_any_update(db):
    before=snapshot(db,'asset_registry')
    for mutant in (sql().replace('"has_writer": true','"has_writer": null',1),
                   sql().replace('"bg_gochara_arcs"','"ka_not_registered"',1)):
        with pytest.raises(psycopg.Error,match='K8'):
            with db.transaction():db.execute(mutant)
        assert snapshot(db,'asset_registry')==before
