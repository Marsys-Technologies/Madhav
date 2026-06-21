"""Unit tests for ka_jivana_parva writer — ≥20 tests required."""
import re
import os
import pytest
from datetime import date

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestrator.writers.ka_jivana_parva import (
    _assign_quality,
    _derive_theme,
    _build_parva_narrative,
    _PLANET_THEMES,
)

WRITER_PATH = str(Path(__file__).parent.parent.parent / 'pipeline' / 'orchestrator' / 'writers' / 'ka_jivana_parva.py')

VALID_QUALITIES = {'building', 'peak', 'consolidating', 'receding', 'transitional'}
TODAY_Y = date.today().year


# --- _assign_quality tests ---

def test_assign_quality_ongoing_high_score():
    """Ongoing period with high avg_score -> peak."""
    result = _assign_quality(0, 9, 3, 0.65, TODAY_Y - 1, TODAY_Y + 5)
    assert result == 'peak'


def test_assign_quality_ongoing_low_score():
    """Ongoing period with low avg_score -> building."""
    result = _assign_quality(0, 9, 1, 0.30, TODAY_Y - 1, TODAY_Y + 5)
    assert result == 'building'


def test_assign_quality_ongoing_no_score():
    """Ongoing period with no avg_score -> building."""
    result = _assign_quality(0, 9, 0, None, TODAY_Y - 1, TODAY_Y + 5)
    assert result == 'building'


def test_assign_quality_past_high_avg():
    """Past period with avg_score >= 0.60 -> peak."""
    result = _assign_quality(3, 9, 5, 0.72, 2005, 2022)
    assert result == 'peak'


def test_assign_quality_past_moderate_avg():
    """Past period with avg_score 0.45-0.59 -> consolidating."""
    result = _assign_quality(3, 9, 2, 0.50, 2005, 2015)
    assert result == 'consolidating'


def test_assign_quality_past_low_avg():
    """Past period with avg_score 0.25-0.44 -> receding."""
    result = _assign_quality(3, 9, 1, 0.30, 2000, 2010)
    assert result == 'receding'


def test_assign_quality_no_avg_score():
    """Past period with no avg_score -> transitional."""
    result = _assign_quality(3, 9, 0, None, 2000, 2010)
    assert result == 'transitional'


def test_assign_quality_past_very_low_avg():
    """Past period with avg_score below 0.25 -> transitional."""
    result = _assign_quality(5, 9, 0, 0.10, 1990, 2000)
    assert result == 'transitional'


# --- _derive_theme tests ---

def test_derive_theme_sun():
    """Sun theme includes 'authority'."""
    result = _derive_theme('Sun', 'peak')
    assert 'authority' in result


def test_derive_theme_saturn():
    """Saturn theme includes 'discipline'."""
    result = _derive_theme('Saturn', 'building')
    assert 'discipline' in result


def test_derive_theme_unknown_planet():
    """Unknown planet returns list without raising."""
    result = _derive_theme('Unknown', 'transitional')
    assert isinstance(result, list)
    assert len(result) >= 1


def test_derive_theme_length():
    """Theme always returns 4 items (3 base + quality)."""
    for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        result = _derive_theme(planet, 'peak')
        assert len(result) == 4, f"Expected 4 items for {planet}, got {len(result)}"


def test_derive_theme_quality_appended():
    """Quality label is the last item in theme keywords."""
    result = _derive_theme('Jupiter', 'consolidating')
    assert result[-1] == 'consolidating'


# --- _build_parva_narrative tests ---

def test_build_parva_narrative_has_required_keys():
    """Narrative dict has all required keys."""
    result = _build_parva_narrative('Jupiter', 2005, 2021, 'peak', 3, 0.65)
    for key in ('summary', 'dasha_planet', 'span', 'quality'):
        assert key in result, f"Missing key: {key}"


def test_build_parva_narrative_past_span():
    """Past span includes end year."""
    result = _build_parva_narrative('Saturn', 1990, 2009, 'consolidating', 2, 0.48)
    assert '2009' in result['span']


def test_build_parva_narrative_ongoing_span():
    """Ongoing span ends with 'present'."""
    result = _build_parva_narrative('Rahu', 2021, None, 'building', 0, None)
    assert result['span'].endswith('present')


def test_build_parva_narrative_high_count_singular():
    """Singular window in narrative."""
    result = _build_parva_narrative('Sun', 2005, 2015, 'peak', 1, 0.70)
    assert '1 high-convergence window' in result['summary']
    assert 'windows' not in result['summary']


def test_build_parva_narrative_high_count_plural():
    """Plural windows in narrative."""
    result = _build_parva_narrative('Moon', 2005, 2015, 'peak', 2, 0.65)
    assert '2 high-convergence windows' in result['summary']


def test_build_parva_narrative_zero_count():
    """Zero windows in narrative."""
    result = _build_parva_narrative('Ketu', 1990, 2000, 'receding', 0, 0.20)
    assert '0 high-convergence windows' in result['summary']


# --- _PLANET_THEMES completeness ---

def test_planet_themes_all_9_defined():
    """All 9 grahas must be in _PLANET_THEMES."""
    expected = {'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'}
    assert expected == set(_PLANET_THEMES.keys())


# --- Quality enum validity ---

def test_quality_valid_enum():
    """_assign_quality never returns a value outside the 5 valid values."""
    test_cases = [
        (0, 9, 3, 0.65, TODAY_Y - 1, TODAY_Y + 5),
        (0, 9, 1, 0.30, TODAY_Y - 1, TODAY_Y + 5),
        (3, 9, 5, 0.72, 2005, 2022),
        (3, 9, 2, 0.50, 2005, 2015),
        (3, 9, 1, 0.30, 2000, 2010),
        (3, 9, 0, None, 2000, 2010),
        (5, 9, 0, 0.10, 1990, 2000),
        (0, 9, 0, None, TODAY_Y - 1, TODAY_Y + 5),
    ]
    for args in test_cases:
        result = _assign_quality(*args)
        assert result in VALID_QUALITIES, f"Invalid quality '{result}' for args {args}"


# --- Contract enforcement via grep ---

def test_writer_contract_no_commit():
    """Writer must not call .commit()."""
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    matches = re.findall(r'\.commit\(\)', content)
    assert len(matches) == 0, f"Found .commit() calls in writer: {matches}"


def test_writer_contract_no_rollback():
    """Writer must not call .rollback()."""
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    matches = re.findall(r'\.rollback\(\)', content)
    assert len(matches) == 0, f"Found .rollback() calls in writer: {matches}"


def test_writer_contract_no_l2_writes():
    """Writer must not write to bodha_ tables."""
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    matches = re.findall(r'INSERT INTO bodha_|UPDATE bodha_', content)
    assert len(matches) == 0, f"Found bodha_ table writes: {matches}"


def test_writer_reads_chart_dashas_not_ganita_dashas():
    """Writer must read from chart_dashas, not ganita_dashas."""
    with open(WRITER_PATH, 'r') as f:
        content = f.read()
    assert 'chart_dashas' in content, "Writer must reference chart_dashas"
    assert 'ganita_dashas' not in content, "Writer must NOT reference ganita_dashas"
