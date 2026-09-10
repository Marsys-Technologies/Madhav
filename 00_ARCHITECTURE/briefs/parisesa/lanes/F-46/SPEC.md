---
lane: F-46
stream: S2 (finding owner); build split per confirmed LEASES.json routing — register_p1_ganita.ts
  piece to S1, register_p1_synthesis.ts piece follows that file's own ordered-handoff chain
  (currently S5, later S4)
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review; two-piece build, see §6
---

# SPEC — route `applyAutoBudgetToEnvelope` callers through `finalizeMcpBudget` for full honesty-echo

## 1. Root-cause statement

`applyAutoBudgetToEnvelope` (`response_budget.ts:584-598`, S2 HOT) calls the weaker
`applyResponseBudget` directly and only appends `trim_report` — it never sets
`budget_kb_applied`/`budget_kb_requested` or merges `recover_via` pointers into top-level
`drill_pointers`, unlike the stronger `finalizeMcpBudget` (`:361-444`) which does all three. The
wiring choice was made at two caller sites (`register_p1_ganita.ts:162`,
`register_p1_synthesis.ts:177`), not inside `response_budget.ts` itself — both functions
individually do what they're documented to do; the defect is which one 19 tools' `dualOutput`
helpers were wired to.

## 2. Fix (single mechanism, two build locations)

**Chosen fix shape (per DIAGNOSIS.md §3's own recommendation, route (b)):** replace
`applyAutoBudgetToEnvelope(obj, toolName)` with `finalizeMcpBudget(obj, { maxKb, sections:
autoDetectTrimmableSections(obj, toolName) })` at both call sites — deletes a redundant weaker
code path rather than duplicating `finalizeMcpBudget`'s logic inside `applyAutoBudgetToEnvelope`.
`finalizeMcpBudget` already does everything `applyAutoBudgetToEnvelope` does plus the three
missing behaviors (it calls `applyResponseBudget` internally, `response_budget.ts:370`).

### 2a. `register_p1_ganita.ts:162` (S1's lease — build routes here)

```ts
// BEFORE:
applyAutoBudgetToEnvelope(obj, toolName)

// AFTER:
const sections = autoDetectTrimmableSections(obj, toolName)
finalizeMcpBudget(obj, { maxKb: 40, sections })
```
Affects 13 tools registered in this file (DIAGNOSIS.md §4): `ganita_strength_get`,
`ganita_structural_get`, `ganita_condition_get`, `ganita_kp_cusps_get`, `ganita_sade_sati_get`,
`ganita_tajaka_get`, `ganita_nakshatra_get`, `ganita_yogas_get`, `phala_rectification_get`,
`ganita_transit_anchors_get`, `ganita_database_schema_get`, `ganita_concept_locate`,
`ganita_planet_get`.

### 2b. `register_p1_synthesis.ts:177` (follows this file's existing ordered-handoff chain — S5
now, S4 later per LEASES.json; not built until it's this stream's turn to hold the file)

Identical one-line swap. Affects 6 tools: `mimamsa_insight_get`, `bodha_discoveries_get`,
`kala_life_arc_get`, `synth_tail_divergence_get`, `synth_chart_brief_get`,
`prashna_undertaking_get`.

**Note for whichever stream builds §2b:** `synth_chart_brief_get` is also F-45's site (this
stream's own `lanes/F-45/SPEC.md`, a DIFFERENT defect in the SAME function —
`coverage_receipt`'s stale narrative count, baked into a string before this exact
`applyAutoBudgetToEnvelope`/`dualOutput` call). Both fixes touch `register_p1_synthesis.ts` at
different points in the same function's control flow; sequence them (either order works, but
land as two separate commits with the second rebased on the first, not parallel edits to the
same function body).

## 3. Exit test

```ts
test('ganita_planet_get echoes budget_kb_applied and merges drill_pointers after trim', async () => {
  const res = await callTool('ganita_planet_get', { chart_id: CANONICAL_CHART_ID, planet: 'Saturn' })
  expect(res.content.trim_report.length).toBeGreaterThan(0)     // trim genuinely happened
  expect(res).toHaveProperty('budget_kb_applied')                // fails today
  expect(res.drill_pointers.length).toBeGreaterThan(0)           // fails today: []
})

test('kala_projections_get and mimamsa_lel_query are unaffected (already correct)', async () => {
  // Regression guard — these two corpus-named suspects were REFUTED in DIAGNOSIS.md §4
  // (already wired through the strong path via register_p1_aliases.ts). This fix must not
  // touch their wiring or double-apply the budget mechanism.
  const res = await callTool('kala_projections_get', { chart_id: CANONICAL_CHART_ID })
  expect(res).toHaveProperty('budget_kb_applied')
  expect(res.content.budget_kb_applied).toBe(40)   // unchanged from today's correct value
})
```
First test fails today (verified live, DIAGNOSIS.md §1). Second test should already pass today
and must keep passing — explicit regression guard since this fix's file (`register_p1_aliases.ts`)
is untouched, but the pattern is easy to over-apply by mistake.

## 4. Sibling sites covered

All 19 confirmed sites (13 + 6, §2a/§2b) — DIAGNOSIS.md §4's exhaustive call-site enumeration for
both `applyAutoBudgetToEnvelope` call sites. The 2 corpus-named suspects that turned out to
already use the strong path (`kala_projections_get`, `mimamsa_lel_query`, both in
`register_p1_aliases.ts`) are explicitly NOT touched — covered by the regression-guard test above,
not silently ignored.

## 5. Recurrence guard

Once both call sites route through `finalizeMcpBudget`, `applyAutoBudgetToEnvelope` itself has
zero remaining callers (DIAGNOSIS.md §4 confirmed exactly 2 call sites, both fixed). Recommend
deleting the now-dead function as part of this build (not just leaving it as unreachable code) —
its continued existence is itself an attractive nuisance for a future caller to accidentally wire
into again. If VERIFIER prefers keeping it for back-compat/external-caller safety, flag as a
disagreement point rather than silently deleting.

## 6. Dependencies and rollback — two-piece build sequencing

`register_p1_ganita.ts` (§2a) is available now (S1's own lease, no ordered-handoff blocking it).
`register_p1_synthesis.ts` (§2b) is currently held by S5 for their own CL-03 predicate work, then
hands to S4 — this spec's §2b piece queues behind that existing chain per LEASES.json, not built
out of turn. **This spec does not gate on §2b landing to close §2a's half of F-46** — the two
pieces are independent hunks in independent files; VERIFIER may mark the spec COMPLETE and S1
builds §2a immediately, with §2b following once `register_p1_synthesis.ts` cycles to whichever
stream holds it. Rollback: both hunks are single-line function-call swaps, trivially revertible,
no shared state between them.

## 7. Coverage table

| Sub-claim | Spec element |
|---|---|
| F-46a: no budget_kb_applied/requested echo | §2a + §2b (via finalizeMcpBudget's existing behavior) |
| F-46b: recover_via not merged into drill_pointers | §2a + §2b (same) |
| F-46c: scope — is it really 4 named tools | §4 — corrected to 19 real sites, 2 named suspects refuted |
