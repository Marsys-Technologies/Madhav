# F-22 Diagnosis — ref_dasha_systems_get dead-backend / false-absence claim

Campaign: PARIŚEṢA · Stream S5 MŪLA · Lane CL-02 (dead-backend class)
Status: **CONFIRMED LIVE** (not fixed) — Tier2-Honesty violation stands, and is worse than
originally scoped: the fallback_reason is not just a stale comment, it is an actively false
claim about the schema that contradicts a table the same author's own writer populated.

## 1. Live reproduction

Called `mcp__marsys-jis-direct__ref_dasha_systems_get({system:'vimshottari', limit:10})`
2026-08-16 against the live MCP server. Raw JSON saved to `lanes/F-22/repro_raw.json`.

Observed (today, live):
- `structured_filter_applied: false`
- `fallback_reason: "No structured bg_dasha_systems catalog table exists — this is a classical-text hybrid search using the system/keyword filter as the search query, not a WHERE-clause match."`
- `content.query_used: "vimshottari dasha system"` (free-text hybrid search string)
- 10 citations returned; 4 of the 10 sampled are **Muhurta Chintamani wedding-timing verses**
  (ekārgala/upagraha/pāta/lattā doṣa apavāda rules, vāra-nakṣatra sarvārtha-siddhi tables,
  Dagdha/Viṣa/Hutāśana yoga-by-tithi tables, graha-śānti bathing remedy) — topically unrelated
  to dasha-system structure. None of the 10 rows contain the Vimshottari total-years (120),
  planet sequence, or per-planet period lengths.
- No `bg_dasha_systems` (nonexistent id, per the finding's own claimed table name) or
  `brahma_dasha_systems` (the real table) row appears anywhere in the response.

**Confirmed: reproduces exactly as F-22 describes. Not already fixed.**

## 2. Claim decomposition

a. **Description promises structured fields** — TRUE. Tool description (register_p1_reference.ts:372-376):
   "Returns system name, total years, planet sequence with period lengths, activation criteria,
   and source authority." None of these fields are present in the actual response shape
   (`content.content.rows[]` are classical-text citation objects: `citation_ref`, `chunk_id`,
   `verse_text_en`, `vector_score`, etc. — no `total_cycle_years`, no `sequence_jsonb`).

b. **Always routes through classical-text search** — TRUE. `system`/`keyword`/nothing all funnel
   into the same `callRegistryCapability('marsys://tool/L0/query_classical_texts', ...)` call
   at register_p1_reference.ts:395. There is no code path in this handler that ever queries a
   structured table.

c. **fallback_reason actively lies** — TRUE, and stronger/more specific than F-04's version.
   The exact string (register_p1_reference.ts:401):
   > "No structured bg_dasha_systems catalog table exists — this is a classical-text hybrid
   > search using the system/keyword filter as the search query, not a WHERE-clause match."
   The inline code comment above it (register_p1_reference.ts:385-386) makes the same claim
   even more assertively: *"no structured bg_dasha_systems catalog table exists (confirmed
   absent from the migration set)"*. This is false on two counts: (1) the literal table name
   `bg_dasha_systems` was never the real name — the real structured table is
   `brahma_dasha_systems` (see §3), so the claim conflates a name that never existed with "no
   structured table exists" and (2) `brahma_dasha_systems` is not merely present in the
   migration set, it is **live in production with 20 rows** (confirmed by CL02_CENSUS.md's DB
   query), correctly populated (Ketu 7 + Venus 20 + Sun 6 + Moon 10 + Mars 7 + Rahu 18 +
   Jupiter 16 + Saturn 19 + Mercury 17 = 120 years — exact match to classical Vimshottari).
   This is a §N.7 Narration Fidelity violation (item 4/6: an "honest gap" flag with no real
   detector behind it — worse here, it's a comment/fallback_reason asserting a specific false
   fact rather than just an unimplemented check).

d. **A working, tested, already-registered replacement exists unused** — TRUE, see §3.

## 3. Mechanism, file:line, and the reference_dasha_systems discrepancy

