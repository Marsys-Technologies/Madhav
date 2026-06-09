"""
bg_rules writer — populates sutravali_rules via deterministic regex extraction
over classical_text_chunks.

Delegates to brahmagyan.l0_rules.seed_rules() for all INSERT logic.
Per holistic design v1.1: ZERO LLM. extracted_by='python_regex_v2'.

Floor policy: target_floor is set to the ACTUAL produced count by the
writer's own migration (191_bg_rules_floor.sql) — the brief's provisional
1,755 is a placeholder only.

BRAHMA-BG-0-8
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_rules import seed_rules

logger = logging.getLogger(__name__)


@register('bg_rules')
class RulesWriter(WriterBase):
    asset_id = 'bg_rules'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_rules(
            ctx.db_conn,
            ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        rows_ins = counts.get('rows_inserted', 0)
        rows_skip = counts.get('rows_skipped_conflict', 0)
        below = counts.get('rows_below_threshold', 0)
        chunks = counts.get('chunks_processed', 0)
        zero_cov = counts.get('chunks_with_zero_extractions', 0)
        upstream = counts.get('upstream_chunks', 0)
        coverage_pct = (
            (chunks - zero_cov) / max(chunks, 1) * 100
            if chunks else 0.0
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_ins,
            rows_skipped=rows_skip,
            duration_seconds=time.time() - t0,
            notes=(
                f"sutravali_rules: +{rows_ins} inserted / {rows_skip} conflict-skipped; "
                f"below_threshold(0.4–0.6): {below}; "
                f"chunks: {chunks} processed / {zero_cov} zero-extraction; "
                f"coverage: {coverage_pct:.1f}%; "
                f"upstream classical_text_chunks: {upstream}"
            ),
        )
