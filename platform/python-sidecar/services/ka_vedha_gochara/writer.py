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
  - ADJUDICATION-11 additions (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md,
    supplemental ruling after PR #1009): bg_sarvatobhadra_grid (migration
    527, school-tagged, tried FIRST, deliberately empty as of this writing)
    · bg_vedha_malefic_scale (migration 528, Phaladeepika PG353, REAL cited)
    · bg_phaladeepika_latta (migration 528, Phaladeepika PG338-339, REAL
    cited, Ketu deliberately absent). See logic.py's own ADJUDICATION-11
    section for the full disclosure.
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
    LATTA,
    NATURAL_MALEFICS,
    SARVATOBHADRA,
    detect_sign_runs,
    house_from_moon,
    latta_nakshatra_idx,
    malefic_count_grade,
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

# ADJUDICATION-11 additions ───────────────────────────────────────────────────

_FETCH_GRID_VEDHA_PAIR_SQL = """
SELECT cell_value, school_tag
FROM bg_sarvatobhadra_grid
WHERE cell_kind = 'vedha_pair' AND cell_index = %s
ORDER BY table_version DESC
LIMIT 1
"""

_FETCH_LATTA_RULES_SQL = """
SELECT graha, count_from_graha, direction, effect_description, affliction_condition, source_citation
FROM bg_phaladeepika_latta
"""

_FETCH_MALEFIC_SCALE_SQL = """
SELECT malefic_count, effect_grade, effect_description, source_citation
FROM bg_vedha_malefic_scale
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


def _fetch_school_tagged_vedha_pair(conn: Any, nakshatra_id_1based: int) -> tuple[int, str] | None:
    """ADJUDICATION-11 Part 2: tries `bg_sarvatobhadra_grid` (school-tagged,
    deliberately empty as of this writing — migration 527) for a
    `cell_kind='vedha_pair'` row. Returns (paired_nakshatra_id_1based,
    school_tag), or None if the table has no matching row (the honest, only
    -currently-possible outcome). A future native-approved, source-verified
    school's grid activates this path with zero code change."""
    with conn.cursor() as cur:
        cur.execute(_FETCH_GRID_VEDHA_PAIR_SQL, (nakshatra_id_1based,))
        row = cur.fetchone()
    if not row or row[0] is None:
        return None
    try:
        return int(row[0]), str(row[1])
    except (TypeError, ValueError):
        return None


