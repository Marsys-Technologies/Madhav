from copy import deepcopy
import ast
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from services.ka_sangam.plan_identity import plan_fingerprint


def _sangam_dispatch_source(clock):
    """Use the real method body with inert connection/windowing seams."""
    source = Path(__file__).resolve().parents[1] / 'pipeline/orchestrator/writers/ka_sangam.py'
    tree = ast.parse(source.read_text())
    legacy, = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == '_LegacyKaSangamWriter']
    methods = [node for node in legacy.body if isinstance(node, ast.FunctionDef)]
    dispatch, = [node for node in methods if node.name == 'run_substep']
    near, = [node for node in methods if node.name == '_substep_near']
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), dispatch], type_ignores=[])
    namespace = {'date': clock, 'convergence_generation': lambda *_: 'fixture-generation'}
    exec(compile(ast.fix_missing_locations(module), str(source), 'exec'), namespace)
    return namespace['run_substep'], near


def test_near_dispatch_preserves_the_three_argument_hook():
    from types import MethodType

    day = date(2026, 11, 11)
    clock = SimpleNamespace(today=lambda: day)
    dispatch, near = _sangam_dispatch_source(clock)
    calls = []
    result = object()
    writer = SimpleNamespace(_chart_id='fixture-chart', _candidate=object(), _reset_pending=False, _planned_near_date=day)

    def hook(self, conn, chart_id, dry_run):
        calls.append((conn, chart_id, dry_run))
        return result

    writer._substep_near = MethodType(hook, writer)
    connection = object()
    assert dispatch(writer, SimpleNamespace(db_conn=connection, dry_run=True), SimpleNamespace(key='near')) is result
    assert calls == [(connection, 'fixture-chart', True)]
    assert not near.args.kwonlyargs and len(near.args.args) == 4


def test_near_dispatch_refuses_midnight_drift_before_the_hook_or_reset():
    dispatch, _ = _sangam_dispatch_source(SimpleNamespace(today=lambda: date(2026, 11, 12)))
    calls = []
    writer = SimpleNamespace(_chart_id='fixture-chart', _candidate=object(), _reset_pending=True,
                             _planned_near_date=date(2026, 11, 11), _substep_near=lambda *_: calls.append('hook'))
    connection = SimpleNamespace(cursor=lambda: calls.append('reset'))
    with pytest.raises(RuntimeError, match='near horizon date changed since planning; replan required'):
        dispatch(writer, SimpleNamespace(db_conn=connection, dry_run=False), SimpleNamespace(key='near'))
    assert calls == []


def test_near_horizon_reuses_the_plan_day_and_unplanned_direct_calls_use_the_clock():
    day = date(2026, 11, 11)
    calls = []
    clock = SimpleNamespace(today=lambda: calls.append('clock') or date(2026, 11, 12))
    _, near = _sangam_dispatch_source(clock)
    assignment, = [node for node in near.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'today' for target in node.targets)]
    expression = compile(ast.Expression(assignment.value), '<actual-near-day-expression>', 'eval')
    assert eval(expression, {'date': clock}, {'self': SimpleNamespace(_planned_near_date=day)}) == day
    assert calls == []
    assert eval(expression, {'date': clock}, {'self': SimpleNamespace()}) == date(2026, 11, 12)
    assert calls == ['clock']


FIRST = {
    'signal_id': UUID('aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa'),
    'signature_class': 'DIGNITY',
    'ayanamsha_id': 'lahiri_chitrapaksha',
    'dignity_score': 0.8,
    'graha_name': 'Jupiter',
    'primary_domain': 'fixture',
    'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.8, 'constituent_lords': ['Jupiter', 'Moon']},
    'transit_trigger_jsonb': {'target_longitude_deg': 90.0, 'aspect_degrees': [0, 90]},
}
SECOND = {**FIRST, 'signal_id': 'bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb', 'dignity_score': 0.7}


def fingerprint(**overrides):
    inputs = dict(
        version=4, chart_id='fixture-chart', generation='candidate:fixture', run_id='fixture-run',
        today=date(2026, 11, 11), birth_year=1980, near=[FIRST, SECOND], lifetime=[FIRST, SECOND],
        near_mode_d=0, lifetime_mode_d=0, gochara_available=True, muhurta_available=True,
        native_context=SimpleNamespace(janma_nakshatra_idx=2, moon_sign='Aries',
                                       location={'lat': 1.0, 'lon': 2.0, 'tz_offset_minutes': 0}),
        enrichment_context=SimpleNamespace(
            ashtakavarga_bindu={'SARVA': {1: 29, 2: 30}},
            vedha_rules=[{'graha': 'Jupiter', 'window_start': date(2026, 11, 12),
                          'window_end': date(2026, 11, 13)}],
            tajika_year_lords=[{'varshesha': 'Jupiter', 'varsha_start': date(2026, 11, 1),
                                'varsha_end': date(2027, 11, 1)}],
            school_consensus_by_domain={},
        ),
    )
    inputs.update(overrides)
    return plan_fingerprint(**inputs)