**Current dead-backend code**: `platform-mcp/src/tools/register_p1_reference.ts:369-408`
(handler body ~383-406). Key lines:
- 385-386: false inline comment ("no structured bg_dasha_systems catalog table exists
  (confirmed absent from the migration set)")
- 394-397: builds `kw` string and calls `query_classical_texts` — the only data path
- 401: the false `fallback_reason` string quoted verbatim in §2c

**Replacement capability**: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts`
- URI: `marsys://tool/L0/query_dasha_systems`
- Queries `brahma_dasha_systems` directly (file's own SQL, line ~64: `FROM brahma_dasha_systems`)
- Selects exactly the fields the ref_dasha_systems_get description promises: `canonical_id,
  name_sa, name_en, total_cycle_years, base_unit, sequence_jsonb, computation_method,
  computation_pseudocode, conditions_for_use, school, classical_citations`
- **Registered**: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts:60` (import),
  and included in the exported capability arrays at lines 125 and 192. Genuinely wired into the
  registry — this is not dead code on the writer side, only unused by ref_dasha_systems_get.
- **Test file present**: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_dasha_systems.test.ts`
  (1980 bytes, exists).
- Own file header self-documents it was purpose-built to serve `brahma_dasha_systems`'s
  18-seeded-row set (W2b dark-set wiring, Batch 2) and was never wired to any MCP tool.

**`reference_dasha_systems` resolved — it is NOT a competing/duplicate candidate table.**
Traced via the writer chain:
- `platform/python-sidecar/brahmagyan/l0_dasha_systems.py` (the actual seeder, lines 634-738)
  writes THREE things per dasha system in one pass: (1) `brahma_dasha_systems` — the full
  catalog row, inserted FIRST (this is the FK target and the "real" data); (2)
  `brahma_ontology` — a `dasha_system`-class ontology entry; (3) `reference_dasha_systems` — an
  explicitly-labeled **"thin pointer row (FK → brahma_dasha_systems.canonical_id)"**
  (line 8 of that file's own docstring).
- Migration 178 (`178_l0_phase_alpha_reference_tables.sql:94`) creates `reference_dasha_systems`
  as one of 15 standalone `reference_*` tables that migration 179's own comment describes as
  following the project pattern "ontology resolves names, reference holds properties" — i.e.
  `reference_dasha_systems` is a name/pointer index row, not the properties table.
  `brahma_dasha_systems` holds the actual properties (`total_cycle_years`, `sequence_jsonb`,
  `computation_pseudocode`, etc.) that `reference_dasha_systems` does not carry.
- `bg_dasha_systems.py` orchestrator writer (`platform/python-sidecar/pipeline/orchestrator/writers/bg_dasha_systems.py`)
  confirms the same story: `rows_inserted` for the asset is defined as the `brahma_dasha_systems`
  catalog count specifically, calling it "the asset's primary table."
- `query_dasha_systems.ts` independently corroborates this by querying `brahma_dasha_systems`
  directly, never `reference_dasha_systems`.

**Verdict: `brahma_dasha_systems` is the correct canonical target — confirmed three independent
ways (writer docstring, migration-179 design-pattern comment, and query_dasha_systems.ts's own
SQL). `reference_dasha_systems` is a thin FK-pointer sibling table, not a duplicate or legacy
table, and is not the fix target.** The eventual spec should name `brahma_dasha_systems`
explicitly (matching CL02_CENSUS.md's row-count finding) and should NOT reference
`reference_dasha_systems` as an alternative.

## 4. Sibling census — F-04 proximity

Same file, same pattern, same author comment lineage. `ref_dasha_systems_get`
(register_p1_reference.ts:369-408) sits immediately before `ref_nakshatra_get`
(register_p1_reference.ts:410-441+), and the nakshatra handler's own inline comment at
line 427-428 says explicitly: *"CR-42/R-19/R-20 fix (D-1.6 S-1): same class of bug as
ref_dasha_systems_get above — no structured bg_nakshatra catalog table exists..."* — i.e. the
original author already flagged these as one defect class, propagated by copy-paste from the
dasha handler to the nakshatra handler. `ref_dignity_reference_get` (lines 297-367, same file)
is a related but *not* identical case — it DOES have a working structured-table path
(`bg_dignity_reference`) and only degrades to classical-text search when no row matches, so it
is the "done right" reference pattern the other two should be fixed to resemble.

F-22 and F-04 (per CL02_CENSUS.md, F-04 is `reference_nakshatra`) are adjacent instances of the
identical mechanism (false/stale "no structured table" comment + a real, unused/underused
structured table) and should share one fix PR pattern: repoint `query_text` hybrid calls to the
real structured capability, correct the fallback_reason/comment to stop asserting table absence,
and set `structured_filter_applied: true` on the structured path. Recommend the eventual spec
cover both in one lane given the shared root cause, unless F-04's own diagnosis finds a shape
mismatch that forces a different fix pattern there.

## 5. Blast radius — is it really "one URI string"?

**No — not literally one string.** Three real deltas exist between "swap the URI" and a working
fix:

1. **Input schema mismatch.** `ref_dasha_systems_get`'s public params are `system` (free-text
   name match) and `keyword` (free-text search). `query_dasha_systems`'s input_schema is
   `canonical_id` (exact match) and `school`. There is no `keyword`/free-text param on the
   replacement at all — it is a pure structured filter, no fuzzy search. Mapping `system` →
   `canonical_id` works for exact-slug values (`vimshottari`, `yogini`, `ashtottari`,
   `kalachakra`, `shodashottari`, `chara_jaimini`, plus ~13 more slugs confirmed in
   `l0_dasha_systems.py`'s `DASHA_SYSTEMS` list, e.g. `sthira_dasha`, `narayana`,
   `tara_dasha`) since callers already pass exactly these lowercase system names in practice —
   but any caller relying on `keyword` free-text matching loses that capability outright unless
   the handler also falls through to the classical-text path when `canonical_id` fails to match
   (mirroring the `ref_dignity_reference_get` pattern in §4).
2. **Response shape mismatch.** `query_dasha_systems`'s handler returns
   `{ rows, count, filters, empty_reason?, disclaimer, provenance }` with `rows[]` containing
   `canonical_id/name_sa/name_en/total_cycle_years/base_unit/sequence_jsonb/computation_method/
   computation_pseudocode/conditions_for_use/school/classical_citations`. The current handler's
   `dataObj` spread (register_p1_reference.ts:398-402) expects `query_classical_texts`'s shape
   (`content.search_mode/query_used/citations/rows/total`, where `rows` are citation objects).
   These do not merge cleanly — the handler needs real branching/reshaping logic, not a
   drop-in replacement of the `uri` argument to `callRegistryCapability`.
3. **`structured_filter_applied` and `fallback_reason` must invert on success**, not just get
   deleted — the honest-envelope contract (§N.6/§N.7) requires `structured_filter_applied: true`
   plus removal of the false fallback_reason when the structured path is used, and a genuine
   (not fabricated) fallback_reason only if `query_dasha_systems` returns zero rows and the
   handler degrades to classical-text search as a second step.

**Conclusion: the underlying finding's "one-URI-string change" characterization is directionally
right (no new backend development, no new DB work, no migration) but operationally understates
the handler work — it's a small, self-contained TypeScript rewrite of one `server.tool(...)`
block (~20-30 lines), not a one-line edit. Flag this precisely for the S-stage spec so the
estimate isn't wrong.**
