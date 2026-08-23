---
lane: F-04
stream: S5 MŪLA
campaign: PARIŚEṢA
stage: S (SPEC)
status: DRAFT — pending VERIFIER review (Stage R)
severity: TIER2-HONESTY
---

# F-04 SPEC — `ref_nakshatra_get`: new `query_nakshatra_catalog` capability + repoint

## 1. Root-cause statement

`register_p1_reference.ts`'s `ref_nakshatra_get` handler unconditionally calls
`query_classical_texts` and serves a `fallback_reason` asserting "No structured
bg_nakshatra catalog table exists" — false: `reference_nakshatra` (28 rows, canonical per
migration 302, live L1 authority already consumed by `ga_nakshatra.py` and others) is real and
populated, but **unlike F-22, no existing registered capability queries it yet** — this fix
needs one small new capability file, not a pure repoint.

## 2. Files to change

1. **New file:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_nakshatra_catalog.ts`
   — mirror `query_dasha_systems.ts`'s structure (~60 lines): URI
   `marsys://tool/L0/query_nakshatra_catalog`, queries `reference_nakshatra` (+ join
   `reference_nakshatra_pada` for pada lords), input_schema `{ nakshatra?: string, lord?:
   string }`, returns `{ rows, count, filters, empty_reason?, disclaimer, provenance }` with
   `rows[].{nakshatra_name, vimshottari_lord, presiding_deity, nakshatra_gender, gana, varna,
   nadi, pada_lords[], body_part, symbol}`.
2. **Register it**: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts` — import
   + add to the exported capability arrays, matching `query_dasha_systems`'s registration
   pattern exactly (same file, adjacent lines).
3. **New test file**: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_nakshatra_catalog.test.ts`
   — mirrors `query_dasha_systems.test.ts`'s structure; assert correct output for Purva
   Bhadrapada (jupiter/Aja Ekapada/Male/Manushya/Brahmin/Adi/left side/front of a funeral cot,
   per CL02_CENSUS.md's DB verification).
4. **`platform-mcp/src/tools/register_p1_reference.ts`** (lines 412-449, handler ~435-444):
   same three changes as F-22 §2.1-2.3 — repoint to the new `query_nakshatra_catalog` URI,
   reshape the response mapping, invert `structured_filter_applied`/`fallback_reason` on
   success, delete the false comment/string at line 442.

## 3. Exit test

New file: `platform-mcp/src/tools/__tests__/register_p1_reference.f04_nakshatra_repoint.test.ts`
- `ref_nakshatra_get({nakshatra:'purva_bhadrapada', limit:5})` — assert
  `structured_filter_applied: true` and the response contains `vimshottari_lord: 'jupiter'`,
  `presiding_deity: 'Aja Ekapada'`, `nakshatra_gender: 'Male'`, `gana: 'Manushya'`. Today: none
  of these fields exist, `structured_filter_applied: false` — FAILS on current code.
- Assert no classical-text OCR-garbled fragments (the two junk rows Stage D §1 found) appear in
  the structured-path response.
- Regression: unrecognized `nakshatra` value degrades gracefully to classical-text search with a
  genuine `fallback_reason`.

## 4. Sibling sites covered (from Stage D §4)

| Sibling | Disposition |
|---|---|
| F-22 (`ref_dasha_systems_get`) | Kept as its own spec (`lanes/F-22/SPEC.md`) — same root cause and same author-comment lineage (F-22's handler comment literally says the nakshatra bug is "same class of bug as ref_dasha_systems_get above"), but F-22 is a pure repoint against an already-registered capability while F-04 needs a new capability file first — different build effort, split intentionally per lane discipline. Both specs cross-reference each other; a builder doing one should do both in the same PR for efficiency, but they remain two lanes/two exit tests. |
| `ref_dignity_reference_get` | Not a sibling (Stage D §4) — already correct, used as the reference pattern both F-04 and F-22 are being fixed to match. |

## 5. Recurrence guard

Same recommendation as F-22 §5 — a lint/CI check for `fallback_reason` strings asserting table
absence without a real `information_schema` check behind them. Not duplicating the
recommendation text; see F-22/SPEC.md §5, filed once for both.

## 6. Dependencies and rollback note

- No dependency on other lanes.
- Rollback: one new file + one registration + one handler change — additive, no migration, no
  orchestrator touch. `git revert` sufficient; the new capability file can also simply be left
  unregistered if reverted (zero blast radius).
- No rebuild dependency per ND-PARISESA-1 — `reference_nakshatra` is a pre-existing, already-
  populated global L0 reference table (confirmed 28 rows, live). Pure serving-layer addition +
  repoint, verifiable live immediately after merge/deploy.

## 7. Sub-claim coverage (Stage D §2)

| Sub-claim | Addressed by |
|---|---|
| (a) description promises structured fields | §2.1 new capability returns exactly these fields |
| (b) always routes through classical-text search | §2.4 repoint |
| (c) fallback_reason/comment actively assert absence (§N.7 violation) | §2.4 inverted on success, false string deleted |
| (d) structured table is real, populated, already an L1 authority elsewhere | §2.1 now queried |
