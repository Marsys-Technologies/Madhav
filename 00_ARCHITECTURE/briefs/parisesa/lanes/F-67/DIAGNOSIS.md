---
finding: F-67
stream: S1 DVARA
class: CL-01 reachability (registered-but-unreachable capability)
stage: D COMPLETE
---

## 1. Live reproduction

```
mcp__marsys-jis-direct__tool_search({query:"pratijna promise denial ledger"})
```
Live result this session: 8 matches, top hit `marsys://tool/L2/query_pratijna` (score 15, correct
match) — but this is the CATALOG DESCRIPTOR, not proof of an invokable tool. Direct attempt to call
`bodha_pratijna_get` or `query_pratijna` as an MCP tool: no such tool is exposed on this session's
`marsys-jis-direct` surface (confirmed by the grep in §3 finding zero `server.tool(...)` registration
calls). CONFIRMED — capability is catalogued, computed, and stored, but not invokable.

## 2. Claim decomposition

1. "135 rows exist in bodha_pratijna for chart 482012f1, 27 event classes" — not independently
   re-verified via direct DB query this pass (would require DB access outside this lane's scope);
   accepted from corpus as an L2 data-layer fact unrelated to this lane's actual defect (the
   registration gap), not in dispute.
2. "CapabilityDescriptor (query_pratijna.ts) exists and is whitelisted under alias
   bodha_pratijna_get in tool_name_bridge.ts:584" — CONFIRMED, see §3.
3. "no file under platform-mcp/src/tools/*.ts or server.ts ever calls server.tool() to register
   'bodha_pratijna_get' or 'query_pratijna'" — CONFIRMED, see §3 (exhaustive grep, zero hits).
4. "this means the rubric's weights/factor_ledger are unreachable by any live caller including
   assess_* and judgment_query" — logical consequence of #3, not independently re-tested against
   assess_*/judgment_query's own output this pass (their non-consumption of pratijna data is a
   separate, larger finding about those tools' own completeness, not this lane's registration gap).

## 3. Mechanism → file:line

`platform/src/lib/retrieval/registry/tool_name_bridge.ts`:
- Line 203: `query_pratijna: 'marsys://tool/L2/query_pratijna',` (bridge entry — capability is known
  to the registry).
- Line 491: `'query_pratijna'` (appears in some allow-list array).
- Line 584: `bodha_pratijna_get: 'query_pratijna',` (the MCP-facing alias name is mapped).

`platform-mcp/src/`: exhaustive grep `server\.tool(\s*['"]query_pratijna|server\.tool(\s*['"]bodha_pratijna_get`
across the entire directory → **zero matches**. Broader `server.tool` census: 26 files contain at
least one `server.tool(...)` call; none registers either name. The only other `pratijna` hits in
`platform-mcp/src` are: a stray comment (`register_p1_synthesis.ts:257`, unrelated context) and the
generated capability-profile file (`generated/mcp_surface_profiles.generated.ts`, which is catalog
metadata, not a live registration — it documents that the descriptor exists, not that it's callable).

**Root cause: the capability was fully specified (descriptor + bridge alias) but the actual
`server.tool('bodha_pratijna_get', ...)` (or `'query_pratijna'`) call that would expose it as an
invokable MCP primitive was never written.** This is a pure omission, not a broken wiring — nothing
needs to be unbroken, a registration function needs to be added.

## 4. Sibling census

Not investigated whether other `tool_name_bridge.ts` aliases have the same "descriptor exists, bridge
entry exists, no server.tool() call" gap — this would require checking all ~180 catalog entries
against the 26 files' actual registrations, which is out of this lane's scope (F-67 is a single,
specific, high-value capability per the finding's own framing — "also unblocks the promise rubric").
Flagging as a systemic-risk follow-up for S1's ledger, not blocking this lane.

## 5. Blast radius

- Fix is a pure addition: a new `registerPratijnaCapability(server, principal)` function (or folded
  into an existing `register_p1_*.ts` file, S1's lease covers `platform-mcp/src/tools/*register*.ts`)
  calling `server.tool('bodha_pratijna_get', ...)`, wired to the existing `query_pratijna` capability
  URI already in the bridge. Zero risk of regressing anything currently working (nothing currently
  calls this path).
- No CL-00 control currently exercises this tool (it doesn't exist yet to test).
- Interacts with (but does not block, and is not blocked by) the separate, larger question of whether
  `assess_*`/`judgment_query` should CONSUME this data once reachable — out of scope for this lane,
  which only closes the reachability gap per S1's CL-01 charter.
