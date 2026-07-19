"""
gochara_grammar.sarvatobhadra — the CR-21 completion: Sarvatobhadra Chakra
vedha-cancellation primitive (G-2's classical centerpiece, BRIEF_D5 §1/§2/§10).

Prior-art search (done before writing this module, per the task brief's
"search the codebase for any existing partial Sarvatobhadra Chakra
implementation first" instruction):

  - `platform/migrations/_archive/140_sarvatobhadra_chakra.sql` creates
    `l1_sarvatobhadra_positions` (28 nakshatra grid-cell rows) and
    `l1_sarvatobhadra_vedha` (14 vedha pairs), both schema-only -- NO INSERT
    statements in that migration or in `144_vedha_extended.sql`'s
    `l1_vedha_extended` follow-on. Confirmed by grep: zero `^INSERT` lines in
    either file. No Python or TypeScript code anywhere in the repo reads
    `l1_sarvatobhadra_*` (also confirmed by grep). So: the SCHEMA exists
    (applied historically per `platform/migrations/README.md` -- this
    directory holds already-applied legacy migrations, read by `migrate.ts`
    alongside `platform/supabase/migrations/`), but there is no populated
    grid data and no prior computation of the vedha-cancellation logic
    anywhere in the codebase. This module is a genuine first implementation,
    not a duplicate of existing work.
  - `ga_sensitive_degree_writer.py` (L1 GA-10) writes a `sarvatobhadra_vedha`
    *evidence* row per chart (natal nakshatra occupancy only) but explicitly
    documents "the full 28-nakshatra SBC rekha/kona/vithi vedha table is not
    in L1" -- it defers the actual grid geometry, same gap this module fills
    for the TRANSIT (gochara) side.
  - `bg_transit_rules` (rule_type='vedha') carries the *general* Gochara
    primary/vedha HOUSE pairs (BPHS Ch.29 + Phaladeepika Ch.26) -- that is a
    coarser, already-implemented mechanism, reused as-is by
    `primitives.gochara_vedha_pair` (primitive family #7). Sarvatobhadra is
    the finer-grained, NAKSHATRA-level vedha geometry BPHS's Gochara chapter
    does not itself specify (the SBC is documented separately, in Muhurta
    Chintamani / Jyotish Sara Sangraha per the migration's own table
    comments) -- these are two distinct classical techniques, not the same
    rule at two granularities.

Because no verified, populated classical vedha-PAIR table exists anywhere in
this codebase or reachable this session, this module's nakshatra-vedha
pairing is computed by an ALGORITHMIC approximation rather than a memorized
28-cell grid lookup: the vedha nakshatra of nakshatra N is taken as the
nakshatra 14 positions away in the 27-nakshatra cycle (the nearest integer
approximation of the 180°-opposition point, 360°/27°/2 = 13.5 -> 14). This
approximates the SBC's classical "opposite-in-the-grid" relationship without
reproducing the grid's actual (non-uniform, geometry-dependent) row/column
adjacency -- so it is NOT presented as a verified reproduction of the
classical 9×9 grid. Every sentence this module emits is therefore
UNCITED_EXTENSION=True, honestly, even though the surrounding technique name
(Sarvatobhadra Chakra vedha) is itself classically attested (see
`citations.SARVATOBHADRA_MUHURTA_CHINTAMANI` /
`citations.SARVATOBHADRA_VEDHA_PRASNA_MARGA`, both cited in the sentence
`detail` payload for traceability, but NOT set as `classical_citation` since
this module's specific opposition-offset computation is not itself the
verified classical rule).

If/when `l1_sarvatobhadra_vedha` is populated with a native-approved,
source-verified 14-pair table (or G-1's resonance map ships an equivalent),
`_vedha_pairs_from_db` below becomes the primary path and a populated,
DB-sourced pair can carry a real `classical_citation` instead.
"""
from __future__ import annotations

import logging
from typing import Optional

from pipeline.transit_search import MEAN_MOTIONS, find_aspect_events, NAKSHATRAS

from .models import ConfigurationSentence, ResonanceTarget
from . import citations as C

logger = logging.getLogger(__name__)

NAKSHATRA_ARC_DEG = 360.0 / 27.0  # 13°20'
_ENTRY_ORB_DEG = 0.25  # tight orb for boundary-crossing detection

_ALL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def nakshatra_boundary_lon(nakshatra_id: int) -> float:
    """Start longitude (deg) of nakshatra_id (1=Ashwini..27=Revati)."""
    if not (1 <= nakshatra_id <= 27):
        raise ValueError(f"nakshatra_id must be 1..27, got {nakshatra_id}")
    return ((nakshatra_id - 1) % 27) * NAKSHATRA_ARC_DEG


def opposite_nakshatra_id(nakshatra_id: int) -> int:
    """Algorithmic vedha-nakshatra: the nakshatra 14 positions away in the
    27-cycle (nearest-integer approximation of the 180°-opposition point).
    See module docstring for why this is an approximation, not a verified
    classical-grid lookup."""
    if not (1 <= nakshatra_id <= 27):
        raise ValueError(f"nakshatra_id must be 1..27, got {nakshatra_id}")
    return ((nakshatra_id - 1 + 14) % 27) + 1


