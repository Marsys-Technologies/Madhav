"""
bg_remedies writer — populates brahma_remedy_corpus with classical remedy corpus.
Delegates to brahmagyan.l0_remedy_corpus.seed_remedy_corpus() for INSERT logic.

Three data buckets:
  1. gen_planet_matrix()  → 108 rows  (9 planets × 8 fixed cells + 36 dana-charity)
  2. DOSHA_REMEDIES       → 102 rows  (50 doshas × 2 remedies + extras)
  3. LEGACY_REMEDIES      → 54 rows   (v1.0 hardcoded set, remedy_type normalised)

All rows scaffold_status='live'. ZERO LLM. ZERO fabrication.
Per holistic design v1.1 and brief CLAUDECODE_BRIEF_BG_REMEDIES_v1_0 (v1.1).

BRAHMA-BG-0-9 writer
"""
from __future__ import annotations

import logging
import time

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_remedy_corpus import seed_remedy_corpus, build_all_remedies

logger = logging.getLogger(__name__)


@register('bg_remedies')
class RemediesWriter(WriterBase):
    asset_id = 'bg_remedies'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()

        if ctx.dry_run:
            all_remedies = build_all_remedies()
            live = sum(1 for r in all_remedies if r.get('scaffold_status') == 'live')
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=live,
                rows_skipped=0,
                duration_seconds=time.time() - t0,
                notes=(
                    f"dry_run: would insert {len(all_remedies)} remedies "
                    f"({live} live) into brahma_remedy_corpus"
                ),
            )

        counts = seed_remedy_corpus(
            ctx.db_conn,
            build_id=ctx.build_id,
            dry_run=False,
            autocommit=False,   # caller (orchestrator) owns the transaction
        )

        inserted = counts.get('remedies_inserted', 0)
        skipped = counts.get('remedies_skipped', 0)
        live_count = counts.get('live_count', 0)
        total_built = counts.get('total_built', 0)

        logger.info(
            "[bg_remedies] inserted=%d skipped=%d live=%d total_built=%d",
            inserted, skipped, live_count, total_built,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            rows_skipped=skipped,
            duration_seconds=time.time() - t0,
            notes=(
                f"brahma_remedy_corpus: +{inserted} inserted / {skipped} skipped; "
                f"live_count={live_count} / total_built={total_built}; "
                f"buckets: 108 matrix + 102 dosha-linked + 54 legacy"
            ),
        )
