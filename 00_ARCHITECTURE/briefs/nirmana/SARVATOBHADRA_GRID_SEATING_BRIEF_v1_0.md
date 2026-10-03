---
artifact: SARVATOBHADRA_GRID_SEATING_BRIEF
canonical_id: SARVATOBHADRA_GRID_SEATING_BRIEF
version: "1.0"
status: READY_PENDING_SOURCE
date: 2026-09-25
decision_owner: Native
authority: "NATIVE_DECISIONS_2026-09-25_v1_0.md decision 12 (the school is named: muhurta_chintamani) + ADJUDICATION-11 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md, which registered the table deliberately empty and forbade transcribing a grid from memory)"
role: "Execution-ready brief for seating the Sarvatobhadra Chakra grid. Everything except the source passage is already in place; this brief exists so that when the passage arrives the work is one bounded pass and not a re-investigation."
blocked_on: "The Muhūrta Cintāmaṇi chapter carrying the chakra. It is not held — see §1, measured."
---

# Seating the Sarvatobhadra grid — what is ready, and the one thing that is not

## 1. The blocker, measured rather than assumed

`bg_sarvatobhadra_grid` cannot be populated today, and the reason is neither tooling nor schema nor the
consumer. It is that **we do not hold the passage**:

| check | result |
|---|---|
| `classical_text_chunks` where `text_id='muhurta_chintamani'` | 274 chunks held |
| of those, containing "sarvatobhadra" (en / sa / summary) | **0** |
| of those, containing "chakra" | **0** |
| of those, containing "vedha" | 1 |
| the source file those chunks were ingested from (`platform/scripts/corpus/data/muhurta_chintamani_translations.json`) | the same 274 entries; "sarvatobhadra" **0**, "chakra" **0** |
| Jyotiṣa Sāra Saṅgraha / Praśna Mārga (the other two recorded candidates) | not in the corpus at all; Praśna Mārga not even as a `text_id` |

So the 274 chunks are a partial holding of Muhūrta Cintāmaṇi that does not include the chakra chapter,
and the file they came from does not either. Migration 529's own header records the same conclusion from
the other direction: 8 `sarvatobhadra` hits corpus-wide, all noise except one passing mention that the
chakra exists without giving its geometry.

**Therefore nothing may be written to the table yet.** ADJUDICATION-11 already refused to transcribe an
SBC grid from memory, because the 9×9 geometry genuinely varies by tradition and choosing one would be a
school-selecting interpretive act seated as an L0 base fact. Product §13 forbids invented computation and
the data plane §4.3 forbids an AI-composed verse. An empty school-keyed table is the honest output until
a real passage exists; it is not a defect to be closed by filling it in.

## 2. What is already in place — do not rebuild any of this

- **The table exists and is correct.** Migration 529 applied (ledger confirms one row for it); the table
  holds 0 rows by design. Columns: `school_tag`, `cell_index`, `cell_kind`
  (`CHECK IN ('nakshatra_position','vedha_pair')`), `cell_value`, `source_text_id`, `source_citation`,
  `table_version`, `native_confirmed` (default FALSE), with the natural key
  `UNIQUE (school_tag, cell_kind, cell_index, table_version)`.
- **The school is named.** Decision 12: `school_tag = 'muhurta_chintamani'` — the most current of the
  three recorded candidates and the only one we hold any of. That decision names *which source to
  verify first*; it does not license writing the grid before verifying it.
- **The consumer is wired and waiting.** `ka_vedha_gochara`'s writer queries this table **first**
  (`_fetch_school_tagged_vedha_pair`), falls through to `l1_sarvatobhadra_vedha` (also empty) and then to
  the disclosed algorithmic opposition approximation. Rows landing here activate the real path with
  **zero code change**.
- **Holding a school's grid is not the same as preferring it.** Per ADJUDICATION-11, grid-variant
  *selection* is a `kala_paddhati_profile` matter (`factor_family='sarvatobhadra_grid'`). Seating
  Muhūrta Cintāmaṇi's grid does not impose it on every reading; a second school can sit beside it under
  its own tag, which is what `school_tag` is for.
- **What is served meanwhile is honest.** The approximation carries `uncited_extension=true` and its
  `grid_basis` / `grid_school_tag` disclosure on every row, so no caller can mistake it for classical.

## 3. Execution, when the passage exists — one bounded pass

1. **Acquire the chapter** of Muhūrta Cintāmaṇi that carries the chakra, recording edition, translator
   and the verse range. Native supplies or authorises the edition; no web-sourced grid image substitutes
   for a text with an edition.
2. **Ingest it into the existing path**, not a new one: extend
   `platform/scripts/corpus/data/muhurta_chintamani_translations.json` and apply it with
   `platform/scripts/corpus/apply_muhurta_chintamani_translations.ts`, so the chunks arrive under the
   `text_id` that already exists with its `translator` / `tradition_school` provenance intact.
3. **Seat the grid** in one migration (numbered at max+1 across both migration directories at the time —
   1093 is the current max after decision 15):
   - 28 rows `cell_kind='nakshatra_position'`, `cell_index` = the grid cell, `cell_value` = the nakshatra
     canonical id (through the controlled vocabulary of data plane §4.1 — the ontology's `nakshatra`
     class, never a free-string label);
   - one row per `vedha_pair` the passage states, `cell_value` carrying the pair;
   - every row: `source_text_id='muhurta_chintamani'`, `source_citation` = the verse reference, not the
     chapter alone; `table_version` = the release id; `native_confirmed=false`.
4. **Leave preference alone** unless the native rules on it: seating rows is L0 holding the grid;
   `kala_paddhati_profile` decides whether a reading prefers it.

## 4. What must be true before it counts

- **D1 source correspondence** (layer template §2.7, the carriage check): each seated cell is compared
  against the cited verse and must agree. A cell whose value cannot be pointed at in its own citation is
  removed, not defaulted.
- **Row-count honesty:** 28 nakshatra positions, and exactly as many vedha pairs as the passage states —
  no pair inferred by symmetry to make the set look complete.
- **Consumer proof:** after seating, `ka_vedha_gochara` takes the DB-grid path and its output changes in
  the declared way, with `uncited_extension` no longer set for the grid term.
- **`native_confirmed` stays FALSE** until the native confirms; the column exists precisely so that
  "sourced" and "confirmed" are not the same claim.

## 5. What must not happen

Transcribing the grid from memory or from a secondary website; seating the algorithmic approximation
under a `school_tag` so the table looks populated; inferring the missing pairs; setting
`native_confirmed=true` without the native; or closing this item by deleting the requirement. Each of
those converts an honest empty table into a confident wrong one, which is the single failure mode this
whole asset was designed around.

## 6. State today

Table present, 0 rows, by design. School named. Consumer waiting. Approximation serving with its
disclosure. **Blocked on one input: the chapter.** That is the entire remaining dependency, and it is
the native's to supply or authorise.
