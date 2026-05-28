---
status: COMPLETE
unit: 2b
wave: 2
title: Unified tool contract — one definition, both channels (sets G3_contract)
stream: A
worktree: ../MadhavStreamA
blockedBy: [naming_ci]
sets_gate: G3_contract
on_red: rollback
---

## Context (self-contained)
Today every retrieval tool is maintained TWICE — `platform/src/lib/retrieve/*` (portal) and
`platform-mcp/src/tools/*` (MCP) — with name-splits and alias bridges (audit + REALITY_REPORT). Create ONE
canonical contract both channels build from. This is TOOL_PORTFOLIO Phase 2/3, and it is where the multi-chart
and multi-ayanamsha dimensions enter the tool layer.

## Scope
- **Shared schema module** `platform/src/lib/contract/` exporting, per tool: `canonical_name`, a Zod
  `input_schema`, Claude-tuned `description`, `annotations` (read-only/idempotent), `role`, `family`,
  `data_dependency`, and the ayanamsha contract (below). Generate JSON-Schema via `zod-to-json-schema`.
- **`chart_id` is a required input** on every per-chart tool (drop the `NATIVE_CHART_ID`/`DEFAULT_CHART_ID`
  default — that default removal is gate G4's concern, but the contract makes chart_id required now).
- **Ayanamsha dimension:** every ayanamsha-dependent tool declares an `ayanamsha_role` (`canonical` | `kp` |
  `reference`) and accepts an optional `ayanamsha_id` (defaulting to its role's id). Parashari/varga/dasha/MSR
  tools = `canonical`; KP tools = `kp`. No ayanamsha-dependent tool may omit the dimension (mirrors the
  engine isolation contract in 1.1).
- **Backfill** the manifest `query_schema` for all tools from the Zod module; **generate** `catalog.ts` +
  capabilities content from the contract (no hand maintenance); MCP server + portal `tool_catalogue` both
  build their tool list from the one contract. Collapse the name-splits per §3.3 (canonical = MCP name).
- Do NOT de-judge here (that is Wave-3) and do NOT build the gateway (Wave-3) — contract only.

## Acceptance criteria (all automated)
1. `npx vitest run platform/src/lib/contract/__tests__/unified_contract.test.ts` green (the G3 gate).
2. Manifest `query_schema` populated for every tool (0 missing); `catalog` count == `server.ts` registration count.
3. Every ayanamsha-dependent tool declares `ayanamsha_role` + accepts `ayanamsha_id`; an assertion fails if any omits it.
4. **Golden-transcript:** for a fixed query set, each tool's output is byte-identical before/after the contract
   migration (behaviour-preserving — the contract reshapes definitions, not results).
5. Both channels demonstrably resolve a tool from the single contract (test mounts both paths).

## must_not_touch
`platform/src/lib/retrieve/msr_sql.ts` judgment logic (Wave-3 de-judgment), `platform/python-sidecar/**`,
`platform/migrations/**`, the charts table (2c owns it).

## Commit cadence / rollback
Commits: (1) contract module + Zod schemas, (2) manifest backfill + catalog generation, (3) dual-channel
wiring + tests. Cleanly cherry-pickable. Rollback = revert; aliases/old paths remain until the canonical
rename (Wave-3) so nothing breaks mid-migration.
