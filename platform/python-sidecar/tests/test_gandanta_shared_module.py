"""
test_gandanta_shared_module.py — Suvarna S-L1 lane I-22 (decision sheet A-4 / X1, SS N-62).

ONE shared Gandanta definition (`brahmagyan.gandanta`, 3 deg 20 min each side of the three
water|fire junctions) imported by the three L1 writers `ga_sensitive_degree`,
`ga_structural` and `ga_nakshatra`; `ga_nakshatra`'s unqualified `is_gandanta` now follows
that width and the former 0 deg 48 min reading is emitted as variant rows
`formula_id = 'strict_0_48'`.

Guards, pure (no database, no ephemeris):
  1. Golden boundary values: just inside / exactly on / just outside the 3 deg 20 min arc on
     BOTH sides of EACH junction (Meena|Mesha, Karka|Simha, Vrischika|Dhanu).
  2. 0 deg 48 min vs 3 deg 20 min cases (strict-and-canonical; canonical-only).
  3. Equivalence: the shared module reproduces the pre-I-22 `ga_sensitive_degree`
     `check_gandanta` and the pre-I-22 `ga_nakshatra` `compute_gandanta` (kept here verbatim
     as reference implementations) on a dense longitude grid plus every boundary value.
  4. All three writers call the SAME function: patching the shared predicate changes the
     output of all three; the importers are object-identical to the shared module's names.
  5. Nothing else in the three writers' output moves (the non-gandanta rows of
     `build_sensitive_degree_rows`, the non-gandanta rows of `emit_gandanta_flags`).
  6. The emitted rows: canonical rows keep formula_id NULL and their keys; variant rows carry
     `strict_0_48`, the same four keys, distinct fact ids (no duplicate identity).
"""
from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SIDECAR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan import gandanta as shared  # noqa: E402
from brahmagyan.gandanta import (  # noqa: E402
    GANDANTA_ARC,
    GANDANTA_JUNCTIONS,
    GANDANTA_STRICT_ARC,
    GANDANTA_STRICT_FORMULA_ID,
    check_gandanta,
    locate_gandanta,
    locate_gandanta_strict,
)
from ga_writers import ga_nakshatra_compute as nak_compute  # noqa: E402
from ga_writers import ga_nakshatra_emitters as nak_emit  # noqa: E402
from ga_writers import ga_sensitive_degree_writer as sd  # noqa: E402
from ga_writers import ga_structural_writer as struct  # noqa: E402

# (water sign, fire sign, cusp longitude, junction_type)
JUNCTIONS = (
    (11, 0, 0.0, "water_fire_0"),        # Meena | Mesha     Revati | Ashwini
    (3, 4, 120.0, "water_fire_120"),     # Karka | Simha     Ashlesha | Magha
    (7, 8, 240.0, "water_fire_240"),     # Vrischika | Dhanu Jyeshtha | Mula
)
_UP = math.inf


def _below(x: float) -> float:
    return math.nextafter(x, -_UP)


def _above(x: float) -> float:
    return math.nextafter(x, _UP)


# ── the constant ─────────────────────────────────────────────────────────────────────

def test_gandanta_arc_is_three_degrees_twenty_minutes_exactly():
    assert GANDANTA_ARC == 30.0 / 9.0                      # the float the writers always used
    assert shared.GANDANTA_ARC_EXACT == Fraction(10, 3)    # 3 deg 20 min as an exact rational
    assert shared.GANDANTA_ARC_ARCMIN == 200               # 3*60 + 20
    assert abs(GANDANTA_ARC - 10 / 3) < 1e-15
    assert shared.GANDANTA_ARC_EXACT * 60 == shared.GANDANTA_ARC_ARCMIN


def test_strict_variant_constants():
    assert GANDANTA_STRICT_FORMULA_ID == "strict_0_48"
    assert shared.GANDANTA_STRICT_ARC_ARCMIN == 48.0
    assert GANDANTA_STRICT_ARC == 48.0 / 60.0


