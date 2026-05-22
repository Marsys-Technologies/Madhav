---
artifact: CLAUDECODE_BRIEF_MCPT_V310_S4_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.1.0-S4
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN
branch: feature/mcpt-foundation
depends_on: [v3.1.0-S1]
parallel_with: [v3.1.0-S2, v3.1.0-S3]
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: Perf system + operator-side nightly audit subsystem (Phases P0–P4 of perf brief)
migration_numbers: [073, 074, 075, 076]
---

# v3.1.0-S4 — Perf System + Audit Subsystem

You are a Claude Code sub-agent on WT-A. Implements the perf brief's Phases P0–P4: source-table extensions, materialized views, MCP tools (`tool_health` + `data_coverage`), capabilities resource wiring (replacing S3's placeholder), and the operator-side nightly audit job that replaces v3.0's self-audit.

Read: `MCP_PERF_SYSTEM_BRIEF_2026-05-22.md §4 (data structures), §5 (audit subsystem), §6 (agent-facing tools), §11 Phase P0–P4`; `MCP_ARCH_v3_PROPOSAL_2026-05-22.md §3.5 (perf tools), §7.6 (audit subsystem)`; parent brief §4 / v3.1.0-S4.

## §1 — Scope

Phases P0–P4 of perf brief: schema extensions (P0), materialized views (P1), MCP tools (P2), capabilities resource wiring (P3), audit job (P4). P5 (operator dashboard) is S5. P6 (calibration views) is v3.4.

## §2 — Files in scope

```
platform/supabase/migrations/073_perf_log_extensions.sql                 # tool_execution_log + 5 columns
platform/supabase/migrations/074_audit_findings.sql                      # mcp_audit_findings + audit_job_runs
platform/supabase/migrations/075_prediction_outcomes.sql                 # mcp_prediction_outcomes + mcp_predictions extensions
platform/supabase/migrations/076_data_source_expected_and_caveats.sql    # data_source_expected + tool_caveats tables
platform/src/lib/perf/mv_refresh.ts                                      # cron entry-point for MV refresh
platform/src/lib/perf/audit_nightly.ts                                   # the audit job
platform/src/lib/perf/heuristics/extract_citations.ts                    # regex extractor
platform/src/lib/perf/heuristics/extract_numerical_claims.ts             # regex extractor
platform/src/lib/perf/heuristics/forward_looking.ts                      # keyword + tense detector
platform/src/lib/perf/heuristics/sanskrit_glossing.ts                    # client-tier compliance heuristic
platform/src/lib/perf/heuristics/layer_attribution.ts                    # L1/L2.5 mixing detector
platform/src/lib/perf/heuristics/is_non_factual.ts                       # response-shape heuristic
platform/src/app/api/mcp/health/tools/route.ts                           # new endpoint
platform/src/app/api/mcp/health/coverage/route.ts                        # new endpoint
platform-mcp/src/tools/tool_health.ts                                    # new MCP tool
platform-mcp/src/tools/data_coverage.ts                                  # new MCP tool
platform-mcp/src/tools/get_trace.ts                                      # extend to include audit findings
platform-mcp/src/resources/capabilities.ts                               # replace S3 placeholder; wire real perf data
00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql          # seed file
platform/test/perf/**                                                    # new tests
platform-mcp/test/tool_health.integration.test.ts                        # new
platform-mcp/test/data_coverage.integration.test.ts                      # new
```

## §3 — Files NOT in scope

```
platform/src/app/admin/mcp/health/**                                     # S5 territory
platform-mcp/src/bundles/**                                              # S2 territory
platform-mcp/src/resources/house_rules*, chart_*, school_conventions     # S3 territory
01_FACTS_LAYER/**                                                        # no FORENSIC changes
```

## §4 — Per-migration spec

Migration schemas are in perf brief §4.1–§4.4 verbatim. Each migration includes a rollback (`DOWN`) script. Apply sequentially: 073 → 074 → 075 → 076.

## §5 — Audit job specification

`platform/src/lib/perf/audit_nightly.ts` runs the 6 checks per perf brief §5.1. Cron at 03:00 UTC via existing Cloud Run scheduler. Inputs: last 24h of traces + response transcripts (Cowork-sourced, where available). Outputs: rows in `mcp_audit_findings`.

Each heuristic file (§2 list) is a single function exporting:

```ts
export function extractCitations(responseText: string): string[] { /* regex: [\^N], SIG.MSR.NNN, LEL.E.NNN, FORENSIC.§N.N */ }
export function extractNumericalClaims(responseText: string): NumericalClaim[] { /* regex: \d+\.?\d*\s*(virupa|degrees|rupas|points)? */ }
export function isForwardLooking(responseText: string): boolean { /* keyword + tense */ }
export function isNonFactualResponse(responseText: string, questionText: string): boolean { /* response length + question shape */ }
// etc.
```

Heuristics-only. No LLM calls in the audit path. Conformance verified by grep test (`grep -rn "openai\|anthropic\|gemini" platform/src/lib/perf/heuristics/` returns nothing).

## §6 — `tool_health` + `data_coverage` MCP tools

Schemas per perf brief §6.1 and §6.2. Tier-gating enforced at endpoint level: super_admin + acharya = 200; client = 403 with house-rules reference.

`get_trace` extension: return now includes `audit_findings: [{class, severity, description, attached_at}]` for the trace. Findings populated by the audit job at 03:00 UTC; traces from "today" may not yet have findings (acceptable).

## §7 — `capabilities` resource wiring (replaces S3 placeholder)

Generator now calls `tool_health()` + `data_coverage()` at attach time to build the markdown structure in perf brief §6.3. Tier-conditioned: super_admin + acharya see full snapshot; client sees tool names + caveats only.

## §8 — Acceptance criteria (AC.S4.1 through AC.S4.8)

Per parent brief §4 / v3.1.0-S4.

## §9 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  test -f platform/supabase/migrations/073_perf_log_extensions.sql && \
  test -f platform/supabase/migrations/074_audit_findings.sql && \
  test -f platform/supabase/migrations/075_prediction_outcomes.sql && \
  test -f platform/supabase/migrations/076_data_source_expected_and_caveats.sql && \
  test -f platform/src/lib/perf/audit_nightly.ts && \
  test -f platform-mcp/src/tools/tool_health.ts && \
  test -f platform-mcp/src/tools/data_coverage.ts && \
  ! grep -rn "openai\|anthropic\|gemini\|@google/generative-ai" platform/src/lib/perf/heuristics/ && \
  cd platform && npm test -- perf/ 2>&1 | tail -10 && \
  cd ../platform-mcp && npm test -- tool_health\|data_coverage 2>&1 | tail -10
```

## §10 — Sealing artifact

`00_ARCHITECTURE/MCPT_V310_S4_CLOSE.md`. Body: heuristic catalog with characterized false-positive rate per heuristic, migration application evidence, audit-job first-run output.

---

*End of CLAUDECODE_BRIEF_MCPT_V310_S4_v1_0.md.*
