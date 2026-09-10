---
artifact: F-06_SPEC
lane: F-06
stream: S5 MULA
class: CL-03 (no-op params)
status: DRAFT
written: 2026-08-17
---

# F-06 — SPEC: `ref_remedies_chart_get` description honesty fix

## 1. Root-cause statement

`queryRemediesForChartCapability` exposes `chart_id` in its `input_schema` as a decorative/provenance-only field that is never bound into the SQL WHERE clause (because `brahma_remedy_corpus` is a global L0 reference table with no `chart_id` column), and the Phase-1 MCP alias `ref_remedies_chart_get` propagates a false description claiming "Chart-specific remedy suggestions" while its Zod schema does not even accept `chart_id` — together constituting an honesty violation where the tool's name and description promise per-chart scoping that the implementation structurally cannot provide.

## 2. Files to change

### File A (unblocked): `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`

**Scope: lines 1453–1468 (`queryRemediesForChartCapability.input_schema`) + capability description string**

**Change 1:** Remove the `chart_id` sub-block (lines 1454–1459) from `input_schema` entirely:
```ts
// DELETE this block:
chart_id: {
  type: 'string',
  description: 'Chart UUID (<chart_uuid>). Optional — used for provenance logging only, not for data filtering.',
  required: false,
},
```
`brahma_remedy_corpus` is a global L0 corpus with no `chart_id` column. The field is never bound into the SQL WHERE clause; its sole use is echoing back into the response/error object at lines 1518/1522. Removing it from `input_schema` closes the honesty gap — callers can no longer pass `chart_id` expecting filtering, and the capability no longer implies per-chart scope even implicitly.

**Change 2:** Update the capability description (at or near line 1440, wherever the top-level description string appears) to:
```ts
'Global remedy lookup by affliction keyword against brahma_remedy_corpus (L0 reference corpus). Not chart-scoped — add a genuine chart join as a separate feature if per-chart remedy scoping is ever wanted.'
```

**Change 3:** Remove the provenance-only `chart_id` variable at line 1487 and its echo at lines 1518/1522. The actual code uses bracket-access style: `const chart_id = args['chart_id'] as string | undefined  // optional — provenance only` — remove this variable declaration entirely and remove `chart_id` from the response/error echo objects.

### File B (BLOCKED — depends on `PAR-register_p1_aliases-RELEASE`): `platform-mcp/src/tools/register_p1_aliases.ts`

**Scope: line 1560 (alias description string)** *(reviewer verified: actual string is at line 1560, not 1565)*

Change:
```ts
'[Phase-1 alias] Chart-specific remedy suggestions (same as query_remedies_for_chart).'
```
To:
```ts
'[Phase-1 alias] Global remedy suggestions by affliction keyword (brahma_remedy_corpus — not chart-scoped; same as query_remedies_for_chart).'
```

**Why:** This is the most user-visible false claim. Callers reading the MCP tool manifest see "Chart-specific" and expect per-chart filtering. This single-string change makes the alias description truthful without touching logic.

**Dependency:** `register_p1_aliases.ts` is leased to S1 (CL-11 dualOutput sweep). Builder MUST NOT touch this file until `PAR-register_p1_aliases-RELEASE` is emitted by the conductor. File A is independently actionable now.

## 3. Exit test

**File:** `platform/src/lib/retrieval/registry/layers/__tests__/F-06.exit.test.ts`

```ts
import { readFileSync } from 'fs';
import * as path from 'path';

const D7 = path.resolve(__dirname, '../register_d7_channel.ts');
const P1 = path.resolve(__dirname, '../../../../../../../platform-mcp/src/tools/register_p1_aliases.ts');

describe('F-06: ref_remedies_chart_get honesty', () => {
  it('register_d7_channel.ts: queryRemediesForChartCapability must not expose chart_id in input_schema', () => {
    const src = readFileSync(D7, 'utf8');
    // Isolate the capability block (bounded by unique SQL LIMIT $2 near end)
    const m = src.match(/queryRemediesForChartCapability[\s\S]{0,6000}?LIMIT \$2/);
    expect(m).toBeTruthy();
    const block = m![0];
    // chart_id must not appear in this block at all
    expect(block).not.toMatch(/'chart_id'/);
    expect(block).not.toMatch(/"chart_id"/);
    expect(block).not.toMatch(/provenance only/);
  });

  it('register_p1_aliases.ts: ref_remedies_chart_get must not claim chart-specific scoping', () => {
    const src = readFileSync(P1, 'utf8');
    expect(src).not.toMatch(/Chart-specific remedy suggestions/);
  });
});
```

