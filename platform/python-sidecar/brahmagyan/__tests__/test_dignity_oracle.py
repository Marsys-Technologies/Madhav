"""Tests for brahmagyan.dignity_oracle — B-01 Dignity Oracle.

Six goldens per lane spec, plus boundary cases.
All tests must pass with NO live DB (pure-logic, data-driven from
_DIGNITY_REFERENCE — the authoritative static reference in bg_dignity_reference.py).
"""
from __future__ import annotations

import pytest

from brahmagyan.dignity_oracle import classify_dignity


# ── §1 Lane spec goldens (must all pass) ─────────────────────────────────────

def test_jupiter_sagittarius_in_mt_range():
    """Jupiter 0°-10° Sag is moolatrikona, not own."""
    assert classify_dignity("Jupiter", "Sagittarius", 9.79) == "moolatrikona"


def test_jupiter_sagittarius_outside_mt_range():
    """Jupiter at 15° Sag is outside MT range → own (own sign)."""
    assert classify_dignity("Jupiter", "Sagittarius", 15.0) == "own"


def test_rahu_taurus_exalted():
    """Rahu exalted in Taurus — no MT or own tier for nodes."""
    assert classify_dignity("Rahu", "Taurus", 5.0) == "exalted"


def test_ketu_sagittarius_neutral():
    """Ketu in Sagittarius — no MT or own tier for nodes → neutral."""
    assert classify_dignity("Ketu", "Sagittarius", 5.0) == "neutral"


def test_sun_leo_in_mt_range():
    """Sun MT in Leo 0°-20°; at 10° → moolatrikona."""
    assert classify_dignity("Sun", "Leo", 10.0) == "moolatrikona"


def test_sun_leo_outside_mt_range():
    """Sun own in Leo, but at 25° outside MT range (0°-20°) → own."""
    assert classify_dignity("Sun", "Leo", 25.0) == "own"


# ── §2 Additional boundary tests ─────────────────────────────────────────────

def test_sun_exalted_aries():
    assert classify_dignity("Sun", "Aries", 10.0) == "exalted"


def test_sun_debilitated_libra():
    assert classify_dignity("Sun", "Libra", 10.0) == "debilitated"


def test_moon_exalted_taurus():
    assert classify_dignity("Moon", "Taurus", 3.0) == "exalted"


def test_moon_own_cancer():
    """Moon own in Cancer — Cancer is not Moon's MT sign (Taurus is)."""
    assert classify_dignity("Moon", "Cancer", 15.0) == "own"


def test_moon_mt_taurus_within_range():
    """Moon's exaltation sign (Taurus) is also Moon's MT sign (Taurus 4°-30°).
    Exaltation is checked before MT, so in-range returns 'exalted', not 'moolatrikona'.
    This is the classical priority: exalted > moolatrikona when signs coincide."""
    # In Taurus at 10° (within 4°-30° MT range): exaltation wins
    assert classify_dignity("Moon", "Taurus", 10.0) == "exalted"


def test_moon_taurus_below_mt_boundary():
    """Moon in Taurus at 3° — below MT lower bound (4°) AND exalted → exalted."""
    assert classify_dignity("Moon", "Taurus", 3.0) == "exalted"


def test_mercury_mt_virgo():
    """Mercury's exaltation sign (Virgo) is also Mercury's MT sign (Virgo 16°-20°).
    Exaltation is checked before MT, so at 18° (in MT range) → 'exalted', not 'moolatrikona'.
    Classical priority: exalted > moolatrikona when signs coincide."""
    assert classify_dignity("Mercury", "Virgo", 18.0) == "exalted"


def test_mercury_virgo_outside_mt():
    """Mercury in Virgo at 25° — exaltation sign = Virgo, so → exalted (not own).
    Exaltation check fires first; own sign check is never reached for Virgo."""
    assert classify_dignity("Mercury", "Virgo", 25.0) == "exalted"


def test_mars_aries_in_mt_range():
    """Mars MT in Aries 0°-12°; at 5° → moolatrikona."""
    assert classify_dignity("Mars", "Aries", 5.0) == "moolatrikona"


def test_mars_aries_outside_mt_range():
    """Mars in Aries at 15° — outside MT range → own."""
    assert classify_dignity("Mars", "Aries", 15.0) == "own"


def test_jupiter_cancer_exalted():
    assert classify_dignity("Jupiter", "Cancer", 5.0) == "exalted"


