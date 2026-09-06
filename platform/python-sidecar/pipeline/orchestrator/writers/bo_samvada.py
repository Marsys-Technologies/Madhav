"""
bo_samvada — Chart Digest View (L2 Bodha UCD surface)
======================================================
Creates or replaces the `vw_chart_digest` VIEW that aggregates the entire
Bodha layer for a chart into a compact, LLM-friendly digest:

  vw_chart_digest columns (matches _CREATE_VIEW_CLEAN below — kept in
  sync here on purpose; NIRMĀṆA L2-W3 S9 found this list stale against
  eight of its own names and corrected it against the live SQL, not a
  prior draft):
    chart_id, ayanamsha_id,
    msr_signal_count INT,            ← DISTINCT signal_id count
    yoga_count INT,                  ← signal_type_class = 'yoga'
    dosha_count INT,                 ← signal_type_class = 'dosha'
    avg_salience NUMERIC,            ← round(avg(computed_salience), 4)
    max_salience NUMERIC,            ← round(max(computed_salience), 4)
    contradiction_count INT,         ← live count from bodha_contradictions
    weakest_graha TEXT,              ← bodha_rm_resonances, rank 1
    top_priority_class TEXT,         ← bodha_rm_resonances, rank 1's remedy_priority_class
    top_convergence_domains JSONB,   ← bodha_convergence, top 5 by score, static_natal snapshot
    trap1_count INT,                 ← synthesis_quality_scorecard.trap1_authority_inversion_count, latest scored_at
    digest_at TIMESTAMPTZ            ← NOW() at view-query time, not build time (a VIEW, not a snapshot)

This is a DDL-only writer: it emits CREATE OR REPLACE VIEW and returns
rows_inserted = 1 if the view was created successfully (0 on dry_run).

The bo_samvada asset in the orchestrator registry counts rows in the
view (via count_sql) to signal success — count_sql already reads
`SELECT count(*) FROM vw_chart_digest WHERE chart_id = '<canonical>'`
(NIRMĀṆA L2-W3 S8, migration 660's expected_volume_formula + the
conformance integrity_check_sql in migration 663 / PR #1843).

POSITION NOTE: bo_samvada is intentionally the LAST bodha asset in execution order.
It is a VIEW definition (DDL, not INSERT) that spans all bodha_* tables. It must
execute only after all upstream data tables are fully populated for the chart.
This is by design — last position in the build plan is correct.
rows_written = 1 (the VIEW itself counts as 1 object created).

LIGHT writer.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_samvada_v1.0"

# ── View DDL ───────────────────────────────────────────────────────────────────
# NOTE: an earlier draft (_CREATE_VIEW) contained a broken GROUP BY that included
# cv.domain, cv.convergence_count, cv.convergence_score — joining those non-aggregate
# columns from bodha_convergence into the outer GROUP BY produced fan-out duplicates.
# That draft was removed; only the corrected single-group-by version below is live.

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
            conn.execute("DROP VIEW IF EXISTS vw_chart_digest CASCADE")
            conn.execute(_CREATE_VIEW_CLEAN)
            logger.info("[bo_samvada] vw_chart_digest created/replaced")
            return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                                notes="vw_chart_digest created")
        except Exception as e:
            logger.error("[bo_samvada] failed to create view: %s", e)
            raise
