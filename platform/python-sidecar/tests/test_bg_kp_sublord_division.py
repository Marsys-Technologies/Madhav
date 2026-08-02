"""
test_bg_kp_sublord_division — the L0 249-fold KP sub-lord division.

ṢAḌ-DARŚANA W3K Lane 1 · ADJUDICATION-7 Part 1 · Gate W3K's two-pass verification.

Three independent classes of check:

  1. GEOMETRY — the divisions tile [0°, 360°) exactly once, each lies wholly inside
     one nakṣatra and one rāśi, and the count 249 FALLS OUT of the arithmetic
     (243 + 6). The count is asserted here, never hard-coded in the builder, so a
     wrong derivation fails to reproduce the classical figure rather than assuming it.

  2. CROSS-IMPLEMENTATION (pass 2 of two) — the table's exact-rational lookup is
     compared against `compute_kp_lords`, the live float-accumulation subdivision
     that `emit_kp_lords` has used in production since PR #738, over a dense sweep
     of the whole circle. Two independently written derivations that could disagree.

  3. CLASSICAL FIXTURE (tier iii, committed) — the nine natal KP lords recorded in
     `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` §2 (the FORENSIC §4.2 column) are
     reproduced from the table. This is the citation-hierarchy tier the brief
     authorises where no KP text is ingested, and it extends the existing
     M3-W3-C2-KP-VARSHAPHALA crosscheck rather than inventing a new harness.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from brahmagyan.l0_kp_sublord_division import (
    NAKSHATRA_COUNT, NAK_SPAN_DEG, PLANET_CYCLE, RASHI_SPAN_DEG, TABLE_VERSION,
    VIMSHOTTARI_YEARS, build_divisions, build_sub_segments, lookup_division,
)


@pytest.fixture(scope="module")
def divisions():
    return build_divisions()


# ── 1. Geometry ────────────────────────────────────────────────────────────────

def test_243_raw_sub_segments_before_the_rashi_cut():
    """R1 alone: 27 nakshatras × 9 Vimshottari subs."""
    assert len(build_sub_segments()) == NAKSHATRA_COUNT * len(PLANET_CYCLE) == 243


def test_exactly_249_divisions_after_the_rashi_cut(divisions):
    """The classical KP figure, DERIVED (243 + 6), not hard-coded in the builder."""
    assert len(divisions) == 249


def test_exactly_six_sub_segments_are_split_by_a_rashi_boundary(divisions):
    """6 split segments → 12 fragment rows. The other 6 rāśi boundaries either start
    a nakṣatra (0°/120°/240°) or land exactly on a sub boundary (60°/180°/300°)."""
    fragments = [d for d in divisions if d["split_by_sign_boundary"]]
    assert len(fragments) == 12
    assert len(divisions) - len(build_sub_segments()) == 6


def test_the_three_exact_coincidences_are_real_not_float_luck():
    """60°, 180° and 300° must fall EXACTLY on a sub boundary — the whole reason the
    count is 249 and not 252. Checked in exact rationals."""
    boundaries = set()
    for seg in build_sub_segments():
        boundaries.add(seg["start"])
    for deg in (60, 180, 300):
        assert Fraction(deg) in boundaries, (
            f"{deg}° is not an exact sub boundary — the 249 derivation is wrong"
        )
    for deg in (30, 90, 150, 210, 270, 330):
        assert Fraction(deg) not in boundaries, (
            f"{deg}° unexpectedly coincides with a sub boundary — the split count changes"
        )


def test_divisions_tile_the_circle_exactly_once(divisions):
    """No gap, no overlap, start at 0°, end at 360°."""
    assert divisions[0]["_start_exact"] == 0
    assert divisions[-1]["_end_exact"] == 360
    for a, b in zip(divisions, divisions[1:]):
        assert a["_end_exact"] == b["_start_exact"], (
            f"gap/overlap between divisions {a['division_index']} and {b['division_index']}"
        )


def test_total_arc_is_exactly_360_degrees(divisions):
    total = sum(d["_end_exact"] - d["_start_exact"] for d in divisions)
    assert total == 360


def test_each_division_lies_wholly_within_one_nakshatra_and_one_rashi(divisions):
    for d in divisions:
        start, end = d["_start_exact"], d["_end_exact"]
        nak_of_start = int(start / NAK_SPAN_DEG)
        # end is exclusive: step just inside it
        nak_of_end = int((end - Fraction(1, 10**9)) / NAK_SPAN_DEG)
        assert nak_of_start == nak_of_end == d["nakshatra_number"] - 1
        sign_of_start = int(start / RASHI_SPAN_DEG)
        sign_of_end = int((end - Fraction(1, 10**9)) / RASHI_SPAN_DEG)
        assert sign_of_start == sign_of_end == d["sign_number"] - 1


def test_star_lord_follows_the_vimshottari_cycle(divisions):
    for d in divisions:
        expected = PLANET_CYCLE[(d["nakshatra_number"] - 1) % len(PLANET_CYCLE)]
        assert d["star_lord"] == expected


def test_unsplit_sub_spans_match_the_vimshottari_proportion(divisions):
    """An unsplit division's arc must be exactly lord_years/9 degrees."""
    for d in divisions:
        if d["split_by_sign_boundary"]:
            continue
        span = d["_end_exact"] - d["_start_exact"]
        assert span == Fraction(VIMSHOTTARI_YEARS[d["sub_lord"]], 9), (
            f"division {d['division_index']} ({d['sub_lord']}) has arc {span}"
        )


