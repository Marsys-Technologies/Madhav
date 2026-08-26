"""
bg_remedies writer — populates brahma_remedy_corpus with classical remedy corpus.
Delegates to brahmagyan.l0_remedy_corpus.seed_remedy_corpus() for INSERT logic.

Writer composition:
  1. deterministic base → 283 rows currently
     (108 planet matrix + 54 dosha + 55 legacy + 66 expansion)
  2. deterministic classical_text_chunks sweep → source-snapshot-derived count;
     rows are classified live/review by the extraction gate
  3. accepted tantric.yaml rows → canonical live rows via the careful-inclusion gate

ZERO LLM. ZERO fabrication.
Per holistic design v1.1 and brief CLAUDECODE_BRIEF_BG_REMEDIES_v1_0 (v1.1).

BRAHMA-BG-0-9 writer
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan import l0_remedy_loader
from brahmagyan.l0_remedy_corpus import seed_remedy_corpus, build_all_remedies

logger = logging.getLogger(__name__)


@register('bg_remedies')
class RemediesWriter(WriterBase):
    asset_id = 'bg_remedies'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        remedy_corpus_dir = Path(__file__).resolve().parents[3] / 'brahmagyan' / 'remedy_corpus'

        if ctx.dry_run:
            all_remedies = build_all_remedies()
            live = sum(1 for r in all_remedies if r.get('scaffold_status') == 'live')
            tantric_counts = l0_remedy_loader.load_remedies(
                yaml_dir=remedy_corpus_dir,
                dry_run=True,
                file_glob='tantric.yaml',
            )
            tantric_inserted = tantric_counts['inserted']
            tantric_queued = tantric_counts['review_queued']
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=live + tantric_inserted,
                rows_skipped=0,
                duration_seconds=time.time() - t0,
                notes=(
                    f"dry_run: would insert {len(all_remedies)} remedies "
                    f"({live} live) into brahma_remedy_corpus; "
                    f"tantric: {tantric_inserted} inserted / {tantric_queued} review_queued"
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
        tantric_counts = l0_remedy_loader.load_remedies(
            yaml_dir=remedy_corpus_dir,
            conn=ctx.db_conn,
            dry_run=False,
            file_glob='tantric.yaml',
            manage_transaction=False,
        )
        tantric_inserted = tantric_counts['inserted']
        tantric_queued = tantric_counts['review_queued']

        with ctx.db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  (SELECT count(*) FROM brahma_remedy_corpus) AS corpus_count,
                  (SELECT count(*) FROM remedy_review_queue
                   WHERE category = 'tantric') AS review_count
                """
            )
            observed = cur.fetchone()
        corpus_count = (
            int(observed['corpus_count']) if isinstance(observed, dict)
            else int(observed[0])
        )
        review_count = (
            int(observed['review_count']) if isinstance(observed, dict)
            else int(observed[1])
        )
        expected_corpus = total_built + tantric_inserted
        if (corpus_count, review_count) != (expected_corpus, tantric_queued):
            raise RuntimeError(
                "bg_remedies postflight mismatch: "
                f"expected corpus/review=({expected_corpus},{tantric_queued}), "
                f"found ({corpus_count},{review_count})"
            )

        logger.info(
            "[bg_remedies] inserted=%d skipped=%d live=%d total_built=%d "
            "tantric_inserted=%d tantric_queued=%d",
            inserted, skipped, live_count, total_built, tantric_inserted, tantric_queued,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted + tantric_inserted,
            rows_skipped=skipped,
            duration_seconds=time.time() - t0,
            notes=(
                f"brahma_remedy_corpus: +{inserted} inserted / {skipped} skipped; "
                f"live_count={live_count} / total_built={total_built}; "
                f"buckets: deterministic base + source-derived sweep={total_built}; "
                f"tantric: {tantric_inserted} inserted / {tantric_queued} review_queued"
            ),
        )
