"""
test_ga_kp_significators — the 4-limbed KP significator ladder (W3K gap G-1).

ṢAḌ-DARŚANA W3K Lane 1 · ADJUDICATION-7 Part 2 (the ladder is an ADDITIVE emitter
on the standing `ga_nakshatra` asset, never a second natal-KP writer).

The fixture below is fully synthetic and hand-checkable: houses are the twelve
30° arcs from 0° Aries, so a planet's KP house is its sign number and every
expected value in this file can be re-derived on paper from the KP rule alone.
That is deliberate — a ladder test whose expected values come out of the same
code it is testing verifies nothing.

The final test runs the REAL native chart (482012f1) through the emitter with the
KP-canonical Krishnamurti ayanāṃśa and pins the worked example reproduced in the
PR body, so the classical claim is anchored to a real chart and not only to a toy.
"""
from __future__ import annotations

import pytest

from brahmagyan.l0_kp_sublord_division import build_divisions
from ga_writers.ga_kp_significators import (
    HOUSE_SIGNIFICATORS_CATEGORY, PLANET_SIGNIFICATIONS_CATEGORY,
    emit_kp_significators,
)

CHART = "test-chart"
AY = "krishnamurti"
BUILD = "test-build"

#: Parāśarī rulership, as the caller loads it from L0 `reference_signs`.
SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

#: (longitude, whole-sign house). Longitudes chosen so each planet's nakṣatra —
#: and therefore its star lord — is trivially checkable: nak0 = floor(lon / 13°20'),
#: star lord = PLANET_CYCLE[nak0 % 9].
SYNTHETIC_GRAHAS = [
    # planet     lon     nak0  star lord   KP house
    ("Sun",        5.0),  #  0  Ketu        1
    ("Moon",      40.0),  #  3  Moon        2
    ("Mars",     100.0),  #  7  Saturn      4
    ("Mercury",  130.0),  #  9  Ketu        5
    ("Jupiter",  200.0),  # 15  Jupiter     7
    ("Venus",    250.0),  # 18  Ketu        9
    ("Saturn",   280.0),  # 21  Moon       10
    ("Rahu",     310.0),  # 23  Rahu       11
    ("Ketu",     130.0),  #  9  Ketu        5
]


@pytest.fixture(scope="module")
def divisions():
    return build_divisions()


