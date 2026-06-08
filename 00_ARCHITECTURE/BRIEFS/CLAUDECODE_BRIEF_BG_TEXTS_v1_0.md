---
artifact: CLAUDECODE_BRIEF_BG_TEXTS_v1_0
canonical_id: L0_BG_TEXTS_BRIEF
version: 1.1
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: Corpus Staging (prep/l0-corpus-staging) 2026-06-08 — 13-text corpus decision, clear-and-rebuild, multi-volume, Devanagari, provenance_tier propagation, floor revision
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_texts writer (classical text corpus ingestion)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: "8000 (11 staged); 10000 (full 13 texts)"
dependencies: []  # Tier 2 — needs source PDFs in GCS, not other L0 assets
llm_cost: "embeddings only (Vertex AI text-multilingual-embedding-002 / text-embedding-004, 768-dim — deterministic transform)"
document_number: 6 of 15
---

## Amendment v1.1 — 13-text corpus decision (2026-06-08)

The following 10 changes supersede the v1.0 body wherever they conflict. Specific inline sections (§0, §1, §2, §3a, §4, §6, §7, §8) have been updated in-place below.

1. **DROP tajaka_neelakanthi and bhrigu_samhita.** Both texts are removed from the §2 table and all references. The corpus is 13 texts, not 15.
2. **Clear-and-rebuild mandate.** The "existing data KEPT / delta-ingest" framing is replaced: the writer executes `DELETE FROM classical_text_chunks` before rebuilding all texts from GCS PDFs. Idempotency contract: same PDF + pinned embedding model version = identical chunks via `content_sha256`.
3. **Multi-volume support.** When a text has `gcs_path_vol2` in the registry (bphs has Vol 1+2; jataka_parijata has Vol I+II; yavana_jataka has vol1+vol2), BOTH volumes are ingested under one `text_id`. The chunker processes each volume sequentially, tagging chunks with `source_volume: 1` or `2`.
4. **Devanagari/multilingual extraction.** The "OCR out of scope" hard stop is qualified: the extractor must handle non-Latin scripts (pdfminer/pymupdf text layer → `content_sa` for Sanskrit/Devanagari). Vertex AI `text-multilingual-embedding-002` handles Sanskrit/Hindi natively. The flag-to-native clause applies only to PDFs with no clean text layer (truly image-only scans); a PDF with a clean non-Latin text layer is NOT the OCR problem.
5. **provenance_tier propagation.** `l0_texts.py` TEXTS registry carries `provenance_tier` (HIGH/MEDIUM/LOW) per text. Carry this into `classical_text_chunks.source_citation` as a structured prefix: e.g. `"[HIGH] BPHS — Trans. R. Santhanam, Ranjan Publications"`. Downstream bg_concordance/bg_compendium can filter/weight by tier (LOW chunks may be excluded from authoritative assemblies).
6. **Floor recalculation for 13 texts.** The ≥14,000 floor is replaced with: staged floor (11 texts with GCS PDFs) ≥8,000 chunks; full floor (all 13 texts including muhurta_chintamani + lal_kitab when remediated) ≥10,000 chunks. muhurta_chintamani and lal_kitab are `UNSTAGED_PENDING_NATIVE_DECISION`; writer logs `AWAITING_NATIVE_DECISION` for these 2 (edition availability issue, not GCS upload issue).
7. **sarvartha_chintamani OCR gate.** The staged PDF (B. Suryanarayana Row 1899) is image-only — no embedded text layer. The writer must OCR it before chunking (Google Document AI or pdfminer fallback). Alternative: the DjVu OCR extract from archive.org (520KB, ~48,423 English words) is an acceptable extraction path. See §2 note.
8. **saravali partial-corpus note.** The staged PDF covers chapters 1–55 of 58 (CC BY-ND 3.0, MEDIUM provenance). See §2 note.
9. **Remove false "existing pipeline" statement.** The v1.0 claim "PDF→text→chunk pipeline already exists in l0_texts.py per Stream C" is incorrect — `l0_texts.py` has a seed-chunk writer, not a PDF ingest pipeline. The writer must implement the PDF→extract→chunk→embed pipeline from scratch.
10. **text_id discipline — bphs_jaimini vs jaimini_sutram.** The registry uses `text_id = bphs_jaimini`. The DB `classical_texts` table may have a legacy `jaimini_sutram` row from the old MCP schema. The writer must upsert a `bphs_jaimini` row in `classical_texts`. Do NOT delete the `jaimini_sutram` row (may have FKs). Do NOT write chunks under `jaimini_sutram`; all Jaimini chunks use `bphs_jaimini`.

