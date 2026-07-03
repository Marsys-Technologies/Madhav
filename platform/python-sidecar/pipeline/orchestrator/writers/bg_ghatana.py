"""
bg_ghatana writer — populates brahma_event_ontology (22 life-event classes)
and brahma_activity_ontology (12 electional activity classes).

Source data: brahmagyan.l0_ghatana — W1 seed package §5–§6.

§N.3: L0 idempotency — ON CONFLICT DO UPDATE (global, not per-chart).
§N.2: Frozen orchestrator contract — run(ctx) → WriterResult, never commits.
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_ghatana import seed_ghatana

logger = logging.getLogger(__name__)


@register('bg_ghatana')
class GhatanaWriter(WriterBase):
    asset_id = 'bg_ghatana'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_ghatana(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=ctx.dry_run,
            autocommit=False,
        )
        events     = counts.get("brahma_event_ontology", 0)
        activities = counts.get("brahma_activity_ontology", 0)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=events,
            duration_seconds=time.time() - t0,
            notes=f"brahma_event_ontology: {events} events; brahma_activity_ontology: {activities} activities",
        )