def test_junction_table():
    assert [(j.water_sign, j.fire_sign, j.cusp_deg, j.name) for j in GANDANTA_JUNCTIONS] == list(JUNCTIONS)
    assert shared.GANDANTA_WATER_SIGNS == frozenset({3, 7, 11})
    assert shared.GANDANTA_FIRE_SIGNS == frozenset({4, 8, 0})
    for j in GANDANTA_JUNCTIONS:
        assert (j.water_sign + 1) % 12 == j.fire_sign          # the fire sign FOLLOWS the water sign
        assert j.cusp_deg == 30.0 * j.fire_sign                # the cusp is the fire sign's start


def test_sign_names_match_the_writers():
    assert list(shared._SIGN_NAMES) == sd.SIGNS


# ── golden boundary values, sign + degree form (float-exact edges) ───────────────────

@pytest.mark.parametrize("water,fire,cusp,jt", JUNCTIONS)
def test_water_side_edges(water, fire, cusp, jt):
    edge = 30.0 - GANDANTA_ARC                                  # 26.666666666666668
    assert check_gandanta(water, edge)["fired"] is True         # exactly on the edge: inclusive
    assert check_gandanta(water, _above(edge))["fired"] is True # just inside
    assert check_gandanta(water, _below(edge))["fired"] is False  # just outside
    assert check_gandanta(water, 29.999)["fired"] is True       # 1 arcsec-ish before the cusp
    assert check_gandanta(water, 26.0)["fired"] is False        # 4 deg before: outside
    inside = check_gandanta(water, 29.5)
    assert inside["gandanta_zone"] == f"end_of_{sd.SIGNS[water]}"
    assert inside["distance_to_junction_deg"] == 0.5


@pytest.mark.parametrize("water,fire,cusp,jt", JUNCTIONS)
def test_fire_side_edges(water, fire, cusp, jt):
    assert check_gandanta(fire, GANDANTA_ARC)["fired"] is True          # exactly on the edge: inclusive
    assert check_gandanta(fire, _below(GANDANTA_ARC))["fired"] is True  # just inside
    assert check_gandanta(fire, _above(GANDANTA_ARC))["fired"] is False  # just outside
    assert check_gandanta(fire, 0.0)["fired"] is True                   # on the cusp itself
    assert check_gandanta(fire, 4.0)["fired"] is False                  # 4 deg after: outside
    inside = check_gandanta(fire, 1.0)
    assert inside["gandanta_zone"] == f"start_of_{sd.SIGNS[fire]}"
    assert inside["distance_to_junction_deg"] == 1.0


def test_other_signs_never_gandanta():
    for sign in range(12):
        if sign in (3, 4, 7, 8, 11, 0):
            continue
        for deg in (0.0, 1.0, 15.0, 29.0, 29.999):
            assert check_gandanta(sign, deg)["fired"] is False


def test_the_zone_is_contiguous_across_each_cusp():
    """Water-side and fire-side arcs together are one 6 deg 40 min zone around the cusp."""
    for water, fire, cusp, jt in JUNCTIONS:
        assert check_gandanta(water, 29.999)["fired"] and check_gandanta(fire, 0.001)["fired"]
        assert 2 * GANDANTA_ARC == pytest.approx(20.0 / 3.0)


# ── golden boundary values, longitude form (human-readable: 3 deg 19' in, 3 deg 21' out) ──

