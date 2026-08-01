"""
services/ka_kota_chakra/writer.py — WriterBase subclass for `ka_kota_chakra`
(ṢAḌ-DARŚANA W3, registry item 16). Pure logic lives in ./logic.py (DB-free,
unit-tested); this module is the DB-touching shell.

Contract adherence (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - Uses ctx.db_conn (caller-owned) for all DB access; NEVER commits/closes it.
  - NEVER writes asset_throughput.
  - Idempotency: per-chart delete-then-insert (§N.3) — DELETE FROM
    kala_kota_chakra WHERE chart_id = %s immediately before INSERT.
  - LIGHT writer (single run() call) — data volume is small (9 grahas x a
    handful of ring-runs over the scanned horizon, typically 15-40 rows/chart).

── DATA SOURCES (§N.5 — L1/L0 is the authority; nothing here is recomputed) ──
  - Janma nakshatra: chart_facts (fact_category='graha_position',
    fact_subject='MOON', fact_key='longitude_sidereal', ayanamsha_id=
    CANONICAL_AYANAMSHA) — the L1-authoritative natal Moon sidereal longitude,
    written by ga_positions. nakshatra_idx is DERIVED from this longitude via
    the SAME `floor(lon / (360/27))` formula brahmagyan.l0_ephemeris.
    derive_sidereal uses internally — not a second, independent nakshatra
    computation, just an index read off an already-computed longitude.
  - Transiting positions: ephemeris_daily (bg_ephemeris, global L0), tropical
    longitudes, ayanamsha-corrected at read time via
    brahmagyan.l0_ephemeris.derive_sidereal — the SAME primitive
    services/ka_graha_sancara/engine.py's PATH-A read uses. A single
    ayanamsha offset is computed once (at the horizon's reference date) and
    applied uniformly across the whole scanned horizon: ayanamsha drift is
    ~50 arcsec/year, i.e. <0.02 deg over this writer's ~460-day horizon —
    negligible next to a 13.33-deg nakshatra span, and day-grade precision is
    what this campaign requires pre-W2G (SHAD_DARSHANA_BRIEF_v2_0.md §4: "No
    wave may be designed to REQUIRE sub-day precision"). This avoids ~9 x
    460 individual swisseph ayanamsha calls in favour of one.

Scope note (single ayanamsha): this writer computes against ONE canonical
ayanamsha (lahiri_chitrapaksha, the project default), matching the L3
convention already used by ka_avadhi/ka_gochara_resonance (NOT the L2 bo_*
5-ayanamsha loop convention) — a deliberate, disclosed scope choice, not an
oversight. Multi-ayanamsha support is a natural, additive follow-on.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_graha_sancara.engine import ALL_GRAHAS, NAKSHATRAS, NAK_SIZE_DEG
from services.ka_kota_chakra.logic import (
    attack_defence_reading,
    count_from_janma,
    detect_ring_runs,
    ring_for_count,
)

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_kota_chakra_v1.0"
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

# Scanned horizon around "now" at build time (see module docstring). Not a
# W2G sub-day precision claim — day-grade, consistent with the campaign's
# day-grade-first discipline.
HORIZON_BACK_DAYS = 60
HORIZON_FORWARD_DAYS = 400

RING_TABLE_CITATION = (
    "Kota-Chakra ring table (Stambha 4/11/18/25th, Durgantara 3/5/10/12/17/19/24/26th, "
    "Prakara 2/6/9/13/16/20/23/27th from janma nakshatra, Bahya = remainder) — tier-(iii) "
    "secondary-source transcription per the W3K citation hierarchy "
    "(SHAD_DARSHANA_BRIEF_v2_0.md §3 W3K); NOT YET traced to a primary ingested classical "
    "text. Corpus-ingestion gap filed; see services/ka_kota_chakra/logic.py docstring."
)

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

_DELETE_SQL = "DELETE FROM kala_kota_chakra WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO kala_kota_chakra (
    chart_id, ayanamsha_id, graha, nakshatra_idx, nakshatra_name,
    count_from_janma, kota_ring, is_natural_malefic, posture, severity,
    window_start, window_end, start_truncated, end_truncated,
    janma_nakshatra_fact_id, ring_table_citation, uncited_extension, formula_version
) VALUES (
    %(chart_id)s, %(ayanamsha_id)s, %(graha)s, %(nakshatra_idx)s, %(nakshatra_name)s,
    %(count_from_janma)s, %(kota_ring)s, %(is_natural_malefic)s, %(posture)s, %(severity)s,
    %(window_start)s, %(window_end)s, %(start_truncated)s, %(end_truncated)s,
    %(janma_nakshatra_fact_id)s, %(ring_table_citation)s, %(uncited_extension)s, %(formula_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, graha, window_start) DO NOTHING
"""


