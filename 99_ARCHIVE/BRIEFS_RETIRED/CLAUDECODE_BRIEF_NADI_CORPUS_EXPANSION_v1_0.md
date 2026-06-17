---
artifact: CLAUDECODE_BRIEF_NADI_CORPUS_EXPANSION_v1_0
canonical_id: NADI_CORPUS_EXPANSION_BRIEF
version: 2.0
status: COMPLETE
authored_by: Cowork (planning) 2026-06-09
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan — Nadi corpus expansion (13→15 texts) — ADDITIVE delta-ingest + downstream consistency
parent: L0 Brahmagyan campaign (SEALED PR #231, merge 3a6ec226) — post-seal deliberate corpus expansion
v2_0_change: "ADDITIVE (non-destructive) model. The 2 Nadi texts are NEW + non-overlapping — they are ADDED to the corpus, NOT a clear-and-rebuild. Existing 13 texts' 8,193 chunks + all derived rows stay UNTOUCHED. Only the Nadi additions flow through the cascade. v1.0's destructive DELETE-then-rebuild is REJECTED for this operation (native decision)."
llm_cost: "embeddings only (Vertex AI, pinned) for the 2 new texts' chunks; ZERO LLM everywhere else"
---

# Nadi Corpus Expansion (13→15) — ADDITIVE Delta-Ingest + Downstream Consistency

> **Goal.** ADD the 2 already-staged Nadi texts to the L0 classical-text corpus **non-destructively** and extend every dependent asset/registry/index to reflect them — so the corpus is consistent at 15 texts WITHOUT touching the existing 13 texts' chunks or any derived row that doesn't depend on the new texts. The PDFs are staged in GCS (vetted PASS). This is a deliberate, additive post-seal expansion.

> **CORE PRINCIPLE (v2.0, native decision): ADDITIVE, NOT DESTRUCTIVE.** The 2 Nadi texts are NEW and have ZERO overlap with the existing corpus. So: INSERT the 2 texts' chunks; leave the existing 8,193 chunks and all 13-text-derived rows exactly as they are. Each downstream asset is EXTENDED over only the new chunks, not re-run over the whole corpus. No `DELETE FROM classical_text_chunks`. Floors INCREASE by the genuine additions.

> **The writers already support this.** Verified on main: bg_texts has skip-logic for already-present texts (lines 297–314) + `content_sha256` idempotency — the only destructive piece is a hardcoded `DELETE` (line 250) that this brief GUARDS behind a mode flag. bg_text_index already processes ONLY `WHERE topic_tag IS NULL` chunks (additive by design). bg_rules uses deterministic rule_ids + `ON CONFLICT DO NOTHING` (re-run = additive). So this is a small, surgical change, not a writer rewrite.

## §0 — Verified starting state (confirmed against main @ current)
- **2 Nadi PDFs already staged in GCS** (PASS, vetted 2026-06-09 on `prep/nadi-texts-sourcing`):
  - `bhrigu_nandi_nadi` — R.G. Rao / Ranjan Publications ~1986. `gs://madhav-marsys-sources/L8/classical_texts/source/bhrigu_nandi_nadi.pdf` (327pp, 100% text layer, clean English aphorism prose). Minor chart-diagram label fragments (Sat./Ven./Dh./Dt.).
  - `nadi_navamsa_patel` — C.S. Patel / Sagar Publications **1996** (NOT 1984). `gs://madhav-marsys-sources/L8/classical_texts/source/nadi_navamsa_patel.pdf` (16.8MB) + `…/nadi_navamsa_patel_djvu.txt` (417KB pre-extracted OCR). **INGEST THE DjVu .txt** (cleaner). 92% coherent English; ~8% inline Sanskrit-verse fragments (English translation follows each).
- **Registry is 13 texts** (confirmed: 13 distinct `text_id`s in `l0_texts.py`). The 2 Nadi texts are NOT yet registered. Clean start, no half-done state.
- **`nadi` is already a recognized school** downstream (`platform/python-sidecar/brahmagyan/bodha/_grounding_engine.py` maps BNN/Chandra Kala → nadi). No new school to invent.
- **STALE BUG to fix in passing:** `bg_concordance` `TEXT_SCHOOL` map still maps `bhrigu_samhita → nadi`, but **bhrigu_samhita was DROPPED** from the corpus. Remove it.
- **bg_texts has BOTH modes available:** additive delta-ingest (skip-already-present + content_sha256 idempotency, already coded) and full clear-and-rebuild (the hardcoded DELETE). This brief uses ADDITIVE; full-rebuild stays available for the delete-rebuild proof.
- **13-text baseline counts (the "before" — these stay UNCHANGED for the 13; only Nadi adds):** bg_texts 8,193 · bg_text_index 327 · bg_rules 1,976 · bg_remedies 265 · bg_concordance 477 · bg_compendium_index 7,025 · bg_yogas 175.

## §1 — The cascade (ADDITIVE — extend over ONLY the new chunks)
```
bg_texts (ADD 2 texts' chunks; existing 8,193 untouched)
  → bg_text_index   (classify ONLY new chunks — already WHERE topic_tag IS NULL)
  → bg_rules        (extract ONLY new chunks — deterministic rule_ids + ON CONFLICT = additive)
  → bg_remedies     (sweep ONLY new chunks for remedy markers)
  → bg_concordance  (TEXT_SCHOOL fix + ADD new (topic × nadi) rows; existing rows untouched)
  → bg_compendium_index (ADD per-text rows for the 2 new texts; existing 13-text rows untouched)
  → bg_yogas        (corpus-verse residual over ONLY new chunks)
```
Each EXTENDS over only the new chunks; each `target_floor` INCREASES by the genuine additions (existing derived rows are never deleted or recomputed).

## §1.1 — Integrity property preserved (why additive is safe)
The L0 delete-rebuild proof (Doc 15) is NOT weakened by additive ingest, BECAUSE bg_texts retains full-rebuild mode: a wipe-and-rebuild still reproduces the identical 15-text corpus (same PDFs + pinned model + content_sha256). Additive is the routine-add path; full-rebuild is the proof path. Both produce the same end state. The reproducibility guarantee holds.

## §2 — Governing principles (binding — carried from L0)
- **Floors are ASPIRATIONAL, not gates** (`[[feedback-floors-are-aspirational-not-gates]]`): after each re-run, `target_floor = achieved count`; never fabricate to hit a number; never halt on a low count. Integrity is the only hard gate.
- **Deterministic + ZERO LLM** except bg_texts embeddings (pinned Vertex AI model). Same PDFs + pinned model = byte-identical chunks (content_sha256).
- **Nadi rows MUST be tagged `tradition_school='nadi'`** and carried through extraction so Nadi predictive logic NEVER blends with Parashari in rules/concordance/synthesis. Nadi is a distinct system.
- **Verify against repo + prod, never the report** (`[[pr-quality-gate-is-not-a-merge]]`, `[[feedback-ac-must-verify-target-environment]]`). ACs verify against PROD.
- **L1 isolation:** this is L0 corpus work — it MUST NOT touch the L1/Ganita build or `chart_facts`. Confirm no collateral.

## §3 — PHASES

### Phase 0 — Pre-flight audit (read-only)
- `gsutil ls gs://madhav-marsys-sources/L8/classical_texts/source/` — confirm both Nadi PDFs (+ patel DjVu .txt) present.
- Confirm `l0_texts.py` registry = 13 texts.
- Snapshot prod baseline (the "before" for the cascade): `SELECT text_id, count(*) FROM classical_text_chunks GROUP BY text_id` + total; and `SELECT asset_id, target_floor FROM asset_registry WHERE asset_id IN ('bg_texts','bg_text_index','bg_rules','bg_remedies','bg_concordance','bg_compendium_index','bg_yogas')` and their live row counts.
- Branch `feature/nadi-corpus-expansion` off main.

### Phase 1 — Register the 2 Nadi texts
- `l0_texts.py` TEXTS: ADD 2 entries → registry = 15:
  - `bhrigu_nandi_nadi`: gcs_path (pdf), tradition_school='nadi', provenance_tier='MEDIUM', language='english', source_citation='Bhrigu Nandi Nadi, R.G. Rao, Ranjan Publications (~1986); archive.org grey-upload, provenance MEDIUM'.
  - `nadi_navamsa_patel`: gcs_path (pdf) + the DjVu .txt source path, tradition_school='nadi', provenance_tier='MEDIUM', language='english', source_citation='Predicting Through Navamsa and Nadi Astrology, C.S. Patel, Sagar Publications (1996); archive.org grey-upload, provenance MEDIUM'. **Mark the DjVu .txt as the ingest source.**
- **Patel verse-fragment handling (chunker):** tag lines where >30% chars are non-ASCII as `verse_fragment` — EXCLUDE from embedding OR prefix "Sanskrit verse context". Wire into the chunker for patel (or globally if it doesn't harm the clean texts). Do NOT let garbled Devanagari verse-lines pollute embeddings.
- **bhrigu_nandi chart-label fragments (optional):** one regex pass stripping chart-diagram labels (Sat./Ven./Dh./Dt./Dh.) — low-impact; do it if cheap, else the chunker degrades gracefully.

### Phase 2 — ADDITIVE bg_texts ingest (ADD 2 texts; NO DELETE) → GATE
- **Guard the DELETE:** add a mode flag to bg_texts (e.g. `rebuild_mode: 'additive' | 'full'`, default `'additive'`). In additive mode the `DELETE FROM classical_text_chunks` at line ~250 is SKIPPED; the existing skip-logic (lines 297–314: skip texts whose chunks already exist) handles the 13 present texts, so only `bhrigu_nandi_nadi` + `nadi_navamsa_patel` are chunked + embedded + INSERTed (`ON CONFLICT (content_sha256) DO NOTHING`). The DELETE path remains available for `mode='full'` (the rebuild proof).
- Run additive: the 13 existing texts are skipped (chunks already present); the 2 Nadi texts are added. Expect total = 8,193 + (bhrigu_nandi ~327pp worth + patel DjVu worth) — **the 8,193 are UNCHANGED, only the delta is new.**
- Set `bg_texts.target_floor` = new total achieved count (migration, next free # after 194 — confirm ceiling: `ls platform/supabase/migrations/ | grep -E '^[0-9]' | sort -n | tail -1`).
- **Integrity check (Phase-2 gate):** 15 rows in `classical_texts`; the 2 Nadi texts' chunks present AND tagged `tradition_school='nadi'`; **the 13 existing texts' chunk counts UNCHANGED vs the Phase-0 baseline** (additive proof — nothing was destroyed); zero null embeddings/citations on the new chunks; FORENSIC anchor still retrievable; re-run of additive inserts 0 (idempotent); no jaimini_sutram/lal_kitab/bhrigu_samhita chunks introduced.
- **GATE — report: new Nadi chunk counts + the per-text breakdown, PROOF the 13 existing counts are unchanged, and a 3-chunk Patel sample (the DjVu verse-fragment handling is the one novel piece — confirm it's neither over-filtering English nor embedding garbled Devanagari). PAUSE for native clearance before the cascade.**

### Phase 3 — ADDITIVE cascade (after gate; extend over ONLY new chunks; DAG order)
Each EXTENDS over only the new Nadi chunks; existing derived rows are NEVER deleted/recomputed. Set each `target_floor` = new total achieved count (one migration per asset, sequential after Phase 2's):
- **bg_text_index** — already additive (processes only `topic_tag IS NULL` chunks). Run it → classifies ONLY the new Nadi chunks; existing 13-text topic_tags untouched. Nadi English prose classifies (unlike Devanagari muhurta/tajaka) → distinct-tag count may GROW from 327. Verify existing chunks' tags unchanged.
- **bg_concordance** — **FIX `TEXT_SCHOOL` FIRST:** remove stale `bhrigu_samhita` (already done in Phase 1 commit — verify); confirm `bhrigu_nandi_nadi → nadi` + `nadi_navamsa_patel → nadi` present. Re-run: because nadi is a NEW school dimension, this ADDS new (topic × nadi) rows; existing (topic × parashari/jaimini/tajaka) rows are untouched (`ON CONFLICT (topic_id, school) DO NOTHING`). Grows from 477 by the nadi rows.
- **bg_rules** — extract over the new chunks. Deterministic rule_ids + `ON CONFLICT DO NOTHING` mean existing rules are untouched even if the writer scans all chunks; only NEW Nadi rules insert. **Nadi rules MUST carry `tradition_school='nadi'`** — confirm the extractor propagates the source text's school so Nadi never blends with Parashari. Grows from 1,976 by genuine Nadi additions.
- **bg_remedies** — sweep ONLY the new chunks for remedy markers (additive; existing 265 untouched). May grow if Nadi has remedy markers.
- **bg_compendium_index** — ADD per-text × topic aggregation rows for the 2 new texts (`ON CONFLICT` dedup); existing 13-text rows untouched. Grows from 7,025 by the Nadi rows.
- **bg_yogas** — corpus-verse residual over ONLY the new chunks (deterministic ids + ON CONFLICT; existing 175 untouched). Nadi may name few/no yogas — accept achieved, prove it scanned.

### Phase 4 — Full consistency verification (the "robust + consistent" gate, vs PROD)
Assert ALL:
- Registry: 15 texts in `l0_texts.py` AND `classical_texts` table. Both Nadi tagged `tradition_school='nadi'`.
- **ADDITIVE PROOF — the 13 existing texts' chunk counts AND their derived rows are UNCHANGED vs Phase-0 baseline** (only Nadi additions are new; nothing was destroyed/recomputed). This is the central assertion of the additive model.
- Every text-dependent asset's `target_floor` = its NEW total achieved count (old count + Nadi additions). No stale floors. No NULL floors (→ no empty cockpit bars).
- `bg_concordance` has a `nadi` school dimension; `TEXT_SCHOOL` has NO dropped-text entries (bhrigu_samhita/lal_kitab gone).
- Cockpit: all affected tiles lit at 100% (achieved = floor); bars populated.
- FORENSIC anchor intact; `chart_facts` / L1 untouched (no collateral).
- Determinism: a re-run of the additive ingest inserts 0 (content_sha256 idempotency); AND full-rebuild mode still reproduces the identical 15-text corpus (the rebuild-proof property is preserved — §1.1).
- **before/after table:** per-asset count 13-text → 15-text, floor old → new — showing the 13-text portion UNCHANGED and the delta clearly attributable to Nadi.

### Phase 5 — Seal
- One PR `feat(l0): Nadi corpus expansion 13→15 + downstream consistency cascade`. Per-phase commits. Migrations: bg_texts floor + 5 cascade floors + the concordance TEXT_SCHOOL fix.
- Verify merge by CONTENT (`[[pr-quality-gate-is-not-a-merge]]`): `gh pr view N --json state,mergeCommit` (MERGED + non-null) AND the migrations + the 15-text registry physically on main (squash makes head-SHA a non-ancestor — check content).
- Update memory `[[project-l0-brahmagyan-campaign-state]]` to 15-text corpus + new per-asset counts.

## §4 — Risks / notes
- **Patel DjVu Sanskrit-verse fragments** — handle via the >30%-non-ASCII tag; don't pollute embeddings with garbled Devanagari verse-lines.
- **bg_rules school-blending** — the single most important integrity point: Nadi rules MUST be tagged `nadi`. Confirm the rule extractor carries the source text's `tradition_school` through to each rule row, so downstream L2+ synthesis never conflates Nadi (planetary-combination/transit logic, often Ascendant-less) with Parashari.
- **Floor growth is expected + GOOD** — Nadi English prose participates in classification/extraction (the Devanagari-invisible gap does NOT apply — these are English texts). Unlike muhurta/tajaka, these 2 SHOULD lift text_index/rules/concordance counts. That growth is genuine data, exactly what floors-aspirational wants.
- **L1 isolation** — confirm zero collateral to the L1/Ganita build or chart_facts. This is L0-only.

## §5 — Execution shape
Phase 1 is DONE (commit 84a8ad21 — push the branch to origin first; it's local-only). Inline through Phase 2 (additive bg_texts ingest — fast now, only 2 texts embed, NOT a 40-min full rebuild), GATE for native clearance, then the Phase 3 additive cascade as a sequence. One branch (`feature/nadi-corpus-expansion`), one PR. HALT on any integrity violation (never on a low count); HALT if any existing chunk/row is destroyed, if Patel DjVu is garbled beyond verse-fragment handling, or if any Nadi rule lands without its `nadi` tag.

> **Note on cost/time:** because this is ADDITIVE (only the 2 new texts embed), Phase 2 is NOT the ~40-min full-corpus rebuild v1.0 implied — it embeds only the Nadi chunks (~minutes), leaving the existing 8,193 embeddings untouched.

## §6 — Hard stops
- **Any DELETE of existing (13-text) chunks or derived rows → integrity violation, HALT.** This operation is ADDITIVE. The only permitted destructive op is removing the stale `bhrigu_samhita`/`lal_kitab` entries from the TEXT_SCHOOL *map* (code, not data). If the 13 existing texts' chunk counts change vs Phase-0 baseline, STOP — something ran in destructive mode.
- A Nadi PDF missing from GCS → halt, report (re-stage from `prep/nadi-texts-sourcing`).
- Patel DjVu garbled beyond the >30%-non-ASCII handling → halt, report (consider the PDF instead of the .txt, or native edition-purchase).
- Any Nadi-sourced rule/concordance row WITHOUT `tradition_school='nadi'` → integrity violation, halt (Nadi must not blend into Parashari).
- FORENSIC anchor lost or chart_facts touched → halt (collateral to L1).
- Phase-4 finds a stale/NULL floor or empty cockpit bar → fix before seal.

---

*End of Nadi Corpus Expansion brief (v1.0). The PDFs are staged; this brief ingests them + propagates full consistency to 15 texts.*
