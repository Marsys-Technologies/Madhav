"""
services/ka_moorti_nirnaya/writer.py — WriterBase subclass for
`ka_moorti_nirnaya` (ṢAḌ-DARŚANA W3, registry item 4). Pure logic lives in
./logic.py (DB-free, unit-tested); this module is the DB-touching shell.

Contract adherence (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - Uses ctx.db_conn (caller-owned) for all DB access; NEVER commits/closes it.
  - NEVER writes asset_throughput.
  - Idempotency: per-chart delete-then-insert (§N.3) — DELETE FROM
    kala_moorti_nirnaya WHERE chart_id = %s immediately before INSERT.
  - LIGHT writer (single run() call) — small data volume (8 grahas x a
    handful of sign-runs over the scanned horizon, typically 15-60 rows/chart:
    slow movers 0-1 ingress, Mercury/Venus/Mars several including retrograde
    reversals).

── DATA SOURCES (§N.5 — L1/L0 is the authority; nothing here is recomputed) ──
  - Janma nakshatra: chart_facts (fact_category='graha_position',
    fact_subject='MOON', fact_key='longitude_sidereal', ayanamsha_id=
    CANONICAL_AYANAMSHA) — the SAME L1-authoritative fetch
    ka_kota_chakra.writer._fetch_janma_nakshatra_idx uses (mirrored here,
    not imported, per this campaign's established one-writer-per-module
    convention — see ka_sudarshana_varsha/ka_kota_chakra precedent).
  - Transiting positions: ephemeris_daily (bg_ephemeris, global L0), tropical
    longitudes, ayanamsha-corrected at read time via
    brahmagyan.l0_ephemeris.derive_sidereal — same primitive
    ka_kota_chakra.writer uses. One ayanamsha offset computed at the
    horizon's reference date and applied uniformly (same disclosed
    day-grade/single-offset scope as ka_kota_chakra — negligible drift over
    a ~460-day horizon, day-grade being what this campaign requires
    pre-W2G).
  - Moorti quality table: bg_transit_moorti (migration 401) — REAL, cited
    (Phaladeepika Ch.26; BPHS Ch.28), 27 rows, read verbatim and NEVER
    re-derived (§N.5). If a nakshatra_offset has no matching row (should not
    happen — the table is a total 1..27 function — but honest defensive
    handling per B.10), the row's moorti fields are left None rather than
    guessed.

Scope note (single ayanamsha, 8-of-9 grahas): see logic.py module docstring.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_graha_sancara.engine import NAKSHATRAS, NAK_SIZE_DEG, SIGNS
from services.ka_moorti_nirnaya.logic import (
    MOORTI_GRAHAS,
    detect_sign_runs,
    nakshatra_offset_from_janma,
)

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_moorti_nirnaya_v1.0"
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

SIGN_SIZE_DEG = 30.0

# Scanned horizon around "now" at build time — matches ka_kota_chakra's own
# convention exactly (day-grade, not a W2G sub-day precision claim).
HORIZON_BACK_DAYS = 60
HORIZON_FORWARD_DAYS = 400

_FETCH_JANMA_MOON_SQL = """
SELECT fact_id, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_subject = 'MOON' AND fact_key = 'longitude_sidereal'
"""

_FETCH_EPHEMERIS_RANGE_SQL = """
SELECT date, body, tropical_longitude
FROM ephemeris_daily
WHERE ayanamsha_id = 'tropical' AND date BETWEEN %s AND %s AND body = ANY(%s)
ORDER BY body, date
"""

_FETCH_MOORTI_TABLE_SQL = """
SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation
FROM bg_transit_moorti
"""

_DELETE_SQL = "DELETE FROM kala_moorti_nirnaya WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO kala_moorti_nirnaya (
    chart_id, ayanamsha_id, graha, target_sign_idx, target_sign_name,
    window_start, window_end, start_truncated, end_truncated,
    moorti_computed, moon_nakshatra_idx_at_ingress, moon_nakshatra_name_at_ingress,
    janma_nakshatra_idx, janma_nakshatra_fact_id, nakshatra_offset,
    moorti_name, quality_tier, phala_brief, moorti_classical_citation, formula_version
) VALUES (
    %(chart_id)s, %(ayanamsha_id)s, %(graha)s, %(target_sign_idx)s, %(target_sign_name)s,
    %(window_start)s, %(window_end)s, %(start_truncated)s, %(end_truncated)s,
    %(moorti_computed)s, %(moon_nakshatra_idx_at_ingress)s, %(moon_nakshatra_name_at_ingress)s,
    %(janma_nakshatra_idx)s, %(janma_nakshatra_fact_id)s, %(nakshatra_offset)s,
    %(moorti_name)s, %(quality_tier)s, %(phala_brief)s, %(moorti_classical_citation)s, %(formula_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, graha, window_start) DO NOTHING
"""


