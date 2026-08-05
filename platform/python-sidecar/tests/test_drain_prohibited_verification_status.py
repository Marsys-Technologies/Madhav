"""
test_drain_prohibited_verification_status.py — Guard 1 halt-vs-note fix.

`platform/scripts/backfill/drain_prohibited_verification_status.py` Guard 1 walks every
CHECK constraint on `verification_pass_status` (found live via `pg_constraint`) and used
to HALT whenever the CHECK's text did not permit the drain's target value (`'single'`).
That self-halted (safely — no writes) the first time a third CHECK-constrained table
appeared, `kala_tithi_pravesha`, whose CHECK permits only
`two_pass_verified`/`divergent_flagged` — it doesn't permit any of the three retired
source spellings (`'PASS'`, `'pass'`, `'single_pass'`) either, so there was never a row
that table could hold for this drain to touch.

M22_NIGHT_LEDGER.md Gate R1 (Opus review): "the guard-fix is structurally sound (halt
condition should be 'CHECK permits a SOURCE value while rejecting target,' not 'target
not permitted' — kala_tithi_pravesha's CHECK permits none of {PASS,pass,single_pass} so
the correct guard would emit NOTE not HALT there)".

This module tests `guard1_verdict(tbl, defn)` directly against fabricated CHECK
constraint-definition strings — no DB, no live `pg_constraint` query — covering:

  1. The two known-good, already-CHECK-constrained tables (`chart_dashas`,
     `chart_divisionals`): CHECK already permits the target -> clean pass, no HALT, no
     "permits none of the source values" NOTE.
  2. The `kala_tithi_pravesha` shape: CHECK permits neither the target nor any source
     value -> NOTE, not HALT.
  3. The genuinely hazardous shape: CHECK permits a source value but rejects the target
     -> HALT (this is the case the old "target not permitted" logic was, by coincidence,
     also right about — must stay right after the fix).
"""
from __future__ import annotations

import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
_BACKFILL_DIR = _REPO / "platform" / "scripts" / "backfill"
sys.path.insert(0, str(_BACKFILL_DIR))

from drain_prohibited_verification_status import (  # noqa: E402
    RESTRICTED_TABLES,
    SOURCE_VALUES,
    UNVERIFIED_DEFAULT,
    guard1_verdict,
)


def _check_defn(*statuses: str) -> str:
    """Fabricate a `pg_get_constraintdef()`-shaped CHECK string permitting exactly
    `statuses`, matching the real shape postgres emits for an ARRAY membership CHECK."""
    members = ", ".join(f"'{s}'::text" for s in statuses)
    return f"CHECK ((verification_pass_status = ANY (ARRAY[{members}])))"


def test_source_values_and_target_are_the_expected_settled_vocabulary():
    """Sanity-check the fixture assumptions this whole test file rests on."""
    assert set(SOURCE_VALUES) == {"PASS", "pass", "single_pass"}
    assert UNVERIFIED_DEFAULT == "single"


# ── 1. known-good restricted tables: CHECK already permits the target ──────────────


def test_chart_dashas_and_chart_divisionals_pass_cleanly():
    """Real shape (migrations 206/210): permits two_pass_verified, classical_match,
    divergent_flagged, single — none of the three retired source spellings, but the
    target IS permitted, so this must never HALT and must never emit the
    "permits none of the source values" NOTE (which is reserved for tables that also
    reject the target)."""
    defn = _check_defn("two_pass_verified", "classical_match", "divergent_flagged", "single")
    for tbl in ("chart_dashas", "chart_divisionals"):
        assert tbl in RESTRICTED_TABLES  # fixture assumption
        halt, messages = guard1_verdict(tbl, defn)
        assert halt is False
        assert not any(m.startswith("HALT") for m in messages)
        assert not any("permits none of the source values" in m for m in messages)
        # Listed in RESTRICTED_TABLES -> no "unlisted CHECK" NOTE either. Clean pass.
        assert messages == []


# ── 2. the kala_tithi_pravesha fix: CHECK permits neither target nor any source ────


def test_kala_tithi_pravesha_shape_is_a_note_not_a_halt():
    """The exact real-world case that used to self-halt the script. CHECK permits only
    two_pass_verified/divergent_flagged — none of {PASS, pass, single_pass} are legal
    there, and neither is the drain's target ('single'). Nothing this drain would ever
    write could have been legally stored there, so it must be a NOTE, never a HALT."""
    defn = _check_defn("two_pass_verified", "divergent_flagged")
    halt, messages = guard1_verdict("kala_tithi_pravesha", defn)
    assert halt is False
    assert not any(m.startswith("HALT") for m in messages)
    assert any("permits none of the source values" in m for m in messages)
    # Not in RESTRICTED_TABLES -> also gets the pre-existing "unlisted CHECK" NOTE.
    assert "kala_tithi_pravesha" not in RESTRICTED_TABLES
    assert any("carries a CHECK the vocabulary module does not list" in m for m in messages)


# ── 3. the genuinely hazardous shape: must still HALT ───────────────────────────────


def test_check_permitting_a_source_value_but_rejecting_target_still_halts():
    """A table whose CHECK would let a source-spelling row exist but rejects the target
    is exactly the CheckViolation hazard Guard 1 exists to catch. Must HALT."""
    defn = _check_defn("PASS", "two_pass_verified")
    halt, messages = guard1_verdict("some_hypothetical_table", defn)
    assert halt is True
    assert len(messages) == 1
    assert messages[0].startswith("HALT")
    assert "PASS" in messages[0]


def test_check_permitting_multiple_source_values_but_rejecting_target_halts_and_lists_all():
    defn = _check_defn("PASS", "pass", "divergent_flagged")
    halt, messages = guard1_verdict("another_hypothetical_table", defn)
    assert halt is True
    assert "PASS" in messages[0]
    assert "pass" in messages[0]
    assert "single_pass" not in messages[0]  # not permitted by this fixture CHECK


def test_check_permitting_single_pass_but_rejecting_target_halts():
    """single_pass is LEGAL (deprecated_alias_of='single') but still a SOURCE value for
    this drain — a CHECK permitting it while rejecting 'single' is still a hazard."""
    defn = _check_defn("single_pass", "two_pass_verified")
    halt, messages = guard1_verdict("yet_another_table", defn)
    assert halt is True
    assert "single_pass" in messages[0]
