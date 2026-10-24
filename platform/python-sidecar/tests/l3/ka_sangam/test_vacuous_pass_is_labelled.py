"""SR-SANGAM-SIGNAL-UNRESOLVED (condition on #3904): zero windows from admitted predicates is a LABELLED outcome, never a silent pass.

The registered integrity contract reads TRUE on an empty kala_convergence (nothing violates it), so a rebuild whose every admitted predicate is
signal-less (ka_yojaka's honest NULL signal_id) goes green having written nothing. The orchestrator persists no WriterResult.notes (FROZEN contract),
so the label is in the LAST substep's notes and in the run log: `signal_unresolved=<n> of <m>; vacuous=true reason=<...>`.

Claims (CLAUDE.md §N.8 a signal is measured, §N.7.6 honest null):
V1 a run that writes 0 windows from N>0 signal-less admitted predicates is labelled vacuous with the count `signal_unresolved=N of N`;
V2 a run that writes windows is NOT labelled vacuous (the label is measured from the windows, not asserted).
"""
import logging
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers import ka_sangam as ks
from services.ka_sangam.engine import EnrichmentContext, _date_to_jd

NATIVE = SimpleNamespace(janma_nakshatra_idx=24, moon_sign='Aquarius', location={'lat': 20.3, 'lon': 85.8})
NULL_TARGET = {'target_identity': None, 'target_longitude_deg': None, 'null_reason': 'target_unresolved'}
GOOD_TARGET = {'target_identity': 'Sun', 'target_longitude_deg': 123.5}


def _pred(signal_id, trigger=NULL_TARGET):
    return {'signal_id': signal_id, 'signature_class': 'YOGA', 'primary_domain': 'career', 'dignity_score': 0.6, 'transit_trigger_jsonb': trigger}


class _Cursor:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        return None


class _Conn:
    def cursor(self, *a, **kw):
        return _Cursor()


def _run(preds, monkeypatch):
    """Near substep + one lifetime substep per predicate, exactly the plan_substeps order; returns every substep's WriterResult."""
    monkeypatch.setattr(ks, 'has_stored_verification', lambda cur, table: False)
    monkeypatch.setattr(ks.KaSangamWriter, '_insert_windows', lambda self, cur, chart_id, windows, tier: len(windows))
    gochara = MagicMock()
    gochara.find_ingresses.side_effect = lambda planet, target_sign, start_jd, end_jd: (
        [SimpleNamespace(event_jd=_date_to_jd(date(2027, 3, 21)))] if target_sign == 'Aries' else [])
    writer = ks.KaSangamWriter.__new__(ks.KaSangamWriter)
    writer._conv_generation = 'candidate:k9'
    writer._pred_dicts = writer._lt_preds = preds
    writer._birth_year = 1984
    writer._resume_fingerprint = 'fixture'
    writer._dks = writer._muhurta = None
    writer._gs = gochara
    writer._enrichment_ctx = EnrichmentContext(ashtakavarga_bindu={'SARVA': {1: 32}})
    writer._native_ctx = NATIVE
    conn = _Conn()
    return [writer._substep_near(conn, 'c', dry_run=False)] + [writer._substep_lifetime(conn, 'c', i, dry_run=False) for i in range(len(preds))]


def test_v1_zero_windows_from_signal_less_predicates_is_labelled_vacuous_with_the_count(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger=ks.logger.name):
        results = _run([_pred(None), _pred(None), _pred(None)], monkeypatch)
    assert sum(r.rows_inserted for r in results) == 0
    assert 'vacuous' not in ''.join(r.notes for r in results[:-1])          # decided once, on the last substep, when the total is known
    last = results[-1].notes
    assert 'signal_unresolved=3 of 3' in last and 'vacuous=true reason=all_admitted_signal_unresolved' in last
    assert any('signal_unresolved=3 of 3; vacuous=true' in rec.getMessage() for rec in caplog.records)      # and in the run log


def test_v2_a_run_that_writes_windows_is_not_labelled_vacuous(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger=ks.logger.name):
        results = _run([_pred(None), _pred('s1', GOOD_TARGET), _pred('s2', GOOD_TARGET)], monkeypatch)
    assert sum(r.rows_inserted for r in results) > 0                        # Mode D on the first attributable predicate wrote windows
    assert all('vacuous' not in r.notes for r in results)
    assert 'signal_unresolved=1' in results[0].notes                         # the plain count of the blank stays visible
    assert not any('vacuous' in rec.getMessage() for rec in caplog.records)


def test_zero_admitted_predicates_is_a_named_vacuous_state_not_a_silent_one():
    """SR-K9-ADMITTED-ZERO: with target_floor = 0 (migration 1409) and 0 admitted predicates (K4-2b unadmitted) the run is labelled, so the K9 gate can tell it from a defect."""
    label = ks._vacuous_label(0, 0, 0)
    assert 'vacuous=true reason=no_admitted_predicates' in label
    assert ks._vacuous_label(0, 0, 5) == ''                                  # windows written: never labelled
