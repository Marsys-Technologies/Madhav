"""
services/ka_sudarshana_varsha/writer.py — WriterBase subclass for
`ka_sudarshana_varsha` (ṢAḌ-DARŚANA W3, registry item 17). Pure logic lives
in ./logic.py (DB-free, unit-tested); this module is the DB-touching shell.

Contract adherence (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - Uses ctx.db_conn (caller-owned) for all DB access; NEVER commits/closes it.
  - NEVER writes asset_throughput.
  - Idempotency: per-chart delete-then-insert (§N.3) — DELETE FROM
    kala_sudarshana_varsha WHERE chart_id = %s immediately before INSERT.
  - LIGHT writer — 120 rows/chart (one per varsha year, full lifespan), pure
    arithmetic, no ephemeris calls at all.

── DATA SOURCES (§N.5 — L1 is the authority) ─────────────────────────────────
Natal Janma Lagna / Chandra Lagna / Sūrya Lagna sign indices are read
VERBATIM from chart_facts (fact_category='graha_position', fact_key='sign',
fact_subject in {LAGNA, MOON, SUN}, ayanamsha_id=CANONICAL_AYANAMSHA) — the
SAME fact rows bo_sudarshana.py (L2) already reads for its own, unrelated
static computation (confirms the namesake-collision-only finding: same input
facts, categorically different computation — see logic.py docstring). Sign
NAMES are converted to indices via the same SIGNS ordering
services/ka_graha_sancara/engine.py uses (Aries=0..Pisces=11) — never a second
independent sign-index derivation.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_graha_sancara.engine import SIGNS
from services.ka_sudarshana_varsha.logic import (
    DEFAULT_MAX_VARSHA_YEAR,
    compute_tri_lagna_year,
    varsha_window,
)

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_sudarshana_varsha_v1.0"
CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

_FETCH_NATAL_SIGNS_SQL = """
SELECT fact_id, fact_subject, fact_value_text
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_key = 'sign'
  AND fact_subject IN ('LAGNA', 'MOON', 'SUN')
"""

_DELETE_SQL = "DELETE FROM kala_sudarshana_varsha WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO kala_sudarshana_varsha (
    chart_id, ayanamsha_id, varsha_year, window_start, window_end,
    jl_natal_sign_idx, cl_natal_sign_idx, sl_natal_sign_idx,
    jl_active_sign_idx, cl_active_sign_idx, sl_active_sign_idx,
    jl_active_sign_name, cl_active_sign_name, sl_active_sign_name,
    tri_lagna_convergence, lagna_fact_id, moon_fact_id, sun_fact_id, formula_version
) VALUES (
    %(chart_id)s, %(ayanamsha_id)s, %(varsha_year)s, %(window_start)s, %(window_end)s,
    %(jl_natal_sign_idx)s, %(cl_natal_sign_idx)s, %(sl_natal_sign_idx)s,
    %(jl_active_sign_idx)s, %(cl_active_sign_idx)s, %(sl_active_sign_idx)s,
    %(jl_active_sign_name)s, %(cl_active_sign_name)s, %(sl_active_sign_name)s,
    %(tri_lagna_convergence)s, %(lagna_fact_id)s, %(moon_fact_id)s, %(sun_fact_id)s, %(formula_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, varsha_year) DO NOTHING
"""


def _sign_idx(sign_name: str) -> int | None:
    try:
        return SIGNS.index(sign_name)
    except ValueError:
        return None


