"""Unit tests for ka_bhavishya_lekha writer — probabilistic forward projection."""
import json
import re
import pytest
from datetime import date

# Import the module under test
from pipeline.orchestrator.writers.ka_bhavishya_lekha import (
    _assign_tier,
    _infer_domain,
    _build_falsifiability,
    _build_projection_narrative,
    _DOMAINS,
    _TIER_LABELS,
)


# ---------------------------------------------------------------------------
# _assign_tier tests
# ---------------------------------------------------------------------------

def test_assign_tier_high():
    """effective >= 0.70, label='auspicious_strong' -> 'tier_1_high'"""
    assert _assign_tier(0.80, 'auspicious_strong') == 'tier_1_high'


def test_assign_tier_high_exact_boundary():
    """exactly 0.70 with a non-obstructed label -> tier_1_high"""
    assert _assign_tier(0.70, 'auspicious') == 'tier_1_high'


def test_assign_tier_moderate():
    """0.45 <= effective < 0.70 -> 'tier_2_moderate'"""
    assert _assign_tier(0.55, 'auspicious') == 'tier_2_moderate'


def test_assign_tier_moderate_lower_boundary():
    """exactly 0.45 -> tier_2_moderate"""
    assert _assign_tier(0.45, 'auspicious') == 'tier_2_moderate'


def test_assign_tier_speculative_low():
    """effective < 0.45 -> 'tier_3_speculative'"""
    assert _assign_tier(0.30, 'neutral') == 'tier_3_speculative'


def test_assign_tier_speculative_obstructed():
    """label='obstructed', effective=0.8 -> NOT tier_1 (obstructed overrides)"""
    result = _assign_tier(0.80, 'obstructed')
    assert result in ('tier_2_moderate', 'tier_3_speculative')
    assert result != 'tier_1_high'


def test_assign_tier_speculative_obstructed_severe():
    """label='obstructed_severe' even with high score -> NOT tier_1"""
    result = _assign_tier(0.90, 'obstructed_severe')
    assert result != 'tier_1_high'


def test_assign_tier_none_score():
    """score=None -> 'tier_3_speculative'"""
    assert _assign_tier(None, 'auspicious') == 'tier_3_speculative'


def test_assign_tier_neutral_high_score():
    """neutral label with high score should not reach tier_1"""
    result = _assign_tier(0.85, 'neutral')
    assert result != 'tier_1_high'


# ---------------------------------------------------------------------------
# _infer_domain tests
# ---------------------------------------------------------------------------

def test_infer_domain_no_rotation_unclassified():
    """Unclassified signals (no signal_type_id keyword match) return 'general'.
    Domain rotation was removed (F-W4-003) — false-precision domain labels
    violated MACRO_PLAN ethical framework (calibrated/falsifiable outputs).
    """
    domains = [_infer_domain(r, 'any') for r in range(7)]
    assert set(domains) == {'general'}, (
        f"Unclassified signals must all map to 'general', got: {set(domains)}"
    )


def test_infer_domain_valid_enum():
    """_infer_domain never returns outside the 13 valid canonical domains"""
    valid = {
        'career', 'wealth', 'relationship', 'progeny', 'health',
        'education', 'family', 'residence', 'travel', 'spirituality',
        'character', 'transition', 'general',
    }
    for rank in range(50):
        assert _infer_domain(rank, 'label') in valid


def test_infer_domain_keyword_match_overrides_general():
    """signal_type_id keyword match produces correct domain (not 'general')."""
    assert _infer_domain(0, 'any', signal_type_id='raja_yoga_career') == 'career'
    assert _infer_domain(0, 'any', signal_type_id='kalatra_seventh') == 'relationship'
    assert _infer_domain(0, 'any', signal_type_id='dhana_wealth') == 'wealth'


# ---------------------------------------------------------------------------
# _build_falsifiability tests
# ---------------------------------------------------------------------------

def test_build_falsifiability_has_required_keys():
    """Must have all four required keys"""
    result = _build_falsifiability('tier_1_high', 'career', date(2026, 9, 1), 0.75)
    assert 'confirm_observable' in result
    assert 'deny_observable' in result
    assert 'evaluation_date' in result
    assert 'evaluation_window_days' in result


def test_build_falsifiability_evaluation_window():
    """evaluation_window_days must be 21"""
    result = _build_falsifiability('tier_1_high', 'finance', date(2026, 8, 1), 0.60)
    assert result['evaluation_window_days'] == 21


def test_build_falsifiability_career_domain():
    """career domain: confirm_observable mentions 'career'"""
    result = _build_falsifiability('tier_2_moderate', 'career', date(2026, 7, 1), 0.55)
    assert 'career' in result['confirm_observable']


def test_build_falsifiability_health_domain():
    """health domain: confirm_observable mentions 'health'"""
    result = _build_falsifiability('tier_1_high', 'health', date(2026, 10, 1), 0.72)
    assert 'health' in result['confirm_observable']


def test_build_falsifiability_no_peak():
    """peak=None -> evaluation_date should be 'peak_date' string"""
    result = _build_falsifiability('tier_3_speculative', 'general', None, 0.30)
    assert result['evaluation_date'] == 'peak_date'


def test_build_falsifiability_peak_date_in_evaluation():
    """with a real peak_date, evaluation_date should include the date string"""
    peak = date(2027, 3, 15)
    result = _build_falsifiability('tier_1_high', 'finance', peak, 0.80)
    assert '2027-03-15' in result['evaluation_date']