@pytest.mark.parametrize('change', [
    {'version': 5}, {'chart_id': 'other-chart'}, {'generation': 'candidate:other'},
    {'run_id': 'other-run'}, {'today': date(2026, 11, 12)}, {'birth_year': None},
    {'near': [SECOND, FIRST]}, {'lifetime': [SECOND, FIRST]},
    {'near_mode_d': 1}, {'lifetime_mode_d': None},
    {'gochara_available': False}, {'muhurta_available': False},
    {'native_context': SimpleNamespace(janma_nakshatra_idx=2, moon_sign='Taurus',
                                       location={'lat': 1.0, 'lon': 2.0, 'tz_offset_minutes': 0})},
])
def test_identity_changes_with_execution_scope_order_carrier_and_context(change):
    assert fingerprint(**change) != fingerprint()


@pytest.mark.parametrize('field,replacement', [
    ('signal_id', None), ('signature_class', 'YOGA'), ('ayanamsha_id', 'different-frame'),
    ('dignity_score', 0.9), ('graha_name', 'Moon'), ('dispositor_lord', 'Mars'),
    ('domain_lord', 'Venus'), ('primary_domain', 'different-domain'),
    ('dasha_eligibility_rule_jsonb', {'eligibility_score': 0.7, 'constituent_lords': ['Jupiter', 'Moon']}),
    ('transit_trigger_jsonb', {'target_longitude_deg': 91.0, 'aspect_degrees': [0, 90]}),
])
def test_same_order_semantic_edits_invalidate_lifetime_identity(field, replacement):
    changed = {**FIRST, field: replacement}
    assert fingerprint(lifetime=[changed, SECOND]) != fingerprint()


def test_canonical_mapping_keys_and_physical_row_changes_preserve_identity():
    equivalent = {
        **FIRST, 'id': 8, 'content_hash': 'replaced-ranking-metadata',
        'strength_affliction_hook_jsonb': {'unused': True}, 'signal_id': str(FIRST['signal_id']),
        'dasha_eligibility_rule_jsonb': {'constituent_lords': ['Jupiter', 'Moon'], 'eligibility_score': 0.8},
    }
    assert fingerprint(near=[equivalent, SECOND], lifetime=[equivalent, SECOND]) == fingerprint()
    changed = deepcopy(equivalent)
    changed['dasha_eligibility_rule_jsonb']['constituent_lords'].reverse()
    assert fingerprint(lifetime=[changed, SECOND]) != fingerprint()


def test_empty_and_signal_unresolved_plans_remain_distinct():
    blank = {**FIRST, 'signal_id': None}
    empty = fingerprint(near=[], lifetime=[], near_mode_d=None, lifetime_mode_d=None)
    assert fingerprint(near=[blank], lifetime=[blank], near_mode_d=None, lifetime_mode_d=None) != empty
    assert len(empty) == 64


def test_loaded_enrichment_changes_identity():
    changed = SimpleNamespace(
        ashtakavarga_bindu={'SARVA': {1: 31, 2: 30}},
        vedha_rules=[{'graha': 'Jupiter', 'window_start': date(2026, 11, 12),
                      'window_end': date(2026, 11, 13)}],
        tajika_year_lords=[{'varshesha': 'Jupiter', 'varsha_start': date(2026, 11, 1),
                            'varsha_end': date(2027, 11, 1)}],
        school_consensus_by_domain={},
    )
    assert fingerprint(enrichment_context=changed) != fingerprint()


@pytest.mark.parametrize('change', [
    {'near': [{**FIRST, 'dignity_score': float('nan')}]},
    {'near': [{**FIRST, 'transit_trigger_jsonb': []}]},
    {'near': [{**FIRST, 'dasha_eligibility_rule_jsonb': {'fixture': {1: True}}}]},
    {'near': [{**FIRST, 'signal_id': object()}]},
    {'native_context': SimpleNamespace(janma_nakshatra_idx=2, moon_sign='Aries',
                                       location={'lat': float('inf'), 'lon': 2.0, 'tz_offset_minutes': 0})},
    {'near_mode_d': -1},
    {'lifetime_mode_d': 2},
    {'today': 'fixture-private-input'},
])
def test_malformed_identity_raises_a_generic_error(change):
    with pytest.raises(ValueError, match='^ka_sangam: malformed resume identity$'):
        fingerprint(**change)
