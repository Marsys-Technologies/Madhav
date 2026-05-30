---
artifact_id: MCPT_V310_S3_CLOSE
version: 1.0
status: CLOSED
session: v3.1.0-S3
worktree: MadhavMCPT-FDN
branch: feature/mcpt-foundation
commit: 6ce019f3
closed_at: 2026-05-22
artifact: MCPT_V310_S3_CLOSE
---

# MCPT v3.1.0-S3 — Session Close Artifact

## Scope
5 MCP auto-loaded resources (`chart-snapshot` NEW, `chart-overview`, `house-rules`, `capabilities`, `school-conventions`); tier-conditioned house-rules variants; regenerated tool descriptions.

## Acceptance Criteria — All PASS

- [x] `marsys://chart-snapshot` resource NEW: parallel fetch of `query_chart_facts`, `query_dasha_periods(active_only:true)`, `query_panchanga(today)` at session attach; builds planetary positions table + active dasha + current panchang
- [x] `marsys://chart-overview` resource: loads from static `chart-overview.md` fallback
- [x] `marsys://house-rules` resource: 4 tier variants loaded at startup; `registerHouseRules` serves super_admin variant; `getHouseRulesForTier(tier)` exported
- [x] House-rules variants cover: super_admin (full + audit), acharya (no audit commentary), client (≤800 tokens, Sanskrit glossing required), public_redacted (redaction policy)
- [x] `marsys://capabilities` resource: S3 placeholder with hardcoded tool list + "perf data pending S4 wiring" note
- [x] `marsys://school-conventions` resource: 4 schools, classical anchors, known disagreements, convergence_score table, tool routing by school
- [x] `resources/index.ts` rewritten: imports + calls all 5 `register*` functions in `registerResources(server)`
- [x] 30 vitest tests pass (resources.test.ts)

## Files Delivered

- `platform-mcp/src/resources/chart_snapshot.ts`
- `platform-mcp/src/resources/chart_overview.ts` (rewritten)
- `platform-mcp/src/resources/house_rules.ts` (rewritten)
- `platform-mcp/src/resources/house_rules_variants/super_admin.md`
- `platform-mcp/src/resources/house_rules_variants/acharya.md`
- `platform-mcp/src/resources/house_rules_variants/client.md`
- `platform-mcp/src/resources/house_rules_variants/public_redacted.md`
- `platform-mcp/src/resources/capabilities.ts` (S3 placeholder)
- `platform-mcp/src/resources/school_conventions.ts`
- `platform-mcp/src/resources/index.ts` (rewritten)
- `platform-mcp/test/resources/resources.test.ts`

## Key Design Decisions

- `house-rules` variants are markdown files loaded via `fs.readFileSync` at startup to avoid per-request I/O
- `chart-snapshot` is the only resource that makes live tool calls at attach time; all others are static or near-static
- `capabilities` resource intentionally left as placeholder in S3 to be wired to live perf data in S4
- `school-conventions` is ~2.5k tokens — within auto-load budget per architecture spec

## Status: CLOSED
