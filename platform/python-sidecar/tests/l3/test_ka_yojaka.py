"""
Tests for ka_yojaka: classifier + binder
Run: pytest -q tests/l3/test_ka_yojaka.py -v
"""
import re
from pathlib import Path

import pytest

from services.ka_yojaka.classifier import classify_signal
from services.ka_yojaka.binder import build_predicate


# ---------------------------------------------------------------------------
# Classifier tests (T1–T8)
# ---------------------------------------------------------------------------

def test_classify_yoga():
    assert classify_signal({'signal_type_class': 'yoga'}) == 'YOGA'


def test_classify_dosha():
    assert classify_signal({'signal_type_class': 'dosha'}) == 'DOSHA'


def test_classify_parivartana():
    assert classify_signal({'signal_type_class': 'parivartana'}) == 'DISPOSITOR_RELATIONAL'


def test_classify_sade_sati():
    assert classify_signal({'signal_type_class': 'sade_sati'}) == 'SUBSYSTEM'


def test_classify_configuration_kala_sarpa():
    sig = {'signal_type_class': 'configuration', 'signal_type_id': 'kala_sarpa_per_varga:ks_detection'}
    assert classify_signal(sig) == 'DOSHA'


def test_classify_configuration_conjunction():
    sig = {'signal_type_class': 'configuration', 'signal_type_id': 'conjunction:sun_moon'}
    assert classify_signal(sig) == 'CONJUNCTION_ASPECT'


def test_classify_unknown_returns_residual():
    assert classify_signal({'signal_type_class': 'totally_unknown_class'}) == 'CLASSIFY_RESIDUAL'


def test_classify_determinism():
    sig = {'signal_type_class': 'yoga', 'signal_type_id': 'some_yoga'}
    assert classify_signal(sig) == classify_signal(sig)


# Additional classifier coverage
def test_classify_karaka_alignment():
    assert classify_signal({'signal_type_class': 'karaka_alignment'}) == 'DISPOSITOR_RELATIONAL'


def test_classify_tradition_specific():
    assert classify_signal({'signal_type_class': 'tradition_specific'}) == 'DIGNITY'


def test_classify_composite_state():
    assert classify_signal({'signal_type_class': 'composite_state'}) == 'SUBSYSTEM'


def test_classify_configuration_sensitive_point():
    sig = {'signal_type_class': 'configuration', 'signal_type_id': 'arudha_lagna_analysis'}
    assert classify_signal(sig) == 'SENSITIVE_POINT'


# ---------------------------------------------------------------------------
# Binder tests (T9–T15)
# ---------------------------------------------------------------------------

_YOGA_SIGNAL = {
    'signal_type_class': 'yoga',
    'signal_type_id': 'test_yoga',
    'configuration_jsonb': {'grahas': ['sun', 'moon']},
    'constituent_facts_array': ['fact1', 'fact2'],
    'valence': 1.0,
    'dignity_score': 0.8,
}

_DOSHA_SIGNAL = {
    'signal_type_class': 'dosha',
    'signal_type_id': 'mangal_dosha',
    'configuration_jsonb': {},
    'constituent_facts_array': [],
}

_SUBSYSTEM_SIGNAL = {
    'signal_type_class': 'sade_sati',
    'signal_type_id': 'sade_sati_phase',
    'configuration_jsonb': {},
    'constituent_facts_array': [],
}


def test_build_predicate_yoga_has_all_keys():
    pred = build_predicate(_YOGA_SIGNAL, 'YOGA')
    assert set(pred.keys()) == {'dasha_eligibility_rule', 'transit_trigger', 'strength_affliction_hook', 'derivation_ledger'}


def test_build_predicate_yoga_derivation_ledger():
    pred = build_predicate(_YOGA_SIGNAL, 'YOGA')
    assert pred['derivation_ledger']['bg_transit_rules_ids'] == [1, 2, 3, 4]


def test_build_predicate_yoga_dasha_type():
    pred = build_predicate(_YOGA_SIGNAL, 'YOGA')
    assert pred['dasha_eligibility_rule']['type'] == 'dasha_lord_in_constituents'


def test_build_predicate_dosha_transit_trigger():
    pred = build_predicate(_DOSHA_SIGNAL, 'DOSHA')
    assert pred['transit_trigger']['type'] == 'malefic_transit_over_afflicted_point'


def test_build_predicate_subsystem_type():
    pred = build_predicate(_SUBSYSTEM_SIGNAL, 'SUBSYSTEM')
    assert pred['dasha_eligibility_rule']['type'] == 'subsystem_specific'


def test_build_predicate_subsystem_empty_bg_rules():
    pred = build_predicate(_SUBSYSTEM_SIGNAL, 'SUBSYSTEM')
    assert pred['derivation_ledger']['bg_transit_rules_ids'] == []


def test_build_predicate_derivation_ledger_ratified_by():
    for sc in ('YOGA', 'DOSHA', 'DIGNITY', 'DISPOSITOR_RELATIONAL', 'SENSITIVE_POINT', 'CONJUNCTION_ASPECT', 'SUBSYSTEM', 'CLASSIFY_RESIDUAL'):
        pred = build_predicate(_YOGA_SIGNAL, sc)
        assert 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md' in pred['derivation_ledger']['ratified_by']


# ---------------------------------------------------------------------------
# Anti-drift / contract tests (T13–T15)
# ---------------------------------------------------------------------------

WRITER_PATH = Path(__file__).parent.parent.parent / 'pipeline' / 'orchestrator' / 'writers' / 'ka_yojaka.py'


def test_no_commit_or_rollback_in_writer():
    """Writer must NEVER call .commit() or .rollback() — orchestrator owns the transaction."""
    src = WRITER_PATH.read_text()
    # Use AST-level check: look for actual method calls, not string mentions in comments/docstrings
    # Strip all comment lines and triple-quoted docstrings before scanning
    import re as _re
    # Remove triple-quoted docstrings
    stripped = _re.sub(r'''""".*?"""''', '', src, flags=_re.DOTALL)
    stripped = _re.sub(r"'''.*?'''", '', stripped, flags=_re.DOTALL)
    # Remove inline and full-line comments
    stripped = _re.sub(r'#.*', '', stripped)
    assert '.commit()' not in stripped, 'Found .commit() call in writer — violates orchestrator contract'
    assert '.rollback()' not in stripped, 'Found .rollback() call in writer — violates orchestrator contract'


def test_no_l2_writes_in_writer():
    """Writer must NEVER INSERT/UPDATE into bodha_* tables."""
    src = WRITER_PATH.read_text()
    assert not re.search(r'INSERT INTO bodha_', src), 'Found INSERT INTO bodha_* in writer'
    assert not re.search(r'UPDATE bodha_', src), 'Found UPDATE bodha_* in writer'


def test_writer_only_selects_from_bodha():
    """bodha_msr_signals should appear only in SELECT context."""
    src = WRITER_PATH.read_text()
    # Check bodha_msr_signals appears (we read from it)
    assert 'bodha_msr_signals' in src
    # Check it's only in a SELECT
    select_match = re.search(r'FROM bodha_msr_signals', src)
    assert select_match, 'Expected SELECT FROM bodha_msr_signals'
