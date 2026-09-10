---
finding: F-67
stream: S1 DVARA
class: CL-01 reachability (registered-but-unreachable capability)
stage: S COMPLETE — S1-owned end to end (registration is squarely inside S1's own
  register*.ts lease, no cross-stream routing needed)
---

## 1. Root cause (one sentence, mechanism-level)

`query_pratijna` (the bo_pratijna v4 promise/denial ledger, 135 rows / 27 event classes for the
native chart, per DIAGNOSIS.md §2) is fully descriptor'd (`mcp_surface_profiles.generated.ts`) and
bridge-aliased (`tool_name_bridge.ts:203,491,584` — both `query_pratijna` and its
`bodha_pratijna_get` alias map to `marsys://tool/L2/query_pratijna`) but no file anywhere in
`platform-mcp/src` ever calls `server.tool('query_pratijna', ...)` or
`server.tool('bodha_pratijna_get', ...)` — the registration step was simply never written, a pure
omission (exhaustive grep, DIAGNOSIS.md §3, 26 registration files checked, zero hits).

## 2. Files to change

- `platform-mcp/src/tools/register_p1_aliases.ts` — add a new `server.tool('bodha_pratijna_get',
  ...)` block, modeled directly on this same file's existing `bodha_signals_get` registration
  (lines 535-609, same file, same L2-per-chart-filtered-listing shape) since both target the same
  `callRegistryCap('marsys://tool/L2/<name>', args, principal)` pattern against a bridge-mapped URI:
  ```ts
  server.tool(
    'bodha_pratijna_get',
    'Retrieve the chart pratijna (promise / denial) ledger from bodha_pratijna — one adjudicated ' +
    'row per event_class: status (promised | denied | conditional), grade, varga_confirmation, ' +
    'the supporting_signal_ids and contradicting_signal_ids that back it, and a derivation. ' +
    'Filters: ayanamsha_id, status, event_class_id. Bounded (LIMIT <=50) with a disclosed total ' +
    '+ offset pagination.',   // verbatim from the already-written descriptor, mcp_surface_profiles.generated.ts:4688
    {
      ...ChartBase,
      status: z.string().optional().describe("Filter to one status: 'promised' | 'denied' | 'conditional'."),
      event_class_id: z.string().optional().describe('Filter to one event_class_id.'),
      limit: z.number().int().min(1).max(50).optional(),
      offset: z.number().int().min(0).optional(),
    },
    async (params) => {
      const { chart_id, ayanamsha_id, status, event_class_id, limit, offset } = params as Record<string, unknown>
      if (!chart_id) return errOut('bodha_pratijna_get', 'chart_id is required')
      try {
        const data = await callRegistryCap('marsys://tool/L2/query_pratijna', {
          chart_id, ayanamsha_id: na(ayanamsha_id as string | undefined),
          status, event_class_id,
          limit: (limit as number) ?? 50, offset: (offset as number) ?? 0,
        }, principal) as Record<string, unknown>
        // CL-11 guard (F-17's own exit test would catch this if omitted): pass the real tool
        // name explicitly — do NOT call bare dualOutput(data), which defaults toolName to the
        // 'unknown_tool' placeholder (register_p1_aliases.ts:188, the exact defect F-17/F-18/
        // F-43 are fixing elsewhere in this same file). A brand-new registration must not
        // reintroduce the class of bug another lane in this campaign is actively closing.
        return dualOutput(data, 'bodha_pratijna_get')
      } catch (err) { return errOut('bodha_pratijna_get', String(err), { chart_id }) }
    }
  )
  ```
  Exact param list/limit bounds to be confirmed against `query_pratijna`'s real handler schema
  (`platform/src/lib/retrieval/registry/layers/L2_bodha/query_pratijna.ts` or equivalent — not
  independently opened this pass; the alias schema above is modeled on the already-written
  descriptor text, which itself should be the source of truth for param names) at Stage B.
- No changes needed to `tool_name_bridge.ts` (already correctly wired) or the generated profiles
  file (already correctly descriptor'd).

## 3. Exit test

```
mcp__marsys-jis-direct__tool_search({query:"pratijna promise denial ledger"})
```
then a direct call:
```
bodha_pratijna_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})
```
FAILS today (live-confirmed this session): no such tool is invokable; only the catalog descriptor
is reachable via `tool_search`. PASSES once built: returns real rows from `bodha_pratijna` (135
rows / 27 event classes expected per the finding's own corpus claim, DB row count not
independently re-verified this pass — flagged for Stage V to confirm via direct SQL as F-28's
lane did, not assumed).

## 4. Sibling sites covered

None — this is a net-new registration, not a fix to an existing broken call site. DIAGNOSIS.md §4
flagged an open, unaudited question (whether other `tool_name_bridge.ts` aliases have the same
"descriptor + bridge entry, no registration" gap across the ~180-entry catalog) — out of this
finding's scope, not resolved by this spec.

## 5. Recurrence guard

Recommend (not built here): a CI check cross-referencing `tool_name_bridge.ts`'s alias map against
the set of names actually passed to `server.tool(...)` across `platform-mcp/src/tools/*.ts` —
would have caught this mechanically at the time the bridge entry was added. Flagged as a candidate
governance addition; not required for this lane's own COMPLETE verdict since the fix itself is a
pure addition with no regression surface.

## 6. Dependencies and rollback

No dependency on other lanes. Independent addition — registering a new tool cannot regress any
existing tool's behavior (no shared code path is modified, only a new `server.tool(...)` call is
added). Rollback: remove the new block; behavior reverts to today's (unreachable-but-harmless)
state.

## 7. Sub-claim coverage table

| D-2 sub-claim | Spec element that closes it |
|---|---|
| "descriptor + bridge alias exist but zero server.tool() registration anywhere" | §2: adds the missing registration |
| "the rubric's weights/factor_ledger are unreachable by any live caller" | §2/§3: exit test confirms the tool becomes callable and returns real ledger rows |
| "also unblocks the promise rubric" (plan's own framing) | Out of this finding's scope — whether assess_*/judgment_query should CONSUME this newly-reachable data is a separate, larger finding not addressed here (noted in DIAGNOSIS.md §5) |
