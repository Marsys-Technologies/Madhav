---
lane: F-12 (exemplar spec — also closes F-37, same Flavor-A defect; full ~20-site sibling
  disposition table per conductor's explicit ask)
stream: filed under S2, build routes to S5 per conductor's routing (get_dignity.ts/get_avasthas.ts/
  get_karakas.ts/query_yoga_catalog.ts are all S5 MŪLA's lease)
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review; build assigned to S5 once VERIFIED-COMPLETE
---

# SPEC — real COUNT(*) for `total`/`total_count` fields computed as `rows.length` of a
LIMIT-bounded query (Flavor A of the CL-06 defect family)

## 0. Board correction (already applied by conductor)

BOARD.md's Phase 0 "BRANCH-EXISTS(adopt ekv/a-09-sara-kernel)" classification is factually wrong
for F-12/F-36/F-37/F-45 — `ekv/a-09-sara-kernel`'s entire diff is `response_budget.ts` +
`registry_bridge.ts`, scoped to `assess_*` tools' `SaraKernel`/`assembleSaraContent`/
`buildAssessResponse` composition (F-56/F-111). None of these four findings' handler files are
touched by that branch. Corrected to OPEN, full pipeline (already done in BOARD.md). This spec is
new work, not a branch extension.

## 1. Root-cause statement

`ganita_condition_get` (dignity/avasthas/karakas facets) and `ref_yogas_get` compute their
response's `total` field as `result.rows.length` — the size of the page a `LIMIT`/`OFFSET`-bound
SQL query happened to return — instead of a second, independent `SELECT COUNT(*)` over the same
`WHERE` clause without the limit. The codebase already has the correct pattern one directory over
(`get_condition_composite.ts:87-99`, a parallel `Promise.all([pageQuery, countQuery])`) — this
spec replicates that exact shape into the four broken sites, then disposes of the ~20-site sibling
census the diagnosis found.

## 2. Files to change (primary fix — 4 sites, F-12 + F-37)

All four in `platform/src/lib/retrieval/registry/layers/` (S5 MŪLA's lease — build routes there):

1. `L1_ganita/get_dignity.ts:69-74`
2. `L1_ganita/get_avasthas.ts` (same line shape, `:72`)
3. `L1_ganita/get_karakas.ts` (same line shape, `:118`)
4. `L0_brahmagyan/query_yoga_catalog.ts:38-53`

**Fix pattern (identical for all four), mirroring `get_condition_composite.ts:87-99` verbatim:**

```ts
// BEFORE (get_dignity.ts:69-74, representative of all four):
const result = await query<Record<string, unknown>>(sql, params)
return {
  content: { chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0 },
  is_error: false,
}

// AFTER:
const countSql = sql.replace(/\bORDER BY[\s\S]*$/i, '').replace(/LIMIT \$\d+ OFFSET \$\d+\s*$/i, '')
  // build the exact WHERE-only variant per file — see per-file note below, do not regex-strip
  // blindly against a query shape that hasn't been read; each of the 4 files' SQL differs enough
  // that BUILD must hand-verify the WHERE-only string against that file's own `sql` construction
const [result, countResult] = await Promise.all([
  query<Record<string, unknown>>(sql, params),
  query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM chart_facts WHERE ${whereOnly}`, countParams),
])
const total_matching = Number(countResult.rows[0]?.total ?? 0)
return {
  content: {
    chart_id: chartId, categories, rows: result.rows ?? [],
    total_matching, more_available: total_matching > (result.rows?.length ?? 0),
  },
  is_error: false,
}
```

**BUILD-STAGE INSTRUCTION (not spec-invented content):** the exact `WHERE`-only SQL string must
be constructed per-file by reading that file's own `sql` variable build-up (params/filters differ
between dignity/avasthas/karakas/yoga_catalog) — copy `get_condition_composite.ts`'s STRUCTURE
(parallel `Promise.all`, separate `COUNT(*)` query, `total_matching` + `more_available` field
names for consistency with the one correct sibling) but do not literally copy its SQL string,
which is a different table/filter shape.

**Field rename note:** `get_condition_composite.ts` uses `total_matching` (not `total`) —
recommend the same rename here for consistency with the one already-correct sibling in this
directory, rather than inventing a third naming convention. This is a response-shape change
(`total` → `total_matching`); Stage S flags this for VERIFIER: is a renamed field acceptable
mid-campaign, or does back-compat require keeping `total` too (deprecated, mirroring
`total_matching`)? Recommend keeping BOTH (`total`: legacy alias = `total_matching`, one release)
to avoid a breaking change for existing callers — VERIFIER to confirm/override.

## 3. Sibling disposition table — all ~20 sites from the Stage-D census

Per established campaign policy (sibling sites of an already-diagnosed mechanism are covered-or-
excluded in the spec's coverage table, not deferred as new lanes):

| Site | Disposition |
|---|---|
| `L1_ganita/get_dignity.ts:85` | **FIXED** (§2.1, this spec) |
| `L1_ganita/get_avasthas.ts:72` | **FIXED** (§2.2, this spec) |
| `L1_ganita/get_karakas.ts:118` | **FIXED** (§2.3, this spec) |
| `L0_brahmagyan/query_yoga_catalog.ts:61` | **FIXED** (§2.4, this spec — closes F-37) |
| `L1_ganita/get_av_transit_gating.ts:348` | **EXCLUDED, same-pattern-applies** — flagged for a follow-up census-driven fix (not this spec's exit test); same fix shape as §2 applies verbatim when built |
| `L1_ganita/get_av_transit_gating.ts:439` | **EXCLUDED, same-pattern-applies** (as above) |
| `L1_ganita/get_dasha_lord_capability.ts:271` | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_dashas.ts:575` | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_divisionals.ts:121` | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_graha_yuddha.ts:269` | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_positions.ts:265` | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_sade_sati.ts:104` (`all:true` branch) | **EXCLUDED, same-pattern-applies** — `fetchLimit=requestedLimit` shape, same fix |
| `L1_ganita/get_sade_sati.ts:116` (default branch) | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_sensitive_points.ts:153` | **EXCLUDED, same-pattern-applies** |
| `L1_ganita/get_strength.ts:214` | **EXCLUDED, same-pattern-applies** |
| `L0_brahmagyan/query_classical_texts.ts:242` | **EXCLUDED, same-pattern-applies** |
| `L0_brahmagyan/query_classical_texts.ts:309` | **EXCLUDED, same-pattern-applies** |
| `platform-mcp/src/tools/register_p1_reference.ts:346` | **EXCLUDED, same-pattern-applies** — outside registry/layers, still same defect shape |
| `platform-mcp/src/tools/register_p1_reference.ts:489` | **EXCLUDED, same-pattern-applies** |
| `platform-mcp/src/tools/register_p1_synthesis.ts:751` (`synth_tail_divergence_get`) | **EXCLUDED, same-pattern-applies** |
| `registry_bridge.ts:2339` (`total_count` from `boundedArj`) | **EXCLUDED, NEEDS RE-READ AT BUILD TIME** — Stage-D flagged this as possibly already-correct (disclosed-pagination shape, not a bug) rather than a confirmed defect; do not fix blindly, verify first |
| `register_d8_assess_domain.ts:1816` | **EXCLUDED, same-pattern-applies** |
| `register_d8_assess_domain.ts:635` | **EXCLUDED, NEEDS RE-READ AT BUILD TIME** — same caveat as `registry_bridge.ts:2339` |

**Rationale for excluding 18 of 22 sites from this spec's exit test:** the 4 primary sites (F-12's
3 + F-37's 1) are what the corpus's findings actually claim and what PARIŚEṢA is scoped to close;
the other 18 are real, Stage-D-confirmed instances of the identical defect shape but were never
filed as their own findings. Fixing all 22 in one build is a legitimate larger cleanup but risks
scope creep beyond what VERIFIER can review in one pass. **Recommendation to conductor:** file the
18 excluded sites (minus the 2 needs-re-read ones) as a follow-up finding/lane
("CL-06-Flavor-A-sweep") for a haiku replication pass once this spec's pattern is BUILD-verified
correct on the 4 primary sites — classic exemplar-then-replicate, just deferred one stage later
than usual because there was no pre-existing finding ID for the other 18.

## 4. Exit test

`platform/src/lib/retrieval/registry/layers/__tests__/count_arithmetic_parity.test.ts`:
```ts
test('ganita_condition_get total_matching is a real COUNT(*), independent of limit', async () => {
  const small = await callCapability('L1/get_condition_dignity', { chart_id: CANONICAL_CHART_ID, limit: 3 })
  const large = await callCapability('L1/get_condition_dignity', { chart_id: CANONICAL_CHART_ID, limit: 25000 })
  expect(small.content.total_matching).toBe(large.content.total_matching)   // fails today: 3 !== 563
  expect(small.content.rows.length).toBe(3)   // page size still respects limit
})

