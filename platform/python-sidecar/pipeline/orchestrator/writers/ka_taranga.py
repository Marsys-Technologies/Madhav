"""
ka_taranga — Activation Waveform (L3 Kāla)
============================================
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or closes ctx.db_conn — orchestrator owns the transaction.
NEVER writes to bodha_* tables.

Monthly convolution of dasha × transit × promise activation scores, stored
for months 1950-01 through 2100-12 per scope (domain + event_class).

Three components per month × scope:
  1. dasha_contribution    — fraction of this month's dasha lord(s) that
                             activates the scope's domain/event_class (0–1).
  2. transit_contribution  — mean convergence_score of kala_convergence windows
                             overlapping this month for this scope's domain (0–1).
  3. promise_contribution  — bodha_pratijna grade/10 for this scope (0–1).

activation = harmonic_mean(dasha, transit, promise) where all three > 0,
             else arithmetic mean of available components.

Fine grain (daily/hourly) = SERVICE computation, never stored.
Known Sade-Sati years should show elevated obstruction-adjusted activation
for 'health' and 'karma' domains (exit gate: waveform sanity check).

BA-P5A Step 3. DAG: ka_avadhi → ka_taranga.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Optional

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.taranga_kernel.kernel import GRAHA_DOMAINS as _GRAHA_DOMAINS
from services.taranga_kernel.kernel import harmonic_mean as _harmonic_mean
from services.taranga_kernel.kernel import month_range as _month_range

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_taranga_v1.0"

_WAVEFORM_START = date(1950, 1, 1)
_WAVEFORM_END   = date(2100, 12, 1)

# _GRAHA_DOMAINS, _harmonic_mean, _month_range: shared kernel extraction
# (wave/D-3/T-3) — moved to services.taranga_kernel.kernel so both this batch
# writer AND a live on-demand caller (sibling lane T-2) use the IDENTICAL
# activation-formula primitives. Re-imported under their original local names
# here so every call site below is unchanged (byte-identical output — see
# tests/l3/test_taranga_kernel_extraction.py).

_INSERT_SQL = """
INSERT INTO kala_taranga (
    chart_id, month, scope_kind, scope_id,
    activation, components, formula_version
) VALUES (
    %(chart_id)s, %(month)s, %(scope_kind)s, %(scope_id)s,
    %(activation)s, %(components)s::jsonb, %(formula_version)s
)
ON CONFLICT (chart_id, month, scope_kind, scope_id) DO UPDATE SET
    activation      = EXCLUDED.activation,
    components      = EXCLUDED.components,
    formula_version = EXCLUDED.formula_version,
    computed_at     = NOW()
