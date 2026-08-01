"""
services/ka_tithi_pravesha/writer.py — WriterBase subclass for
`ka_tithi_pravesha` (ṢAḌ-DARŚANA W3, registry item 13). Pure root-find/
windowing logic lives in ./logic.py (engine/DB-free, unit-tested); this
module is the ephemeris-engine-calling + DB-touching shell.

Contract adherence (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - Uses ctx.db_conn (caller-owned) for all DB access; NEVER commits/closes it.
  - NEVER writes asset_throughput.
  - Idempotency: per-chart delete-then-insert (§N.3) — DELETE FROM
    kala_tithi_pravesha WHERE chart_id = %s immediately before INSERT.
  - LIGHT writer (single run() call) — 120 rows/chart, real ephemeris
    root-find + full annual-chart cast per row, benchmarked ~3.4ms/row during
    design (see logic.py module docstring) — comfortably within
    writer_timeout_seconds=120.

── DATA SOURCES (§N.5 — L1 is the authority) ─────────────────────────────────
Natal Moon exact sidereal longitude is read VERBATIM from chart_facts
(fact_category='graha_position', fact_subject='MOON',
fact_key='longitude_sidereal', ayanamsha_id=CANONICAL_AYANAMSHA) — the SAME
fact `ka_moorti_nirnaya.writer._fetch_janma_nakshatra_idx` reads (for its own,
unrelated computation). Never recomputed independently (B.10 / §N.5).

── ENGINE (B.10 — no fabricated computation) ─────────────────────────────────
`_moon_longitude` (lightweight position-only) and `_annual_chart` (full chart
cast) both call `pyjhora_adapter` — the SAME Swiss-Ephemeris-backed engine
`ga_tajaka_writer.py` (L1 Vārṣaphal) uses for its own solar-return root-find
and annual-chart cast, and the same engine every L1 writer uses. No
independent ephemeris implementation anywhere in this module.

── CITATION HONESTY (B.3 / §N.7 item 6) ──────────────────────────────────────
No primary-source chapter/verse citation for Tithi-Praveśa specifically is
ingested in this corpus (see logic.py module docstring for the full
derivation this writer is built from). `classical_source_citation` is
honestly `not_in_corpus` on every row — never a fabricated chapter reference.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from pyjhora_adapter._jhora import drik, utils
from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.positions import compute_positions
from services.ka_tithi_pravesha.logic import (
    DEFAULT_MAX_PRAVESHA_YEAR,
    LUNAR_RETURN_TOL_DEG,
    ang_diff,
    lunar_return,
    pravesha_anniversary,
)

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_tithi_pravesha_v1.0"
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"
ENGINE_AYANAMSHA = "lahiri"  # pyjhora_adapter's own id for the same ayanamsha

CLASSICAL_SOURCE_CITATION = (
    "not_in_corpus: Tithi-Praveśa (lunar-return annual chart) named in "
    "KALA_TRANSFORMATION_HANDOFF_v1_0.md's glossary as the lunar-return "
    "counterpart to Tājika Vārṣaphala; no primary-source chapter/verse "
    "citation for the technique specifically is ingested in this corpus — "
    "an ingestion work item is filed, not fabricated here (§N.7 item 6)."
)

_FETCH_NATAL_MOON_SQL = """
SELECT fact_id, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_subject = 'MOON' AND fact_key = 'longitude_sidereal'
"""

_DELETE_SQL = "DELETE FROM kala_tithi_pravesha WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO kala_tithi_pravesha (
    chart_id, ayanamsha_id, pravesha_year, window_start, window_end,
    start_converged, end_converged,
    pravesha_lagna_sign_idx, pravesha_lagna_sign_name, pravesha_lagna_degree,
    graha_positions_jsonb, natal_moon_longitude_deg, moon_fact_id,
    ephemeris_audit_jsonb, verification_pass_status, classical_source_citation,
    formula_version
) VALUES (
    %(chart_id)s, %(ayanamsha_id)s, %(pravesha_year)s, %(window_start)s, %(window_end)s,
    %(start_converged)s, %(end_converged)s,
    %(pravesha_lagna_sign_idx)s, %(pravesha_lagna_sign_name)s, %(pravesha_lagna_degree)s,
    %(graha_positions_jsonb)s, %(natal_moon_longitude_deg)s, %(moon_fact_id)s,
    %(ephemeris_audit_jsonb)s, %(verification_pass_status)s, %(classical_source_citation)s,
    %(formula_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, pravesha_year) DO NOTHING
"""


