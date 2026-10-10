"""Real disposable PostgreSQL tests for additive F1 isolation and write dispatch."""
import importlib
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from tests.l3.kala_db.conftest import kala_db_dsn  # guarded disposable-server fixture
from services.ka_gochara_resonance.writer import KaGocharaResonanceWriter

CHART = '00000000-0000-4000-8000-000000000384'
BUILD = '00000000-0000-4000-8000-000000000385'
AYAN = 'lahiri_chitrapaksha'
MIGRATION = Path(__file__).resolve().parents[4] / 'migrations/1342_k2_2_f1_relationships.sql'


def api():
    name = 'services.ka_gochara_resonance.relationship_storage'
    assert importlib.util.find_spec(name), 'F1 storage is missing'
    return importlib.import_module(name)


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute('''CREATE TABLE kala_layer_head(chart_id uuid PRIMARY KEY, generation text);
          CREATE TABLE kala_layer_candidate(chart_id uuid, generation text, state text, build_id uuid,
            PRIMARY KEY(chart_id,generation));
          CREATE TABLE gochara_resonance_map(chart_id uuid, target_ref text, weight double precision);
          INSERT INTO gochara_resonance_map VALUES ('00000000-0000-4000-8000-000000000384','legacy',.8);''')
        conn.execute('INSERT INTO kala_layer_head VALUES (%s,%s)', (CHART, 'published:old'))
        conn.execute('INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,%s)', (CHART, 'candidate:new', 'building', BUILD))
        yield conn
        conn.rollback()


def migrate(conn):
    assert MIGRATION.exists(), 'K2-2 additive migration is missing'
    conn.execute(MIGRATION.read_text())


def projection():
    resolver = importlib.import_module('services.kala_core.promise.relationships')
    return resolver.resolve_relationships('marriage', facts=[dict(fact_id='venus', fact_subject='VEN',
        fact_category='graha_position', fact_key='longitude_sidereal', fact_value_num=0, unit='degrees')],
        sign_lords={}, signature={'karakas': ['Venus']})


def store(conn, generation='candidate:new'):
    return api().store_projection(conn, chart_id=CHART, ayanamsha_id=AYAN,
                                  generation=generation, build_id=BUILD, projections=[projection()])


def test_additive_migration_reapplies_and_has_no_weight_column(db):
    migrate(db)
    migrate(db)
    assert not db.execute("SELECT 1 FROM information_schema.columns WHERE table_name LIKE 'kala_f1_%' AND column_name='weight'").fetchall()


def test_repeat_build_is_same_rows_and_legacy_is_unchanged(db):
    migrate(db)
    store(db)
    before = db.execute('SELECT * FROM kala_f1_relationship ORDER BY edge_id').fetchall()
    store(db)
    assert (db.execute('SELECT * FROM kala_f1_relationship ORDER BY edge_id').fetchall(),
            db.execute('SELECT target_ref, weight FROM gochara_resonance_map').fetchall()) == (before, [('legacy', .8)])


@pytest.mark.parametrize('generation', ['legacy', 'published:old', 'candidate:'])
def test_legacy_or_non_candidate_generation_refused(db, generation):
    migrate(db)
    with pytest.raises(ValueError, match='candidate'):
        store(db, generation)


def test_current_head_candidate_refused(db):
    migrate(db)
    db.execute('UPDATE kala_layer_head SET generation=%s', ('candidate:new',))
    with pytest.raises(ValueError, match='published'):
        store(db)


@pytest.mark.parametrize('state', ['published', 'verified', 'complete', 'rejected'])
def test_retained_or_sealed_candidate_refused(db, state):
    migrate(db)
    db.execute('UPDATE kala_layer_candidate SET state=%s', (state,))
    with pytest.raises(ValueError, match='building'):
        store(db)


def test_candidate_build_binding_refused(db):
    migrate(db)
    db.execute('UPDATE kala_layer_candidate SET build_id=NULL')
    with pytest.raises(ValueError, match='build'):
        store(db)


def test_isolation_across_generations(db):
    migrate(db)
    store(db)
    db.execute('UPDATE kala_layer_candidate SET state=%s', ('published',))
    db.execute('INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,%s)', (CHART, 'candidate:next', 'building', BUILD))
    store(db, 'candidate:next')
    assert db.execute('SELECT generation, count(*) FROM kala_f1_relationship GROUP BY generation ORDER BY generation').fetchall() == [('candidate:new', 1), ('candidate:next', 1)]


def test_schema_cannot_mark_null_target_resolved(db):
    migrate(db)
    store(db)
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute('UPDATE kala_f1_relationship SET object_id=NULL')


def test_foreign_key_cannot_cross_generation(db):
    migrate(db)
    store(db)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute('UPDATE kala_f1_relationship SET generation=%s', ('candidate:other',))