def test_jupiter_capricorn_debilitated():
    assert classify_dignity("Jupiter", "Capricorn", 5.0) == "debilitated"


def test_jupiter_pisces_own():
    """Jupiter own in Pisces (not MT sign, which is Sagittarius)."""
    assert classify_dignity("Jupiter", "Pisces", 5.0) == "own"


def test_venus_mt_libra():
    """Venus MT in Libra 0°-15°; at 10° → moolatrikona."""
    assert classify_dignity("Venus", "Libra", 10.0) == "moolatrikona"


def test_venus_libra_outside_mt():
    """Venus in Libra at 20° — outside MT → own."""
    assert classify_dignity("Venus", "Libra", 20.0) == "own"


def test_saturn_mt_aquarius():
    """Saturn MT in Aquarius 0°-20°; at 10° → moolatrikona."""
    assert classify_dignity("Saturn", "Aquarius", 10.0) == "moolatrikona"


def test_saturn_aquarius_outside_mt():
    """Saturn in Aquarius at 25° → own."""
    assert classify_dignity("Saturn", "Aquarius", 25.0) == "own"


def test_neutral_planet():
    """Sun in Gemini — neither exalted, debilitated, own, nor MT → neutral."""
    assert classify_dignity("Sun", "Gemini", 15.0) == "neutral"


def test_ketu_debilitated_taurus():
    """Ketu debilitated in Taurus — node, so only exalted/debilitated/neutral."""
    assert classify_dignity("Ketu", "Taurus", 5.0) == "debilitated"


def test_rahu_debilitated_scorpio():
    assert classify_dignity("Rahu", "Scorpio", 5.0) == "debilitated"


def test_rahu_neutral():
    """Rahu in Gemini — neither exalted (Taurus) nor debilitated (Scorpio) → neutral."""
    assert classify_dignity("Rahu", "Gemini", 15.0) == "neutral"


def test_mt_boundary_exclusive_upper():
    """MT range is [from, to) — the upper bound is exclusive."""
    # Jupiter MT is 0°-10° in Sagittarius: degree=10.0 is NOT in range
    assert classify_dignity("Jupiter", "Sagittarius", 10.0) == "own"


def test_mt_boundary_inclusive_lower():
    """MT range lower bound is inclusive."""
    # Jupiter MT is 0°-10° in Sagittarius: degree=0.0 IS in range
    assert classify_dignity("Jupiter", "Sagittarius", 0.0) == "moolatrikona"


def test_unknown_graha_raises():
    """An unknown graha name raises KeyError."""
    with pytest.raises(KeyError):
        classify_dignity("Neptune", "Aries", 5.0)


# ── §2b PAR-R-2 — exact-boundary goldens for every graha with an MT range ────
#      (PRATINIDHI ruling PAR-R-2: half-open [from, to) confirmed as-built; the
#      ruling REQUIRES the boundary decision be visible as test evidence for
#      every MT-bearing graha, not just Jupiter — "a boundary decided but
#      untested is an undetected boundary", §N.8.)

def test_sun_mt_upper_boundary_is_own():
    """Sun MT is 0-20 Leo: 20°00' is own (upper bound exclusive)."""
    assert classify_dignity("Sun", "Leo", 20.0) == "own"


def test_sun_mt_lower_boundary_is_mt():
    assert classify_dignity("Sun", "Leo", 0.0) == "moolatrikona"


def test_moon_taurus_is_always_exalted_mt_currently_unreachable():
    """FLAGGED FINDING (not a PRATINIDHI-resolved boundary — see DIAGNOSIS.md):
    Moon's exaltation sign (Taurus) and MT sign (Taurus) are the SAME sign, and
    classify_dignity's exaltation check is sign-only (no degree gate), checked
    BEFORE moolatrikona in priority order. Consequence: for Moon, "moolatrikona"
    is currently unreachable at ANY degree in Taurus — exalted always wins.
    Asserting actual current behavior at what would otherwise be the MT range
    (4-30) rather than silently omitting Moon's boundary coverage or asserting
    an unverified guess about the classically-correct resolution."""
    assert classify_dignity("Moon", "Taurus", 4.0) == "exalted"
    assert classify_dignity("Moon", "Taurus", 29.999) == "exalted"
    assert classify_dignity("Moon", "Taurus", 3.999) == "exalted"


def test_mars_mt_upper_boundary_is_own():
    """Mars MT is 0-12 Aries: 12°00' is own."""
    assert classify_dignity("Mars", "Aries", 12.0) == "own"


