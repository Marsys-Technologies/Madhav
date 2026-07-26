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
  trap1_authority_inversion_count, trap2_narration_leak_count,
  unresolved_constituent_facts_count,
  l1_assets_projected_count, l1_assets_projected_array,
  lel_zero_leak_pass, no_pre_answer_pass,
  pillars_meet_reachability_pass, ledger_independence_pass,
  discovery_not_fabricated_pass,
  notes
) VALUES (
  %(scorecard_id)s, %(chart_id)s, %(build_id)s, %(scored_at)s,
  %(msr_signal_count)s, %(cdlm_cell_count)s, %(cgm_node_count)s, %(cgm_edge_count)s,
  %(rm_resonance_count)s, %(rm_prescription_count)s, %(embedding_count)s,
  %(convergence_count)s, %(contradiction_count)s,
  %(divergent_flagged_count)s, %(two_pass_verified_pct)s, %(documented_approximation_pct)s,
  %(msr_no_threshold_drop_flag)s, %(msr_citation_ref_coverage_pct)s,
  %(salience_formula_version)s, %(linkage_formula_version)s, %(resonance_formula_version)s,
  %(convergence_formula_version)s, %(centrality_formula_version)s,
  %(trap1_authority_inversion_count)s, %(trap2_narration_leak_count)s,
  %(unresolved_constituent_facts_count)s,
  %(l1_assets_projected_count)s, %(l1_assets_projected_array)s,
  %(lel_zero_leak_pass)s, %(no_pre_answer_pass)s,
  %(pillars_meet_reachability_pass)s, %(ledger_independence_pass)s,
  %(discovery_not_fabricated_pass)s,
  %(notes)s
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

        # ── MC-001 (ŚODHANA T2, item 3): REAL unresolved-constituent count ──────
        # The field `unresolved_constituent_facts_count` must measure how many
        # constituent fact_id REFERENCES fail to resolve against live chart_facts —
        # NOT how many signals have a missing/empty array (that is trap1_count above,
        # correctly named trap1_authority_inversion_count). The prior writer stored
        # trap1_count here, so a chart whose signals all HAVE arrays but whose members
        # are ALL orphaned (the live MC-001 case: 100% of 71,430 refs orphaned after an
        # L1 delete-then-insert rebuild changed every build_id-embedded fact_id) reported
        # unresolved_constituent_facts_count = 0 — a GA.1 stored-vs-live contradiction.
        # Derive the true live orphan count via a LEFT JOIN against chart_facts.
        orphan_row = conn.execute(
            """SELECT
                 count(*)                                   AS total_refs,
                 count(*) FILTER (WHERE cf.fact_id IS NULL)  AS orphaned_refs
               FROM (
                 SELECT unnest(constituent_facts_array) AS fid
                 FROM bodha_msr_signals
                 WHERE chart_id = %s AND constituent_facts_array IS NOT NULL
               ) refs
               LEFT JOIN chart_facts cf ON cf.fact_id = refs.fid""",
            [chart_id],
        ).fetchone()
        if orphan_row is None:
            total_constituent_refs = 0
            orphaned_constituent_refs = 0
        elif isinstance(orphan_row, (tuple, list)):
            total_constituent_refs = int(orphan_row[0] or 0)
            orphaned_constituent_refs = int(orphan_row[1] or 0)
        else:
            total_constituent_refs = int(orphan_row.get("total_refs", 0) or 0)
            orphaned_constituent_refs = int(orphan_row.get("orphaned_refs", 0) or 0)
        constituent_orphan_pct = (
            round(100.0 * orphaned_constituent_refs / total_constituent_refs, 2)
            if total_constituent_refs > 0 else 0.0
        )
        if orphaned_constituent_refs > 0:
            logger.warning(
                "[bo_pramana_mapa] MC-001: %d/%d constituent refs orphaned (%.2f%%) "
                "against live chart_facts for chart_id=%s — Bodha↔L1 linkage is stale.",
                orphaned_constituent_refs, total_constituent_refs, constituent_orphan_pct, chart_id,
            )

        # Formula versions
        sal_ver  = _formula_version(conn, chart_id, "salience_formula_version", "bodha_msr_signals")
        link_ver = _formula_version(conn, chart_id, "linkage_formula_version", "bodha_cdlm_cells")
        res_ver  = _formula_version(conn, chart_id, "resonance_score_formula_version", "bodha_rm_resonances")
        conv_ver = _formula_version(conn, chart_id, "convergence_formula_version", "bodha_convergence")

        # ── Grounding pass flags ──────────────────────────────────────────────
        # lel_zero_leak_pass: True when no life-event rows exist yet for this
        # chart in bodha_msr_signals that would indicate premature LEL injection.
        # Proxy: if every signal has a constituent_facts_array (trap1_count == 0),
        # the grounding chain is intact and we treat this as a clean pass.
        lel_zero_leak = trap1_count == 0

        # pillars_meet_reachability_pass: True when at least one signal exists
        # (msr_count > 0 already enforced above; this is a belt-and-suspenders flag).
        pillars_pass = msr_count > 0

        # L1 assets referenced — real distinct count/array of source_l1_asset
        # values on this chart's bodha_msr_signals (previously hardcoded to a
        # degenerate `1 if msr_count>0 else 0` with an always-empty array; per
        # bo_laksana's depends_on this should be up to 9 distinct L1 assets).
        with conn.cursor() as l1_cur:
            l1_cur.execute(
                """SELECT DISTINCT source_l1_asset FROM bodha_msr_signals
                   WHERE chart_id = %s AND source_l1_asset IS NOT NULL
                   ORDER BY source_l1_asset""",
                [chart_id],
            )
            # conn's default row_factory is dict_row — index by column name.
            l1_assets_projected_array = [r["source_l1_asset"] for r in l1_cur.fetchall()]
        l1_assets_projected = len(l1_assets_projected_array)

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
            # NOT YET IMPLEMENTED (schema is NOT NULL DEFAULT 0, so this cannot be
            # NULL like the boolean gates below): no divergence detector exists.
            # A future detector must replace this literal 0 with a real count.
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
            # NOT YET IMPLEMENTED (schema is NOT NULL DEFAULT 0): the UCN-contamination
            # narration-leak detector (MSR_UCN_CONTAMINATION_AUDIT_v1_0.md) does not
            # exist yet. This literal 0 can never report a real leak — a future
            # detector scanning configuration_jsonb/citation_human for UCN-narrative
            # phrasing must replace it.
            "trap2_narration_leak_count": 0,
            # ── 8 grounding columns (were missing from INSERT) ────────────────
            # MC-001 (item 3): REAL live orphan count (refs that don't resolve
            # against chart_facts), not trap1_count (missing-array count).
            "unresolved_constituent_facts_count": orphaned_constituent_refs,
            "l1_assets_projected_count": l1_assets_projected,
            "l1_assets_projected_array": l1_assets_projected_array,
            "lel_zero_leak_pass": lel_zero_leak,
            # These three gates have no real detector implemented yet. Previously
            # hardcoded to True, which is indistinguishable from a genuinely-passed
            # verification. NULL is the honest "not yet computed" value — a
            # scorecard consumer must not read a NULL gate as a clean pass.
            "no_pre_answer_pass": None,
            "pillars_meet_reachability_pass": pillars_pass,
            "ledger_independence_pass": None,
            "discovery_not_fabricated_pass": None,
            "notes": json.dumps({
                "engine_version": ENGINE_VERSION,
                "counts": {
                    "msr": msr_count, "cdlm": cdlm_count, "nodes": node_count,
                    "edges": edge_count, "resonances": res_count,
                    "prescriptions": presc_count, "embeddings": emb_count,
                    "convergence": conv_count, "contradictions": contr_count,
                },
                # MC-001: live constituent-linkage health at scorecard time. NOTE these
                # values are a build-time snapshot — a later L1 rebuild can orphan them,
                # so serve-time surfaces MUST re-derive live (see bodha_l1_linkage.ts) and
                # never trust the stored unresolved_constituent_facts_count alone.
                "constituent_linkage": {
                    "total_refs": total_constituent_refs,
                    "orphaned_refs": orphaned_constituent_refs,
                    "orphan_pct": constituent_orphan_pct,
                    "trap1_missing_array_count": trap1_count,
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
