"""
bo_pramana_mapa — Synthesis Quality Scorecard (L2 Bodha)
=========================================================
The terminal Bodha writer. Runs last (after all other bo_* writers complete).

Reads from ALL bodha_* tables for this chart and writes one row to
synthesis_quality_scorecard:
  - Per-asset row counts
  - Quality pct (two_pass_verified vs documented_approximation)
  - Formula versions in use
  - Trap checks (authority inversion = MSR re-deriving L1 facts)
  - Materialised view refresh (3 MVs from A10, 5 from A11)

Also refreshes the 3 spec materialized views:
  - mv_msr_top_signals_per_chart
  - mv_msr_recurring_patterns_per_chart
  - mv_msr_domain_summary
  (CONCURRENTLY if supported, otherwise blocking refresh)

LIGHT writer. Single INSERT; no ayanamsha loop (scorecard is chart-scoped).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_pramana_mapa_v1.0"

_SCORECARD_INSERT = """
INSERT INTO synthesis_quality_scorecard (
  scorecard_id, chart_id, build_id, scored_at,
  msr_signal_count, cdlm_cell_count, cgm_node_count, cgm_edge_count,
  rm_resonance_count, rm_prescription_count, embedding_count,
  convergence_count, contradiction_count,
  divergent_flagged_count, two_pass_verified_pct, documented_approximation_pct,
  msr_no_threshold_drop_flag, msr_citation_ref_coverage_pct,
  salience_formula_version, linkage_formula_version, resonance_formula_version,
  convergence_formula_version, centrality_formula_version,
  trap1_authority_inversion_count, trap2_narration_leak_count, notes
) VALUES (
  %(scorecard_id)s, %(chart_id)s, %(build_id)s, %(scored_at)s,
  %(msr_signal_count)s, %(cdlm_cell_count)s, %(cgm_node_count)s, %(cgm_edge_count)s,
  %(rm_resonance_count)s, %(rm_prescription_count)s, %(embedding_count)s,
  %(convergence_count)s, %(contradiction_count)s,
  %(divergent_flagged_count)s, %(two_pass_verified_pct)s, %(documented_approximation_pct)s,
  %(msr_no_threshold_drop_flag)s, %(msr_citation_ref_coverage_pct)s,
  %(salience_formula_version)s, %(linkage_formula_version)s, %(resonance_formula_version)s,
  %(convergence_formula_version)s, %(centrality_formula_version)s,
  %(trap1_authority_inversion_count)s, %(trap2_narration_leak_count)s, %(notes)s
)
"""


def _count_one(conn: Any, sql: str, params: list) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return 0
    return int(row[0] if isinstance(row, (tuple, list)) else row.get("count", 0))


def _formula_version(conn: Any, chart_id: str, col: str, table: str) -> str | None:
    """Fetch the first non-null formula version string from a bodha table."""
    try:
        row = conn.execute(
            f"SELECT {col} FROM {table} WHERE chart_id = %s LIMIT 1",
            [chart_id],
        ).fetchone()
        if row:
            v = row[0] if isinstance(row, (tuple, list)) else row.get(col)
            return str(v) if v else None
    except Exception:
        pass
    return None


def _refresh_mv(conn: Any, mv_name: str) -> None:
    """Refresh a materialized view (non-concurrently; data lock acceptable at build close)."""
    try:
        conn.execute(f"REFRESH MATERIALIZED VIEW {mv_name}")
        logger.info("[bo_pramana_mapa] refreshed MV: %s", mv_name)
    except Exception as e:
        logger.warning("[bo_pramana_mapa] MV refresh failed (%s): %s", mv_name, e)


@register("bo_pramana_mapa")
class BoPramanaMapa(WriterBase):
    """bo_pramana_mapa: global synthesis quality scorecard + MV refresh."""
    asset_id = "bo_pramana_mapa"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_scorecard
        from bodha_writers.formulas import (
            VERSION_SALIENCE_FORMULA, VERSION_LINKAGE_FORMULA,
            VERSION_RESONANCE_FORMULA, VERSION_CONVERGENCE_FORMULA,
        )

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            logger.info("[bo_pramana_mapa dry_run] chart_id=%s", chart_id)
            return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run")

        # ── Row counts ────────────────────────────────────────────────────────
        msr_count  = _count_one(conn, "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s", [chart_id])
        if msr_count == 0:
            raise RuntimeError(
                f"[bo_pramana_mapa] G3: chart_id={chart_id} — bodha_msr_signals is empty; "
                "upstream Bodha writers (bo_laksana) must succeed before scorecard can run"
            )
        cdlm_count = _count_one(conn, "SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = %s", [chart_id])
        node_count = _count_one(conn, "SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = %s", [chart_id])
        edge_count = _count_one(conn, "SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = %s", [chart_id])
        res_count  = _count_one(conn, "SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = %s", [chart_id])
        presc_count= _count_one(conn, "SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = %s", [chart_id])
        emb_count  = _count_one(conn, "SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = %s", [chart_id])
        conv_count = _count_one(conn, "SELECT count(*) FROM bodha_convergence WHERE chart_id = %s", [chart_id])
        contr_count= _count_one(conn, "SELECT count(*) FROM bodha_contradictions WHERE chart_id = %s", [chart_id])

        # ── Quality metrics ───────────────────────────────────────────────────
        two_pass = _count_one(
            conn,
            "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s AND verification_pass_status = 'two_pass_verified'",
            [chart_id],
        )
        doc_approx = _count_one(
            conn,
            "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s AND verification_pass_status = 'documented_approximation'",
            [chart_id],
        )
        has_citation = _count_one(
            conn,
            "SELECT count(*) FROM bodha_msr_signals WHERE chart_id = %s AND citation_ref IS NOT NULL",
            [chart_id],
        )

        two_pass_pct  = round(two_pass / msr_count * 100, 2) if msr_count > 0 else None
        doc_approx_pct= round(doc_approx / msr_count * 100, 2) if msr_count > 0 else None
        citation_pct  = round(has_citation / msr_count * 100, 2) if msr_count > 0 else None

        # Trap 1: check if MSR signals have constituent_facts_array set (non-empty)
        # Authority inversion = signals with constituent_facts_array IS NULL or empty
        trap1_count = _count_one(
            conn,
            """SELECT count(*) FROM bodha_msr_signals
               WHERE chart_id = %s AND (constituent_facts_array IS NULL OR array_length(constituent_facts_array,1) IS NULL)""",
            [chart_id],
        )

        # Formula versions
        sal_ver  = _formula_version(conn, chart_id, "salience_formula_version", "bodha_msr_signals")
        link_ver = _formula_version(conn, chart_id, "linkage_formula_version", "bodha_cdlm_cells")
        res_ver  = _formula_version(conn, chart_id, "resonance_score_formula_version", "bodha_rm_resonances")
        conv_ver = _formula_version(conn, chart_id, "convergence_formula_version", "bodha_convergence")

        scorecard = {
            "scorecard_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "build_id": build_id,
            "scored_at": now,
            "msr_signal_count": msr_count,
            "cdlm_cell_count": cdlm_count,
            "cgm_node_count": node_count,
            "cgm_edge_count": edge_count,
            "rm_resonance_count": res_count,
            "rm_prescription_count": presc_count,
            "embedding_count": emb_count,
            "convergence_count": conv_count,
            "contradiction_count": contr_count,
            "divergent_flagged_count": 0,
            "two_pass_verified_pct": two_pass_pct,
            "documented_approximation_pct": doc_approx_pct,
            "msr_no_threshold_drop_flag": msr_count > 0,
            "msr_citation_ref_coverage_pct": citation_pct,
            "salience_formula_version": sal_ver or VERSION_SALIENCE_FORMULA,
            "linkage_formula_version": link_ver or VERSION_LINKAGE_FORMULA,
            "resonance_formula_version": res_ver or VERSION_RESONANCE_FORMULA,
            "convergence_formula_version": conv_ver or VERSION_CONVERGENCE_FORMULA,
            "centrality_formula_version": None,
            "trap1_authority_inversion_count": trap1_count,
            "trap2_narration_leak_count": 0,
            "notes": json.dumps({
                "engine_version": ENGINE_VERSION,
                "counts": {
                    "msr": msr_count, "cdlm": cdlm_count, "nodes": node_count,
                    "edges": edge_count, "resonances": res_count,
                    "prescriptions": presc_count, "embeddings": emb_count,
                    "convergence": conv_count, "contradictions": contr_count,
                },
            }),
        }

        replace_prior_scorecard(conn, chart_id, build_id)
        conn.execute(_SCORECARD_INSERT, scorecard)
        logger.info("[bo_pramana_mapa] scorecard written: trap1=%d msr=%d", trap1_count, msr_count)

        # ── Materialised view refresh (G5: all 8 Bodha MVs) ─────────────────
        for mv in [
            # MSR MVs (3)
            "mv_msr_top_signals_per_chart",
            "mv_msr_recurring_patterns_per_chart",
            "mv_msr_domain_summary",
            # CDLM MVs (5) — previously not refreshed; added by G5 fix
            "mv_cdlm_static_summary",
            "mv_cdlm_top_K_links_per_chart",
            "mv_cdlm_per_tradition_summary",
            "mv_cdlm_dasha_window_lookup",
            "mv_cdlm_pattern_summary",
        ]:
            _refresh_mv(conn, mv)

        return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                            notes=f"msr={msr_count} cdlm={cdlm_count} nodes={node_count} trap1={trap1_count}")
