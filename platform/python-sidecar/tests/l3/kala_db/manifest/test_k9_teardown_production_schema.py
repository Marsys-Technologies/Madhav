"""SR-K9-PUBLISHABLE D8 (round-2 rehearsal finding): the failed-run teardown must work on the PRODUCTION schema.

The schema here is built from the real migration files 1330 (candidate tables) and 1351 (issued_forecast, referenced by issued_forecast_outcome),
not a synthetic stand-in. Source of the rules: migration 1351 (delivered forecasts and their outcomes are append-only: BEFORE UPDATE/DELETE
triggers, FK ... ON DELETE RESTRICT) and the ruling SR-K9-PUBLISHABLE (never touch issued forecasts; refuse, never cascade).

  P1  a failed run's teardown on the production schema removes exactly the run's candidate rows (candidate, grains, verification) and restores
      exactly the stale/error rows the run wrote; another candidate's rows and an issued forecast on ANOTHER candidate are untouched
  P2  an issued forecast (with or without outcomes) that references the run's candidate makes the teardown REFUSE, naming issued_forecast and
      issued_forecast_outcome; nothing is deleted, restored or cascaded

Round 3 (K9_REHEARSAL_R3.md section 7, ruling SR-K9-PUBLISHABLE). The schema also carries migration 1383 (vedha candidate + interval tables, the
interval referencing the candidate: platform/migrations/1383:51-52) and kala_activation_predicates (supabase 243 + the 1339 columns; no foreign key
to kala_layer_candidate; ka_yojaka writes its rows under the run's generation, writers/ka_yojaka.py:571). Only chart_facts is a minimal stand-in
(the columns the 1383 guard reads).

  R1  D8  the run's OWN vedha candidate + interval rows (a referenced dependent scoped to the same (chart_id, generation)) go with the run;
          another generation's vedha rows stay (1383:51-52; vedha storage.py:114-116 writes them under the run's candidate)
  R2  D8  real issued history still refuses even when the run also holds vedha rows, and nothing is deleted (1351: outcomes reference
          issued_forecast by issue_id, not by generation)
  R3  D8  a database guard that refuses the deletion (1383's building-candidate guard) is a named refusal of the teardown, not a raw driver error
  R4  N1  the run's kala_activation_predicates rows are removed
  R5  N1  ...and only those of the run's generation and chart (never 'legacy', another generation, or another chart's same-named generation)
  R6  N1  the census / readback counts the predicates (the dry run shows what the teardown will remove)
  R7  N1  a candidate whose generation is 'legacy' is refused (the predicates' default partition is never a teardown target; 1339)
  R8  N3  an asset a LATER run changed after the failed run is not restored (a later stale write of the same state included)
  R9  N3  ...and is reported as left alone, with who changed it
  R10 N3  the restore UPDATE refuses an asset whose latest audit row moved after the selection
"""
import json
import uuid
from pathlib import Path

import psycopg
import pytest

from services.kala_core import rebuild_control
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, failed_run, stale_world, states, verdict  # noqa: F401  (stale_world, db are fixtures)
from tests.l3.kala_db.manifest.test_publication_ops import accept, db, prepare, snapshot  # noqa: F401
from tests.l3.kala_db.manifest.test_rebuild_control import CHART, make_run

MIGRATIONS = Path(__file__).resolve().parents[5] / 'migrations'
ISSUED = MIGRATIONS / '1351_issued_forecast_lifecycle.sql'
VEDHA = MIGRATIONS / '1383_ka_3a_vedha_candidate_intervals.sql'
PREDICATES_BASE = MIGRATIONS.parent / 'supabase/migrations/243_l3_ka_yojaka.sql'
PREDICATES_GENERATION = MIGRATIONS / '1339_k2_1b_promise_graph_columns.sql'
NATAL, OTHER_CHART = '00000000-0000-0000-0000-0000000000a2', '00000000-0000-0000-0000-0000000000b1'
AYANAMSHA = 'lahiri_chitrapaksha'


@pytest.fixture
def prod_world(stale_world):
    stale_world.execute(ISSUED.read_text().replace('public.', ''))
    stale_world.commit()
    return stale_world