def _fetch_natal_reference_signs(conn: Any, chart_id: str) -> dict[str, dict] | None:
    """Returns {'LAGNA': {...}, 'MOON': {...}, 'SUN': {...}} or None if any
    are missing (honest absence — B.10, never fabricated)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_NATAL_SIGNS_SQL, (chart_id, CANONICAL_AYANAMSHA))
        rows = cur.fetchall()
    by_subject: dict[str, dict] = {}
    for r in rows:
        idx = _sign_idx(r["fact_value_text"])
        if idx is None:
            continue
        by_subject[r["fact_subject"]] = {"sign_idx": idx, "fact_id": str(r["fact_id"])}
    if not all(k in by_subject for k in ("LAGNA", "MOON", "SUN")):
        return None
    return by_subject


def _birth_date_from_config(ctx) -> date | None:
    """§N.2: writers get chart_id + birth_params from ctx.config.
    `birth_params` is the shape `pipeline/orchestrator/birth_params.py`'s
    `_to_birth_params` produces: {'datetime_iso': ..., 'latitude_deg': ...,
    ...} — this reads its `datetime_iso` field and takes the calendar-date
    component (the varsha-year wheel only needs the birth DATE, not the
    exact instant). Returns None (honest absence, B.10) if birth_params is
    genuinely missing or unparsable — never guesses a birth date."""
    birth_params = ctx.config.get("birth_params") or {}
    raw = birth_params.get("datetime_iso")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


@register("ka_sudarshana_varsha")
class KaSudarshanaVarshaWriter(WriterBase):
    """ka_sudarshana_varsha — Sudarśana-Chakra year-wheel (L3 Kāla, item 17). LIGHT writer."""

    asset_id = "ka_sudarshana_varsha"

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        if ctx.dry_run:
            logger.info("[ka_sudarshana_varsha] dry_run=True — skipping")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run=True")

        birth_date = _birth_date_from_config(ctx)
        if birth_date is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="ctx.config['birth_params'] missing/unparsable birth_date",
            )

        natal = _fetch_natal_reference_signs(conn, chart_id)
        if natal is None:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="missing natal LAGNA/MOON/SUN sign facts — run ga_positions first",
            )

        jl_idx = natal["LAGNA"]["sign_idx"]
        cl_idx = natal["MOON"]["sign_idx"]
        sl_idx = natal["SUN"]["sign_idx"]

        # Idempotency: per-chart delete-then-insert (§N.3)
        with conn.cursor() as cur:
            cur.execute(_DELETE_SQL, (chart_id,))

        all_rows: list[dict] = []
        for varsha_year in range(1, DEFAULT_MAX_VARSHA_YEAR + 1):
            year_result = compute_tri_lagna_year(varsha_year, jl_idx, cl_idx, sl_idx)
            window_start, window_end = varsha_window(birth_date, varsha_year)
            all_rows.append({
                "chart_id": chart_id,
                "ayanamsha_id": CANONICAL_AYANAMSHA,
                "varsha_year": varsha_year,
                "window_start": window_start,
                "window_end": window_end,
                "jl_natal_sign_idx": jl_idx,
                "cl_natal_sign_idx": cl_idx,
                "sl_natal_sign_idx": sl_idx,
                "jl_active_sign_idx": year_result["jl_active_sign_idx"],
                "cl_active_sign_idx": year_result["cl_active_sign_idx"],
                "sl_active_sign_idx": year_result["sl_active_sign_idx"],
                "jl_active_sign_name": SIGNS[year_result["jl_active_sign_idx"]],
                "cl_active_sign_name": SIGNS[year_result["cl_active_sign_idx"]],
                "sl_active_sign_name": SIGNS[year_result["sl_active_sign_idx"]],
                "tri_lagna_convergence": year_result["tri_lagna_convergence"],
                "lagna_fact_id": natal["LAGNA"]["fact_id"],
                "moon_fact_id": natal["MOON"]["fact_id"],
                "sun_fact_id": natal["SUN"]["fact_id"],
                "formula_version": FORMULA_VERSION,
            })

        with conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, all_rows)

        logger.info(
            "[ka_sudarshana_varsha] %d varsha-year rows for chart %s (years 1..%d)",
            len(all_rows), chart_id, DEFAULT_MAX_VARSHA_YEAR,
        )
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=len(all_rows),
            notes=f"max_varsha_year={DEFAULT_MAX_VARSHA_YEAR}",
        )