def test_build_falsifiability_deny_mentions_domain():
    """deny_observable should reference the domain"""
    result = _build_falsifiability('tier_2_moderate', 'spiritual', date(2026, 12, 1), 0.50)
    assert 'spiritual' in result['deny_observable']


# ---------------------------------------------------------------------------
# _build_projection_narrative tests
# ---------------------------------------------------------------------------

def test_build_projection_narrative_has_required_keys():
    """Must have headline, probability_statement, domain_context, caveat"""
    result = _build_projection_narrative(
        tier='tier_1_high', domain='career', peak_date=date(2026, 9, 1),
        eff_score=0.75, conf_label='high', rarity=12.0, net_label='auspicious_strong'
    )
    assert 'headline' in result
    assert 'probability_statement' in result
    assert 'domain_context' in result
    assert 'caveat' in result


def test_build_projection_narrative_tier_in_prob_stmt():
    """probability_statement should mention the tier label text"""
    result = _build_projection_narrative(
        tier='tier_1_high', domain='finance', peak_date=date(2026, 8, 1),
        eff_score=0.80, conf_label='high', rarity=8.0, net_label='auspicious'
    )
    assert 'High probability' in result['probability_statement']


def test_build_projection_narrative_domain_in_headline():
    """headline must contain the domain name"""
    result = _build_projection_narrative(
        tier='tier_2_moderate', domain='relationship', peak_date=date(2027, 1, 1),
        eff_score=0.55, conf_label='medium', rarity=7.0, net_label='auspicious'
    )
    assert 'relationship' in result['headline'].lower()


def test_build_projection_narrative_calibration_caveat():
    """caveat must contain 'calibrated' or 'probabilistic'"""
    result = _build_projection_narrative(
        tier='tier_3_speculative', domain='general', peak_date=None,
        eff_score=0.30, conf_label='low', rarity=None, net_label='neutral'
    )
    assert 'calibrated' in result['caveat'] or 'probabilistic' in result['caveat']


def test_build_projection_narrative_none_peak():
    """None peak_date should not crash; headline uses 'unknown date'"""
    result = _build_projection_narrative(
        tier='tier_3_speculative', domain='health', peak_date=None,
        eff_score=0.25, conf_label=None, rarity=None, net_label='neutral'
    )
    assert 'headline' in result
    assert 'unknown date' in result['headline']


def test_build_projection_narrative_none_rarity():
    """rarity=None should not crash; domain_context still present"""
    result = _build_projection_narrative(
        tier='tier_2_moderate', domain='education', peak_date=date(2027, 6, 1),
        eff_score=0.50, conf_label='medium', rarity=None, net_label='auspicious'
    )
    assert 'domain_context' in result


# ---------------------------------------------------------------------------
# Module-level constant tests
# ---------------------------------------------------------------------------

def test_tier_labels_all_3_defined():
    """All 3 probability tiers must be in _TIER_LABELS"""
    assert 'tier_1_high' in _TIER_LABELS
    assert 'tier_2_moderate' in _TIER_LABELS
    assert 'tier_3_speculative' in _TIER_LABELS


def test_domains_all_7_defined():
    """_DOMAINS must contain exactly 13 entries (canonical vocabulary per migration 386)"""
    assert len(_DOMAINS) == 13


def test_domains_contains_required_values():
    """_DOMAINS must include all 13 canonical domain values"""
    required = {
        'career', 'wealth', 'relationship', 'progeny', 'health',
        'education', 'family', 'residence', 'travel', 'spirituality',
        'character', 'transition', 'general',
    }
    assert set(_DOMAINS) == required


# ---------------------------------------------------------------------------
# Writer contract tests (static analysis)
# ---------------------------------------------------------------------------

def test_writer_contract_no_commit():
    """Writer source must not call .commit()"""
    import inspect
    import pipeline.orchestrator.writers.ka_bhavishya_lekha as mod
    src = inspect.getsource(mod)
    # Allow occurrences only in comments
    non_comment_lines = [l for l in src.splitlines() if '.commit()' in l and not l.strip().startswith('#')]
    assert len(non_comment_lines) == 0, f"Found .commit() calls: {non_comment_lines}"


def test_writer_contract_no_rollback():
    """Writer source must not call .rollback()"""
    import inspect
    import pipeline.orchestrator.writers.ka_bhavishya_lekha as mod
    src = inspect.getsource(mod)
    non_comment_lines = [l for l in src.splitlines() if '.rollback()' in l and not l.strip().startswith('#')]
    assert len(non_comment_lines) == 0, f"Found .rollback() calls: {non_comment_lines}"


def test_writer_contract_no_l2_writes():
    """Writer source must not write to bodha_* tables"""
    import inspect
    import pipeline.orchestrator.writers.ka_bhavishya_lekha as mod
    src = inspect.getsource(mod)
    matches = re.findall(r'INSERT INTO bodha_|UPDATE bodha_', src)
    assert len(matches) == 0, f"Found L2 writes: {matches}"


def test_outcome_recorded_defaults_false():
    """The writer inserts outcome_recorded=False for all rows (static check)"""
    import inspect
    import pipeline.orchestrator.writers.ka_bhavishya_lekha as mod
    src = inspect.getsource(mod)
    # The writer explicitly appends False for outcome_recorded
    assert 'False' in src and 'outcome_recorded' in src