def test_mercury_virgo_is_always_exalted_mt_currently_unreachable():
    """FLAGGED FINDING (same class as Moon/Taurus above): Mercury's exaltation
    sign (Virgo) and MT sign (Virgo) are also the same sign, and Virgo is
    additionally one of Mercury's own signs — a rare triple overlap. Exaltation
    (sign-only, no degree gate) wins over MT at every degree, making Mercury's
    16-20 Virgo MT range currently unreachable too."""
    assert classify_dignity("Mercury", "Virgo", 15.99) == "exalted"
    assert classify_dignity("Mercury", "Virgo", 16.0) == "exalted"
    assert classify_dignity("Mercury", "Virgo", 20.0) == "exalted"


def test_venus_mt_upper_boundary_is_own():
    """Venus MT is 0-15 Libra: 15°00' is own."""
    assert classify_dignity("Venus", "Libra", 15.0) == "own"


def test_saturn_mt_upper_boundary_is_own():
    """Saturn MT is 0-20 Aquarius: 20°00' is own."""
    assert classify_dignity("Saturn", "Aquarius", 20.0) == "own"


# ── §3 Recurrence guard — §N.7 item 3 (no wrapper-local constant may shadow ──
#      an L1-computed value, even when currently correct; a constant can
#      drift from its source, a reference cannot).
#
#      dignity_oracle._DATA is a deliberate static reproduction of
#      bg_dignity_reference._DIGNITY_REFERENCE (the module docstring explains
#      why it does not import the writer module directly — to avoid pulling
#      writer-layer deps into serving-layer code). That tradeoff is only safe
#      if the two are asserted equal in CI; this test is the recurrence guard
#      that makes the next silent divergence fail closed instead of drifting.

def test_data_matches_bg_dignity_reference_source_of_truth():
    """PAR-R-6 (LEDGER_PRATINIDHI.md, par/pratinidhi-ledger) re-point: the
    degree table now lives in ONE place, brahmagyan.l0_dignity_reference — both
    dignity_oracle._DATA and bg_dignity_reference._DIGNITY_REFERENCE derive
    from (and for the writer, ARE) the same import. This test now guards two
    things at once: (1) an identity check that the writer did not reintroduce
    a local copy instead of importing the shared module, and (2) that
    dignity_oracle's _DATA derivation transform stays faithful to the shared
    source's field names/values. Either regressing to a local copy or breaking
    the derivation must fail this test, not ship a silent divergence.
    """
    from brahmagyan.dignity_oracle import _DATA
    from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE
    from pipeline.orchestrator.writers.bg_dignity_reference import (
        _DIGNITY_REFERENCE,
    )

    # Identity, not just equality: bg_dignity_reference must be importing the
    # shared module's list object, not holding its own (even value-identical)
    # copy — a copy is exactly the §N.7 item 3 defect this extraction removed.
    assert _DIGNITY_REFERENCE is DIGNITY_REFERENCE, (
        "bg_dignity_reference._DIGNITY_REFERENCE is no longer the same object "
        "as brahmagyan.l0_dignity_reference.DIGNITY_REFERENCE — someone "
        "reintroduced a local copy in the writer."
    )

    ref_by_graha = {row["graha"]: row for row in DIGNITY_REFERENCE}

    assert set(_DATA.keys()) == set(ref_by_graha.keys()), (
        "dignity_oracle._DATA graha set has diverged from "
        "l0_dignity_reference.DIGNITY_REFERENCE"
    )

    for graha, ref_row in ref_by_graha.items():
        local = _DATA[graha]
        assert local["exaltation"] == ref_row["exaltation_sign"], graha
        assert local["debilitation"] == ref_row["debilitation_sign"], graha
        assert local["mt_sign"] == ref_row["moolatrikona_sign"], graha
        assert local["mt_from"] == ref_row["moolatrikona_from"], graha
        assert local["mt_to"] == ref_row["moolatrikona_to"], graha
        assert set(local["own"]) == set(ref_row["own_signs"]), graha


