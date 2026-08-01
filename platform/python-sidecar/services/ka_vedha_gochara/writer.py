"""
services/ka_vedha_gochara/writer.py — WriterBase subclass for
`ka_vedha_gochara` (ṢAḌ-DARŚANA W3, registry item 5 — closes defect R-19).
Pure logic lives in ./logic.py (DB-free, unit-tested); this module is the
DB-touching shell. See logic.py's module docstring FIRST for the full R-19
honesty disclosure — it is load-bearing for understanding what this writer
does and does not close.

Contract adherence (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - Uses ctx.db_conn (caller-owned) for all DB access; NEVER commits/closes it.
  - NEVER writes asset_throughput.
  - Idempotency: per-chart delete-then-insert (§N.3) — DELETE FROM
    kala_vedha_gochara WHERE chart_id = %s immediately before INSERT.
  - LIGHT writer (single run() call) — small data volume: house_vedha rows
    are gated on `bg_transit_rules` having a vedha-checkable rule for the
    (graha, house) pair (~a few per graha), sarvatobhadra rows are gated on
    a graha actually dwelling in the one vedha nakshatra per scanned
    horizon (a handful across all 9 grahas, since only ~1/27 of any given
    horizon falls in that specific nakshatra per graha).

── DATA SOURCES (§N.5 — L1/L0 is the authority; nothing here is recomputed) ──
  - Janma reference: chart_facts (fact_category='graha_position',
    fact_subject='MOON', fact_key='longitude_sidereal') — the SAME natal
    Moon longitude fact ka_kota_chakra/ka_moorti_nirnaya read, used here for
    BOTH the house_vedha house-counting reference (Moon's SIGN) and the
    sarvatobhadra nakshatra reference (Moon's NAKSHATRA) — one L1 fact, two
    derived indices, never two independent fetches or a second "natal Moon"
    concept.
  - House-vedha rules: bg_transit_rules (rule_type='favourable', vedha_house
    IS NOT NULL) — REAL, cited (BPHS Ch.29 / Phaladeepika Ch.26), read
    verbatim, never re-derived.
  - Sarvatobhadra vedha nakshatra: services/gochara_grammar/sarvatobhadra.py
    `opposite_nakshatra_id` (or, if ever populated, `_vedha_pairs_from_db`
    via the SAME function, reused unchanged) — the existing, already-honestly
    -disclosed algorithmic approximation; see logic.py's R-19 section for
    why this writer does not attempt to populate a "real" 9x9 grid table.
  - Transiting positions: ephemeris_daily (bg_ephemeris, global L0), tropical
    longitudes, ayanamsha-corrected via brahmagyan.l0_ephemeris.derive_sidereal
    — same primitive ka_kota_chakra/ka_moorti_nirnaya use, single ayanamsha
    offset computed once at the horizon's reference date (disclosed
    day-grade scope, matching campaign convention).
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_graha_sancara.engine import ALL_GRAHAS, NAKSHATRAS, NAK_SIZE_DEG, SIGNS
from services.ka_vedha_gochara.logic import (
    HOUSE_VEDHA,
    SARVATOBHADRA,
    detect_sign_runs,
    house_from_moon,
    overlap_window,
    sign_from_house,
)
from services.gochara_grammar.sarvatobhadra import _vedha_pairs_from_db, opposite_nakshatra_id
from services.gochara_grammar import citations as C

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_vedha_gochara_v1.0"
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

SIGN_SIZE_DEG = 30.0

# Scanned horizon around "now" at build time — matches ka_kota_chakra/
# ka_moorti_nirnaya's own convention exactly (day-grade, not a W2G sub-day
# precision claim).
HORIZON_BACK_DAYS = 60
HORIZON_FORWARD_DAYS = 400

SARVATOBHADRA_CITATION = C.SARVATOBHADRA_VEDHA_PRASNA_MARGA

_FETCH_JANMA_MOON_SQL = """
SELECT fact_id, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_subject = 'MOON' AND fact_key = 'longitude_sidereal'
"""

_FETCH_VEDHA_RULES_SQL = """
SELECT graha, primary_house, vedha_house, phala, classical_citation
FROM bg_transit_rules
WHERE rule_type = 'favourable' AND vedha_house IS NOT NULL
"""

_FETCH_EPHEMERIS_RANGE_SQL = """
SELECT date, body, tropical_longitude
FROM ephemeris_daily
WHERE ayanamsha_id = 'tropical' AND date BETWEEN %s AND %s AND body = ANY(%s)
ORDER BY body, date
"""

_DELETE_SQL = "DELETE FROM kala_vedha_gochara WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO kala_vedha_gochara (
    chart_id, ayanamsha_id, vedha_kind, graha,
    window_start, window_end, start_truncated, end_truncated,
    janma_reference_fact_id, classical_citation, uncited_extension,
    detail, formula_version
) VALUES (
    %(chart_id)s, %(ayanamsha_id)s, %(vedha_kind)s, %(graha)s,
    %(window_start)s, %(window_end)s, %(start_truncated)s, %(end_truncated)s,
    %(janma_reference_fact_id)s, %(classical_citation)s, %(uncited_extension)s,
    %(detail)s::jsonb, %(formula_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, vedha_kind, graha, window_start) DO NOTHING
"""