test('ref_yogas_get total_matching is stable across offset', async () => {
  const page1 = await callTool('ref_yogas_get', { offset: 50, limit: 10 })
  const page2 = await callTool('ref_yogas_get', { offset: 999999 })
  expect(page1.content.total_matching).toBe(page2.content.total_matching)   // fails today: 10 !== 0
})
```
Both fail today (verified against the live reproductions in DIAGNOSIS.md §1); both pass once §2's
four fixes land.

## 5. Sibling sites covered

18 of 22 census sites explicitly excluded-with-reason (§3); 4 fixed (§2). 2 flagged needs-re-read,
not asserted as defects.

## 6. Recurrence guard

Recommend a lint (out of this spec's build scope, flagged for conductor as a possible follow-up):
grep-based CI check for the pattern `total\s*:\s*[\w.]*\.(rows\.)?length\b` inside any file whose
surrounding query has a `LIMIT`/`OFFSET` — would have caught all ~22 sites at write time. Not
built here; flagged only.

## 7. Dependencies and rollback

No DB migration. Files are all S5's lease (per conductor routing) — S2 does not build this, only
specs it; VERIFIER confirms COMPLETE, S5's builder applies. Rollback: revert per-file, each of the
4 fixes is independent (no shared helper introduced, so no cross-file rollback dependency).
Response-shape change (`total` → `total_matching`, with back-compat alias per §2's note) — flag
for VERIFIER to confirm this doesn't collide with any consumer expecting the old field name to
change meaning.

## 8. Coverage table

| Sub-claim | Finding | Spec element |
|---|---|---|
| F-12a: dignity/avasthas/karakas `total` = page length | F-12 | §2.1-2.3 |
| F-12b: correct pattern exists in-codebase (contrast) | F-12 | §2 mirrors it exactly |
| F-12c: no disclosure that total is page-scoped | F-12 | §2's `total_matching`/`more_available` naming closes this |
| F-37a/b: ref_yogas_get total varies with page | F-37 | §2.4 |
| ~18 sibling sites, same pattern | (Stage-D census, unfiled) | §3 disposition table — excluded, recommended as follow-up lane |
