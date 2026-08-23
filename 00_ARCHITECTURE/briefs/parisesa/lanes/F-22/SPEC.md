---
lane: F-22
stream: S5 MŪLA
campaign: PARIŚEṢA
stage: S (SPEC)
status: DRAFT — pending VERIFIER review (Stage R)
severity: TIER2-HONESTY
---

# F-22 SPEC — `ref_dasha_systems_get` repoint to `query_dasha_systems` (real structured table)

## 1. Root-cause statement

`register_p1_reference.ts`'s `ref_dasha_systems_get` handler unconditionally calls
`query_classical_texts` and serves a `fallback_reason` actively asserting "no structured
bg_dasha_systems catalog table exists (confirmed absent from the migration set)" — false: the
real table is `brahma_dasha_systems` (20 rows, live, correctly populated), and a complete,
tested, already-registered capability (`query_dasha_systems.ts`) already queries it but is never
called by this handler.

## 2. Files to change

**`platform-mcp/src/tools/register_p1_reference.ts`** (lines 369-408, handler ~383-406):
1. Replace the unconditional `callRegistryCapability('marsys://tool/L0/query_classical_texts', ...)`
   call with `callRegistryCapability('marsys://tool/L0/query_dasha_systems', { canonical_id: system, school }, principal)`.
   Map the handler's existing `system` param (free-text name) to `canonical_id` — confirmed
   exact-match-compatible for the ~19 real slugs `l0_dasha_systems.py` seeds
   (`vimshottari`, `yogini`, `ashtottari`, `kalachakra`, `shodashottari`, `chara_jaimini`, etc.).
2. **Response reshape, not a drop-in swap** (Stage D §5 correction): `query_dasha_systems`
   returns `{ rows, count, filters, empty_reason?, disclaimer, provenance }` with
   `rows[].{canonical_id,name_sa,name_en,total_cycle_years,base_unit,sequence_jsonb,
   computation_method,computation_pseudocode,conditions_for_use,school,classical_citations}` —
   shaped differently from `query_classical_texts`'s citation-object rows. Rewrite the handler's
   `dataObj` construction to map the new shape into the response fields the tool description
   promises (total years, planet sequence, activation criteria, source authority).
3. **Invert the honesty fields, don't just delete them**: on a successful structured match, set
   `structured_filter_applied: true` and remove the false `fallback_reason`. Only emit a
   `fallback_reason` (real, not fabricated) if `query_dasha_systems` returns zero rows for the
   given `system` — and only THEN degrade to the classical-text search as a genuine second step,
   mirroring `ref_dignity_reference_get`'s already-correct pattern (Stage D §4).
4. Delete the false inline comment at lines 385-386 ("no structured bg_dasha_systems catalog
   table exists... confirmed absent from the migration set").
5. **`reference_dasha_systems` is explicitly NOT touched or referenced** — confirmed (Stage D
   §3) to be a thin FK-pointer sibling table, not a duplicate; `brahma_dasha_systems` is the
   sole correct target.

## 3. Exit test

New file: `platform-mcp/src/tools/__tests__/register_p1_reference.f22_dasha_repoint.test.ts`
- `ref_dasha_systems_get({system:'vimshottari', limit:10})` — assert `structured_filter_applied:
  true`, assert response contains `total_cycle_years: 120` and a 9-planet `sequence_jsonb`
  matching Ketu 7 + Venus 20 + Sun 6 + Moon 10 + Mars 7 + Rahu 18 + Jupiter 16 + Saturn 19 +
  Mercury 17. Today: `structured_filter_applied: false`, no such fields present — FAILS on
  current code.
- Assert `fallback_reason` is absent (or null) on a successful structured match.
- Regression: call with an unrecognized `system` value, assert graceful degrade to
  classical-text search with a genuine (non-fabricated) `fallback_reason`, not a crash.

## 4. Sibling sites covered (from Stage D §4)

| Sibling | Disposition |
|---|---|
| F-04 (`ref_nakshatra_get`) | NOT covered by this spec — same defect class, adjacent in the same file, but requires a NEW capability file first (no `query_nakshatra_catalog` equivalent exists yet, per F-04's own Stage D §5). Covered in F-04's own spec instead of folded in here, since F-22 is a pure repoint and F-04 is repoint-plus-new-capability — different effort shape, kept as separate specs per lane discipline even though root cause is identical. |
| `ref_dignity_reference_get` | Not a sibling — already correctly implements the structured-first pattern this spec is copying. No action. |

## 5. Recurrence guard

New lint/CI check (or extend `fact-category-pin-lint`'s sibling tooling): flag any
`fallback_reason` string containing "no structured... table exists" or "confirmed absent" that
isn't backed by an actual `information_schema` check at build/test time — this is the general
form of the §N.7 item 4 violation both F-04 and F-22 share. Filed as a recommendation; the exact
CI mechanism is a call for whoever owns governance tooling (`platform/scripts/governance/**`,
S6's lease), not built in this spec.

## 6. Dependencies and rollback note

- No dependency on other lanes — `query_dasha_systems.ts` is already registered and tested
  independently of this fix.
- Rollback: single-file change to `register_p1_reference.ts`, no data/migration/orchestrator
  touch. `git revert` sufficient.
- No rebuild dependency per ND-PARISESA-1 — `brahma_dasha_systems` is a pre-existing, already-
  populated global L0 reference table; this is a pure serving-layer repoint, verifiable live
  immediately after merge/deploy.

## 7. Sub-claim coverage (Stage D §2)

| Sub-claim | Addressed by |
|---|---|
| (a) description promises structured fields | §2.2 reshape maps real fields into the response |
| (b) always routes through classical-text search | §2.1 repoint |
| (c) fallback_reason actively lies | §2.3/§2.4 — inverted on success, false comment deleted |
| (d) working replacement capability exists unused | §2.1 — now called |