def test_split_fragments_reassemble_to_the_full_sub_arc(divisions):
    """Every split sub is still whole: its two fragments sum to lord_years/9."""
    fragments = [d for d in divisions if d["split_by_sign_boundary"]]
    assert len(fragments) % 2 == 0
    for a, b in zip(fragments[0::2], fragments[1::2]):
        assert a["sub_lord"] == b["sub_lord"]
        assert a["nakshatra_number"] == b["nakshatra_number"]
        total = (a["_end_exact"] - a["_start_exact"]) + (b["_end_exact"] - b["_start_exact"])
        assert total == Fraction(VIMSHOTTARI_YEARS[a["sub_lord"]], 9)


def test_row_shape_is_insertable(divisions):
    required = {
        "table_version", "division_index", "start_longitude_deg", "end_longitude_deg",
        "span_arcmin", "nakshatra_number", "star_lord", "sub_lord", "sign_number",
        "pada_at_start", "pada_at_end", "split_by_sign_boundary", "source_citation",
    }
    for d in divisions:
        assert required <= set(d)
        assert d["table_version"] == TABLE_VERSION
        assert 1 <= d["pada_at_start"] <= 4
        assert 1 <= d["pada_at_end"] <= 4
        assert d["span_arcmin"] > 0
    assert [d["division_index"] for d in divisions] == list(range(1, len(divisions) + 1))


# ── 2. Cross-implementation two-pass check ─────────────────────────────────────

def test_l0_constants_have_not_drifted_from_the_l1_consumer():
    """The L0 authority and the L1 subdivision function must agree on the Vimśottarī
    table and order, or every KP value in the instrument silently forks."""
    from ga_writers import ga_nakshatra_compute as l1

    assert l1.VIMSHOTTARI_YEARS == VIMSHOTTARI_YEARS
    assert l1.PLANET_CYCLE == PLANET_CYCLE


@pytest.mark.parametrize("step_deg", [0.01])
def test_table_lookup_agrees_with_compute_kp_lords_across_the_whole_circle(
    divisions, step_deg,
):
    """PASS 2. Exact-rational division table vs. the live float-accumulating
    `compute_kp_lords` — two independent derivations over 36,000 longitudes.

    Boundary-adjacent samples are EXCLUDED and counted, not silently tolerated: at a
    boundary the two implementations legitimately round to opposite sides, and a
    disagreement there is not evidence of an engine defect (the same GAP.09
    boundary-flip effect CROSSCHECK §3 documents). Everything else must agree exactly.
    """
    from ga_writers.ga_nakshatra_compute import compute_kp_lords

    boundary_orb_deg = 1e-6
    edges = sorted({float(d["_start_exact"]) for d in divisions})

    checked = skipped = 0
    mismatches: list[str] = []
    lon = 0.0
    while lon < 360.0:
        near_edge = any(abs(lon - e) < boundary_orb_deg for e in edges)
        if near_edge:
            skipped += 1
        else:
            d = lookup_division(lon, divisions)
            live = compute_kp_lords(lon)
            checked += 1
            if (d["star_lord"], d["sub_lord"]) != (live["star_lord"], live["sub_lord"]):
                mismatches.append(
                    f"{lon:.4f}°: table {d['star_lord']}/{d['sub_lord']} "
                    f"vs compute_kp_lords {live['star_lord']}/{live['sub_lord']}"
                )
        lon = round(lon + step_deg, 6)

    assert checked > 35_000, f"sweep too sparse: only {checked} samples"
    assert not mismatches, (
        f"{len(mismatches)} of {checked} samples disagree between the L0 division table "
        f"and compute_kp_lords (first 5: {mismatches[:5]}) — halt-worthy, §N.5"
    )


