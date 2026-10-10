"""Real SQL, real migrated index, repeat-build and serving isolation oracles."""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import psycopg
import psycopg.rows
import pytest
from psycopg.types.json import Jsonb

from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter

PLATFORM = Path(__file__).resolve().parents[5]
CHART = '00000000-0000-0000-0000-000000000361'
BUILD = '00000000-0000-0000-0000-000000000362'
NATAL = '00000000-0000-0000-0000-000000000363'
DASHA = '00000000-0000-0000-0000-000000000364'
MD = '00000000-0000-0000-0000-000000000365'
AD = '00000000-0000-0000-0000-000000000366'
GEN = 'candidate:CODEX-k1-2'
AYA = 'lahiri_chitrapaksha'


def seed(conn, *, migrate=True):
    conn.execute((PLATFORM / 'supabase/migrations/395_kala_avadhi.sql').read_text().split('INSERT INTO asset_registry')[0].replace('BEGIN;', ''))
    conn.execute('''CREATE TABLE asset_registry(asset_id text PRIMARY KEY, integrity_check_sql text, depends_on text[], count_sql text);
        CREATE TABLE chart_dashas(dasha_row_id uuid, chart_id uuid, build_id uuid, ayanamsha_id text,
          verification_pass_status text, system_id text, level_n int, lord_graha text, parent_row_id uuid,
          start_iso timestamptz, end_iso timestamptz, start_date date, end_date date,
          applies_to_this_chart_flag bool, is_truncated_at_window_start bool,
          is_truncated_at_window_end bool, lord_to_parent_relationship text);
        CREATE TABLE chart_facts(fact_id text, chart_id uuid, build_id uuid, ayanamsha_id text,
          verification_pass_status text, fact_category text, fact_subject text, fact_key text,
          fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, citation_ref text);
        CREATE TABLE bodha_pratijna(chart_id uuid, pratijna_id uuid);
        CREATE TABLE kala_activation_predicates(id bigint, chart_id uuid, generation text,
          ayanamsha_id text, mechanism_id text, mechanism_route text, event_class_id text,
          derivation_ledger_jsonb jsonb, conclusion_state_jsonb jsonb);
        CREATE TABLE kala_layer_candidate(chart_id uuid, generation text, build_id uuid, state text, conventions jsonb);
        CREATE TABLE kala_layer_head(chart_id uuid, generation text);''')
    check = (PLATFORM / 'migrations/1023_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql').read_text().split('$ck$')[1]
    conn.execute("INSERT INTO asset_registry VALUES ('ka_avadhi',%s,ARRAY['ga_dashas'],NULL)", (check,))
    if migrate:
        conn.execute((PLATFORM / 'migrations/1341_k1_2_avadhi_candidate_dossiers.sql').read_text())
    pins = {'f2': {'build_id': DASHA, 'ayanamsha_id': AYA, 'tier': 'verified', 'systems': ['vimshottari']},
            'natal': {'build_id': NATAL, 'ayanamsha_id': AYA, 'tier': 'verified'}, 'node_model': 'mean'}
    conn.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,'building',%s)", (CHART, GEN, BUILD, Jsonb(pins)))
    for row_id, lord, level, parent, start, end in [
        (MD, 'Mars', 1, None, '1999-01-01T12:00:00Z', '2002-01-01T12:00:00Z'),
        (AD, 'Venus', 2, MD, '2000-01-01T12:00:00Z', '2001-01-01T12:00:00Z')]:
        conn.execute('''INSERT INTO chart_dashas VALUES (%s,%s,%s,%s,'verified','vimshottari',%s,%s,%s,
            %s,%s,%s::timestamptz::date,%s::timestamptz::date,true,false,false,'friend')''',
            (row_id, CHART, DASHA, AYA, level, lord, parent, start, end, start, end))
        conn.execute('''INSERT INTO kala_avadhi(chart_id,system_id,level_n,lord_graha,period_start,period_end,dossier)
            VALUES (%s,'vimshottari',%s,%s,%s::timestamptz::date,%s::timestamptz::date,%s)''',
            (CHART, level, lord, start, end, Jsonb({'lord_condition_fact_refs': [
                {'fact_id': f'CODEX-{lord}-house', 'fact_subject': 'MAR' if lord == 'Mars' else 'VEN'}]})))
    for graha, code, house in [('Mars', 'MAR', 3), ('Venus', 'VEN', 7)]:
        for key, value in [('house_d1', house), ('longitude_sidereal', 12), ('retrograde_flag', 'direct')]:
            conn.execute('''INSERT INTO chart_facts VALUES (%s,%s,%s,%s,'verified','graha_position',%s,%s,%s,%s,NULL,'CODEX-l1')''',
                (f'CODEX-{graha}-house' if key == 'house_d1' else f'CODEX-{graha}-{key}', CHART, NATAL, AYA, code, key,
                 value if isinstance(value, str) else None, value if isinstance(value, int) else None))
    conn.execute("INSERT INTO chart_facts VALUES ('CODEX-Mars-dignity',%s,%s,%s,'verified','graha_dignity_per_varga','D1_MAR','dignity_state','own',NULL,'{\"varga\":\"D1\"}','CODEX-l1')", (CHART, NATAL, AYA))
    ledger = {'constituent_planets': ['Mars'], 'fact_ids': ['CODEX-Mars-house'], 'source': 'CODEX-rule',
              'graph_edges': [{'polarity': 'supports'}], 'rule_version': 'v1'}
    conn.execute("INSERT INTO kala_activation_predicates VALUES (%s,%s,%s,%s,'CODEX-f1','admitted','major_gain',%s,%s)",
                 (1, CHART, GEN, AYA, Jsonb(ledger), Jsonb({'effective_state': 'defeated'})))


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        seed(conn)
        yield conn
        conn.rollback()