def test_candidate_entrypoint_uses_real_sources_and_keeps_legacy(db):
    migrate(db)
    db.execute('''CREATE TABLE chart_facts(chart_id uuid, ayanamsha_id text, fact_id text,
      fact_category text, fact_subject text, fact_key text, fact_value_num numeric, fact_value_text text, unit text);
      CREATE TABLE reference_signs(sign_id int,lord text);
      CREATE TABLE brahma_event_ontology(event_class_id text,signature_model jsonb,citations jsonb);
      CREATE TABLE bg_transit_rules(id int,rule_type text,graha text,primary_house int,classical_citation text);
      CREATE TABLE ga_yoga_firings(chart_id uuid,ayanamsha_id text,yoga_canonical_id text,fired bool,
          constituent_fact_ids jsonb,constituent_planets jsonb,constituent_houses jsonb,bhanga_active bool);
      CREATE TABLE chart_dashas(chart_id uuid,ayanamsha_id text,system_id text,level_n int,lord_graha text);
      CREATE TABLE kala_activation_predicates(chart_id uuid,ayanamsha_id text,generation text,
          event_class_id text,mechanism_id text,derivation_ledger_jsonb jsonb);''')
    db.execute('INSERT INTO chart_facts VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,%s)',
               (CHART, AYAN, 'venus', 'graha_position', 'VEN', 'longitude_sidereal', 0, 'degrees'))
    db.execute('INSERT INTO brahma_event_ontology VALUES (%s,%s,%s)',
               ('marriage', '{"karakas":["Venus"]}', '["BPHS"]'))
    from services.ka_gochara_resonance.writer import TARGET_EVENT_CLASSES
    for c in TARGET_EVENT_CLASSES:
        if c != 'marriage':
            db.execute('INSERT INTO brahma_event_ontology VALUES (%s,%s,%s)', (c, '{}', '[]'))
    ctx = SimpleNamespace(db_conn=db, config={'chart_id': CHART, 'candidate_generation': 'candidate:new'},
                          build_id=BUILD, dry_run=False)
    result = KaGocharaResonanceWriter().run(ctx)
    assert (result.rows_inserted, db.execute('SELECT target_ref FROM gochara_resonance_map').fetchall(),
            db.execute('SELECT object_id,longitude_deg FROM kala_f1_target_object').fetchall()) == (12, [('legacy',)], [('graha:VEN', 0)])


def test_dry_run_does_not_need_connection():
    assert KaGocharaResonanceWriter().run(SimpleNamespace(dry_run=True, db_conn=None,
        config={'chart_id': CHART,'candidate_generation':'candidate:new'},build_id=BUILD)).rows_inserted == 0


def test_repeat_build_drops_stale_yoga_edges_without_touching_other_generation(db):
    migrate(db)
    resolver = importlib.import_module('services.kala_core.promise.relationships')
    source = [dict(fact_id='venus', fact_subject='VEN', fact_category='graha_position',
                  fact_key='longitude_sidereal', fact_value_num=0, unit='degrees')]
    live = resolver.resolve_relationships('marriage', facts=source, sign_lords={}, signature={},
        yogas=[dict(yoga_canonical_id='live', fired=True, constituent_fact_ids=['venus'], constituent_planets=['Venus'])])
    api().store_projection(db, chart_id=CHART, ayanamsha_id=AYAN, generation='candidate:new',
                          build_id=BUILD, projections=[live])
    gone = resolver.resolve_relationships('marriage', facts=source, sign_lords={}, signature={}, yogas=[])
    api().store_projection(db, chart_id=CHART, ayanamsha_id=AYAN, generation='candidate:new',
                          build_id=BUILD, projections=[gone])
    assert (db.execute('SELECT count(*) FROM kala_f1_relationship').fetchone()[0],
            db.execute('SELECT target_ref FROM gochara_resonance_map').fetchall()) == (0, [('legacy',)])


def test_no_declared_candidate_refused(db):
    migrate(db)
    with pytest.raises(ValueError, match='registered'):
        store(db, 'candidate:unknown')


def test_same_physical_object_two_roles_persist_as_two_edges(db):
    migrate(db)
    resolver = importlib.import_module('services.kala_core.promise.relationships')
    source = [dict(fact_id='venus', fact_subject='VEN', fact_category='graha_position',
                   fact_key='longitude_sidereal', fact_value_num=0, unit='degrees')]
    p = resolver.resolve_relationships('marriage', facts=source, sign_lords={},
                                       signature={'karakas': ['Venus']}, dasha_lords=['Venus'])
    api().store_projection(db, chart_id=CHART, ayanamsha_id=AYAN, generation='candidate:new',
                          build_id=BUILD, projections=[p])
    assert (db.execute('SELECT count(*) FROM kala_f1_target_object').fetchone()[0],
            db.execute('SELECT count(*) FROM kala_f1_relationship').fetchone()[0]) == (1, 2)


def test_store_has_no_independent_commit(db):
    migrate(db)
    store(db)
    db.rollback()
    assert db.execute("SELECT to_regclass('public.kala_f1_target_object')").fetchone()[0] is None
