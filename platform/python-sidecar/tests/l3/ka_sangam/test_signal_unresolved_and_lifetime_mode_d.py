"""SR-K9-TRIAGE-DUP: ka_sangam must not write a window it cannot attribute, and must not write Mode D once per lifetime predicate.

Evidence (K9 round B2 re-measure, counts only): a full rebuild wrote 994 Mode D rows (38 near, 956 lifetime = 478 x 2) and then failed its own
integrity contract on conjunct (a) (478 duplicate natural-key groups) and conjunct (g) (994 of 994 rows). The two predicates ka_sangam received had
signal_id NULL: ka_yojaka's F1 graph writes an honest NULL for an admitted row whose signal is shared, several or absent
(services/ka_yojaka/promise_adapter.py bind_signal_ids; pinned by tests/l3/kala_db/test_k2_1b_source_writer.py).

Claims (CLAUDE.md §N.7.6 honest null, B.10 no invented value, §N.8 each signal measured; integrity contract 670 (a)/(g)):
C1 a predicate with no signal_id yields no window in ANY mode (Mode D included, whose score would read the invented 0.5 dignity default) and is a
   named, counted blank `signal_unresolved`;
C2 Mode D rides the first predicate that HAS a signal, not the first predicate;
C3 the lifetime tier (one call per predicate) computes the predicate-agnostic Mode D set on exactly ONE substep (the A3 once-per-call guard,
   074d69ee8, held for none of them there).
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers import ka_sangam as ks

GOOD_TARGET = {'target_identity': 'Sun', 'target_longitude_deg': 123.5}
NULL_TARGET = {'target_identity': None, 'target_longitude_deg': None, 'null_reason': 'target_unresolved'}
NATIVE = SimpleNamespace(janma_nakshatra_idx=24, moon_sign='Aquarius', location={'lat': 20.3, 'lon': 85.8})


def _pred(signal_id, trigger=GOOD_TARGET, signature_class='YOGA'):
    return {'signal_id': signal_id, 'signature_class': signature_class, 'primary_domain': 'career', 'transit_trigger_jsonb': trigger}


@pytest.fixture
def engine(monkeypatch):
    calls = {'a': [], 'b': [], 'c': [], 'd': []}
    monkeypatch.setattr(ks, 'mode_a_search', lambda **kw: calls['a'].append(kw['predicate']['signal_id']) or [])
    monkeypatch.setattr(ks, 'mode_b_sweep', lambda **kw: calls['b'].append(kw['signal_id']) or [])
    monkeypatch.setattr(ks, 'mode_c_subsystem_period', lambda **kw: calls['c'].append(kw['predicate']['signal_id']) or [])
    monkeypatch.setattr(ks, 'mode_d_av_bindhu', lambda **kw: calls['d'].append(kw['predicate']['signal_id']) or [])
    monkeypatch.setattr(ks, 'apply_trigger_suppression', lambda windows, **kw: windows)
    return calls


def _generate(preds, **extra):
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    windows = writer._generate_windows(
        pred_dicts=preds, horizon_start=date(2026, 1, 1), horizon_end=date(2027, 1, 1), dasha_kala_service=None,
        gochara_service=None, chart_id='c', native_ctx=NATIVE, enrichment_context=None, **extra)
    return writer, windows


def test_c1_signal_less_predicate_is_a_named_blank_in_every_mode(engine):
    writer, windows = _generate([_pred(None), _pred(None, signature_class='SUBSYSTEM'), _pred(None, NULL_TARGET)])
    assert windows == []
    assert engine == {'a': [], 'b': [], 'c': [], 'd': []}            # no mode ran for any of them, Mode D and Mode C included
    assert [(b['signal_id'], b['reason']) for b in writer._target_blanks] == [(None, 'signal_unresolved')] * 3


def test_c1_the_substep_notes_count_the_signal_blanks_beside_the_target_blanks(engine):
    writer, _ = _generate([_pred(None), _pred('s1', NULL_TARGET), _pred('s2')])
    notes = ks._target_blank_note(writer._target_blanks)
    assert 'signal_unresolved=1' in notes and 'target_unresolved=1' in notes
    assert ks._target_blank_note([]) == ''


def test_c2_mode_d_rides_the_first_predicate_that_has_a_signal(engine):
    _generate([_pred(None), _pred('sig-first'), _pred('sig-second')])
    assert engine['d'] == ['sig-first']
    assert engine['a'] == ['sig-first', 'sig-second']


def _lifetime_writer(preds, engine):
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    writer._conv_generation = 'candidate:test'
    writer._lt_preds = preds
    writer._birth_year = 1984
    writer._dks = writer._gs = writer._enrichment_ctx = writer._muhurta = None
    writer._native_ctx = NATIVE
    return writer


def test_c3_lifetime_tier_computes_mode_d_on_one_substep_only(engine):
    preds = [_pred(None), _pred('s1'), _pred('s2'), _pred('s3')]
    writer = _lifetime_writer(preds, engine)
    for idx in range(len(preds)):
        writer._substep_lifetime(MagicMock(), 'c', idx, dry_run=True)
    assert engine['d'] == ['s1']                                     # once, on the first attributable lifetime predicate
    assert engine['a'] == ['s1', 's2', 's3']                        # Mode A/B still scan every predicate against its own target


def test_c2_c3_a_subsystem_first_list_still_computes_mode_d_once_per_tier(engine):
    """Review of PR #3904, B-1: Mode C `continue`s before Mode D, so a SUBSYSTEM predicate cannot carry the Mode D set; it rides the first
    non-SUBSYSTEM predicate that has a signal, in the near call and on exactly one lifetime substep (contract 670 (a))."""
    preds = [_pred('sub1', signature_class='SUBSYSTEM'), _pred('y1'), _pred('y2')]
    _generate(preds)
    assert engine['d'] == ['y1']
    engine['d'].clear()
    writer = _lifetime_writer(preds, engine)
    for idx in range(len(preds)):
        writer._substep_lifetime(MagicMock(), 'c', idx, dry_run=True)
    assert engine['d'] == ['y1']
