---
artifact: CLAUDECODE_BRIEF_BG_TEXTS_v1_0
canonical_id: L0_BG_TEXTS_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: Racayitā (Build-Guarantor gap-author) 2026-06-08 — added §3a (≥14,000 chunks emergent; 3 manual PDFs are the hard operator prerequisite; CONDITIONAL-APPROVE)
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_texts writer (classical text corpus ingestion)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 14000  # classical_text_chunks rows across 15 texts
dependencies: []  # Tier 2 — needs source PDFs in GCS, not other L0 assets
llm_cost: "embeddings only (Vertex AI text-multilingual-embedding-002 / text-embedding-004, 768-dim — deterministic transform)"
document_number: 6 of 15
---

# bg_texts — Writer Brief (classical text corpus ingestion + embeddings)

> **The corpus.** `bg_texts` is the chunked, verse-addressable, embedded body of the classical literature. 5 texts (~8,432 chunks) are already ingested; this brief ingests the remaining 10 to reach ≥14,000 chunks across 15 texts. The ONLY non-deterministic call permitted anywhere in L0 is the embedding transform here (Vertex AI, deterministic at a fixed model version) — holistic design v1.1 locked decision. No LLM generation, no LLM classification (that moved to the deterministic classifier in bg_text_index, Doc 7).

## §0 — Asset summary

- **Asset ID:** `bg_texts`. **Backing:** `classical_text_chunks` (NOT `classical_chunks` — see §1). **Scope:** `global`. **Tier:** 2.
- **Target floor:** **≥14,000 chunks** across 15 texts (design §3.3).
- **Source category:** source PDFs in GCS + deterministic embedding transform.
- **Dependency:** source PDFs present in the GCS bucket. Texts 11 (Tajaka Neelakanthi), 12 (Yavana Jataka), 13 (Bhrigu Samhita) require MANUAL native upload (design §3.3 table).

## §3a — Floor Achievement Arithmetic (Racayitā amendment; floor ≥14,000 chunks — EMERGENT, operator-gated)

| Bucket | What | Count | Provable from |
|---|---|---|---|
| `structured_extraction` | chunks from the 15 source PDFs (existing 5 ≈ 8,432 + 10 new ≈ 8,200) ingested + embedded (Vertex AI, the one permitted deterministic transform) | **≥14,000 projected** | per-text expected-chunk sums (§2 table): Saravali ~1,800, Brihat Samhita ~2,000, etc. |
| **TOTAL** | | **≥14,000 (EMERGENT, needs 3 manual PDFs)** | 8,432 + ~8,200 ≈ 16,600 potential − ~1,300 behind manual PDFs |

> **HARD OPERATOR PREREQUISITE:** 3 texts (Tajaka Neelakanthi, Yavana Jataka, Bhrigu Samhita ≈ 1,300 chunks) require MANUAL native upload to GCS. The writer logs `AWAITING_MANUAL_UPLOAD` and CONDITIONAL-APPROVEs the available corpus. Full floor reached only after the uploads + re-ingest. No migration (bg_texts authors no depends_on UPDATE).


## §1 — Schema reference