---

# bg_texts — Writer Brief (classical text corpus ingestion + embeddings)

> **The corpus.** `bg_texts` is the chunked, verse-addressable, embedded body of the classical literature. This brief ingests all 13 texts of the native's corpus and rebuilds `classical_text_chunks` from scratch. The ONLY non-deterministic call permitted anywhere in L0 is the embedding transform here (Vertex AI, deterministic at a fixed model version) — holistic design v1.1 locked decision. No LLM generation, no LLM classification (that moved to the deterministic classifier in bg_text_index, Doc 7).

## §0 — Asset summary

- **Asset ID:** `bg_texts`. **Backing:** `classical_text_chunks` (NOT `classical_chunks` — see §1). **Scope:** `global`. **Tier:** 2.
- **Target floor:** **≥8,000 chunks** (11 staged texts); **≥10,000 chunks** (full 13 texts once muhurta_chintamani + lal_kitab are remediated).
- **Source category:** source PDFs in GCS + deterministic embedding transform.
- **Dependency:** source PDFs staged in GCS for 11 of 13 texts. muhurta_chintamani + lal_kitab are `UNSTAGED_PENDING_NATIVE_DECISION` (edition sourcing required, not a GCS upload issue). yavana_jataka has multi-volume GCS paths (vol1 + vol2) and is staged.

## §3a — Floor Achievement Arithmetic (v1.1 — 13-text corpus)

Per-text expected chunk estimates for the 13-text corpus:

| # | text_id | Expected chunks | Notes |
|---|---|---|---|
| 1 | bphs | ~2,000 | Vol 1 + Vol 2 (multi-volume) |
| 2 | phaladeepika | ~800 | |
| 3 | jataka_parijata | ~1,000 | Vol I + Vol II (multi-volume) |
| 4 | uttara_kalamrita | ~350 | |
| 5 | bphs_jaimini | ~200 | |
| 6 | saravali | ~800 | chs 1–55/58 only |
| 7 | brihat_jataka | ~600 | |
| 8 | hora_sara | ~350 | |
| 9 | sarvartha_chintamani | ~600 | OCR required (image-only PDF) |
| 10 | brihat_samhita | ~1,800 | |
| 11 | yavana_jataka | ~700 | vol1 + vol2 (multi-volume) |
| 12 | muhurta_chintamani | ~700 | **UNSTAGED_PENDING_NATIVE_DECISION** |
| 13 | lal_kitab | ~700 | **UNSTAGED_PENDING_NATIVE_DECISION** |
| **11 staged** | | **~9,200** | texts 1–11 |
| **All 13** | | **~10,600** | includes texts 12–13 when remediated |

> **Floor thresholds:** Staged (11 texts): ≥8,000 chunks. Full (13 texts): ≥10,000 chunks. For texts 12–13, the writer logs `AWAITING_NATIVE_DECISION` (edition sourcing issue, not a GCS upload gap) and CONDITIONAL-APPROVEs the 11-text build. No migration authored by bg_texts (no depends_on UPDATE).


## §1 — Schema reference

