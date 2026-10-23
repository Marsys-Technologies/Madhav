"""SR-K9B-TRIAGE: a ka_sangam predicate whose target longitude is NULL is a NAMED blank, never a float and never a default.

Claims (CLAUDE.md §N.7.6 honest null; §N.8 each measured by a detector that can read false; B.10 no invented chart value):
C1 a predicate with `target_longitude_deg: null` (what ka_yojaka writes for `null_reason: target_unresolved`, ka_yojaka.py:149-150) reaches
   `_generate_windows` without raising, and Mode A/B are never run against an invented longitude;
C2 a predicate whose key is ABSENT gets the same treatment (the old `.get(key, 0.0)` invented 0 deg for it);
C3 a resolved predicate still scans against exactly its own longitude, beside a blank one;
C4 the substep result names the blank and counts it (`target_unresolved=<n>`; the orchestrator does not persist WriterResult.notes, so the run log carries the count too);
C5 Mode D (sign-level, reads no target) still runs for the first predicate of the call when that predicate is blank: a blank target costs only its own Mode A/B windows.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers import ka_sangam as ks

RESOLVED_LON = 123.5


def _pred(signal_id, trigger):
    return {'signal_id': signal_id, 'signature_class': 'YOGA', 'primary_domain': 'career', 'transit_trigger_jsonb': trigger}


NULL_TARGET = {'target_identity': None, 'target_longitude_deg': None, 'null_reason': 'target_unresolved'}
ABSENT_TARGET = {'null_reason': 'target_unresolved'}
GOOD_TARGET = {'target_identity': 'Sun', 'target_longitude_deg': RESOLVED_LON}


@pytest.fixture
def engine(monkeypatch):
    """Replace the four engines with recorders; the only thing under test is what `_generate_windows` hands them."""
    calls = {'a': [], 'b': [], 'd': [], 'trigger': []}
    monkeypatch.setattr(ks, 'mode_a_search', lambda **kw: calls['a'].append(kw['predicate']['signal_id']) or [])
    monkeypatch.setattr(ks, 'mode_b_sweep', lambda **kw: calls['b'].append(kw['signal_id']) or [])
    monkeypatch.setattr(ks, 'mode_d_av_bindhu', lambda **kw: calls['d'].append(kw['predicate']['signal_id']) or [])
    monkeypatch.setattr(ks, 'apply_trigger_suppression',
                        lambda windows, **kw: calls['trigger'].append(kw['target_lon']) or windows)
    return calls


def _generate(preds):
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    native = SimpleNamespace(janma_nakshatra_idx=24, moon_sign='Aquarius', location={'lat': 20.3, 'lon': 85.8})
    windows = writer._generate_windows(
        pred_dicts=preds, horizon_start=date(2026, 1, 1), horizon_end=date(2027, 1, 1), dasha_kala_service=None,
        gochara_service=None, chart_id='c', native_ctx=native, enrichment_context=None)
    return writer, windows


def test_c1_null_target_is_a_named_blank_not_a_crash(engine):
    writer, windows = _generate([_pred('sig-null', NULL_TARGET)])
    assert windows == []
    assert engine['a'] == [] and engine['b'] == [] and engine['trigger'] == []        # nothing scanned against an invented longitude
    assert [(b['signal_id'], b['reason']) for b in writer._target_blanks] == [('sig-null', 'target_unresolved')]


def test_c2_absent_target_key_is_blank_not_zero_degrees(engine):
    writer, _ = _generate([_pred('sig-absent', ABSENT_TARGET)])
    assert engine['trigger'] == [] and engine['a'] == []        # the old default scanned at 0.0 deg
    assert [b['signal_id'] for b in writer._target_blanks] == ['sig-absent']


def test_c3_resolved_predicate_scans_its_own_longitude_beside_a_blank(engine):
    writer, _ = _generate([_pred('sig-good', GOOD_TARGET), _pred('sig-null', NULL_TARGET)])
    assert engine['a'] == ['sig-good'] and engine['b'] == ['sig-good']
    assert engine['trigger'] == [RESOLVED_LON, RESOLVED_LON]        # Mode A and Mode B suppression, the exact longitude, nothing else
    assert engine['d'] == ['sig-good']                              # Mode D still attaches to the first predicate
    assert [b['signal_id'] for b in writer._target_blanks] == ['sig-null']


def test_c4_substep_result_counts_the_blank_for_the_k9_receipt(engine):
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    writer._conv_generation = 'candidate:test'
    writer._lt_preds = []
    writer._pred_dicts = [_pred('sig-null', NULL_TARGET), _pred('sig-null-2', NULL_TARGET), _pred('sig-good', GOOD_TARGET)]
    writer._dks = writer._gs = writer._enrichment_ctx = writer._muhurta = None
    writer._native_ctx = SimpleNamespace(janma_nakshatra_idx=24, moon_sign='Aquarius', location={'lat': 20.3, 'lon': 85.8})
    result = writer._substep_near(MagicMock(), 'c', dry_run=True)
    assert 'target_unresolved=2' in result.notes
    assert engine['a'] == ['sig-good']


def test_c4_no_blank_leaves_notes_empty(engine):
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    writer._conv_generation = 'candidate:test'
    writer._lt_preds = []
    writer._pred_dicts = [_pred('sig-good', GOOD_TARGET)]
    writer._dks = writer._gs = writer._enrichment_ctx = writer._muhurta = None
    writer._native_ctx = SimpleNamespace(janma_nakshatra_idx=24, moon_sign='Aquarius', location={'lat': 20.3, 'lon': 85.8})
    assert writer._substep_near(MagicMock(), 'c', dry_run=True).notes == ''


def test_c5_mode_d_still_runs_when_the_first_predicate_is_blank(engine):
    _, _ = _generate([_pred('sig-null', NULL_TARGET), _pred('sig-good', GOOD_TARGET)])
    assert engine['d'] == ['sig-null']        # the pre-change behaviour of Mode D (first predicate of the call) is untouched by a blank target
    assert engine['a'] == ['sig-good'] and engine['b'] == ['sig-good']


def test_c6_substep_notes_read_blanks_before_any_generate_call(engine, monkeypatch):
    """review-3901 NB-4: `_target_blanks` was only set inside `_generate_windows`; a substep whose generator is stubbed (or a writer
    that has not generated yet) reads it first. It must read as 'no blanks' (honest empty note), never raise AttributeError (§N.7.6)."""
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    writer._conv_generation = 'candidate:test'
    writer._lt_preds = []
    writer._pred_dicts = []
    writer._dks = writer._gs = writer._enrichment_ctx = writer._muhurta = writer._native_ctx = None
    monkeypatch.setattr(writer, '_generate_windows', lambda **kw: [])
    assert writer._substep_near(MagicMock(), 'c', dry_run=True).notes == ''
