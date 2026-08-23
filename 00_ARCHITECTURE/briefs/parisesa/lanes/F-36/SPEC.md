---
lane: F-36 (standalone — NOT the same defect class as F-12/F-37, see DIAGNOSIS.md §5 correction)
stream: filed under S2, build routes to S5 per conductor (register_d7_channel.ts added to S5's lease)
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — disclose offset clamping in `ganita_chart_facts_get`

## 0. Board correction

Same as F-12/SPEC.md §0: BRANCH-EXISTS classification wrong, corrected to OPEN. Additionally,
per DIAGNOSIS.md §5: F-36 is **not** the CL-06 "total dies under composition" defect at all —
`register_d7_channel.ts`'s `total` field is already a correct, independent `COUNT(*)`
(`:1091-1120`), confirmed stable across offsets in live reproduction. The actual bug is a
different, narrower thing: a silent offset-clamp-and-echo.

## 1. Root-cause statement

`register_d7_channel.ts:924` clamps any `offset` above 100,000 down to 100,000
(`Math.max(0, Math.min(Number(args['offset'] ?? 0), 100_000))`) and both response branches
(`:1140` shape="rows", `:1216` shape="pivoted") echo this clamped local variable back under the
field name `offset` — indistinguishable from an honest echo of the caller's own input. No
`offset_requested`/`offset_clamped` disclosure exists.

## 2. Files to change

`platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`, one hunk near `:924` plus
both echo sites (`:1140`, `:1216`):

```ts
// :924, BEFORE:
const offset = Math.max(0, Math.min(Number(args['offset'] ?? 0), 100_000))

// AFTER:
const offsetRequested = Number(args['offset'] ?? 0)
const offset = Math.max(0, Math.min(offsetRequested, 100_000))
const offsetClamped = offset !== offsetRequested
```

At both echo sites (`:1140`, `:1216`), add two fields to the returned `content` object alongside
the existing `offset`:
```ts
content = {
  ..., offset, offset_requested: offsetRequested, offset_clamped: offsetClamped,
  limit, total, more_available: offset + servedRows.length < total,
}
```
This mirrors the codebase's own existing disclosed-pagination convention (`more_available` is
already an honest derived boolean two fields away) — `offset_clamped` is the same pattern applied
to the clamp itself.

## 3. Exit test

```ts
test('ganita_chart_facts_get discloses offset clamping', async () => {
  const res = await callTool('ganita_chart_facts_get', { chart_id: CANONICAL_CHART_ID, offset: 999999 })
  expect(res.content.offset).toBe(100000)
  expect(res.content.offset_requested).toBe(999999)   // fails today: field doesn't exist
  expect(res.content.offset_clamped).toBe(true)        // fails today: field doesn't exist
})
test('ganita_chart_facts_get does not falsely flag an unclamped offset', async () => {
  const res = await callTool('ganita_chart_facts_get', { chart_id: CANONICAL_CHART_ID, offset: 50 })
  expect(res.content.offset_clamped).toBe(false)
})
```

## 4. Sibling sites covered

Both echo branches (`:1140` rows-shape, `:1216` pivoted-shape — the one exercised by the live
repro) — both use the same clamped local, both get both new fields. No other clamp-with-silent-
echo site was found for this tool in the Stage-D pass (DIAGNOSIS.md §4 — a broader campaign-wide
census of this different defect shape was out of this lane's budget, not claimed exhaustive;
flagged as a possible follow-up census for conductor, distinct from F-12/F-37's Flavor-A sweep).

## 5. Recurrence guard

None built in this spec (single, isolated fix). If the follow-up broader clamp-census (§4) is
run, its results would inform whether a generic lint is warranted.

## 6. Dependencies and rollback

No DB migration. File is S5's lease per conductor routing — S2 specs, S5 builds. Rollback:
single-file, single-hunk revert. Purely additive fields (`offset_requested`, `offset_clamped`) —
no existing field renamed or removed, zero back-compat risk (unlike F-12/F-37's `total` rename).

## 7. Coverage table

| Sub-claim | Finding | Spec element |
|---|---|---|
| F-36a: offset > 100,000 silently clamped | F-36 | §2 (clamp logic unchanged, now measured) |
| F-36b: clamped value echoed as if caller's own | F-36 | §2 (`offset_requested` disambiguates) |
| F-36c: no disclosure field exists | F-36 | §2 (`offset_clamped` is exactly this) |
