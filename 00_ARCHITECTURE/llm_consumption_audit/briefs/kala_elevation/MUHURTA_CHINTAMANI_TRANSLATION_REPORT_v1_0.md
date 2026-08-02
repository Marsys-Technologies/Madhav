---
artifact: MUHURTA_CHINTAMANI_TRANSLATION_REPORT
canonical_id: MUHURTA_CHINTAMANI_TRANSLATION_REPORT
version: 1.0
status: CLOSED — priority sections complete, verified, re-embedded; remainder of the 274 chunks
  intentionally out of scope this session (see §7 Resume State).
created: 2026-08-03
author: Claude Code (Sonnet 5), supervised corpus-curation session
governing_brief: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md v1.1 (this directory)
---

# Muhūrta-Cintāmaṇi Translation — Close-Out Report

## §1 — Summary

Session scope was the four priority sections of `MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md`
v1.1: Agnivāsa reckoning, doṣa-parihāra, vāra×nakṣatra×tithi combination-yogas, and Kota-Chakra
material, within the 274-chunk `muhurta_chintamani` text in `classical_text_chunks`. All 274
chunks were read and classified; **88 chunks matching a priority topic were translated,
independently verified, corrected where the verifier found real defects, and re-embedded**. The
remaining 186 chunks (general muhūrta material outside the four priority topics) were
deliberately left untouched — `content_en` still equals `content_sa`, `translation_status` is
`NULL` — per the brief's own "partial success is real success" framing (§6, §Truth over
completion).

| | Count |
|---|---|
| Total chunks (`muhurta_chintamani`) | 274 |
| Read and classified | 274 / 274 |
| Translated (priority-topic) | 88 |
| Deferred (reviewed, judged untranslatable) | 0 |
| Untouched (non-priority, out of scope) | 186 |
| Re-embedded | 88 / 88 |
| Independently verified (100% of translated) | 88 / 88 |
| Verifier-flagged defects found and corrected | 3 |

## §2 — The gap this closes

Before this pass, `muhurta_chintamani` was ingested (274 chunks, `content_sa` populated) but
`content_en` was byte-identical to `content_sa` for all 274 rows — unretrievable by English
search, unciteable by rules extraction. This pass makes the four priority topics readable in
English for the first time, unblocking the four ṢAḌ-DARŚANA deliverables the brief names as
parked on this gap (item 41's Agnivāsa grounding; paddhati convention (B)
`agnivasa_muhurta_chintamani_arithmetic`; parihāra-graph depth; possible Kota-Chakra
corroboration).

## §3 — Priority-section status

| Topic | Chunks found | Status |
|---|---|---|
| (a) Agnivāsa reckoning | **1** (`muhurta_chintamani_pg0048_c01`, verse 36) | **Translated, verified clean.** This is the *only* Agnivāsa verse in the entire 274-chunk text. The rule: `(tithi + 1 + vāra) mod 4`; remainder 0 or 3 → Agni resides in the earth (homa auspicious); 1 → sky (prāṇa-nāśa); 2 → pātāla (artha-nāśa). Verified metrically exact (Indravajrā, all four pādas) and doctrinally exact against the received tradition. **Deliverables (1) and (2) can re-open on this chunk.** |
| (b) Doṣa-parihāra | **66** | Translated. Covers vratabandha/marriage/travel/vāstu/gṛha-praveśa parihāras: kartarī, ekārgala, upagraha, pāta, lattā, yāmitra exceptions; Bhadrā mukha/puccha and regional exemptions; Jupiter-in-Siṃha/Makara regional parihāras; bāṇa-doṣa cancellation by time-of-day; gaṇa/bhakūṭa/nāḍī-kūṭa marriage-doṣa cancellations; śānti procedures throughout. **Deliverable (3) — parihāra-graph depth — has substantial new material to extract from.** |
| (c) Vāra×nakṣatra×tithi combination-yogas | **21** | Translated. The full Ānandādi 28-yoga system (names, weekday-starting-points, cancellation ghaṭikās), Ravi-yoga, Siddhi-yoga, Utpāta/Mṛtyu/Kāṇa/Siddhi tetrad, Tripuṣkara/Dvipuṣkara, Dagdha/Viṣa/Hutāśana tithi-vāra series, Yamaghaṇṭa, Amṛtasiddhi with its own tithi-level exceptions, and the explicit taxonomy (MC 1.31) classifying combination-doṣas into tithi×vāra / tithi×nakṣatra / nakṣatra×vāra / all-three-together. |
| (d) Kota-Chakra | **0** | **Genuine negative finding**, confirmed independently by multiple shard agents across the full 274-chunk read: no `कोटचक्र` / `कोट-चक्र` material appears anywhere in this text. **Deliverable (4) does not re-open from this source** — if Kota-Chakra corroboration is still wanted, it must come from a different classical text. This is reported, not silently dropped, per B.10.

## §4 — Provenance scheme applied (per brief §4, verbatim)

