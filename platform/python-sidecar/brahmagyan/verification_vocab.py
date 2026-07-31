"""
brahmagyan.verification_vocab — THE settled `verification_pass_status` vocabulary.

SINGLE SOURCE OF TRUTH (build side). The serve side declares the identical table in
`platform/src/lib/retrieval/envelope.ts` (which must stay zero-import — see
`platform-mcp/scripts/generate_envelope.ts`), and `tests/test_verification_vocab.py`
asserts the two agree member-for-member and verified-flag-for-verified-flag. Change
one, that test fails until you change the other.

WHY IT LIVES IN L0 (brahmagyan) rather than beside the writers that emit the field:
this vocabulary is a cross-layer contract — `ga_*` (L1), `bo_*` (L2) and the build
gate all speak it. Putting it under `ga_writers/` would have made every L2 writer
import an L1 package. L0 Brahmagyan is the foundation layer every other layer may
depend on (`bo_yantra_mechanism` / `bo_karanajala` already import
`brahmagyan.valence_doctrine`), so the dependency runs the right way.

WHY THIS FILE EXISTS (SAMĀPTI · B-VERIFSTATUS-VOCAB · DVA Ruling 13, findings F-11/F-25/F-38)
--------------------------------------------------------------------------------------
Before this module the field had SIX disagreeing definitions in one instrument:

  1. Writers emitted 14 distinct literals across the sidecar, with no shared declaration.
  2. `chart_dashas` / `chart_divisionals` carry a CHECK constraint allowing exactly
     four of them; `chart_facts` and every `bodha_*` table carry NO constraint at all.
  3. `ga_writers/gates.py` G7 hardcoded its own four-value set (which 5,428 live
     `chart_facts` rows already violated — the gate was not being run on those builds).
  4. `platform/src/lib/ganita/types.ts` declared a hand-written four-value TS union —
     a FALSE one: `chart_facts` legitimately stores ten distinct values, so the type
     described a row shape the database has never had.
  5. `tests/test_verification_pass_status_vocab.py` hardcoded its own copy of the
     restricted-table set.
  6. The serve layer counted a row as "verified" if its status was
     `two_pass_verified` OR `pass` (lowercase), while `register_p1_ganita.ts` told the
     caller, in the same response, that the number meant `two_pass_verified` only.

A seventh copy — `platform/scripts/governance/drift_detector.py`'s `VALID_STATUS` —
is deliberately NOT folded in here: it is CI-gate surface owned by another lane. It
currently raises a HARD violation (exit 3) for 56,028 live rows, of which only the
5,428 `PASS` rows are the real defect. Routed as a residual, not fixed in this lane.

THE ONE RULE THIS TABLE ENCODES (CLAUDE.md §N.8, Earned-Signal Principle)
-------------------------------------------------------------------------
A status is `verified: True` only if a detector ran that could have produced a
DIFFERENT answer. `two_pass_verified` is the only member that means that today.
Everything else is an honest description of a value that was computed once, floored,
approximated, deferred, or is structurally undefined — all of which are legitimate
states to store and serve, and none of which may be counted as grounding.

`pass` / `PASS` ARE PROHIBITED, not merely deprecated. A bare "PASS" asserts that some
pass succeeded without naming which pass, so no reader can tell whether a detector ran.
All 12 emission sites of these two spellings (11 × `pass` in bo_* writers, 1 × `PASS`
in `ga_nakshatra.py`) were audited under Ruling 13 and every one was an unconditional
dict literal with zero verification logic behind it. They are banned by
`assert_legal()` so the class cannot come back.
"""
from __future__ import annotations

from typing import Any, Final, NamedTuple


class VocabEntry(NamedTuple):
    """One member of the settled vocabulary."""

    status: str
    verified: bool
    meaning: str
    #: When set, this status is a spelling variant kept only so stored rows stay
    #: readable. New writer code must use the target instead.
    deprecated_alias_of: str | None = None


