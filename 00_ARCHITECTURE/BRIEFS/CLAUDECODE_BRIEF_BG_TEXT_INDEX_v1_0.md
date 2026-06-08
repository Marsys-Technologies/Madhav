---
artifact: CLAUDECODE_BRIEF_BG_TEXT_INDEX_v1_0
canonical_id: L0_BG_TEXT_INDEX_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: Racayitā (Build-Guarantor gap-author) 2026-06-08 — added §3a (≥400 distinct tags, emergent on corpus, CONDITIONAL on manual PDFs); migration 187
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_text_index writer (deterministic topic_tag classifier)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 400  # DISTINCT topic_tag values present on embedded chunks
dependencies: [bg_texts, bg_reference]  # needs chunks + the reference_topic_tags vocabulary
llm_cost: $0  # pure-Python keyword-rule classifier (v1.1 removed the LLM classifier)
document_number: 7 of 15
---

# bg_text_index — Writer Brief (deterministic topic_tag classifier / index-health metric)

> **A measurement asset, not a data store.** Per holistic design v1.1 §2.2, `bg_text_index` no longer counts chunks. It is the retrieval-index health metric: **the number of DISTINCT `topic_tag` values present on embedded chunks.** This writer sets `classical_text_chunks.topic_tag` using a deterministic keyword-rule classifier over the `reference_topic_tags` vocabulary. ZERO LLM (v1.1 explicitly removed the Gemini classifier the v1.0 design used). All retrieval tools query `bg_texts`; nothing queries `bg_text_index` directly.

## §0 — Asset summary

- **Asset ID:** `bg_text_index`. **Backing:** `classical_text_chunks` (the `topic_tag` column, filtered). **Scope:** `global`. **Tier:** 3.
- **count_sql** (already set, migration 179): `SELECT count(DISTINCT topic_tag) FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL`.
- **Target floor:** **≥400 distinct topic tags** present on chunks (design §3.5 floor 400-600).
- **Source category:** deterministic Python keyword-rule classifier.

## §3a — Floor Achievement Arithmetic (Racayitā amendment; floor ≥400 distinct topic_tags — EMERGENT)

| Bucket | What | Count | Provable from |
|---|---|---|---|
| `deterministic_generated` | distinct `topic_tag` values assigned by the §3 keyword-rule classifier over the embedded chunks, from the `reference_topic_tags` vocabulary (≥450, Doc 4 §3.6) | **≥400 projected** | classifier rules (planet×house 108, lordship 144, domain/dasha/yoga families) ∩ corpus coverage |
| **TOTAL** | | **≥400 (EMERGENT on corpus)** | bounded above by the ≥450 vocabulary; reached as corpus coverage grows |

> Floor is EMERGENT: it holds only if the corpus covers ≥400 of the ≥450 topic tags. **CONDITIONAL** if the 3 manual PDFs are absent (fewer chunks → fewer matchable tags) — rerun after full corpus. Every assigned tag MUST resolve in `reference_topic_tags` (no orphan tags). Migration **187** carries `depends_on=['bg_texts','bg_reference']`.


## §1 — Schema reference

No new table. This writer UPDATEs `classical_text_chunks.topic_tag` (TEXT, added by migration 177). The tag values come from `reference_topic_tags.canonical_id` (≥450 authored in bg_reference Doc 4 §3.6). A chunk may be assigned exactly one PRIMARY `topic_tag` (the column is scalar); multi-topic membership is captured by bg_compendium_index (Doc 14), not here.

## §2 — Source references

The classifier is authored logic, not a classical text. Its vocabulary (`reference_topic_tags`) is the canonical topic set from bg_reference. The mapping rules (keyword → tag) are deterministic and authored here.

## §3 — Embedded content — the classifier rule table

Author `platform/python-sidecar/brahmagyan/l0_text_index.py` classifier (the file exists; add the classifier function). The classifier is a deterministic ordered rule list: each rule is `(compiled_regex, topic_tag)`; the FIRST matching rule wins; chunks matching no rule get `topic_tag=NULL` (and are excluded from the metric).