def issue(conn, generation, *, outcome=False, chart=CHART):
    issue_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO issued_forecast (issue_id, version, chart_id, generation, event_class, phase, affected_person, episode, issued_at,
               information_cutoff, delivered_at, delivery_channel, delivered_statement, result_policy, calibration_status, intervals,
               disclosed_grain, point_functional, falsifier)
           VALUES (%s, 1, %s, %s, 'e', 'p', 'native', 'ep', now(), now(), now(), 'fixture', 'statement', 'all_null', 'uncalibrated',
               tstzmultirange(tstzrange(now(), now() + interval '1 day')), 'grain', 'point',
               '{"ontology_locator": "x", "observation_predicate": "y"}'::jsonb)""", (issue_id, chart, generation))
    if outcome:
        conn.execute("INSERT INTO issued_forecast_outcome VALUES (%s, %s, 1, now(), now(), '{\"seen\": true}'::jsonb)", (str(uuid.uuid4()), issue_id))
    conn.commit()
    return issue_id


def held(conn):
    return {t: conn.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ('issued_forecast', 'issued_forecast_outcome')}


def of_generation(conn, generation):
    return conn.execute("SELECT (SELECT count(*) FROM kala_layer_candidate WHERE generation = %(g)s), "
                        "(SELECT count(*) FROM kala_layer_candidate_grain WHERE generation = %(g)s), "
                        "(SELECT count(*) FROM kala_layer_verification WHERE generation = %(g)s), "
                        "(SELECT count(*) FROM ka_dep_candidate WHERE generation = %(g)s)", {'g': generation}).fetchone()


def p1(module, conn):
    assert conn.execute("SELECT to_regclass('issued_forecast_outcome')").fetchone()[0] is not None, 'premise: the production schema (1351) is in place'
    keep = prepare(conn, 'keep', chart=CHART)                       # another candidate of the chart, with an issued forecast and an outcome on it
    accept(conn, keep)
    issue(conn, 'keep', outcome=True)
    c = failed_run(conn)                                            # generation 'g': candidate, 2 grains, 2 ka_dep rows, stale/error marks from the real writers
    accept(conn, c)
    conn.commit()
    assert states(conn)['ka_sangam'] == 'error' and states(conn)['ka_kshetra'] == 'stale', 'premise: the run left stale/error rows'
    issued, kept = held(conn), of_generation(conn, 'keep')
    try:
        result = module.teardown(conn, run_id=c.build_id)
    except ValueError as exc:                       # the reversion: the teardown refuses on the production schema (the rehearsal's observed failure)
        raise AssertionError(f'the teardown refused on the production schema: {exc}')
    assert result['status'] == 'TORN_DOWN' and result['generation'] == 'g'
    assert result['deleted'] == {'kala_layer_candidate': 1, 'kala_layer_candidate_grain': 2, 'kala_layer_verification': 1, 'ka_dep_candidate': 2,
                                 'issued_forecast': 0}
    assert of_generation(conn, 'g') == (0, 0, 0, 0)
    assert of_generation(conn, 'keep') == kept                       # another candidate is untouched
    assert held(conn) == issued                                      # issued history untouched
    after = states(conn)
    assert (after['ka_kshetra'], after['mi_bhara'], after['ka_sangam']) == ('lit', 'service_ok', 'lit')
    assert sorted(r['asset_id'] for r in result['asset_states_restored']) == ['ka_kshetra', 'ka_sangam', 'mi_bhara']


def p2(module, conn, with_outcome):
    c = failed_run(conn)
    issue(conn, 'g', outcome=with_outcome)
    before = snapshot(conn), states(conn), held(conn), of_generation(conn, 'g')
    try:
        with pytest.raises(ValueError) as refused:
            module.teardown(conn, run_id=c.build_id)
    except psycopg.Error as exc:                    # the reversion: the database's own RESTRICT/append-only guard refuses later, and unnamed
        conn.rollback()
        raise AssertionError(f'refused by the database, not by the teardown: {exc}')
    reason = str(refused.value)
    assert 'issued_forecast' in reason and 'issued_forecast_outcome' in reason and '1 row' in reason
    conn.rollback()
    assert (snapshot(conn), states(conn), held(conn), of_generation(conn, 'g')) == before      # nothing deleted, restored or cascaded


def p2_without_outcome(module, conn):
    p2(module, conn, False)


def p2_with_outcome(module, conn):
    p2(module, conn, True)


OLD_REFUSAL = ("        found[(schema, table, tuple(columns))] = {'schema': schema, 'table': table, 'columns': list(columns),\n",
               "        if foreign:\n            raise ValueError(f'{table} is itself referenced by another table')\n"
               "        found[(schema, table, tuple(columns))] = {'schema': schema, 'table': table, 'columns': list(columns),\n")
NO_REFUSAL = ("    if held:      # delivered history", "    if False:      # delivered history")


@BOTH
def test_p1_a_failed_runs_teardown_works_on_the_production_schema(prod_world, tmp_path, reverted):
    # reversion: the pre-fix rule, any candidate dependent that is itself referenced (issued_forecast) refuses every teardown
    verdict(reverted, p1, rebuild_control, tmp_path, *OLD_REFUSAL, prod_world)


@BOTH
def test_p2_an_issued_forecast_on_the_candidate_refuses_the_teardown_naming_it(prod_world, tmp_path, reverted):
    # reversion: the held-rows refusal is dropped, so the teardown would go on to the database's RESTRICT guard
    verdict(reverted, p2_with_outcome, rebuild_control, tmp_path, *NO_REFUSAL, prod_world)


def test_p2_a_forecast_without_outcomes_refuses_too(prod_world):
    p2_without_outcome(rebuild_control, prod_world)


# ---------------------------------------------------------------- round 3: D8 (vedha), N1 (predicates), N3 (later run)


@pytest.fixture
def r3_world(prod_world):
    """prod_world + migration 1383 + kala_activation_predicates (243 + the generation columns of 1339, the file's own text up to its detector block)."""
    prod_world.execute('CREATE TABLE kala_vedha_gochara (id uuid PRIMARY KEY, chart_id uuid, detail jsonb, window_start date)')
    prod_world.execute('CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, build_id uuid, ayanamsha_id text, fact_category text, '
                       'fact_subject text, fact_key text)')
    prod_world.execute('INSERT INTO build_runs (id, chart_id) VALUES (%s, %s)', (NATAL, CHART))
    prod_world.execute("INSERT INTO chart_facts VALUES ('moon-ref', %s, %s, %s, 'graha_position', 'MOON', 'longitude_sidereal')", (CHART, NATAL, AYANAMSHA))
    prod_world.execute(VEDHA.read_text().replace('public.', ''))
    prod_world.execute(PREDICATES_BASE.read_text())
    prod_world.execute(PREDICATES_GENERATION.read_text().split('-- Version the registered detector')[0].replace('public.', ''))
    prod_world.commit()
    return prod_world


def vedha(conn, generation, intervals=2):
    """What the vedha writer stores under a candidate (storage.py:114-116): one header and its intervals, through 1383's own guard triggers."""
    conn.execute("UPDATE kala_layer_candidate SET conventions = conventions || %s::jsonb WHERE chart_id = %s AND generation = %s",
                 (json.dumps({'natal': {'build_id': NATAL, 'ayanamsha_id': AYANAMSHA}}), CHART, generation))
    conn.execute("INSERT INTO kala_vedha_gochara_candidate (chart_id, generation, ayanamsha_id, vedha_kind, janma_reference_fact_id, formula_version, "
                 "natal_build_id, coverage, upstream_fingerprint, payload, method_qualification) VALUES (%s, %s, %s, 'house_vedha', 'moon-ref', 'v1', %s, "
                 "%s::jsonb, %s::jsonb, '{\"schema\": \"ka_vedha_payload/1\"}'::jsonb, 'qualified')",
                 (CHART, generation, AYANAMSHA, NATAL,
                  json.dumps({'search_state': 'searched', 'requested': 1, 'source_interval': 1, 'covered': 1, 'complete': True, 'backend': 'x',
                              'convention_id': 'c', 'gaps': []}),
                  json.dumps({'schema': 'ka_vedha_inputs/1', 'digest': 'a' * 64})))
    for day in range(intervals):
        conn.execute("INSERT INTO kala_vedha_gochara_interval VALUES (%s, %s, %s, 'house_vedha', 'Sun', 'active', 'cite', 'verse_cited', "
                     "%s::timestamptz, %s::timestamptz, '{}', '{Mars}', '{}', %s::jsonb, NULL, NULL)",
                     (CHART, generation, AYANAMSHA, f'2025-01-{1 + 2 * day:02d}T00:00Z', f'2025-01-{2 + 2 * day:02d}T00:00Z',
                      json.dumps({'primary_house': 1, 'vedha_house': 9})))
    conn.commit()


def vedha_counts(conn, generation):
    return conn.execute("SELECT (SELECT count(*) FROM kala_vedha_gochara_candidate WHERE generation = %(g)s), "
                        "(SELECT count(*) FROM kala_vedha_gochara_interval WHERE generation = %(g)s)", {'g': generation}).fetchone()


def predicates(conn, generation, n, *, chart=CHART):
    for _ in range(n):
        conn.execute("INSERT INTO kala_activation_predicates (chart_id, signal_id, signature_class, generation) VALUES (%s, %s, 'YOGA', %s)",
                     (chart, str(uuid.uuid4()), generation))
    conn.commit()


def predicate_counts(conn):
    return dict(conn.execute("SELECT chart_id::text || '/' || generation, count(*) FROM kala_activation_predicates GROUP BY 1").fetchall())


def refused_by(module, conn, run_id, *, said):
    """The teardown's own ValueError (never a driver error), whose text carries ``said``."""
    try:
        module.teardown(conn, run_id=run_id)
    except ValueError as exc:
        assert said in str(exc), f'refused, but not as expected: {exc}'
        conn.rollback()
        return str(exc)
    except psycopg.Error as exc:                   # the reversion: the database refuses, unnamed
        conn.rollback()
        raise AssertionError(f'refused by the database, not by the teardown: {exc}')
    raise AssertionError('the teardown went through')


def torn_down(module, conn, run_id):
    try:
        return module.teardown(conn, run_id=run_id)
    except ValueError as exc:                      # the reversion: refuses
        raise AssertionError(f'the teardown refused: {exc}')


def r1(module, conn):
    c = failed_run(conn)
    keep = prepare(conn, 'keep', chart=CHART)
    vedha(conn, 'g')
    vedha(conn, 'keep', intervals=3)
    assert vedha_counts(conn, 'g') == (1, 2) and vedha_counts(conn, 'keep') == (1, 3), 'premise: the vedha writer left its rows under both candidates'
    result = torn_down(module, conn, c.build_id)
    assert result['deleted']['kala_vedha_gochara_candidate'] == 1 and result['deleted']['kala_vedha_gochara_interval'] == 2
    assert vedha_counts(conn, 'g') == (0, 0)
    assert vedha_counts(conn, 'keep') == (1, 3)                      # another generation's vedha rows are untouched
    assert conn.execute('SELECT count(*) FROM kala_layer_candidate WHERE generation IN (%s, %s)', ('g', keep.generation)).fetchone() == (1,)


def r2(module, conn):
    c = failed_run(conn)
    vedha(conn, 'g')
    issue(conn, 'g', outcome=True)
    before = snapshot(conn), states(conn), held(conn), of_generation(conn, 'g'), vedha_counts(conn, 'g')
    reason = refused_by(module, conn, c.build_id, said='issued_forecast')
    assert 'issued_forecast_outcome' in reason and 'kala_vedha_gochara' not in reason
    assert (snapshot(conn), states(conn), held(conn), of_generation(conn, 'g'), vedha_counts(conn, 'g')) == before      # the run's vedha rows included


def r3(module, conn):
    c = failed_run(conn)
    vedha(conn, 'g')
    conn.execute("UPDATE kala_layer_candidate SET state = 'complete' WHERE generation = 'g'")      # 1383's guard allows only a building candidate
    conn.commit()
    before = snapshot(conn), states(conn), vedha_counts(conn, 'g')
    refused_by(module, conn, c.build_id, said='kala_vedha_gochara_interval')
    assert (snapshot(conn), states(conn), vedha_counts(conn, 'g')) == before


def r4(module, conn):
    c = failed_run(conn)
    predicates(conn, 'g', 3)
    result = torn_down(module, conn, c.build_id)
    assert result['deleted'].get('kala_activation_predicates') == 3
    assert predicate_counts(conn) == {}


def r5(module, conn):
    c = failed_run(conn)
    prepare(conn, 'keep', chart=CHART)
    predicates(conn, 'g', 3)
    predicates(conn, 'legacy', 2)
    predicates(conn, 'keep', 2)
    predicates(conn, 'g', 2, chart=OTHER_CHART)
    torn_down(module, conn, c.build_id)
    assert predicate_counts(conn) == {f'{CHART}/legacy': 2, f'{CHART}/keep': 2, f'{OTHER_CHART}/g': 2}


def r6(module, conn):
    c = failed_run(conn)
    predicates(conn, 'g', 3)
    assert module.census(conn, c.build_id).get('kala_activation_predicates') == 3
    torn_down(module, conn, c.build_id)
    assert module.row_counts(conn, CHART, 'g').get('kala_activation_predicates') == 0


def r7(module, conn):
    c = make_run(conn, 'failed', generation='legacy')
    predicates(conn, 'legacy', 2)
    refused_by(module, conn, c.build_id, said='legacy')
    assert predicate_counts(conn) == {f'{CHART}/legacy': 2}


def later_run(conn, writes):
    """What a LATER run does to the asset states: orchestrator-GUC writes, then the audit rows placed after the failed run's window ended."""
    first = conn.execute('SELECT coalesce(max(id), 0) FROM asset_throughput_state_audit').fetchone()[0]
    conn.execute("SET marsys.triggered_by = 'asset_runner'")
    for asset, state in writes:
        conn.execute('UPDATE asset_throughput SET state = %s WHERE chart_id = %s AND asset_id = %s', (state, CHART, asset))
    conn.execute("RESET marsys.triggered_by")
    conn.execute("UPDATE asset_throughput_state_audit SET changed_at = changed_at + interval '3 hours' WHERE id > %s", (first,))    # past ended_at + 1 hour
    conn.commit()


LATER = [('ka_kshetra', 'lit'), ('ka_kshetra', 'stale'), ('ka_sangam', 'lit')]      # kshetra rebuilt, then staled again by the later run; sangam repaired


def r8(module, conn):
    c = failed_run(conn)
    assert states(conn)['ka_kshetra'] == 'stale' and states(conn)['mi_bhara'] == 'stale', 'premise: the failed run staled them'
    later_run(conn, LATER)
    result = torn_down(module, conn, c.build_id)
    after = states(conn)
    assert after['ka_kshetra'] == 'stale'                             # the later run's own stale mark: not undone
    assert after['ka_sangam'] == 'lit'
    assert after['mi_bhara'] == 'service_ok'                          # untouched since the failed run: restored
    assert [r['asset_id'] for r in result['asset_states_restored']] == ['mi_bhara']


def r9(module, conn):
    c = failed_run(conn)
    later_run(conn, LATER)
    result = torn_down(module, conn, c.build_id)
    left = {r['asset_id']: r for r in result['asset_states_left_alone']}
    assert sorted(left) == ['ka_edited_after', 'ka_kshetra', 'ka_sangam']      # ka_edited_after: the fixture's hand edit after the run (no orchestrator GUC)
    assert left['ka_edited_after']['changed_since_by'] is None and left['ka_edited_after']['changed_since_to'] == 'error'
    assert left['ka_kshetra']['changed_since_by'] == 'asset_runner' and left['ka_kshetra']['state_now'] == 'stale'
    assert left['ka_sangam']['changed_since_to'] == 'lit' and left['ka_sangam']['run_wrote'] == 'error'


def r10(module, conn):
    c = failed_run(conn)
    found, _left = module.failed_run_asset_states(conn, c.build_id)
    assert 'ka_kshetra' in [f[0] for f in found], 'premise: selected before the later run'
    later_run(conn, [('ka_kshetra', 'lit'), ('ka_kshetra', 'stale')])        # same state again, so only the audit trail tells it changed
    try:
        module.restore_asset_states(conn, found, CHART)
    except ValueError as exc:
        assert 'ka_kshetra' in str(exc)
        conn.rollback()
        return
    raise AssertionError('restored an asset a later run changed')


OWN_AS_ISSUED = ("if child_oid in seen or not set(key) <= set(referenced):", "if True:")
ALL_OWNED = ("if child_oid in seen or not set(key) <= set(referenced):", "if child_oid in seen:")
NO_DB_REFUSAL_NAMED = ("    except psycopg.Error as exc:\n        raise ValueError(f\"{table['table']} refused the deletion of this candidate's rows: {exc}\")\n",
                       "    except KeyError:\n        raise\n")
NO_PREDICATE_DELETE = ("    for table in unlinked_tables(conn):        # no foreign key", "    for table in []:        # no foreign key")
PREDICATES_BY_CHART = ("sql.SQL('DELETE FROM {} WHERE chart_id = %s AND generation = %s')", "sql.SQL('DELETE FROM {} WHERE chart_id = %s AND (generation = %s OR true)')")
NO_PREDICATE_COUNT = ("    for table in unlinked_tables(conn):\n        counts[table] =", "    for table in []:\n        counts[table] =")
NO_LEGACY_GUARD = ("if generation == 'legacy':", "if False:")
NOT_RESTORED_BY_AUDIT = ("if later_id is None and state == last_new]", "if state == last_new]")
NOT_REPORTED = ("    return restorable, left\n", "    return restorable, []\n")
NO_UPDATE_AUDIT_GUARD = ("f\"AND NOT EXISTS (SELECT 1 FROM {AUDIT_TABLE} l WHERE l.chart_id = t.chart_id AND l.asset_id = t.asset_id AND l.id > %s)\",",
                         "\"AND %s IS NOT NULL\",")


@BOTH
def test_r1_the_runs_own_vedha_rows_are_torn_down_with_it(r3_world, tmp_path, reverted):
    # reversion: every referenced dependent is issued history again (the round-3 rehearsal's refusal of every real K9 failed run)
    verdict(reverted, r1, rebuild_control, tmp_path, *OWN_AS_ISSUED, r3_world)


@BOTH
def test_r2_issued_history_still_refuses_beside_the_runs_vedha_rows(r3_world, tmp_path, reverted):
    # reversion: a referrer keyed by something other than the generation counts as the run's own output, so the teardown reaches for the forecast
    verdict(reverted, r2, rebuild_control, tmp_path, *ALL_OWNED, r3_world)


@BOTH
def test_r3_a_database_guard_refusal_is_a_named_refusal_of_the_teardown(r3_world, tmp_path, reverted):
    # reversion: the driver error escapes unnamed
    verdict(reverted, r3, rebuild_control, tmp_path, *NO_DB_REFUSAL_NAMED, r3_world)


@BOTH
def test_r4_the_runs_predicates_are_removed(r3_world, tmp_path, reverted):
    # reversion: the unlinked tables are not visited
    verdict(reverted, r4, rebuild_control, tmp_path, *NO_PREDICATE_DELETE, r3_world)


@BOTH
def test_r5_only_the_runs_generation_and_chart_of_predicates_are_removed(r3_world, tmp_path, reverted):
    # reversion: the delete is scoped to the chart alone
    verdict(reverted, r5, rebuild_control, tmp_path, *PREDICATES_BY_CHART, r3_world)


@BOTH
def test_r6_the_census_counts_the_predicates(r3_world, tmp_path, reverted):
    # reversion: row_counts ignores the unlinked tables
    verdict(reverted, r6, rebuild_control, tmp_path, *NO_PREDICATE_COUNT, r3_world)


@BOTH
def test_r7_a_legacy_generation_is_never_a_teardown_target(r3_world, tmp_path, reverted):
    # reversion: the guard is dropped
    verdict(reverted, r7, rebuild_control, tmp_path, *NO_LEGACY_GUARD, r3_world)


@BOTH
def test_r8_an_asset_a_later_run_changed_is_not_restored(r3_world, tmp_path, reverted):
    # reversion: the selection checks the current state against the run's last write only (the pre-fix rule)
    verdict(reverted, r8, rebuild_control, tmp_path, *NOT_RESTORED_BY_AUDIT, r3_world)


@BOTH
def test_r9_the_assets_left_alone_are_reported_with_who_changed_them(r3_world, tmp_path, reverted):
    # reversion: nothing is reported
    verdict(reverted, r9, rebuild_control, tmp_path, *NOT_REPORTED, r3_world)


@BOTH
def test_r10_the_restore_update_refuses_an_asset_whose_latest_audit_row_moved(r3_world, tmp_path, reverted):
    # reversion: the UPDATE checks the current state only
    verdict(reverted, r10, rebuild_control, tmp_path, *NO_UPDATE_AUDIT_GUARD, r3_world)
