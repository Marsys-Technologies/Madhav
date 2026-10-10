"""K4-3: reading claims are links, never independent evidence or extra events."""
from importlib import import_module
from uuid import UUID

import pytest

from tests.l3.ka_sangam.test_jury_writer import api, fixture_input, CHART


def core():
    return import_module('services.kala_core.assertion.attachment')


def event(**change):
    return dict(event_class='career', phase='onset', affected_person='native',
                episode='F1:episode:career:1', **change)


def claim(signal='MSR:signal:1', **change):
    value = dict(signal_id=signal, kind='observable_event', event=event(),
                 observable_event_ref='F1:predicate:career:1', objects=('employer:1',))
    return {**value, **change}


def forecast(**change):
    value = dict(chart_id=CHART, event=event(), assertion_ids=('jury:1',),
                 observable_event_ref='F1:predicate:career:1', objects=('employer:1',))
    return core().CanonicalForecast.model_validate({**value, **change})


def report(claims, forecasts=None):
    return core().attach_reading_claims((forecast(),) if forecasts is None else forecasts,
                                      tuple(core().ReadingClaim.model_validate(c) for c in claims))


def test_claim_attached_twice_credits_once():
    result = report([claim()] * 20)
    assert result.forecasts[0].reading_attachments == ('MSR:signal:1',)


def test_multiple_signals_share_one_event_evaluation_unit():
    result = report([claim('MSR:2'), claim('MSR:1')])
    assert result.evaluation_clusters[0].forecast_ids == (result.forecasts[0].forecast.forecast_id,)


def test_unattached_claim_is_reported_not_dropped():
    result = report([claim(event={**event(), 'episode': 'F1:episode:missing'})])
    assert [(v.claim.signal_id, v.reason) for v in result.unattached] == [
        ('MSR:signal:1', 'canonical_forecast_unavailable')]


@pytest.mark.parametrize('kind', ['trait', 'condition', 'lifetime_tendency', 'subjective_rasa'])
def test_nonobservable_reading_is_retained_without_forecast_registration(kind):
    result = report([claim(kind=kind)])
    assert result.unattached[0].reason == 'nonobservable_reading'


@pytest.mark.parametrize('change,reason', [
    ({'event': None}, 'event_mapping_unavailable'),
    ({'observable_event_ref': None}, 'observable_predicate_unavailable'),
    ({'observable_event_ref': 'F1:other'}, 'observable_predicate_mismatch'),
    ({'objects': ('other:object',)}, 'event_objects_mismatch'),
])
def test_incomplete_or_incompatible_mapping_has_a_named_reason(change, reason):
    assert report([claim(**change)]).unattached[0].reason == reason


def test_conflicting_duplicate_signal_is_refused():
    with pytest.raises(ValueError, match='conflicting reading signal'):
        report([claim(), claim(event={**event(), 'phase': 'end'})])


def test_duplicate_forecasts_union_assertions_without_an_extra_event():
    result = report([claim()], (forecast(), forecast(assertion_ids=('jury:2',)), forecast()))
    assert result.forecasts[0].forecast.assertion_ids == ('jury:1', 'jury:2')
    assert len(result.forecasts) == 1


def test_conflicting_forecast_definition_is_refused():
    with pytest.raises(ValueError, match='conflicting canonical forecast'):
        report([], (forecast(), forecast(observable_event_ref='F1:other')))


@pytest.mark.parametrize('axis', ['event_class', 'phase', 'affected_person', 'episode'])
def test_all_four_event_identity_axes_are_required_for_attachment(axis):
    assert report([claim(event={**event(), axis: 'other'})]).forecasts[0].reading_attachments == ()


def test_shared_episode_clusters_distinct_phases_once_each():
    result = report([], (forecast(), forecast(event={**event(), 'phase': 'end'})))
    assert len(result.evaluation_clusters) == 1
    assert len(result.evaluation_clusters[0].forecast_ids) == 2


def test_chart_identity_separates_evaluation_clusters_and_refuses_ambiguous_claims():
    with pytest.raises(ValueError, match='one chart'):
        report([claim()], (forecast(), forecast(chart_id=UUID(int=999))))


def attachment_input():
    return {**fixture_input(), 'event_identity': event(),
            'observable_event_ref': 'F1:predicate:career:1',
            'reading_claims': [claim(objects=()), claim(objects=())]}


def test_integrated_claims_attach_to_the_computed_jury_assertion():
    result = api().compute(api().ClassInput.model_validate(attachment_input()))
    assert result.attachments.forecasts[0].forecast.assertion_ids == (result.assertion_id,)


def test_reading_attachment_does_not_change_evidence_or_agreement():
    plain = api().compute(api().ClassInput.model_validate(fixture_input()))
    attached = api().compute(api().ClassInput.model_validate(attachment_input()))
    assert attached.agreement == plain.agreement


def test_missing_canonical_identity_retains_claim_with_honest_null():
    value = {**fixture_input(), 'reading_claims': [claim()]}
    result = api().compute(api().ClassInput.model_validate(value))
    assert result.attachments.unattached[0].reason == 'canonical_forecast_unavailable'
    assert result.attachments.null_reason == 'canonical_event_identity_unavailable'


