"""
bg_compendium_index writer — top-level navigational cross-reference index.

Per CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md (Doc 14 of 15) and holistic design v1.1 §3.12:
  - ZERO LLM — pure deterministic aggregation over classical_text_chunks.
  - Pass A: per-text-per-chapter rows (~5,795 projected from actual corpus).
  - Pass B: per-text-per-topic_tag rows (~1,230 projected from actual topic coverage).
  - summary_text is a MECHANICAL first-3-chunks synopsis (deterministic concatenation, NOT LLM).
  - Idempotent via ON CONFLICT on (text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,'')).

BRAHMA-BG-0-14 | L0 Brahmagyan Build — bg_compendium_index asset (Doc 14 of 15)
"""
from __future__ import annotations

import logging
import math
import time
from typing import Any

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# Mechanical synopsis: join first N chunks' content, truncated
SYNOPSIS_CHUNKS = 3
SYNOPSIS_MAX_CHARS = 1_000
SYNOPSIS_SEPARATOR = " … "


def _mechanical_synopsis(content_list: list[str]) -> str:
    """
    Deterministic first-N-chunks synopsis. NOT LLM-generated.
    Concatenates first SYNOPSIS_CHUNKS entries, truncates to SYNOPSIS_MAX_CHARS.
    """
    parts = []
    for text in content_list[:SYNOPSIS_CHUNKS]:
        if text:
            # Take first 300 chars of each chunk to keep synopsis balanced
            parts.append(text[:300].strip())
    joined = SYNOPSIS_SEPARATOR.join(parts)
    return joined[:SYNOPSIS_MAX_CHARS]


def _significance_score(chunk_count: int, max_chunks: int = 50) -> float:
    """Deterministic significance score: min(1.0, chunk_count / max_chunks)."""
    return round(min(1.0, chunk_count / max_chunks), 3)


