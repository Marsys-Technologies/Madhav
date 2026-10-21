"""SR-K9-PUBLISHABLE D8 (round-2 rehearsal finding): the failed-run teardown must work on the PRODUCTION schema.

The schema here is built from the real migration files 1330 (candidate tables) and 1351 (issued_forecast, referenced by issued_forecast_outcome),
not a synthetic stand-in. Source of the rules: migration 1351 (delivered forecasts and their outcomes are append-only: BEFORE UPDATE/DELETE
triggers, FK ... ON DELETE RESTRICT) and the ruling SR-K9-PUBLISHABLE (never touch issued forecasts; refuse, never cascade).

  P1  a failed run's teardown on the production schema removes exactly the run's candidate rows (candidate, grains, verification) and restores
      exactly the stale/error rows the run wrote; another candidate's rows and an issued forecast on ANOTHER candidate are untouched
  P2  an issued forecast (with or without outcomes) that references the run's candidate makes the teardown REFUSE, naming issued_forecast and
      issued_forecast_outcome; nothing is deleted, restored or cascaded
"""
import uuid
from pathlib import Path

import psycopg
import pytest

from services.kala_core import rebuild_control
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, failed_run, stale_world, states, verdict  # noqa: F401  (stale_world, db are fixtures)
from tests.l3.kala_db.manifest.test_publication_ops import accept, db, prepare, snapshot  # noqa: F401
from tests.l3.kala_db.manifest.test_rebuild_control import CHART

ISSUED = Path(__file__).resolve().parents[5] / 'migrations/1351_issued_forecast_lifecycle.sql'


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


OLD_REFUSAL = ("        found[(schema, table, tuple(columns))] = {'schema': schema,",
               "        if referenced_by_others:\n            raise ValueError(f'{table} is itself referenced by another table')\n"
               "        found[(schema, table, tuple(columns))] = {'schema': schema,")
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