@pytest.mark.parametrize('change', [
    {'event_identity': {**event(), 'event_class': 'family'}},
    {'event_identity': {**event(), 'affected_person': 'someone_else'}},
    {'observable_event_ref': None},
])
def test_forecast_identity_must_match_the_jury_subject(change):
    with pytest.raises(ValueError):
        api().ClassInput.model_validate({**attachment_input(), **change})


def test_attachment_order_and_repeated_claims_leave_candidate_stable():
    value = attachment_input()
    before = api().compute(api().ClassInput.model_validate(value))
    value['reading_claims'] = list(reversed(value['reading_claims'])) * 20
    assert api().compute(api().ClassInput.model_validate(value)) == before


def _mutate(monkeypatch, old, new):
    import ast
    from pathlib import Path
    module = core()
    source = Path(module.__file__).read_text()
    replacements = zip(old, new) if isinstance(old, tuple) else ((old, new),)
    for before, after in replacements:
        assert source.count(before) == 1
        source = source.replace(before, after)
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'attach_reading_claims')
    scope = dict(module.__dict__)
    exec(compile(ast.Module(body=[function], type_ignores=[]), module.__file__, 'exec'), scope)
    monkeypatch.setattr(module, 'attach_reading_claims', scope['attach_reading_claims'])


def test_duplicate_credit_mutation_fails_the_event_oracle(monkeypatch):
    _mutate(monkeypatch, "'assertion_ids': tuple(sorted(ids))",
            "'assertion_ids': tuple(sorted(forecast.assertion_ids + (previous.assertion_ids if previous else ())))")
    with pytest.raises(AssertionError):
        test_duplicate_forecasts_union_assertions_without_an_extra_event()


def test_duplicate_claim_mutation_fails_the_attachment_oracle(monkeypatch):
    _mutate(monkeypatch, (
        'attached = {key: set() for key in canonical}',
        'for signal_id, claim in sorted(unique_claims.items()):',
        'attached[_event_key(claim.event)].add(signal_id)',
    ), (
        'attached = {key: [] for key in canonical}',
        'for claim in claims:\n        signal_id = claim.signal_id',
        'attached[_event_key(claim.event)].append(signal_id)',
    ))
    with pytest.raises(AssertionError):
        test_claim_attached_twice_credits_once()


def test_dropped_unattached_claim_mutation_fails_the_reporting_oracle(monkeypatch):
    _mutate(monkeypatch, 'unattached.append(UnattachedClaim(claim=claim, reason=reason))', 'pass')
    with pytest.raises(AssertionError):
        test_unattached_claim_is_reported_not_dropped()


def test_persisted_report_contains_canonical_identity_and_nulls():
    value = api().compute(api().ClassInput.model_validate(attachment_input()))
    stored = value.attachments.model_dump(mode='json')
    assert stored['forecasts'][0]['forecast']['forecast_id'].startswith('forecast:')
    assert stored['forecasts'][0]['reading_attachments'] == ['MSR:signal:1']
    assert stored['acceptance_scope'] == 'candidate_preparation'


def test_attachment_report_typed_round_trip_preserves_derived_ids():
    result = report([claim(), claim('MSR:missing', event=None)])
    assert core().AttachmentReport.model_validate(result.model_dump(mode='json')) == result


@pytest.mark.parametrize('field', ['forecast_id', 'shared_episode_id'])
def test_forged_canonical_identity_is_refused_on_readback(field):
    stored = forecast().model_dump(mode='json')
    stored[field] = 'forecast:forged'
    with pytest.raises(ValueError):
        core().CanonicalForecast.model_validate(stored)


def test_missing_event_with_stored_identifier_is_a_validation_error():
    stored = forecast().model_dump(mode='json')
    del stored['event']
    with pytest.raises(ValueError):
        core().CanonicalForecast.model_validate(stored)


def test_certification_mapping_keeps_unmeasured_gates_honest():
    import ast
    import json
    from pathlib import Path
    mapping = json.loads((Path(api().__file__).parent / 'certification_mapping.json').read_text())
    assert mapping['asset'] == 'ka_sangam'
    assert mapping['registry_revision'] == 26
    assert mapping['density_tier_columns'] is None
    assert mapping['production_certification'] is None
    assert mapping['gates']['Dens']['expected_reading'] == 'No producer-stored tier; no Dens PASS claimed'
    tree = ast.parse((Path(__file__).parents[4] / 'scripts/governance/asset_census.py').read_text())
    registry = next(n.value for n in tree.body if isinstance(n, ast.AnnAssign)
                    and isinstance(n.target, ast.Name) and n.target.id == 'CRITERION_REGISTRY')
    revisions = {key.value: next(k.value.value for k in value.keywords if k.arg == 'revision')
                 for key, value in zip(registry.keys, registry.values)}
    for gate in mapping['gates'].values():
        for criterion, revision in gate['revisions'].items():
            assert revision == revisions[criterion]