def ctx(conn):
    return SimpleNamespace(db_conn=conn, config={'chart_id': CHART}, build_id=BUILD, dry_run=False)


def rows(conn):
    return conn.execute("SELECT lord_graha,dossier FROM kala_avadhi WHERE generation=%s ORDER BY level_n", (GEN,)).fetchall()


def test_build_twice_has_zero_net_rows_and_identical_dossiers(db):
    writer = KaAvdhiWriter(); writer.run(ctx(db)); first = rows(db); writer.run(ctx(db))
    assert rows(db) == first and len(first) == 2


def test_rebuild_preserves_entire_legacy_rows(db):
    legacy = db.execute("SELECT * FROM kala_avadhi WHERE generation='legacy'").fetchall()
    KaAvdhiWriter().run(ctx(db))
    assert db.execute("SELECT * FROM kala_avadhi WHERE generation='legacy'").fetchall() == legacy


def test_actual_serving_filters_exclude_candidate_rows(db):
    source = (PLATFORM / 'src/lib/retrieval/registry/layers/L3_kala/query_dasha_dossier.ts').read_text()
    filters = source.split('const filters: string[] = [', 1)[1].split(']', 1)[0]
    assert '"generation = \'legacy\'"' in filters


def test_real_sql_dignity_change_affects_only_mars(db):
    writer = KaAvdhiWriter(); writer.run(ctx(db)); first = dict(rows(db))
    db.execute("UPDATE chart_facts SET fact_value_text='debilitated' WHERE fact_id='CODEX-Mars-dignity'")
    writer.run(ctx(db))
    assert [lord for lord, dossier in rows(db) if dossier != first[lord]] == ['Mars']


def test_mechanism_does_not_attach_to_nonparticipating_lord(db):
    KaAvdhiWriter().run(ctx(db))
    assert dict(rows(db))['Venus']['attached_mechanisms'] == []


def test_candidate_has_no_quality_labels_or_scores(db):
    KaAvdhiWriter().run(ctx(db))
    assert db.execute("SELECT quality FROM kala_avadhi WHERE generation=%s", (GEN,)).fetchall() == [(None,), (None,)]


