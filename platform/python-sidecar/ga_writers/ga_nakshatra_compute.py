"""
ga_writers.ga_nakshatra_compute — Pure nakshatra computation algorithms.

No DB access. No chart_facts rows. Only deterministic transformations:
  - KP Vimshottari sub-lord chain (star/sub/sub-sub/prana)
  - Gaṇḍānta detection with severity (arc-minutes from junction), computed by the ONE
    shared definition `brahmagyan.gandanta` (3°20' each side; the 0°48' reading is the
    named variant `strict_0_48`)
  - Tara bala per body from Moon's nakshatra
  - Nakshatra dispositor graph (chain + cycle detection)
"""
from __future__ import annotations

from brahmagyan.gandanta import locate_gandanta, locate_gandanta_strict

VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
PLANET_CYCLE: list[str] = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
]
NAK_SPAN_ARCMIN: float = 800.0   # 13°20' × 60 arcmin
TARA_NAMES: list[str] = [
    "Janma","Sampat","Vipat","Kshema","Pratyari",
    "Sadhaka","Vadha","Mitra","Atimitra",
]


def _nakshatra_0based(longitude: float) -> int:
    """0-based nakshatra index (0=Ashwini … 26=Revati) from sidereal longitude."""
    return int((longitude % 360.0) * 60.0 / NAK_SPAN_ARCMIN)


def _pos_in_nak_arcmin(longitude: float) -> float:
    """Arc-minutes elapsed within current nakshatra (0 to <800)."""
    return ((longitude % 360.0) * 60.0) % NAK_SPAN_ARCMIN


def compute_kp_lords(longitude: float) -> dict[str, str]:
    """
    Compute KP star-lord, sub-lord, sub-sub-lord, prana-lord
    from a sidereal body longitude (degrees).

    Algorithm: Vimshottari proportional subdivision (4 levels).
    Returns: {"star_lord": str, "sub_lord": str, "sub_sub_lord": str, "prana_lord": str}
    """
    nak0 = _nakshatra_0based(longitude)
    pos  = _pos_in_nak_arcmin(longitude)

    def _find_lord(start_planet: str, span_arcmin: float, pos_in_span: float) -> tuple[str, float, float]:
        """Return (lord, lord_span, pos_within_lord_span)."""
        start_idx = PLANET_CYCLE.index(start_planet)
        acc = 0.0
        for i in range(9):
            p = PLANET_CYCLE[(start_idx + i) % 9]
            p_span = VIMSHOTTARI_YEARS[p] / 120.0 * span_arcmin
            if acc + p_span > pos_in_span or i == 8:
                return p, p_span, pos_in_span - acc
            acc += p_span
        raise RuntimeError("KP lord not found")

    star_lord = PLANET_CYCLE[nak0 % 9]
    sub_lord,     sub_span,     pos_in_sub     = _find_lord(star_lord, NAK_SPAN_ARCMIN, pos)
    sub_sub_lord, sub_sub_span, pos_in_sub_sub = _find_lord(sub_lord,  sub_span,        pos_in_sub)
    prana_lord, _, _                            = _find_lord(sub_sub_lord, sub_sub_span, pos_in_sub_sub)

    return {
        "star_lord":     star_lord,
        "sub_lord":      sub_lord,
        "sub_sub_lord":  sub_sub_lord,
        "prana_lord":    prana_lord,
    }


def _gandanta_reading(located: dict) -> dict:
    """Project a `brahmagyan.gandanta.locate_gandanta*` result onto the four keys this
    asset has always stored (`is_gandanta`, `arc_minutes_from_junction`, `junction_type`,
    `side`)."""
    return {
        "is_gandanta":               located["fired"],
        "arc_minutes_from_junction": located["arc_minutes_from_junction"],
        "junction_type":             located["junction_type"],
        "side":                      located["side"],
    }


def compute_gandanta(longitude: float) -> dict:
    """
    Detect gaṇḍānta (water-fire nakshatra/rashi junction) for a longitude at the CANONICAL
    width: 3°20' each side of the junction, from the shared `brahmagyan.gandanta` module
    (the same function `ga_sensitive_degree` and `ga_structural` use).

    Returns:
      {
        "is_gandanta": bool,
        "arc_minutes_from_junction": float | None,
        "junction_type": str | None,   # "water_fire_0", "water_fire_120", "water_fire_240"
        "side": str | None,            # "approaching" or "departing"
      }
    """
    return _gandanta_reading(locate_gandanta(longitude))


def compute_gandanta_strict(longitude: float) -> dict:
    """
    The named stricter variant `strict_0_48` (formula_id): 0°48' each side of the junction.
    This is the reading `compute_gandanta` returned before decision sheet X1 (SS N-62);
    it is now emitted only as variant rows. Same four keys as `compute_gandanta`.
    """
    return _gandanta_reading(locate_gandanta_strict(longitude))