```python
# Rule families (deterministic; keyword/phrase → reference_topic_tags.canonical_id).
# Author ≥1 rule per topic_tag that the corpus can realistically match, so ≥400 DISTINCT
# tags actually appear. Rules are ordered most-specific first.
CLASSIFIER_RULES = [
  # planet-in-house family (108 tags): 'saturn ... 7th house' → 'saturn_in_7th'
  (re.compile(r'\bsaturn\b.{0,40}\b(7th|seventh)\b.{0,20}\bhouse\b', re.I), 'saturn_in_7th'),
  (re.compile(r'\bshani\b.{0,40}\bsaptama\b', re.I), 'saturn_in_7th'),
  # ... generate the planet×house rules programmatically from PLANETS × HOUSES with
  #     name + synonym alternations (English ordinal + Sanskrit bhava names).
  # lordship family (144 tags): 'lord of the 7th in the 10th' → 'lord_7th_in_10th'
  (re.compile(r'\blord\b.{0,15}\b(7th|seventh)\b.{0,30}\b(10th|tenth)\b', re.I), 'lord_7th_in_10th'),
  # domain family: 'marriage' near timing words → 'marriage_timing', etc.
  (re.compile(r'\b(marriage|wife|husband|spouse|kalatra)\b', re.I), 'marriage_general'),
  (re.compile(r'\b(career|profession|karma|livelihood)\b', re.I), 'career_general'),
  # dasha/transit family: 'vimshottari ... saturn' → 'vimshottari_saturn_dasha'; 'sade sati' → 'sade_sati'
  (re.compile(r'\bsade[\s-]?sati\b', re.I), 'sade_sati'),
  # yoga/dosha family: 'gajakesari' → 'gajakesari_yoga'; 'manglik|kuja dosha' → 'manglik_dosha'
  (re.compile(r'\bgajakesari\b', re.I), 'gajakesari_yoga'),
  # ... continue so that ≥400 of the reference_topic_tags canonical_ids have at least one rule.
]
```

> **Generation, not fabrication:** the bulk of rules (planet×house = 108, lordship = 144) are generated by code from `PLANETS × HOUSES` with name/synonym alternations — the executor writes a small generator that emits the `(regex, tag)` tuples for every `reference_topic_tags` entry of those families. The domain/dasha/yoga/dosha rules are authored from the topic vocabulary. The tag set is exactly `reference_topic_tags.canonical_id` — the classifier NEVER invents a tag (every assigned tag must resolve in `reference_topic_tags`, enforced in §5).

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_text_index.py` (`@register('bg_text_index')`):

1. Load `reference_topic_tags.canonical_id` into a set `VALID_TAGS` (the allowed vocabulary).
2. Load all chunks with `embedding IS NOT NULL AND topic_tag IS NULL` (only classify embedded, unclassified chunks; idempotent).
3. For each chunk, run `CLASSIFIER_RULES` in order; first match → `tag`. Assert `tag in VALID_TAGS` (else skip + log). `UPDATE classical_text_chunks SET topic_tag=%s WHERE id=%s`.
4. Batch-commit. Report `rows_inserted` = chunks newly tagged; the asset's count_sql (distinct tags) is the cockpit metric.

> **Idempotency:** only NULL-topic_tag chunks are processed; re-runs are no-ops. Deterministic: same chunk text + same rule list → same tag. A clear-and-rebuild re-derives identical tags.

## §5 — FK validation

- Every assigned `topic_tag` MUST exist in `reference_topic_tags.canonical_id` (the writer asserts membership before UPDATE; a tag not in the vocabulary is a classifier bug, not a silent insert).
- **depends_on:** `UPDATE asset_registry SET depends_on = ARRAY['bg_texts','bg_reference']::text[] WHERE asset_id='bg_text_index';` (needs chunks + the topic-tag vocabulary). Note: migration 179 did NOT set this — this brief's migration adds it.

## §6 — Unit tests

`test_bg_text_index.py`: (1) after run, `count(DISTINCT topic_tag) ≥ 400`; (2) every non-null `topic_tag` resolves in `reference_topic_tags`; (3) a known BPHS Saturn-7th chunk gets `topic_tag='saturn_in_7th'` (deterministic spot-check); (4) re-run tags 0 additional chunks (idempotent); (5) chunks with NULL embedding are never tagged.

## §7 — Vimarśaka check

APPROVE iff: distinct topic_tags ≥ 400; every assigned tag ∈ `reference_topic_tags`; idempotent; deterministic spot-check passes. **If < 400 because the corpus is incomplete** (manual PDFs not yet uploaded → fewer chunks → fewer matchable tags), Vimarśaka returns CONDITIONAL with the note "rerun after bg_texts reaches full corpus" — not a writer failure.

## §8 — Hard stops + scope discipline

- A rule assigns a tag absent from `reference_topic_tags` → STOP; the vocabulary (bg_reference §3.6) and the classifier must agree. Reconcile; do not insert orphan tags.
- Do NOT re-introduce an LLM classifier (v1.1 removed it; this is pure Python). The design v1.0 body mentions Gemini Flash — that is SUPERSEDED by v1.1; follow v1.1.
- Do NOT alter chunk content or embeddings (that's bg_texts). This writer only sets `topic_tag`.
- < 400 distinct tags after the FULL corpus is ingested and the generator emitted all family rules → investigate the rules (too-narrow regexes), do NOT loosen rules to over-match. Report to native if the corpus genuinely can't disambiguate 400 topics.

---

*End of bg_text_index brief (Document 7 of 15).*