Two chunk tables exist in the DB — **use `classical_text_chunks`** (the one `l0_texts.py` + `l0_text_index.py` operate on, the one migration 177 added `topic_tag` to, the one the design's count_sql targets). `classical_chunks`/`classical_texts` (migration 158, `text_key`/`VECTOR(768)`) is the older M8 schema; do NOT switch the writer to it. Confirm at runtime:

```bash
psql_prod -c "\d classical_text_chunks"   # the bg_texts backing table
```

`classical_text_chunks` carries (from l0_texts.py INSERTs + migration 081/177 ALTERs): `text_id, chapter, verse_start, verse_end, verse_ref, content_sa, content_en, summary, topics, source_citation, translator, tradition_school, embedding vector(768), content_sha256, topic_tag`. Verify exact columns with `\d`.

> **Existing data is CLEARED.** The writer executes `DELETE FROM classical_text_chunks` before rebuilding all 13 texts deterministically from GCS PDFs. This ensures determinism — prior chunking method was unknown/non-reproducible. Idempotency contract: same PDF + pinned embedding model version = identical chunks via `content_sha256`. `l0_texts.py` defines `TEXTS` (registry entries) and a `seed_texts` writer; this brief replaces that approach with a full PDF→extract→chunk→embed pipeline implemented from scratch (the seed-chunk writer is not a PDF ingest pipeline). The `TEXTS` registry must be extended to all 13 texts with `provenance_tier`, `gcs_path`, and `gcs_path_vol2` (where applicable).

## §2 — Source references (the 13 texts)

Per design §3.3 / `L0FR_SOURCE_DATA_v1_0.md`:

| # | text_id | Provenance tier | GCS staged? | Multi-vol? | Expected chunks | Notes |
|---|---|---|---|---|---|---|
| 1 | bphs | HIGH | YES | YES (vol1+vol2) | ~2,000 | |
| 2 | phaladeepika | HIGH | YES | NO | ~800 | |
| 3 | jataka_parijata | HIGH | YES | YES (Vol I+II) | ~1,000 | |
| 4 | uttara_kalamrita | HIGH | YES | NO | ~350 | |
| 5 | bphs_jaimini | HIGH | YES | NO | ~200 | See text_id discipline note below |
| 6 | saravali | MEDIUM | YES | NO | ~800 | Chs 1–55 of 58 only (CC BY-ND 3.0) |
| 7 | brihat_jataka | HIGH | YES | NO | ~600 | |
| 8 | hora_sara | MEDIUM | YES | NO | ~350 | |
| 9 | sarvartha_chintamani | MEDIUM | YES | NO | ~600 | **OCR required** — staged PDF (B. Suryanarayana Row 1899) is image-only; no embedded text layer. Writer must OCR before chunking (Google Document AI or pdfminer fallback). Alternative: DjVu OCR extract from archive.org (~520KB, ~48,423 English words) is an acceptable extraction path. |
| 10 | brihat_samhita | HIGH | YES | NO | ~1,800 | |
| 11 | yavana_jataka | MEDIUM | YES | YES (vol1+vol2) | ~700 | |
| 12 | muhurta_chintamani | MEDIUM | **NO** | NO | ~700 | **UNSTAGED_PENDING_NATIVE_DECISION** — edition sourcing required; writer logs `AWAITING_NATIVE_DECISION` |
| 13 | lal_kitab | LOW | **NO** | NO | ~700 | **UNSTAGED_PENDING_NATIVE_DECISION** — edition sourcing required; writer logs `AWAITING_NATIVE_DECISION` |

**Staged floor (11 texts): ≥8,000 chunks. Full floor (all 13 texts): ≥10,000 chunks.**

> **provenance_tier propagation:** each text's `provenance_tier` (HIGH/MEDIUM/LOW) must be carried into `classical_text_chunks.source_citation` as a structured prefix, e.g. `"[HIGH] BPHS — Trans. R. Santhanam, Ranjan Publications"`. Downstream bg_concordance/bg_compendium can filter/weight by tier (LOW chunks may be excluded from authoritative assemblies).

> **text_id discipline:** these 13 `text_id` values MUST match the `entity_class='text'` canonical_ids authored in bg_ontology Doc 5 §3.6. **bphs_jaimini vs jaimini_sutram:** the registry uses `text_id = bphs_jaimini`. The DB `classical_texts` table may have a legacy `jaimini_sutram` row (old MCP schema). The writer must upsert a `bphs_jaimini` row in `classical_texts`. Do NOT delete the `jaimini_sutram` row (may have FKs). All Jaimini chunks use `bphs_jaimini`; no chunks are written under `jaimini_sutram`.

## §3 — Embedded content

None to embed — the content lives in the source PDFs. This brief requires the writer to implement the full **PDF→extract→chunk→embed pipeline from scratch** (the existing `l0_texts.py` `seed_texts` writer is a seed-chunk writer, not a PDF ingest pipeline). The `TEXTS` registry in `l0_texts.py` must be extended/replaced with all 13 texts including `provenance_tier`, `gcs_path`, `gcs_path_vol2` (for multi-volume texts), and `staged` flag.

```python
# Replace/extend TEXTS in l0_texts.py — full 13-text registry (one shown):
TEXTS = [
  # ...
  {"text_id":"saravali","title_en":"Saravali","title_sa":"Sārāvalī","author":"Kalyana Varma",
   "provenance_tier":"MEDIUM","tradition":"parashari","school":"parashari","language_original":"sanskrit",
   "gcs_path":"gs://<bucket>/classical_texts/saravali.pdf","gcs_path_vol2":None,
   "expected_chunks":800,"staged":True,
   "source_citation":"[MEDIUM] Saravali (Kalyana Varma), chs 1–55/58, CC BY-ND 3.0"},
  # ... bphs (vol1+vol2), jataka_parijata (Vol I+II), yavana_jataka (vol1+vol2) — gcs_path_vol2 set;
  # muhurta_chintamani/lal_kitab — staged=False, logs AWAITING_NATIVE_DECISION
]
```

## §4 — Writer implementation

`pipeline/orchestrator/writers/bg_texts.py` (`@register('bg_texts')`) implementing the full PDF→extract→chunk→embed pipeline from scratch. Steps:

0. **Clear the table.** Execute `DELETE FROM classical_text_chunks` before any ingest. This is the clear-and-rebuild mandate — determinism requires a clean slate (prior chunking method was unknown). Log the row count deleted.
1. **Locate the PDF(s)** in GCS (`gcs_path`; `gcs_path_vol2` if present for multi-volume texts).
   - If `staged=False` (muhurta_chintamani, lal_kitab) → log `AWAITING_NATIVE_DECISION: <text_id>` (edition not yet sourced) and SKIP. Do NOT log these as `AWAITING_MANUAL_UPLOAD` — the issue is edition availability, not GCS upload.
   - If `staged=True` but GCS object absent → log `AWAITING_MANUAL_UPLOAD: <text_id>` and SKIP (operator action required).
   - For multi-volume texts (bphs, jataka_parijata, yavana_jataka): process `gcs_path` then `gcs_path_vol2` sequentially under the same `text_id`. Tag each chunk with `source_volume: 1` or `2`.
2. **Extract + OCR gate.** Use pdfminer/pymupdf to extract the text layer. If the PDF has a clean text layer (including non-Latin/Devanagari scripts), proceed directly — multilingual PDFs with embedded text are not the "OCR problem". If the PDF is image-only (no text layer; detected by zero-character extraction): for sarvartha_chintamani, use Google Document AI or the archive.org DjVu OCR extract (~520KB); for other image-only PDFs, log `AWAITING_OCR: <text_id>` and flag to native. Sanskrit/Devanagari text layers are extracted to `content_sa`; English translations to `content_en`.
3. **Chunk** (chapter/verse-delimiter aware). Each chunk → `{text_id, chapter, verse_start, verse_end, verse_ref, content_en, content_sa?, source_citation, content_sha256, source_volume}`. `source_citation` must carry the `provenance_tier` prefix: `"[HIGH|MEDIUM|LOW] <title> — <translator/edition>"`.
4. **Embed** each chunk's `content_en` (or `content_sa` if no English layer) via Vertex AI `text-multilingual-embedding-002`, 768-dim → `embedding` column. Batch for cost. Pin and record the model version. This is the only permitted non-deterministic call; it is deterministic at a fixed model version.
5. **Insert** `ON CONFLICT (content_sha256) DO NOTHING` (or `(text_id, chapter, verse_start, verse_end)` — match the existing unique constraint) for idempotency within a run.
6. Update `classical_texts.chunk_count` per text. Upsert the `bphs_jaimini` row in `classical_texts` if absent; do NOT create or modify `jaimini_sutram`.
7. `topic_tag` is left NULL here — it is set by **bg_text_index (Doc 7)** deterministically. Do NOT classify topics in this writer.

> **Idempotency + determinism:** after the initial clear-and-rebuild, re-running ingest with the same PDFs + same pinned embedding model version produces identical chunks (same `content_sha256`) → 0 new rows on the second pass. The count-first guard applies: if `classical_text_chunks` already ≥ staged floor and all 11 staged texts present, the writer verifies coverage and exits cleanly.

## §5 — FK validation

- `classical_text_chunks.text_id` should correspond to a `classical_texts` registry row (insert the registry row first per text).
- No ontology FK (chunks are not entities). But `text_id` values must be in the bg_ontology `text` class set (§2 discipline) so downstream `bg_compendium_index.text_id` resolves.
- **depends_on:** none on other L0 assets (Tier 2 by PDF availability, not by L0 dependency). Leave `asset_registry.depends_on` empty for bg_texts unless native wants it after bg_reference (not required).

## §6 — Unit tests

`test_bg_texts.py`: (1) ≥8,000 chunks total from staged texts OR (if any staged PDFs absent) ≥ the floor of the available texts with a logged `AWAITING_MANUAL_UPLOAD` / `AWAITING_NATIVE_DECISION` list; (2) every chunk has non-null `source_citation` (with `[HIGH|MEDIUM|LOW]` prefix) + `verse_ref`; (3) every chunk has a 768-dim `embedding` (no null embeddings on ingested texts); (4) all 13 `text_id`s present in `classical_texts` registry (muhurta_chintamani and lal_kitab rows present but chunk_count=0 with AWAITING_NATIVE_DECISION logged); (5) re-ingest after clear inserts the same count (idempotent); (6) FORENSIC spot-check: BPHS Ch.7 (bhava) chunks retrievable; (7) multi-volume check: bphs chunks tagged source_volume=1 AND source_volume=2; (8) `bphs_jaimini` row exists in `classical_texts`; `jaimini_sutram` row NOT deleted.

## §7 — Vimarśaka check

APPROVE iff: ≥8,000 chunks from staged texts (OR all staged texts ingested + gaps explicitly logged); zero null `source_citation` (every `source_citation` has `[HIGH|MEDIUM|LOW]` prefix); zero null `embedding` on ingested texts; 13 registry rows in `classical_texts`. **If below 8,000 staged floor solely due to `AWAITING_NATIVE_DECISION` (muhurta_chintamani, lal_kitab) or `AWAITING_MANUAL_UPLOAD` (staged text with missing GCS object), Vimarśaka returns CONDITIONAL-APPROVE with the gap list** — this is an operator/native action, not a writer failure. If below floor for any OTHER reason (pipeline failure, missing chunks on a staged text with a valid GCS object), REJECT. Full APPROVE (≥10,000) available only when all 13 texts are staged and ingested.

## §8 — Hard stops + scope discipline

- **Clear-before-rebuild mandate.** The writer MUST execute `DELETE FROM classical_text_chunks` before any ingest. Do NOT skip this step. Do NOT delta-ingest onto prior data — prior chunking method was unknown/non-reproducible.
- **AWAITING_NATIVE_DECISION vs AWAITING_MANUAL_UPLOAD.** muhurta_chintamani and lal_kitab are `UNSTAGED_PENDING_NATIVE_DECISION` (edition sourcing issue). Log them as `AWAITING_NATIVE_DECISION`, NOT `AWAITING_MANUAL_UPLOAD`. Do NOT fabricate chunks, do NOT fail the whole asset. Surface the decision list to native.
- **OCR gate for image-only PDFs.** If a staged PDF has no embedded text layer (zero-character extraction): for sarvartha_chintamani specifically, use Google Document AI or the archive.org DjVu OCR extract. For any other image-only PDF, log `AWAITING_OCR: <text_id>` and surface to native. Do NOT skip OCR-required texts silently.
- **Non-Latin text layers are NOT the OCR problem.** A PDF with a clean Devanagari/Sanskrit text layer is extracted normally via pdfminer/pymupdf; Vertex AI `text-multilingual-embedding-002` handles Sanskrit/Hindi natively.
- **provenance_tier propagation.** Every chunk's `source_citation` MUST carry a `[HIGH|MEDIUM|LOW]` prefix. Do NOT insert chunks with bare (un-prefixed) `source_citation` values.
- Do NOT classify `topic_tag` here (that is bg_text_index, Doc 7). Do NOT extract rules here (bg_rules, Doc 8). Ingest + embed only.
- Do NOT switch to the `classical_chunks`/`classical_texts` (migration 158) tables — the design + all downstream assets use `classical_text_chunks`.
- Embedding model version MUST be pinned (record it) so rebuilds are byte-deterministic (design §4.5).
- Do NOT write chunks under `jaimini_sutram`; do NOT delete the `jaimini_sutram` row. All Jaimini chunks use `bphs_jaimini`.

---

*End of bg_texts brief (Document 6 of 15).*
