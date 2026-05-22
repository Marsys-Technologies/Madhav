---
artifact_id: MCPT_V310_S2_CLOSE
version: 1.0
status: CLOSED
session: v3.1.0-S2
worktree: MadhavMCPT-FDN
branch: feature/mcpt-foundation
commit: 61a6ebf1
closed_at: 2026-05-22
---

# MCPT v3.1.0-S2 — Session Close Artifact

## Scope
Tier-2 composite bundles (`holistic_bundle`, `multi_school_bundle`), SSE streaming endpoint, and 5-minute content-addressable bundle cache (migration 072).

## Acceptance Criteria — All PASS

- [x] `holistic_bundle` MCP tool registered; delegates to `executeHolisticBundle`
- [x] `multi_school_bundle` MCP tool registered; delegates to `executeMultiSchoolBundle`
- [x] Both bundles execute sub-tools in parallel via `Promise.allSettled` with per-sub-tool 8s timeouts
- [x] Error isolation: failed sub-tool does not crash envelope; recorded in `bundle_entries[].error`
- [x] Bundle cache: sha256 key = bundleName + queryText + compositionParams + tier + chartId
- [x] SSE endpoint at `/api/mcp/bundles/[name]/route.ts`: streams `bundle.sub_tool.started`, `bundle.sub_tool.completed`, `bundle.sub_tool.error`, `bundle.completed` events
- [x] Migration 072 (`mcp_bundle_cache`): cache_key PK, envelope_json JSONB, expires_at, expiry index
- [x] 25 vitest tests pass (cache: 6, holistic_bundle: 7, multi_school_bundle: 6, SSE integration: 6)

## Files Delivered

- `platform-mcp/src/bundles/cache.ts`
- `platform-mcp/src/bundles/holistic_bundle.ts`
- `platform-mcp/src/bundles/multi_school_bundle.ts`
- `platform-mcp/src/bundles/index.ts`
- `platform-mcp/src/tools/holistic_bundle_tool.ts`
- `platform-mcp/src/tools/multi_school_bundle_tool.ts`
- `platform/src/app/api/mcp/bundles/[name]/route.ts`
- `platform/src/lib/mcp/bundle_adapters.ts`
- `platform/supabase/migrations/072_mcp_bundle_cache.sql`
- `platform-mcp/src/server.ts` (updated — added bundle tool registrations)
- `platform-mcp/test/bundles/cache.test.ts`
- `platform-mcp/test/bundles/holistic_bundle.test.ts`
- `platform-mcp/test/bundles/multi_school_bundle.test.ts`
- `platform-mcp/test/bundles/sse_streaming.integration.test.ts`

## Key Design Decisions

- `subset` filter on `holistic_bundle` is case-insensitive match against 8 valid sub-tool names
- Bundle cache uses HTTP calls to platform `/api/mcp/bundles/cache/*` to avoid direct DB coupling
- SSE uses Next.js `ReadableStream` with `TextEncoder`; no third-party SSE library
- `served_from_cache: boolean` surfaced in `HolisticBundleEnvelope`

## Status: CLOSED