@register('bg_compendium_index')
class CompendiumIndexWriter(WriterBase):
    asset_id = 'bg_compendium_index'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # ── Step 0: Upstream dependency checks ───────────────────────────────
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM classical_text_chunks")
            chunk_count = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM classical_text_chunks WHERE topic_tag IS NOT NULL")
            tagged_count = cur.fetchone()["n"]

        logger.info(
            "[bg_compendium_index] upstream: %d chunks total, %d with topic_tag",
            chunk_count, tagged_count,
        )

        if chunk_count == 0:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="HALT: classical_text_chunks is empty — bg_texts must run first",
            )

        if ctx.dry_run:
            # Project expected rows without writing
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM (SELECT text_id, chapter FROM classical_text_chunks GROUP BY text_id, chapter) x"
                )
                proj_a = cur.fetchone()["n"]
                cur.execute(
                    "SELECT COUNT(*) AS n FROM (SELECT text_id, topic_tag FROM classical_text_chunks WHERE topic_tag IS NOT NULL GROUP BY text_id, topic_tag) x"
                )
                proj_b = cur.fetchone()["n"]
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=(
                    f"dry_run=True; projected Pass A={proj_a} (per-text-per-chapter) + "
                    f"Pass B={proj_b} (per-text-per-topic) = {proj_a + proj_b} total rows"
                ),
            )

        # ── Step 1: Ensure dedup unique index exists ──────────────────────────
        # Migration 191 was planned but may not be applied yet; ensure idempotently.
        with conn.cursor() as cur:
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS compendium_dedup_idx
                  ON brahma_compendium_index (text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,''))
            """)
        logger.info("[bg_compendium_index] dedup unique index ensured")

        # ── Step 2: Pass A — per-text-per-chapter rows ────────────────────────
        # Idempotency: full clear before re-seed (L0 global reference, no chart_id scope).
        with conn.cursor() as cur:
            cur.execute("DELETE FROM brahma_compendium_index")
        logger.info("[bg_compendium_index] cleared brahma_compendium_index for re-seed")

        # For each (text_id, chapter) group: verse range, chunk_ids, synopsis, score.
        logger.info("[bg_compendium_index] Pass A: loading per-text-per-chapter groups...")

        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    text_id,
                    chapter            AS chapter_num,
                    MIN(verse_start)   AS verse_start,
                    MAX(verse_end)     AS verse_end,
                    COUNT(*)           AS chunk_count
                FROM classical_text_chunks
                GROUP BY text_id, chapter
                ORDER BY text_id, chapter
            """)
            pass_a_groups = cur.fetchall()

        logger.info("[bg_compendium_index] Pass A: %d groups to process", len(pass_a_groups))

        # Fetch first-N content for synopsis: keyed by (text_id, chapter)
        # We batch-fetch the first 3 chunks per group using a window function
        with conn.cursor() as cur:
            cur.execute("""
                SELECT text_id, chapter, content_en
                FROM (
                    SELECT text_id, chapter, content_en,
                           ROW_NUMBER() OVER (PARTITION BY text_id, chapter ORDER BY id) AS rn
                    FROM classical_text_chunks
                ) ranked
                WHERE rn <= %s
                ORDER BY text_id, chapter, rn
            """, (SYNOPSIS_CHUNKS,))
            synopsis_rows = cur.fetchall()

        # Build synopsis map: (text_id, chapter) → [content_en, ...]
        synopsis_map: dict[tuple[str, int], list[str]] = {}
        for row in synopsis_rows:
            key = (row["text_id"], row["chapter"])
            synopsis_map.setdefault(key, []).append(row["content_en"] or "")

        # Insert Pass A rows
        pass_a_inserted = 0
        pass_a_skipped = 0

        for row in pass_a_groups:
            text_id = row["text_id"]
            chapter_num = row["chapter_num"]
            verse_start = row["verse_start"]
            verse_end = row["verse_end"]
            chunk_count = row["chunk_count"]

            key = (text_id, chapter_num)
            content_list = synopsis_map.get(key, [])
            synopsis = _mechanical_synopsis(content_list)
            score = _significance_score(chunk_count)
            significance = f"{text_id} chapter {chapter_num}: {chunk_count} passage(s)"

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO brahma_compendium_index
                      (text_id, chapter_num, verse_start, verse_end,
                       chunk_ids, summary_text, significance,
                       classical_significance_score)
                    VALUES (%s, %s, %s, %s, ARRAY[]::BIGINT[], %s, %s, %s)
                    ON CONFLICT (text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,''))
                    DO NOTHING
                """, (
                    text_id, chapter_num, verse_start, verse_end,
                    synopsis, significance, score,
                ))
                if cur.rowcount > 0:
                    pass_a_inserted += 1
                else:
                    pass_a_skipped += 1

            if (pass_a_inserted + pass_a_skipped) % 500 == 0:
                logger.info(
                    "[bg_compendium_index] Pass A progress: inserted=%d skipped=%d / %d",
                    pass_a_inserted, pass_a_skipped, len(pass_a_groups),
                )

        logger.info(
            "[bg_compendium_index] Pass A complete: inserted=%d, skipped=%d",
            pass_a_inserted, pass_a_skipped,
        )

        # ── Step 3: Pass B — per-text-per-topic_tag rows ─────────────────────
        if tagged_count == 0:
            logger.info(
                "[bg_compendium_index] Pass B: 0 tagged chunks — skipping "
                "(bg_text_index must run first to populate topic_tag)"
            )
            pass_b_inserted = 0
            pass_b_skipped = 0
        else:
            logger.info("[bg_compendium_index] Pass B: loading per-text-per-topic groups...")

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        text_id,
                        topic_tag          AS topic_id,
                        MIN(verse_start)   AS verse_start,
                        MAX(verse_end)     AS verse_end,
                        COUNT(*)           AS chunk_count
                    FROM classical_text_chunks
                    WHERE topic_tag IS NOT NULL
                    GROUP BY text_id, topic_tag
                    ORDER BY text_id, topic_tag
                """)
                pass_b_groups = cur.fetchall()

            logger.info("[bg_compendium_index] Pass B: %d groups to process", len(pass_b_groups))

            # Fetch first-N content for Pass B synopsis: keyed by (text_id, topic_tag)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT text_id, topic_tag, content_en
                    FROM (
                        SELECT text_id, topic_tag, content_en,
                               ROW_NUMBER() OVER (PARTITION BY text_id, topic_tag ORDER BY id) AS rn
                        FROM classical_text_chunks
                        WHERE topic_tag IS NOT NULL
                    ) ranked
                    WHERE rn <= %s
                    ORDER BY text_id, topic_tag, rn
                """, (SYNOPSIS_CHUNKS,))
                topic_synopsis_rows = cur.fetchall()

            # Build topic synopsis map: (text_id, topic_tag) → [content_en, ...]
            topic_synopsis_map: dict[tuple[str, str], list[str]] = {}
            for row in topic_synopsis_rows:
                key = (row["text_id"], row["topic_tag"])
                topic_synopsis_map.setdefault(key, []).append(row["content_en"] or "")

            # Validate topic_ids against reference_topic_tags
            with conn.cursor() as cur:
                cur.execute("SELECT canonical_id FROM reference_topic_tags")
                valid_topics: frozenset[str] = frozenset(r["canonical_id"] for r in cur.fetchall())

            pass_b_inserted = 0
            pass_b_skipped = 0
            pass_b_invalid_topic = 0

            for row in pass_b_groups:
                text_id = row["text_id"]
                topic_id = row["topic_id"]
                verse_start = row["verse_start"]
                verse_end = row["verse_end"]
                chunk_count = row["chunk_count"]

                # FK validation: topic_id must resolve in reference_topic_tags
                if topic_id not in valid_topics:
                    logger.warning(
                        "[bg_compendium_index] Pass B SKIP: topic_id '%s' not in reference_topic_tags",
                        topic_id,
                    )
                    pass_b_invalid_topic += 1
                    continue

                key = (text_id, topic_id)
                content_list = topic_synopsis_map.get(key, [])
                synopsis = _mechanical_synopsis(content_list)
                score = _significance_score(chunk_count)
                significance = f"{text_id} covers {topic_id} in {chunk_count} passage(s)"

                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO brahma_compendium_index
                          (text_id, topic_id, verse_start, verse_end,
                           chunk_ids, summary_text, significance,
                           classical_significance_score)
                        VALUES (%s, %s, %s, %s, ARRAY[]::BIGINT[], %s, %s, %s)
                        ON CONFLICT (text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,''))
                        DO NOTHING
                    """, (
                        text_id, topic_id, verse_start, verse_end,
                        synopsis, significance, score,
                    ))
                    if cur.rowcount > 0:
                        pass_b_inserted += 1
                    else:
                        pass_b_skipped += 1

                if (pass_b_inserted + pass_b_skipped) % 500 == 0:
                    logger.info(
                        "[bg_compendium_index] Pass B progress: inserted=%d skipped=%d / %d",
                        pass_b_inserted, pass_b_skipped, len(pass_b_groups),
                    )

            logger.info(
                "[bg_compendium_index] Pass B complete: inserted=%d, skipped=%d, invalid_topic=%d",
                pass_b_inserted, pass_b_skipped, pass_b_invalid_topic,
            )

        # ── Step 4: Final count ───────────────────────────────────────────────
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM brahma_compendium_index")
            total_rows = cur.fetchone()["n"]

        duration = time.time() - t0
        total_inserted = pass_a_inserted + pass_b_inserted

        logger.info(
            "[bg_compendium_index] COMPLETE: total_in_table=%d, "
            "pass_a_inserted=%d, pass_b_inserted=%d, duration=%.1fs",
            total_rows, pass_a_inserted, pass_b_inserted, duration,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            rows_skipped=pass_a_skipped + pass_b_skipped,
            duration_seconds=duration,
            notes=(
                f"pass_a_inserted={pass_a_inserted}; pass_a_skipped={pass_a_skipped}; "
                f"pass_b_inserted={pass_b_inserted}; pass_b_skipped={pass_b_skipped}; "
                f"total_in_table={total_rows}; duration={duration:.1f}s"
            ),
        )