**Path rationale for P1:** `__dirname` resolves to `platform/src/lib/retrieval/registry/layers/__tests__/`. Seven `../` traversals reach the repo root: `__tests__` → `layers` → `registry` → `retrieval` → `lib` → `src` → `platform` → repo root. Then `platform-mcp/src/tools/register_p1_aliases.ts` is appended. The previous SPEC used only 5 `../` (landing at `platform/src/` — wrong), which was the path bug that blocked the builder.

**FAILS today:** Test 1 fails — `chart_id` with "provenance only" comment present in `queryRemediesForChartCapability` block. Test 2 fails — "Chart-specific remedy suggestions" at `register_p1_aliases.ts:1560`.

**PASSES after fix:** Test 1 passes once `chart_id` is removed from File A's `input_schema`. Test 2 passes after File B's description string is corrected (post S1 lease release).

**Run command:**
```
cd /Users/Dev/par-night/wt/F-06 && npx jest --testPathPattern F-06.exit.test --no-coverage 2>&1
```

## 4. Sibling sites covered

Diagnosis §4 sibling census result: **0 siblings.**

- `register_d7_channel.ts`: 46 `chart_id` occurrences checked; 3 "provenance only" comments, all within `queryRemediesForChartCapability` (lines 1448/1456/1487). All other `chart_id` usages in this file are genuinely required inputs bound in WHERE predicates (`WHERE chart_id = $1` at lines 979, 1039, 1061, 1072, 1188, 1190, 1250–1251, 1294). Isolated singleton.
- `register_p1_aliases.ts`: 6 other remedy aliases (`ref_remedies_get`, `ref_remedies_by_category_list`, `ref_remedy_get`, `ref_tantric_remedies_get`, `ref_remedies_by_planet_get`, `ref_mantras_get`, `ref_remedies_search`) are correctly-described global corpus lookups with no false chart-specificity claim. No siblings.

No additional sites to fix beyond File A and File B.

## 5. Recurrence guard

The exit test in §3 is the primary guard — re-adding `chart_id` to `queryRemediesForChartCapability.input_schema` or restoring the "Chart-specific" alias description both fail closed.

Additionally, add a guard comment to the capability after the fix:
```ts
// NOTE: brahma_remedy_corpus is a global L0 reference table — no chart_id column exists.
// Do NOT add chart_id back to input_schema unless a real chart-scoped join is implemented.
// See F-06 spec for rationale.
```

This prevents future editors from restoring the decorative field under the impression it is useful provenance infrastructure.

## 6. Dependencies, rollback, rebuild

**Dependencies:**
- File B (`register_p1_aliases.ts:1560`) is blocked on `PAR-register_p1_aliases-RELEASE` from S1 CL-11 conductor. File A (`register_d7_channel.ts`) is independently actionable.
- No migrations (TypeScript `input_schema` object change only — no SQL schema, no Prisma migration).
- No rebuild: neither file is in `ga_writers/`, `bo_*` orchestrators, or `pipeline/orchestrator/writers/`. Both are retrieval/MCP registration layer — no asset data is generated. Shadow run is NOT required (this is not a writer-layer fix per PROTOCOL §Level 0).

**Rollback:** `git revert <commit>` on the two-file change. No data to roll back. MCP manifest reverts on next server restart.

## 7. Coverage table

| DIAGNOSIS claim | SPEC section covering it |
|---|---|
| a: Tool description claims "Chart-specific remedy suggestions" (false) | §2 File B: alias description string corrected |
| b: MCP Zod schema has no `chart_id` — hard-rejected before reaching server | §2 File A: capability `input_schema` drops `chart_id`, removing even server-side implication; File B corrects description |
| c: `chart_id` in capability handler is provenance-only, never in SQL WHERE; `brahma_remedy_corpus` has no chart_id column | §2 File A changes 1–3: field removed from schema, handler variable dropped, echo removed |
| Sibling census: 0 siblings in both files | §4: confirmed, no additional sites |
| S1 lease on `register_p1_aliases.ts` (lines 1558–1568) | §2 File B dependency note; §6 dependencies |
| Two remediation shapes: minimal/honest vs build-out chart join | §2 explicitly chooses minimal/honest; build-out (real chart join) left as separate future backlog item |
| `brahma_remedy_corpus` global — no per-chart rows possible even in principle | §2 File A rationale; §5 guard comment codifies this |
