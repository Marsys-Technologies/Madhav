---
artifact: CLAUDECODE_BRIEF_BG_COMPENDIUM_INDEX_v1_0
canonical_id: L0_BG_COMPENDIUM_INDEX_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: |
  Racayitā (Build-Guarantor gap-author) 2026-06-08 — added §3a (≥3,000 aggregation rows,
    emergent on corpus/topic_tags, CONDITIONAL); migration 191 (dedup index)
  fix/l0-text-asset-floors 2026-06-09 — floor 3,000 → 1,755 PROVISIONAL in asset_registry
    (migration 183: 3,000 × 8,193/14,000 linear scale; prevents NULL-bar bug on unbuilt asset);
    writer MUST correct to REAL emergent count at build time (see §3a provisional note)
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_compendium_index writer (search-acceleration meta-index)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 1755  # PROVISIONAL (migration 183, 2026-06-09): 3,000 × 8,193/14,000 linear scale.
                    # Writer MUST correct to actual emergent count at build time (see §3a).
dependencies: [bg_texts, bg_text_index, bg_reference]
llm_cost: $0  # v1.1: summary_text is a mechanical first-N-chunks synopsis, NOT LLM-generated
document_number: 14 of 15
---

# bg_compendium_index — Writer Brief (search-acceleration meta-index)

> **"Where does text X cover topic Y?"** bg_compendium_index is a pre-computed cross-reference over the corpus: per-text-per-chapter rows + per-text-per-topic rows, so a query resolves to chapter/verse pointers without a whole-corpus scan. Per holistic design v1.1, `summary_text` is a MECHANICAL first-N-chunks synopsis (concatenation), NOT an LLM summary (the v1.0 Gemini-Pro summary is REMOVED). ZERO LLM.

## §0 — Asset summary

- **Asset ID:** `bg_compendium_index`. **Backing:** `brahma_compendium_index`. **Scope:** `global`. **Tier:** 4.
- **Target floor:** **1,755 PROVISIONAL** (migration 183, 2026-06-09: 3,000 × 8,193/14,000 linear scale from actual bg_texts chunk count). This is a placeholder to prevent the NULL-bar bug — NOT the emergent design target. The writer, after its build, **MUST** correct `asset_registry.target_floor` to the REAL produced count via an `UPDATE` in its own migration. Pattern: bg_texts went estimated-9,100 → actual-8,193; bg_compendium_index must do the same.
- **Source category:** deterministic aggregation over `bg_texts` chunks grouped by chapter + topic_tag.

## §3a — Floor Achievement Arithmetic (Racayitā amendment; floor ≥3,000 index rows — EMERGENT)

| Bucket | What | Count | Provable from |
|---|---|---|---|
| `deterministic_generated` | Pass A per-text-per-chapter (~300) + Pass B per-text-per-topic_tag (~2,700-4,000) aggregations over the corpus | **≥3,000 projected** | 15 texts × ~20 chapters ≈ 300; + per-text × distinct-topic_tag (≥450 tags × texts-they-appear-in) ≈ 2,700+ |
| **TOTAL** | | **≥3,000 (EMERGENT on corpus)** | ~300 + ~2,700 = ≥3,000 |

> Floor is EMERGENT: Pass B depends on `bg_text_index` having populated `topic_tag` on enough chunks across enough texts. **CONDITIONAL** if the corpus/topic_tags are incomplete (rerun after bg_text_index). `summary_text` is a mechanical first-N-chunks synopsis (ZERO LLM). Migration **191** carries the dedup unique index + `depends_on`.

> **PROVISIONAL FLOOR — correction required at build time.** `asset_registry.target_floor = 1,755` is a linear-scaled placeholder (migration 183) set to prevent the NULL-bar bug before this asset is built. The design target was 3,000 (projected at 15 texts / ~14,000 chunks); the actual corpus has 13 texts / 8,193 chunks, so 1,755 is the honest scaled floor for NOW. **The writer's migration MUST include:** `UPDATE asset_registry SET target_floor = <actual_produced_count> WHERE asset_id = 'bg_compendium_index';` — replacing 1,755 with the real emergent count from the build, exactly as bg_texts corrected 9,100 → 8,193.


## §1 — Schema reference (migration 176, verified)

