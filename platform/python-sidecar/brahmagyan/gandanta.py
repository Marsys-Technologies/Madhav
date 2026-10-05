"""
brahmagyan.gandanta — THE one definition of Gandanta (the water->fire sandhi).

SINGLE SOURCE OF TRUTH for the canonical width, the junction table and the zone test.
Imported by the three L1 writers that state a Gandanta fact — ``ga_sensitive_degree``
(`sensitive_degree_check.gandanta`), ``ga_structural`` (the legacy ``GANDANTA_DOSHA``
fallback) and ``ga_nakshatra`` (`graha_gandanta`) — so that two L1 assets can never again
answer "is this graha in Gandanta" differently on the same chart (decision sheet A-4 / X1,
SS ruling N-62, Track I item I-22). ``ka_vighnakara`` (L3) reads the same definition today
through ``ga_writers.ga_sensitive_degree_writer`` (which re-exports ``GANDANTA_ARC``,
``GANDANTA_CITATION`` and ``check_gandanta`` from here, unchanged in shape) and may import
this module directly later without any change in behaviour.

WHY IT LIVES IN L0 (brahmagyan) rather than in any one writer: a Gandanta test is a
cross-layer contract (L1 states it, L3 windows it, L2 reads it). Same rationale as
``brahmagyan.domain_vocabulary``, ``brahmagyan.graha_vocabulary`` and
``brahmagyan.verification_vocab``. This module is deliberately a NEW file that imports
nothing from the repository (standard library only): no widely-imported L0 module is edited,
so no writer outside the three above moves its source digest through this change.

THE DEFINITION
--------------
Gandanta is the last ``GANDANTA_ARC`` of a water sign (Cancer, Scorpio, Pisces) together
with the first ``GANDANTA_ARC`` of the fire sign that follows (Leo, Sagittarius, Aries):
one contiguous zone of twice the arc around each of the three sign junctions
(Karka|Simha 120 deg, Vrischika|Dhanu 240 deg, Meena|Mesha 0 deg) = the Ashlesha|Magha,
Jyeshtha|Mula and Revati|Ashwini nakshatra junctions. The arc is one pada / one navamsa,
3 deg 20 min (= 10/3 deg = 200 arcmin = 30 deg / 9). Both edges are INCLUSIVE.

CITATION STATE (decision sheet A-4; nothing here is above ``sourced_ocr_unverified``)
  * 3 deg 20 min, water side  — ``sourced_ocr_unverified`` (BPHS, Santhanam trans.,
    ``bphs_pg0111_c01``: "the last Navamsas of Cancer, of Scorpio and of Pisces are called
    Gandanta").
  * 3 deg 20 min, fire side   — ``unsourced``: a symmetric convention (BPHS Ch. 92 states
    Lagna Gandanta in ghatikas, not degrees).
  * 0 deg 48 min              — ``unsourced`` (no passage in the code or the corpus search);
    kept ONLY as the named stricter variant ``strict_0_48``.
  * the "Sarvartha Chintamani" pointer inside ``GANDANTA_CITATION`` is ``unsourced`` (the
    corpus holds that text with no Gandanta passage found). The string is unchanged here so
    stored ``citation_human`` text does not move; the state is recorded, not hidden.

API (all pure; no database, no ephemeris)
  * ``GANDANTA_ARC``                — 3 deg 20 min as a float (``30.0 / 9.0``, the value the
                                      L1 writers have always used; edges are float-exact to it).
  * ``GANDANTA_ARC_EXACT``          — the same arc as ``Fraction(10, 3)`` for exact reasoning.
  * ``GANDANTA_ARC_ARCMIN``         — 200 (arcmin).
  * ``GANDANTA_STRICT_ARC`` / ``GANDANTA_STRICT_ARC_ARCMIN`` / ``GANDANTA_STRICT_FORMULA_ID``
                                    — the named 0 deg 48 min variant.
  * ``GANDANTA_JUNCTIONS``          — the three junctions (name, cusp longitude, water sign,
                                      fire sign) in ascending longitude order of the cusp.
  * ``GANDANTA_WATER_SIGNS`` / ``GANDANTA_FIRE_SIGNS`` — sign-number sets (0 = Aries).
  * ``check_gandanta(sign_num, degree_in_sign)`` — the canonical zone test in the shape
                                      ``ga_sensitive_degree`` has always stored (unchanged).
  * ``locate_gandanta(longitude_deg, arc_deg=None)`` — the same test from a sidereal
                                      longitude, returning junction, side and distance.
  * ``locate_gandanta_strict(longitude_deg)`` — ``locate_gandanta`` at the 0 deg 48 min arc.
"""
from __future__ import annotations