Every touched row carries: `translation_status='machine_translated_supervised'`,
`translation_provenance='machine_translation_supervised_2026-08; commissioned per
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS; source edition per translator
field'`, `ocr_cleanup_pass_version='mc_ocr_translation_v1_2026-08'` (identical string on every
touched row), `cleaned_devanagari_text` (OCR-repaired Devanāgarī, `content_sa` never modified),
`low_confidence_flag`, `ocr_review_note`, `ocr_confidence_score`, and a recomputed
`content_sha256 = sha256(new content_en)`. `translator`, `content_sa`, `source_citation`,
`content_summary`, `topics` were read-only for this task and are confirmed unmutated on all 274
rows (verified: `count(*) FILTER (WHERE translator IS DISTINCT FROM '<original citation>') = 0`).

### Confidence rubric (stated once, applied uniformly, per brief §5.3)

| `[?]` markers in `cleaned_devanagari_text` | `ocr_confidence_score` |
|---|---|
| 0 | 1.0 |
| 1 | 0.85 |
| 2 | 0.70 |
| 3 | 0.55 |
| 4 or more | 0.40 |

Applied by 10 independent translation agents (one per ~27-chunk page-range shard) and audited
for calibration drift by the verification pass (§6). Final distribution across the 88 translated
chunks: 78 flagged (`low_confidence_flag=true`), 10 clean; mean `ocr_confidence_score` 0.635,
range 0.40–1.00 — consistent with genuinely noisy OCR on a text no prior session had cleaned.

## §5 — Mechanics

- **Migration first**: `platform/supabase/migrations/536_muhurta_chintamani_translation_provenance.sql`
  — additive, nullable `translation_status`/`translation_provenance` columns. `migration-guard`
  reviewed PASS; landed via PR #1041 to `main`, applied to production before any row write.
