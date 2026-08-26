"""
bg_compendium_index writer — top-level navigational cross-reference index.

Per CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0.md (Doc 14 of 15) and holistic design v1.1 §3.12:
  - ZERO LLM — pure deterministic aggregation over classical_text_chunks.
  - Pass A: per-text-per-chapter rows (~5,795 projected from actual corpus).
  - Pass B: per-text-per-topic_tag rows (~1,230 projected from actual topic coverage).
  - summary_text is a MECHANICAL first-3-chunks synopsis (deterministic concatenation, NOT LLM).
  - Convergent full replacement after complete source validation.

BRAHMA-BG-0-14 | L0 Brahmagyan Build — bg_compendium_index asset (Doc 14 of 15)
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
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


def _build_desired_rows(
    chunks: list[dict[str, Any]],
    valid_topics: frozenset[str],
) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    """Build the complete desired projection before any target-table write."""
    if not chunks:
        raise RuntimeError(
            "bg_compendium_index HALT: classical_text_chunks is empty — bg_texts must run first"
        )

    null_chapter_ids = [str(row["id"]) for row in chunks if row["chapter"] is None]
    if null_chapter_ids:
        sample = ", ".join(sorted(null_chapter_ids)[:5])
        raise RuntimeError(
            "bg_compendium_index HALT: source contains NULL chapter values; "
            f"sample chunk ids: {sample}"
        )

    invalid_topics = sorted({
        str(row["topic_tag"])
        for row in chunks
        if row["topic_tag"] is not None and row["topic_tag"] not in valid_topics
    })
    if invalid_topics:
        raise RuntimeError(
            "bg_compendium_index HALT: source contains unknown topic_tag values: "
            + ", ".join(invalid_topics[:10])
        )

    chapter_groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    topic_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(chunks, key=lambda item: item["id"]):
        chapter_groups[(row["text_id"], row["chapter"])].append(row)
        if row["topic_tag"] is not None:
            topic_groups[(row["text_id"], row["topic_tag"])].append(row)

    def _range(rows: list[dict[str, Any]], field: str, reducer: Any) -> int | None:
        values = [row[field] for row in rows if row[field] is not None]
        return reducer(values) if values else None

    chapter_rows: list[tuple[Any, ...]] = []
    for (text_id, chapter_num), rows in sorted(chapter_groups.items()):
        chapter_rows.append((
            text_id,
            chapter_num,
            _range(rows, "verse_start", min),
            _range(rows, "verse_end", max),
            _mechanical_synopsis([row["content_en"] or "" for row in rows]),
            f"{text_id} chapter {chapter_num}: {len(rows)} passage(s)",
            _significance_score(len(rows)),
        ))

    topic_rows: list[tuple[Any, ...]] = []
    for (text_id, topic_id), rows in sorted(topic_groups.items()):
        topic_rows.append((
            text_id,
            topic_id,
            _range(rows, "verse_start", min),
            _range(rows, "verse_end", max),
            _mechanical_synopsis([row["content_en"] or "" for row in rows]),
            f"{text_id} covers {topic_id} in {len(rows)} passage(s)",
            _significance_score(len(rows)),
        ))

    return chapter_rows, topic_rows


@register('bg_compendium_index')
class CompendiumIndexWriter(WriterBase):
    asset_id = 'bg_compendium_index'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # ── Step 0: materialize and validate desired state ───────────────────
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, text_id, chapter, topic_tag, verse_start, verse_end, content_en
                FROM classical_text_chunks
                ORDER BY id
            """)
            chunks = cur.fetchall()
            cur.execute("SELECT canonical_id FROM reference_topic_tags")
            valid_topics = frozenset(row["canonical_id"] for row in cur.fetchall())

        chapter_rows, topic_rows = _build_desired_rows(chunks, valid_topics)
        chunk_count = len(chunks)
        tagged_count = sum(row["topic_tag"] is not None for row in chunks)

        logger.info(
            "[bg_compendium_index] upstream: %d chunks total, %d tagged; "
            "desired chapters=%d topics=%d",
            chunk_count, tagged_count, len(chapter_rows), len(topic_rows),
        )

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=(
                    f"dry_run=True; projected Pass A={len(chapter_rows)} "
                    f"(per-text-per-chapter) + Pass B={len(topic_rows)} "
                    f"(per-text-per-topic) = {len(chapter_rows) + len(topic_rows)} total rows"
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

        # ── Step 2: replace the whole global projection ──────────────────────
        # Desired state was fully materialized and validated before this delete.
        with conn.cursor() as cur:
            cur.execute("DELETE FROM brahma_compendium_index")
            cur.executemany("""
                INSERT INTO brahma_compendium_index
                  (text_id, chapter_num, verse_start, verse_end, chunk_ids,
                   summary_text, significance, classical_significance_score)
                VALUES (%s, %s, %s, %s, ARRAY[]::BIGINT[], %s, %s, %s)
            """, chapter_rows)
            cur.executemany("""
                INSERT INTO brahma_compendium_index
                  (text_id, topic_id, verse_start, verse_end, chunk_ids,
                   summary_text, significance, classical_significance_score)
                VALUES (%s, %s, %s, %s, ARRAY[]::BIGINT[], %s, %s, %s)
            """, topic_rows)

        # ── Step 3: exact postflight ─────────────────────────────────────────
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM brahma_compendium_index")
            total_rows = cur.fetchone()["n"]

        duration = time.time() - t0
        total_inserted = len(chapter_rows) + len(topic_rows)
        if total_rows != total_inserted:
            raise RuntimeError(
                "bg_compendium_index postflight mismatch: "
                f"expected {total_inserted} rows, observed {total_rows}"
            )

        logger.info(
            "[bg_compendium_index] COMPLETE: total_in_table=%d, "
            "pass_a_inserted=%d, pass_b_inserted=%d, duration=%.1fs",
            total_rows, len(chapter_rows), len(topic_rows), duration,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            rows_skipped=0,
            duration_seconds=duration,
            notes=(
                f"pass_a_inserted={len(chapter_rows)}; pass_a_skipped=0; "
                f"pass_b_inserted={len(topic_rows)}; pass_b_skipped=0; "
                f"total_in_table={total_rows}; duration={duration:.1f}s"
            ),
        )
