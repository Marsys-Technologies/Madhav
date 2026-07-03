---
artifact: RETRIEVAL_CITATION_REPORT_MCP_TOOL_HYGIENE
canonical_id: RETRIEVAL_CITATION_REPORT_MCP_TOOL_HYGIENE
version: 1.0
status: CURRENT
created: 2026-06-28
classification: Citation report for ISSUE-7 MCP tool hygiene
---

# MCP Tool Hygiene — Citation Report (ISSUE-7)

## Summary

19 contaminated files in `platform-mcp/src/tools/` processed as part of ISSUE-7.
Classification: WIRED (imported in server.ts = scrub only), UNWIRED (zero imports = retire).

## Per-File Decision Table

| File | Status | Decision | Reason |
|------|--------|----------|--------|
| l0_ephemeris.ts | WIRED (server.ts:47) | SCRUBBED | Native identifiers in JSDoc comments only |
| muhurta_finder.ts | WIRED (server.ts:31) | SCRUBBED | Native identifiers in JSDoc FORENSIC section |
| phala_event_anchors.ts | WIRED (server.ts:35) | SCRUBBED | Native identifiers in JSDoc + function comment |
| mimamsa_lel_intake.ts | WIRED (server.ts:32) | SCRUBBED | Native identifiers in JSDoc |
| mimamsa_outcome.ts | WIRED (server.ts:33) | SCRUBBED | Native identifiers in JSDoc |
| phala_outlook.ts | WIRED (server.ts:30) | SCRUBBED | Native identifiers in JSDoc |
| phala_mitigation_map.ts | WIRED (server.ts:29) | SCRUBBED | Native identifiers in JSDoc |
| retrieval/kala_temporal.ts | WIRED (server.ts:37) | SCRUBBED | Native identifiers in JSDoc + functional NATIVE_CHART_ID_CONST branching removed |
| kala_timeline.ts | UNWIRED (tests only) | SCRUBBED | Unique capability; native identifiers in comments/error messages |
| bo_2-5.ts | UNWIRED | RETIRED | Superseded by consolidated sealed MCP surface (D6/D7) |
| bo_2-6.ts | UNWIRED | RETIRED | Superseded by consolidated sealed MCP surface (D6/D7) |
| get_cgm_subgraph.ts | UNWIRED | RETIRED | Superseded; targets dropped bodha_graph table (pre-migration 325) |
| bodha_bo22.ts | UNWIRED | RETIRED | Superseded by consolidated sealed MCP surface (D6/D7) |
| bodha_bo24.ts | UNWIRED | RETIRED | Superseded by consolidated sealed MCP surface (D6/D7) |
| phala_rectification.ts | UNWIRED | RETIRED | No unique capability vs sealed surface; unwired |
| kala_period_snapshot.ts | UNWIRED | RETIRED | No unique capability vs sealed surface; unwired |
| kala_convergence.ts | UNWIRED | RETIRED | No unique capability vs sealed surface; unwired |
| retrieval/ganita_forensic_render.ts | UNWIRED | RETIRED | Retire-target noted in D1 closure; superseded |
| kala_temporal.ts (root) | UNWIRED (tests only) | RETIRED | Duplicate of retrieval/kala_temporal.ts (the wired version); test file also deleted |

## Gate Extension

The chart-agnostic CI gate (`platform/src/lib/retrieval/registry/chart_agnostic_gate.ts`) was
extended with `scanMcpToolFileContent()` which detects:
- `482012f1` (native UUID)
- `NATIVE_CHART_ID` (native UUID constant)
- `Abhisek Mohanty` (native name)

A test was added in `chart_agnostic_gate.test.ts` proving the gate catches a native UUID in mock MCP tool file content.

## Post-hygiene verification

After all changes: `grep -rn "482012f1\|NATIVE_CHART_ID\|Abhisek Mohanty" platform-mcp/src/tools/` should return zero results.
