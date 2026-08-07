"""
tests/l3/test_ka_yojaka_domain_vocab.py — Regression guard for Fix 2:
ka_yojaka _infer_signal_domain triple dead-junction.

TDD: these tests were written BEFORE the fix.

The bug:
  _infer_signal_domain infers raw domain keywords from signal_type_id and returns
  strings like 'finance', 'spiritual', 'education'. But the three downstream lookups
  use dicts keyed by CANONICAL domains ('wealth', 'spirituality', 'education'):

    cdlm_domain_strength.get(domain, 0.5)   → bodha_cdlm_cells keys: canonical
    pratijna_by_domain.get(domain, [])       → bodha_pratijna → beo.domain: canonical
    domain_confirmation.get(domain, 0)       → same join: canonical

  So 'finance' never hits 'wealth', 'spiritual' never hits 'spirituality', etc.
  All three lookups fall through to their defaults:
    cdlm_domain_strength = 0.5
    pratijna_ids = []
    multi_system_confirmation_count = 0

The fix:
  Apply canonical_domain() from brahmagyan.domain_vocabulary to the raw inferred
  domain before doing any of the three lookups.

These tests verify canonical_domain() normalises the legacy terms correctly,
and that _infer_signal_domain returns the RIGHT canonical form after the fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SIDECAR = Path(__file__).parent.parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from brahmagyan.domain_vocabulary import canonical_domain, CANONICAL_DOMAINS  # noqa: E402
from pipeline.orchestrator.writers.ka_yojaka import _infer_signal_domain  # noqa: E402


# ── canonical_domain() resolves the legacy terms ka_yojaka uses ───────────────

def test_canonical_domain_finance_resolves_to_wealth():
    assert canonical_domain('finance') == 'wealth', (
        "'finance' is a known synonym for 'wealth' per DOMAIN_SYNONYMS"
    )


def test_canonical_domain_spiritual_resolves_to_spirituality():
    assert canonical_domain('spiritual') == 'spirituality', (
        "'spiritual' is a known synonym for 'spirituality'"
    )


def test_canonical_domain_education_is_already_canonical():
    assert canonical_domain('education') == 'education', (
        "'education' is already a canonical domain"
    )


def test_canonical_domain_health_is_already_canonical():
    assert canonical_domain('health') == 'health'


def test_canonical_domain_career_is_already_canonical():
    assert canonical_domain('career') == 'career'


def test_canonical_domain_relationship_is_already_canonical():
    assert canonical_domain('relationship') == 'relationship'


def test_canonical_domain_general_is_already_canonical():
    assert canonical_domain('general') == 'general'


# ── _infer_signal_domain must return canonical domains after the fix ───────────
#
# These tests pin the EXPECTED correct output after the fix is applied.
# Before the fix, _infer_signal_domain returns raw keyword matches like
# 'finance', 'spiritual' which are NOT in CANONICAL_DOMAINS.

_FINANCE_SIGNAL = {
    'signal_type_id': 'dhana_yoga:second_lord_in_eleventh',  # 'dhana' → 'finance' raw
}

_SPIRITUAL_SIGNAL = {
    'signal_type_id': 'dharma_trikon:ninth_lord_strength',   # 'dharma' → 'spiritual' raw
}

_EDUCATION_SIGNAL = {
    'signal_type_id': 'vidya_yoga:fifth_lord_mercury',       # 'vidya' → 'education' raw
}

_CAREER_SIGNAL = {
    'signal_type_id': 'raja_yoga:tenth_lord_exalted',        # 'raja' → 'career' raw
}

_HEALTH_SIGNAL = {
    'signal_type_id': 'ayur_yoga:eighth_lord_strength',      # 'ayur' → 'health' raw
}

_GENERAL_SIGNAL = {
    'signal_type_id': 'unknown_type',
}


def test_infer_signal_domain_finance_signal_returns_canonical():
    """A 'finance'-matching signal should resolve to canonical 'wealth'."""
    result = _infer_signal_domain(_FINANCE_SIGNAL)
    assert result in CANONICAL_DOMAINS, (
        f"_infer_signal_domain returned {result!r} which is not canonical. "
        f"Expected 'wealth' (canonical synonym for 'finance')."
    )
    assert result == 'wealth', (
        f"'dhana' keyword should resolve via 'finance' → canonical 'wealth'; got {result!r}"
    )


def test_infer_signal_domain_spiritual_signal_returns_canonical():
    """A 'spiritual'-matching signal should resolve to canonical 'spirituality'."""
    result = _infer_signal_domain(_SPIRITUAL_SIGNAL)
    assert result in CANONICAL_DOMAINS, (
        f"_infer_signal_domain returned {result!r} which is not canonical."
    )
    assert result == 'spirituality', (
        f"'dharma' keyword should resolve via 'spiritual' → canonical 'spirituality'; got {result!r}"
    )


def test_infer_signal_domain_education_signal_returns_canonical():
    """'vidya' keyword → 'education' which is already canonical."""
    result = _infer_signal_domain(_EDUCATION_SIGNAL)
    assert result in CANONICAL_DOMAINS, (
        f"_infer_signal_domain returned {result!r} which is not canonical."
    )
    assert result == 'education', f"Expected 'education'; got {result!r}"


def test_infer_signal_domain_career_signal_returns_canonical():
    result = _infer_signal_domain(_CAREER_SIGNAL)
    assert result in CANONICAL_DOMAINS, (
        f"_infer_signal_domain returned {result!r} which is not canonical."
    )
    assert result == 'career', f"Expected 'career'; got {result!r}"


def test_infer_signal_domain_health_signal_returns_canonical():
    result = _infer_signal_domain(_HEALTH_SIGNAL)
    assert result in CANONICAL_DOMAINS, (
        f"_infer_signal_domain returned {result!r} which is not canonical."
    )
    assert result == 'health', f"Expected 'health'; got {result!r}"


def test_infer_signal_domain_unknown_returns_general():
    result = _infer_signal_domain(_GENERAL_SIGNAL)
    assert result == 'general', (
        f"Unrecognized signal_type_id should return 'general'; got {result!r}"
    )


def test_infer_signal_domain_always_returns_canonical():
    """All outputs of _infer_signal_domain must be members of CANONICAL_DOMAINS."""
    signals = [
        _FINANCE_SIGNAL, _SPIRITUAL_SIGNAL, _EDUCATION_SIGNAL,
        _CAREER_SIGNAL, _HEALTH_SIGNAL, _GENERAL_SIGNAL,
    ]
    for sig in signals:
        result = _infer_signal_domain(sig)
        assert result in CANONICAL_DOMAINS, (
            f"_infer_signal_domain({sig!r}) → {result!r} is not canonical"
        )