def _fetch_janma_nakshatra_idx(conn: Any, chart_id: str) -> tuple[int, str] | None:
    """Returns (0-based nakshatra_idx, fact_id) for the natal Moon, or None if
    the L1 dependency (ga_positions) has not produced this fact — honest
    absence, never fabricated (B.10)."""
    # DB9: the orchestrator connection is created with row_factory=dict_row, so a
    # bare conn.cursor() yields dict rows and positional row[1] raised KeyError: 1,
    # failing the whole asset. Pin the factory explicitly (the convention already
    # used elsewhere in this file) and read by column name.
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_JANMA_MOON_SQL, (chart_id, CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if not row or row["fact_value_num"] is None:
        return None
    lon = float(row["fact_value_num"])
    nak_idx = int(lon // NAK_SIZE_DEG) % 27
    return nak_idx, str(row["fact_id"])


def _compute_ayanamsha_offset(reference_date: date) -> float:
    from brahmagyan.l0_ephemeris import _tropical_to_jd, derive_sidereal

    jd = _tropical_to_jd(reference_date)
    return derive_sidereal(0.0, jd, CANONICAL_AYANAMSHA)["ayanamsha_offset"]


def _fetch_daily_sidereal_by_body(
    conn: Any, horizon_start: date, horizon_end: date, offset: float, bodies: tuple[str, ...],
) -> dict[str, list[tuple[date, float]]]:
    """Returns {body: [(date, sidereal_longitude_deg), ...]} for every
    requested body over the horizon, sorted ascending by date."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_EPHEMERIS_RANGE_SQL, (horizon_start, horizon_end, list(bodies)))
        rows = cur.fetchall()

    by_body: dict[str, list[tuple[date, float]]] = {b: [] for b in bodies}
    for r in rows:
        body = r["body"]
        if body not in by_body:
            continue
        sid_lon = (float(r["tropical_longitude"]) - offset) % 360.0
        by_body[body].append((r["date"], sid_lon))
    return by_body


def _fetch_moorti_table(conn: Any) -> dict[int, dict[str, Any]]:
    """Reads bg_transit_moorti verbatim (§N.5 — L0 reference, never
    re-derived). Returns {nakshatra_offset (1..27): {moorti_name,
    quality_tier, phala_brief, classical_citation}}."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_MOORTI_TABLE_SQL)
        rows = cur.fetchall()
    return {int(r["nakshatra_offset"]): dict(r) for r in rows}


@register("ka_moorti_nirnaya")
class KaMoortiNirnayaWriter(WriterBase):
    """ka_moorti_nirnaya — Moorti-nirṇaya per ingress (L3 Kāla, item 4). LIGHT writer."""

    asset_id = "ka_moorti_nirnaya"

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        if ctx.dry_run:
            logger.info("[ka_moorti_nirnaya] dry_run=True — skipping")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run=True")

        janma = _fetch_janma_nakshatra_idx(conn, chart_id)
        if janma is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="no natal MOON longitude_sidereal fact — run ga_positions first",
            )
        janma_nak_idx, janma_fact_id = janma

        moorti_table = _fetch_moorti_table(conn)
        if not moorti_table:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="bg_transit_moorti is empty — run bg_transit_rules (L0 seed) first",
            )

        today = date.today()
        horizon_start = today - timedelta(days=HORIZON_BACK_DAYS)
        horizon_end = today + timedelta(days=HORIZON_FORWARD_DAYS)

        offset = _compute_ayanamsha_offset(today)
        bodies_needed = MOORTI_GRAHAS + ("Moon",)
        daily_by_body = _fetch_daily_sidereal_by_body(conn, horizon_start, horizon_end, offset, bodies_needed)

        moon_daily = daily_by_body.get("Moon") or []
        moon_nak_by_date: dict[date, int] = {
            d: int(lon // NAK_SIZE_DEG) % 27 for d, lon in moon_daily
        }

        # Idempotency: per-chart delete-then-insert (§N.3)
        with conn.cursor() as cur:
            cur.execute(_DELETE_SQL, (chart_id,))

        all_rows: list[dict] = []
        grahas_with_data = 0
        for graha in MOORTI_GRAHAS:
            daily = daily_by_body.get(graha) or []
            if not daily:
                continue
            grahas_with_data += 1
            daily_sign_idx = [(d, int(lon // SIGN_SIZE_DEG) % 12) for d, lon in daily]
            runs = detect_sign_runs(daily_sign_idx, horizon_start=horizon_start, horizon_end=horizon_end)

            for run in runs:
                moorti_computed = not run["start_truncated"]
                row: dict[str, Any] = {
                    "chart_id": chart_id,
                    "ayanamsha_id": CANONICAL_AYANAMSHA,
                    "graha": graha,
                    "target_sign_idx": run["sign_idx"],
                    "target_sign_name": SIGNS[run["sign_idx"]],
                    "window_start": run["start_date"],
                    "window_end": run["end_date"],
                    "start_truncated": run["start_truncated"],
                    "end_truncated": run["end_truncated"],
                    "moorti_computed": moorti_computed,
                    "moon_nakshatra_idx_at_ingress": None,
                    "moon_nakshatra_name_at_ingress": None,
                    "janma_nakshatra_idx": janma_nak_idx,
                    "janma_nakshatra_fact_id": janma_fact_id,
                    "nakshatra_offset": None,
                    "moorti_name": None,
                    "quality_tier": None,
                    "phala_brief": None,
                    "moorti_classical_citation": None,
                    "formula_version": FORMULA_VERSION,
                }

                if moorti_computed:
                    moon_nak_idx = moon_nak_by_date.get(run["start_date"])
                    if moon_nak_idx is not None:
                        offset_key = nakshatra_offset_from_janma(moon_nak_idx, janma_nak_idx)
                        moorti_row = moorti_table.get(offset_key)
                        if moorti_row is not None:
                            # Every field below is populated together — the
                            # migration's kala_moorti_nirnaya_computed_consistency
                            # CHECK constraint requires moorti_computed=true to
                            # imply ALL of these are non-null, never a partial set.
                            row["moon_nakshatra_idx_at_ingress"] = moon_nak_idx
                            row["moon_nakshatra_name_at_ingress"] = NAKSHATRAS[moon_nak_idx]
                            row["nakshatra_offset"] = offset_key
                            row["moorti_name"] = moorti_row["moorti_name"]
                            row["quality_tier"] = moorti_row["quality_tier"]
                            row["phala_brief"] = moorti_row["phala_brief"]
                            row["moorti_classical_citation"] = moorti_row["classical_citation"]
                        else:
                            # Defensive-only: bg_transit_moorti is a total 1..27
                            # function; a missing key here would mean the L0
                            # seed is itself incomplete. Honest gap, not guessed
                            # — row["moorti_computed"] stays False and every
                            # moorti-derived field stays at its None default
                            # (set above), matching the CHECK constraint.
                            row["moorti_computed"] = False
                    else:
                        # No Moon ephemeris row for this exact date (gap in
                        # ephemeris_daily) — honest gap, not guessed.
                        row["moorti_computed"] = False

                all_rows.append(row)

        if not all_rows:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"no ephemeris_daily rows for horizon {horizon_start}..{horizon_end} — "
                      "run bg_ephemeris first",
            )

        with conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, all_rows)

        computed_count = sum(1 for r in all_rows if r["moorti_computed"])
        logger.info(
            "[ka_moorti_nirnaya] %d sign-run rows (%d moorti-computed) for chart %s across %d/%d grahas",
            len(all_rows), computed_count, chart_id, grahas_with_data, len(MOORTI_GRAHAS),
        )
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=len(all_rows),
            notes=f"grahas_with_data={grahas_with_data}/{len(MOORTI_GRAHAS)};"
                  f"moorti_computed={computed_count}/{len(all_rows)};"
                  f"horizon={horizon_start}..{horizon_end}",
        )