"""

_BATCH = 2000


@register("ka_taranga")
class KaTarangaWriter(WriterBase):
    """ka_taranga — Activation Waveform (L3 Kāla). LIGHT writer."""

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        # Idempotency: delete-then-insert
        with conn.cursor() as _timeout_cur:
            _timeout_cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_taranga WHERE chart_id = %s", (chart_id,))

        # ── Load raw data ────────────────────────────────────────────────────

        # 1. All MD dasha rows (system=vimshottari for primary dasha contribution)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT lord_graha, start_date AS ds, end_date AS de
                FROM chart_dashas
                WHERE chart_id = %s AND level_n = 1 AND system_id = 'vimshottari'
                ORDER BY start_date
                """,
                (chart_id,),
            )
            vimsh_md = cur.fetchall()

        if not vimsh_md:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="no vimshottari MD rows — run ka_dasha_kala first")

        # 2. Transit windows from kala_convergence (domain × month presence)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT domain, window_start::date, window_end::date, convergence_score
                FROM kala_convergence
                WHERE chart_id = %s AND domain IS NOT NULL
                  AND window_start IS NOT NULL AND window_end IS NOT NULL
                ORDER BY window_start
                """,
                (chart_id,),
            )
            transit_windows = cur.fetchall()

        # 3. Pratijna grades by scope (domain + event_class)
        pratijna_domain: dict[str, float] = {}   # domain → mean grade
        pratijna_ec: dict[str, float] = {}        # event_class_id → grade
        with conn.cursor() as _sp:
            _sp.execute("SAVEPOINT sp_taranga_pratijna")
        try:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT bp.event_class_id, beo.domain, bp.grade
                    FROM bodha_pratijna bp
                    JOIN brahma_event_ontology beo USING (event_class_id)
                    WHERE bp.chart_id = %s
                      AND bp.ayanamsha_id = 'lahiri_chitrapaksha'
                    """,
                    (chart_id,),
                )
                ec_rows = cur.fetchall()
            for r in ec_rows:
                ec_id = r["event_class_id"]
                domain = str(r.get("domain") or "unknown")
                grade = float(r.get("grade") or 0)
                pratijna_ec[ec_id] = grade / 10.0
                pratijna_domain.setdefault(domain, []).append(grade / 10.0)  # type: ignore[arg-type]
            pratijna_domain = {k: sum(v) / len(v) for k, v in pratijna_domain.items()}  # type: ignore[arg-type]
            with conn.cursor() as _sp:
                _sp.execute("RELEASE SAVEPOINT sp_taranga_pratijna")
        except Exception as exc:
            with conn.cursor() as _sp:
                _sp.execute("ROLLBACK TO SAVEPOINT sp_taranga_pratijna")
            logger.debug("ka_taranga: pratijna fetch skipped: %s", exc)

        # ── Build lookup structures ──────────────────────────────────────────

        # dasha lord → which months it covers
        def _lord_for_month(m: date) -> Optional[str]:
            for row in vimsh_md:
                if row["ds"] <= m <= row["de"]:
                    return row["lord_graha"]
            return None

        # transit: month → {domain: mean_convergence_score}
        transit_by_month_domain: dict[date, dict[str, list[float]]] = {}
        for tw in transit_windows:
            ws = tw["window_start"]
            we = tw["window_end"]
            d  = tw.get("domain") or "unknown"
            cs = float(tw.get("convergence_score") or 0)
            for m in _month_range(max(ws, _WAVEFORM_START), min(we, _WAVEFORM_END)):
                transit_by_month_domain.setdefault(m, {}).setdefault(d, []).append(cs)

        # Determine scope lists
        all_domains = sorted(set(
            d for domains in _GRAHA_DOMAINS.values() for d in domains
        ) | set(pratijna_domain.keys()))
        all_event_classes = sorted(pratijna_ec.keys())

        # ── Generate rows ────────────────────────────────────────────────────

        rows_inserted = 0
        batch: list[dict] = []

        def _flush():
            nonlocal rows_inserted
            with conn.cursor() as cur:
                cur.executemany(_INSERT_SQL, batch)
            rows_inserted += len(batch)
            batch.clear()

        for month in _month_range(_WAVEFORM_START, _WAVEFORM_END):
            lord = _lord_for_month(month)
            lord_domains = set(_GRAHA_DOMAINS.get(lord, [])) if lord else set()
            transit_this_month = transit_by_month_domain.get(month, {})

            for domain in all_domains:
                d_contrib = 1.0 if domain in lord_domains else 0.15
                t_vals = transit_this_month.get(domain, [])
                t_contrib = sum(t_vals) / len(t_vals) if t_vals else 0.0
                p_contrib = float(pratijna_domain.get(domain) or 0)
                act = _harmonic_mean([d_contrib, t_contrib, p_contrib]) if p_contrib > 0 \
                    else (d_contrib + t_contrib) / 2.0

                batch.append({
                    "chart_id": chart_id,
                    "month": month,
                    "scope_kind": "domain",
                    "scope_id": domain,
                    "activation": round(min(1.0, max(0.0, act)), 6),
                    "components": json.dumps({
                        "dasha_contribution": round(d_contrib, 4),
                        "transit_contribution": round(t_contrib, 4),
                        "promise_contribution": round(p_contrib, 4),
                        "dasha_lord": lord,
                        "formula_note": FORMULA_VERSION,
                    }),
                    "formula_version": FORMULA_VERSION,
                })
                if len(batch) >= _BATCH:
                    _flush()

            for ec_id in all_event_classes:
                p_contrib = float(pratijna_ec.get(ec_id) or 0)
                d_contrib = 1.0 if lord and any(
                    d in lord_domains for d in _GRAHA_DOMAINS.get(lord, [])
                ) else 0.1
                t_vals = [s for d_vals in transit_this_month.values() for s in d_vals]
                t_contrib = max(t_vals) if t_vals else 0.0
                act = _harmonic_mean([d_contrib, t_contrib, p_contrib]) if p_contrib > 0 \
                    else (d_contrib + t_contrib) / 2.0

                batch.append({
                    "chart_id": chart_id,
                    "month": month,
                    "scope_kind": "event_class",
                    "scope_id": ec_id,
                    "activation": round(min(1.0, max(0.0, act)), 6),
                    "components": json.dumps({
                        "dasha_contribution": round(d_contrib, 4),
                        "transit_contribution": round(t_contrib, 4),
                        "promise_contribution": round(p_contrib, 4),
                        "dasha_lord": lord,
                        "formula_note": FORMULA_VERSION,
                    }),
                    "formula_version": FORMULA_VERSION,
                })
                if len(batch) >= _BATCH:
                    _flush()

        if batch:
            _flush()

        logger.info("[ka_taranga] %d waveform rows for chart %s", rows_inserted, chart_id)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
            notes=f"domains={len(all_domains)};event_classes={len(all_event_classes)};"
                  f"months={((_WAVEFORM_END.year - _WAVEFORM_START.year)*12)}",
        )