def _fetch_janma_moon(conn: Any, chart_id: str) -> tuple[int, int, str] | None:
    """Returns (moon_sign_idx 0-11, moon_nak_idx 0-26, fact_id) for the natal
    Moon, or None if the L1 dependency (ga_positions) has not produced this
    fact — honest absence, never fabricated (B.10)."""
    with conn.cursor() as cur:
        cur.execute(_FETCH_JANMA_MOON_SQL, (chart_id, CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if not row or row[1] is None:
        return None
    lon = float(row[1])
    sign_idx = int(lon // SIGN_SIZE_DEG) % 12
    nak_idx = int(lon // NAK_SIZE_DEG) % 27
    return sign_idx, nak_idx, str(row[0])


def _compute_ayanamsha_offset(reference_date: date) -> float:
    from brahmagyan.l0_ephemeris import _tropical_to_jd, derive_sidereal

    jd = _tropical_to_jd(reference_date)
    return derive_sidereal(0.0, jd, CANONICAL_AYANAMSHA)["ayanamsha_offset"]


def _fetch_vedha_rules(conn: Any) -> dict[tuple[str, int], dict[str, Any]]:
    """Returns {(graha_lower, primary_house): {vedha_house, phala,
    classical_citation}} — REAL, cited bg_transit_rules rows, read verbatim
    (§N.5)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_VEDHA_RULES_SQL)
        rows = cur.fetchall()
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for r in rows:
        key = (str(r["graha"]).lower(), int(r["primary_house"]))
        out[key] = dict(r)
    return out


def _fetch_daily_sidereal_by_body(
    conn: Any, horizon_start: date, horizon_end: date, offset: float, bodies: tuple[str, ...],
) -> dict[str, list[tuple[date, float]]]:
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


@register("ka_vedha_gochara")
class KaVedhaGocharaWriter(WriterBase):
    """ka_vedha_gochara — Vedha application + Sarvatobhadra (L3 Kāla, item 5,
    closes R-19). LIGHT writer."""

    asset_id = "ka_vedha_gochara"

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        if ctx.dry_run:
            logger.info("[ka_vedha_gochara] dry_run=True — skipping")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run=True")

        janma = _fetch_janma_moon(conn, chart_id)
        if janma is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="no natal MOON longitude_sidereal fact — run ga_positions first",
            )
        janma_moon_sign_idx, janma_moon_nak_idx, janma_fact_id = janma

        vedha_rules = _fetch_vedha_rules(conn)
        if not vedha_rules:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="bg_transit_rules has no vedha-checkable (favourable + vedha_house) "
                      "rows — run bg_transit_rules (L0 seed) first",
            )

        today = date.today()
        horizon_start = today - timedelta(days=HORIZON_BACK_DAYS)
        horizon_end = today + timedelta(days=HORIZON_FORWARD_DAYS)

        offset = _compute_ayanamsha_offset(today)
        daily_by_body = _fetch_daily_sidereal_by_body(conn, horizon_start, horizon_end, offset, ALL_GRAHAS)

        if not any(daily_by_body.values()):
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"no ephemeris_daily rows for horizon {horizon_start}..{horizon_end} — "
                      "run bg_ephemeris first",
            )

        # Per-graha sign runs and nakshatra runs, computed once and reused by
        # both vedha_kind branches below (no repeat ephemeris derivation).
        sign_runs_by_graha: dict[str, list[dict]] = {}
        nak_runs_by_graha: dict[str, list[dict]] = {}
        for graha in ALL_GRAHAS:
            daily = daily_by_body.get(graha) or []
            if not daily:
                continue
            daily_sign = [(d, int(lon // SIGN_SIZE_DEG) % 12) for d, lon in daily]
            daily_nak = [(d, int(lon // NAK_SIZE_DEG) % 27) for d, lon in daily]
            sign_runs_by_graha[graha] = detect_sign_runs(
                daily_sign, horizon_start=horizon_start, horizon_end=horizon_end,
            )
            nak_runs_by_graha[graha] = detect_sign_runs(
                daily_nak, horizon_start=horizon_start, horizon_end=horizon_end,
            )

        # Vedha-target nakshatra: the SBC vedha nakshatra of the janma nakshatra.
        # Tries the DB-sourced path FIRST (l1_sarvatobhadra_vedha), exactly
        # mirroring sarvatobhadra.py::find_sarvatobhadra_vedha_states's own
        # primary/fallback order — this is what makes the R-19 disclosure's
        # "becomes the primary path automatically, zero code change" claim
        # actually true, rather than aspirational. As of this writing that
        # table is confirmed empty (see logic.py's R-19 section), so
        # db_sourced is False and the algorithmic approximation is used; if a
        # native-approved table is ever populated, this call starts returning
        # real pairs with no writer change required. (opposite_nakshatra_id /
        # _vedha_pairs_from_db are both 1-based; convert both ways.)
        vedha_nak_idx_1based = _vedha_pairs_from_db(conn, janma_moon_nak_idx + 1)
        db_sourced = vedha_nak_idx_1based is not None
        if vedha_nak_idx_1based is None:
            vedha_nak_idx_1based = opposite_nakshatra_id(janma_moon_nak_idx + 1)
        vedha_nak_idx = vedha_nak_idx_1based - 1

        all_rows: list[dict] = []

        # ── house_vedha ────────────────────────────────────────────────────
        for graha, runs in sign_runs_by_graha.items():
            graha_lower = graha.lower()
            for run in runs:
                house = house_from_moon(run["sign_idx"], janma_moon_sign_idx)
                rule = vedha_rules.get((graha_lower, house))
                if rule is None:
                    continue  # not a vedha-checkable transit — out of scope (logic.py)

                vedha_house = int(rule["vedha_house"])
                vedha_sign_idx = sign_from_house(janma_moon_sign_idx, vedha_house)

                obstruction_active = False
                obstructing_graha = None
                obstruction_start = None
                obstruction_end = None
                for other_graha, other_runs in sign_runs_by_graha.items():
                    if other_graha == graha:
                        continue
                    for other_run in other_runs:
                        if other_run["sign_idx"] != vedha_sign_idx:
                            continue
                        ov = overlap_window(
                            run["start_date"], run["end_date"],
                            other_run["start_date"], other_run["end_date"],
                        )
                        if ov is not None:
                            obstruction_active = True
                            obstructing_graha = other_graha
                            obstruction_start = ov["start"]
                            obstruction_end = ov["end"]
                            break
                    if obstruction_active:
                        break

                all_rows.append({
                    "chart_id": chart_id,
                    "ayanamsha_id": CANONICAL_AYANAMSHA,
                    "vedha_kind": HOUSE_VEDHA,
                    "graha": graha,
                    "window_start": run["start_date"],
                    "window_end": run["end_date"],
                    "start_truncated": run["start_truncated"],
                    "end_truncated": run["end_truncated"],
                    "janma_reference_fact_id": janma_fact_id,
                    "classical_citation": rule.get("classical_citation") or C.PHALADEEPIKA_VEDHA_26,
                    "uncited_extension": False,
                    "detail": {
                        "primary_house": house,
                        "primary_sign_idx": run["sign_idx"],
                        "primary_sign_name": SIGNS[run["sign_idx"]],
                        "vedha_house": vedha_house,
                        "vedha_sign_idx": vedha_sign_idx,
                        "vedha_sign_name": SIGNS[vedha_sign_idx],
                        "phala": rule.get("phala"),
                        "obstruction_active": obstruction_active,
                        "obstructing_graha": obstructing_graha,
                        "obstruction_window_start": obstruction_start.isoformat() if obstruction_start else None,
                        "obstruction_window_end": obstruction_end.isoformat() if obstruction_end else None,
                    },
                    "formula_version": FORMULA_VERSION,
                })

        # ── sarvatobhadra (R-19; see logic.py for the full honesty disclosure) ──
        for graha, runs in nak_runs_by_graha.items():
            for run in runs:
                if run["sign_idx"] != vedha_nak_idx:  # field is generically named; holds nak_idx here
                    continue
                all_rows.append({
                    "chart_id": chart_id,
                    "ayanamsha_id": CANONICAL_AYANAMSHA,
                    "vedha_kind": SARVATOBHADRA,
                    "graha": graha,
                    "window_start": run["start_date"],
                    "window_end": run["end_date"],
                    "start_truncated": run["start_truncated"],
                    "end_truncated": run["end_truncated"],
                    "janma_reference_fact_id": janma_fact_id,
                    "classical_citation": SARVATOBHADRA_CITATION,
                    "uncited_extension": True,
                    "detail": {
                        "target_nakshatra_idx": janma_moon_nak_idx,
                        "target_nakshatra_name": NAKSHATRAS[janma_moon_nak_idx],
                        "vedha_nakshatra_idx": vedha_nak_idx,
                        "vedha_nakshatra_name": NAKSHATRAS[vedha_nak_idx],
                        "vedha_pair_source": "algorithmic_opposition_approximation",
                        "cancellation_effect": (
                            f"While {graha} dwells in {NAKSHATRAS[vedha_nak_idx]} "
                            f"(vedha to the janma nakshatra {NAKSHATRAS[janma_moon_nak_idx]}), "
                            "primary gochara results are classically held to be obstructed."
                        ),
                        "r19_disclosure": (
                            "l1_sarvatobhadra_positions/l1_sarvatobhadra_vedha (the REAL 9x9-grid "
                            "tables) remain unpopulated — no ingested-corpus or responsibly-"
                            "transcribable secondary source was available this session. This row "
                            "is the existing, already-disclosed algorithmic opposition "
                            "approximation (services/gochara_grammar/sarvatobhadra.py), now served "
                            "live per-chart for the first time. See ka_vedha_gochara/logic.py "
                            "module docstring for the full R-19 disclosure."
                        ),
                    },
                    "formula_version": FORMULA_VERSION,
                })

        if not all_rows:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="no vedha-checkable house transit and no sarvatobhadra-vedha-nakshatra "
                      f"dwelling found in horizon {horizon_start}..{horizon_end}",
            )

        # Idempotency: per-chart delete-then-insert (§N.3)
        with conn.cursor() as cur:
            cur.execute(_DELETE_SQL, (chart_id,))

        for row in all_rows:
            row["detail"] = json.dumps(row["detail"])

        with conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, all_rows)

        house_count = sum(1 for r in all_rows if r["vedha_kind"] == HOUSE_VEDHA)
        sbc_count = sum(1 for r in all_rows if r["vedha_kind"] == SARVATOBHADRA)
        logger.info(
            "[ka_vedha_gochara] %d rows (%d house_vedha, %d sarvatobhadra) for chart %s",
            len(all_rows), house_count, sbc_count, chart_id,
        )
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=len(all_rows),
            notes=f"house_vedha={house_count};sarvatobhadra={sbc_count};"
                  f"horizon={horizon_start}..{horizon_end}",
        )
