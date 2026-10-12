"""
bg_gochara_citation_resolution writer (TI-L0-20, SS Q7) - dispatchable re-seed of the 14-row
citation -> verse-ref resolution table from its git source (brahmagyan.l0_gochara_citation_resolution).

L0 static, chart-agnostic. Delegates all SQL to seed_gochara_citation_resolution(). ZERO LLM,
ZERO computed values. R9 asset: this writer exists so Build is measurable; DISPATCHING it belongs
to Suvarṇa in its certification window. FROZEN WriterBase contract: ctx.db_conn only, no commit.
"""
from __future__ import annotations

import time

from pipeline.orchestrator.writers import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.l0_gochara_citation_resolution import seed_gochara_citation_resolution


@register('bg_gochara_citation_resolution')
class GocharaCitationResolutionWriter(WriterBase):
    asset_id = 'bg_gochara_citation_resolution'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        counts = seed_gochara_citation_resolution(ctx.db_conn, dry_run=ctx.dry_run)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=counts['bg_gochara_citation_resolution'],
            duration_seconds=time.time() - t0,
            notes=f'bg_gochara_citation_resolution: {counts} (delete-then-insert from git source; 13 honest corpus gaps)',
        )
