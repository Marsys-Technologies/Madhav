"""
bo_samvada — Chart Digest View (L2 Bodha UCD surface)
======================================================
Creates or replaces the `vw_chart_digest` VIEW that aggregates the entire
Bodha layer for a chart into a compact, LLM-friendly digest:

  vw_chart_digest columns:
    chart_id, ayanamsha_id,
    msr_signal_count, top_signal_ids[10],
    top_5_yogas TEXT[], top_5_doshas TEXT[],
    domain_summary JSONB,           ← {domain: {count, score}}
    convergence_leaders JSONB,      ← [{domain, score, count}] top 5
    contradiction_count INT,
    rm_priority_class TEXT,         ← highest priority class across resonances
    weakest_graha TEXT,
    scorecard_trap1_count INT,
    scored_at TIMESTAMPTZ

This is a DDL-only writer: it emits CREATE OR REPLACE VIEW and returns
rows_inserted = 1 if the view was created successfully (0 on dry_run).

The bo_samvada asset in the orchestrator registry counts rows in the
view (via count_sql) to signal success. B5 must update count_sql
to use: SELECT count(*) FROM vw_chart_digest WHERE chart_id = '<canonical>'

LIGHT writer.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_samvada_v1.0"

# ── View DDL ───────────────────────────────────────────────────────────────────

_CREATE_VIEW = """
CREATE OR REPLACE VIEW vw_chart_digest AS
SELECT
  m.chart_id,
  m.ayanamsha_id,
  count(*) AS msr_signal_count,
  array_agg(m.signal_id ORDER BY m.top_k_salience_rank NULLS LAST) FILTER (WHERE m.top_k_salience_rank <= 10)
    AS top_10_signal_ids,
  array_agg(m.signal_type_id ORDER BY m.computed_salience DESC NULLS LAST) FILTER (WHERE m.signal_type_class = 'yoga')
    AS yoga_signals,
  array_agg(m.signal_type_id ORDER BY m.computed_salience DESC NULLS LAST) FILTER (WHERE m.signal_type_class = 'dosha')
    AS dosha_signals,
  jsonb_object_agg(
    cv.domain,
    jsonb_build_object('convergence_count', cv.convergence_count, 'convergence_score', cv.convergence_score)
    ORDER BY cv.convergence_score DESC
  ) FILTER (WHERE cv.domain IS NOT NULL) AS domain_summary,
  (
    SELECT jsonb_agg(j ORDER BY (j->>'convergence_score')::numeric DESC)
    FROM (
      SELECT jsonb_build_object(
        'domain',    cv2.domain,
        'score',     cv2.convergence_score,
        'count',     cv2.convergence_count
      ) AS j
      FROM bodha_convergence cv2
      WHERE cv2.chart_id = m.chart_id AND cv2.ayanamsha_id = m.ayanamsha_id
        AND cv2.snapshot_type = 'static_natal'
      ORDER BY cv2.convergence_score DESC
      LIMIT 5
    ) t
  ) AS convergence_leaders,
  (
    SELECT count(*) FROM bodha_contradictions bc
    WHERE bc.chart_id = m.chart_id AND bc.ayanamsha_id = m.ayanamsha_id
  ) AS contradiction_count,
  (
    SELECT MIN(rm.remedy_priority_class)
    FROM bodha_rm_resonances rm
    WHERE rm.chart_id = m.chart_id AND rm.ayanamsha_id = m.ayanamsha_id
      AND rm.weakest_rank_in_chart = 1
  ) AS rm_top_priority_class,
  (
    SELECT rm.graha FROM bodha_rm_resonances rm
    WHERE rm.chart_id = m.chart_id AND rm.ayanamsha_id = m.ayanamsha_id
    ORDER BY rm.weakest_rank_in_chart ASC NULLS LAST
    LIMIT 1
  ) AS weakest_graha,
  (
    SELECT sc.trap1_authority_inversion_count
    FROM synthesis_quality_scorecard sc
    WHERE sc.chart_id = m.chart_id
    ORDER BY sc.scored_at DESC
    LIMIT 1
  ) AS scorecard_trap1_count,
  NOW() AS viewed_at
FROM bodha_msr_signals m
LEFT JOIN bodha_convergence cv
  ON cv.chart_id = m.chart_id
  AND cv.ayanamsha_id = m.ayanamsha_id
  AND cv.snapshot_type = 'static_natal'
GROUP BY m.chart_id, m.ayanamsha_id, cv.domain, cv.convergence_count, cv.convergence_score
"""

# Simplified, single-group-by version:
_CREATE_VIEW_CLEAN = """
CREATE OR REPLACE VIEW vw_chart_digest AS
SELECT
  m.chart_id,
  m.ayanamsha_id,
  count(DISTINCT m.signal_id)                                      AS msr_signal_count,
  count(DISTINCT m.signal_id) FILTER (WHERE m.signal_type_class = 'yoga')  AS yoga_count,
  count(DISTINCT m.signal_id) FILTER (WHERE m.signal_type_class = 'dosha') AS dosha_count,
  round(avg(m.computed_salience), 4)                               AS avg_salience,
  round(max(m.computed_salience), 4)                               AS max_salience,
  (
    SELECT count(*) FROM bodha_contradictions bc
    WHERE bc.chart_id = m.chart_id AND bc.ayanamsha_id = m.ayanamsha_id
  )                                                                AS contradiction_count,
  (
    SELECT rm.graha FROM bodha_rm_resonances rm
    WHERE rm.chart_id = m.chart_id AND rm.ayanamsha_id = m.ayanamsha_id
    ORDER BY rm.weakest_rank_in_chart ASC NULLS LAST LIMIT 1
  )                                                                AS weakest_graha,
  (
    SELECT rm.remedy_priority_class FROM bodha_rm_resonances rm
    WHERE rm.chart_id = m.chart_id AND rm.ayanamsha_id = m.ayanamsha_id
    ORDER BY rm.weakest_rank_in_chart ASC NULLS LAST LIMIT 1
  )                                                                AS top_priority_class,
  (
    SELECT jsonb_agg(
      jsonb_build_object('domain', cv2.domain, 'score', cv2.convergence_score, 'n', cv2.convergence_count)
      ORDER BY cv2.convergence_score DESC
    )
    FROM bodha_convergence cv2
    WHERE cv2.chart_id = m.chart_id AND cv2.ayanamsha_id = m.ayanamsha_id
      AND cv2.snapshot_type = 'static_natal'
    LIMIT 5
  )                                                                AS top_convergence_domains,
  (
    SELECT sc.trap1_authority_inversion_count
    FROM synthesis_quality_scorecard sc
    WHERE sc.chart_id = m.chart_id
    ORDER BY sc.scored_at DESC LIMIT 1
  )                                                                AS trap1_count,
  NOW()                                                            AS digest_at
FROM bodha_msr_signals m
GROUP BY m.chart_id, m.ayanamsha_id
"""


@register("bo_samvada")
class BoSamvadaWriter(WriterBase):
    """
    bo_samvada: creates vw_chart_digest view (UCD read surface).
    DDL-only writer; rows_inserted = 1 on success.
    """
    asset_id = "bo_samvada"

    def run(self, ctx: ContextSpec) -> WriterResult:
        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="dry_run — would CREATE OR REPLACE VIEW vw_chart_digest")

        conn = ctx.db_conn
        try:
            conn.execute(_CREATE_VIEW_CLEAN)
            logger.info("[bo_samvada] vw_chart_digest created/replaced")
            return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                                notes="vw_chart_digest created")
        except Exception as e:
            logger.error("[bo_samvada] failed to create view: %s", e)
            raise