def test_lookup_is_half_open_at_every_boundary(divisions):
    """A longitude exactly ON a boundary belongs to the division that STARTS there."""
    for d in divisions[:50]:
        got = lookup_division(float(d["_start_exact"]), divisions)
        assert got["division_index"] == d["division_index"]


def test_lookup_wraps_360_to_0(divisions):
    assert lookup_division(360.0, divisions)["division_index"] == 1
    assert lookup_division(-0.5, divisions)["division_index"] == \
        lookup_division(359.5, divisions)["division_index"]


# ── 3. Classical fixture (tier iii, committed) ─────────────────────────────────

#: `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` §2 — the FORENSIC §4.2 column, the
#: canonical KP Planetary Positions table for the native (chart 482012f1).
#: {planet: (degree_within_sign, sign_index_0_based, star_lord, sub_lord)}
#: Absolute sidereal longitude = sign_index × 30 + degree_within_sign.
FORENSIC_KP_FIXTURE: dict[str, tuple[float, int, str, str]] = {
    #             deg w/i sign      sign (0=Aries)      star     sub
    "Sun":     (22 + 2 / 60,   9,  "Moon",    "Venus"),    # 22°02' Capricorn
    "Moon":    (27 + 8 / 60,  10,  "Jupiter", "Venus"),    # 27°08' Aquarius
    "Mars":    (18 + 37 / 60,  6,  "Rahu",    "Moon"),     # 18°37' Libra
    "Mercury": (0 + 55 / 60,   9,  "Sun",     "Rahu"),     # 00°55' Capricorn
    "Jupiter": (9 + 53 / 60,   8,  "Ketu",    "Saturn"),   # 09°53' Sagittarius
    "Venus":   (19 + 15 / 60,  8,  "Venus",   "Rahu"),     # 19°15' Sagittarius
    "Saturn":  (22 + 32 / 60,  6,  "Jupiter", "Saturn"),   # 22°32' Libra
    "Rahu":    (19 + 7 / 60,   1,  "Moon",    "Mercury"),  # 19°07' Taurus
    "Ketu":    (19 + 7 / 60,   7,  "Mercury", "Ketu"),     # 19°07' Scorpio
}


def test_forensic_fixture_star_lords_9_of_9(divisions):
    """CROSSCHECK §0 records Star Lord 9/9 PASS. The division table must reproduce it."""
    for planet, (deg, sign0, star, _sub) in FORENSIC_KP_FIXTURE.items():
        got = lookup_division(sign0 * 30 + deg, divisions)["star_lord"]
        assert got == star, f"{planet}: table says star_lord={got}, FORENSIC §4.2 says {star}"


def test_forensic_fixture_sub_lords_9_of_9(divisions):
    """CROSSCHECK §0 records Sub Lord 9/9 PASS. Same requirement."""
    for planet, (deg, sign0, _star, sub) in FORENSIC_KP_FIXTURE.items():
        got = lookup_division(sign0 * 30 + deg, divisions)["sub_lord"]
        assert got == sub, f"{planet}: table says sub_lord={got}, FORENSIC §4.2 says {sub}"


def test_worked_example_sun_in_capricorn(divisions):
    """The PR's hand-worked example, asserted end to end.

    Sun 22°02' Capricorn → absolute sidereal 292°02' = 292.0333°.
    292.0333 / 13°20' = nakshatra 22 (Shravana, 0-based 21) → star lord
    PLANET_CYCLE[21 % 9] = PLANET_CYCLE[3] = Moon. Shravana starts at
    21 × 13°20' = 280°00'; the Sun is 12°02' = 722' into it. Sub sequence from Moon:
    Moon 10/9° = 66.67', Mars 46.67' (→113.33'), Rahu 120' (→233.33'),
    Jupiter 106.67' (→340'), Saturn 126.67' (→466.67'), Mercury 113.33' (→580'),
    Ketu 46.67' (→626.67'), Venus 133.33' (→760'). 722' falls in the Venus segment
    (626.67'–760'). Star lord Moon, sub lord Venus — exactly FORENSIC §4.2.
    """
    d = lookup_division(270 + 22 + 2 / 60, divisions)
    assert d["nakshatra_number"] == 22          # Shravana
    assert d["sign_number"] == 10               # Capricorn
    assert d["star_lord"] == "Moon"
    assert d["sub_lord"] == "Venus"
    # Venus sub arc = 20/9° = 133.333' — this division is not split by a sign boundary.
    assert d["split_by_sign_boundary"] is False
    assert d["span_arcmin"] == pytest.approx(20 / 9 * 60)
