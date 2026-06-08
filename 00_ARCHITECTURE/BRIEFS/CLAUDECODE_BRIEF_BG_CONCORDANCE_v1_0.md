---
artifact: CLAUDECODE_BRIEF_BG_CONCORDANCE_v1_0
canonical_id: L0_BG_CONCORDANCE_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_concordance writer (chunk-pointer index per topic × school)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 800  # classical_attributions rows (topic × school chunk-pointers)
dependencies: [bg_texts, bg_text_index, bg_reference, bg_rules]
llm_cost: $0  # v1.1: deterministic topic × school chunk matching; NO stance synthesis (that's L1 query-time)
document_number: 10 of 15
---

# bg_concordance — Writer Brief (cross-school chunk-pointer index)

> **What does each school say about each topic — pointed, not synthesized.** Per holistic design v1.1 §2.5, bg_concordance does NOT generate stance prose (the v1.0 design's LLM stance-generation is REMOVED). It stores, per `(topic, school)`, WHICH chunks + rules contain that school's discussion. Stance SYNTHESIS happens at L1+ query-time from these pointers. ZERO LLM.

## §0 — Asset summary

- **Asset ID:** `bg_concordance`. **Backing:** `classical_attributions` (reshaped by migration 177 to the chunk-pointer model). **Scope:** `global`. **Tier:** 4.
- **Target floor:** **≥800 rows** (design §3.8: ~200 topics × 4-6 schools = 800-1,200; cockpit "topic count" ≈ 200).
- **Source category:** deterministic topic × school chunk matching over the corpus.

## §1 — Schema reference (migration 177, verified — NOT the migration-158 MSR schema)

```
classical_attributions (
  attribution_id        BIGSERIAL PRIMARY KEY,
  topic_id              TEXT NOT NULL,            -- e.g. 'saturn_7th_marriage' (a reference_topic_tags id)
  topic_canonical_name  TEXT NOT NULL,
  topic_category        TEXT NOT NULL,            -- 'house_placement'|'yoga'|'dosha'|'remedy'|'dasha'|'transit'
  school                TEXT NOT NULL,            -- 'parashari'|'jaimini'|'kp'|'tajaka'|'lal-kitab'|'phaladeepika'
  source_text_ids       TEXT[] DEFAULT '{}',
  source_chunk_ids      BIGINT[] NOT NULL DEFAULT '{}',
  rule_ids              UUID[] DEFAULT '{}',
  match_method          TEXT NOT NULL,            -- 'keyword'|'topic_tag'|'manual'|'cross_ref'
  match_confidence      NUMERIC(4,3),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_topic_school UNIQUE (topic_id, school)
)
```

> Migration 177 DROPPED the old MSR-signal `classical_attributions` (158) and rebuilt it as this chunk-pointer index. Confirm with `\d classical_attributions` that `source_chunk_ids BIGINT[]` + `uq_topic_school` exist (the v177 shape), NOT `msr_signal_id` (the v158 shape).

## §2 — Source references

No new classical source. Concordance POINTS at `bg_texts` chunks (already cited) + `bg_rules` rows (already cited), grouped by topic × school. The school of a chunk is `classical_text_chunks.tradition_school` (or derived from `text_id` → school via the bg_ontology text/school mapping).

## §3 — Embedded content — the topic set

The ~200 canonical topics ARE `reference_topic_tags` (bg_reference §3.6) — reuse them; do not author a separate topic list. Each topic's `topic_category` is the `reference_topic_tags.category`. The school-of-text mapping:

```python
TEXT_SCHOOL = {  # text_id → school (matches bg_ontology school class)
  "bphs":"parashari","phaladeepika":"phaladeepika","jataka_parijata":"parashari",
  "uttara_kalamrita":"parashari","bphs_jaimini":"jaimini","brihat_jataka":"parashari",
  "saravali":"parashari","hora_sara":"parashari","sarvartha_chintamani":"parashari",
  "brihat_samhita":"parashari","tajaka_neelakanthi":"tajaka","yavana_jataka":"parashari",
  "bhrigu_samhita":"nadi","muhurta_chintamani":"parashari","lal_kitab":"lal_kitab",
}
```

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_concordance.py` (`@register('bg_concordance')`):

For each topic in `reference_topic_tags` (cap at the top ~200 most-covered for the cockpit "topic count", but author ALL that have matches):
1. Find chunks whose `topic_tag = topic_id` (from bg_text_index) OR whose content keyword-matches the topic (the bg_text_index classifier rule for that topic).
2. Group the matched chunks by `school` (via `TEXT_SCHOOL[text_id]`).
3. For each `(topic_id, school)` with ≥1 matched chunk, insert one row: `source_chunk_ids` = the chunk ids, `source_text_ids` = distinct texts, `rule_ids` = `sutravali_rules` whose `verse_ref`/chunk falls in the set, `match_method` = 'topic_tag' (or 'keyword'), `match_confidence` = a deterministic score (e.g. min(1.0, n_chunks/5)).
4. `ON CONFLICT (topic_id, school) DO NOTHING` (or DO UPDATE to merge chunk arrays — choose DO NOTHING for idempotent determinism; a clear-rebuild re-derives identically).

> **NO stance_text.** The row says "school X discusses topic Y in these chunks/rules". It does NOT say what the school's position IS — that synthesis is L1 query-time (design v1.1 §2.5). Do not add a stance column; do not call an LLM.

## §5 — FK validation

- `source_chunk_ids[]` MUST resolve in `classical_text_chunks` → **depends_on bg_texts** (+ bg_text_index for topic_tag).
- `rule_ids[]` MUST resolve in `sutravali_rules` → **depends_on bg_rules**.
- `topic_id` SHOULD resolve in `reference_topic_tags` → **depends_on bg_reference**.
- **depends_on:** `UPDATE asset_registry SET depends_on = ARRAY['bg_texts','bg_text_index','bg_reference','bg_rules']::text[] WHERE asset_id='bg_concordance';` (migration 179 didn't set this — add it).

## §6 — Unit tests

`test_bg_concordance.py`: (1) ≥800 rows; (2) every row has ≥1 `source_chunk_ids` element that resolves in `classical_text_chunks`; (3) every `rule_ids` element resolves in `sutravali_rules`; (4) `uq_topic_school` holds (no duplicate topic×school); (5) NO stance/prose column exists (schema check); (6) idempotent re-run inserts 0; (7) distinct topic count ≈ ≥150.

## §7 — Vimarśaka check

APPROVE iff: ≥800 rows; all chunk/rule pointers resolve; unique (topic,school); no stance synthesis present; idempotent. **If <800 because the corpus is incomplete** (manual PDFs missing → fewer chunks → fewer topic×school pairs), CONDITIONAL with "rerun after full corpus". Otherwise REJECT and report which topics had no school coverage.

## §8 — Hard stops + scope discipline

- Tempted to add stance prose or call an LLM to summarize positions → STOP. v1.1 explicitly moved synthesis to L1 query-time. Pointers only.
- A chunk/rule pointer doesn't resolve → skip + log; do not insert a dangling pointer.
- Do NOT use the migration-158 MSR `classical_attributions` shape; use the v177 chunk-pointer shape.
- Out of scope: stance generation, agreement scoring prose, per-chart concordance.

---

*End of bg_concordance brief (Document 10 of 15).*
