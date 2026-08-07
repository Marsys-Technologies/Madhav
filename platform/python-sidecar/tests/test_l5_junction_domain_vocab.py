"""
test_l5_junction_domain_vocab.py — SHABDA-SHUDDHI · Lane L5 Dead Junctions

TDD tests written FIRST (failing before fixes land).

Covers:
  Fix 1 — ka_bhavishya_lekha._DOMAINS must use CANONICAL_DOMAINS (no 'finance'/'spiritual')
  Fix 2 — ka_yojaka._SIGNAL_DOMAIN_KEYWORDS must use canonical keys ('wealth' / 'spirituality')
  Fix 5 — ph_phaladesa / engine._ALL_DOMAINS must cover all 13 canonical domains
  Fix 7a — bo_upaya: empty-prescriptions summary must NOT yield "light" intensity
  Fix 7b — mi_adhilepa._overlay_row: leakage must be None (not hardcoded 'clean')
"""
from __future__ import annotations

import sys
import pathlib
import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS


# ─────────────────────────────────────────────────────────────────────────────
# Fix 1: ka_bhavishya_lekha._DOMAINS
# ─────────────────────────────────────────────────────────────────────────────

def test_ka_bhavishya_lekha_domains_are_all_canonical():
    """_DOMAINS in ka_bhavishya_lekha must be a subset of CANONICAL_DOMAINS.

    Before the fix: 'finance' and 'spiritual' are present — both violate the
    DB CHECK constraint on kala_bhavishya (migration 386).  This test is
    written FAILING first and must pass after the fix.
    """
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import _DOMAINS
    non_canonical = [d for d in _DOMAINS if d not in CANONICAL_DOMAINS]
    assert not non_canonical, (
        f"ka_bhavishya_lekha._DOMAINS contains non-canonical values: {non_canonical}. "
        f"These violate the DB CHECK constraint (migration 386). "
        f"Replace with canonical equivalents from brahmagyan.domain_vocabulary.CANONICAL_DOMAINS."
    )


def test_ka_bhavishya_lekha_domain_keywords_keys_are_canonical():
    """_DOMAIN_KEYWORDS keys in ka_bhavishya_lekha must all be canonical domain names.

    Before the fix: 'finance' and 'spiritual' keys are present.
    """
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import _DOMAIN_KEYWORDS
    keys = [domain for domain, _ in _DOMAIN_KEYWORDS]
    non_canonical = [k for k in keys if k not in CANONICAL_DOMAINS]
    assert not non_canonical, (
        f"ka_bhavishya_lekha._DOMAIN_KEYWORDS has non-canonical domain keys: {non_canonical}"
    )


def test_ka_bhavishya_lekha_no_finance_key():
    """'finance' must not appear anywhere in _DOMAINS or _DOMAIN_KEYWORDS keys."""
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import _DOMAINS, _DOMAIN_KEYWORDS
    kw_keys = [d for d, _ in _DOMAIN_KEYWORDS]
    assert 'finance' not in _DOMAINS, "'finance' is a legacy non-canonical domain"
    assert 'finance' not in kw_keys, "'finance' key in _DOMAIN_KEYWORDS violates canonical vocab"


def test_ka_bhavishya_lekha_no_spiritual_key():
    """'spiritual' must not appear anywhere in _DOMAINS or _DOMAIN_KEYWORDS keys."""
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import _DOMAINS, _DOMAIN_KEYWORDS
    kw_keys = [d for d, _ in _DOMAIN_KEYWORDS]
    assert 'spiritual' not in _DOMAINS, "'spiritual' is a legacy non-canonical domain"
    assert 'spiritual' not in kw_keys, "'spiritual' key in _DOMAIN_KEYWORDS violates canonical vocab"


def test_ka_bhavishya_lekha_has_wealth_and_spirituality():
    """The canonical replacements 'wealth' and 'spirituality' must be present."""
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import _DOMAINS, _DOMAIN_KEYWORDS
    kw_keys = [d for d, _ in _DOMAIN_KEYWORDS]
    assert 'wealth' in _DOMAINS, "'wealth' (canonical) must be in _DOMAINS"
    assert 'spirituality' in _DOMAINS, "'spirituality' (canonical) must be in _DOMAINS"
    assert 'wealth' in kw_keys, "'wealth' key must appear in _DOMAIN_KEYWORDS"
    assert 'spirituality' in kw_keys, "'spirituality' key must appear in _DOMAIN_KEYWORDS"


# ─────────────────────────────────────────────────────────────────────────────
# Fix 2: ka_yojaka._SIGNAL_DOMAIN_KEYWORDS
# ─────────────────────────────────────────────────────────────────────────────

def test_ka_yojaka_signal_domain_keywords_keys_are_canonical():
    """_SIGNAL_DOMAIN_KEYWORDS in ka_yojaka must have only canonical domain keys.

    Before the fix: 'finance' and 'spiritual' are used as keys.
    """
    from pipeline.orchestrator.writers.ka_yojaka import _SIGNAL_DOMAIN_KEYWORDS
    non_canonical = [k for k in _SIGNAL_DOMAIN_KEYWORDS if k not in CANONICAL_DOMAINS]
    assert not non_canonical, (
        f"ka_yojaka._SIGNAL_DOMAIN_KEYWORDS has non-canonical keys: {non_canonical}"
    )


