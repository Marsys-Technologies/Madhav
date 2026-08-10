"""
gochara_v3.context — ClassContext: the ONE-SHOT data fetch that makes
batched lambda_e evaluation possible.

The v1 engine (`compute_lambda_e`) does DB round-trips per candidate JD:
  - resonance targets (1 query per call, or shared via series)
  - enrichment (N queries per target)
  - dasha periods (1 query per call, or shared via series)
  - temporal_shape (1 query)
  - sade_sati phase (1 query via primitives)
  - guru-shani double transit (ephemeris calls per target pair)
  - av_threshold (DB query for gate rows)
  - planetary_return (ephemeris per target)
  - valence (1 query)
  - 9 primitives per target (ephemeris calls)

ClassContext.fetch() does ALL of these DB reads ONCE, storing the results
in an immutable frozen dataclass. After construction, evaluate_lambda_vector
in engine.py operates ENTIRELY in-memory — zero per-JD DB access.

Per I2: v1 modules are IMPORTED for their data-fetching functions, not
copied or modified.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

# v1 imports (I2 compliance — read-only consumption, never edited)
from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_grammar.models import ResonanceTarget
from services.gochara_intensity.enrichment import enrich_targets
from services.gochara_intensity.valence import VALENCE_MAP, is_adverse, fetch_valence
from services.gochara_intensity.engine import fetch_temporal_shape, SHAPE_MAP
from services.gochara_intensity.beta_priors import beta_for
from services.gochara_intensity.promise import compute_promise
from services.gochara_intensity.suppression import SUPPRESSION_WEIGHTS
from services.gochara_intensity.permission import (
    SYSTEM_WEIGHTS, DASHA_SYSTEM_IDS,
    _relevant_grahas, _relevant_signs, YOGINI_LORD_TO_GRAHA,
)
from services.gochara_intensity._dbutil import savepoint_scope

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NatalFacts:
    """Natal chart positions needed for permission/configuration evaluation.
    Pre-fetched from chart_facts once, never re-queried."""
    # Graha longitudes (sidereal) — keyed by full Title-case name ("Sun", "Moon", etc.)
    graha_longitudes: dict[str, float]    # graha -> longitude_deg
    graha_signs: dict[str, str]           # graha -> sign name
    lagna_sign: Optional[str] = None
    lagna_longitude: Optional[float] = None


@dataclass(frozen=True)
class DashaPeriod:
    """One dasha period row from chart_dashas, pre-fetched."""
    system_id: str
    level_n: int
    lord_graha: Optional[str]
    start_iso: str
    end_iso: str


@dataclass(frozen=True)
class AVGateRow:
    """One row from bg_transit_av_gates, pre-fetched for av_threshold evaluation."""
    target_ref: str  # bhava number as string
    graha: str
    min_sav_score: Optional[float]
    effect: Optional[str]
    classical_citation: Optional[str]


@dataclass(frozen=True)
class ClassContext:
    """All data needed to evaluate lambda_e for a (chart x event_class) pair,
    fetched ONCE. After construction this object is immutable and contains
    everything needed for vectorized evaluation — ZERO per-JD DB access.

    The fetch() classmethod does ALL DB access. evaluate_lambda_vector()
    in engine.py operates purely against this context's pre-fetched data.
    """
    chart_id: str
    event_class: str

    # Resonance targets (enriched with degree data, nakshatra, etc.)
    resonance_targets: tuple[ResonanceTarget, ...]

    # Pre-computed PROMISE (time-invariant for a given chart x event_class)
    promise: float
    promise_detail: dict

    # Full dasha timelines for all PERMISSION systems
    # (list of dicts matching DD.fetch_dasha_periods output)
    dasha_periods: tuple[dict, ...]

    # Pre-computed dasha-relevant sets for PERMISSION lord-matching
    relevant_grahas: frozenset[str]
    relevant_signs: frozenset[str]

    # Temporal shape and valence (time-invariant)
    temporal_shape: str
    valence: str
    is_adverse: bool
    beta_e: float

    # Weight map for X(t) computation
    weight_by_target_ref: dict[str, float] = field(default_factory=dict)

    # Natal facts for enrichment-equivalent lookups
    natal_facts: Optional[NatalFacts] = None

    # AV gate rows (pre-fetched for av_threshold PERMISSION generator)
    av_gate_rows: tuple[AVGateRow, ...] = ()

    # Sade Sati phases (pre-fetched intervals)
    sade_sati_phases: tuple[dict, ...] = ()

    @classmethod
    def fetch(
        cls,
        conn,
        chart_id: str,
        event_class: str,
        ayanamsha_id: str = "lahiri_chitrapaksha",
    ) -> "ClassContext":
        """One-shot fetch — all DB access happens here, NEVER in evaluate().

        Calls the same v1 fetching functions (I2: imported, not copied) but
        collects ALL results into an immutable ClassContext. This is the
        single DB round-trip that replaces N per-candidate round-trips.
        """
        # 1. Resonance targets (same v1 function)
        with savepoint_scope(conn, "v3_resonance_targets"):
            raw_targets = RM.fetch_resonance_targets(conn, chart_id, event_class)
        targets = enrich_targets(conn, raw_targets, ayanamsha_id=ayanamsha_id)
        targets_tuple = tuple(targets)

        # 2. PROMISE (time-invariant — depends only on targets)
        promise, promise_detail = compute_promise(list(targets))
        # Freeze promise_detail
        promise_detail = dict(promise_detail)

        # 3. Dasha periods (same v1 function, all systems)
        with savepoint_scope(conn, "v3_dasha_periods"):
            dasha_periods_list = DD.fetch_dasha_periods(
                conn, chart_id, ayanamsha_id=ayanamsha_id,
                systems=list(DASHA_SYSTEM_IDS),
            )
        dasha_periods_tuple = tuple(dasha_periods_list)

        # 4. Dasha-relevant grahas/signs (time-invariant)
        rel_grahas = frozenset(_relevant_grahas(list(targets)))
        rel_signs = frozenset(_relevant_signs(list(targets)))

        # 5. Temporal shape
        shape = fetch_temporal_shape(conn, event_class)

        # 6. Valence
        adverse, valence = is_adverse(conn, event_class)

        # 7. Beta_e
        beta_e = beta_for(event_class)

        # 8. Weight map for X(t)
        weight_map = {t.target_ref: t.weight for t in targets}

        # 9. Natal facts (pre-fetch graha positions for ephemeris-free checks)
        natal_facts = _fetch_natal_facts(conn, chart_id, ayanamsha_id)

        # 10. AV gate rows for av_threshold PERMISSION
        av_gate_rows = _fetch_all_av_gate_rows(conn, targets)

        # 11. Sade Sati phases (pre-fetch the intervals)
        sade_sati_phases = _fetch_sade_sati_phases(conn, chart_id, targets)

        return cls(
            chart_id=chart_id,
            event_class=event_class,
            resonance_targets=targets_tuple,
            promise=promise,
            promise_detail=promise_detail,
            dasha_periods=dasha_periods_tuple,
            relevant_grahas=rel_grahas,
            relevant_signs=rel_signs,
            temporal_shape=shape,
            valence=valence,
            is_adverse=adverse,
            beta_e=beta_e,
            weight_by_target_ref=weight_map,
            natal_facts=natal_facts,
            av_gate_rows=tuple(av_gate_rows),
            sade_sati_phases=tuple(sade_sati_phases),
        )


def _fetch_natal_facts(
    conn, chart_id: str, ayanamsha_id: str,
) -> Optional[NatalFacts]:
    """Pre-fetch all graha positions from chart_facts in one query."""
    if conn is None:
        return None
    try:
        with savepoint_scope(conn, "v3_natal_facts"):
            cur = conn.execute(
                """
                SELECT fact_subject, fact_key, fact_value_text, fact_value_num
                  FROM chart_facts
                 WHERE chart_id = %s AND ayanamsha_id = %s
                   AND fact_category = 'graha_position'
                   AND fact_key IN ('longitude_sidereal', 'sign')
                """,
                [chart_id, ayanamsha_id],
            )
            rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[v3.context] natal_facts fetch failed: %s", exc)
        return None

    longitudes: dict[str, float] = {}
    signs: dict[str, str] = {}
    lagna_sign = None
    lagna_lon = None

    for row in rows:
        d = row if isinstance(row, dict) else dict(
            zip(["fact_subject", "fact_key", "fact_value_text", "fact_value_num"], row)
        )
        subject = d["fact_subject"]
        if d["fact_key"] == "longitude_sidereal" and d.get("fact_value_num") is not None:
            longitudes[subject] = float(d["fact_value_num"])
            if subject == "LAGNA":
                lagna_lon = float(d["fact_value_num"])
        elif d["fact_key"] == "sign" and d.get("fact_value_text"):
            signs[subject] = d["fact_value_text"]
            if subject == "LAGNA":
                lagna_sign = d["fact_value_text"]

    return NatalFacts(
        graha_longitudes=longitudes,
        graha_signs=signs,
        lagna_sign=lagna_sign,
        lagna_longitude=lagna_lon,
    )


def _fetch_all_av_gate_rows(
    conn, targets: list[ResonanceTarget],
) -> list[AVGateRow]:
    """Pre-fetch AV gate rows for all bhava targets at once."""
    if conn is None:
        return []
    bhava_refs = [t.target_ref for t in targets if t.target_type == "bhava"]
    if not bhava_refs:
        return []
    try:
        with savepoint_scope(conn, "v3_av_gates"):
            cur = conn.execute(
                """
                SELECT bhava_num::text AS target_ref, graha, min_sav_score,
                       effect, classical_citation
                  FROM bg_transit_av_gates
                 WHERE gate_kind = 'sav_threshold'
                   AND bhava_num::text = ANY(%s)
                """,
                [bhava_refs],
            )
            rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[v3.context] av_gate_rows fetch failed: %s", exc)
        return []

    result = []
    for row in rows:
        d = row if isinstance(row, dict) else dict(
            zip(["target_ref", "graha", "min_sav_score", "effect", "classical_citation"], row)
        )
        result.append(AVGateRow(
            target_ref=str(d["target_ref"]),
            graha=d["graha"],
            min_sav_score=float(d["min_sav_score"]) if d.get("min_sav_score") is not None else None,
            effect=d.get("effect"),
            classical_citation=d.get("classical_citation"),
        ))
    return result


def _fetch_sade_sati_phases(
    conn, chart_id: str, targets: list[ResonanceTarget],
) -> list[dict]:
    """Pre-fetch Sade Sati phase intervals from chart_facts.

    The v1 permission.py calls P.sade_sati_phase which reads chart_facts
    rows with fact_category='sade_sati_cycle' or 'sade_sati_phase'. We
    pre-fetch all of them here so PERMISSION evaluation is DB-free.
    """
    if conn is None or not targets:
        return []
    try:
        with savepoint_scope(conn, "v3_sade_sati"):
            cur = conn.execute(
                """
                SELECT fact_key, fact_value_text, fact_value_num,
                       fact_subject, fact_category
                  FROM chart_facts
                 WHERE chart_id = %s
                   AND fact_category IN ('sade_sati_cycle', 'sade_sati_phase')
                ORDER BY fact_key
                """,
                [chart_id],
            )
            rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[v3.context] sade_sati phases fetch failed: %s", exc)
        return []

    phases = []
    for row in rows:
        d = row if isinstance(row, dict) else dict(
            zip(["fact_key", "fact_value_text", "fact_value_num",
                 "fact_subject", "fact_category"], row)
        )
        phases.append(d)
    return phases


__all__ = [
    "ClassContext", "NatalFacts", "DashaPeriod", "AVGateRow",
]