@pytest.mark.parametrize('state,head', [('published', None), ('building', GEN)])
def test_current_and_retained_published_candidates_are_immutable(db, state, head):
    db.execute('UPDATE kala_layer_candidate SET state=%s', (state,))
    if head: db.execute('INSERT INTO kala_layer_head VALUES (%s,%s)', (CHART, head))
    with pytest.raises(ValueError): KaAvdhiWriter().run(ctx(db))


def test_missing_candidate_keeps_old_main_build_nonmutating(db):
    db.execute('DELETE FROM kala_layer_candidate')
    before = db.execute('SELECT * FROM kala_avadhi').fetchall()
    KaAvdhiWriter().run(ctx(db))
    assert db.execute('SELECT * FROM kala_avadhi').fetchall() == before


def test_migration_is_repeatable_and_real_detector_accepts_both_partitions(db):
    db.execute((PLATFORM / 'migrations/1341_k1_2_avadhi_candidate_dossiers.sql').read_text())
    KaAvdhiWriter().run(ctx(db))
    check = db.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_avadhi'").fetchone()[0]
    assert db.execute(check).fetchone()[0] is True


def test_mixed_pin_cannot_change_existing_candidate_partition(db):
    db.execute("UPDATE kala_layer_candidate SET conventions=jsonb_set(conventions,'{natal,ayanamsha_id}','\"true_chitra\"')")
    with pytest.raises(ValueError): KaAvdhiWriter().run(ctx(db))


@pytest.mark.parametrize('mutation', [
    "source_natal_build_id='00000000-0000-0000-0000-000000000999'",
    "dossier=jsonb_set(dossier,'{lord_condition}','{\"value\":null,\"null_reason\":null}')",
    "dossier=jsonb_set(dossier,'{attached_mechanisms,0,effective_state}','\"in_force\"')",
])
def test_real_detector_rejects_unsourced_pin_untyped_null_and_cancelled_promotion_mutants(db, mutation):
    KaAvdhiWriter().run(ctx(db))
    db.execute(f"UPDATE kala_avadhi SET {mutation} WHERE generation=%s AND lord_graha='Mars'", (GEN,))
    check = db.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_avadhi'").fetchone()[0]
    assert db.execute(check).fetchone()[0] is False


def test_registry_served_count_stays_unchanged_during_candidate_build(db):
    count = db.execute("SELECT count_sql FROM asset_registry WHERE asset_id='ka_avadhi'").fetchone()[0].replace('$1', '%s')
    before = db.execute(count, (CHART, CHART)).fetchone()
    KaAvdhiWriter().run(ctx(db))
    assert db.execute(count, (CHART, CHART)).fetchone() == before


def test_one_f2_sql_read_for_hundreds_of_period_dossiers(db):
    db.execute('DELETE FROM chart_dashas WHERE level_n=2')
    db.execute('''INSERT INTO chart_dashas SELECT gen_random_uuid(),chart_id,build_id,ayanamsha_id,
        verification_pass_status,system_id,2,'Venus',dasha_row_id,
        start_iso + n * interval '1 day', start_iso + (n+1) * interval '1 day',
        (start_iso + n * interval '1 day')::date,(start_iso + (n+1)*interval '1 day')::date,
        true,false,false,'friend' FROM chart_dashas CROSS JOIN generate_series(0,199) n WHERE level_n=1''')
    class CountingConnection:
        def __init__(self): self.clock_reads = 0
        def execute(self, *args): return db.execute(*args)
        def cursor(self, **kwargs):
            owner = self
            class Cursor:
                def __enter__(self): self.cur=db.cursor(**kwargs); return self
                def __exit__(self, *args): self.cur.close()
                def execute(self, query, params):
                    if 'FROM chart_dashas' in query: owner.clock_reads += 1
                    return self.cur.execute(query, params)
                def fetchall(self): return self.cur.fetchall()
            return Cursor()
    counted = CountingConnection()
    result = KaAvdhiWriter().run(ctx(counted))
    assert (counted.clock_reads, result.rows_inserted) == (1, 201)
