---
artifact: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF (commissioned corpus-curation task)
canonical_id: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF
version: 1.1
status: COMMISSIONED — by the native, 2026-08-02 (recorded in
  SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS item 3). NOT a
  ṢAḌ-DARŚANA night-run lane: this is corpus curation (generative translation), which the
  campaign's deterministic-first rail keeps out of autonomous builder hands. Runs as its own
  supervised session; the campaign only CONSUMES its output.
created: 2026-08-02
revised: 2026-08-02 (v1.1 — the first task session HALTED correctly rather than invent a
  provenance scheme, and its findings falsified two of v1.0's assumptions; see changelog)
changelog:
  - "1.1 (2026-08-02): PROVENANCE SCHEME NOW EXPLICIT — v1.0 instructed the session to
    match 'the corpus schema's existing convention'; the session's live census proved NO
    such convention exists (the six ocr_*/cleaned_* columns are 100% null across all
    9,600+ rows of all 15 texts — added speculatively, never used), and v1.0's mechanics
    referenced translation_status/translation_provenance columns that do not exist in the
    schema. Both corrected: §4 now DEFINES the first-ever convention for the dormant
    columns and §3.1 specifies the tiny additive migration for the two missing ones. Also
    corrected: the translator field for muhurta_chintamani is NOT empty — it holds the
    source-edition citation ('Muhurta Chintamani — Mahidhara Sharma bhasha tika, Khemraj
    Shrikrishnadas Press'), consistent with every text's use of that field; it is READ-ONLY.
    Credit: the halting session's refusal to guess is exactly the §N.7 discipline this
    repo exists to enforce."
  - "1.0 (2026-08-02): initial commissioning."
author: Fable (native-decisions session; v1.1 same)
blocking: >
  Four ṢAḌ-DARŚANA deliverables, all currently PARKED-HONEST on this exact gap: (1) item
  41's Agnivāsa corpus grounding; (2) paddhati convention (B)
  `agnivasa_muhurta_chintamani_arithmetic` (declared_not_computed, ADJUDICATION-8 part 3);
  (3) parihāra-graph depth beyond the currently-extractable rules; (4) possible Kota-Chakra
  corroboration (ADJUDICATION docket note). Each re-opens when this lands.
---

# Muhūrta-Cintāmaṇi Translation — Task Brief

## §1 — The gap, precisely

`muhurta_chintamani` (Rāma Daivajña — THE classical muhūrta authority) is already ingested
in `classical_text_chunks`: **274 chunks**, `content_sa` populated, `content_en`
**byte-identical to `content_sa`** — raw, OCR-noisy, untranslated Devanāgarī plus Hindi
ṭīkā. It is unretrievable by English search, unciteable by rules extraction, and invisible
to every corpus census. All 274 chunks carry embeddings built over the raw Devanāgarī — so
**re-embedding after translation is mandatory**, or English vector retrieval stays broken
while looking done. Zero acquisition cost — only the translation layer is missing.

## §2 — Verified schema facts (live-checked 2026-08-02; the session re-verifies cheaply)

- Table `classical_text_chunks` · `text_id='muhurta_chintamani'` · 274 rows, all with
  `content_en = content_sa`.
- **`translator` is NOT empty and is NOT ours to write**: it holds the source-edition
  citation (`Muhurta Chintamani — Mahidhara Sharma bhasha tika, Khemraj Shrikrishnadas
  Press`), the same convention every other text uses. Overwriting it destroys real
  provenance. READ-ONLY for this task.
- The six columns `cleaned_devanagari_text`, `cleaned_translation_text`,
  `ocr_confidence_score`, `low_confidence_flag`, `ocr_review_note`,
  `ocr_cleanup_pass_version` exist but are **100% unused across the entire table (all 15
  texts)** — there is no prior convention to mirror. **§4 DEFINES their first convention**;
  the session follows §4 verbatim and invents nothing.
- `translation_status` and `translation_provenance` **do not exist** — §3.1 specifies the
  additive migration that creates them.
- `content_sha256` hashes the ENGLISH content: `sha256(content_en or content)` — verified
  at `platform/python-sidecar/brahmagyan/l0_text_chunker.py` (`_sha256(content_en or
  content)`, ~lines 228/264). When `content_en` changes, recompute accordingly.
- Convention exemplar for translation STYLE (not provenance): `sarvartha_chintamani`
  (342 chunks, fully translated) — match its `content_en` register and citation habits.

## §3 — Scope of work

1. **Migration first (the session's first PR, before any row write):** one additive,
   nullable, zero-backfill migration on `classical_text_chunks` — next free number in
   `platform/supabase/migrations/` (≥534 as of this writing; **re-verify the live max
   immediately before use** — the standing collision discipline), migration-guard reviewed:
   - `translation_status TEXT NULL` with
     `CHECK (translation_status IN ('machine_translated_supervised','deferred') OR
     translation_status IS NULL)`
   - `translation_provenance TEXT NULL`
   Nullable + no backfill = zero effect on the other 15 texts. This is the clean answer;
   semantically overloading the OCR fields to carry translation status was considered and
   rejected.
2. **OCR cleanup pass** per chunk: repaired Devanāgarī goes to `cleaned_devanagari_text` —
   **`content_sa` is NEVER modified, ever**. Genuinely ambiguous readings are marked `[?]`
   inline in the cleaned text — flagged, never guessed.
3. **Translation pass** per chunk into **`content_en`** (the served field — this is what
   unblocks the four deliverables): verse-faithful English; technical terms in IAST with a
   gloss on first use per chunk; the Hindi ṭīkā translated as clearly-marked commentary
   (`[ṭīkā] …`), never blended into the mūla verse's rendering. `content_summary` is OUT of
   scope — untouched this pass.
4. **Priority order within the 274:** sections covering (a) Agnivāsa reckoning, (b)
   doṣa-parihāra, (c) vara×nakṣatra×tithi combination-yogas, (d) any Kota-Chakra material —
   COMPLETELY FIRST, so the four blocked deliverables re-open even if the session ends
   before all 274. The rest of the text follows.

## §4 — THE PROVENANCE SCHEME (explicit; defined here for the first time; nothing is left
to inference)

For every chunk the pass touches, set ALL of the following atomically with the content
write:

| Field | Value | Notes |
|---|---|---|
| `content_en` | the translation | served field; deferred chunks keep it EXACTLY as-is (still `= content_sa`) so nothing half-translated ever serves |
| `cleaned_devanagari_text` | the OCR-cleaned source | first-ever use of this column; this brief IS its convention now |
| `cleaned_translation_text` | NULL (unused) | reserved; do not write — one translation field (`content_en`) keeps serving unambiguous |
| `ocr_cleanup_pass_version` | `'mc_ocr_translation_v1_2026-08'` | the machine-readable pass marker; format `<task>_v<N>_<YYYY-MM>`; identical string on every row this pass touches (translated AND deferred) |
| `translation_status` | `'machine_translated_supervised'` or `'deferred'` | new column (§3.1); NULL everywhere the pass didn't touch |
| `translation_provenance` | `'machine_translation_supervised_2026-08; commissioned per SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS; source edition per translator field'` | new column (§3.1); the `translator` field itself is READ-ONLY |
| `low_confidence_flag` | TRUE iff the cleaned text contains any `[?]` | |
| `ocr_review_note` | ambiguity locations for flagged rows; for deferred rows, reason prefixed `'deferred: '` | |
| `ocr_confidence_score` | 0–1 per a rubric the session states ONCE in its report (e.g. 1.0 clean, stated deductions per ambiguity) and applies uniformly | |
| `content_sha256` | `sha256(new content_en)` | per the verified ingestion convention (§2); unchanged for deferred rows |
| `embedding` | regenerated from the new `content_en` via the existing embedding pipeline | verify non-null AND changed; unchanged for deferred rows |
| `translator`, `content_sa`, `source_citation`, `content_summary`, `topics` | **READ-ONLY** | |

## §5 — Mechanics

1. **BACKUP BEFORE ANY WRITE:** snapshot all 274 rows' current `content_en`,
   `content_sha256`, and embedding presence to a timestamped backup (table or committed
   fixture) — trivially reversible or the pass doesn't start.
2. Writes land via a reviewed, idempotent, batched script (mirroring the
   `bootstrap_classical_texts_*.ts` house style — never ad-hoc UPDATEs), keyed on
   `(text_id, chunk_id)`, with dry-run mode, per-batch row-count verification, and
   checkpointed progress (stalls resume, never restart).
3. **Acceptance:** an independent verifier — not the translator — re-reads ≥10% of
   translated chunks randomly PLUS 100% of the four priority sections against the
   Devanāgarī for fidelity; verdict verbatim in the report.
4. **Close-out:** `MUHURTA_CHINTAMANI_TRANSLATION_REPORT_v1_0.md` (this directory) —
   translated/deferred/remaining counts, priority-section status, verifier verdict,
   re-embedding confirmation, confidence rubric, backup location, resume state — landed
   with the script via PR to `main`. The task NEVER edits `SHAD_DARSHANA_STATE.md`; the
   campaign's Conductor picks the report up in its reconciliation sweep.

## §6 — What this task must NOT do

No rule-table extraction, no convention adjudication, no schema changes beyond §3.1's two
columns, no writes to any field marked READ-ONLY in §4, no touching the campaign ledger or
any `shad-darshana/*` branch. Extraction from the newly-readable text is the campaign's own
verified work (item 41's lanes, ADJUDICATION-8's convention (B)), under its own
verification, in its own PRs. Keeping the two separate keeps the provenance chain clean:
translation cites the chunk; extraction cites the translation. Honest-deferred beats
fabricated-fluent, always.
