"""SR-EMPTY-REASON (root CLAUDE.md §N.6 rule 4, §N.7.6): pure oracles for the empty-layer vocabulary and the two places a
Python writer turns an empty obstruction layer into a statement (ph_muhurta's verdict reason, ka_kala_darshana's narrative).
The database-backed oracles are in tests/l3/kala_db/test_empty_layer_reason_db.py.

  P1  the classification maps measured counts to the reason, and an unmeasured count is never read as "none"
  P2  the vocabulary is the TypeScript route's (empty_layer_reason.ts), pinned against the source
  P3  a muhurta record whose obstruction layer was empty says so in its verdict reason and ledger; a measured-clear or populated
      layer adds nothing; an unmeasured layer is not read as clear
  P4  a darshana narrative over an unassessed empty obstruction layer says "not checked"; with no layer argument it is unchanged
"""
import re
from pathlib import Path

import pytest

from pipeline.orchestrator.writers.ka_kala_darshana import _build_narrative
from services.kala_core.empty_layer_reason import EMPTY_LAYER_REASONS, classify_empty_layer
from services.ph_muhurta.engine import MuhurtaContext, derive_muhurta_record, obstruction_layer_note

TS = Path(__file__).resolve().parents[4] / 'src/lib/retrieval/registry/layers/L3_kala/empty_layer_reason.ts'


@pytest.mark.parametrize('any_rows,served,state,reason', [
    (0, 0, None, 'layer_not_computed'),
    (0, 0, 'stale', 'layer_not_computed'),
    (0, 0, 'building', 'layer_not_computed'),
    (0, 0, 'lit', 'computed_found_none'),
    (3, 0, 'lit', 'rows_outside_served_generation'),
    (3, 0, None, 'rows_outside_served_generation'),
    (3, 2, 'lit', 'filters_excluded_all_rows'),
    (None, 0, 'lit', 'layer_state_unreadable'),
    (0, None, 'lit', 'layer_state_unreadable'),
])
def test_p1_classification(any_rows, served, state, reason):
    assert classify_empty_layer(any_rows, served, state) == reason


def test_p2_vocabulary_matches_the_typescript_route():
    source = TS.read_text(encoding='utf-8')
    block = re.search(r'EMPTY_LAYER_REASONS = \[(.*?)\] as const', source, re.S).group(1)
    assert tuple(re.findall(r"'([a-z_]+)'", block)) == EMPTY_LAYER_REASONS


def ctx(layer):
    return MuhurtaContext(action_class='new_venture', obstruction_layer=layer)


@pytest.mark.parametrize('layer', [
    {'windows': 0, 'empty_reason': 'layer_not_computed'},
    {'windows': 0, 'empty_reason': 'served_rows_without_convergence_window'},
    {'windows': 0, 'empty_reason': 'obstruction_read_failed'},
    {'windows': 0, 'empty_reason': 'layer_state_unreadable'},
    None,
])
def test_p3_an_unassessed_obstruction_layer_is_stated_not_read_as_no_overlap(layer):
    record = derive_muhurta_record(ctx(layer))
    assert 'Obstruction overlap not assessed' in record.verdict_reason
    if layer is not None:
        assert layer['empty_reason'] in record.verdict_reason
    assert record.derivation_ledger_jsonb['obstruction_overlap_assessed'] is False
    assert record.derivation_ledger_jsonb['obstruction_layer'] == layer


@pytest.mark.parametrize('layer', [
    {'windows': 4, 'empty_reason': None},
    {'windows': 0, 'empty_reason': 'computed_found_none'},
])
def test_p3_a_populated_or_measured_clear_layer_adds_no_note(layer):
    record = derive_muhurta_record(ctx(layer))
    assert 'not assessed' not in (record.verdict_reason or '')
    assert record.derivation_ledger_jsonb['obstruction_overlap_assessed'] is True
    assert obstruction_layer_note(layer) == (True, None)


def narrative(layer=None, obstructions=()):
    return _build_narrative(mode='C', effective_score=0.8, net_label='auspicious_strong', peak_date='2030-03-03',
                            conf_label='high', obstructions=list(obstructions), orb_strength=0.5, rarity_years=3.0,
                            **({} if layer is None else {'obstruction_layer': layer}))


def test_p4_unassessed_empty_layer_narrative_says_not_checked():
    n = narrative({'assessed': False, 'empty_reason': 'layer_not_computed', 'layer_state': {}})
    assert n['caution'] == 'Not checked against obstructions: the obstruction layer is empty (layer_not_computed).'
    assert n['obstruction_layer']['assessed'] is False


def test_p4_measured_clear_and_no_layer_argument_leave_the_narrative_unchanged():
    assert narrative()['caution'] is None and 'obstruction_layer' not in narrative()
    clear = narrative({'assessed': True, 'empty_reason': 'computed_found_none', 'layer_state': {}})
    assert clear['caution'] is None and clear['obstruction_layer']['assessed'] is True
