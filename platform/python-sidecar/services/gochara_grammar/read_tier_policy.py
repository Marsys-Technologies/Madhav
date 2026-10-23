"""Reader policy for L1 rows by verification tier (honest-tier readers, A58).

WHY. A reader whose tier predicate is an equality on the two-pass-verified tier treats
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
    documented_approximation, computed_extension.
  * `LEVEL_TIER_POLICY`     -- which (system, level) reads accept the honest set;
    every other (system, level) stays STRICT, so a row set read today is read
    identically (behaviour-neutral) and only the relabelled level-1 rows return.

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
    ALL_STATUSES,
    CLASSICAL_MATCH,
    TWO_PASS_VERIFIED,
    UNVERIFIED_DEFAULT,
    is_verified,
)

# Vocabulary members that have no named constant in verification_vocab.py. They are NOT invented here:
# each is asserted at import to be a member of the settled vocabulary, so a rename or removal there fails
# loudly. (They are not added to verification_vocab.py itself because that module is in the provenance closure
# of the L0 bg_* writers — editing it re-pins the L0 convergence anchor, which a reader policy must not do.)
SINGLE = UNVERIFIED_DEFAULT            # "single"
SINGLE_PASS = "single_pass"            # deprecated spelling variant of `single` (chart_facts writers)
DOCUMENTED_APPROXIMATION = "documented_approximation"
COMPUTED_EXTENSION = "computed_extension"
assert {SINGLE, SINGLE_PASS, DOCUMENTED_APPROXIMATION, COMPUTED_EXTENSION} <= ALL_STATUSES

STRICT_TIERS: Final[frozenset[str]] = frozenset({TWO_PASS_VERIFIED})

HONEST_COMPUTED_TIERS: Final[frozenset[str]] = frozenset({
    TWO_PASS_VERIFIED, CLASSICAL_MATCH, SINGLE, SINGLE_PASS,
    DOCUMENTED_APPROXIMATION, COMPUTED_EXTENSION,
})


# PER-(system, level) policy. The default for every (system, level) is STRICT — exactly what the
# pinned read accepted before this policy existed — so a row set read today is read identically.
# Only the entries below are widened, and only for the rows a base-layer relabel moves OFF
# `two_pass_verified` while the system's reading contract is unchanged: the level-1 (MD) rows of
# the non-pinned systems whose level 1 is read today (mudda, narayana: today `two_pass_verified`,
# after the rebuild `classical_match`). Deeper levels of every system, every other system's level
# 1, and vimshottari at every level are NOT widened here: whether `single` deeper levels, or the
# `classical_match` / `single` level-1 rows the strict read already excludes today (yogini,
# ashtottari, chara_karaka, naisargika, kalachakra), SHOULD vote in the plurality is a separate
# question that changes today's permission values — a decision, not this policy (see the A58
# report). Widening is a one-line edit of this table.
LEVEL_TIER_POLICY: Final[dict[tuple[str, int], frozenset[str]]] = {
    ("mudda", 1): HONEST_COMPUTED_TIERS,
    ("narayana", 1): HONEST_COMPUTED_TIERS,
}


# SR-DASHA-SINGLE-TIER (surrogate ruling 2026-10-22, option (a) scoped). The L1 rebuild stores five systems at
# `single` at every level (nothing double-checked them). The governed reader admits `single` for THESE FIVE
# systems only, and only into a consumer that asks for it by name (`admit_single_tier`) AND carries
# `single_tier_input` onto every row it derives (CLAUDE.md §N.6: counted and flagged separately, never
# presented as verified). It is deliberately NOT a LEVEL_TIER_POLICY entry: that table feeds the vote /
# permission readers, which cannot carry the flag and so keep refusing `single`. vimshottari (the 5.0 P1
# operand) and every unlisted system (vimshottari_kp, narayana level 2, mudda levels 2-4) stay STRICT.
# Post-campaign item F-L1-DASHA-TWO-PASS: two-pass verify these five, then delete this set and the flag.
SINGLE_TIER_ADMITTED_SYSTEMS: Final[frozenset[str]] = frozenset({
    "ashtottari", "chara_karaka", "kalachakra", "naisargika", "yogini",
})
SINGLE_TIER_INPUT_FLAG: Final[str] = "single_tier_input"


def single_tier_admitted(system_id: Any, status: Any) -> bool:
    """True iff (system_id, status) is a `single` row of one of the five ruled systems."""
    return status == SINGLE and system_id in SINGLE_TIER_ADMITTED_SYSTEMS


def accepted_tiers_for(system_id: str, level_n: int) -> frozenset[str]:
    """The tiers a read of (system_id, level_n) accepts: the table entry, else STRICT."""
    return LEVEL_TIER_POLICY.get((system_id, int(level_n)), STRICT_TIERS)


def tier_accepted(status: Any, accepted: Iterable[str] = HONEST_COMPUTED_TIERS) -> bool:
    """True iff `status` is exactly one of the `accepted` tiers. Case-sensitive,
    NULL / non-string / unknown spellings are refused (never case-folded)."""
    return isinstance(status, str) and status in frozenset(accepted)


def row_tier_accepted(system_id: Any, level_n: Any, status: Any) -> bool:
    """The per-level policy applied to one row (a NULL level or system is STRICT)."""
    try:
        accepted = accepted_tiers_for(str(system_id), int(level_n))
    except (TypeError, ValueError):
        accepted = STRICT_TIERS
    return tier_accepted(status, accepted)


def tier_evidence(status: Any) -> dict:
    """The tier an accepted row carries to its consumer: the row's own status,
    and whether it is a *verified* one (only `two_pass_verified` is)."""
    return {"verification_pass_status": status, "tier_verified": is_verified(status)}


__all__ = ["STRICT_TIERS", "HONEST_COMPUTED_TIERS", "LEVEL_TIER_POLICY",
           "SINGLE_TIER_ADMITTED_SYSTEMS", "SINGLE_TIER_INPUT_FLAG", "single_tier_admitted",
           "accepted_tiers_for", "tier_accepted", "row_tier_accepted", "tier_evidence"]
