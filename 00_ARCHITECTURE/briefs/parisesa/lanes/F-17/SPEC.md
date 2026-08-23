---
finding: F-17
stream: S1 DVARA
role: EXEMPLAR for CL-11 — spec once here, F-18 + F-43's 19 sites replicate this pattern
stage: S (awaiting VERIFIER review — do not build until REVIEW.md verdict is COMPLETE)
---

## 1. Root cause (one sentence, mechanism-level)

`register_p1_aliases.ts`'s shared `dualOutput(data, toolName='unknown_tool')` helper silently
defaults `toolName` to a placeholder string whenever a call site omits the second argument, and 21
of the file's 21+ call sites do exactly that, so the placeholder — not the real tool name — is what
the budget/trim layer (`response_budget.ts`) reads into `recover_via.instrument` on every trimmed
response from those tools.

## 2. Files to change

- `platform-mcp/src/tools/register_p1_aliases.ts` — all 21 bare `dualOutput(data)` call sites (lines
  606, 657, 1155, 1207, 1249, 1368, 1499, 1522, 1558, 1570, 1582, 1594, 1606, 1618, 1630, 1670, 1781,
  1844, 1860, 1874, 1971) become `dualOutput(data, '<real_tool_name>')`, where `<real_tool_name>` is
  the exact `server.tool('<name>', ...)` string that call site's enclosing handler registers under
  (each site sits inside one `server.tool(...)` block — the name is the literal already present a
  few lines above each call, not a guess).
- No other file changes required — `dualOutput`'s signature already accepts the second argument;
  this is a pure call-site fix, not an API change.

## 3. Exit test

New test file: `platform-mcp/src/tools/__tests__/dual_output_tool_name.test.ts`
```ts
// FAILS today (21 call sites resolve to 'unknown_tool'); PASSES once all 21 pass an explicit name.
import * as fs from 'fs'
test('every dualOutput(data) call site in register_p1_aliases.ts passes an explicit toolName', () => {
  const src = fs.readFileSync('platform-mcp/src/tools/register_p1_aliases.ts', 'utf8')
  const bare = [...src.matchAll(/dualOutput\(data\)/g)]
  expect(bare.length).toBe(0)
})
```
Live confirmation (Stage V, post-build): re-run this lane's `reproduce_cmd` and assert
`trim_report[0].recover_via.instrument === 'bodha_graph_subgraph_get'` (not `'unknown_tool'`).

## 4. Sibling sites covered

All 21 bare-call sites from DIAGNOSIS.md §4 are covered by this same mechanical fix — see file list
above. None excluded. F-18 (line 657) and F-43's 19 remaining sites are replications of this exact
diff pattern, not independent specs — VERIFIER reviews this spec once; F-18/F-43 builds cite this
REVIEW.md as their authority per plan §5 "Exemplar-then-replicate."

## 5. Recurrence guard

The exit test above (§3) is itself the permanent recurrence guard — it is not deleted after this
lane closes; it stays in the suite so any future `dualOutput(data)` call added without a name fails
CI immediately. (Candidate secondary guard, out of scope for this lane: promote the same regex check
into `platform/scripts/governance/ekv_controls.py` as a new cheap CL-00 check — flagged as a
follow-up, not built here, to keep this lane's diff minimal per §6 rollback note below.)

## 6. Dependencies and rollback

No dependency on other lanes, deploys, or rebuilds — pure same-file, same-PR change; `dualOutput`'s
call signature is unchanged (second arg was always optional), so no caller outside this file is
affected. Rollback: revert the single commit; `toolName` reverts to its default and behavior returns
to today's (degraded but non-crashing) state — zero risk of breaking a currently-working path.

## 7. Sub-claim coverage table

| D-2 sub-claim | Spec element that closes it |
|---|---|
| "recover_via.instrument reads the literal 'unknown_tool'" | §2 fix at line 1249 (this finding's own site) |
| (implicit, from D-4 sibling census) "the same defect fires on any of the ~21 other sites" | §2 fix at all 20 other listed lines; §3 exit test asserts zero remaining bare sites file-wide |