Two chunk tables exist in the DB — **use `classical_text_chunks`** (the one `l0_texts.py` + `l0_text_index.py` operate on, the one migration 177 added `topic_tag` to, the one the design's count_sql targets). `classical_chunks`/`classical_texts` (migration 158, `text_key`/`VECTOR(768)`) is the older M8 schema; do NOT switch the writer to it. Confirm at runtime:

```bash
psql_prod -c "\d classical_text_chunks"   # the bg_texts backing table
```

`classical_text_chunks` carries (from l0_texts.py INSERTs + migration 081/177 ALTERs): `text_id, chapter, verse_start, verse_end, verse_ref, content_sa, content_en, summary, topics, source_citation, translator, tradition_school, embedding vector(768), content_sha256, topic_tag`. Verify exact columns with `\d`.

> **Existing data is KEPT.** `l0_texts.py` already defines `TEXTS` (5 texts: bphs, phaladeepika, jataka_parijata, uttara_kalamrita, bphs_jaimini) + seed chunks and a `seed_texts(conn, build_id, dry_run)` writer. This brief EXTENDS `TEXTS` with 10 more and runs delta-ingest. The 5 existing texts' chunks are not re-ingested (idempotent on `content_sha256` / `(text_id, chapter, verse_*)`).

## §2 — Source references (the 15 texts)

Per design §3.3 / `L0FR_SOURCE_DATA_v1_0.md`:

| # | text_id | Tier | Manual upload? | Expected chunks |
|---|---|---|---|---|
| 1-5 | bphs, phaladeepika, jataka_parijata, uttara_kalamrita, bphs_jaimini | 1 | NO | ~8,432 (have) |
| 6 | brihat_jataka | 1 | NO | ~700 |
| 7 | saravali | 1 | NO | ~1,800 |
| 8 | hora_sara | 1 | NO | ~400 |
| 9 | sarvartha_chintamani | 2 | NO | ~600 |
| 10 | brihat_samhita | 2 | NO | ~2,000 |
| 11 | tajaka_neelakanthi | 2 | **MANUAL** | ~400 |
| 12 | yavana_jataka | 3 | **MANUAL** | ~600 |
| 13 | bhrigu_samhita | 3 | **MANUAL** | ~300 |
| 14 | muhurta_chintamani | 3 | NO | ~700 |
| 15 | lal_kitab | 3 | NO | ~700 |

**Total target ≥14,000 chunks** (the §3.4 floor in the holistic design is 14,500; the master plan floor is ≥14,000).

> **text_id discipline:** these 15 `text_id` values MUST match the `entity_class='text'` canonical_ids authored in bg_ontology Doc 5 §3.6. (Note: the existing l0_texts.py uses `bphs_jaimini`; reconcile — either keep `bphs_jaimini` and add that synonym to the ontology `jaimini_sutram` entry, or align ids. Document the choice.)

## §3 — Embedded content

None to embed — the content lives in the source PDFs. This brief embeds only the 15-text **registry rows** (title/author/tier/source) to extend `TEXTS`, and the per-text ingestion config (chunk size, chapter-delimiter regex). The PDF→text→chunk pipeline already exists in `l0_texts.py` per Stream C; this brief adds entries to its config, not new pipeline code.

```python
# Extend TEXTS in l0_texts.py with the 10 new registry entries (one shown):
TEXTS += [
  {"text_id":"saravali","title_en":"Saravali","title_sa":"Sārāvalī","author":"Kalyana Varma",
   "tier":1,"tradition":"parashari","school":"parashari","language_original":"sanskrit",
   "gcs_path":"gs://<bucket>/classical_texts/saravali.pdf","expected_chunks":1800,
   "manual_upload":False,"source_citation":"Saravali (Kalyana Varma), classical tradition, public domain"},
  # ... brihat_jataka, hora_sara, sarvartha_chintamani, brihat_samhita, tajaka_neelakanthi,
  #     yavana_jataka, bhrigu_samhita, muhurta_chintamani, lal_kitab — full registry rows.
]
```

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_texts.py` (`@register('bg_texts')`) delegating to an extended `l0_texts.seed_texts(...)` + a delta-ingest routine. Pipeline per new text:

1. **Locate the PDF** in GCS (`gcs_path`). If `manual_upload=True` and the object is absent → the writer logs `AWAITING_MANUAL_UPLOAD: <text_id>` and SKIPS that text (does not fail the asset). It records the skip so Vimarśaka can distinguish "below floor because PDF missing" from "below floor because pipeline broke".
2. **Extract + chunk** using the existing l0_texts chunker (chapter/verse-delimiter aware). Each chunk → `{text_id, chapter, verse_start, verse_end, verse_ref, content_en, content_sa?, source_citation, content_sha256}`.
3. **Embed** each chunk's `content_en` via Vertex AI (`text-multilingual-embedding-002` or the model already used by l0_text_index — confirm and reuse for consistency), 768-dim → `embedding` column. Batch for cost. This is the only permitted non-deterministic call; it is deterministic at a fixed model version.
4. **Insert** `ON CONFLICT (content_sha256) DO NOTHING` (or `(text_id, chapter, verse_start, verse_end)` — match the existing unique constraint) for idempotency.
5. Update `classical_texts.chunk_count` per text.
6. `topic_tag` is left NULL here — it is set by **bg_text_index (Doc 7)** deterministically. Do NOT classify topics in this writer (holistic design v1.1 moved classification out of ingest to a pure-Python classifier).

> **Idempotency + determinism:** re-running ingest with the same PDFs + same embedding model version produces identical chunks (same `content_sha256`) and identical embeddings → 0 new rows. The `bg_ephemeris`-style count-first guard applies: if `classical_text_chunks` already ≥ floor and all 15 texts present, the writer is a near no-op (verifies coverage, re-embeds nothing).

## §5 — FK validation

- `classical_text_chunks.text_id` should correspond to a `classical_texts` registry row (insert the registry row first per text).
- No ontology FK (chunks are not entities). But `text_id` values must be in the bg_ontology `text` class set (§2 discipline) so downstream `bg_compendium_index.text_id` resolves.
- **depends_on:** none on other L0 assets (Tier 2 by PDF availability, not by L0 dependency). Leave `asset_registry.depends_on` empty for bg_texts unless native wants it after bg_reference (not required).

## §6 — Unit tests

`test_bg_texts.py`: (1) ≥14,000 chunks total OR (if manual PDFs absent) ≥ the floor of the available texts with a logged `AWAITING_MANUAL_UPLOAD` list; (2) every chunk has non-null `source_citation` + `verse_ref`; (3) every chunk has a 768-dim `embedding` (no null embeddings on lit texts); (4) all 15 `text_id`s present in `classical_texts` registry; (5) re-ingest inserts 0 (idempotent); (6) FORENSIC spot-check: BPHS Ch.7 (bhava) chunks retrievable.

## §7 — Vimarśaka check

APPROVE iff: ≥14,000 chunks (OR all NON-manual texts fully ingested + manual gaps explicitly logged for native upload); zero null `source_citation`; zero null `embedding` on ingested texts; 15 registry rows. **If below 14,000 solely due to absent manual PDFs (texts 11/12/13), Vimarśaka returns CONDITIONAL-APPROVE with the upload list** — this is an operator action, not a writer failure. If below floor for any OTHER reason, REJECT.

## §8 — Hard stops + scope discipline

- A manual-upload PDF is absent → SKIP + log `AWAITING_MANUAL_UPLOAD`; do NOT fabricate chunks, do NOT fail the whole asset. Surface the upload list to native.
- Do NOT classify `topic_tag` here (that is bg_text_index, Doc 7). Do NOT extract rules here (bg_rules, Doc 8). Ingest + embed only.
- Do NOT switch to the `classical_chunks`/`classical_texts` (migration 158) tables — the design + all downstream assets use `classical_text_chunks`.
- Embedding model version MUST be pinned (record it) so rebuilds are byte-deterministic (design §4.5).
- Out of scope: OCR of poor scans (if a PDF won't chunk cleanly, flag to native), per-chart anything.

---

*End of bg_texts brief (Document 6 of 15).*
