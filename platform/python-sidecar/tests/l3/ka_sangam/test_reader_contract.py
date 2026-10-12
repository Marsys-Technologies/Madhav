"""D(W) has signed structural meaning, never a confidence/probability tier."""
from datetime import datetime, timezone
from importlib import import_module
from types import SimpleNamespace

import pytest


def api():
    return import_module('services.ka_sangam.jury.reader')


def stored(**change):
    return dict(chart_id='00000000-0000-0000-0000-000000000001', generation='candidate:test',
        assertion_id='jury:fixture', event_class='career',
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        conditional_effect=-.25, witness_signature=['G-P', 'G-T'],
        conditional_null={'estimand': 'jury_incremental_agreement', 'verdict': 'insufficient_evidence',
                          'reason': 'zero_null_variance', 'denominator': 32},
        pipeline_null=None, pipeline_null_reason='whole_pipeline_selector_not_supplied',
        null_reason='zero_null_variance', coverage={'coverage_ref': 'fixture:coverage'},
        provenance={'acceptance_scope': 'fixture_only', 'anchor': {'stage': 'judge'}}, **change)


@pytest.mark.parametrize('change', [
    {'conditional_effect': float('nan')}, {'conditional_effect': float('inf')},
    {'conditional_effect': True}, {'witness_signature': ['G-A']},
    {'witness_signature': ['G-T', 'G-T']}, {'generation': 'published:test'},
    {'provenance': {'acceptance_scope': 'live'}}, {'pipeline_null_reason': None},
    {'conditional_null': {'estimand': 'whole_pipeline_selection'}},
])
def test_invalid_stored_evidence_cannot_become_reader_evidence(change):
    row = stored()
    row.update(change)
    with pytest.raises(ValueError):
        api().JuryView.from_row(row)


def test_null_dw_preserves_qualification_and_missing_reason():
    row = stored()
    row['conditional_effect'] = None
    view = api().JuryView.from_row(row)
    assert (view.dw, view.null_reason, view.conditional_null['verdict']) == (
        None, 'zero_null_variance', 'insufficient_evidence')


def test_tulana_candidates_sort_by_signed_dw_without_legacy_weight_conversion(monkeypatch):
    ranker = import_module('services.ka_tulana.ranker').KaTulanaService()
    values = []
    for event_class, dw, signature in [('unknown', None, ['G-P', 'G-T', 'G-K']),
                                      ('negative', -.25, ['G-P', 'G-T']),
                                      ('zero', 0.0, ['G-T']),
                                      ('positive', .5, ['G-T'])]:
        row = stored()
        row.update(event_class=event_class, conditional_effect=dw, witness_signature=signature)
        values.append(api().JuryView.from_row(row))
    monkeypatch.setattr(ranker, 'read_jury', lambda ctx, generation: api().JuryRead('candidate', tuple(values)))
    result = ranker.rank_jury_candidates(SimpleNamespace(), generation='candidate:test')
    assert [(v.rank, v.window.event_class, v.window.dw) for v in result] == [
        (1, 'positive', .5), (2, 'zero', 0.0), (3, 'negative', -.25), (4, 'unknown', None)]


def test_tulana_candidate_ties_use_identity_and_no_witness_count_credit(monkeypatch):
    ranker = import_module('services.ka_tulana.ranker').KaTulanaService()
    a, b = stored(), stored()
    a.update(assertion_id='jury:a', witness_signature=['G-T'])
    b.update(assertion_id='jury:b', witness_signature=['G-P', 'G-T', 'G-K'])
    result = api().JuryRead('candidate', tuple(api().JuryView.from_row(r) for r in (b, a)))
    monkeypatch.setattr(ranker, 'read_jury', lambda ctx, generation: result)
    ranked = ranker.rank_jury_candidates(SimpleNamespace(), generation='candidate:test')
    assert [r.window.assertion_id for r in ranked] == ['jury:a', 'jury:b']


def test_tulana_candidate_ranking_refuses_implicit_legacy_source(monkeypatch):
    ranker = import_module('services.ka_tulana.ranker').KaTulanaService()
    monkeypatch.setattr(ranker, 'read_jury', lambda ctx, generation: api().JuryRead('legacy', ()))
    with pytest.raises(ValueError):
        ranker.rank_jury_candidates(SimpleNamespace(), generation=None)
