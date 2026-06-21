"""Tests for ka_kala_darshana writer — effective score, net label, narrative, contracts."""
import pytest
import re
from pathlib import Path

# Import the pure functions directly
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestrator.writers.ka_kala_darshana import (
    _compute_effective_score,
    _compute_net_label,
    _build_narrative,
)

VALID_LABELS = {
    'auspicious_strong',
    'auspicious_moderate',
    'auspicious_speculative',
    'obstructed',
    'obstructed_severe',
    'neutral',
}


# --- effective score ---

def test_effective_score_no_obstructions():
    assert _compute_effective_score(0.75, []) == pytest.approx(0.75)


def test_effective_score_with_override():
    obs = [{'override_score': 0.25, 'severity': 'moderate', 'type': 'papa_graha'}]
    result = _compute_effective_score(0.8, obs)
    assert result == pytest.approx(0.8 * 0.75)


def test_effective_score_max_override_not_additive():
    obs = [
        {'override_score': 0.2, 'severity': 'moderate', 'type': 'papa_graha'},
        {'override_score': 0.3, 'severity': 'moderate', 'type': 'graha_yuddha'},
    ]
    result = _compute_effective_score(1.0, obs)
    # max is 0.3, not 0.5
    assert result == pytest.approx(1.0 * (1 - 0.3))


def test_effective_score_clamp_low():
    obs = [{'override_score': 1.5, 'severity': 'severe', 'type': 'papa_graha'}]
    result = _compute_effective_score(0.5, obs)
    assert result >= 0.0


def test_effective_score_clamp_high():
    result = _compute_effective_score(1.5, [])
    assert result <= 1.0


def test_effective_score_zero_override():
    obs = [{'override_score': 0.0, 'severity': 'moderate', 'type': 'papa_graha'}]
    result = _compute_effective_score(0.6, obs)
    assert result == pytest.approx(0.6)


def test_effective_score_full_override():
    obs = [{'override_score': 1.0, 'severity': 'severe', 'type': 'papa_graha'}]
    result = _compute_effective_score(0.9, obs)
    assert result == pytest.approx(0.0)


# --- net label ---

def test_net_label_strong():
    label = _compute_net_label(0.80, [])
    assert label == 'auspicious_strong'


def test_net_label_moderate():
    label = _compute_net_label(0.55, [])
    assert label == 'auspicious_moderate'


def test_net_label_speculative():
    label = _compute_net_label(0.30, [])
    assert label == 'auspicious_speculative'


def test_net_label_obstructed_severe():
    obs = [{'severity': 'severe', 'type': 'papa_graha', 'override_score': 0.5}]
    # Even with high effective score, severe obstruction → obstructed_severe
    label = _compute_net_label(0.90, obs)
    assert label == 'obstructed_severe'


def test_net_label_obstructed_moderate_low_score():
    obs = [{'severity': 'moderate', 'type': 'papa_graha', 'override_score': 0.3}]
    label = _compute_net_label(0.35, obs)
    assert label == 'obstructed'


def test_net_label_neutral():
    label = _compute_net_label(0.10, [])
    assert label == 'neutral'


def test_net_label_moderate_high_score_not_obstructed():
    # moderate obstruction but effective score >= 0.4 → NOT 'obstructed', goes through score thresholds
    obs = [{'severity': 'moderate', 'type': 'papa_graha', 'override_score': 0.1}]
    label = _compute_net_label(0.70, obs)
    # has_moderate=True, effective=0.70 >= 0.4 → skip obstructed check → effective >= 0.70 → auspicious_strong
    assert label == 'auspicious_strong'


def test_net_label_valid_enum():
    test_cases = [
        (0.80, []),
        (0.55, []),
        (0.30, []),
        (0.10, []),
        (0.90, [{'severity': 'severe', 'type': 'x', 'override_score': 0.5}]),
        (0.35, [{'severity': 'moderate', 'type': 'x', 'override_score': 0.3}]),
        (0.05, [{'severity': 'mild', 'type': 'x', 'override_score': 0.1}]),
    ]
    for score, obs in test_cases:
        label = _compute_net_label(score, obs)
        assert label in VALID_LABELS, f"Invalid label '{label}' for score={score}, obs={obs}"


# --- narrative ---

