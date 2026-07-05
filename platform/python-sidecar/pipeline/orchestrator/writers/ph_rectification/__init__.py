"""
ph_rectification — Birth-time rectification (L4 Phala remediation R4).

FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits, rolls back, or closes ctx.db_conn (orchestrator owns the txn).
NEVER writes outside phala_rectification + phala_rectification_best.
NEVER mutates the charts table — D43 NO-AUTO-OVERRIDE hard gate. The canonical
chart 482012f1 is never auto-revised; the best candidate is only STAGED for
native review (auto_action = 'stage_for_review').

Reads:  birth params from ctx.config['birth_params'] (orchestrator pre-fetches
        from public.charts via fetch_birth_params(); PyJHora computes the scan).
Writes: phala_rectification        (delete-then-insert per chart_id; 37*5 = 185 rows)
        phala_rectification_best    (delete-then-insert per chart_id; 1 row)

Scoring is delegated to services.ph_rectification.engine (DB-free, unit-tested).
PyJHora supplies the per-candidate ascendant via _ascendant_fn().
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from pipeline.orchestrator.birth_params import resolve_birth_params
from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_rectification.engine import (
    AYANAMSHAS,
    AUTO_ACTION,
    NATIVE_CHART_ID,
    run_rectification,
    select_best,
)

logger = logging.getLogger(__name__)


def _build_ascendant_fn(local_birth_dt: datetime, lat: float, lon: float, tz_offset_hours: float):
    """Return a PyJHora-backed ascendant function (offset_min, ayanamsha) -> dict.

    Imports PyJHora lazily so the module imports cleanly even where the native
    ephemeris is unavailable (e.g. lint-only environments); the orchestrator
    always runs with PyJHora present.

    JD convention: drik.ascendant expects a LOCAL-time Julian Day (see
    compute.py docstring). Using swe.julday with UTC hours gives the wrong sign
    (a 9-sign error caused by the tz offset). We build the base JD from LOCAL
    birth time via utils.julian_day_number and shift candidates via JD arithmetic.

    Args:
        local_birth_dt: naive datetime representing the chart's LOCAL birth time.
        lat: birth latitude in decimal degrees.
        lon: birth longitude in decimal degrees.
        tz_offset_hours: UTC offset in fractional hours (e.g. 5.5 for IST).
    """
    from jhora import utils
    from jhora.panchanga import drik as _drik
    from pyjhora_adapter.houses import compute_ascendant  # type: ignore

    _base_jd = utils.julian_day_number(
        _drik.Date(local_birth_dt.year, local_birth_dt.month, local_birth_dt.day),
        (local_birth_dt.hour, local_birth_dt.minute, local_birth_dt.second),
    )

    def fn(offset_minutes: int, ayanamsha_id: str) -> dict:
        jd = _base_jd + offset_minutes / 1440.0  # 1440 min per JD day
        asc = compute_ascendant(
            jd, ayanamsha_id, lat=lat, lon=lon, tz=tz_offset_hours
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

        # JL-017 (BA Phase 2.5 #11, CONTAMINATION-CLASS): the engine's embedded
        # TRAINING_EVENTS + natal dasha-lord positions are the native's own LEL
        # events and chart facts. No other chart has a training-event corpus in
        # this system yet, so scoring any other chart against them would be
        # silently attributing the native's life history to a stranger's chart —
        # exactly the plausible-but-wrong failure class this audit hunts. Fail
        # loudly, before any DB writes, instead of guessing.
        if chart_id != NATIVE_CHART_ID:
            raise ValueError(
                f"ph_rectification: no chart-specific LEL training-event corpus exists for "
                f"chart_id={chart_id!r}. The engine's TRAINING_EVENTS + natal dasha-lord "
                f"positions belong exclusively to the native chart ({NATIVE_CHART_ID}); "
                f"scoring another chart against them would silently misattribute the "
                f"native's life events (JL-017). Refusing rather than guessing."
            )

        birth_params = resolve_birth_params(chart_id, ctx.config.get("birth_params"))

        # Derive LOCAL birth datetime and UTC birth datetime from birth_params.
        # birth_params['datetime_iso'] is the LOCAL birth datetime (naive ISO string).
        # birth_params['tz_offset_hours'] is the UTC offset in fractional hours.
        local_birth_dt = datetime.fromisoformat(birth_params["datetime_iso"])
        tz_offset_hours = float(birth_params["tz_offset_hours"])
        lat = float(birth_params["latitude_deg"])
        lon = float(birth_params["longitude_deg"])

        # Derive UTC birth time: local - tz_offset as a UTC-aware datetime.
        from datetime import timedelta
        utc_birth_dt = (local_birth_dt - timedelta(hours=tz_offset_hours)).replace(
            tzinfo=timezone.utc
        )

        # Delete-then-insert idempotency (L1+ standard, §N.3). Children first.
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM phala_rectification_best WHERE chart_id = %s", (chart_id,)
            )
            cur.execute(
                "DELETE FROM phala_rectification WHERE chart_id = %s", (chart_id,)
            )

        ascendant_fn = _build_ascendant_fn(local_birth_dt, lat, lon, tz_offset_hours)
        candidates = run_rectification(ascendant_fn, recorded_birth_utc=utc_birth_dt)
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
                new_id = cur.fetchone()["id"]
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