def _fetch_latta_rules(conn: Any) -> dict[str, dict[str, Any]]:
    """Returns {graha: {count_from_graha, direction, effect_description,
    affliction_condition, source_citation}} — REAL, cited
    bg_phaladeepika_latta rows (ADJUDICATION-11 Part 4), read verbatim
    (§N.5). Ketu is deliberately absent from the table (see
    brahmagyan/l0_phaladeepika_vedha.py) — this dict simply will not have a
    'Ketu' key, and the writer's Latta loop below naturally skips it."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_LATTA_RULES_SQL)
        rows = cur.fetchall()
    return {str(r["graha"]): dict(r) for r in rows}


def _fetch_malefic_scale(conn: Any) -> dict[int, dict[str, Any]]:
    """Returns {malefic_count: {effect_grade, effect_description,
    source_citation}} — REAL, cited bg_vedha_malefic_scale rows
    (ADJUDICATION-11 Part 4, Phaladeepika PG353), read verbatim (§N.5)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_MALEFIC_SCALE_SQL)
        rows = cur.fetchall()
    return {int(r["malefic_count"]): dict(r) for r in rows}


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

        # ADJUDICATION-11 Part 4: the two cited-reference tables. Neither being
        # empty is fatal to the whole writer — house_vedha/sarvatobhadra still
        # serve honestly; only the malefic-count grading / latta kind are
        # skipped, each with its own coverage note (never silently degraded).
        malefic_scale = _fetch_malefic_scale(conn)
        latta_rules = _fetch_latta_rules(conn)

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
        # ADJUDICATION-11 Part 2: THREE tiers, tried in order, each already
        # wired so a future populated source activates with zero code change:
        #   1. bg_sarvatobhadra_grid (school-tagged, migration 527) — the
        #      ruling's own affirmed "DB-sourced-grid-first path".
        #   2. l1_sarvatobhadra_vedha (migration _archive/140, the original
        #      fallback sarvatobhadra.py::find_sarvatobhadra_vedha_states uses).
        #   3. The disclosed algorithmic opposition approximation.
        # As of this writing BOTH DB tables are confirmed empty (see logic.py's
        # R-19 section), so grid_basis='algorithmic_approximation' and
        # grid_school_tag=None on every sarvatobhadra row — machine-readable,
        # per ADJUDICATION-11 Part 3, never prose-only. (opposite_nakshatra_id
        # / _vedha_pairs_from_db / the grid table are all 1-based; convert
        # both ways.)
        grid_school_tag: str | None = None
        grid_pair = _fetch_school_tagged_vedha_pair(conn, janma_moon_nak_idx + 1)
        if grid_pair is not None:
            vedha_nak_idx_1based, grid_school_tag = grid_pair
            grid_basis = "db_sourced_grid"
        else:
            vedha_nak_idx_1based = _vedha_pairs_from_db(conn, janma_moon_nak_idx + 1)
            if vedha_nak_idx_1based is not None:
                grid_basis = "db_sourced_grid"
            else:
                vedha_nak_idx_1based = opposite_nakshatra_id(janma_moon_nak_idx + 1)
                grid_basis = "algorithmic_approximation"
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

                # Collect EVERY overlapping occupant (not just the first) so the
                # ADJUDICATION-11 malefic-count grading below has a real count to
                # grade, not just a boolean.
                obstruction_active = False
                obstructing_graha = None
                obstruction_start = None
                obstruction_end = None
                malefic_occupants: list[str] = []
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
                        if ov is None:
                            continue
                        if not obstruction_active:
                            obstruction_active = True
                            obstructing_graha = other_graha
                            obstruction_start = ov["start"]
                            obstruction_end = ov["end"]
                        if other_graha in NATURAL_MALEFICS and other_graha not in malefic_occupants:
                            malefic_occupants.append(other_graha)

                # ADJUDICATION-11 Part 4: PG353 malefic-count -> effect-grade
                # scale. The REFERENCE TABLE (bg_vedha_malefic_scale) is REAL
                # and cited; APPLYING it here — to an ordinary transit vedha,
                # not the verse's literal "at the time of a battle" context —
                # is this writer's own extension of scope, disclosed via
                # `malefic_grade_uncited_extension` (nested, distinct from the
                # row-level `uncited_extension=False`, which covers the
                # house_vedha rule itself, unaffected by this addition).
                malefic_count = len(malefic_occupants)
                grade_row = malefic_count_grade(malefic_count, malefic_scale) if malefic_count > 0 else None

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
                        "malefic_obstructing_grahas": malefic_occupants,
                        "malefic_count": malefic_count,
                        "malefic_effect_grade": grade_row["effect_grade"] if grade_row else None,
                        "malefic_effect_description": grade_row["effect_description"] if grade_row else None,
                        "malefic_scale_citation": grade_row["source_citation"] if grade_row else None,
                        "malefic_grade_uncited_extension": grade_row is not None,
                    },
                    "formula_version": FORMULA_VERSION,
                })

        # ── sarvatobhadra (R-19; see logic.py for the full honesty disclosure) ──
        # ADJUDICATION-11 Part 3: uncited_extension reflects grid_basis — False
        # (a real, cited source) only when a school-tagged/DB-sourced pair was
        # actually found; True (the current, only-populated state) for the
        # algorithmic approximation. grid_basis/grid_school_tag are
        # machine-readable data fields (never prose-only), so a caller/census
        # can exclude these rows from a "cited" count without parsing text.
        sarvatobhadra_uncited = grid_basis == "algorithmic_approximation"
        r19_disclosure_text = (
            "no SBC grid in the ingested corpus (8 term hits, all "
            "index/OCR/passing-mention); grid geometry varies by tradition; "
            "served value is an algorithmic approximation, not a transcribed "
            "grid."
        ) if sarvatobhadra_uncited else None
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
                    "uncited_extension": sarvatobhadra_uncited,
                    "detail": {
                        "target_nakshatra_idx": janma_moon_nak_idx,
                        "target_nakshatra_name": NAKSHATRAS[janma_moon_nak_idx],
                        "vedha_nakshatra_idx": vedha_nak_idx,
                        "vedha_nakshatra_name": NAKSHATRAS[vedha_nak_idx],
                        "grid_basis": grid_basis,
                        "grid_school_tag": grid_school_tag,
                        "cancellation_effect": (
                            f"While {graha} dwells in {NAKSHATRAS[vedha_nak_idx]} "
                            f"(vedha to the janma nakshatra {NAKSHATRAS[janma_moon_nak_idx]}), "
                            "primary gochara results are classically held to be obstructed."
                        ),
                        "r19_disclosure": r19_disclosure_text,
                    },
                    "formula_version": FORMULA_VERSION,
                })

        # ── latta (ADJUDICATION-11 Part 4; Phaladeepika PG338-339, REAL,
        # cited; uncited_extension=False) — Ketu is absent from
        # bg_phaladeepika_latta (its own counting rule was not found in the
        # retrieved passage; see brahmagyan/l0_phaladeepika_vedha.py), so
        # `latta_rules.get(graha)` naturally skips it, never guessed.
        for graha, runs in nak_runs_by_graha.items():
            rule = latta_rules.get(graha)
            if rule is None:
                continue  # Ketu, or bg_phaladeepika_latta not yet seeded — honest skip
            for run in runs:
                latta_nak_idx = latta_nakshatra_idx(
                    run["sign_idx"], int(rule["count_from_graha"]), str(rule["direction"]),
                )
                if latta_nak_idx != janma_moon_nak_idx:
                    continue  # affliction fires only when the Latta point IS the janma nakshatra
                all_rows.append({
                    "chart_id": chart_id,
                    "ayanamsha_id": CANONICAL_AYANAMSHA,
                    "vedha_kind": LATTA,
                    "graha": graha,
                    "window_start": run["start_date"],
                    "window_end": run["end_date"],
                    "start_truncated": run["start_truncated"],
                    "end_truncated": run["end_truncated"],
                    "janma_reference_fact_id": janma_fact_id,
                    "classical_citation": rule["source_citation"],
                    "uncited_extension": False,
                    "detail": {
                        "count_from_graha": int(rule["count_from_graha"]),
                        "direction": rule["direction"],
                        "latta_nakshatra_idx": latta_nak_idx,
                        "latta_nakshatra_name": NAKSHATRAS[latta_nak_idx],
                        "janma_nakshatra_idx": janma_moon_nak_idx,
                        "janma_nakshatra_name": NAKSHATRAS[janma_moon_nak_idx],
                        "effect_description": rule["effect_description"],
                        "affliction_condition": rule["affliction_condition"],
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
        latta_count = sum(1 for r in all_rows if r["vedha_kind"] == LATTA)
        logger.info(
            "[ka_vedha_gochara] %d rows (%d house_vedha, %d sarvatobhadra, %d latta) for "
            "chart %s; sbc_grid_basis=%s",
            len(all_rows), house_count, sbc_count, latta_count, chart_id, grid_basis,
        )
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=len(all_rows),
            notes=f"house_vedha={house_count};sarvatobhadra={sbc_count};latta={latta_count};"
                  f"grid_basis={grid_basis};horizon={horizon_start}..{horizon_end}",
        )