def test_ka_yojaka_no_finance_key():
    from pipeline.orchestrator.writers.ka_yojaka import _SIGNAL_DOMAIN_KEYWORDS
    assert 'finance' not in _SIGNAL_DOMAIN_KEYWORDS, (
        "'finance' is a legacy key — use 'wealth' (canonical)"
    )


def test_ka_yojaka_no_spiritual_key():
    from pipeline.orchestrator.writers.ka_yojaka import _SIGNAL_DOMAIN_KEYWORDS
    assert 'spiritual' not in _SIGNAL_DOMAIN_KEYWORDS, (
        "'spiritual' is a legacy key — use 'spirituality' (canonical)"
    )


def test_ka_yojaka_has_wealth_and_spirituality():
    from pipeline.orchestrator.writers.ka_yojaka import _SIGNAL_DOMAIN_KEYWORDS
    assert 'wealth' in _SIGNAL_DOMAIN_KEYWORDS, "'wealth' must be a key in _SIGNAL_DOMAIN_KEYWORDS"
    assert 'spirituality' in _SIGNAL_DOMAIN_KEYWORDS, "'spirituality' must be a key in _SIGNAL_DOMAIN_KEYWORDS"


# ─────────────────────────────────────────────────────────────────────────────
# Fix 5: ph_phaladesa engine._ALL_DOMAINS covers all 13 canonical domains
# ─────────────────────────────────────────────────────────────────────────────

def test_ph_phaladesa_all_domains_covers_canonical():
    """_ALL_DOMAINS in services.ph_phaladesa.engine must cover all 13 canonical domains.

    Before the fix: only 7 domains are listed — progeny, education, family,
    residence, travel, and transition are missing from what gets iterated.
    """
    from services.ph_phaladesa.engine import _ALL_DOMAINS
    missing = CANONICAL_DOMAINS - set(_ALL_DOMAINS)
    assert not missing, (
        f"ph_phaladesa engine._ALL_DOMAINS is missing canonical domains: {sorted(missing)}. "
        f"These domains will never receive a phala_phaladesa row."
    )


def test_ph_phaladesa_all_domains_no_non_canonical():
    """_ALL_DOMAINS must not contain any non-canonical domain strings."""
    from services.ph_phaladesa.engine import _ALL_DOMAINS
    non_canonical = [d for d in _ALL_DOMAINS if d not in CANONICAL_DOMAINS]
    assert not non_canonical, (
        f"ph_phaladesa engine._ALL_DOMAINS has non-canonical values: {non_canonical}"
    )


def test_ph_phaladesa_all_domains_has_13_members():
    """_ALL_DOMAINS must have exactly 13 members (all canonical domains)."""
    from services.ph_phaladesa.engine import _ALL_DOMAINS
    assert len(set(_ALL_DOMAINS)) == 13, (
        f"Expected 13 canonical domains in _ALL_DOMAINS, got {len(set(_ALL_DOMAINS))}: "
        f"{sorted(_ALL_DOMAINS)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fix 7a: bo_upaya — empty prescriptions must not yield "light" intensity
# ─────────────────────────────────────────────────────────────────────────────

def test_bo_upaya_empty_prescriptions_summary_intensity_is_not_light():
    """When prescriptions list is empty, recommended_intensity_class must NOT be 'light'.

    Before the fix: an empty prescriptions list yields top_class='low'→intensity='light'
    because `ranked_res[0]` falls back to 'low' as top_class on an empty resonance list.

    The correct behaviour for a chart with no prescriptions at all:
    intensity_class = None (no prescriptions to assess intensity for).
    """
    import uuid
    from datetime import datetime, timezone

    from pipeline.orchestrator.writers.bo_upaya import _build_rm_summary

    now = datetime.now(timezone.utc).isoformat()
    result = _build_rm_summary(
        chart_id=str(uuid.uuid4()),
        aya='lahiri_chitrapaksha',
        build_id=str(uuid.uuid4()),
        resonances=[],
        prescriptions=[],
        chart_typology='standard',
        now=now,
    )
    assert result['recommended_intensity_class'] is None, (
        f"With empty prescriptions, recommended_intensity_class should be None "
        f"(no prescriptions to assess), not {result['recommended_intensity_class']!r}. "
        f"'light' is a false clean-bill that implies a real assessment was made."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fix 7b: mi_adhilepa._overlay_row leakage must be None
# ─────────────────────────────────────────────────────────────────────────────

def test_mi_adhilepa_overlay_row_leakage_is_none():
    """_overlay_row must NOT hardcode leakage='clean'.

    Before the fix: leakage = 'clean' is a hardcoded string with no detector
    behind it — violates §N.7-4 (a verification flag needs a real detector or
    must be null).  The fix sets leakage=None until a real detector exists.
    """
    import uuid
    from pipeline.orchestrator.writers.mi_adhilepa import _overlay_row

    mult = {
        'target_ref': 'fam_yoga',
        'applied_multiplier': 1.2,
        'raw_multiplier': 1.2,
        'kill_switch_state': 'active',
        'n_observations': 5,
    }
    row = _overlay_row(str(uuid.uuid4()), 'L2', 'bo_laksana', str(uuid.uuid4()), mult, 0)
    # leakage_status is index 9 in the tuple
    leakage_status = row[9]
    assert leakage_status is None, (
        f"mi_adhilepa._overlay_row leakage_status should be None (no real detector exists), "
        f"not {leakage_status!r}. Hardcoding 'clean' violates §N.7-4."
    )
