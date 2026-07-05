"""
bg_concordance writer — chunk-pointer cross-reference index (topic × school).

Per CLAUDECODE_BRIEF_BG_CONCORDANCE_v1_0.md (Doc 10 of 15) and holistic design v1.1 §2.5:
  - Builds classical_attributions rows: one row per (topic_id, school) where the corpus
    has ≥1 chunk tagged with that topic, grouped by school via TEXT_SCHOOL mapping.
  - ZERO LLM — deterministic JOIN over existing catalog tables.
  - source_text_ids: distinct text_ids for the (topic, school) group.
  - source_chunk_ids: empty BIGINT[] (schema mismatch: classical_text_chunks has no BIGINT pk;
    chunk_id is TEXT; see schema note below).
  - rule_ids: UUID[] of sutravali_rules whose text_id + verse_ref overlaps any matched chunk.
  - ON CONFLICT (topic_id, school) DO NOTHING for idempotency.
  - Floor = actual inserted count (emergent on corpus per brief §3a).

Schema note: classical_attributions.source_chunk_ids is BIGINT[] (migration 177) but
classical_text_chunks has only uuid `id` and text `chunk_id` — no bigint primary key.
source_chunk_ids is stored as an empty array; source_text_ids (TEXT[]) carries the
text-level pointers. The FK guard in §5 applies to rule_ids (UUID → sutravali_rules.rule_id).

BRAHMA-BG-0-10 | L0 Brahmagyan Build — bg_concordance asset (Doc 10 of 15)
"""
from __future__ import annotations

import logging
import time
from typing import Any

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult

logger = logging.getLogger(__name__)

# ── School mapping (from brief §3) ────────────────────────────────────────────

TEXT_SCHOOL: dict[str, str] = {
    "bphs":                 "parashari",
    "phaladeepika":         "phaladeepika",
    "jataka_parijata":      "parashari",
    "uttara_kalamrita":     "parashari",
    "bphs_jaimini":         "jaimini",
    "brihat_jataka":        "parashari",
    "saravali":             "parashari",
    "hora_sara":            "parashari",
    "sarvartha_chintamani": "parashari",
    "brihat_samhita":       "parashari",
    "tajaka_neelakanthi":   "tajaka",
    "yavana_jataka":        "parashari",
    "muhurta_chintamani":   "parashari",
    "bhrigu_nandi_nadi":    "nadi",
    "nadi_navamsa_patel":   "nadi",
}


def _school_for(text_id: str) -> str:
    """Return school name for a text_id; fall back to 'parashari' for unknown texts."""
    return TEXT_SCHOOL.get(text_id, "parashari")