```
brahma_compendium_index (
  index_id BIGSERIAL PRIMARY KEY,
  text_id TEXT NOT NULL,                  -- → classical_texts / bg_ontology text class
  chapter_num INT, chapter_title_en TEXT, chapter_title_sa TEXT,
  topic_id TEXT,                          -- → reference_topic_tags (for per-topic rows)
  verse_start INT, verse_end INT,
  chunk_ids BIGINT[] DEFAULT '{}',        -- → classical_text_chunks
  summary_text TEXT,                      -- MECHANICAL first-N-chunks synopsis (NOT LLM)
  significance TEXT,
  classical_significance_score NUMERIC(4,3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

> Design §3.9 schema mentioned FK `text_id REFERENCES classical_texts(text_id)` and `topic_id REFERENCES reference_topic_tags(canonical_id)`, but migration 176 created the columns WITHOUT the FK constraints (verify with `\d brahma_compendium_index`). The writer enforces resolution in code regardless (§5).

## §2 — Source references

No new source. Aggregates `bg_texts` chunks (cited) by chapter + topic_tag (from bg_text_index).

## §3 — Embedded content

None. Pure aggregation. The only authored data is the chapter-title map per text (English/Sanskrit chapter names), which the executor pulls from each text's structure (or leaves null where unknown — not a blocker).

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_compendium_index.py` (`@register('bg_compendium_index')`):

**Pass A — per-text-per-chapter (~300 rows):** `SELECT text_id, chapter, min(verse_start), max(verse_end), array_agg(id), count(*) FROM classical_text_chunks GROUP BY text_id, chapter`. For each group: `verse_start/end`, `chunk_ids`, `summary_text` = mechanical concat of the first N (e.g. 3) chunks' `summary`/`content_en` truncated, `classical_significance_score` = deterministic (e.g. min(1.0, chunk_count/50)).

**Pass B — per-text-per-topic (~3,000-4,000 rows):** `SELECT text_id, topic_tag, array_agg(id), count(*) FROM classical_text_chunks WHERE topic_tag IS NOT NULL GROUP BY text_id, topic_tag`. For each group: `topic_id` = topic_tag, `chunk_ids`, `summary_text` = mechanical first-N-chunks synopsis, `significance` = e.g. f"{text_id} covers {topic} in {n} passages".

Deterministic `index_id` is the BIGSERIAL — for idempotency, use `ON CONFLICT` on a deterministic unique key instead: add a unique index on `(text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,''))` in this brief's migration, and `ON CONFLICT DO NOTHING`. (Re-run produces identical groups → identical rows.)

```sql
-- this brief's migration (next free number, e.g. 182+):
CREATE UNIQUE INDEX IF NOT EXISTS compendium_dedup_idx
  ON brahma_compendium_index (text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,''));
```

> **NO LLM summary.** `summary_text` is `' … '.join(first_3_chunk_texts)[:1000]` — a deterministic synopsis. v1.0's Gemini-Pro chapter summaries are REMOVED by v1.1. Do not call an LLM.

## §5 — FK validation

- `text_id` resolves in `classical_texts` / bg_ontology text class → **depends_on bg_texts**.
- `topic_id` (Pass B) resolves in `reference_topic_tags` → **depends_on bg_reference** + bg_text_index (topic_tag must be populated first).
- `chunk_ids[]` resolve in `classical_text_chunks`.
- **depends_on:** `UPDATE asset_registry SET depends_on = ARRAY['bg_texts','bg_text_index','reference_topic_tags']::text[] WHERE asset_id='bg_compendium_index';` (migration 179 set `['bg_texts','reference_topic_tags']` — ADD `bg_text_index` since topic_tag must be populated first; verify and reconcile).

## §6 — Unit tests

`test_bg_compendium_index.py`: (1) ≥1,755 rows (provisional floor; update test to actual emergent count post-build); (2) per-text-chapter rows present for all ingested texts; (3) every `chunk_ids` element resolves; (4) every Pass-B `topic_id` resolves in `reference_topic_tags`; (5) `summary_text` present + non-LLM (deterministic concat — verify it equals the recomputed concat for a sample row); (6) idempotent re-run inserts 0.

## §7 — Vimarśaka check

APPROVE iff: ≥1,755 rows (provisional floor — writer's migration MUST `UPDATE asset_registry SET target_floor = <actual_count> WHERE asset_id = 'bg_compendium_index'`); pointers resolve; topic_ids valid; summaries deterministic; idempotent. If < actual emergent count because topic_tag coverage is low (bg_text_index incomplete → fewer Pass-B groups), CONDITIONAL with "rerun after bg_text_index reaches floor". Otherwise REJECT.

## §8 — Hard stops + scope discipline

- Tempted to LLM-summarize chapters for richer `summary_text` → STOP. v1.1 mandates mechanical synopsis.
- Pass B yields too few rows → bg_text_index hasn't populated topic_tags; confirm Tier-3 ran first (depends_on). Do not pad.
- Out of scope: stance/concordance (bg_concordance), per-chart anything.

---

*End of bg_compendium_index brief (Document 14 of 15).*
