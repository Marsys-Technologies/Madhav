"""Reader policy for L1 rows by verification tier (honest-tier readers, A58).

WHY. A reader that pins `verification_pass_status = 'two_pass_verified'` treats
"verified" as the price of admission. When a base-layer rebuild relabels a
system's rows to the tier they honestly earn (`classical_match`, `single`, ...)
such a reader comes back EMPTY and the consumer silently reports the system as
inactive -- an omission that reads as a finding (CLAUDE.md §N.7 item 6, §N.8).

THE POLICY. Two named sets, both built from `brahmagyan/verification_vocab.py`
constants (never literals, CLAUDE.md §N.4):

  * `STRICT_TIERS`          -- `{two_pass_verified}`. For a reader whose contract
    names that tier (the '5.0' writer's §4.0 daśā read, AM-10, the vimshottari
    build pin). Unchanged behaviour.
  * `HONEST_COMPUTED_TIERS` -- every tier a writer emits for a value it actually
    computed: two_pass_verified, classical_match, single, single_pass,
    documented_approximation, computed_extension. A reader that only needs the
    computed value (a timing system that votes in a plurality) accepts these.

Everything else is REFUSED: floored (a null/zero stood in for the value),
divergent_flagged (two passes disagreed), pending_w3_verification, the
not-defined / sentinel / skipped / external-computation markers, NULL, and any
string outside the vocabulary. Acceptance is never promotion: the row keeps its
own tier and `tier_evidence` states it (and whether it is *verified*) so a
consumer can never read an accepted-but-unverified row as verified.
"""
from __future__ import annotations

from typing import Any, Final, Iterable

from brahmagyan.verification_vocab import (
    CLASSICAL_MATCH,
    COMPUTED_EXTENSION,
    DOCUMENTED_APPROXIMATION,
    SINGLE,
    SINGLE_PASS,
    TWO_PASS_VERIFIED,
    is_verified,
)

STRICT_TIERS: Final[frozenset[str]] = frozenset({TWO_PASS_VERIFIED})

HONEST_COMPUTED_TIERS: Final[frozenset[str]] = frozenset({
    TWO_PASS_VERIFIED, CLASSICAL_MATCH, SINGLE, SINGLE_PASS,
    DOCUMENTED_APPROXIMATION, COMPUTED_EXTENSION,
})


def tier_accepted(status: Any, accepted: Iterable[str] = HONEST_COMPUTED_TIERS) -> bool:
    """True iff `status` is exactly one of the `accepted` tiers. Case-sensitive,
    NULL / non-string / unknown spellings are refused (never case-folded)."""
    return isinstance(status, str) and status in frozenset(accepted)


def tier_evidence(status: Any) -> dict:
    """The tier an accepted row carries to its consumer: the row's own status,
    and whether it is a *verified* one (only `two_pass_verified` is)."""
    return {"verification_pass_status": status, "tier_verified": is_verified(status)}


def sql_params(accepted: Iterable[str]) -> list[str]:
    """Deterministic (sorted) parameter list for a `= ANY(%s)` predicate."""
    return sorted(frozenset(accepted))


__all__ = ["STRICT_TIERS", "HONEST_COMPUTED_TIERS", "tier_accepted",
           "tier_evidence", "sql_params"]