from fractions import Fraction
from typing import NamedTuple, Optional

# ── The canonical width ───────────────────────────────────────────────────────────────
# 3 deg 20 min = one pada = one navamsa = 30 deg / 9 = 10/3 deg = 200 arcmin.
# The float `30.0 / 9.0` is the exact expression the L1 writers have always used
# (3.3333333333333335); every edge comparison below is made against it, so moving the
# definition here changes no stored value.
GANDANTA_ARC: float = 30.0 / 9.0
GANDANTA_ARC_EXACT: Fraction = Fraction(10, 3)
GANDANTA_ARC_ARCMIN: int = 200

# ── The named stricter variant (formula_id) ───────────────────────────────────────────
# 0 deg 48 min on each side of the junction (the reading `ga_nakshatra` used to store
# unlabelled as `is_gandanta`). `unsourced` — kept only as a named variant (SS N-62, X1).
GANDANTA_STRICT_ARC_ARCMIN: float = 48.0
GANDANTA_STRICT_ARC: float = GANDANTA_STRICT_ARC_ARCMIN / 60.0
GANDANTA_STRICT_FORMULA_ID: str = "strict_0_48"

# Unchanged text of the writer's citation (see CITATION STATE above).
GANDANTA_CITATION: str = (
    "Classical gandanta (BPHS / Sarvartha Chintamani): last 3°20' of a water sign "
    "and first 3°20' of the succeeding fire sign — the Ashlesha-Magha, Jyeshtha-Mula "
    "and Revati-Ashwini nakshatra sandhi."
)

# Sign names, index 0 = Aries (the order every L1 writer uses; parity is asserted by
# tests/test_gandanta_shared_module.py against ga_sensitive_degree_writer.SIGNS).
_SIGN_NAMES: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


class GandantaJunction(NamedTuple):
    """One water|fire sign junction."""
    name: str            # `junction_type` value stored by ga_nakshatra since its first build
    cusp_deg: float      # sidereal longitude of the junction (0.0 = the Meena|Mesha cusp)
    water_sign: int      # sign number whose LAST arc is Gandanta (0 = Aries)
    fire_sign: int       # sign number whose FIRST arc is Gandanta
    nakshatra_pair: str  # the nakshatra junction (informational)


GANDANTA_JUNCTIONS: tuple[GandantaJunction, ...] = (
    GandantaJunction("water_fire_0",   0.0,   11, 0, "Revati|Ashwini"),     # Meena|Mesha
    GandantaJunction("water_fire_120", 120.0, 3,  4, "Ashlesha|Magha"),     # Karka|Simha
    GandantaJunction("water_fire_240", 240.0, 7,  8, "Jyeshtha|Mula"),      # Vrischika|Dhanu
)

GANDANTA_WATER_SIGNS: frozenset[int] = frozenset(j.water_sign for j in GANDANTA_JUNCTIONS)  # {3, 7, 11}
GANDANTA_FIRE_SIGNS: frozenset[int] = frozenset(j.fire_sign for j in GANDANTA_JUNCTIONS)    # {4, 8, 0}

_JUNCTION_BY_WATER = {j.water_sign: j for j in GANDANTA_JUNCTIONS}
_JUNCTION_BY_FIRE = {j.fire_sign: j for j in GANDANTA_JUNCTIONS}

SIDE_APPROACHING = "approaching"   # body is before the cusp (end of the water sign)
SIDE_DEPARTING = "departing"       # body is after the cusp (start of the fire sign)


def _classify(sign_num: int, degree_in_sign: float, arc: float):
    """Return (junction, side, distance_deg) when (sign, degree) is inside the arc, else None.

    Edges are inclusive on both sides: `degree >= 30 - arc` on the water side,
    `degree <= arc` on the fire side. This is the exact predicate `ga_sensitive_degree`
    has always used (with `arc = GANDANTA_ARC`).
    """
    if sign_num in GANDANTA_WATER_SIGNS and degree_in_sign >= (30.0 - arc):
        return _JUNCTION_BY_WATER[sign_num], SIDE_APPROACHING, 30.0 - degree_in_sign
    if sign_num in GANDANTA_FIRE_SIGNS and degree_in_sign <= arc:
        return _JUNCTION_BY_FIRE[sign_num], SIDE_DEPARTING, degree_in_sign
    return None


