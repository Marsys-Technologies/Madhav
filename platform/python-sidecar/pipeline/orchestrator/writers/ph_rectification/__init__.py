"""
ph_rectification — Birth-time rectification (L4 Phala remediation R4).

FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits, rolls back, or closes ctx.db_conn (orchestrator owns the txn).
NEVER writes outside phala_rectification + phala_rectification_best.
NEVER mutates the charts table — D43 NO-AUTO-OVERRIDE hard gate. The canonical
chart 482012f1 is never auto-revised; the best candidate is only STAGED for
native review (auto_action = 'stage_for_review').

Reads:  nothing from DB (birth params from ctx.config; PyJHora computes the scan).
Writes: phala_rectification        (delete-then-insert per chart_id; 37*5 = 185 rows)
        phala_rectification_best    (delete-then-insert per chart_id; 1 row)

Scoring is delegated to services.ph_rectification.engine (DB-free, unit-tested).
PyJHora supplies the per-candidate ascendant via _ascendant_fn().
"""
from __future__ import annotations

import json
import logging

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_rectification.engine import (
    AYANAMSHAS,
    AUTO_ACTION,
    NATIVE_LAT,
    NATIVE_LON,
    NATIVE_TZ,
    RECORDED_BIRTH_UTC,
    run_rectification,
    select_best,
)

logger = logging.getLogger(__name__)


def _build_ascendant_fn():
    """Return a PyJHora-backed ascendant function (offset_min, ayanamsha) -> dict.

    Imports PyJHora lazily so the module imports cleanly even where the native
    ephemeris is unavailable (e.g. lint-only environments); the orchestrator
    always runs with PyJHora present.

    JD convention: drik.ascendant expects a LOCAL-time Julian Day (see
    compute.py docstring). Using swe.julday with UTC hours (05:13) gives
    Capricorn instead of Aries — a 9-sign error caused by the 5.5h IST offset.
    We build the base JD from LOCAL birth time (10:43 IST) via
    utils.julian_day_number and shift candidates via JD arithmetic.
    """
    from jhora import utils
    from jhora.panchanga import drik as _drik
    from pyjhora_adapter.houses import compute_ascendant  # type: ignore

    # Local birth: 1984-02-05 10:43:00 IST (= RECORDED_BIRTH_UTC + NATIVE_TZ h).
    _base_jd = utils.julian_day_number(_drik.Date(1984, 2, 5), (10, 43, 0))

    def fn(offset_minutes: int, ayanamsha_id: str) -> dict:
        jd = _base_jd + offset_minutes / 1440.0  # 1440 min per JD day
        asc = compute_ascendant(
            jd, ayanamsha_id, lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ
        )
        return {
            "sign": asc["sign"],
            "longitude_deg": asc["longitude_deg"],
            "degree_in_sign": asc["degree_in_sign"],
        }

    return fn


@register("ph_rectification")
class PhRectificationWriter(WriterBase):
    """Builds phala_rectification + phala_rectification_best.

    D43: best candidate is STAGED only (auto_action='stage_for_review').
    The writer never executes UPDATE/DELETE against the charts table.
    """
    asset_id = "ph_rectification"

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or close — orchestrator owns the txn
        chart_id = ctx.config["chart_id"]

        # Delete-then-insert idempotency (L1+ standard, §N.3). Children first.
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM phala_rectification_best WHERE chart_id = %s", (chart_id,)
            )
            cur.execute(
                "DELETE FROM phala_rectification WHERE chart_id = %s", (chart_id,)
            )

        ascendant_fn = _build_ascendant_fn()
        candidates = run_rectification(ascendant_fn)
        best = select_best(candidates)
        logger.info(
            "ph_rectification: scored %d candidate rows; best offset=%s label=%s",
            len(candidates),
            best.offset_minutes,
            best.confidence_label,
        )

        rows_inserted = 0
        id_by_offset_ayan: dict[tuple[int, str], str] = {}
        with conn.cursor() as cur:
            for c in candidates:
                cur.execute(
                    """
                    INSERT INTO phala_rectification (
                        chart_id, candidate_birth_utc, offset_minutes, ayanamsha_id,
                        lagna_sign, lagna_longitude_deg, lagna_degree_in_sign,
                        lel_fit_score, lel_events_matched, lel_events_tested,
                        lagna_stable
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        chart_id, c.candidate_birth_utc, c.offset_minutes, c.ayanamsha_id,
                        c.lagna_sign, c.lagna_longitude_deg, c.lagna_degree_in_sign,
                        c.lel_fit_score, c.lel_events_matched, c.lel_events_tested,
                        c.lagna_stable,
                    ),
                )
                new_id = cur.fetchone()[0]
                id_by_offset_ayan[(c.offset_minutes, c.ayanamsha_id)] = new_id
                rows_inserted += 1

            # Best row — D43: auto_action is ALWAYS 'stage_for_review'.
            best_candidate_id = None
            if best.best_candidate is not None:
                best_candidate_id = id_by_offset_ayan.get(
                    (best.best_candidate.offset_minutes, best.best_candidate.ayanamsha_id)
                )
            cur.execute(
                """
                INSERT INTO phala_rectification_best (
                    chart_id, best_candidate_id, candidate_birth_utc, offset_minutes,
                    best_lagna_sign, best_lagna_longitude, best_lel_fit_score,
                    confidence_low, confidence_high, confidence_label, win_margin,
                    competing_candidates, lel_training_events, lel_training_matched,
                    leakage_firewall_note, auto_action
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s, %s,
                    %s, %s
                )
                """,
                (
                    chart_id, best_candidate_id, best.candidate_birth_utc, best.offset_minutes,
                    best.best_lagna_sign, best.best_lagna_longitude, best.best_lel_fit_score,
                    best.confidence_low, best.confidence_high, best.confidence_label,
                    best.win_margin,
                    json.dumps(best.competing_candidates),
                    best.lel_training_events, best.lel_training_matched,
                    best.leakage_firewall_note, AUTO_ACTION,
                ),
            )
            rows_inserted += 1

        logger.info(
            "ph_rectification: inserted %d rows (%d candidates + 1 best) for %s",
            rows_inserted, len(candidates), chart_id,
        )
        return WriterResult(asset_id="ph_rectification", rows_inserted=rows_inserted)