def test_l0_dignity_reference_matches_seeded_migration_250():
    """The one seam extraction does NOT close (PAR-R-6): Python vs. the
    literal SQL rows migration 250 seeds into the live `bg_dignity_reference`
    DB table. No live DB in this test environment, so this parses the
    migration's own static VALUES block (regex, not a SQL engine — the block
    is hand-authored and stable) and compares it field-by-field against
    l0_dignity_reference.DIGNITY_REFERENCE. §N.5/§N.8: a derivation
    disagreeing with the fact it cites is halt-worthy, not silently
    reconciled — this test is that real detector for the Python<->seed seam.
    """
    import re
    from pathlib import Path

    from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE

    migration_path = (
        Path(__file__).resolve().parents[3] / "migrations" / "250_bg_dignity_reference.sql"
    )
    assert migration_path.exists(), f"migration not found at {migration_path}"
    sql = migration_path.read_text()

    # Isolate the bg_dignity_reference INSERT ... VALUES ( ... ) block only
    # (stops at the ON CONFLICT (graha) clause that closes it).
    m = re.search(
        r"INSERT INTO bg_dignity_reference.*?VALUES\s*(.*?)\nON CONFLICT \(graha\)",
        sql,
        re.DOTALL,
    )
    assert m, "could not locate bg_dignity_reference INSERT...VALUES block in migration 250"
    values_block = m.group(1)

    # One capture group per graha row: 9 fields between the outer parens.
    row_re = re.compile(
        r"\(\s*'(?P<graha>\w+)',\s*"
        r"(?P<exalt_sign>'[^']*'|NULL),\s*(?P<exalt_deg>[\d.]+|NULL),\s*"
        r"(?P<debil_sign>'[^']*'|NULL),\s*(?P<debil_deg>[\d.]+|NULL),\s*"
        r"(?P<mt_sign>'[^']*'|NULL),\s*(?P<mt_from>[\d.]+|NULL),\s*(?P<mt_to>[\d.]+|NULL),\s*"
        r"(?P<own>ARRAY\[[^\]]*\](?:::TEXT\[\])?),",
        re.DOTALL,
    )

    def _sql_str(tok: str) -> str | None:
        return None if tok == "NULL" else tok.strip("'")

    def _sql_num(tok: str) -> float | None:
        return None if tok == "NULL" else float(tok)

    def _sql_array(tok: str) -> list[str]:
        inner = re.search(r"ARRAY\[(.*?)\]", tok, re.DOTALL).group(1)
        return [s.strip("'") for s in inner.split(",") if s.strip()]

    seeded_by_graha = {}
    for row_match in row_re.finditer(values_block):
        g = row_match.group("graha")
        seeded_by_graha[g] = {
            "exaltation_sign": _sql_str(row_match.group("exalt_sign")),
            "exaltation_degree": _sql_num(row_match.group("exalt_deg")),
            "debilitation_sign": _sql_str(row_match.group("debil_sign")),
            "debilitation_degree": _sql_num(row_match.group("debil_deg")),
            "moolatrikona_sign": _sql_str(row_match.group("mt_sign")),
            "moolatrikona_from": _sql_num(row_match.group("mt_from")),
            "moolatrikona_to": _sql_num(row_match.group("mt_to")),
            "own_signs": _sql_array(row_match.group("own")),
        }

    assert len(seeded_by_graha) == 9, (
        f"expected 9 grahas parsed from migration 250, got "
        f"{len(seeded_by_graha)}: {sorted(seeded_by_graha)} — regex may need "
        f"updating if the migration's formatting changed"
    )

    py_by_graha = {row["graha"]: row for row in DIGNITY_REFERENCE}
    assert set(seeded_by_graha.keys()) == set(py_by_graha.keys())

    for graha, seeded in seeded_by_graha.items():
        py = py_by_graha[graha]
        assert seeded["exaltation_sign"] == py["exaltation_sign"], graha
        assert seeded["debilitation_sign"] == py["debilitation_sign"], graha
        assert seeded["moolatrikona_sign"] == py["moolatrikona_sign"], graha
        assert set(seeded["own_signs"]) == set(py["own_signs"]), graha
        # Degrees: SQL NUMERIC parses as float; Python ints compare equal to
        # float via ==, so a direct comparison (with NULL/None on both sides
        # for Rahu/Ketu) is exact, not approximate.
        assert seeded["exaltation_degree"] == (
            None if py["exaltation_degree"] is None else float(py["exaltation_degree"])
        ), graha
        assert seeded["debilitation_degree"] == (
            None if py["debilitation_degree"] is None else float(py["debilitation_degree"])
        ), graha
        assert seeded["moolatrikona_from"] == (
            None if py["moolatrikona_from"] is None else float(py["moolatrikona_from"])
        ), graha
        assert seeded["moolatrikona_to"] == (
            None if py["moolatrikona_to"] is None else float(py["moolatrikona_to"])
        ), graha
