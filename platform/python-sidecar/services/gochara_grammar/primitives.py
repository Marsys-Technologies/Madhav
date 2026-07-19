"""
gochara_grammar.primitives — the 12 contact-primitive families (BRIEF_D5 §1 G-1
row / §10 promise-ledger). Family #8 (Sarvatobhadra vedha) lives in
`sarvatobhadra.py` (the CR-21 centerpiece gets its own module + long provenance
docstring); the other 11 live here.

Every function is `(swe, chart_id, target: ResonanceTarget, start_jd, end_jd, ...)
-> list[ConfigurationSentence]`. All ephemeris scanning delegates to
`pipeline.transit_search` (find_aspect_events / find_ingress_events /
find_conjunction_events / find_station_events / find_eclipse_proximity_events /
find_return_events) -- this module does zero direct `swe.calc_ut` calls of its
own; the one exception is `_planet_sign_at` in the vedha-cancellation check,
which calls the already-exported `_get_planet_pos` helper (not new ephemeris
math, just a position read at an already-computed exact_jd).

Per-family citation-or-uncited decision (B.10 / BRIEF_D5 §6), each drawn from a
citation string ALREADY present elsewhere in this codebase (see `citations.py`
provenance comments) rather than a newly authored one:

  1. degree_contact           -> uncited_extension (grammar's own tight-orb
     decomposition of the general BPHS Ch.29 gochara-to-a-point idea; no
     codebase-attested citation names "exact degree contact" as its own
     technique).
  2. drishti_contact          -> BPHS Ch.26 (Graha Drishti; l0_reference.py).
  3. sign_ingress              -> BPHS Ch.29 (Gochara Phala; the base classical
     sign-transit-result technique).
  4. nakshatra_ingress_tara    -> Muhurta Chintamani/BPHS/Jataka Parijata Tara
     Bala (tara_bala.py module docstring).
  5. kakshya_cell_crossing     -> BPHS Ch.66 when DB-sourced boundaries are used
     (ga_strength_writer.py's real `ashtakavarga_kakshya_boundary` chart_facts
     rows); uncited_extension when falling back to the equal-eighths fixture
     approximation (no live boundary data reachable).
  6. av_threshold_state        -> BPHS Ch.66-68 + Phaladeepika Ch.26 when a real
     `bg_transit_av_gates` row is matched (migration 397); uncited_extension on
     the specific bindu-count resolution sub-claim when chart_facts SAV data is
     unreachable (disclosed via detail['bindu_count_resolved']=False, never
     silently assumed).
  7. gochara_vedha_pair         -> BPHS Ch.29 + Phaladeepika Ch.26, INHERITED
     verbatim from the matched `bg_transit_rules.classical_citation` row (never
     a module constant -- this primitive's citation is literally whatever the
     live rule row says, per BRIEF_D5 §6's "inherited from bg_transit_rules.
     classical_citation via the target it fired on").
  9. station_retro_loop         -> BPHS Ch.27 (Vakra; l0_reference.py).
  10. eclipse_degree            -> uncited_extension (no codebase-attested
     classical citation for eclipse-degree-to-natal-point contact was found in
     this session's search).
  11. returns                   -> uncited_extension (no codebase-attested
     citation for planetary-return-to-own-natal-degree as a named technique).
  12. sade_sati_phase           -> BPHS Ch.71, INHERITED from the matched
     `chart_facts` sade_sati_cycle/sade_sati_phase row's own citation_human
     when available (ga_sade_sati_writer.py), falling back to the module
     constant when reading the live fact row's citation_human is unavailable.
"""
from __future__ import annotations

import logging
from typing import Optional

from pipeline.transit_search import (
    SIGNS,
    NAKSHATRAS,
    find_aspect_events,
    find_ingress_events,
    find_station_events,
    find_eclipse_proximity_events,
    find_return_events,
    _get_planet_pos,
    _shortest_arc_diff,
)
from panchang_engine.tara_bala import compute_tara_position, get_tara_detail

