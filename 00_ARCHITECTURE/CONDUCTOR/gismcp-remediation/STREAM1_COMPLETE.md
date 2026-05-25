---
id: STREAM1_COMPLETE
status: COMPLETE
branch: fix/gismcp-r1-r2
sealed_at: 2026-05-26
seal_commit: 4c83257f
---

# GISMCP Remediation Stream 1 — COMPLETE

## Branch

`fix/gismcp-r1-r2`

## Commits

| SHA | Description |
|-----|-------------|
| d5ba6774 | fix(R1): remove tier gating from server.ts — all 40 tools unconditional |
| feec914f | test(R1): tier visibility unit + integration tests — all 40 tools for all tiers |
| 9b001bcc | fix(gismcp-r2): implement 4 MCP primitive retrieval engines (R2-S1/S2/T1) |
| 4c83257f | test(gismcp-r2): add R2-T2 MCP stub engines smoke integration test |

## Sessions Executed

### R1-S1 — Tier Gate Removal (COMPLETE)
- Removed `if (tier !== 'client')` block from `platform-mcp/src/server.ts:233-239`
- Removed secondary tier gate from `tool_health.ts` handler body
- Removed secondary tier gate from `data_coverage.ts` handler body
- Updated tierNote to `'Available: all tiers (unconditional — R1 de-gating).'`
- Updated existing tests that asserted old 403 behavior → now assert ok:true

### R1-T1 — Tier Visibility Tests (COMPLETE)
- `platform-mcp/src/__tests__/server_tier_visibility.test.ts`: 11 unit tests
  - All 40 tools register for client/acharya/super_admin tiers
  - All 5 ops tools present for all tiers
  - No duplicates
- `platform-mcp/src/__tests__/integration/mcp_visibility.integration.test.ts`: 1 integration test
  - CI-safe skipIf without MCP_BASE_URL+MCP_API_KEY_CLIENT
  - Asserts 40 tools visible for client tier

### R2-S1 — query_tara_balam + query_chandra_balam Engines (COMPLETE)
- `platform/src/lib/retrieve/query_tara_balam.ts`: canonical-name alias (TOOL_NAME='query_tara_balam')
- `platform/src/lib/retrieve/query_chandra_balam.ts`: canonical-name alias (TOOL_NAME='query_chandra_balam')
- Both delegate to existing single-date implementations via `baseTool.retrieve()`
- Both added to RETRIEVAL_TOOLS in `index.ts` (tools 52-53)

### R2-S2 — jaimini_chara_dasha + jaimini_chara_dasha_full Engines (COMPLETE)
- `platform/src/lib/retrieve/jaimini_chara_dasha.ts`: delegates to query_jaimini_chara_dasha (include_sub_periods=false)
- `platform/src/lib/retrieve/jaimini_chara_dasha_full.ts`: delegates (include_sub_periods=true)
- Both added to RETRIEVAL_TOOLS in `index.ts` (tools 54-55)

### R2-T1 — FORENSIC-Grounded Engine Integration Tests (COMPLETE)
- `platform/src/lib/retrieve/__tests__/query_tara_balam.test.ts`: 5 unit + 1 DB-integration (skip)
- `platform/src/lib/retrieve/__tests__/query_chandra_balam.test.ts`: 5 unit + 1 DB-integration (skip)
- `platform/src/lib/retrieve/__tests__/jaimini_chara_dasha.test.ts`: 7 unit + 2 sidecar-integration (skip)
- All 17 unit tests PASS

### R2-T2 — Full Vitest Run + Seal (COMPLETE)
- `platform/src/__tests__/integration/mcp_stub_engines.integration.test.ts`: 8 registry smoke + 2 live (skip)
- Platform vitest: 13 failures (all pre-existing); 5180 passing; 27 skipped
- Platform-mcp vitest: 22 failures (all pre-existing); 868 passing; 1 skipped
- Total pre-existing failures: 35 (matches KNOWN_PRE_EXISTING_FAILURES.md v1.5 baseline)

## Acceptance Criteria Status

### R1: Remove Tier Gating
- [x] R1-AC1: `server.ts` registers all 40 tools unconditionally (no tier gate)
- [x] R1-AC2: `tool_health.ts` handler body has no tier gate
- [x] R1-AC3: `data_coverage.ts` handler body has no tier gate
- [x] R1-AC4: 11 unit tests verify all 40 tools for all 3 tiers — PASS
- [x] R1-AC5: Integration test CI-safe skipIf — PASS

### R2: Implement Retrieval Engines for Stub Tools
- [x] R2-AC1: `getTool('query_tara_balam')` returns non-null — PASS
- [x] R2-AC2: `getTool('query_chandra_balam')` returns non-null — PASS
- [x] R2-AC3: `getTool('jaimini_chara_dasha')` returns non-null — PASS
- [x] R2-AC4: `getTool('jaimini_chara_dasha_full')` returns non-null — PASS
- [x] R2-AC5: All 4 tools in RETRIEVAL_TOOLS array — PASS
- [x] R2-AC6: bundle.tool_name correct for each alias — PASS
- [x] R2-AC7: FORENSIC-grounded unit tests pass (tara: Janma on birth date, chandra: Sama Rashi) — PASS
- [x] R2-AC8: 8 registry smoke tests PASS; live endpoint tests CI-safe skip

## Operator Instructions

1. Merge `fix/gismcp-r1-r2` to main (after `fix/gismcp-r3` also merged).
2. Deploy `amjis-mcp` sidecar — all 40 tools will be visible for client tier.
3. Deploy `amjis-web` portal — 4 previously-500 MCP primitives now resolve.
4. Smoke: call `tara_balam_for_native` + `chandra_balam_for_native` + `query_jaimini_chara_dasha` with a client-tier API key — all should return ok:true.