@pytest.mark.parametrize("water,fire,cusp,jt", JUNCTIONS)
def test_longitude_form_both_sides(water, fire, cusp, jt):
    c = cusp if cusp else 360.0
    d19, d21 = 3 + 19 / 60, 3 + 21 / 60
    # before the cusp (approaching)
    r = locate_gandanta(c - d19)
    assert r["fired"] and r["side"] == "approaching" and r["junction_type"] == jt
    assert r["arc_minutes_from_junction"] == pytest.approx(199.0, abs=0.01)
    assert locate_gandanta(c - d21)["fired"] is False
    # after the cusp (departing)
    r = locate_gandanta(cusp + d19)
    assert r["fired"] and r["side"] == "departing" and r["junction_type"] == jt
    assert r["arc_minutes_from_junction"] == pytest.approx(199.0, abs=0.01)
    assert locate_gandanta(cusp + d21)["fired"] is False
    # the shared longitude form agrees with the sign+degree form
    for lon in (c - d19, c - d21, cusp + d19, cusp + d21, c - 0.5, cusp + 0.5):
        assert locate_gandanta(lon)["fired"] == check_gandanta(int((lon % 360) // 30) % 12, (lon % 360) % 30.0)["fired"]


def test_pisces_aries_wraparound():
    assert locate_gandanta(359.5)["side"] == "approaching"       # Pisces 29 deg 30 min
    assert locate_gandanta(0.5)["side"] == "departing"           # Aries 0 deg 30 min
    assert locate_gandanta(360.5)["fired"] is True               # longitude reduced mod 360
    assert locate_gandanta(-0.5)["fired"] is True
    assert locate_gandanta(356.0)["fired"] is False              # 4 deg before 0/360


# ── 0 deg 48 min strict variant vs the canonical 3 deg 20 min width ──────────────────

def test_strict_and_canonical_both_true():
    for lon in (359.5, 0.5, 119.6, 240.5):                      # 30', 30', 24', 30' from a cusp
        assert locate_gandanta(lon)["fired"] is True
        assert locate_gandanta_strict(lon)["fired"] is True


def test_canonical_only_not_strict():
    # 1 deg from a cusp: gandanta at 3 deg 20 min, NOT at 0 deg 48 min
    for lon in (359.0, 1.0, 119.0, 121.0, 239.0, 241.0, 357.0, 3.0):
        assert locate_gandanta(lon)["fired"] is True, lon
        assert locate_gandanta_strict(lon)["fired"] is False, lon


def test_strict_edge_is_forty_eight_arcminutes_inclusive():
    assert locate_gandanta_strict(0.8)["fired"] is True          # 48' exactly (departing side)
    assert locate_gandanta_strict(0.8001)["fired"] is False
    # approaching side, in sign + degree form (the longitude 359.2 is not exactly representable
    # as "29.2 deg into Pisces" in binary floating point, so the exact edge is asserted there)
    edge = 30.0 - GANDANTA_STRICT_ARC
    assert shared._classify(11, edge, GANDANTA_STRICT_ARC) is not None
    assert shared._classify(11, _below(edge), GANDANTA_STRICT_ARC) is None
    assert locate_gandanta_strict(359.2001)["fired"] is True
    assert locate_gandanta_strict(359.1999)["fired"] is False


def test_strict_is_always_a_subset_of_canonical():
    for k in range(0, 36000):
        lon = k / 100.0
        if locate_gandanta_strict(lon)["fired"]:
            assert locate_gandanta(lon)["fired"] is True


def test_nothing_is_gandanta_far_from_every_cusp():
    for lon in (30.0, 60.0, 90.0, 150.0, 180.0, 210.0, 270.0, 300.0, 330.0):
        assert locate_gandanta(lon)["fired"] is False


# ── equivalence to the pre-I-22 implementations (verbatim reference copies) ─────────

def _legacy_check_gandanta(sign_num: int, degree_in_sign: float) -> dict:
    """ga_sensitive_degree_writer.check_gandanta exactly as it was before I-22."""
    arc = 30.0 / 9.0
    water, fire = {3, 7, 11}, {4, 8, 0}
    dist = None
    zone = None
    if sign_num in water and degree_in_sign >= (30.0 - arc):
        dist = 30.0 - degree_in_sign
        zone = f"end_of_{sd.SIGNS[sign_num]}"
    elif sign_num in fire and degree_in_sign <= arc:
        dist = degree_in_sign
        zone = f"start_of_{sd.SIGNS[sign_num]}"
    return {
        "fired": dist is not None,
        "gandanta_zone": zone,
        "distance_to_junction_deg": round(dist, 4) if dist is not None else None,
        "gandanta_arc_deg": round(arc, 4),
        "graha_deg_in_sign": round(degree_in_sign, 4),
        "sign": sd.SIGNS[sign_num],
    }


def _legacy_compute_gandanta(longitude: float, orb_arcmin: float) -> dict:
    """ga_nakshatra_compute.compute_gandanta exactly as it was before I-22 (orb 48')."""
    long_mod = longitude % 360.0
    best_dist = best_junction = best_side = None
    for jdeg in (0.0, 120.0, 240.0):
        d_approach = (jdeg - long_mod) % 360.0
        d_depart = (long_mod - jdeg) % 360.0
        for dist_deg, side in [(d_approach, "approaching"), (d_depart, "departing")]:
            dist_am = dist_deg * 60.0
            if dist_am <= orb_arcmin:
                if best_dist is None or dist_am < best_dist:
                    best_dist, best_junction, best_side = dist_am, f"water_fire_{int(jdeg)}", side
    return {
        "is_gandanta": best_dist is not None,
        "arc_minutes_from_junction": round(best_dist, 2) if best_dist is not None else None,
        "junction_type": best_junction,
        "side": best_side,
    }


def test_check_gandanta_equals_the_pre_i22_function_everywhere():
    """Same dict, same values, on a dense (sign x degree) grid plus every boundary value."""
    degs = [k / 50.0 for k in range(0, 1500)]
    edge = 30.0 - GANDANTA_ARC
    degs += [edge, _below(edge), _above(edge), GANDANTA_ARC, _below(GANDANTA_ARC),
             _above(GANDANTA_ARC), 0.0, 29.999999999, 30.0 - 1e-12]
    for sign in range(12):
        for d in degs:
            assert check_gandanta(sign, d) == _legacy_check_gandanta(sign, d), (sign, d)
    # and the writer's re-export is the very same function
    assert sd.check_gandanta is check_gandanta


def test_strict_variant_equals_the_pre_i22_ga_nakshatra_reading():
    """`compute_gandanta_strict` (0 deg 48 min) reproduces the old stored reading, except at
    the exact cusp longitude where the old code tie-broke to 'approaching' and the shared
    definition follows the sign (the fire sign starts there: 'departing')."""
    diffs = []
    lons = [k / 100.0 for k in range(0, 36000)]
    lons += [0.0, 120.0, 240.0, 359.9999999, 0.8, 119.2, 120.8, 239.2, 240.8, 359.2, 360.0 - 0.8]
    for lon in lons:
        old = _legacy_compute_gandanta(lon, 48.0)
        new = nak_compute.compute_gandanta_strict(lon)
        if old != new:
            diffs.append((lon, old, new))
    cusp_ties = [d for d in diffs if d[0] % 120.0 == 0.0]
    other = [d for d in diffs if d[0] % 120.0 != 0.0]
    assert other == [], other[:5]
    for lon, old, new in cusp_ties:
        assert old["is_gandanta"] is new["is_gandanta"] is True
        assert old["side"] == "approaching" and new["side"] == "departing"
        assert old["arc_minutes_from_junction"] == new["arc_minutes_from_junction"] == 0.0


def test_compute_gandanta_now_follows_three_twenty_not_forty_eight():
    # 1 deg from the cusp: the OLD ga_nakshatra reading said False; the canonical reading says True
    assert _legacy_compute_gandanta(359.0, 48.0)["is_gandanta"] is False
    assert nak_compute.compute_gandanta(359.0)["is_gandanta"] is True
    assert nak_compute.compute_gandanta(359.0) == {
        "is_gandanta": True, "arc_minutes_from_junction": 60.0,
        "junction_type": "water_fire_0", "side": "approaching",
    }
    # return shape unchanged
    assert set(nak_compute.compute_gandanta(90.0)) == {
        "is_gandanta", "arc_minutes_from_junction", "junction_type", "side"}
    # the Abhinandan Mars case from the decision sheet: 3.18 deg before the end of Pisces
    mars = 360.0 - 3.18
    assert nak_compute.compute_gandanta(mars)["is_gandanta"] is True
    assert nak_compute.compute_gandanta_strict(mars)["is_gandanta"] is False
    assert check_gandanta(11, 30.0 - 3.18)["fired"] is True      # the sensitive-degree reading agrees


# ── all three writers call the SAME function ──────────────────────────────────────────

def test_importers_are_object_identical_to_the_shared_definition():
    assert sd.check_gandanta is shared.check_gandanta
    assert sd.GANDANTA_ARC is shared.GANDANTA_ARC
    assert sd.GANDANTA_CITATION is shared.GANDANTA_CITATION
    assert struct._shared_check_gandanta is shared.check_gandanta
    assert nak_compute.locate_gandanta is shared.locate_gandanta
    assert nak_compute.locate_gandanta_strict is shared.locate_gandanta_strict
    assert nak_emit.GANDANTA_STRICT_FORMULA_ID is shared.GANDANTA_STRICT_FORMULA_ID


def test_no_writer_still_declares_its_own_gandanta_definition():
    for mod in (sd, nak_compute, nak_emit):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        # (a navamsa arc 30.0 / 9.0 may legitimately appear for Pushkara; a GANDANTA arc may not)
        assert "GANDANTA_ARC =" not in src and "GANDANTA_ARC:" not in src, mod.__name__
        assert "_WATER_SIGNS" not in src and "_FIRE_SIGNS" not in src, mod.__name__
    assert not hasattr(nak_compute, "GANDANTA_ORB_ARCMIN")
    assert not hasattr(nak_compute, "GANDANTA_JUNCTION_DEG")
    assert not hasattr(sd, "_WATER_SIGNS") and not hasattr(sd, "_FIRE_SIGNS")


def _sd_positions(sign: int, deg: float) -> dict:
    return {"Mars": {"sign_num": sign, "degree_in_sign": deg, "house_d1": 1,
                     "longitude_sidereal": sign * 30.0 + deg}}


def _sensitive_degree_gandanta_row(sign: int, deg: float) -> dict:
    rows = sd.build_sensitive_degree_rows("c", "b", "lahiri_chitrapaksha", _sd_positions(sign, deg))
    return next(r for r in rows if r["fact_key"] == "gandanta")


def _structural_gandanta_fires(longitude: float) -> bool:
    grahas = [{"name": "Mars", "longitude": longitude, "house": 12, "sign": "Pisces"},
              {"name": "Sun", "longitude": 100.0, "house": 4, "sign": "Cancer"}]
    chart_output = {"grahas": grahas, "ascendant": {"longitude": 10.0, "sign": "Aries", "sign_id": 1}}
    rows = struct._build_dosha_rows(MagicMock(), chart_output, "c", "b", "lahiri_chitrapaksha",
                                    "2026-10-02T00:00:00+00:00", "test", dosha_catalog=None)
    return any(r["fact_subject"] == "GANDANTA_DOSHA" for r in rows)


def test_patching_the_shared_predicate_changes_all_three_writers(monkeypatch):
    lon = 360.0 - 3.18                                        # Pisces 26 deg 49' 12": canonical gandanta
    sign, deg = 11, 30.0 - 3.18
    # baseline: all three say gandanta
    assert _sensitive_degree_gandanta_row(sign, deg)["fact_value_text"] == "gandanta"
    assert nak_compute.compute_gandanta(lon)["is_gandanta"] is True
    assert _structural_gandanta_fires(lon) is True
    # make the ONE shared predicate say "never": all three flip
    monkeypatch.setattr(shared, "_classify", lambda sign_num, degree_in_sign, arc: None)
    assert _sensitive_degree_gandanta_row(sign, deg)["fact_value_text"] == "not_gandanta"
    assert nak_compute.compute_gandanta(lon)["is_gandanta"] is False
    assert _structural_gandanta_fires(lon) is False
    # and the strict variant is derived from the same predicate too
    assert nak_compute.compute_gandanta_strict(359.9)["is_gandanta"] is False


def test_patching_the_shared_arc_width_widens_every_consumer(monkeypatch):
    """The width lives in exactly one place: widening it there widens every consumer."""
    assert nak_compute.compute_gandanta(355.0)["is_gandanta"] is False   # 5 deg before the cusp
    assert check_gandanta(11, 25.0)["fired"] is False
    monkeypatch.setattr(shared, "GANDANTA_ARC", 6.0)
    assert check_gandanta(11, 25.0)["fired"] is True
    assert sd.check_gandanta(11, 25.0)["fired"] is True
    assert nak_compute.compute_gandanta(355.0)["is_gandanta"] is True
    # the strict variant has its own named width and does not follow the canonical one
    assert nak_compute.compute_gandanta_strict(355.0)["is_gandanta"] is False


# ── nothing else in the three writers' output moves ──────────────────────────────────

def test_sensitive_degree_rows_outside_gandanta_are_unmoved_by_the_shared_module():
    """build_sensitive_degree_rows still emits the same facets in the same order, and the
    gandanta row's value_jsonb is the pre-I-22 dict byte for byte."""
    import json
    rows = sd.build_sensitive_degree_rows("c", "b", "lahiri_chitrapaksha", _sd_positions(11, 26.8))
    keys = [r["fact_key"] for r in rows]
    assert keys.count("gandanta") == 1
    g = next(r for r in rows if r["fact_key"] == "gandanta")
    assert json.loads(g["fact_value_jsonb"]) == _legacy_check_gandanta(11, 26.8)
    assert g["citation_human"] == shared.GANDANTA_CITATION
    assert g["fact_value_num"] == round(30.0 - 26.8, 4)
    assert g["fact_value_text"] == "gandanta"


def test_gandanta_citation_text_is_unchanged():
    assert shared.GANDANTA_CITATION == (
        "Classical gandanta (BPHS / Sarvartha Chintamani): last 3°20' of a water sign "
        "and first 3°20' of the succeeding fire sign — the Ashlesha-Magha, Jyeshtha-Mula "
        "and Revati-Ashwini nakshatra sandhi."
    )


# ── ga_nakshatra rows: canonical + strict_0_48 variant ───────────────────────────────

def _chart_output(mars_lon: float, moon_lon: float = 322.0) -> dict:
    def g(name, lon):
        return {"name": name, "longitude_deg": lon, "sign": "Pisces", "pada_navamsa_sign": "Pisces"}
    return {"grahas": [g("Mars", mars_lon), g("Moon", moon_lon)],
            "ascendant": {"longitude_deg": 10.0, "sign": "Aries", "pada_navamsa_sign": "Aries"}}


def _gandanta_rows(mars_lon: float) -> list[dict]:
    return [r for r in nak_emit.emit_gandanta_flags("c", "lahiri_chitrapaksha", "b", _chart_output(mars_lon))
            if r["fact_category"] == "graha_gandanta" and r["fact_subject"] == "MAR"]


def test_canonical_and_variant_rows_for_a_canonical_only_longitude():
    rows = _gandanta_rows(356.82)                     # 3.18 deg before the cusp: canonical yes, strict no
    canon = {r["fact_key"]: r for r in rows if "formula_id" not in r}
    strict = {r["fact_key"]: r for r in rows if r.get("formula_id") == "strict_0_48"}
    assert canon["is_gandanta"]["fact_value_text"] == "true"
    assert set(canon) == {"is_gandanta", "arc_minutes_from_junction", "junction_type", "side"}
    assert canon["junction_type"]["fact_value_text"] == "water_fire_0"
    assert canon["side"]["fact_value_text"] == "approaching"
    assert canon["arc_minutes_from_junction"]["fact_value_num"] == pytest.approx(190.8, abs=0.01)
    # the strict variant says false and carries only is_gandanta
    assert set(strict) == {"is_gandanta"}
    assert strict["is_gandanta"]["fact_value_text"] == "false"


def test_canonical_and_variant_rows_for_a_strict_longitude():
    rows = _gandanta_rows(359.5)                      # 30' before the cusp: both readings
    canon = {r["fact_key"]: r for r in rows if "formula_id" not in r}
    strict = {r["fact_key"]: r for r in rows if r.get("formula_id") == "strict_0_48"}
    for d in (canon, strict):
        assert d["is_gandanta"]["fact_value_text"] == "true"
        assert set(d) == {"is_gandanta", "arc_minutes_from_junction", "junction_type", "side"}
        assert d["junction_type"]["fact_value_text"] == "water_fire_0"
        assert d["side"]["fact_value_text"] == "approaching"
        assert d["arc_minutes_from_junction"]["fact_value_num"] == pytest.approx(30.0, abs=0.01)
    assert strict["is_gandanta"]["source_calculation"].startswith("ga_nakshatra:gandanta:strict_0_48:")
    assert not canon["is_gandanta"]["source_calculation"].startswith("ga_nakshatra:gandanta:strict")


def test_clear_longitude_has_one_false_row_per_reading():
    rows = _gandanta_rows(90.0)
    assert [(r["fact_key"], r["fact_value_text"], r.get("formula_id")) for r in rows] == [
        ("is_gandanta", "false", None), ("is_gandanta", "false", "strict_0_48")]


def test_canonical_rows_keep_exactly_their_old_shape():
    """A canonical row has no `formula_id` key at all (so it takes the unchanged canonical
    INSERT / unique partition); only variant rows carry the key."""
    for r in nak_emit.emit_gandanta_flags("c", "lahiri_chitrapaksha", "b", _chart_output(359.5)):
        if r["fact_category"] == "graha_gandanta" and "formula_id" not in r:
            assert set(r) == {"chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject",
                              "fact_key", "fact_value_text", "fact_value_num", "source_calculation"}


def test_non_gandanta_rows_of_the_emitter_are_unmoved():
    rows = nak_emit.emit_gandanta_flags("c", "lahiri_chitrapaksha", "b", _chart_output(359.5))
    flags = [r for r in rows if r["fact_category"] == "graha_degree_flags"]
    assert sorted((r["fact_subject"], r["fact_key"], r["fact_value_text"]) for r in flags) == [
        ("LAGNA", "vargottama_via_pada", "true"),
        ("MAR", "vargottama_via_pada", "true"),
        ("MOON", "vargottama_via_pada", "true"),
    ]
    assert all("formula_id" not in r for r in flags)


def test_variant_rows_get_distinct_fact_ids_and_the_same_canonical_ids_as_before():
    from pipeline.orchestrator.writers import ga_nakshatra as w
    rows = nak_emit.emit_gandanta_flags("c", "lahiri_chitrapaksha", "b", _chart_output(359.5))
    enriched = w._enrich_rows(rows, "eng", "2026-10-02T00:00:00+00:00")
    ids = [r["fact_id"] for r in enriched]
    assert len(ids) == len(set(ids)), "duplicate fact_id between a canonical row and its variant"
    cites = [r["citation_ref"] for r in enriched]
    assert len(cites) == len(set(cites))
    # canonical identity is formula-free and equals the pre-I-22 hash input
    import hashlib
    canon = next(r for r in enriched if r["fact_subject"] == "MAR" and r["fact_key"] == "is_gandanta"
                 and not r.get("formula_id"))
    assert canon["fact_id"] == hashlib.sha256(
        "graha_gandanta|MAR|is_gandanta|c|lahiri_chitrapaksha".encode()).hexdigest()[:16]
    var = next(r for r in enriched if r["fact_subject"] == "MAR" and r["fact_key"] == "is_gandanta"
               and r.get("formula_id") == "strict_0_48")
    assert var["fact_id"] == hashlib.sha256(
        "graha_gandanta|MAR|is_gandanta|c|lahiri_chitrapaksha|strict_0_48".encode()).hexdigest()[:16]
    # honest tier: nothing re-derived these, so they stay at the default (never two_pass_verified)
    assert {r["verification_pass_status"] for r in enriched if r["fact_category"] == "graha_gandanta"} == {"single"}


def _structural_fallback(grahas: list[dict]):
    chart_output = {"grahas": grahas, "ascendant": {"longitude": 10.0, "sign": "Aries", "sign_id": 1}}
    return struct._build_dosha_rows(MagicMock(), chart_output, "c", "b", "lahiri_chitrapaksha",
                                    "2026-10-02T00:00:00+00:00", "test", dosha_catalog=None)


def test_structural_fallback_raises_when_the_shared_function_fails(monkeypatch):
    """SS ruling on PR #2892 (CLAUDE.md N.7 item 6): a failed evaluation is not 'no gandanta'.
    A raise in the shared Gandanta call inside the legacy dosha fallback must fail loudly,
    naming the dosha and the cause, never return 'not fired'."""
    def boom(sign_num, degree_in_sign):
        raise ValueError("wiring error")

    monkeypatch.setattr(struct, "_shared_check_gandanta", boom)
    with pytest.raises(RuntimeError) as ei:
        _structural_gandanta_fires(356.82)
    msg = str(ei.value)
    assert "GANDANTA_DOSHA could not be evaluated" in msg and "ValueError: wiring error" in msg
    assert "graha 'Mars'" in msg
    assert isinstance(ei.value.__cause__, ValueError)
    assert not hasattr(struct, "DOSHA_FALLBACK_EVAL_ERRORS")      # the count-and-continue counter is gone


def test_structural_fallback_raises_on_a_missing_or_bad_longitude():
    """No invented 0.0 (which would read as exactly on the Meena|Mesha cusp = gandanta)."""
    for bad in ({"name": "Mars", "house": 12}, {"name": "Mars", "longitude": None, "house": 12}):
        with pytest.raises(RuntimeError, match="could not be evaluated"):
            _structural_fallback([bad, {"name": "Sun", "longitude": 100.0, "house": 4, "sign": "Cancer"}])


def test_structural_fallback_raises_when_the_import_of_mrityu_bhaga_fails(monkeypatch):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "ga_writers.ga_sensitive_degree_writer":
            raise ImportError("simulated wiring error")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(RuntimeError, match="MRITYU_BHAGA_DOSHA could not be evaluated"):
        _structural_gandanta_fires(356.82)


def test_structural_fallback_ordinary_results_are_unchanged():
    """The ordinary no-gandanta and gandanta results keep working exactly as before."""
    assert _structural_gandanta_fires(100.0) is False
    assert _structural_gandanta_fires(356.82) is True
    assert _structural_gandanta_fires(10.0) is False


def test_insert_statement_selection_follows_formula_id():
    from pipeline.orchestrator.writers import ga_nakshatra as w
    assert "WHERE formula_id IS NULL" in w._INSERT_CANONICAL_SQL
    assert "formula_id)" not in w._INSERT_CANONICAL_SQL.split("VALUES")[0]      # canonical SQL never names the column
    assert "WHERE formula_id IS NOT NULL" in w._INSERT_VARIANT_SQL
    assert "build_id, formula_id)" in w._INSERT_VARIANT_SQL                      # the with_formula unique partition
