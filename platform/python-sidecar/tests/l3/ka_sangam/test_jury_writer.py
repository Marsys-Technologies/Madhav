"""Explicit fixture dispatch and the complete class consumer contract."""
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID
import importlib

import pytest
from services.kala_core.assertion import AssertionEnvelope
from services.kala_core.measure import Interval
from services.ka_sangam.jury import Node, Use, declarations, admit, Opinion

CHART = '00000000-0000-0000-0000-000000000417'
GEN = 'candidate:k4-2aw:fixture'
T = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
H = Interval(T, T + 30)


def fixture_input(event_class='career', generation=GEN, chart=CHART):
    envelope = AssertionEnvelope.model_validate(dict(
        assertion_id='judge:fixture', chart_id=chart, generation=generation, stage='judge',
        method='fixture:judge', rule_version='fixture:1',
        subject=dict(event_class=event_class, affected_person='native', objects=[]),
        frame='fixture:frame', period_anchor=dict(system='vimshottari', MD='Jupiter',
            AD='Saturn', applicability='applicable'),
        interval=dict(t0=datetime.fromtimestamp(T, timezone.utc),
            t1=datetime.fromtimestamp(T + 30, timezone.utc)), grain='day',
        resolution=dict(computation='fixture', source_licensed='fixture', empirically_supported=None),
        role='selects', roots=dict(contact_ids=['selected:contact'], record_ids=[], fact_ids=[]),
        derivation_parents=['fixture:upstream'], used_for_selection=['selected:contact'],
        source=dict(text='planted fixture', locator='fixture:judge:1'), provenance='uncited_extension',
        operator_role='scored', null_reason=None, coverage_ref='fixture:coverage',
        precision=dict(method='fixture', delta_lambda=None, delta_t=None), input_vector_hash='a' * 64))
    groups = tuple(admit(g, ('fixture:' + g.group_id,), (H,), ('fixture:review',))
                   if g.group_id == 'G-P' else g for g in declarations(H))
    return dict(contract_version='k4-2aw:class_input:v1', acceptance_scope='fixture_only',
        anchor=envelope, upstream_refs={k: ('fixture:' + k,) for k in ('judge', 'negative_space', 'F1', 'F2')},
        nodes=(Node('p', frozenset({'judge:other'})),),
        uses=(Use('p', 'G-P', Interval(T, T + 10), 'corroborates'),), groups=groups,
        opinions=(Opinion(event_class, Interval(T, T + 10), 'supportive',
                          frozenset({'G-P'}), frozenset({'judge:other'})),),
        jaimini=None, alpha=.05, exchangeable=False, non_identity_shifts=31)


def api():
    return importlib.import_module('services.ka_sangam.jury.candidate')


def test_contract_round_trip_and_explicit_missing_method():
    value = api().ClassInput.model_validate(fixture_input())
    row = api().compute(value)
    assert api().ClassInput.model_validate(value.model_dump(mode='json')) == value
    assert row.agreement.groups[1].reason == 'jaimini_output_missing'
    assert row.agreement.pipeline_reason == 'whole_pipeline_selector_not_supplied'


@pytest.mark.parametrize('change', [
    {'contract_version': 'unknown'}, {'acceptance_scope': 'live'},
    {'upstream_refs': {'judge': ('fixture:judge',)}}, {'alpha': 0},
    {'exchangeable': 'false'}, {'non_identity_shifts': 0},
    {'corpus_admitted': 'yes'}, {'kp_ingested': 1},
])
def test_unknown_or_incomplete_contract_refused(change):
    with pytest.raises(ValueError):
        api().ClassInput.model_validate({**fixture_input(), **change})


def test_foreign_class_opinion_refused():
    value = fixture_input()
    value['opinions'] = (replace(value['opinions'][0], event_class='family'),)
    with pytest.raises(ValueError):
        api().ClassInput.model_validate(value)


def test_testimony_cannot_select_a_jury_window():
    value = fixture_input()
    value['anchor'] = value['anchor'].model_copy(update={'operator_role': 'testimony'})
    with pytest.raises(ValueError):
        api().ClassInput.model_validate(value)


def test_duplicate_class_inputs_collapse_and_conflicting_class_is_refused():
    value = fixture_input()
    assert len(api().class_inputs([value, value])) == 1
    changed = {**value, 'alpha': .1}
    with pytest.raises(ValueError):
        api().class_inputs([value, changed])
    with pytest.raises(ValueError):
        api().class_inputs([])


def test_plan_is_read_only_and_per_class(monkeypatch):
    writer = importlib.import_module('pipeline.orchestrator.writers.ka_sangam').KaSangamWriter()
    monkeypatch.setattr(api(), 'bind_candidate', lambda ctx, lock: GEN)
    ctx = SimpleNamespace(config={'chart_id': CHART, 'jury_fixture_inputs': [fixture_input(), fixture_input()]},
                          build_id=UUID(int=417), dry_run=False, db_conn=None)
    assert [s.key for s in writer.plan_substeps(ctx)] == ['class:career']


def test_legacy_dispatch_preserves_the_original_plan(monkeypatch):
    module = importlib.import_module('pipeline.orchestrator.writers.ka_sangam')
    sentinel = object()
    monkeypatch.setattr(module._LegacyKaSangamWriter, 'plan_substeps', lambda self, ctx: sentinel)
    assert module.KaSangamWriter().plan_substeps(SimpleNamespace(config={})) is sentinel


def test_dry_run_inserts_nothing(monkeypatch):
    module = importlib.import_module('pipeline.orchestrator.writers.ka_sangam')
    writer = module.KaSangamWriter()
    monkeypatch.setattr(api(), 'bind_candidate', lambda ctx, lock: GEN)
    ctx = SimpleNamespace(config={'chart_id': CHART, 'jury_fixture_inputs': [fixture_input()]},
                          build_id=UUID(int=417), dry_run=True, db_conn=None)
    steps = writer.plan_substeps(ctx)
    assert writer.run_substep(ctx, steps[0]).rows_inserted == 0