def _vedha_pairs_from_db(conn, nakshatra_id: int) -> Optional[int]:
    """Primary path: read a real vedha pair from `l1_sarvatobhadra_vedha` if
    populated. Returns the paired nakshatra_id, or None if unreachable/empty
    (falls back to the algorithmic approximation)."""
    try:
        cur = conn.execute(
            """
            SELECT nakshatra_2_id FROM l1_sarvatobhadra_vedha WHERE nakshatra_1_id = %s
            UNION ALL
            SELECT nakshatra_1_id FROM l1_sarvatobhadra_vedha WHERE nakshatra_2_id = %s
            LIMIT 1
            """,
            [nakshatra_id, nakshatra_id],
        )
        row = cur.fetchone()
        if row:
            return int(row[0] if not isinstance(row, dict) else row["nakshatra_2_id"])
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[sarvatobhadra] l1_sarvatobhadra_vedha unreachable/empty, falling back "
            "to algorithmic opposition rule: %s", exc,
        )
    return None


def _estimate_dwell_days(planet: str) -> float:
    """Estimate nakshatra dwell time from the average daily motion already
    defined in `pipeline.transit_search.MEAN_MOTIONS`. Approximate -- actual
    dwell varies with retrograde loops (a station/retro-loop can roughly
    double or more the effective dwell in a nakshatra); this is disclosed in
    every emitted sentence's `detail['dwell_is_estimate']`."""
    motion = abs(MEAN_MOTIONS.get(planet, 1.0)) or 1.0
    return NAKSHATRA_ARC_DEG / motion


def find_sarvatobhadra_vedha_states(
    swe,
    chart_id: str,
    target: ResonanceTarget,
    start_jd: float,
    end_jd: float,
    transit_planets: Optional[list[str]] = None,
    conn=None,
) -> list[ConfigurationSentence]:
    """
    Primitive family #8: Sarvatobhadra vedha -- the classical centerpiece
    (CR-21 completion).

    A transiting graha entering the nakshatra that is vedha to `target`'s
    natal nakshatra is a VEDHA STATE: while the transiting graha dwells in
    that nakshatra, ANY primary gochara result bearing on `target` is
    classically held to be obstructed/cancelled (Prasna Marga's rekha/kona/
    vithi vedha doctrine, at the coarse "is the vedha nakshatra currently
    occupied" level this primitive implements -- rekha/kona/vithi's finer
    directional sub-classification is NOT implemented here, an honest scope
    limit, not a silent gap: it is disclosed in `detail['scope_note']`).

    Returns [] (with a logged reason) if `target.target_nakshatra_id` is
    unresolved -- this primitive needs a natal nakshatra anchor and does not
    guess one.
    """
    if target.target_nakshatra_id is None:
        logger.info(
            "[sarvatobhadra] target_ref=%s has no resolved target_nakshatra_id; "
            "skipping (honest empty result, not a crash).", target.target_ref,
        )
        return []

    planets = transit_planets or _ALL_GRAHAS
    vedha_nak = None
    if conn is not None:
        vedha_nak = _vedha_pairs_from_db(conn, target.target_nakshatra_id)
    db_sourced = vedha_nak is not None
    if vedha_nak is None:
        vedha_nak = opposite_nakshatra_id(target.target_nakshatra_id)

    boundary_lon = nakshatra_boundary_lon(vedha_nak)
    sentences: list[ConfigurationSentence] = []

    for planet in planets:
        entry_events = find_aspect_events(
            swe, planet, boundary_lon, [0], _ENTRY_ORB_DEG, start_jd, end_jd
        )
        dwell_days = _estimate_dwell_days(planet)
        for ev in entry_events:
            estimated_exit_jd = ev.event_jd + dwell_days
            sentences.append(
                ConfigurationSentence(
                    primitive="sarvatobhadra_vedha",
                    chart_id=chart_id,
                    event_class=target.event_class,
                    target_type=target.target_type,
                    target_ref=target.target_ref,
                    transit_planet=planet,
                    secondary_planet=None,
                    event_jd=ev.event_jd,
                    event_datetime_ist=ev.event_datetime_ist,
                    temporal_shape="interval",
                    fact_ids=[f"sarvatobhadra_vedha:{chart_id}:{target.target_ref}:{planet}:{ev.event_jd}"],
                    classical_citation=None,
                    uncited_extension=True,
                    detail={
                        "target_nakshatra_id": target.target_nakshatra_id,
                        "target_nakshatra_name": NAKSHATRAS[target.target_nakshatra_id - 1],
                        "vedha_nakshatra_id": vedha_nak,
                        "vedha_nakshatra_name": NAKSHATRAS[vedha_nak - 1],
                        "vedha_pair_source": "l1_sarvatobhadra_vedha" if db_sourced else "algorithmic_opposition_approximation",
                        "entry_event_jd": ev.event_jd,
                        "estimated_exit_jd": estimated_exit_jd,
                        "dwell_estimate_days": round(dwell_days, 2),
                        "dwell_is_estimate": True,
                        "cancellation_effect": (
                            f"While {planet} dwells in {NAKSHATRAS[vedha_nak - 1]} "
                            f"(vedha to {target.target_ref}'s natal nakshatra "
                            f"{NAKSHATRAS[target.target_nakshatra_id - 1]}), primary gochara "
                            f"results bearing on {target.target_ref} are classically obstructed."
                        ),
                        "technique_citation_for_traceability": C.SARVATOBHADRA_VEDHA_PRASNA_MARGA,
                        "scope_note": (
                            "Implements the coarse 'is the vedha nakshatra currently occupied' "
                            "check only; Prasna Marga's finer rekha/kona/vithi directional "
                            "sub-classification of vedha strength is not implemented."
                        ),
                    },
                )
            )

    sentences.sort(key=lambda s: s.event_jd)
    return sentences


__all__ = [
    "NAKSHATRA_ARC_DEG",
    "nakshatra_boundary_lon",
    "opposite_nakshatra_id",
    "find_sarvatobhadra_vedha_states",
]
