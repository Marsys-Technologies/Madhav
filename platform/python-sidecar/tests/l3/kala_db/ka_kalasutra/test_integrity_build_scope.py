"""Real SQL: the build under verification cannot be replaced by a newer build."""
import psycopg
import pytest
from pipeline.orchestrator.asset_runner import _probe_asset
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_read_model_integrity import bind_integrity_target

from tests.l3.kala_db.ka_kalasutra.test_read_models import (
    ASSETS, BUILD, CHART, GEN, MODELS, PLATFORM, WRITERS, ctx, db, payloads,
)

OTHER_CHART = '00000000-0000-0000-0000-000000000701'
OTHER_BUILD = '00000000-0000-0000-0000-000000000702'
OTHER_GEN = 'candidate:integrity-other'


def check_sql(db, asset):
    return db.execute('SELECT integrity_check_sql FROM asset_registry WHERE asset_id=%s',
                      (asset,)).fetchone()[0]


def newer_build(db, chart=OTHER_CHART, fixture=True):
    db.execute("INSERT INTO build_runs VALUES (%s,%s,'completed','2001-01-01')",
               (OTHER_BUILD, chart))
    if fixture:
        db.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,'complete','{\"fixture\":true}')",
                   (chart, OTHER_GEN, OTHER_BUILD))


@pytest.mark.parametrize('asset', ASSETS)
@pytest.mark.parametrize('chart,fixture', [(OTHER_CHART, True), (CHART, True), (CHART, False)])
def test_newer_build_cannot_mask_corrupted_candidate(db, asset, chart, fixture):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    table = MODELS[asset][0]
    db.execute(f"UPDATE {table} SET payload=jsonb_set(payload,'{{acceptance_scope}}','\"admitted\"') "
               'WHERE chart_id=%s AND generation=%s', (CHART, GEN))
    sql = check_sql(db, asset)
    assert db.execute(sql).fetchone()[0] is False
    newer_build(db, chart, fixture)
    assert db.execute(f"SELECT count(*) FROM {table} WHERE chart_id=%s AND generation=%s "
                      "AND payload->>'acceptance_scope'='admitted'", (CHART, GEN)).fetchone()[0] > 0
    assert db.execute(sql).fetchone()[0] is False


@pytest.mark.parametrize('asset', ASSETS)
def test_healthy_candidate_ignores_corruption_in_newer_unrelated_build(db, asset):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    newer_build(db)
    table = MODELS[asset][0]
    db.execute(f'''INSERT INTO {table} SELECT %s,%s,model_key,row_kind,interval_start,interval_end,
        as_of,jsonb_set(payload,'{{acceptance_scope}}','"admitted"'),upstream_refs,tier
        FROM {table} WHERE chart_id=%s AND generation=%s''', (OTHER_CHART, OTHER_GEN, CHART, GEN))
    assert db.execute(check_sql(db, asset)).fetchone()[0] is True


@pytest.mark.parametrize('asset', ASSETS)
@pytest.mark.parametrize('chart,build', [('', ''), (CHART, ''), ('', BUILD), (OTHER_CHART, BUILD),
                                       (CHART, OTHER_BUILD)])
def test_integrity_without_matching_chart_and_build_fails_closed(db, asset, chart, build):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    db.execute("SELECT set_config('kala.integrity_chart_id',%s,true), "
               "set_config('kala.integrity_build_id',%s,true)", (chart, build))
    assert db.execute(check_sql(db, asset)).fetchone()[0] is False


@pytest.mark.parametrize('asset', ASSETS)
def test_verification_remains_bound_to_completed_build(db, asset):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    db.execute("UPDATE build_runs SET state='completed'")
    db.execute("UPDATE kala_layer_candidate SET state='complete'")
    newer_build(db)
    assert db.execute(check_sql(db, asset)).fetchone()[0] is True
    count = db.execute('SELECT count_sql FROM asset_registry WHERE asset_id=%s', (asset,)).fetchone()[0]
    assert db.execute(count.replace('$1', '%s'), (CHART, CHART)).fetchone()[0] == len(payloads(db, asset))


@pytest.mark.parametrize('asset', ASSETS)
def test_actual_orchestrator_probe_rejects_masked_corruption(db, asset):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    sql = check_sql(db, asset)
    with db.cursor() as cur:
        assert _probe_asset(db, cur, asset, {'integrity_check_sql': sql}, False)[0] is True
        table = MODELS[asset][0]
        db.execute(f"UPDATE {table} SET upstream_refs=upstream_refs-'judge' WHERE chart_id=%s", (CHART,))
        newer_build(db)
        assert _probe_asset(db, cur, asset, {'integrity_check_sql': sql}, False)[0] is False


@pytest.mark.parametrize('asset', ASSETS)
def test_writer_pins_are_local_to_the_writer_transaction(db, asset):
    assert db.execute(check_sql(db, asset)).fetchone()[0] is False
    with pytest.raises(RuntimeError, match='rollback savepoint'):
        with db.transaction():
            WRITERS[ASSETS.index(asset)]().run(ctx(db))
            assert db.execute(check_sql(db, asset)).fetchone()[0] is True
            raise RuntimeError('rollback savepoint')
    assert db.execute(check_sql(db, asset)).fetchone()[0] is False