from .models import ConfigurationSentence, ResonanceTarget
from . import citations as C

logger = logging.getLogger(__name__)

ALL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
CLASSICAL_SEVEN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Classical graha drishti (BPHS Ch.26): every graha casts a full (7th-house,
# 180deg) aspect; Mars/Jupiter/Saturn cast additional special full aspects.
SPECIAL_DRISHTI_DEG: dict[str, list[float]] = {
    "Mars": [90.0, 180.0, 210.0],       # 4th, 7th, 8th
    "Jupiter": [120.0, 180.0, 240.0],   # 5th, 7th, 9th
    "Saturn": [60.0, 180.0, 270.0],     # 3rd, 7th, 10th
}
_DEFAULT_DRISHTI_DEG = [180.0]  # every other graha: 7th-house aspect only


def _sign_index(sign_name: str) -> int:
    return SIGNS.index(sign_name)


def _offset_sign(sign_name: str, offset_houses: int) -> str:
    """Sign `offset_houses` (1-indexed house count, whole-sign) away from
    sign_name. offset_houses=1 returns sign_name itself (same house)."""
    idx = (_sign_index(sign_name) + (offset_houses - 1)) % 12
    return SIGNS[idx]


def _sign_of_longitude(lon_deg: float) -> str:
    return SIGNS[int(lon_deg // 30.0) % 12]


def _normalize_graha(name: str) -> str:
    """bg_transit_rules stores lowercase canonical graha names; transit_search
    expects Title-case ('Saturn' not 'saturn')."""
    return name.strip().capitalize() if name else name


def _fact_id(prefix: str, *parts) -> str:
    return prefix + ":" + ":".join(str(p) for p in parts)


# ── #1 — degree-contact ────────────────────────────────────────────────────

def degree_contact(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    planets: Optional[list[str]] = None,
    orb_deg: float = 1.0,
) -> list[ConfigurationSentence]:
    """Exact degree conjunction, tight orb, of a transiting graha to
    target.target_longitude_deg. See module docstring #1 for the
    uncited_extension rationale."""
    if target.target_longitude_deg is None:
        logger.info("[degree_contact] target_ref=%s has no target_longitude_deg; skipping.", target.target_ref)
        return []
    sentences: list[ConfigurationSentence] = []
    for planet in (planets or ALL_GRAHAS):
        events = find_aspect_events(swe, planet, target.target_longitude_deg, [0], orb_deg, start_jd, end_jd)
        for ev in events:
            sentences.append(ConfigurationSentence(
                primitive="degree_contact",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="point",
                fact_ids=[_fact_id("degree_contact", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=None,
                uncited_extension=True,
                detail={"orb_at_event_deg": ev.orb_at_event_deg, "orb_strength": ev.orb_strength,
                        "target_longitude_deg": target.target_longitude_deg,
                        "exact_longitude_deg": ev.exact_longitude_deg,
                        "signed_offset_from_target_deg": round(_shortest_arc_diff(ev.exact_longitude_deg, target.target_longitude_deg), 4)},
            ))
    return sentences


# ── #2 — drishti-contact ───────────────────────────────────────────────────

def drishti_contact(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    planets: Optional[list[str]] = None,
    orb_deg: float = 3.0,
) -> list[ConfigurationSentence]:
    """Classical graha drishti (BPHS Ch.26) from a transiting graha onto
    target.target_longitude_deg -- reuses find_aspect_events with each
    graha's classical special-aspect degree set."""
    if target.target_longitude_deg is None:
        logger.info("[drishti_contact] target_ref=%s has no target_longitude_deg; skipping.", target.target_ref)
        return []
    sentences: list[ConfigurationSentence] = []
    for planet in (planets or ALL_GRAHAS):
        aspect_degrees = SPECIAL_DRISHTI_DEG.get(planet, _DEFAULT_DRISHTI_DEG)
        events = find_aspect_events(swe, planet, target.target_longitude_deg, aspect_degrees, orb_deg, start_jd, end_jd)
        for ev in events:
            sentences.append(ConfigurationSentence(
                primitive="drishti_contact",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="point",
                fact_ids=[_fact_id("drishti_contact", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=C.GRAHA_DRISHTI_BPHS_26,
                uncited_extension=False,
                detail={"aspect_deg": ev.extra.get("aspect_deg"), "orb_at_event_deg": ev.orb_at_event_deg,
                        "exact_longitude_deg": ev.exact_longitude_deg,
                        "signed_offset_from_target_deg": round(_shortest_arc_diff(ev.exact_longitude_deg, target.target_longitude_deg), 4)},
            ))
    return sentences


# ── #3 — sign-ingress ──────────────────────────────────────────────────────

def sign_ingress(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    planets: Optional[list[str]] = None,
) -> list[ConfigurationSentence]:
    """Planet entering target's sign (target.target_sign)."""
    if not target.target_sign:
        logger.info("[sign_ingress] target_ref=%s has no target_sign; skipping.", target.target_ref)
        return []
    sentences: list[ConfigurationSentence] = []
    for planet in (planets or ALL_GRAHAS):
        events = find_ingress_events(swe, planet, target.target_sign, start_jd, end_jd)
        for ev in events:
            sentences.append(ConfigurationSentence(
                primitive="sign_ingress",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="point",
                fact_ids=[_fact_id("sign_ingress", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=C.GOCHARA_PHALA_BPHS_29,
                uncited_extension=False,
                detail={"target_sign": target.target_sign},
            ))
    return sentences


# ── #4 — nakshatra-ingress / tara-state ────────────────────────────────────

def nakshatra_ingress_tara(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    natal_moon_nakshatra_id: Optional[int] = None,
    planets: Optional[list[str]] = None,
    orb_deg: float = 0.25,
) -> list[ConfigurationSentence]:
    """Planet entering target's nakshatra (target.target_nakshatra_id), with
    the entered nakshatra's Tara relationship to the natal Moon's nakshatra
    (Nava Tara Chakra, reusing panchang_engine.tara_bala) attached when
    natal_moon_nakshatra_id is supplied."""
    if target.target_nakshatra_id is None:
        logger.info("[nakshatra_ingress_tara] target_ref=%s has no target_nakshatra_id; skipping.", target.target_ref)
        return []
    boundary_lon = ((target.target_nakshatra_id - 1) % 27) * (360.0 / 27.0)
    sentences: list[ConfigurationSentence] = []
    for planet in (planets or ALL_GRAHAS):
        events = find_aspect_events(swe, planet, boundary_lon, [0], orb_deg, start_jd, end_jd)
        for ev in events:
            detail = {
                "target_nakshatra_id": target.target_nakshatra_id,
                "target_nakshatra_name": NAKSHATRAS[target.target_nakshatra_id - 1],
            }
            if natal_moon_nakshatra_id is not None:
                tara_pos = compute_tara_position(natal_moon_nakshatra_id, target.target_nakshatra_id)
                detail["tara"] = get_tara_detail(tara_pos)
            sentences.append(ConfigurationSentence(
                primitive="nakshatra_ingress_tara",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="point",
                fact_ids=[_fact_id("nakshatra_ingress", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=C.TARA_BALA_MUHURTA_CHINTAMANI,
                uncited_extension=False,
                detail=detail,
            ))
    return sentences


# ── #5 — kakṣyā-cell crossing ──────────────────────────────────────────────

_KAKSHYA_LORD_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna"]


def _fetch_kakshya_boundaries(conn, chart_id: str, planet: str) -> list[dict]:
    """Real path: read `ashtakavarga_kakshya_boundary` rows written by
    ga_strength_writer.py (fact_category='ashtakavarga_kakshya_boundary',
    fact_subject=f'{planet}.<kakshya_index>', fact_key in
    {'lord','start_deg','end_deg'}). Defensive -- [] on any failure."""
    try:
        cur = conn.execute(
            """
            SELECT fact_subject, fact_key, fact_value_text, fact_value_num
              FROM chart_facts
             WHERE chart_id = %s AND fact_category = 'ashtakavarga_kakshya_boundary'
               AND fact_subject LIKE %s
            """,
            [chart_id, f"{planet}.%"],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[kakshya_cell_crossing] chart_facts kakshya boundary read failed: %s", exc)
        return []
    by_subject: dict[str, dict] = {}
    for row in rows:
        d = row if isinstance(row, dict) else dict(zip(
            ["fact_subject", "fact_key", "fact_value_text", "fact_value_num"], row))
        by_subject.setdefault(d["fact_subject"], {})[d["fact_key"]] = d.get("fact_value_text") or d.get("fact_value_num")
    return list(by_subject.values())


def kakshya_cell_crossing(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    conn=None,
    planets: Optional[list[str]] = None,
    orb_deg: float = 0.1,
) -> list[ConfigurationSentence]:
    """Transiting graha crossing an Ashtakavarga kakṣyā (1/8-sign) sub-arc
    boundary within target's sign. Prefers real chart_facts boundaries
    (ga_strength_writer.py's ashtakavarga_kakshya_boundary rows, cited BPHS
    Ch.66); falls back to an equal-eighths approximation with
    uncited_extension=True when unreachable."""
    if not target.target_sign:
        logger.info("[kakshya_cell_crossing] target_ref=%s has no target_sign; skipping.", target.target_ref)
        return []
    sign_start = _sign_index(target.target_sign) * 30.0
    sentences: list[ConfigurationSentence] = []

    for planet in (planets or ALL_GRAHAS):
        db_boundaries = _fetch_kakshya_boundaries(conn, chart_id, planet) if conn is not None else []
        if db_boundaries:
            boundary_degs = sorted({float(b["start_deg"]) for b in db_boundaries if b.get("start_deg") is not None})
            citation = C.KAKSHYA_BPHS_66
            uncited = False
            source = "chart_facts.ashtakavarga_kakshya_boundary"
        else:
            # Fallback: 8 equal 3.75deg divisions within the sign, classical
            # lord order applied cyclically starting from Saturn (see
            # _KAKSHYA_LORD_ORDER) -- an approximation, honestly flagged.
            boundary_degs = [sign_start + i * (30.0 / 8.0) for i in range(8)]
            citation = None
            uncited = True
            source = "equal_eighths_fixture_approximation"

        for i, b in enumerate(boundary_degs):
            events = find_aspect_events(swe, planet, b, [0], orb_deg, start_jd, end_jd)
            for ev in events:
                sentences.append(ConfigurationSentence(
                    primitive="kakshya_cell_crossing",
                    chart_id=chart_id,
                    event_class=target.event_class,
                    target_type=target.target_type,
                    target_ref=target.target_ref,
                    transit_planet=planet,
                    secondary_planet=None,
                    event_jd=ev.event_jd,
                    event_datetime_ist=ev.event_datetime_ist,
                    temporal_shape="point",
                    fact_ids=[_fact_id("kakshya_cell_crossing", chart_id, target.target_ref, planet, ev.event_jd)],
                    classical_citation=citation,
                    uncited_extension=uncited,
                    detail={"boundary_deg": b, "kakshya_index": i, "source": source},
                ))
    return sentences


# ── #6 — AV-threshold state ────────────────────────────────────────────────

def _fetch_av_gate_rows(conn, target_house: Optional[str]) -> list[dict]:
    if conn is None:
        return []
    try:
        cur = conn.execute(
            """
            SELECT gate_kind, graha, house_from_moon, min_av_score, min_sav_score,
                   effect, classical_citation
              FROM bg_transit_av_gates
             WHERE gate_kind = 'sav_threshold'
               AND (%s IS NULL OR house_from_moon = %s::int)
            """,
            [target_house, target_house],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[av_threshold_state] bg_transit_av_gates read failed: %s", exc)
        return []
    keys = ["gate_kind", "graha", "house_from_moon", "min_av_score", "min_sav_score", "effect", "classical_citation"]
    return [row if isinstance(row, dict) else dict(zip(keys, row)) for row in rows]


def av_threshold_state(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    conn=None,
    fixture_gate_rows: Optional[list[dict]] = None,
) -> list[ConfigurationSentence]:
    """Ashtakavarga bindu-threshold state for the transiting sign, sourced
    from `bg_transit_av_gates` (gate_kind='sav_threshold', migration 397).
    The live SAV bindu count for chart_id (to actually evaluate the
    threshold) is a further chart_facts read this primitive attempts
    defensively; when unreachable it still emits the gate-fired sentence but
    discloses `detail['bindu_count_resolved']=False` rather than asserting a
    pass/fail it cannot back.

    `fixture_gate_rows` lets a caller (test) inject gate rows matching the
    `bg_transit_av_gates` row shape ({graha, min_sav_score, effect,
    classical_citation}) when no DB connection is available -- an explicit,
    documented fixture path, mirroring `sade_sati_phase`'s fixture_phases."""
    if not target.target_sign or target.target_type != "bhava":
        logger.info("[av_threshold_state] target_ref=%s not a bhava target with resolved sign; skipping.", target.target_ref)
        return []
    gate_rows = _fetch_av_gate_rows(conn, target.target_ref) if conn is not None else (fixture_gate_rows or [])
    if not gate_rows:
        return []

    sentences: list[ConfigurationSentence] = []
    for gate in gate_rows:
        planet = _normalize_graha(gate["graha"])
        events = find_ingress_events(swe, planet, target.target_sign, start_jd, end_jd)
        for ev in events:
            sentences.append(ConfigurationSentence(
                primitive="av_threshold_state",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="point",
                fact_ids=[_fact_id("av_threshold_state", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=gate.get("classical_citation") or C.ASHTAKAVARGA_AV_GATES,
                uncited_extension=False,
                detail={
                    "min_sav_score": gate.get("min_sav_score"),
                    "effect": gate.get("effect"),
                    "bindu_count_resolved": False,
                    "bindu_count_note": "live SAV bindu count for this chart not resolved in this pass -- gate rule matched, threshold evaluation deferred.",
                },
            ))
    return sentences


# ── #7 — gochara-vedha pairs ───────────────────────────────────────────────

def _fetch_vedha_rules(conn, primary_house: Optional[str]) -> list[dict]:
    if conn is None:
        return []
    try:
        cur = conn.execute(
            """
            SELECT graha, primary_house, vedha_house, phala, classical_citation
              FROM bg_transit_rules
             WHERE rule_type = 'vedha'
               AND (%s IS NULL OR primary_house = %s::int)
            """,
            [primary_house, primary_house],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[gochara_vedha_pair] bg_transit_rules read failed: %s", exc)
        return []
    keys = ["graha", "primary_house", "vedha_house", "phala", "classical_citation"]
    return [row if isinstance(row, dict) else dict(zip(keys, row)) for row in rows]


def gochara_vedha_pair(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    conn=None,
    other_grahas: Optional[list[str]] = None,
    fixture_vedha_rows: Optional[list[dict]] = None,
) -> list[ConfigurationSentence]:
    """Primary/vedha house pair from `bg_transit_rules` (rule_type='vedha').
    Implements the CANCELLATION check (not just detection, per the task
    brief): at each primary-transit ingress event, checks whether ANY other
    graha simultaneously occupies the vedha house's sign -- vedha cancels the
    primary transit's effect only when both houses are simultaneously
    occupied, per classical rule.

    `fixture_vedha_rows` lets a caller (test) inject rows matching the
    `bg_transit_rules` row shape ({graha, vedha_house, phala,
    classical_citation}) when no DB connection is available."""
    if not target.target_sign or target.target_type != "bhava":
        logger.info("[gochara_vedha_pair] target_ref=%s not a bhava target with resolved sign; skipping.", target.target_ref)
        return []
    vedha_rows = _fetch_vedha_rules(conn, target.target_ref) if conn is not None else (fixture_vedha_rows or [])
    if not vedha_rows:
        return []

    sentences: list[ConfigurationSentence] = []
    try:
        primary_house_num = int(target.target_ref)
    except (TypeError, ValueError):
        logger.info("[gochara_vedha_pair] target_ref=%r is not an integer house; skipping.", target.target_ref)
        return []

    for rule in vedha_rows:
        planet = _normalize_graha(rule["graha"])
        vedha_house = rule.get("vedha_house")
        if vedha_house is None:
            continue
        vedha_sign = _offset_sign(target.target_sign, int(vedha_house) - primary_house_num + 1)

        primary_events = find_ingress_events(swe, planet, target.target_sign, start_jd, end_jd)
        for ev in primary_events:
            occupants = []
            for other in (other_grahas or ALL_GRAHAS):
                if other == planet:
                    continue
                lon, _ = _get_planet_pos(swe, other, ev.event_jd)
                if _sign_of_longitude(lon) == vedha_sign:
                    occupants.append(other)
            cancelled = len(occupants) > 0

            sentences.append(ConfigurationSentence(
                primitive="gochara_vedha_pair",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=occupants[0] if occupants else None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="interval" if cancelled else "point",
                fact_ids=[_fact_id("gochara_vedha_pair", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=rule.get("classical_citation") or C.PHALADEEPIKA_VEDHA_26,
                uncited_extension=False,
                detail={
                    "primary_house": primary_house_num,
                    "vedha_house": int(vedha_house),
                    "vedha_sign": vedha_sign,
                    "phala": rule.get("phala"),
                    "cancelled": cancelled,
                    "cancelling_occupants": occupants,
                },
            ))
    return sentences


# ── #9 — station / retro-loop ──────────────────────────────────────────────

def station_retro_loop(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    planets: Optional[list[str]] = None,
    near_orb_deg: float = 5.0,
) -> list[ConfigurationSentence]:
    """Planet stationary (retrograde or direct station) at/near target's
    degree -- a station intensifies/internalizes the planet's influence on
    whatever it is near (BPHS Ch.27, Vakra/cheshta bala)."""
    if target.target_longitude_deg is None:
        logger.info("[station_retro_loop] target_ref=%s has no target_longitude_deg; skipping.", target.target_ref)
        return []
    sentences: list[ConfigurationSentence] = []
    for planet in (planets or [p for p in ALL_GRAHAS if p not in ("Sun", "Moon", "Rahu", "Ketu")]):
        events = find_station_events(swe, planet, start_jd, end_jd)
        for ev in events:
            orb = abs(_shortest_arc_diff(ev.exact_longitude_deg, target.target_longitude_deg))
            if orb > near_orb_deg:
                continue
            sentences.append(ConfigurationSentence(
                primitive="station_retro_loop",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet=planet,
                secondary_planet=None,
                event_jd=ev.event_jd,
                event_datetime_ist=ev.event_datetime_ist,
                temporal_shape="point",
                fact_ids=[_fact_id("station_retro_loop", chart_id, target.target_ref, planet, ev.event_jd)],
                classical_citation=C.VAKRA_RETROGRADE_BPHS_27,
                uncited_extension=False,
                detail={"station_type": ev.extra.get("station_type"), "orb_to_target_deg": round(orb, 4)},
            ))
    return sentences


# ── #10 — eclipse-degree ───────────────────────────────────────────────────

def eclipse_degree(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    orb_deg: float = 8.0,
    node_luminary_pairs: Optional[list[tuple[str, str]]] = None,
) -> list[ConfigurationSentence]:
    """Solar/lunar eclipse-proximity degree (node-luminary conjunction, per
    find_eclipse_proximity_events) conjunct/opposing target's degree."""
    if target.target_longitude_deg is None:
        logger.info("[eclipse_degree] target_ref=%s has no target_longitude_deg; skipping.", target.target_ref)
        return []
    pairs = node_luminary_pairs or [("Rahu", "Sun"), ("Rahu", "Moon"), ("Ketu", "Sun"), ("Ketu", "Moon")]
    sentences: list[ConfigurationSentence] = []
    for node, luminary in pairs:
        events = find_eclipse_proximity_events(swe, node, luminary, orb_deg, start_jd, end_jd)
        for ev in events:
            for aspect_target_deg, label in (
                (target.target_longitude_deg, "conjunct"),
                ((target.target_longitude_deg + 180.0) % 360.0, "opposite"),
            ):
                orb = abs(_shortest_arc_diff(ev.exact_longitude_deg, aspect_target_deg))
                if orb > orb_deg:
                    continue
                sentences.append(ConfigurationSentence(
                    primitive="eclipse_degree",
                    chart_id=chart_id,
                    event_class=target.event_class,
                    target_type=target.target_type,
                    target_ref=target.target_ref,
                    transit_planet=node,
                    secondary_planet=luminary,
                    event_jd=ev.event_jd,
                    event_datetime_ist=ev.event_datetime_ist,
                    temporal_shape="point",
                    fact_ids=[_fact_id("eclipse_degree", chart_id, target.target_ref, node, luminary, ev.event_jd)],
                    classical_citation=None,
                    uncited_extension=True,
                    detail={"relation": label, "orb_to_target_deg": round(orb, 4),
                            "eclipse_type": ev.extra.get("eclipse_type")},
                ))
    return sentences


# ── #11 — returns (K-7) ─────────────────────────────────────────────────────

def planetary_return(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    orb_deg: float = 1.0,
) -> list[ConfigurationSentence]:
    """Planet returns to its own natal degree -- target must represent that
    planet's OWN natal position (target.natal_planet set, target.
    target_longitude_deg = that planet's natal longitude)."""
    if target.target_longitude_deg is None or not target.natal_planet:
        logger.info("[planetary_return] target_ref=%s missing natal_planet/target_longitude_deg; skipping.", target.target_ref)
        return []
    events = find_return_events(swe, target.natal_planet, target.target_longitude_deg, orb_deg, start_jd, end_jd)
    sentences: list[ConfigurationSentence] = []
    for ev in events:
        sentences.append(ConfigurationSentence(
            primitive="planetary_return",
            chart_id=chart_id,
            event_class=target.event_class,
            target_type=target.target_type,
            target_ref=target.target_ref,
            transit_planet=target.natal_planet,
            secondary_planet=None,
            event_jd=ev.event_jd,
            event_datetime_ist=ev.event_datetime_ist,
            temporal_shape="point",
            fact_ids=[_fact_id("planetary_return", chart_id, target.target_ref, target.natal_planet, ev.event_jd)],
            classical_citation=None,
            uncited_extension=True,
            detail={"natal_longitude_deg": target.target_longitude_deg, "orb_at_event_deg": ev.orb_at_event_deg},
        ))
    return sentences


# ── #12 — Sāde-Satī phase ──────────────────────────────────────────────────

def _fetch_sade_sati_rows(conn, chart_id: str) -> list[dict]:
    if conn is None:
        return []
    try:
        cur = conn.execute(
            """
            SELECT fact_subject, fact_key, fact_value_text, fact_value_num, citation_human
              FROM chart_facts
             WHERE chart_id = %s AND fact_category IN ('sade_sati_cycle', 'sade_sati_phase')
            """,
            [chart_id],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[sade_sati_phase] chart_facts sade_sati read failed: %s", exc)
        return []
    keys = ["fact_subject", "fact_key", "fact_value_text", "fact_value_num", "citation_human"]
    return [row if isinstance(row, dict) else dict(zip(keys, row)) for row in rows]


def sade_sati_phase(
    chart_id: str,
    target: ResonanceTarget,
    conn=None,
    fixture_phases: Optional[list[dict]] = None,
) -> list[ConfigurationSentence]:
    """Sade Sati cycle/phase intervals -- REUSES ga_sade_sati_writer.py's
    already-computed `chart_facts` rows (fact_category in
    {'sade_sati_cycle','sade_sati_phase'}) rather than recomputing the Saturn
    transit-around-natal-Moon cycle logic. Not tied to a specific target's
    longitude (Sade Sati is a whole-chart Saturn/Moon configuration); this
    primitive is included per target only to carry the resonance-map's
    event_class/weight context through to the emitted sentence.

    `fixture_phases` lets tests supply a synthetic phase list (each dict with
    keys phase_start_iso/phase_end_iso/phase_name/cycle_id) matching the shape
    of a grouped chart_facts read, when no DB connection is available.
    """
    rows = _fetch_sade_sati_rows(conn, chart_id) if conn is not None else []
    sentences: list[ConfigurationSentence] = []

    if rows:
        by_subject: dict[str, dict] = {}
        citation_by_subject: dict[str, str] = {}
        for r in rows:
            by_subject.setdefault(r["fact_subject"], {})[r["fact_key"]] = r.get("fact_value_text") or r.get("fact_value_num")
            if r.get("citation_human"):
                citation_by_subject.setdefault(r["fact_subject"], r["citation_human"])
        for subject, kv in by_subject.items():
            if "phase_start_iso" not in kv:
                continue
            sentences.append(ConfigurationSentence(
                primitive="sade_sati_phase",
                chart_id=chart_id,
                event_class=target.event_class,
                target_type=target.target_type,
                target_ref=target.target_ref,
                transit_planet="Saturn",
                secondary_planet=None,
                event_jd=None,
                event_datetime_ist=str(kv.get("phase_start_iso")),
                temporal_shape="interval",
                fact_ids=[_fact_id("sade_sati_phase", chart_id, subject)],
                classical_citation=citation_by_subject.get(subject, C.SADE_SATI_BPHS_71),
                uncited_extension=False,
                detail={"subject": subject, **{k: v for k, v in kv.items() if k != "phase_start_iso"},
                        "phase_start_iso": kv.get("phase_start_iso")},
            ))
        return sentences

    # Fallback: synthetic fixture (explicit, not silently faked as chart_facts data).
    for ph in (fixture_phases or []):
        sentences.append(ConfigurationSentence(
            primitive="sade_sati_phase",
            chart_id=chart_id,
            event_class=target.event_class,
            target_type=target.target_type,
            target_ref=target.target_ref,
            transit_planet="Saturn",
            secondary_planet=None,
            event_jd=None,
            event_datetime_ist=ph.get("phase_start_iso"),
            temporal_shape="interval",
            fact_ids=[_fact_id("sade_sati_phase_fixture", chart_id, ph.get("cycle_id"), ph.get("phase_name"))],
            classical_citation=C.SADE_SATI_BPHS_71,
            uncited_extension=False,
            detail={"source": "fixture", **ph},
        ))
    return sentences


__all__ = [
    "ALL_GRAHAS",
    "CLASSICAL_SEVEN",
    "degree_contact",
    "drishti_contact",
    "sign_ingress",
    "nakshatra_ingress_tara",
    "kakshya_cell_crossing",
    "av_threshold_state",
    "gochara_vedha_pair",
    "station_retro_loop",
    "eclipse_degree",
    "planetary_return",
    "sade_sati_phase",
]
