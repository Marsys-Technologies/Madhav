"""
Tests for brahmagyan.kala.l3_convergence — BRAHMA-KA-3-2 (kala.convergence).

SUDDHA-VACA P0-8 (D4_GRADE_INVERSION): CONVERGENCE_DOMAINS gives each named
convergence type a self-including tag (its own type name is a member of its
own domain set) EXCEPT health_attention, whose set
({"conflict", "separation", "transformation", "hardship"}) omits the literal
tag "health_attention" -- even though "health_attention" is used as a live
domain tag on real SIGNAL_ANCHORS entries (see l3_convergence.py, anchors
dated 2004-09-25 and 2020-01-24).

These tests construct a convergence-window input whose theme/domain tag set
is *exactly* the type's own name and assert `_classify_convergence_type`
recovers that type. The four other named types already pass this shape;
health_attention is expected to fail pre-fix.
"""
from __future__ import annotations

import pytest

from brahmagyan.kala.l3_convergence import _classify_convergence_type, CONVERGENCE_DOMAINS


# ── Symmetry check: every non-fallback type should classify correctly when
#    the ONLY tag present is its own name. ────────────────────────────────────

SELF_TAG_CASES = [
    ("career_peak", "career_peak"),
    ("relationship", "relationship"),
    ("health_attention", "health_attention"),
    ("spiritual_peak", "spiritual_peak"),
    ("wealth", "wealth"),
]


@pytest.mark.parametrize("expected_type, self_tag", SELF_TAG_CASES)
def test_self_tag_classifies_into_own_type(expected_type: str, self_tag: str) -> None:
    """A signal/window tagged with exactly its own convergence-type name as
    its only theme/domain must classify into that type, not fall through to
    'general'. This is the shape the other four types already satisfy; it is
    the failing case for health_attention pre-fix (D4_GRADE_INVERSION)."""
    result = _classify_convergence_type(themes=[self_tag], signal_domains=[self_tag])
    assert result == expected_type, (
        f"expected {expected_type!r} for self-tag {self_tag!r}, got {result!r} -- "
        f"CONVERGENCE_DOMAINS[{expected_type!r}] = {CONVERGENCE_DOMAINS[expected_type]!r}"
    )


def test_convergence_domains_self_inclusion_symmetry() -> None:
    """Every named (non-'general') convergence type's own name should be a
    member of its own domain set -- the four other types already do this;
    health_attention is the documented asymmetry (P0-8)."""
    named_types = {k: v for k, v in CONVERGENCE_DOMAINS.items() if k != "general"}
    missing_self_inclusion = [
        ctype for ctype, domain_set in named_types.items() if ctype not in domain_set
    ]
    assert missing_self_inclusion == [], (
        f"types missing self-inclusion in their own CONVERGENCE_DOMAINS set: "
        f"{missing_self_inclusion}"
    )
