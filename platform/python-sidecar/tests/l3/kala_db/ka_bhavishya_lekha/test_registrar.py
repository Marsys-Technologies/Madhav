"""K6-5: real SQL registrar oracles; fixtures do not establish live delivery."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb
import pytest

from pipeline.orchestrator.writers import ka_bhavishya_lekha as registrar
from services.kala_core.idempotency import ImmutableIssueConflict
from tests.l3.kala_db.conftest import kala_db_dsn  # noqa: F401

ROOT = Path(__file__).parents[5]
CHART = UUID('11111111-1111-4111-8111-111111111111')
BUILD = UUID('22222222-2222-4222-8222-222222222222')
ISSUE = UUID('33333333-3333-4333-8333-333333333333')
AT = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
STATEMENT = 'A career event in either disclosed interval.'
PINS = {
    'producer_ref': 'fixture:complete-jury:1', 'coverage_ref': 'fixture:coverage:1',
    'qualification_ref': 'fixture:qualification:1',
    'classes': {'career_change': {
        'result_policy': 'structural', 'calibration_status': 'uncalibrated',
        'ontology_locator': 'fixture:ontology:career:1', 'domain': 'career',
        'observation_predicate': 'No recorded career change in the covered intervals',
    }},
}


@pytest.fixture(scope='module')
def database(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        # Same columns as 1330, omitting its verifier-role privilege operation.
        ddl = (ROOT / 'migrations/1330_kala_layer_manifest_candidates.sql').read_text()
        conn.execute(ddl.split('-- A separately dispatched verifier')[0])
        conn.execute((ROOT / 'migrations/1351_issued_forecast_lifecycle.sql').read_text())
        conn.execute((ROOT / 'migrations/1352_issued_forecast_finite_intervals.sql').read_text())
    return kala_db_dsn


@pytest.fixture
def ctx(database):
    with psycopg.connect(database) as conn:
        conn.execute('INSERT INTO kala_layer_candidate '
                     '(chart_id,generation,build_id,state,model_digest,rule_registry_version,conventions) '
                     "VALUES (%s,'fixture:v1',%s,'complete','fixture:model:1','fixture:rules:1',%s)",
                     (CHART, BUILD, Jsonb({'fixture': True, 'registrar': PINS})))
        yield SimpleNamespace(db_conn=conn, build_id=str(BUILD),
                              config={'chart_id': str(CHART)}, dry_run=False)
        conn.rollback()


def request(ctx, **changes):
    # On base this is a failing behavioral oracle rather than an import error.
    assert hasattr(registrar, 'RegistrarInput'), 'K6-5 typed registrar is absent on base'
    intervals = ctx.db_conn.execute("SELECT '{[2027-01-01 00:00Z,2027-01-03 00:00Z),"
                                    "[2027-02-01 00:00Z,2027-02-03 00:00Z)}'::tstzmultirange").fetchone()[0]
    value = registrar.RegistrarInput(
        issue_id=ISSUE, version=1, generation='fixture:v1',
        event_class='career_change', phase='fruition', affected_person='native', episode='career:1',
        issued_at=AT, information_cutoff=AT, statement=STATEMENT, intervals=intervals,
        disclosed_grain='day', point_functional='none', probability_target=None,
        model_digest='fixture:model:1', producer_ref=PINS['producer_ref'], coverage_ref=PINS['coverage_ref'],
        qualification_ref=PINS['qualification_ref'], result_policy='structural', calibration_status='uncalibrated',
        delivery=registrar.DeliveryConfirmation(ISSUE, 1, STATEMENT, 'fixture:native-inbox', AT, True),
        ontology=registrar.ObservationPredicate('fixture:ontology:career:1', 'career_change', 'career',
                                              'No recorded career change in the covered intervals'),
    )
    return replace(value, **changes)


def run(ctx, value):
    ctx.config['registrar_fixture_inputs'] = (value,)
    return registrar.KaBhavishyaLekhaWriter().run(ctx)


def count(ctx):
    return ctx.db_conn.execute('SELECT count(*) FROM issued_forecast').fetchone()[0]


def test_unchanged_inputs_create_no_new_issue(ctx):
    value = request(ctx)
    run(ctx, value)
    run(ctx, value)
    assert count(ctx) == 1


def test_two_issues_keep_one_episode_outcome_cluster(ctx):
    value = request(ctx)
    run(ctx, value)
    run(ctx, replace(value, version=2, delivery=replace(value.delivery, version=2)))
    ctx.db_conn.execute('INSERT INTO issued_forecast_outcome '
                        '(outcome_id,issue_id,version,observed_at,recorded_at,observation) '
                        "SELECT gen_random_uuid(),issue_id,version,%s,%s,'{\"occurred\":true}' FROM issued_forecast",
                        (AT, AT))
    assert ctx.db_conn.execute('SELECT count(*),count(DISTINCT (chart_id,event_class,phase,affected_person,episode)) '
                              'FROM issued_forecast JOIN issued_forecast_outcome USING(issue_id,version)').fetchone() == (2, 1)


@pytest.mark.parametrize('confirmation', ['missing', 'unconfirmed', 'wrong_statement', 'wrong_issue', 'wrong_version', 'blank_channel'])
def test_candidate_never_issues_without_matching_confirmed_delivery(ctx, confirmation):
    value = request(ctx)
    mutations = {
        'missing': None, 'unconfirmed': replace(value.delivery, confirmed=False),
        'wrong_statement': replace(value.delivery, statement='Other statement'),
        'wrong_issue': replace(value.delivery, issue_id=BUILD),
        'wrong_version': replace(value.delivery, version=2),
        'blank_channel': replace(value.delivery, channel=' '),
    }
    run(ctx, replace(value, delivery=mutations[confirmation]))
    assert count(ctx) == 0


def test_uncalibrated_probability_cannot_be_issued(ctx):
    run(ctx, request(ctx, probability_target=0.7))
    assert count(ctx) == 0


def test_domain_and_falsifier_come_from_pinned_ontology_not_keywords(ctx):
    value = request(ctx, statement='marriage dhana wealth health guru')
    value = replace(value, delivery=replace(value.delivery, statement=value.statement))
    run(ctx, value)
    assert ctx.db_conn.execute("SELECT falsifier->>'domain',falsifier->>'observation_predicate' "
                              'FROM issued_forecast').fetchone() == (
                                  'career', 'No recorded career change in the covered intervals')


def test_changed_retry_cannot_rewrite_delivered_issue(ctx):
    value = request(ctx)
    run(ctx, value)
    with pytest.raises(ImmutableIssueConflict):
        run(ctx, replace(value, point_functional='midpoint'))
    assert ctx.db_conn.execute('SELECT point_functional FROM issued_forecast').fetchone() == ('none',)


@pytest.mark.parametrize('mutation', ['building', 'rejected', 'published', 'live', 'no_pins', 'wrong_build',
                                      'wrong_model', 'wrong_qualification', 'wrong_coverage', 'wrong_ontology',
                                      'missing_episode', 'empty_intervals', 'future_cutoff', 'future_delivery', 'naive_time'])
def test_incomplete_or_unbound_source_is_unavailable_before_issue_insert(ctx, mutation):
    value = request(ctx)
    if mutation in {'building', 'rejected', 'published'}:
        ctx.db_conn.execute('UPDATE kala_layer_candidate SET state=%s', (mutation,))
    elif mutation == 'live':
        ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s', (Jsonb({'fixture': False, 'registrar': PINS}),))
    elif mutation == 'no_pins':
        ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s', (Jsonb({'fixture': True}),))
    elif mutation == 'wrong_build':
        ctx.build_id = str(ISSUE)
    elif mutation == 'wrong_model':
        value = replace(value, model_digest='invented')
    elif mutation == 'wrong_qualification':
        value = replace(value, calibration_status='calibrated', probability_target=0.7)
    elif mutation == 'wrong_coverage':
        value = replace(value, coverage_ref='invented')
    elif mutation == 'wrong_ontology':
        value = replace(value, ontology=replace(value.ontology, predicate='invented'))
    elif mutation == 'missing_episode':
        value = replace(value, episode=' ')
    elif mutation == 'empty_intervals':
        value = replace(value, intervals=ctx.db_conn.execute("SELECT '{}'::tstzmultirange").fetchone()[0])
    elif mutation == 'future_cutoff':
        value = replace(value, information_cutoff=datetime(2027, 1, 1, tzinfo=timezone.utc))
    elif mutation == 'future_delivery':
        value = replace(value, delivery=replace(value.delivery, delivered_at=datetime(2027, 1, 1, tzinfo=timezone.utc)))
    else:
        value = replace(value, issued_at=AT.replace(tzinfo=None))
    result = run(ctx, value)
    assert (count(ctx), 'information_unavailable' in result.notes) == (0, True)


def test_completed_candidate_that_is_served_is_refused(ctx):
    ctx.db_conn.execute("INSERT INTO kala_layer_head VALUES (%s,'fixture:v1',%s)", (CHART, AT))
    run(ctx, request(ctx))
    assert count(ctx) == 0


def test_dry_run_and_outer_rollback_own_transaction(ctx, database):
    value = request(ctx)
    ctx.dry_run = True
    run(ctx, value)
    assert count(ctx) == 0
    ctx.dry_run = False
    run(ctx, value)
    ctx.db_conn.rollback()
    with psycopg.connect(database) as observer:
        assert observer.execute('SELECT count(*) FROM issued_forecast').fetchone() == (0,)


def test_disconnected_intervals_and_verbatim_statement_survive(ctx):
    value = request(ctx, statement='  Verbatim delivered text.\n')
    run(ctx, replace(value, delivery=replace(value.delivery, statement=value.statement)))
    assert ctx.db_conn.execute('SELECT delivered_statement,(SELECT count(*) FROM unnest(intervals)) '
                              'FROM issued_forecast').fetchone() == ('  Verbatim delivered text.\n', 2)


@pytest.mark.parametrize('probability', [0.7, None])
def test_calibrated_class_uses_explicit_probability_only(ctx, probability):
    pins = {**PINS, 'classes': {'career_change': {**PINS['classes']['career_change'],
            'calibration_status': 'calibrated', 'result_policy': 'calibrated_probability'}}}
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s',
                        (Jsonb({'fixture': True, 'registrar': pins}),))
    run(ctx, request(ctx, calibration_status='calibrated', result_policy='calibrated_probability',
                     probability_target=probability))
    assert ctx.db_conn.execute('SELECT probability_target::float8 FROM issued_forecast').fetchone() == (probability,)


@pytest.mark.parametrize('probability', [float('nan'), float('inf'), -0.1, 1.1, True])
def test_calibrated_status_does_not_license_invalid_probability(ctx, probability):
    pins = {**PINS, 'classes': {'career_change': {**PINS['classes']['career_change'],
            'calibration_status': 'calibrated', 'result_policy': 'calibrated_probability'}}}
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s',
                        (Jsonb({'fixture': True, 'registrar': pins}),))
    run(ctx, request(ctx, calibration_status='calibrated', result_policy='calibrated_probability',
                     probability_target=probability))
    assert count(ctx) == 0


def test_all_null_policy_refuses_probability_even_when_calibrated(ctx):
    pins = {**PINS, 'classes': {'career_change': {**PINS['classes']['career_change'],
            'calibration_status': 'calibrated', 'result_policy': 'all_null'}}}
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s',
                        (Jsonb({'fixture': True, 'registrar': pins}),))
    run(ctx, request(ctx, calibration_status='calibrated', result_policy='all_null', probability_target=0.7))
    assert count(ctx) == 0


def test_unavailable_bindings_do_not_reclassify_archived_issue(ctx):
    value = request(ctx)
    run(ctx, value)
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s', (Jsonb({'fixture': False}),))
    run(ctx, value)
    assert ctx.db_conn.execute('SELECT delivered_statement,calibration_status,probability_target '
                              'FROM issued_forecast').fetchone() == (STATEMENT, 'uncalibrated', None)


def test_real_dict_row_context_keeps_manifest_binding(ctx):
    value = request(ctx)
    ctx.db_conn.row_factory = psycopg.rows.dict_row
    run(ctx, value)
    run(ctx, value)
    assert ctx.db_conn.execute('SELECT delivered_statement FROM issued_forecast').fetchall() == [{'delivered_statement': STATEMENT}]


def test_non_boolean_delivery_version_is_required(ctx):
    value = request(ctx)
    run(ctx, replace(value, delivery=replace(value.delivery, version=True)))
    assert count(ctx) == 0
