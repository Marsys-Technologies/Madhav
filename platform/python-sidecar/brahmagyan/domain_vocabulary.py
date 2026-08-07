"""
brahmagyan.domain_vocabulary — THE settled canonical domain vocabulary.

SINGLE SOURCE OF TRUTH (build side). The serve side declares the identical set in
``platform/src/lib/domain_vocabulary.ts`` (which must stay zero-import), and
``tests/test_domain_vocabulary.py`` asserts the two agree member-for-member.
Change one, that test fails until you change the other.

WHY IT LIVES IN L0 (brahmagyan) rather than beside any single writer: domain
vocabulary is a cross-layer contract — ``bo_*`` (L2), ``ka_*`` (L3), ``ph_*`` (L4)
and ``mi_*`` (L5) all speak it. Putting it in any one layer would have forced
every other layer to import that layer's package. L0 Brahmagyan is the
foundation layer every other layer may depend on (same rationale as
``brahmagyan.verification_vocab``).

WHY THIS FILE EXISTS (SHABDA-SHUDDHI campaign, R7, 2026-08-07)
--------------------------------------------------------------
Before this module the platform had NINE divergent domain vocabularies:

  1. bo_laksana.py: 6-element subset {career, wealth, health, relationship,
     spirituality, character} with fallback ["career", "character"].
  2. ka_yojaka.py: legacy keys 'finance', 'spiritual'.
  3. ka_bhavishya_lekha.py: pre-migration-386 vocabulary with 'finance', 'spiritual'.
  4. ph_phaladesa.py: 8-element label map (missing progeny/education/family/
     residence/travel).
  5. ph_nimitta/engine.py: correctly aligned but local to one service.
  6. synthesis/types.ts: 6 + 'other'.
  7. scope_classifier.ts: 11 with 'marriage', 'children', 'litigation', 'property'.
  8. spine/constants.ts: 7 + 'other'.
  9. priors_config.ts: 12 + 'moksha'.

Migration 386 (canonical_domain_normalization) established the canonical
13-domain vocabulary in the DB CHECK constraints but never provided a shared
module for code to import. This module fills that gap.
"""
from __future__ import annotations

from typing import Optional


# ── The canonical 13-domain vocabulary ────────────────────────────────────────
#
# Mirrors the CHECK constraint established by migration 386
# (canonical_domain_normalization) on phala_anchors, phala_phaladesa,
# kala_bhavishya, school_analysis_runs, convergence_scores.
#
# These are the ONLY values any writer may emit into a domain column that
# is constrained by one of those CHECKs, and the ONLY values any serving
# surface should present as domain labels.

CANONICAL_DOMAINS: frozenset[str] = frozenset({
    'career',
    'wealth',
    'relationship',
    'progeny',
    'health',
    'education',
    'family',
    'residence',
    'travel',
    'spirituality',
    'character',
    'transition',
    'general',
})

# Sorted tuple for deterministic iteration (tests, CI reports, TS mirror check).
CANONICAL_DOMAINS_SORTED: tuple[str, ...] = tuple(sorted(CANONICAL_DOMAINS))


# ── Synonym mapping: legacy / alternate terms → canonical ─────────────────────
#
# Every key is a known legacy or alternate term that has appeared in at least one
# writer, serving surface, or user-facing query. Every value is the canonical
# domain it maps to. A lookup miss means the input is either already canonical
# or genuinely unknown.
#
# Promoted from ph_nimitta/engine.py:85-98 (the one correctly-aligned site) and
# extended with terms found across the other eight divergent vocabularies.

DOMAIN_SYNONYMS: dict[str, str] = {
    # wealth
    'financial': 'wealth',
    'finance': 'wealth',
    'money': 'wealth',
    # spirituality
    'spiritual': 'spirituality',
    'dharma': 'spirituality',
    'moksha': 'spirituality',
    # character
    'psychological': 'character',
    'psychology': 'character',
    'mind': 'character',
    # relationship
    'marriage': 'relationship',
    'spouse': 'relationship',
    'relationships': 'relationship',
    # progeny
    'children': 'progeny',
    'progeny_children': 'progeny',
    'creativity': 'progeny',
    # education
    'intellect': 'education',
    # residence
    'property': 'residence',
    'residential': 'residence',
    # travel
    'foreign': 'travel',
    # family (no known synonyms beyond the canonical term)
    # transition (no known synonyms)
    # general (no known synonyms)
    # health (no known synonyms beyond the canonical term)
    # career (no known synonyms beyond the canonical term)
}

# litigation is NOT a synonym — it's a scope_classifier.ts-only concept with
# no canonical domain equivalent. Callers emitting 'litigation' should map it
# contextually (usually 'career' or 'general') or leave it for the fallback.


def canonical_domain(*candidates: Optional[str], fallback: str = 'general') -> str:
    """Return the first valid canonical domain from candidates; else *fallback*.

    Applies DOMAIN_SYNONYMS first so a legacy/alternate word (e.g. 'financial')
    resolves to its canonical value ('wealth') rather than falling through.

    Args:
        *candidates: Domain strings to try, in priority order. None/empty skipped.
        fallback: Value to return if no candidate resolves. Must itself be canonical.
                  Defaults to 'general'. Callers that want a different fallback
                  (e.g. 'transition' for ph_nimitta compatibility) pass it explicitly.

    Returns:
        A member of CANONICAL_DOMAINS, guaranteed.

    Raises:
        ValueError: if *fallback* is not in CANONICAL_DOMAINS.
    """
    if fallback not in CANONICAL_DOMAINS:
        raise ValueError(
            f"fallback {fallback!r} is not a canonical domain; "
            f"must be one of {CANONICAL_DOMAINS_SORTED}"
        )
    for c in candidates:
        if not c:
            continue
        cl = c.lower().strip()
        cl = DOMAIN_SYNONYMS.get(cl, cl)
        if cl in CANONICAL_DOMAINS:
            return cl
    return fallback


def is_canonical(domain: Optional[str]) -> bool:
    """Check whether a domain string is in the canonical vocabulary."""
    return domain is not None and domain in CANONICAL_DOMAINS


def assert_canonical(domain: str, *, context: str = '') -> str:
    """Assert that *domain* is canonical; raise ValueError if not.

    If *domain* is a known synonym, the error message includes the canonical
    equivalent to guide the fix.
    """
    if domain in CANONICAL_DOMAINS:
        return domain
    suggestion = DOMAIN_SYNONYMS.get(domain.lower().strip() if domain else '')
    ctx = f" ({context})" if context else ""
    if suggestion:
        raise ValueError(
            f"domain {domain!r}{ctx} is a legacy synonym — "
            f"use {suggestion!r} (canonical) instead"
        )
    raise ValueError(
        f"domain {domain!r}{ctx} is not in the canonical vocabulary "
        f"{CANONICAL_DOMAINS_SORTED}"
    )
