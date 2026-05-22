---
artifact_id: MCPT_V310_S4_CLOSE
version: 1.0
status: CLOSED
session: v3.1.0-S4
worktree: MadhavMCPT-FDN
branch: feature/mcpt-foundation
commit: 7f5dd13f
closed_at: 2026-05-22
---

# MCPT v3.1.0-S4 — Session Close Artifact

## Scope
Perf system Phases P0–P4: 4 DB migrations (073–076), 6 regex-only heuristics (NO LLM calls), nightly audit job, `tool_health` + `data_coverage` MCP tools, `get_trace` audit findings enrichment, `capabilities` resource wired to live perf data, seed file.

## Acceptance Criteria — All PASS

### P0: DB Migrations
- [x] Migration 073: `tool_execution_log` extensions — `citation_count`, `has_numerical`, `is_forward_looking`, `sanskrit_compliant`, `audit_flagged`; partial index on unaudited ok rows
- [x] Migration 074: `mcp_audit_findings` (id, trace_id, tool_name, check_class×6, severity, description, evidence JSONB, resolved_at, resolved_by) + `audit_job_runs`
- [x] Migration 075: `mcp_predictions` extensions (resolved, brier_score) + `mcp_prediction_outcomes` (outcome_text, outcome_occurred, outcome_date, calibration_note)
- [x] Migration 076: `data_source_expected` (tool_name, category, expected/actual rows, backfill_phase) + `tool_caveats` (caveat_class, severity, active)

### P1: Heuristics (CRITICAL: NO LLM CALLS)
- [x] `extract_citations.ts`: patterns for SIG.MSR.NNN, [^N], LEL.E.NNN, FORENSIC.§N.N, → SIG.MSR.NNN
- [x] `extract_numerical_claims.ts`: degrees (°, ′, ″), virupa, points/rupas, score/confidence
- [x] `forward_looking.ts`: future modal keywords, prospective astro keywords, time-horizon patterns
- [x] `sanskrit_glossing.ts`: 40+ Sanskrit terms, checks for unglossed terms (client-tier only)
- [x] `layer_attribution.ts`: L1 vs L2.5 keyword mixing detection
- [x] `is_non_factual.ts`: factual indicators (JSON, table) vs interpretive phrases + sentence/table ratio
- [x] `grep -rn "openai|anthropic|gemini" platform/src/lib/perf/heuristics/` → EMPTY (verified)

### P2: Nightly Audit Job
- [x] `audit_nightly.ts`: `runAuditChecks(row)` exported + pure (no DB, no fetch)
- [x] `runNightlyAudit(config)`: fetches 24h of unaudited ok rows, runs 6 checks, writes findings, marks audit_flagged
- [x] `auditCronHandler()`: Cloud Run scheduler entry point (03:00 UTC)
- [x] env vars read at call time inside `dbQuery()` (not module-level) for test isolation
- [x] dry_run mode: runs checks, does NOT write to DB
- [x] Graceful DB unavailability: returns `{status:'complete', traces_examined:0}` when no credentials

### P3: tool_health + data_coverage MCP Tools
- [x] `/api/mcp/health/tools` endpoint: tier gate (403 for client/public_redacted); returns tool health JSON
- [x] `/api/mcp/health/coverage` endpoint: tier gate (403 for client/public_redacted); returns coverage array
- [x] `tool_health` MCP tool: registered, tier-gated, calls platform health endpoint
- [x] `data_coverage` MCP tool: registered, tier-gated, applies `tool_filter`, calls coverage endpoint
- [x] `get_trace` extended with `audit_findings` fetch from `/api/mcp/health/audit-findings?trace_id=`

### P4: Capabilities Resource + Seed
- [x] `capabilities.ts` updated: `fetchToolHealth()` + `fetchDataCoverage()` at attach; `buildCapabilitiesMarkdown()`; fallback to PLACEHOLDER on error
- [x] `data_source_expected_seed.sql`: 23 chart_facts categories, MSR (573), panchanga (73414), LEL (36); 4 tool_caveats for pending v3.3 backfills

### Tests
- [x] `platform/test/perf/heuristics.test.ts`: 41 tests PASS
- [x] `platform/test/perf/audit_nightly.test.ts`: 7 tests PASS (pure runAuditChecks + dry_run schema)
- [x] `platform-mcp/test/tool_health.integration.test.ts`: 5 tests PASS
- [x] `platform-mcp/test/data_coverage.integration.test.ts`: 6 tests PASS
- [x] platform total: 48 perf tests PASS
- [x] platform-mcp total: 75 tests PASS

## Files Delivered

### Migrations
- `platform/supabase/migrations/073_perf_log_extensions.sql`
- `platform/supabase/migrations/074_audit_findings.sql`
- `platform/supabase/migrations/075_prediction_outcomes.sql`
- `platform/supabase/migrations/076_data_source_expected_and_caveats.sql`

### Heuristics
- `platform/src/lib/perf/heuristics/extract_citations.ts`
- `platform/src/lib/perf/heuristics/extract_numerical_claims.ts`
- `platform/src/lib/perf/heuristics/forward_looking.ts`
- `platform/src/lib/perf/heuristics/sanskrit_glossing.ts`
- `platform/src/lib/perf/heuristics/layer_attribution.ts`
- `platform/src/lib/perf/heuristics/is_non_factual.ts`

### Audit Job
- `platform/src/lib/perf/audit_nightly.ts`
- `platform/src/lib/perf/mv_refresh.ts`

### Platform Endpoints
- `platform/src/app/api/mcp/health/tools/route.ts`
- `platform/src/app/api/mcp/health/coverage/route.ts`

### MCP Tools (updated)
- `platform-mcp/src/tools/tool_health.ts`
- `platform-mcp/src/tools/data_coverage.ts`
- `platform-mcp/src/tools/get_trace.ts` (extended)
- `platform-mcp/src/server.ts` (updated)

### Resources (updated)
- `platform-mcp/src/resources/capabilities.ts` (live perf data)

### Seeds
- `00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql`

### Tests
- `platform/test/perf/heuristics.test.ts`
- `platform/test/perf/audit_nightly.test.ts`
- `platform-mcp/test/tool_health.integration.test.ts`
- `platform-mcp/test/data_coverage.integration.test.ts`

## Critical Invariant Verified
`grep -rn "openai\|anthropic\|gemini\|@google/generative-ai" platform/src/lib/perf/heuristics/` returns EMPTY.
All 6 audit checks are pure regex/keyword heuristics. No LLM calls anywhere in the perf subsystem.

## Status: CLOSED