def compute_tara(nak_body_1based: int, nak_moon_1based: int) -> dict:
    """
    Tara bala for a body relative to Moon's nakshatra.

    count = ((nak_body - nak_moon) % 27) + 1  (1–27)
    tara_pos = ((count - 1) % 9) + 1          (1–9)
    """
    count    = ((nak_body_1based - nak_moon_1based) % 27) + 1
    tara_pos = ((count - 1) % 9) + 1
    return {
        "tara_count":    count,
        "tara_position": tara_pos,
        "tara_name":     TARA_NAMES[tara_pos - 1],
    }


def compute_dispositor_chain(
    body: str,
    nak_lord_map: dict[str, str],
    max_depth: int = 12,
) -> dict:
    """
    Walk the nakshatra dispositor chain for a body until terminus or cycle.

    nak_lord_map: {body_name: nakshatra_lord_name, ...} for all 10 bodies.
    A body that IS its own nakshatra lord is a terminus.
    Returns:
      {
        "chain": list[str],
        "terminus": str,
        "is_cycle": bool,
        "chain_depth": int,
      }
    """
    chain = [body]
    visited = {body}
    current = body

    for _ in range(max_depth):
        lord = nak_lord_map.get(current)
        if lord is None or lord == current:
            return {"chain": chain, "terminus": current, "is_cycle": False, "chain_depth": len(chain)}
        if lord in visited:
            chain.append(lord)
            return {"chain": chain, "terminus": lord, "is_cycle": True, "chain_depth": len(chain)}
        chain.append(lord)
        visited.add(lord)
        current = lord

    return {"chain": chain, "terminus": current, "is_cycle": False, "chain_depth": len(chain)}


def compute_center_of_gravity(
    chains: dict[str, dict],
) -> dict:
    """
    The nakshatra center-of-gravity: body that the most chains terminate on.
    Returns {"terminus_body": str, "chain_count": int}.
    """
    from collections import Counter
    counts: Counter = Counter()
    for body, chain_result in chains.items():
        terminus = chain_result.get("terminus")
        if terminus:
            counts[terminus] += 1
    if not counts:
        return {"terminus_body": None, "chain_count": 0}
    top_body, top_count = counts.most_common(1)[0]
    return {"terminus_body": top_body, "chain_count": top_count}


def compute_cross_ayanamsha_agreement(nak_ids: list[float]) -> tuple[int, int]:
    """
    NAR-GA fix (P2 :289 in ga_nakshatra.py). Returns (agree_cnt, total_ay) for
    the nak_5ay_consistency fact — how many of the (usually 5) sidereal
    ayanamsha computations for one graha agree on the same nakshatra id.

    Prior defect: the writer computed `agree_cnt = total_ay if len(unique) == 1
    else 0` — a full collapse to a literal 0 the instant ANY ayanamsha
    disagreed, even when e.g. 4 of 5 shared the same nakshatra. That 0 is
    narrated verbatim by registry_bridge.ts's readCrossAyanamshaFamily as
    "holds the SAME nakshatra in 0 of the 5 sidereal ayanamshas" — a false
    report of zero agreement when substantial (4/5) agreement existed.

    agree_cnt is the size of the largest agreeing subset (the mode count of
    nak_ids) — honest for the unanimous case (== total_ay), for every partial
    case, and for total disagreement (mode count == 1, not 0).
    """
    from collections import Counter
    total_ay = len(nak_ids)
    if not nak_ids:
        return 0, 0
    agree_cnt = Counter(nak_ids).most_common(1)[0][1]
    return agree_cnt, total_ay


def _self_check() -> None:
    # KP: Purva Bhadrapada (nakshatra 25, lord=Jupiter)
    # PBP spans from 24×13.333...° = 320° to 333.333°
    pbp_long = 322.0
    kp = compute_kp_lords(pbp_long)
    assert kp["star_lord"] == "Jupiter", f"Expected Jupiter star-lord at PBP, got {kp['star_lord']}"

    # Gaṇḍānta: 0.5° before Ashwini start (359.5° should be gandanta)
    g = compute_gandanta(359.5)
    assert g["is_gandanta"] is True
    assert g["side"] == "approaching"

    # Tara: Moon in PBP (nak 25), body in PBP (nak 25) → count=1 → Janma
    t = compute_tara(25, 25)
    assert t["tara_name"] == "Janma"

    # Cross-ayanamsha agreement: 4 of 5 share id 25.0, one is 26.0 —
    # agree_cnt must be 4 (the majority), never 0.
    agree_cnt, total_ay = compute_cross_ayanamsha_agreement([25.0, 25.0, 25.0, 25.0, 26.0])
    assert (agree_cnt, total_ay) == (4, 5), (
        f"Expected (4, 5) for 4-of-5 partial agreement, got ({agree_cnt}, {total_ay})"
    )

_self_check()
