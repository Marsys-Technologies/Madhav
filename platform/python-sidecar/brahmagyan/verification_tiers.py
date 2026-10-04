"""
brahmagyan.verification_tiers -- named constants for EVERY settled `verification_pass_status`
member, plus `emit_tier()`. Q-L1-16(a) (SS ruling N-62), CLAUDE.md §N.4.

WHAT THIS IS. `brahmagyan.verification_vocab` stays THE single source of truth for the
vocabulary (members, `verified` flags, the alias table). This module is the WRITER-FACING
symbol layer over it: one importable constant per member, so a writer never has to spell a
tier as a bare string literal (a drifted literal is invisible to the type system; a drifted
constant is an ImportError). Every constant is DERIVED from the vocabulary at import time
(`_member()`), never a second hardcoded copy: rename or remove a member in
`verification_vocab` and this module fails to import, loudly.

    from brahmagyan.verification_tiers import SINGLE, FLOORED, CLASSICAL_MATCH, emit_tier

`TWO_PASS_VERIFIED` / `DIVERGENT_FLAGGED` / `CLASSICAL_MATCH` / `UNVERIFIED_DEFAULT` are
re-exported from `verification_vocab` (where they already live); a writer may import them
from either module. `two_pass_verified` is still PRODUCED only by
`verification_vocab.two_pass_verdict()` (M-22 / §N.8) -- exporting the constant here is for
comparisons and rank tables, not for asserting the tier.

WHY A SEPARATE MODULE (and not more constants inside verification_vocab.py).
The first attempt added these constants to `verification_vocab.py` itself (the original
ruling text). Measured consequence: that file sits in the local-import closure
(`asset_runner.get_writer_source_hash`) of 30 writers, so editing it moved 30 writer
digests -- including ONE L0 writer (`bg_kp_sublord_division`, whose L0 receipt spine is
pinned to 29 already-frozen capsules and went `NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE =
false`), 15 L2 writers (including the FROZEN `bo_laksana`) and 4 L3 writers. The ruling's
own estimate was "about 24 L1 and L2 writers". Leaving `verification_vocab.py`
byte-identical and adding this sibling moves ONLY the digests of the writers that adopt it
plus their importers -- measured at 7: ga_panchanga, ga_strength, ga_structural (adopters);
ga_ayurdaya, ga_sensitive_degree, ga_yoga (importers of ga_strength / ga_structural); and ONE
L3 writer, `ka_vighnakara`, which imports `ga_sensitive_degree_writer` -> `ga_structural_writer`.
So "no L0/L2/L3 digest moves" is NOT claimed: no L0 and no L2 writer moves, but
`ka_vighnakara` (L3) does -- any edit to `ga_structural_writer` moves it, with or without
this module. Every other digest, L0/L2 included, is unchanged.

SINGLE vs SINGLE_PASS. `SINGLE` ("single") is the canonical spelling of "no second
derivation ran". `SINGLE_PASS` ("single_pass") is its DEPRECATED alias: the live
`chart_facts` CHECK (migration 539) still allows both, `verification_vocab.canonical()` and
`bodha_writers.formulas` resolve the alias, so READERS keep accepting it; WRITERS must
emit `SINGLE` (`emit_tier()` rejects the alias; `tests/test_verification_tier_literal_guard.py`
fails on any new emission).
"""
from __future__ import annotations

from typing import Final

from brahmagyan.verification_vocab import (
    CLASSICAL_MATCH,
    DIVERGENT_FLAGGED,
    TWO_PASS_VERIFIED,
    UNVERIFIED_DEFAULT,
    assert_legal,
    canonical,
    entry_for,
)

__all__ = [
    "TWO_PASS_VERIFIED", "CLASSICAL_MATCH", "DIVERGENT_FLAGGED", "UNVERIFIED_DEFAULT",
    "SINGLE", "SINGLE_PASS", "DOCUMENTED_APPROXIMATION", "COMPUTED_EXTENSION", "FLOORED",
    "NOT_DEFINED_FOR_NODES", "SCOPE_CAP_SENTINEL", "SKIPPED_MALFORMED_SOURCE",
    "EXTERNAL_COMPUTATION_REQUIRED", "PENDING_W3_VERIFICATION",
    "DEPRECATED_ALIAS_STATUSES", "emit_tier",
]


def _member(status: str) -> str:
    """The vocabulary's own spelling of `status`; ImportError-grade failure if absent."""
    entry = entry_for(status)
    if entry is None:  # pragma: no cover - only fires if the vocabulary drops a member
        raise ImportError(
            f"brahmagyan.verification_vocab no longer has a {status!r} member; "
            "brahmagyan.verification_tiers must be updated with it (Q-L1-16(a))."
        )
    return entry.status


#: Canonical "no second derivation ran" (== UNVERIFIED_DEFAULT).
SINGLE: Final[str] = _member("single")
#: DEPRECATED alias of SINGLE -- readers only. Writers must never emit this.
SINGLE_PASS: Final[str] = _member("single_pass")
DOCUMENTED_APPROXIMATION: Final[str] = _member("documented_approximation")
COMPUTED_EXTENSION: Final[str] = _member("computed_extension")
FLOORED: Final[str] = _member("floored")
NOT_DEFINED_FOR_NODES: Final[str] = _member("not_defined_for_nodes")
SCOPE_CAP_SENTINEL: Final[str] = _member("scope_cap_sentinel")
SKIPPED_MALFORMED_SOURCE: Final[str] = _member("skipped_malformed_source")
EXTERNAL_COMPUTATION_REQUIRED: Final[str] = _member("external_computation_required")
PENDING_W3_VERIFICATION: Final[str] = _member("pending_w3_verification")

#: Spelling variants kept ONLY so stored rows stay readable (today: `single_pass`).
DEPRECATED_ALIAS_STATUSES: Final[frozenset[str]] = frozenset({SINGLE_PASS})

assert SINGLE == UNVERIFIED_DEFAULT, "UNVERIFIED_DEFAULT must be the canonical SINGLE"
assert canonical(SINGLE_PASS) == SINGLE, "single_pass must remain a declared alias of single"


def emit_tier(status: str, *, table: str | None = None) -> str:
    """Validate a tier a WRITER is about to store, and return it unchanged.

    `verification_vocab.assert_legal()` plus one rule: a deprecated spelling alias
    (`single_pass`) is legal to READ but not to EMIT -- a writer that reaches for it gets a
    ValueError naming the canonical spelling. It does NOT decide whether `two_pass_verified`
    is earned: that verdict still comes only from `two_pass_verdict()`; this helper is a
    spelling/legality gate, not a detector.
    """
    assert_legal(status, table=table)
    resolved = canonical(status)
    if resolved != status:
        raise ValueError(
            f"verification_pass_status={status!r} is a DEPRECATED alias of {resolved!r}: "
            f"readers still accept it, writers must emit {resolved!r} "
            "(Q-L1-16(a); brahmagyan.verification_tiers.SINGLE)."
        )
    return status
