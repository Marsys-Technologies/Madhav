---
finding: F-17
stream: S1 DVARA
class: CL-11 (dead recover_via pointer — 'unknown_tool' placeholder)
role: EXEMPLAR for CL-11 (siblings: F-18 direct dupe, F-43 census of ~19 more sites)
stage: D COMPLETE
---

## 1. Live reproduction

Ran verbatim:
```
mcp__marsys-jis-direct__bodha_graph_subgraph_get({chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  mode: 'neighbors', start_node: '478359a4-0637-46b6-8a78-300ead95787f', depth: 2})
```
Result (2026-08-16, live): `content.edges` trimmed **166 → 41** (`node_count:24, edge_count:166`,
`trim_report[0].kept_count:41`) — matches the finding's claimed 166→41 exactly.
`trim_report[0].recover_via` = `{"instrument":"unknown_tool","hint":"call unknown_tool again with a
narrower filter/date_range, or a smaller top_k/limit, to reach the rest of \"content.edges\""}`.
`drill_pointers[0]` carries the same `instrument:"unknown_tool"`.
STILL REPRODUCES — not already-fixed. Raw JSON: see tool-call output in this lane's evidence (not
re-saved separately; identical shape to corpus `evidence_file`).

## 2. Claim decomposition

Single assertion, cleanly falsifiable: "recover_via.instrument reads the literal string
'unknown_tool' instead of the real tool name whenever the response is budget-trimmed." Confirmed
verbatim above. No sub-claims to split.

## 3. Mechanism → file:line

`platform-mcp/src/tools/register_p1_aliases.ts:188`:
```ts
function dualOutput(data: unknown, toolName = 'unknown_tool') {
```
Call site for this specific tool, `register_p1_aliases.ts:1249`:
```ts
        return dualOutput(data)
```
— the second argument is omitted, so `toolName` defaults to the placeholder string. Whatever
downstream budget/trim helper builds `recover_via.instrument` (in
`platform-mcp/src/lib/response_budget.ts`, `applyAutoBudgetToEnvelope`) reads that placeholder
verbatim into the served envelope.

**Known-good fix pattern already exists in the same file**, unapplied here: `register_p1_aliases.ts`
lines 1800-1803 carry a comment showing the correct call shape,
`dualOutput(data, 'the_real_tool_name')`. `phala_outlook_get` (RC-04, 2026-07-23, verified live in
this same session — see F-09 lane) is the one sibling in the whole codebase already patched this way;
its `recover_via.instrument` now correctly reads `"phala_outlook_get"`.

## 4. Sibling census

`grep -n "return dualOutput(data)$" platform-mcp/src/tools/register_p1_aliases.ts` → **21 bare
call sites** (no `toolName` argument): lines 606, 657, 1155, 1207, **1249 (this finding, F-17)**,
1368, 1499, 1522, 1558, 1570, 1582, 1594, 1606, 1618, 1630, 1670, 1781, 1844, 1860, 1874, 1971.

Of these, line 657 = F-18 (`bodha_graph_traverse_get`, filed separately, identical mechanism — treat
as a direct replication of this spec, not a new diagnosis). The remaining 19 sites (606, 1155, 1207,
1368, 1499, 1522, 1558, 1570, 1582, 1594, 1606, 1618, 1630, 1670, 1781, 1844, 1860, 1874, 1971) are
F-43's census scope — F-43's own corpus claim named 16 of these by tool name plus the F-17/F-18 pair;
this grep independently confirms the exact line count/positions for all 21 for the first time.
**Every one of these 21 sites needs its own `toolName` literal** — each call site must be told which
tool it is registering; there is no way to derive it generically inside `dualOutput` (it isn't passed
`this`/closure tool identity).

## 5. Blast radius

- CL-00 controls: none of the 27 directly test `recover_via.instrument` shape today (confirmed no
  hit in a scan of `platform/scripts/governance/ekv_controls.py` for `unknown_tool` or
  `recover_via`) — this fix, once landed, is a candidate for a NEW cheap CL-00 lint (grep for bare
  `dualOutput(data)` with no second arg → fail), which becomes this lane's recurrence guard (Stage S
  item 5).
- Other lanes sharing this file: F-18 (line 657, same file, same mechanism) and F-43 (census of the
  other 19, same file). All three are S1-owned (`register_p1_aliases.ts` is NOT in the
  lease-conflict table for this file under S1 — the only conflict on this path is the *ordered
  handoff* to S5 for CL-03 param work, which is unrelated to this dualOutput mechanism and does not
  block this lane).
- No other stream's lease touches `register_p1_aliases.ts` for this defect class.