def _fetch_janma_nakshatra_idx(conn: Any, chart_id: str) -> tuple[int, str] | None:
    """Returns (0-based nakshatra_idx, fact_id) for the natal Moon, or None if
    the L1 dependency (ga_positions) has not produced this fact — honest
    absence, never fabricated (B.10)."""
    with conn.cursor() as cur:
        cur.execute(_FETCH_JANMA_MOON_SQL, (chart_id, CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if not row or row[1] is None:
        return None
    lon = float(row[1])
    nak_idx = int(lon // NAK_SIZE_DEG) % 27
    return nak_idx, str(row[0])


def _compute_ayanamsha_offset(reference_date: date) -> float:
    from brahmagyan.l0_ephemeris import _tropical_to_jd, derive_sidereal

    jd = _tropical_to_jd(reference_date)
    return derive_sidereal(0.0, jd, CANONICAL_AYANAMSHA)["ayanamsha_offset"]


def _fetch_daily_nak_idx_by_graha(
    conn: Any, horizon_start: date, horizon_end: date, offset: float,
) -> dict[str, list[tuple[date, int]]]:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_EPHEMERIS_RANGE_SQL, (horizon_start, horizon_end, list(ALL_GRAHAS)))
        rows = cur.fetchall()

    by_graha: dict[str, list[tuple[date, int]]] = {g: [] for g in ALL_GRAHAS}
    for r in rows:
        graha = r["body"]
        if graha not in by_graha:
            continue
        sid_lon = (float(r["tropical_longitude"]) - offset) % 360.0
        nak_idx = int(sid_lon // NAK_SIZE_DEG) % 27
        by_graha[graha].append((r["date"], nak_idx))
    return by_graha


@register("ka_kota_chakra")
class KaKotaChakraWriter(WriterBase):
    """ka_kota_chakra — Kota-Chakra fort chart (L3 Kāla, item 16). LIGHT writer."""

    asset_id = "ka_kota_chakra"

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        if ctx.dry_run:
            logger.info("[ka_kota_chakra] dry_run=True — skipping")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run=True")

        janma = _fetch_janma_nakshatra_idx(conn, chart_id)
        if janma is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="no natal MOON longitude_sidereal fact — run ga_positions first",
            )
        janma_nak_idx, janma_fact_id = janma

        today = date.today()
        horizon_start = today - timedelta(days=HORIZON_BACK_DAYS)
        horizon_end = today + timedelta(days=HORIZON_FORWARD_DAYS)

        offset = _compute_ayanamsha_offset(today)
        daily_by_graha = _fetch_daily_nak_idx_by_graha(conn, horizon_start, horizon_end, offset)

        # Idempotency: per-chart delete-then-insert (§N.3)
        with conn.cursor() as cur:
            cur.execute(_DELETE_SQL, (chart_id,))

        all_rows: list[dict] = []
        grahas_with_data = 0
        for graha in ALL_GRAHAS:
            daily = daily_by_graha.get(graha) or []
            if not daily:
                continue
            grahas_with_data += 1
            runs = detect_ring_runs(daily, horizon_start=horizon_start, horizon_end=horizon_end)
            for run in runs:
                count = count_from_janma(run["nakshatra_idx"], janma_nak_idx)
                ring = ring_for_count(count)
                reading = attack_defence_reading(graha, ring)
                all_rows.append({
                    "chart_id": chart_id,
                    "ayanamsha_id": CANONICAL_AYANAMSHA,
                    "graha": graha,
                    "nakshatra_idx": run["nakshatra_idx"],
                    "nakshatra_name": NAKSHATRAS[run["nakshatra_idx"]],
                    "count_from_janma": count,
                    "kota_ring": ring,
                    "is_natural_malefic": reading["is_natural_malefic"],
                    "posture": reading["posture"],
                    "severity": reading["severity"],
                    "window_start": run["start_date"],
                    "window_end": run["end_date"],
                    "start_truncated": run["start_truncated"],
                    "end_truncated": run["end_truncated"],
                    "janma_nakshatra_fact_id": janma_fact_id,
                    "ring_table_citation": RING_TABLE_CITATION,
                    "uncited_extension": True,  # the posture/severity synthesis — see logic.py docstring
                    "formula_version": FORMULA_VERSION,
                })

        if not all_rows:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"no ephemeris_daily rows for horizon {horizon_start}..{horizon_end} — "
                      "run bg_ephemeris first",
            )

        with conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, all_rows)

        logger.info(
            "[ka_kota_chakra] %d ring-run rows for chart %s across %d/%d grahas",
            len(all_rows), chart_id, grahas_with_data, len(ALL_GRAHAS),
        )
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=len(all_rows),
            notes=f"grahas_with_data={grahas_with_data}/{len(ALL_GRAHAS)};"
                  f"horizon={horizon_start}..{horizon_end}",
        )
