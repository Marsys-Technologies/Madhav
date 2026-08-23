---
lane: F-28
stream: filed under S2 (finding owner), build routes to S1 per conductor's confirmed routing
  (tool_name_bridge.ts is S1's lease)
stage: S — SPEC
author: MATRA-LEAD (S2)
status: DRAFT — awaiting VERIFIER review; build assigned to S1 once VERIFIED-COMPLETE
---

# SPEC — stop `toToolBundleResults` from collapsing structured object content into one
opaque string before any array-based trimmer can see it

## 0. Routing confirmation

Conductor confirmed (relayed, then independently verified against `LEASES.json` at source per
FM-09): F-28 → S1 builds, mechanism is `tool_name_bridge.ts`'s `toToolBundleResults`, already
S1's lease. S2 keeps the finding, writes this spec, S1's builder applies once VERIFIED-COMPLETE.

## 1. Root-cause statement

`tool_name_bridge.ts:237-262`'s `toToolBundleResults` — the single, universal ToolBundle↔ToolResult
adapter used by every one of the ~70 whitelisted surgical-primitive tools — has no branch for a
`ToolResult` whose `content` is a structured object with multiple arrays inside it (the standard,
documented shape per `types.ts:533`). Its only two branches are "array content" and "single
opaque-string-or-JSON.stringify'd object content" — the latter fires for `query_calibration`'s
four-array response, collapsing `verdict_distribution`/`reliability_curve`/`multipliers`/
`qa_results` (168 rows) into ONE JSON string inside a 1-item `results` array, before
`response_budget.ts`'s trimmer ever runs. `autoDetectTrimmableSections` only declares sections for
top-level arrays >10 items — a 1-item wrapper array never qualifies — so no structural trim is
possible, and the response's fate is decided entirely by the 120-char last-resort string truncation
(`response_budget.ts:454`, confirmed working-as-designed, not itself the defect).

## 2. Files to change

`platform/src/lib/retrieval/registry/tool_name_bridge.ts:237-262` (S1's lease) — add a third
branch, checked before the final "Single ToolResult" fallback:

```ts
// BEFORE (:132-137, current "Single ToolResult" branch, unconditional):
if (typeof content === 'object' && 'content' in content) {
  const inner = (content as Record<string, unknown>)['content']
  const str = typeof inner === 'string' ? inner : JSON.stringify(inner)
  return [{ content: str }]
}

// AFTER — recognize a multi-array object shape and preserve structure instead of collapsing it:
if (typeof content === 'object' && 'content' in content) {
  const inner = (content as Record<string, unknown>)['content']
  if (typeof inner === 'object' && inner !== null && !Array.isArray(inner)) {
    // If any top-level value inside `inner` is itself an array, preserve `inner` as a structured
    // object result rather than flattening to a string — this is what lets
    // autoDetectTrimmableSections see the real arrays.
    const hasArrayField = Object.values(inner).some((v) => Array.isArray(v))
    if (hasArrayField) {
      return [{ content: inner as Record<string, unknown> }]  // structured, not stringified
    }
  }
  const str = typeof inner === 'string' ? inner : JSON.stringify(inner)
  return [{ content: str }]
}
```

**BUILD-STAGE VERIFICATION REQUIRED (not assumed by this spec):** confirm the `ToolBundleResult`
type (wherever it's declared — not read in this DIAGNOSE pass) actually permits `content: object`,
not only `content: string`. If it's typed as `string`-only, this fix needs a companion type
widening, which is a larger, more carefully-reviewed change given the "genuine multi-lane hotspot"
blast radius DIAGNOSIS.md §5 documents (S1's own F-11/F-25/F-67/F-73/F-09/F-17/F-18/F-43/F-123/F-38
all touch this same function). VERIFIER must confirm this before Stage B, not assume it.

## 3. Exit test

```ts
test('toToolBundleResults preserves multi-array object content for downstream trimming', () => {
  const input = { content: { chart_id: 'x', verdict_distribution: [1,2,3,4], reliability_curve: [1,2,3,4,5,6],
    multipliers: [1,2,3,4,5,6,7,8,9], qa_results: new Array(168).fill(0) }, is_error: false }
  const result = toToolBundleResults(input)
  expect(result).toHaveLength(1)
  expect(typeof result[0].content).toBe('object')          // fails today: content is a JSON string
  expect((result[0].content as any).qa_results).toHaveLength(168)  // fails today: not addressable, buried in a string
})

test('mimamsa_calibration_get no longer hard-truncates its real data', async () => {
  const res = await callTool('mimamsa_calibration_get', { chart_id: CANONICAL_CHART_ID })
  const text = JSON.stringify(res)
  expect(text).not.toContain('[truncated for budget]')     // fails today
  expect(res.content.qa_results?.length ?? 0).toBeGreaterThan(0)  // fails today: field doesn't survive the collapse
})
```
Both fail today (verified in DIAGNOSIS.md §1/§3b); both pass once §2 lands, PROVIDED the
budget-kb ceiling (40KB default, S5's file, see §7) doesn't independently still truncate the
now-visible 168-row `qa_results` array — flagged as a real risk, not glossed over (see §7).

## 4. Sibling sites covered

DIAGNOSIS.md §4b found this defect is the DEFAULT behavior of the adapter for the entire registry
(zero of 172 capability handlers pre-shape as `{results:[...]}`) — the fix in §2 is a mechanism-
level change that benefits every surgical-primitive tool whose `content` is a multi-array object,
not just `mimamsa_calibration_get`. DIAGNOSIS.md names 8 same-shape siblings within S3's
`L5_mimamsa/**` lease (`query_attribution.ts`, `query_insight_embeddings.ts`, `query_journal.ts`,
`query_load_bearing.ts`, `query_mimamsa_discoveries.ts`, `query_manifestation_sets.ts`,
`query_insights.ts`, `query_signal_families.ts`) — NOT independently live-verified as
over-40KB/actually-observably-broken in the Stage-D pass (a full whitelist-wide byte-size audit
was explicitly flagged there as its own SPEC-stage-scale task, not attempted). **This spec's exit
test covers the mechanism generically (test 1) and the one confirmed-broken tool specifically
(test 2) — it does not individually verify the 8 named siblings.** Recommend a follow-up
census/replication pass once this fix is BUILD-verified, scoped to S3 (their lease) using this
spec's mechanism as the exemplar.

## 5. Recurrence guard

Test 1 (§3) is itself the recurrence guard — any future regression collapsing object content with
array fields fails it immediately, independent of any specific tool.

## 6. Dependencies and rollback

No DB migration. File is S1's lease — S2 specs, S1 builds once VERIFIED-COMPLETE. **Real
dependency, flagged honestly:** DIAGNOSIS.md §5 documents `tool_name_bridge.ts` as a "genuine
multi-lane hotspot" — S1 has multiple of its own findings (F-11, F-25, F-67, F-73, F-09, F-17,
F-18, F-43, F-123, F-38) touching this same file. S1's builder must sequence this change against
their own in-flight edits to the same function; not S2's call to make, flagged for S1/conductor.
Rollback: single function, single added branch, trivially revertible; does not change the
function's behavior for any content shape that doesn't have a top-level array field (the common
case for most handlers), so a revert has no other side effects.

## 7. Known, deliberately incomplete scope — flagged, not glossed over

This spec fixes the STRUCTURAL collapse (§2) so `response_budget.ts`'s trimmer can finally SEE
`qa_results` as a real 168-item array. It does NOT itself guarantee the full 168 rows survive to
the caller — once visible, the array is still subject to normal budget trimming (S2's own
`response_budget.ts`, working correctly per DIAGNOSIS.md §3a) and `mimamsa_calibration_get`'s
schema still has no `budget_kb` override param (S5's `register_p1_aliases.ts:1844-1857`, a
SEPARATE gap this spec does not close — F-28's own claim is about the truncation being total and
unrecoverable, which this spec fixes; a caller wanting to page through all 168 QA rows specifically
would still need S5's schema gap closed too). **Recommend a follow-up finding/lane for the
`budget_kb` param gap**, distinct from this spec's mechanism-level fix — not silently bundled in
as if closed.

## 8. Coverage table

| Sub-claim | Spec element |
|---|---|
| F-28a: ~120-char hard truncation | §2 (removes the root cause that makes truncation the only option; truncation lever itself, §3a of DIAGNOSIS.md, is untouched — it's correct) |
| F-28b: no override parameter | **NOT closed by this spec** — separate gap, S5's file, flagged §7 as a follow-up |
| F-28c: real data exists in DB | n/a — already true, not a defect to fix |
| F-28d: practically unrecoverable through this tool | §2 (once structural collapse stops, the real arrays become visible/addressable, even if still budget-bounded rather than unlimited) |