- **Backup**: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/backups/muhurta_chintamani_pretranslation_backup_20260803.json`
  — all 274 rows' pre-touch `content_sha256` + embedding presence. Revert path documented in the
  fixture's own `note` field (content_sa is immutable and never touched, so it is always the
  ground truth to restore `content_en` from; embeddings are a pure function of `(model, text)`
  per `embedText.ts`, so re-embedding `content_sa` deterministically reproduces the original
  vector — no vectors needed storing).
- **Apply script**: `platform/scripts/corpus/apply_muhurta_chintamani_translations.ts` — batched
  (10/batch), dry-run mode, per-batch row-count verification against
  `ocr_cleanup_pass_version`, idempotent resume (checks target state before writing, skips
  already-applied rows), keyed on `(text_id, chunk_id)`. Mirrors the house style of
  `backfill_conversation_embeddings.ts` (local Vertex AI re-implementation, since
  `embedText.ts` is `server-only`-guarded and cannot be imported from a plain script).
- **Data**: `platform/scripts/corpus/data/muhurta_chintamani_translations.json` — the 274-record
  dataset (88 `action:"translated"`, 186 `action:"skipped_non_priority"`) that the apply script
  consumed; committed alongside the script so a future session can re-run/resume/audit it.
  Per-shard intermediate files are under `platform/scripts/corpus/data/shard_*.json` (10 files,
  one per page-range) and `data/corrections/verifier_corrections_20260803.json` (the 3
  post-verification fixes, §6).
- **Real-data validation**: consolidated 274-record dataset's `chunk_id` set diffed byte-for-byte
  against a live `SELECT chunk_id FROM classical_text_chunks WHERE text_id='muhurta_chintamani'`
  — identical, zero drift, zero duplicates.
- **Apply run**: 88/88 applied, 0 errors, 0 invalid. Post-apply DB verification (not just script
  self-report): joined the live `content_sha256` against the pre-touch backup — **exactly** the
  88 intended rows changed and **exactly** the other 186 are byte-identical to their pre-touch
  state. All 274 rows retain non-null embeddings.

## §6 — Independent verification (brief's acceptance gate)

Per brief §5.3: an independent verifier — not the translator — re-reads ≥10% of translated
chunks plus 100% of the four priority sections. Since only priority-topic chunks were translated
this pass, **100% of translated chunks is also the full priority-section review** — no sampling
gap.

**Method**: 4 independent Opus-tier agents, each reviewing a distinct ~22-chunk slice of the 88,
none of which did any translation work. Each agent independently re-queried `content_sa` live
from the database (not from the translator's output) and checked: fidelity, silent-fabrication
risk, `content_sa` integrity (the immutable-source invariant), ṭīkā/mūla separation, IAST/gloss
discipline, and confidence calibration. The Agnivāsa chunk (§3a) was called out for extra
scrutiny given its outsized downstream weight.

**Verdict, verbatim aggregate**: 88/88 chunks reviewed. **35 clean, 50 minor, 3 major.**

- **`content_sa` integrity: 88/88 pass.** Every chunk's immutable source reads as genuinely
  uncorrected raw OCR in all four verifier groups — no evidence of the "already-cleaned source
  masquerading as raw" failure mode.
- **Domain accuracy**: verifiers independently re-derived roughly 150+ nakṣatra-deity codes,
  bhūta-saṅkhyā numeral ciphers, and classical-doctrine cross-checks (e.g. the Tripuṣkara nakṣatra
  pāda-boundary computation, the Ādi/Madhya/Antya nāḍī sets, the aṣṭama-lagna friendly-lord
  exemptions) against tradition, not just against the ṭīkā — zero decoding errors found.
- **3 major findings, all found, all fixed same session** (see below). No major finding survived
  to the final DB state.
- **50 minor findings**: mostly calibration drift of one rubric step, metre-siglum
  mis-expansions (non-doctrinal), and a handful of unflagged-but-correct typo-level repairs.
  Left as-is — recorded here for the campaign's own reconciliation sweep, not fixed, since none
  affect doctrinal correctness and re-touching 50 rows for cosmetic notes was judged out of
  proportion to the session's remaining scope.

### The 3 major findings and their fixes

| Chunk | Verifier finding | Fix applied |
|---|---|---|
| `pg0020_c01` | Ṭīkā's own region gloss (possibly "Malabar (Kerala)") silently dropped and replaced with "Mālava," inconsistent with this pass's own convention of preserving parenthetical region glosses elsewhere. | The verse-level translation ("Gauḍa and Mālava") is independently correct and unchanged — only the ṭīkā's ambiguous restatement is now marked `[?]` with an explanatory note, rather than silently resolved either way. |
| `pg0034_c01` | The deśāntara (longitude-correction) rule's east/west sign was **inverted** in `content_en` relative to both the source Hindi and the chunk's own worked example three sentences later. A whole rule-bearing sentence (governing whether weekday-entry falls before/after sunrise) was present in `cleaned_devanagari_text` but dropped from `content_en`. | Sign corrected to match the source and the internally-consistent worked example. Missing sentence restored, rendered as literally as the compressed Hindi allows, flagged `[?]` since independent re-derivation of that specific terse clause wasn't possible this pass. |
| `pg0154_c01` | `महाडल` (Mahāḍala — a doṣa this same text defines at `pg0133_c01`, verse 25) was silently rewritten as `महाशूल` (a different technical term) in both `cleaned_devanagari_text` and `content_en`, unflagged. | Reverted to the legible, correct, unambiguous source reading in both fields; the parallel guess elsewhere in the same chunk corrected to match. |

All 3 corrections applied via the same apply script (`--input
data/corrections/verifier_corrections_20260803.json`), dry-run validated first, then applied for
real with the same batched/verified/re-embedded mechanics as the main run. Confirmed in the live
DB post-fix.

## §7 — Re-embedding confirmation

All 88 translated chunks (85 original + 3 corrected, since the 3 corrections re-embedded their
already-embedded rows a second time with the corrected `content_en`) were re-embedded via the
production Vertex AI `text-multilingual-embedding-002` pipeline (768-dim), the same model/endpoint
as `platform/src/lib/embeddings/embedText.ts`. Confirmed: `embedding IS NOT NULL` for all 274
rows post-pass; the apply script's `applyOne()` computes `content_sha256` and the embedding from
the *same* new `content_en` in the same transaction, so the two can never drift from each other
for a row this pass touched.

## §8 — Resume state (186 chunks remain out of scope)

This session translated only priority-topic chunks. 186 chunks covering general muhūrta material
(gṛhārambha details outside the priority topics, general vivāha/yātrā procedural verses not
matching a priority topic, etc.) remain fully untouched: `content_en = content_sa`,
`translation_status IS NULL`, `ocr_cleanup_pass_version IS NULL`. This is the correct honest state
per brief §4 ("NULL everywhere the pass didn't touch") — not a partial/broken state, a legitimate
stopping point.

**To resume**: a future session can re-run the same 10-shard classify+translate pipeline against
the 186 untouched `chunk_id`s (recoverable via
`SELECT chunk_id FROM classical_text_chunks WHERE text_id='muhurta_chintamani' AND
translation_status IS NULL`), or narrow scope further if only specific chapters are wanted next.
The apply script and its idempotency check (`alreadyApplied()`) make this safe to re-run without
re-touching the 88 chunks already done.

## §9 — Artifacts landed (this PR)

- `platform/supabase/migrations/536_muhurta_chintamani_translation_provenance.sql` (already
  merged separately via PR #1041, referenced here for completeness)
- `platform/scripts/corpus/apply_muhurta_chintamani_translations.ts`
- `platform/scripts/corpus/data/muhurta_chintamani_translations.json` (final, corrected)
- `platform/scripts/corpus/data/shard_*.json` (10 files — per-shard intermediate translator output)
- `platform/scripts/corpus/data/corrections/verifier_corrections_20260803.json`
- `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/backups/muhurta_chintamani_pretranslation_backup_20260803.json`
- This report

Per brief §6/§5.4: this task does **not** edit `SHAD_DARSHANA_STATE.md` or any
`shad-darshana/*` branch. The campaign's own Conductor picks this report up in its
reconciliation sweep.

---
*End of report v1.0.*