def _fetch_natal_moon_longitude(conn: Any, chart_id: str) -> tuple[float, str] | None:
    """Returns (natal Moon sidereal longitude deg, fact_id), or None if the L1
    dependency (ga_positions) has not produced this fact — honest absence,
    never fabricated (B.10)."""
    with conn.cursor() as cur:
        cur.execute(_FETCH_NATAL_MOON_SQL, (chart_id, CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if not row or row[1] is None:
        return None
    return float(row[1]), str(row[0])


def _birth_dt_and_params_from_config(ctx) -> tuple[datetime, dict] | None:
    """§N.2: writers get chart_id + birth_params from ctx.config. Returns
    (birth wall-clock datetime, birth_params dict), or None if genuinely
    missing/unparsable — never guesses a birth instant (B.10)."""
    birth_params = ctx.config.get("birth_params") or {}
    raw = birth_params.get("datetime_iso")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw[:19]), birth_params
    except ValueError:
        return None


def _moon_longitude(dt_local: datetime, birth_params: dict) -> float:
    """Sidereal Moon longitude (deg, 0..360) at a local-wallclock instant, via
    the lightweight position engine (no full chart) — same call shape as
    ga_tajaka_writer.py's `_sun_longitude`, for the Moon instead of the Sun."""
    bp = birth_params
    dob = drik.Date(dt_local.year, dt_local.month, dt_local.day)
    tob = (dt_local.hour, dt_local.minute, dt_local.second)
    jd = utils.julian_day_number(dob, tob)
    grahas = compute_positions(
        jd, ENGINE_AYANAMSHA,
        lat=float(bp["latitude_deg"]), lon=float(bp["longitude_deg"]),
        tz=float(bp["tz_offset_hours"]),
    )
    for g in grahas:
        if g["name"] == "Moon":
            return float(g["longitude_deg"]) % 360.0
    raise RuntimeError("[ka_tithi_pravesha] Moon not found in positions")


def _annual_chart(instant: datetime, birth_params: dict) -> dict[str, Any]:
    """Full annual chart (Praveśa Lagna + graha positions) cast for `instant`,
    using the chart's own place/tz (birth_params) — same call shape as
    ga_tajaka_writer.py's `annual = compute_chart(...)`."""
    return compute_chart(
        {**birth_params, "datetime_iso": instant.replace(microsecond=0).isoformat()},
        ayanamsha_id=ENGINE_AYANAMSHA,
    )


def _graha_positions_jsonb(annual_chart: dict[str, Any]) -> list[dict[str, Any]]:
    """The sanctioned irreducible composite (matches ga_tajaka's
    candidate_lord_jsonb/muntha_position_jsonb precedent) — one entry per
    graha in the annual chart, verbatim from compute_chart's own output,
    never re-derived."""
    rows = []
    for g in annual_chart.get("grahas", []):
        rows.append({
            "name": g["name"],
            "sign_idx": int(g["sign_id"]) - 1,
            "sign_name": g["sign"],
            "degree_in_sign": round(float(g["degree_in_sign"]), 4),
            "longitude_deg": round(float(g["longitude_deg"]), 6),
            "house": g.get("house"),
            "retrograde": bool(g.get("retrograde", False)),
            "nakshatra": g.get("nakshatra"),
            "nakshatra_pada": g.get("nakshatra_pada") or g.get("pada"),
            "dignity_status": g.get("dignity_status"),
        })
    return rows


def _compute_one_year(
    pravesha_year: int, birth_dt: datetime, birth_params: dict,
    natal_moon_long: float,
) -> dict[str, Any]:
    """Compute a single praveśa-year row dict (annual chart at the lunar
    return nearest that year's solar-birthday anniversary)."""
    anniversary = pravesha_anniversary(birth_dt, pravesha_year)
    next_anniversary = pravesha_anniversary(birth_dt, pravesha_year + 1)

    def _longitude_fn(dt: datetime) -> float:
        return _moon_longitude(dt, birth_params)

    instant, audit = lunar_return(anniversary, natal_moon_long, _longitude_fn)
    next_instant, next_audit = lunar_return(next_anniversary, natal_moon_long, _longitude_fn)

    annual = _annual_chart(instant, birth_params)
    ascendant = annual["ascendant"]
    annual_moon_long = float(
        next(g for g in annual["grahas"] if g["name"] == "Moon")["longitude_deg"]
    ) % 360.0
    # Two-pass verification (§N.7 item 5): the annual chart's own,
    # independently-computed Moon longitude (via compute_chart's full
    # position pipeline) must agree with the root-find's target — a
    # different code path recomputing the same value, matching ga_tajaka's
    # own sr_ok cross-check discipline.
    cross_check_diff = abs(ang_diff(annual_moon_long, natal_moon_long))
    verification = (
        "two_pass_verified"
        if (audit["converged"] and cross_check_diff <= LUNAR_RETURN_TOL_DEG)
        else "divergent_flagged"
    )

    return {
        "pravesha_year": pravesha_year,
        "window_start": instant,
        "window_end": next_instant,
        "start_converged": audit["converged"],
        "end_converged": next_audit["converged"],
        "pravesha_lagna_sign_idx": int(ascendant["sign_id"]) - 1,
        "pravesha_lagna_sign_name": ascendant["sign"],
        "pravesha_lagna_degree": round(float(ascendant["degree_in_sign"]), 4),
        "graha_positions_jsonb": _graha_positions_jsonb(annual),
        "natal_moon_longitude_deg": round(natal_moon_long, 6),
        "ephemeris_audit_jsonb": {
            "start": audit,
            "end": next_audit,
            "annual_chart_moon_cross_check_diff_deg": round(cross_check_diff, 6),
        },
        "verification_pass_status": verification,
        "formula_version": FORMULA_VERSION,
    }


@register("ka_tithi_pravesha")
class KaTithiPraveshaWriter(WriterBase):
    """ka_tithi_pravesha — Tithi-Praveśa lunar-return annual chart (L3 Kāla, item 13). LIGHT writer."""

    asset_id = "ka_tithi_pravesha"

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        if ctx.dry_run:
            logger.info("[ka_tithi_pravesha] dry_run=True — skipping")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run=True")

        birth = _birth_dt_and_params_from_config(ctx)
        if birth is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="ctx.config['birth_params'] missing/unparsable datetime_iso",
            )
        birth_dt, birth_params = birth

        natal = _fetch_natal_moon_longitude(conn, chart_id)
        if natal is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="missing natal MOON longitude_sidereal fact — run ga_positions first",
            )
        natal_moon_long, moon_fact_id = natal

        # Idempotency: per-chart delete-then-insert (§N.3)
        with conn.cursor() as cur:
            cur.execute(_DELETE_SQL, (chart_id,))

        all_rows: list[dict] = []
        divergent = 0
        for pravesha_year in range(1, DEFAULT_MAX_PRAVESHA_YEAR + 1):
            computed = _compute_one_year(pravesha_year, birth_dt, birth_params, natal_moon_long)
            if computed["verification_pass_status"] == "divergent_flagged":
                divergent += 1
            row: dict[str, Any] = {
                "chart_id": chart_id,
                "ayanamsha_id": CANONICAL_AYANAMSHA,
                "moon_fact_id": moon_fact_id,
                "classical_source_citation": CLASSICAL_SOURCE_CITATION,
                **computed,
            }
            row["graha_positions_jsonb"] = json.dumps(row["graha_positions_jsonb"])
            row["ephemeris_audit_jsonb"] = json.dumps(row["ephemeris_audit_jsonb"])
            all_rows.append(row)

        with conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, all_rows)

        logger.info(
            "[ka_tithi_pravesha] %d praveśa-year rows for chart %s (years 1..%d, %d divergent_flagged)",
            len(all_rows), chart_id, DEFAULT_MAX_PRAVESHA_YEAR, divergent,
        )
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=len(all_rows),
            notes=f"max_pravesha_year={DEFAULT_MAX_PRAVESHA_YEAR};divergent_flagged={divergent}",
        )