#: The settled vocabulary. Ordered most-to-least epistemically load-bearing.
VERIFICATION_PASS_STATUS_VOCAB: Final[tuple[VocabEntry, ...]] = (
    VocabEntry(
        "two_pass_verified",
        True,
        "The value was confirmed by a second, independently-implemented derivation "
        "that could have disagreed. The ONLY status that counts as grounding.",
    ),
    VocabEntry(
        "classical_match",
        False,
        "The value was matched against a canonical classical reference table. A real "
        "check, but a relay-fidelity check rather than an independent re-derivation — "
        "held out of the verified set pending a per-site earnedness audit "
        "(SAMĀPTI residual R-VOCAB-1).",
    ),
    VocabEntry(
        "divergent_flagged",
        False,
        "Two passes ran and DISAGREED. Explicitly not verified — the row is stored so "
        "the divergence is auditable (B.10: never silently drop data).",
    ),
    VocabEntry(
        "single",
        False,
        "Single-pass computation. No second derivation ran, so nothing could have "
        "contradicted the value. This is the expressible form of 'no verification "
        "ran' on the many NOT NULL columns that cannot hold a literal NULL.",
    ),
    VocabEntry(
        "single_pass",
        False,
        "Spelling variant of 'single' used by some chart_facts writers.",
        deprecated_alias_of="single",
    ),
    VocabEntry(
        "documented_approximation",
        False,
        "A documented approximation rather than an exact derivation; the "
        "approximation is named in the row's citation.",
    ),
    VocabEntry(
        "computed_extension",
        False,
        "Derived by extension from some other value. The base may be verified; this "
        "extension is not independently checked.",
    ),
    VocabEntry(
        "floored",
        False,
        "Honest floor — the canonical source was unreachable so the writer emitted a "
        "null/zero rather than fabricate "
        "(CLAUDE.md §N.4, floors-aspirational-not-gates).",
    ),
    VocabEntry(
        "not_defined_for_nodes",
        False,
        "The underlying classical formula is structurally undefined for this subject "
        "(Rahu/Ketu have no BPHS ṣaḍbala terms). Not a failure — an N/A.",
    ),
    VocabEntry(
        "scope_cap_sentinel",
        False,
        "Sentinel row marking where a declared scope cap truncated the emission. "
        "Carries no computed value to verify.",
    ),
    VocabEntry(
        "skipped_malformed_source",
        False,
        "The source row was malformed and was skipped; the row records the skip.",
    ),
    VocabEntry(
        "external_computation_required",
        False,
        "CLAUDE.md §B.10 marker — the value needs a specialist ephemeris/tool and was "
        "deliberately not invented.",
    ),
    VocabEntry(
        "pending_w3_verification",
        False,
        "Verification deliberately deferred to a later wave; the row is served with "
        "its status visible so no caller mistakes it for checked.",
    ),
)

_BY_STATUS: Final[dict[str, VocabEntry]] = {e.status: e for e in VERIFICATION_PASS_STATUS_VOCAB}

#: Every legal status.
ALL_STATUSES: Final[frozenset[str]] = frozenset(_BY_STATUS)

#: The statuses a serve layer may count as grounding. Exactly one member — see §N.8.
VERIFIED_STATUSES: Final[frozenset[str]] = frozenset(
    e.status for e in VERIFICATION_PASS_STATUS_VOCAB if e.verified
)

#: Banned outright. See the module docstring — these name no pass.
PROHIBITED_STATUSES: Final[frozenset[str]] = frozenset({"pass", "PASS"})

#: The status to write when no detector ran. `single` rather than NULL because
#: `chart_facts.verification_pass_status` and most `bodha_*` equivalents are NOT NULL.
UNVERIFIED_DEFAULT: Final[str] = "single"

#: The narrower CHECK-constraint vocabulary enforced by the live database on
#: `chart_dashas` and `chart_divisionals` ONLY (migrations 206 / 210; verified against
#: pg_constraint 2026-07-30). `chart_facts` and every `bodha_*` table have no CHECK.
#: A writer targeting either of those two tables must stay inside this subset.
RESTRICTED_TABLE_VOCAB: Final[frozenset[str]] = frozenset(
    {"two_pass_verified", "classical_match", "divergent_flagged", "single"}
)

#: Tables whose CHECK constraint restricts them to RESTRICTED_TABLE_VOCAB.
RESTRICTED_TABLES: Final[frozenset[str]] = frozenset({"chart_dashas", "chart_divisionals"})


def is_verified(status: Any) -> bool:
    """True only for a status backed by a detector that could have said otherwise.

    Case-SENSITIVE on purpose. A caller passing 'PASS' or 'Two_Pass_Verified' has a bug
    in its writer, and silently case-folding it here is how 5,428 unverified rows
    nearly became grounded (Ruling 13). Returns False for anything unrecognized.
    """
    return status in VERIFIED_STATUSES


def entry_for(status: str) -> VocabEntry | None:
    """The vocabulary entry for `status`, or None if it is not a member."""
    return _BY_STATUS.get(status)


def canonical(status: str) -> str:
    """Resolve a deprecated spelling to its canonical target; identity otherwise."""
    e = _BY_STATUS.get(status)
    return e.deprecated_alias_of if (e and e.deprecated_alias_of) else status


def assert_legal(status: Any, *, table: str | None = None) -> str:
    """Raise ValueError unless `status` is a legal member (and legal for `table`).

    Pass `table` to additionally enforce the DB CHECK constraint for the two
    restricted tables, catching a psycopg CheckViolation before the INSERT.
    """
    if status in PROHIBITED_STATUSES:
        raise ValueError(
            f"verification_pass_status={status!r} is PROHIBITED (CLAUDE.md §N.8, DVA "
            "Ruling 13): a bare pass/PASS asserts verification without naming the pass "
            "that ran. Emit 'two_pass_verified' only behind a real detector; otherwise "
            f"emit {UNVERIFIED_DEFAULT!r}."
        )
    if status not in ALL_STATUSES:
        raise ValueError(
            f"verification_pass_status={status!r} is not in the settled vocabulary "
            f"{sorted(ALL_STATUSES)}. Add it to brahmagyan/verification_vocab.py AND to "
            "the mirrored table in platform/src/lib/retrieval/envelope.ts (the parity "
            "test enforces both) before emitting it."
        )
    if table in RESTRICTED_TABLES and status not in RESTRICTED_TABLE_VOCAB:
        raise ValueError(
            f"verification_pass_status={status!r} violates {table}'s CHECK constraint "
            f"(allowed: {sorted(RESTRICTED_TABLE_VOCAB)}); the INSERT would raise "
            "psycopg.errors.CheckViolation."
        )
    return status
