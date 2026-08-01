---
artifact: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF (commissioned corpus-curation task)
canonical_id: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF
version: 1.0
status: COMMISSIONED — by the native, 2026-08-02 (recorded in
  SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS item 3). NOT a
  ṢAḌ-DARŚANA night-run lane: this is corpus curation (generative translation), which the
  campaign's deterministic-first rail keeps out of autonomous builder hands. Runs as its own
  supervised session; the campaign only CONSUMES its output.
created: 2026-08-02
author: Fable (native-decisions session)
blocking: >
  Four ṢAḌ-DARŚANA deliverables, all currently PARKED-HONEST on this exact gap: (1) item
  41's Agnivāsa corpus grounding; (2) paddhati convention (B)
  `agnivasa_muhurta_chintamani_arithmetic` (declared_not_computed, ADJUDICATION-8 part 3);
  (3) parihāra-graph depth beyond the currently-extractable rules; (4) possible Kota-Chakra
  corroboration (ADJUDICATION docket note). Each re-opens when this lands.
---

# Muhūrta-Cintāmaṇi Translation — Task Brief

## The gap, precisely

`muhurta_chintamani` (Rāma Daivajña — THE classical muhūrta authority) is already ingested:
**274 chunks**, with `content_sa` populated. But `content_en` is **byte-identical to
`content_sa`** — raw, OCR-noisy, untranslated Devanāgarī plus Hindi ṭīkā. It is therefore
unretrievable by English vector/keyword search, unciteable by rules extraction, and invisible
to every corpus census. Zero acquisition cost — the text is in the tree; only the
translation layer is missing.

## Scope of work

1. **OCR cleanup pass** on `content_sa` per chunk: repair obvious OCR corruption in the
   Devanāgarī (conservatively — flag, don't guess, where the reading is genuinely ambiguous;
   an uncertain source reading is marked `[?]` inline, never silently normalized).
2. **Translation pass** into `content_en` per chunk: verse-faithful English, technical terms
   kept in IAST with gloss on first use per chunk (tithi, vāra, agnivāsa, pariḥāra, etc.).
   The Hindi ṭīkā, where present, is translated as clearly-marked commentary
   (`[ṭīkā] …`), never blended into the mūla verse's rendering.
3. **Provenance discipline (non-negotiable):** `content_sa` is NEVER modified in place —
   cleanup output goes to a separate field/version if the schema supports it, else the
   cleanup notes ride the translation. Every translated chunk carries
   `translation_provenance = 'machine_translation_supervised_2026-08'` (exact tag to match
   the corpus schema's existing convention — inspect before writing). A chunk the
   translator cannot render faithfully is marked `translation_status='deferred'` with
   reason — honest-empty beats fabricated-fluent, the same rail as everywhere else.
4. **Priority order within the 274:** chapters/sections covering (a) Agnivāsa reckoning,
   (b) doṣa-parihāra, (c) vara×nakṣatra×tithi combination-yogas, (d) any Kota-Chakra
   material — i.e., the four blocked deliverables' sections FIRST, so the campaign can
   re-open them before the full text completes. The rest of the text follows.
5. **Acceptance:** an independent verification pass re-reads a sample (≥10% of chunks,
   including 100% of the four priority sections) against the Devanāgarī for fidelity —
   the same two-pass discipline the campaign uses everywhere. Then the four PARKED-HONEST
   deliverables are notified (ledger note) to re-open.

## What this task must NOT do

No rule-table extraction, no convention adjudication, no schema changes beyond the
translation fields — translation only. Extraction from the newly-readable text is the
campaign's own work (item 41's lanes, ADJUDICATION-8's convention (B)), under its own
verification, in its own PRs. Keeping the two separate keeps the provenance chain clean:
translation cites the chunk; extraction cites the translation.
