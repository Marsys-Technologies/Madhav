---
contract_id: C1
title: budget_kb request param + paging response fields
version: 1.0
status: FROZEN
authored_by: RUNWAY session (non-participant, charter M2.4)
grounded_in:
  - platform-mcp/src/lib/response_budget.ts (TrimmableSection, applyResponseBudget, finalizeMcpBudget, budgetMcpContent, applyAutoBudgetToEnvelope)
  - platform-mcp/src/tools/registry_bridge.ts:303-307 (MCP_RESPONSE_BUDGET_KB static per-tool ceilings)
  - platform-mcp/src/generated/envelope.ts (v3 envelope pagination/more_available/next_cursor)
---

# C1 — `budget_kb` request param + paging response fields

## Problem this closes
Response byte budgets today are a **server-side constant per tool** (`MCP_RESPONSE_BUDGET_KB` in
`registry_bridge.ts`), never client-controllable. There is no `budget_kb` request param anywhere in
the codebase. This contract adds one, without breaking the existing trim machinery in
`response_budget.ts`, which already does the real work (`TrimmableSection`, `applyResponseBudget`,
`finalizeMcpBudget`).

## Request param (frozen)

Every capability handler that accepts pagination/trimming MAY accept:

```ts
budget_kb?: number   // optional. 1 <= budget_kb <= 64. Omitted => use the tool's
                      // existing MCP_RESPONSE_BUDGET_KB[toolName] default (unchanged behavior).
```

- Zod: `budget_kb: z.number().min(1).max(64).optional()`
- A caller-supplied `budget_kb` LOWER than the tool's static default is honored (tighter budget).
- A caller-supplied `budget_kb` HIGHER than the tool's static default is clamped to the static
  default — **the server ceiling is a hard cap, not merely a suggestion**. This preserves the
  existing `SAFETY_MARGIN_BYTES` invariant in `finalizeMcpBudget` and prevents a caller from
  disabling the trim safety net.
- Implementation: pass the resolved `maxKb = budget_kb ? Math.min(budget_kb, MCP_RESPONSE_BUDGET_KB[toolName]) : MCP_RESPONSE_BUDGET_KB[toolName]` into the existing `applyResponseBudget` / `finalizeMcpBudget` call. No new trimming logic — this contract only adds the request-side override.

## Response paging fields (frozen — codifies what v3 envelope already does)

Every paginated response carries, at the envelope top level (per `envelope.ts`):

```ts
pagination: { offset: number, limit: number, total: number, next_cursor: string | null }
more_available: boolean   // computed from actual remaining rows, never guessed
next_cursor: string | null  // opaque base64 { offset[, fp] }, via encodeCursor/decodeCursor
```

Request-side pairing (unchanged, already live): `cursor?: string`, `limit?: number`, `offset?: number`.

**New field this contract adds** — every response that was trimmed by `budget_kb` (whether
caller-supplied or default) MUST also carry:

```ts
budget_kb_applied: number       // the actual maxKb used after clamping
budget_kb_requested?: number    // echoed back only if the caller supplied budget_kb
```

This lets a caller distinguish "I got everything within my requested budget" from "the server
ceiling silently overrode my request" — an honesty field, consistent with §N.6 Serving Density
Principle (density signaling is data, not narration).

## Non-goals
- Does NOT change per-tool default ceilings in `MCP_RESPONSE_BUDGET_KB`.
- Does NOT introduce a new trimming algorithm — reuses `TrimmableSection`/`hardFloor` untouched.
- Does NOT apply to non-paginated single-object responses (e.g. `graha_portrait` narrative blocks) —
  scope is capabilities that already emit `pagination`/`more_available`.