@pytest.fixture
def chart_output():
    return {
        "grahas": [
            {"name": name, "longitude_deg": lon, "house": int(lon // 30) + 1}
            for name, lon in SYNTHETIC_GRAHAS
        ],
        "ascendant": {"longitude_deg": 0.0, "sign_id": 1},
        "bhava_chalit": {
            "placidus": {
                "cusp_boundaries": [h * 30.0 for h in range(12)],
                "cusps": [
                    {"house": h + 1, "start": h * 30.0,
                     "madhya": h * 30.0 + 15.0, "end": (h + 1) * 30.0 % 360.0}
                    for h in range(12)
                ],
            }
        },
    }


def _index(rows):
    return {(r["fact_category"], r["fact_subject"], r["fact_key"]): r for r in rows}


@pytest.fixture
def rows(chart_output, divisions):
    return emit_kp_significators(CHART, AY, BUILD, chart_output, divisions, SIGN_LORDS)


# ── Star lords: REFERENCED from the L0 authority, and two-pass verified ────────

def test_star_lords_come_from_the_l0_division_table(rows):
    ix = _index(rows)
    expected = {
        "SUN": "Ketu", "MOON": "Moon", "MAR": "Saturn", "MER": "Ketu",
        "JUP": "Jupiter", "VEN": "Ketu", "SAT": "Moon",
        "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu",
    }
    for subject, star in expected.items():
        assert ix[(PLANET_SIGNIFICATIONS_CATEGORY, subject, "star_lord")]["fact_value_text"] == star


def test_star_lord_rows_cite_the_bg_division_index(rows):
    ix = _index(rows)
    src = ix[(PLANET_SIGNIFICATIONS_CATEGORY, "SUN", "star_lord")]["source_calculation"]
    assert "REF bg_kp_sublord_division:division_index=" in src


def test_star_lord_rows_carry_a_real_two_pass_verdict(rows):
    """The L0 table and the live `compute_kp_lords` path agree here, so the verdict is
    `two_pass_verified` — a status that could genuinely have come back
    `divergent_flagged` (§N.8: a detector that can fail)."""
    ix = _index(rows)
    for subject in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"):
        row = ix[(PLANET_SIGNIFICATIONS_CATEGORY, subject, "star_lord")]
        assert row["verification_pass_status"] == "two_pass_verified"


def test_ladder_rows_do_not_claim_a_pass(rows):
    """The ladder itself is a deterministic join, not a second derivation. It must NOT
    set a verification status — it inherits the honest default in `_enrich_rows`."""
    for r in rows:
        if r["fact_category"] == HOUSE_SIGNIFICATORS_CATEGORY:
            assert "verification_pass_status" not in r


# ── The 4 limbs, per house ────────────────────────────────────────────────────

def test_house_5_full_ladder_hand_derived(rows):
    """House 5 (Leo, 120°–150°) is tenanted by Mercury and Ketu; its owner is the Sun.

    Level A = planets in the STAR of an occupant. Occupants are Mercury and Ketu;
    the planets whose star lord is Mercury or Ketu are Sun, Mercury, Venus and Ketu
    (all four sit in Ketu-lorded nakṣatras: Aśvinī, Maghā, Mūla).
    Level B = the occupants: Mercury, Ketu.
    Level C = planets in the star of the OWNER (Sun): none — no planet here is in a
    Sun-lorded nakṣatra (Kṛttikā/Uttara Phalgunī/Uttarāṣāḍhā).
    Level D = the owner: Sun.
    """
    ix = _index(rows)
    h5 = lambda key: ix[(HOUSE_SIGNIFICATORS_CATEGORY, "HOUSE_05", key)]["fact_value_text"]
    assert h5("cusp_owner") == "Sun"
    assert h5("level_a_star_of_occupants") == "Sun,Mercury,Venus,Ketu"
    assert h5("level_b_occupants") == "Mercury,Ketu"
    assert h5("level_c_star_of_owner") == "none"
    assert h5("level_d_owner") == "Sun"
    assert h5("ranked_significators") == "Sun,Mercury,Venus,Ketu"


def test_ranking_dedups_to_the_strongest_appearance(rows):
    """Mercury and Ketu appear at BOTH level A and level B for house 5; each must
    appear once in the ranking, at its strongest (earliest) position."""
    ix = _index(rows)
    ranked = ix[(HOUSE_SIGNIFICATORS_CATEGORY, "HOUSE_05", "ranked_significators")]["fact_value_text"]
    parts = ranked.split(",")
    assert len(parts) == len(set(parts))
    assert parts.index("Mercury") < parts.index("Venus")  # A-position, not B-position


def test_empty_house_still_yields_its_owner(rows):
    """House 3 (Gemini) is untenanted. The ladder is not empty — level D always fires —
    and the empty limbs report the literal 'none', not an empty string."""
    ix = _index(rows)
    h3 = lambda key: ix[(HOUSE_SIGNIFICATORS_CATEGORY, "HOUSE_03", key)]["fact_value_text"]
    assert h3("cusp_owner") == "Mercury"
    assert h3("level_a_star_of_occupants") == "none"
    assert h3("level_b_occupants") == "none"
    assert h3("ranked_significators") == "Mercury"


def test_all_twelve_houses_emitted(rows):
    subjects = {r["fact_subject"] for r in rows
                if r["fact_category"] == HOUSE_SIGNIFICATORS_CATEGORY}
    assert subjects == {f"HOUSE_{h:02d}" for h in range(1, 13)}


def test_house_rows_declare_the_kp_house_frame(rows):
    ix = _index(rows)
    for h in range(1, 13):
        row = ix[(HOUSE_SIGNIFICATORS_CATEGORY, f"HOUSE_{h:02d}", "house_system")]
        assert row["fact_value_text"] == "placidus_kp"


# ── The per-planet direction ──────────────────────────────────────────────────

def test_venus_signified_houses_hand_derived(rows):
    """Venus's star lord is Ketu, which tenants house 5 → level A house 5.
    Venus itself tenants house 9 → level B. No house is owned by Ketu → level C empty.
    Venus owns Taurus (house 2) and Libra (house 7) → level D houses 2 and 7."""
    ix = _index(rows)
    v = lambda key: ix[(PLANET_SIGNIFICATIONS_CATEGORY, "VEN", key)]["fact_value_text"]
    assert v("level_a_houses") == "5"
    assert v("level_b_houses") == "9"
    assert v("level_c_houses") == "none"
    assert v("level_d_houses") == "2,7"
    assert v("signified_houses") == "5,9,2,7"
    assert v("strongest_level") == "a"


def test_planet_and_house_directions_are_consistent(rows):
    """Every (planet, house) pair claimed in one direction must appear in the other."""
    ix = _index(rows)
    subj_to_name = {
        "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury",
        "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn",
        "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu",
    }
    for level in ("a", "b", "c", "d"):
        house_key = {
            "a": "level_a_star_of_occupants", "b": "level_b_occupants",
            "c": "level_c_star_of_owner", "d": "level_d_owner",
        }[level]
        from_houses: set[tuple[str, int]] = set()
        for h in range(1, 13):
            txt = ix[(HOUSE_SIGNIFICATORS_CATEGORY, f"HOUSE_{h:02d}", house_key)]["fact_value_text"]
            if txt != "none":
                for p in txt.split(","):
                    from_houses.add((p, h))
        from_planets: set[tuple[str, int]] = set()
        for subj, name in subj_to_name.items():
            txt = ix[(PLANET_SIGNIFICATIONS_CATEGORY, subj, f"level_{level}_houses")]["fact_value_text"]
            if txt != "none":
                for h in txt.split(","):
                    from_planets.add((name, int(h)))
        assert from_planets <= from_houses, (
            f"level {level}: per-planet claims not backed by the per-house ladder: "
            f"{from_planets - from_houses}"
        )


# ── Law 4: the house-system divergence is served as data ──────────────────────

def test_both_house_frames_are_emitted_with_an_explicit_divergence_flag(rows):
    ix = _index(rows)
    for subj in ("SUN", "MOON", "SAT"):
        kp = ix[(PLANET_SIGNIFICATIONS_CATEGORY, subj, "kp_cuspal_house")]["fact_value_num"]
        ws = ix[(PLANET_SIGNIFICATIONS_CATEGORY, subj, "whole_sign_house")]["fact_value_num"]
        flag = ix[(PLANET_SIGNIFICATIONS_CATEGORY, subj, "house_system_divergence")]["fact_value_text"]
        assert kp is not None and ws is not None
        assert flag == ("true" if kp != ws else "false")


# ── B.10 honesty ──────────────────────────────────────────────────────────────

def test_nodal_agency_gap_is_emitted_not_hidden(rows):
    ix = _index(rows)
    for subj in ("RAH_MEAN", "KET_MEAN"):
        row = ix[(PLANET_SIGNIFICATIONS_CATEGORY, subj, "nodal_agency_not_applied")]
        assert row["fact_value_text"].startswith("[HONEST_GAP]")
    for subj in ("SUN", "MOON"):
        assert (PLANET_SIGNIFICATIONS_CATEGORY, subj, "nodal_agency_not_applied") not in ix


def test_absent_placidus_cusps_yield_external_required_not_a_whole_sign_substitute(
    chart_output, divisions,
):
    chart_output["bhava_chalit"] = {}
    rows = emit_kp_significators(CHART, AY, BUILD, chart_output, divisions, SIGN_LORDS)
    assert len(rows) == 12
    for r in rows:
        assert r["fact_value_text"].startswith("[EXTERNAL_COMPUTATION_REQUIRED]")
        assert r["verification_pass_status"] == "external_computation_required"


def test_lagna_is_not_a_significator(rows):
    """In KP the ascendant is cusp 1 — a house, not a significator."""
    subjects = {r["fact_subject"] for r in rows
                if r["fact_category"] == PLANET_SIGNIFICATIONS_CATEGORY}
    assert "LAGNA" not in subjects
    assert len(subjects) == 9


# ── The real native chart (worked example pinned in the PR body) ──────────────

NATIVE_BIRTH = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.2961,
    "longitude_deg": 85.8245,
    "place_name": "Bhubaneswar",
}


@pytest.fixture(scope="module")
def native_rows(divisions):
    compute_chart = pytest.importorskip(
        "pyjhora_adapter.compute", reason="ephemeris unavailable",
    ).compute_chart
    out = compute_chart(inputs=NATIVE_BIRTH, ayanamsha_id="kp")  # KP-canonical ayanāṃśa
    return emit_kp_significators("482012f1", "krishnamurti", "b", out, divisions, SIGN_LORDS)


def test_native_chart_10th_house_worked_example(native_rows):
    """Chart 482012f1, Krishnamurti ayanāṃśa, 10th cusp — the PR's worked example.

    10th Placidus cusp at 273.0669° (Capricorn) → owner Saturn. The 10th cuspal arc
    is [273.0669°, 301.1276°): the Sun (292.0595°) falls inside it; Mercury
    (270.9356°) does NOT — it is below the cusp and so is cuspally 9th, although
    whole-sign it is 10th. That divergence is real and is served, not reconciled.

      Level A  planets in the star of an occupant. The occupant is the Sun; the
               planet tenanting a Sun-lorded nakṣatra is Mercury (270.9356°,
               Uttarāṣāḍhā, star lord Sun) → Mercury.
      Level B  the occupants → Sun.
      Level C  planets in the star of the owner (Saturn) → none; no graha here sits
               in Puṣya / Anurādhā / Uttara Bhādrapadā.
      Level D  the owner → Saturn.
      Ranked   Mercury, Sun, Saturn.

    The classical point, and the reason KP is a genuinely independent voice: MERCURY
    is the strongest 10th-house significator even though Mercury is not in the 10th
    cuspal house at all. No Parāśarī rule reaches that verdict.
    """
    ix = _index(native_rows)
    h10 = lambda key: ix[(HOUSE_SIGNIFICATORS_CATEGORY, "HOUSE_10", key)]["fact_value_text"]
    assert h10("cusp_owner") == "Saturn"
    assert h10("level_a_star_of_occupants") == "Mercury"
    assert h10("level_b_occupants") == "Sun"
    assert h10("level_c_star_of_owner") == "none"
    assert h10("level_d_owner") == "Saturn"
    assert h10("ranked_significators") == "Mercury,Sun,Saturn"

    cusp = ix[(HOUSE_SIGNIFICATORS_CATEGORY, "HOUSE_10", "cusp_longitude_sidereal")]
    assert cusp["fact_value_num"] == pytest.approx(273.0669, abs=1e-3)


def test_native_chart_mercury_house_frame_divergence_is_served(native_rows):
    """Mercury at 270.9356° is cuspally 9th and whole-sign 10th. Both frames are
    stored side by side with an explicit flag — Elevation Law 4 / brief §W3K's
    "served as data, never silently reconciled"."""
    ix = _index(native_rows)
    m = lambda key: ix[(PLANET_SIGNIFICATIONS_CATEGORY, "MER", key)]
    assert m("kp_cuspal_house")["fact_value_num"] == 9.0
    assert m("whole_sign_house")["fact_value_num"] == 10.0
    assert m("house_system_divergence")["fact_value_text"] == "true"
    assert m("star_lord")["fact_value_text"] == "Sun"
    # Level A of the 10th, level B of the 9th — the two frames, both honoured.
    assert "10" in m("level_a_houses")["fact_value_text"].split(",")
    assert "9" in m("level_b_houses")["fact_value_text"].split(",")


def test_native_chart_every_star_lord_two_pass_verified(native_rows):
    """Gate W3K's two-pass requirement on the real chart: the L0 division table and the
    live subdivision path agree for all nine grahas."""
    ix = _index(native_rows)
    verdicts = [
        r["verification_pass_status"]
        for (cat, _subj, key), r in ix.items()
        if cat == PLANET_SIGNIFICATIONS_CATEGORY and key == "star_lord"
    ]
    assert len(verdicts) == 9
    assert set(verdicts) == {"two_pass_verified"}
