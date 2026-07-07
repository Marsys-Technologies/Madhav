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
from services.mimamsa.lel_calibration import rectification_basis
from services.ph_rectification.engine import (
    AYANAMSHAS,
    AUTO_ACTION,
    TrainingEvent,
    run_rectification,
    select_best,
)

logger = logging.getLogger(__name__)

_SIGN_INDEX = {
    "Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3, "Leo": 4, "Virgo": 5,
    "Libra": 6, "Scorpio": 7, "Sagittarius": 8, "Capricorn": 9,
    "Aquarius": 10, "Pisces": 11,
}


def _dasha_lord_on_date(conn, chart_id: str, ev_date, level_n: int):
    """This chart's OWN Vimshottari dasha lord (level_n=1 maha, 2 antar) active
    on ev_date, from ITS chart_dashas (lahiri reference). Never the native's.
    Served by cd_temporal_lookup_idx (chart_id, ayanamsha_id, system_id,
    level_n, start_date, end_date)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT lord_graha FROM chart_dashas
            WHERE chart_id = %s AND system_id = 'vimshottari' AND level_n = %s
              AND ayanamsha_id = 'lahiri_chitrapaksha'
              AND start_date <= %s AND end_date >= %s
            ORDER BY start_date
            LIMIT 1
            """,
            (chart_id, level_n, ev_date, ev_date),
        )
        r = cur.fetchone()
    return r["lord_graha"] if r else None


def _load_chart_training_events(conn, chart_id: str) -> list[TrainingEvent]:
    """Build rectification training events from THIS chart's OWN life history +
    OWN chart_dashas — availability-driven (BA-P4 R2.2 / W2.2).

    Since migration 423 `life_events` is chart-scoped (`chart_id` NOT NULL), so
    every chart reads ONLY its own events (`WHERE chart_id = %s`). There is no
    chart-identity branch: a chart with recorded events is scored against them
    (LEL-fit); a chart with none yields [] — a clean, honest, lagna-stability-
    only rectification. A chart NEVER trains on another chart's history (the
    chart-scope filter IS the JL-017 contamination firewall). The engine still
    re-applies its own leakage firewall (pre-2020, exact/month-exact).

    Pre-migration-423 schema (no `chart_id` column) or a missing table yields []
    rather than crashing or silently reading a different chart's rows — the safe,
    structural-only default. Events whose per-chart mahadasha lord can't be
    determined from this chart's chart_dashas are skipped (never fabricated)."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_id, event_date, category, domain
                FROM life_events
                WHERE chart_id = %s AND event_date IS NOT NULL
                ORDER BY event_date
                """,
                (chart_id,),
            )
            rows = cur.fetchall()
    except Exception as e:
        # Pre-423 schema (no chart_id column) or missing table → no per-chart
        # training source → structural-only rectification. Never a hard failure.
        logger.warning(
            "ph_rectification: chart-scoped life_events read failed (%s); "
            "proceeding structural-only (no LEL training)", e,
        )
        return []

    events: list[TrainingEvent] = []
    for row in rows:
        ev_date = row["event_date"]
        d = ev_date.date() if hasattr(ev_date, "date") else ev_date
        md_lord = _dasha_lord_on_date(conn, chart_id, d, 1)
        if md_lord is None:
            continue  # can't place this chart's own MD lord — skip, never guess
        ad_lord = _dasha_lord_on_date(conn, chart_id, d, 2)
        events.append(TrainingEvent(
            event_id=str(row.get("event_id") or f"EVT.{d.isoformat()}"),
            date=datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
            domain=str(row.get("domain") or row.get("category") or "unknown"),
            maha_dasha_lord=str(md_lord).capitalize(),
            date_confidence="month-exact",
            antar_dasha_lord=(str(ad_lord).capitalize() if ad_lord else None),
        ))
    return events


def _load_chart_natal_sign_index(conn, chart_id: str) -> dict[str, int]:
    """This chart's OWN natal graha -> sidereal sign index (0=Aries..11=Pisces),
    from ITS chart_facts graha_position/sign facts. Feeds the dasha-lord natal
    house computation for per-chart rectification scoring. Never the native's."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_value_text
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = 'lahiri_chitrapaksha'
              AND fact_category = 'graha_position' AND fact_key = 'sign'
            """,
            (chart_id,),
        )
        rows = cur.fetchall()
    idx: dict[str, int] = {}
    for row in rows:
        subj = row.get("fact_subject")
        sign_i = _SIGN_INDEX.get(row.get("fact_value_text"))
        if subj and sign_i is not None:
            idx[str(subj).capitalize()] = sign_i
    return idx


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

        # JL-017 (CONTAMINATION-CLASS) — now AVAILABILITY-DRIVEN (BA-P4 R2.2/W2.2):
        # rectification is a per-chart asset every chart gets, and each chart is
        # scored ONLY against ITS OWN life events. Since migration 423
        # life_events is chart-scoped, so there is no native-identity branch and
        # the engine's embedded native corpus is NEVER used: every chart (native
        # included) sources its training events + natal sign index from ITS OWN
        # rows, passed EXPLICITLY. A chart with no recorded events yields an
        # empty training set -> a clean lagna-stability-only rectification
        # (185 candidates, structural_no_lel), not another chart's history and
        # not a hard failure.
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

        # Per-chart corpus — availability-driven for EVERY chart (no identity
        # branch; the engine's embedded native corpus is never used).
        training_events = _load_chart_training_events(conn, chart_id)
        natal_sign_index = _load_chart_natal_sign_index(conn, chart_id)
        basis = rectification_basis(len(training_events))  # lel_fit | structural_no_lel
        logger.info(
            "ph_rectification: chart %s sourced %d own training events -> basis=%s "
            "(structural_no_lel = clean lagna-stability-only rectification)",
            chart_id, len(training_events), basis,
        )

        ascendant_fn = _build_ascendant_fn(local_birth_dt, lat, lon, tz_offset_hours)
        candidates = run_rectification(
            ascendant_fn,
            recorded_birth_utc=utc_birth_dt,
            training_events=training_events,
            dasha_lord_natal_sign_index=natal_sign_index,
        )
        best = select_best(candidates, training_events=training_events)
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
                    # Persist the availability-driven basis alongside the engine's
                    # firewall note (no schema change; a dedicated column lands with
                    # the calibration-state persistence migration).
                    f"[basis={basis}] {best.leakage_firewall_note}", AUTO_ACTION,
                ),
            )
            rows_inserted += 1

        logger.info(
            "ph_rectification: inserted %d rows (%d candidates + 1 best) for %s",
            rows_inserted, len(candidates), chart_id,
        )
        return WriterResult(asset_id="ph_rectification", rows_inserted=rows_inserted)