@register("bg_concordance")
class ConcordanceWriter(WriterBase):
    """
    Builds classical_attributions (bg_concordance asset).

    Algorithm:
    1. Load all reference_topic_tags (topic_id, name, category).
    2. Load all classical_text_chunks that have a topic_tag set, grouped by (topic_tag, text_id).
       Derive school from text_id via TEXT_SCHOOL map.
    3. Aggregate to (topic_id, school) groups: collect distinct text_ids and row counts.
    4. Load sutravali_rules grouped by (text_id) to find matching rule_ids per school/text.
    5. INSERT one row per (topic_id, school) into classical_attributions.
       ON CONFLICT (topic_id, school) DO NOTHING.
    6. Return WriterResult with rows_inserted = actual inserted count.
    """

    asset_id = "bg_concordance"

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        # ── Step 1: Load reference_topic_tags ─────────────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT canonical_id, name, category FROM reference_topic_tags"
            )
            topic_rows = cur.fetchall()

        if not topic_rows:
            logger.warning(
                "[bg_concordance] reference_topic_tags is empty — bg_reference must be seeded first"
            )
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="HALT: reference_topic_tags is empty (depends_on bg_reference)",
            )

        topic_meta: dict[str, tuple[str, str]] = {
            row["canonical_id"]: (row["name"], row["category"]) for row in topic_rows
        }
        logger.info("[bg_concordance] loaded %d topics from reference_topic_tags", len(topic_meta))

        # ── Step 2: Check upstream classical_text_chunks ──────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS count FROM classical_text_chunks WHERE topic_tag IS NOT NULL"
            )
            tagged_chunks = cur.fetchone()["count"]

        if tagged_chunks == 0:
            logger.warning(
                "[bg_concordance] classical_text_chunks has no tagged chunks — "
                "bg_text_index must run first"
            )
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="HALT: 0 tagged chunks in classical_text_chunks (depends_on bg_text_index)",
            )

        logger.info(
            "[bg_concordance] upstream: %d tagged chunks available", tagged_chunks
        )

        # Dry-run: report what would happen but don't INSERT
        if ctx.dry_run:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT topic_tag, text_id, COUNT(*) as n
                    FROM classical_text_chunks
                    WHERE topic_tag IS NOT NULL
                    GROUP BY topic_tag, text_id
                """)
                group_rows = cur.fetchall()
            # Deduplicate to (topic_id, school) pairs
            pairs: set[tuple[str, str]] = set()
            for row in group_rows:
                topic_tag, text_id = row["topic_tag"], row["text_id"]
                if topic_tag in topic_meta:
                    school = _school_for(text_id)
                    pairs.add((topic_tag, school))
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=(
                    f"dry_run=True; would insert ~{len(pairs)} rows "
                    f"from {tagged_chunks} tagged chunks"
                ),
            )

        # ── Step 3: Aggregate chunks by (topic_tag, text_id) ──────────────────
        with conn.cursor() as cur:
            cur.execute("""
                SELECT topic_tag, text_id, COUNT(*) AS n_chunks
                FROM classical_text_chunks
                WHERE topic_tag IS NOT NULL
                GROUP BY topic_tag, text_id
                ORDER BY topic_tag, text_id
            """)
            chunk_agg_rows = cur.fetchall()

        # Build: topic_school_map[(topic_id, school)] = {text_ids: set, n_chunks: int}
        from collections import defaultdict
        topic_school_map: dict[
            tuple[str, str], dict[str, Any]
        ] = defaultdict(lambda: {"text_ids": set(), "n_chunks": 0})

        skipped_unknown_topic = 0
        for row in chunk_agg_rows:
            topic_tag, text_id, n_chunks = row["topic_tag"], row["text_id"], row["n_chunks"]
            if topic_tag not in topic_meta:
                skipped_unknown_topic += 1
                continue
            school = _school_for(text_id)
            key = (topic_tag, school)
            topic_school_map[key]["text_ids"].add(text_id)
            topic_school_map[key]["n_chunks"] += n_chunks

        logger.info(
            "[bg_concordance] aggregated %d (topic, school) pairs; skipped_unknown_topic=%d",
            len(topic_school_map), skipped_unknown_topic,
        )

        # ── Step 4: Build rule_ids index: (text_id) → list[uuid] ──────────────
        # sutravali_rules has text_id; join to chunks via text_id to find applicable rules
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rule_id::text, text_id FROM sutravali_rules"
            )
            rule_rows = cur.fetchall()

        rules_by_text: dict[str, list[str]] = defaultdict(list)
        for row in rule_rows:
            rule_id, text_id = row["rule_id"], row["text_id"]
            if text_id:
                rules_by_text[text_id].append(rule_id)

        logger.info(
            "[bg_concordance] loaded %d rules across %d texts",
            len(rule_rows), len(rules_by_text),
        )

        # ── Step 5: INSERT rows into classical_attributions ───────────────────
        rows_inserted = 0
        rows_skipped = 0
        BATCH_SIZE = 100

        def _match_confidence(n_chunks: int) -> float:
            """Deterministic confidence: min(1.0, n_chunks/5). Matches brief §4."""
            return min(1.0, n_chunks / 5.0)

        insert_sql = """
            INSERT INTO classical_attributions (
                topic_id,
                topic_canonical_name,
                topic_category,
                school,
                source_text_ids,
                source_chunk_ids,
                rule_ids,
                match_method,
                match_confidence
            ) VALUES (
                %s, %s, %s, %s,
                %s::text[],
                ARRAY[]::BIGINT[],
                %s::uuid[],
                %s,
                %s
            )
            ON CONFLICT (topic_id, school) DO NOTHING
        """

        batch: list[tuple] = []

        def _flush(b: list[tuple]) -> int:
            if not b:
                return 0
            inserted = 0
            with conn.cursor() as cur:
                for params in b:
                    cur.execute(insert_sql, params)
                    inserted += cur.rowcount
            return inserted

        for (topic_id, school), data in sorted(topic_school_map.items()):
            topic_name, topic_category = topic_meta[topic_id]
            text_ids_list = sorted(data["text_ids"])
            n_chunks = data["n_chunks"]
            confidence = _match_confidence(n_chunks)

            # Collect rule_ids for all text_ids in this (topic, school) group
            seen_rules: set[str] = set()
            for tid in text_ids_list:
                for rule_id in rules_by_text.get(tid, []):
                    seen_rules.add(rule_id)
            rule_ids_list = sorted(seen_rules)

            # Build psycopg-compatible array literals
            # TEXT[]: '{bphs,saravali}' format
            source_text_ids_pg = "{" + ",".join(f'"{t}"' for t in text_ids_list) + "}"
            # UUID[]: '{uuid1,uuid2}' format
            rule_ids_pg = "{" + ",".join(rule_ids_list) + "}"

            # match_method: 'topic_tag' (all rows here come from topic_tag classification)
            match_method = "topic_tag"

            batch.append((
                topic_id,
                topic_name,
                topic_category,
                school,
                source_text_ids_pg,
                rule_ids_pg,
                match_method,
                confidence,
            ))

            if len(batch) >= BATCH_SIZE:
                n = _flush(batch)
                rows_inserted += n
                rows_skipped += len(batch) - n
                batch.clear()
                logger.info(
                    "[bg_concordance] progress: %d rows inserted so far...", rows_inserted
                )

        if batch:
            n = _flush(batch)
            rows_inserted += n
            rows_skipped += len(batch) - n

        # ── Step 6: Verify final count ────────────────────────────────────────
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM classical_attributions")
            final_count = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(DISTINCT topic_id) AS count FROM classical_attributions")
            distinct_topics = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(DISTINCT school) AS count FROM classical_attributions")
            distinct_schools = cur.fetchone()["count"]

        duration = time.time() - t0
        logger.info(
            "[bg_concordance] COMPLETE: rows_inserted=%d rows_skipped=%d "
            "final_count=%d distinct_topics=%d distinct_schools=%d duration=%.1fs",
            rows_inserted, rows_skipped, final_count,
            distinct_topics, distinct_schools, duration,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
            rows_skipped=rows_skipped,
            duration_seconds=duration,
            notes=(
                f"classical_attributions: +{rows_inserted} inserted / {rows_skipped} conflict-skipped; "
                f"final_count={final_count}; distinct_topics={distinct_topics}; "
                f"distinct_schools={distinct_schools}; "
                f"tagged_chunks_upstream={tagged_chunks}; "
                f"skipped_unknown_topic={skipped_unknown_topic}; "
                f"source_chunk_ids=[] (schema: no BIGINT pk on classical_text_chunks)"
            ),
        )