def check_gandanta(sign_num: int, degree_in_sign: float) -> dict:
    """Canonical (3 deg 20 min) zone test for a sign number and a degree within the sign.

    Fired iff the point is within the last arc of a water sign or the first arc of a
    fire sign. The returned dict is the shape `ga_sensitive_degree` stores in
    `value_jsonb` and `ka_vighnakara` reads; its keys and values are unchanged by the
    move into this module.
    """
    hit = _classify(sign_num, degree_in_sign, GANDANTA_ARC)
    dist = None
    zone = None
    if hit is not None:
        _junction, side, dist = hit
        zone = (f"end_of_{_SIGN_NAMES[sign_num]}" if side == SIDE_APPROACHING
                else f"start_of_{_SIGN_NAMES[sign_num]}")
    return {
        "fired": dist is not None,
        "gandanta_zone": zone,
        "distance_to_junction_deg": round(dist, 4) if dist is not None else None,
        "gandanta_arc_deg": round(GANDANTA_ARC, 4),
        "graha_deg_in_sign": round(degree_in_sign, 4),
        "sign": _SIGN_NAMES[sign_num],
    }


def locate_gandanta(longitude_deg: float, arc_deg: Optional[float] = None) -> dict:
    """Gandanta test from a sidereal longitude (degrees), at `arc_deg` each side.

    Default arc (None) = the canonical 3 deg 20 min, read from `GANDANTA_ARC` at call time, so `locate_gandanta(lon)["fired"]` equals
    `check_gandanta(int(lon // 30) % 12, lon % 30.0)["fired"]` by construction (same
    predicate). Returns:

      fired                      bool
      junction_type              "water_fire_0" | "water_fire_120" | "water_fire_240" | None
      junction_deg               cusp longitude of that junction | None
      junction_signs             (water sign number, fire sign number) | None
      side                       "approaching" (before the cusp) | "departing" (after) | None
      distance_deg               distance to the cusp, degrees | None
      arc_minutes_from_junction  distance_deg * 60 rounded to 2 places | None
      zone                       "end_of_<water sign>" | "start_of_<fire sign>" | None
      sign_num, degree_in_sign   the decomposition used
    """
    if arc_deg is None:
        arc_deg = GANDANTA_ARC
    lon = float(longitude_deg) % 360.0
    sign_num = int(lon // 30.0) % 12
    deg = lon % 30.0
    hit = _classify(sign_num, deg, arc_deg)
    base = {"sign_num": sign_num, "degree_in_sign": deg}
    if hit is None:
        return {"fired": False, "junction_type": None, "junction_deg": None,
                "junction_signs": None, "side": None, "distance_deg": None,
                "arc_minutes_from_junction": None, "zone": None, **base}
    junction, side, dist = hit
    zone = (f"end_of_{_SIGN_NAMES[sign_num]}" if side == SIDE_APPROACHING
            else f"start_of_{_SIGN_NAMES[sign_num]}")
    return {"fired": True, "junction_type": junction.name, "junction_deg": junction.cusp_deg,
            "junction_signs": (junction.water_sign, junction.fire_sign), "side": side,
            "distance_deg": dist, "arc_minutes_from_junction": round(dist * 60.0, 2),
            "zone": zone, **base}


def locate_gandanta_strict(longitude_deg: float) -> dict:
    """The named stricter variant `strict_0_48`: `locate_gandanta` at 0 deg 48 min each side."""
    return locate_gandanta(longitude_deg, GANDANTA_STRICT_ARC)


__all__ = [
    "GANDANTA_ARC", "GANDANTA_ARC_EXACT", "GANDANTA_ARC_ARCMIN",
    "GANDANTA_STRICT_ARC", "GANDANTA_STRICT_ARC_ARCMIN", "GANDANTA_STRICT_FORMULA_ID",
    "GANDANTA_CITATION", "GandantaJunction", "GANDANTA_JUNCTIONS",
    "GANDANTA_WATER_SIGNS", "GANDANTA_FIRE_SIGNS", "SIDE_APPROACHING", "SIDE_DEPARTING",
    "check_gandanta", "locate_gandanta", "locate_gandanta_strict",
]