@pytest.mark.parametrize('asset', ASSETS)
def test_legacy_writer_binds_its_build_and_preserves_legacy_detector(db, asset, monkeypatch):
    # This oracle qualifies output integrity binding; its empty input tables
    # are projections, not a settled daśā population.
    import importlib
    from tests.l3._dasha_projection import emulated_projection
    monkeypatch.setattr(importlib.import_module('pipeline.orchestrator.writers.ka_jivana_parva'),
                        'execute_governed_dasha_query', emulated_projection)
    # Empty real upstream relations take each default writer's no-input path.
    db.execute('''CREATE TABLE kala_activation_predicates(chart_id uuid,signal_id uuid,
        ayanamsha_id text,signature_class text,dasha_eligibility_rule_jsonb jsonb,
        transit_trigger_jsonb jsonb,strength_affliction_hook_jsonb jsonb,generation text,
        mechanism_route text,conclusion_state_jsonb jsonb);
        CREATE TABLE kala_convergence(chart_id uuid,convergence_id uuid,signal_id uuid,mode text,
        peak_date date,window_start date,window_end date,convergence_score numeric,
        confidence_label text,orb_strength numeric,rarity_years numeric);
        CREATE TABLE chart_dashas(chart_id uuid,lord_graha text,start_date date,end_date date,
        level_n int,system_id text,ayanamsha_id text);
        ALTER TABLE kala_darshana ADD COLUMN generation text;''')
    newer_build(db, CHART, False)
    legacy_table = {'ka_kalasutra': 'kala_activation', 'ka_kala_darshana': 'kala_darshana',
                    'ka_jivana_parva': 'kala_jivana_parva'}[asset]
    # Plant a real legacy corruption predicate in the preserved ELSE branch.
    sql = check_sql(db, asset).replace('SELECT true',
        f"SELECT NOT EXISTS (SELECT 1 FROM {legacy_table} WHERE payload ? 'broken')")
    db.execute('UPDATE asset_registry SET integrity_check_sql=%s WHERE asset_id=%s', (sql, asset))
    context = ContextSpec(asset_id=asset, build_id=OTHER_BUILD, db_conn=db,
                          config={'chart_id': CHART})
    assert WRITERS[ASSETS.index(asset)]().run(context).rows_inserted == 0
    assert db.execute(sql).fetchone()[0] is True
    db.execute(f"INSERT INTO {legacy_table}(chart_id,payload) VALUES (%s,'{{\"broken\":true}}')", (CHART,))
    assert db.execute(sql).fetchone()[0] is False


def test_repeated_binding_migration_does_not_fire_registry_update_triggers(db):
    db.execute('''CREATE TABLE registry_updates(asset_id text);
        CREATE FUNCTION record_registry_update() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN INSERT INTO registry_updates VALUES (NEW.asset_id); RETURN NEW; END $$;
        CREATE TRIGGER record_registry_update AFTER UPDATE ON asset_registry
        FOR EACH ROW EXECUTE FUNCTION record_registry_update();''')
    before = db.execute('SELECT * FROM asset_registry ORDER BY asset_id').fetchall()
    db.execute((PLATFORM/'migrations/1375_k6_integrity_chart_build_binding.sql').read_text())
    assert db.execute('SELECT * FROM asset_registry ORDER BY asset_id').fetchall() == before
    assert db.execute('SELECT * FROM registry_updates').fetchall() == []


@pytest.mark.parametrize('drift', ['missing_registration', 'unknown_detector'])
def test_binding_migration_refuses_unreviewed_registry_state(db, drift):
    if drift == 'missing_registration':
        db.execute("DELETE FROM asset_registry WHERE asset_id='ka_kala_darshana'")
    else:
        db.execute("UPDATE asset_registry SET integrity_check_sql='SELECT true' "
                   "WHERE asset_id='ka_kala_darshana'")
    before = db.execute('SELECT * FROM asset_registry ORDER BY asset_id').fetchall()
    with pytest.raises(psycopg.errors.RaiseException, match='1375: (missing K6|unexpected K6)'):
        with db.transaction():
            db.execute((PLATFORM/'migrations/1375_k6_integrity_chart_build_binding.sql').read_text())
    assert db.execute('SELECT * FROM asset_registry ORDER BY asset_id').fetchall() == before


@pytest.mark.parametrize('finish', ['commit', 'rollback'])
def test_integrity_binding_does_not_leak_past_transaction(kala_db_dsn, finish):
    with psycopg.connect(kala_db_dsn) as conn:
        context = ContextSpec(asset_id='ka_kalasutra', build_id=BUILD, db_conn=conn,
                              config={'chart_id': CHART})
        bind_integrity_target(context)
        assert conn.execute("SELECT current_setting('kala.integrity_chart_id'), "
                            "current_setting('kala.integrity_build_id')").fetchone() == (CHART, BUILD)
        getattr(conn, finish)()
        assert conn.execute("SELECT NULLIF(current_setting('kala.integrity_chart_id',true),''), "
                            "NULLIF(current_setting('kala.integrity_build_id',true),'')").fetchone() == (None, None)