def test_narrative_has_required_keys():
    narrative = _build_narrative(
        mode='A', effective_score=0.75, net_label='auspicious_strong',
        peak_date='2026-09-15', conf_label='high', obstructions=[],
        orb_strength=0.8, rarity_years=5.0,
    )
    assert 'headline' in narrative
    assert 'context' in narrative
    assert 'caution' in narrative


def test_narrative_headline_contains_peak_date():
    narrative = _build_narrative(
        mode='A', effective_score=0.75, net_label='auspicious_strong',
        peak_date='2026-09-15', conf_label='high', obstructions=[],
        orb_strength=0.8, rarity_years=5.0,
    )
    assert '2026-09-15' in narrative['headline']


def test_narrative_caution_none_for_clear_window():
    narrative = _build_narrative(
        mode='A', effective_score=0.80, net_label='auspicious_strong',
        peak_date='2026-09-15', conf_label='high', obstructions=[],
        orb_strength=0.9, rarity_years=3.0,
    )
    assert narrative['caution'] is None


def test_narrative_caution_set_for_severe():
    obs = [{'severity': 'severe', 'type': 'papa_graha_conjunction', 'override_score': 0.6}]
    narrative = _build_narrative(
        mode='A', effective_score=0.40, net_label='obstructed_severe',
        peak_date='2026-09-15', conf_label='moderate', obstructions=obs,
        orb_strength=0.5, rarity_years=2.0,
    )
    assert narrative['caution'] is not None
    assert narrative['caution'].startswith('Severe')


def test_narrative_caution_set_for_moderate():
    obs = [{'severity': 'moderate', 'type': 'graha_yuddha', 'override_score': 0.3}]
    narrative = _build_narrative(
        mode='B', effective_score=0.55, net_label='auspicious_moderate',
        peak_date='2026-09-15', conf_label='moderate', obstructions=obs,
        orb_strength=0.6, rarity_years=1.5,
    )
    assert narrative['caution'] is not None
    assert narrative['caution'].startswith('Moderate')


def test_narrative_mode_a_label():
    narrative = _build_narrative(
        mode='A', effective_score=0.75, net_label='auspicious_strong',
        peak_date='2026-09-15', conf_label='high', obstructions=[],
        orb_strength=0.8, rarity_years=5.0,
    )
    assert 'daśā-aligned' in narrative['context']


def test_narrative_mode_b_label():
    narrative = _build_narrative(
        mode='B', effective_score=0.75, net_label='auspicious_strong',
        peak_date='2026-09-15', conf_label='high', obstructions=[],
        orb_strength=0.8, rarity_years=5.0,
    )
    assert 'independent sweep' in narrative['context']


def test_narrative_unknown_peak_date():
    narrative = _build_narrative(
        mode='A', effective_score=0.60, net_label='auspicious_moderate',
        peak_date=None, conf_label='low', obstructions=[],
        orb_strength=None, rarity_years=None,
    )
    assert 'unknown date' in narrative['headline']


# --- contract checks ---

def test_writer_contract_no_commit():
    writer_path = Path(__file__).parent.parent.parent / 'pipeline/orchestrator/writers/ka_kala_darshana.py'
    content = writer_path.read_text()
    # Should not contain .commit() call
    assert '.commit()' not in content, "Writer must not call .commit()"


def test_writer_contract_no_rollback():
    writer_path = Path(__file__).parent.parent.parent / 'pipeline/orchestrator/writers/ka_kala_darshana.py'
    content = writer_path.read_text()
    assert '.rollback()' not in content, "Writer must not call .rollback()"


def test_writer_contract_no_l2_writes():
    writer_path = Path(__file__).parent.parent.parent / 'pipeline/orchestrator/writers/ka_kala_darshana.py'
    content = writer_path.read_text()
    assert 'INSERT INTO bodha_' not in content, "Writer must not write to L2 tables"
    assert 'UPDATE bodha_' not in content, "Writer must not update L2 tables"


def test_writer_registered():
    """Writer must be decorated with @register('ka_kala_darshana')."""
    writer_path = Path(__file__).parent.parent.parent / 'pipeline/orchestrator/writers/ka_kala_darshana.py'
    content = writer_path.read_text()
    assert "register('ka_kala_darshana')" in content, "Writer must have @register('ka_kala_darshana') decorator"
