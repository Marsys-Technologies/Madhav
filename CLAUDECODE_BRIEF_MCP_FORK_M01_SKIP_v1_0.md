---
canonical_id: CLAUDECODE_BRIEF_MCP_FORK_M01_SKIP
version: 1.0
status: INFORMATIONAL — read before starting MCP fork M0 phase
created: 2026-06-30
author: Retrieval Engine R-series run (RETRIEVAL_ENGINE_SEAL_RECORD_v1_0 §6)
purpose: Coordinate so the MCP fork does NOT redo work already completed by the retrieval engine run.
---

# MCP FORK COORDINATION NOTE — M0.1 Already Done

The retrieval engine run (R-series) completed the 401-fix work that was earmarked as **M0.1** for the MCP fork.
**Do not re-implement M0.1.** Verify the fix is live and proceed directly to M0.2+.

## What was done (R2.0)

`platform/src/app/api/mcp/primitives/[tool]/route.ts` — the `x-mcp-audience-tier` header is **no longer a gate**:
- Previously the route returned 401 when this header was absent.
- R2.0 (2026-05-28 "tier_excision", then confirmed in the R-series) excised it: the header is read for
  informational/logging purposes only; missing header now defaults to `'client'`.
- Comment on line 83 of that file confirms: "See R2.0 fix: removing 401 on missing audience-tier."

## What was also completed by the R-series

| Item | Status |
|---|---|
| `getMcpSurfaceSpec` seam | **LIVE** — `GET /api/mcp/surface-spec` returns the registry surface spec for the MCP fork to consume |
| Single registry source | **DONE** — chat + MCP channels both consume `platform/src/lib/retrieval/registry/` capabilities |
| bodha_contradictions populated | **DONE** — 10,670 rows across both charts (Abhinandan + Abhisek native), all 5 ayanamshas |
| `query_contradictions` default ayanamsha | **FIXED** — default changed from stale `'LAHIRI'` → `'lahiri_chitrapaksha'` |
| assess_* tools contradiction output | **LIVE** — returns `status: 'ok'` with items when chart has been built |

## What the MCP fork still owns

- M0.2+: `authorizeChartAccess` entitlement wiring (the MCP channel owns entitlement — NOT retrieval).
- M1+: Any MCP-fork-specific work not covered above.
- The chart-agnostic + contamination invariants still apply: no native defaults anywhere in the channel.

## Verification command (confirm 401 fix before proceeding)

```bash
# Should return the surface spec (not a 401):
curl -s http://localhost:3000/api/mcp/surface-spec | jq '.capability_count'
```

*End of CLAUDECODE_BRIEF_MCP_FORK_M01_SKIP v1.0*
