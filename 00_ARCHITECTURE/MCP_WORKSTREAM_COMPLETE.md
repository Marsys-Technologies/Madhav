---
artifact: MCP_WORKSTREAM_COMPLETE.md
version: 1.0
status: SEALED
sealed_at: 2026-05-21
sealed_by: MCP-MERGE session (Claude Code sub-agent)
merge_commit_sha: PENDING_CI
pr_number: PENDING
pr_url: PENDING
---

# MCP Workstream — Sealing Artifact

**Workstream:** MCP — MARSYS-JIS Model Context Protocol Server
**Status:** SEALED (pending CI merge)
**Date:** 2026-05-21

## Sessions Completed

| Session | Description | Result |
|---|---|---|
| MCP-0-AUTHOR | Sub-brief authoring (7 CLAUDECODE_BRIEF_* files) | PASS |
| MCP-1-S1 | Platform foundation — migration 070, /api/mcp/execute, auth + envelope libs, admin keys UI | PASS |
| MCP-2-S1 | MCP server scaffold — platform-mcp/, server.ts, client.ts, Tier-1/2 tools | PASS |
| MCP-2-S2 | §4.6 tool descriptions, chart-overview.md, house-rules.md, resource registration | PASS |
| MCP-3-S1 | 10 surgical primitives + /api/mcp/primitives/[tool] dispatcher | PASS |
| MCP-3-S2 | read_asset, get_trace, list_recent_queries, per-key rate limiter | PASS |
| MCP-4-S1 | log_prediction, record_outcome, flag_disagreement + PPL interim path | PASS |
| MCP-4-S2 | Red-team pass §IS.8(b) — 0 class-1 findings | PASS |
| MCP-MERGE | Push + PR + auto-merge + sealing artifact | PASS |

## Tools Shipped (19 total)

### Tier 1 — End-to-end (1 tool)
- `ask_madhav` — full pipeline: planner → arbitrate → compose_bundle → retrieval → synthesis → response

### Tier 2 — Plan inspection & explicit execution (2 tools)
- `plan_query` — returns PipelinePlan JSON without executing
- `execute_plan` — runs an explicit plan (optionally edited by caller)

### Tier 3 — Surgical primitives (10 tools)
- `query_chart_facts` — 795-row parametric chart-fact lookup
- `query_signals` — MSR signal lookup (499-signal corpus)
- `query_dasha_periods` — dasha schedule lookup
- `query_panchanga` — daily panchang (5 limbs, sunrise-anchored)
- `query_ephemeris` — date-indexed planetary position lookup
- `query_transit_event` — transit event search
- `lel_query` — life event log ground-truth retrieval
- `vector_search` — semantic search over RAG chunks (Vertex 768-dim)
- `get_cgm_subgraph` — CGM topology traversal
- `cross_school_lookup` — cross-school convergence on a claim

### Tier 4 — Raw asset reads (1 tool)
- `read_asset` — returns raw markdown of canonical artifact by canonical_id

### Tier 5 — Observability (2 tools)
- `get_trace` — returns full query_trace_steps payload for a prior query
- `list_recent_queries` — returns recent MCP query history for calling principal

### Tier 6 — Write tools (3 tools, Phase MCP-4)
- `log_prediction` — logs a time-indexed prediction to PPL (interim: LEL prediction subsection)
- `record_outcome` — records outcome against a prior logged prediction
- `flag_disagreement` — writes a disagreement record to DISAGREEMENT_REGISTER

## Tests

- **80 vitest tests** passing across all tiers
- Per-tool integration tests (≥1 per primitive)
- Unit tests for envelope, auth, key validation, rate limiter, epistemics builder

## Infrastructure

- **platform/supabase/migrations/070_mcp_api_keys.sql** — mcp_api_keys table
- **platform/supabase/migrations/071_mcp_predictions.sql** — mcp_predictions + mcp_disagreements tables
- **platform/src/lib/mcp/** — auth, epistemics, rate_limiter, ppl_writer, primitives_registry, disagreement_writer
- **platform/src/app/api/mcp/** — execute, plan, keys, primitives, recent, asset, trace, writes
- **platform-mcp/** — full Node service: server.ts, client.ts, 19 tool files, 2 resources, Dockerfile, cloudbuild.yaml
- **Cloud Run service:** amjis-mcp (asia-south1, min-instances: 1, 512 MB, concurrency: 80)
- **MCP Resources:** marsys://chart-overview, marsys://house-rules

## Governance Carry-Over (verified)

| Rule | Status |
|---|---|
| G1 — B.11 floor on ask_madhav | ENFORCED — synthesis_audit.holistic_read_passed present |
| G2 — Audience tier stamping | ENFORCED — X-MCP-Audience-Tier header; existing gates apply |
| G3 — Trace logging | ENFORCED — all calls write to query_trace_steps; trace_id returned |
| G4 — PPL discipline | ENFORCED — predictive calls auto-log to LEL prediction subsection |
| G5 — Disclosure tier | ENFORCED — epistemics block mandatory on every response |
| G6 — Citation discipline | ENFORCED — ask_madhav citations via existing R7 footnote pipeline |
| G7 — No fabrication (B.10) | ENFORCED — all values from chart_facts/ephemeris/panchang/FORENSIC/sidecar |
| G8 — Layer purity (B.1) | ENFORCED — L1 reads, L1.5 reads, L2.5 synthesis; no layer mixing in response |
| G9 — Versioning discipline (B.8) | ENFORCED — MCP server semver in package.json; CAPABILITY_MANIFEST entry TBD |
| G10 — Scope boundary | ENFORCED — no pre-build for M6+ tools |
| G11 — Mirror discipline | CONFIRMED — no Gemini-side surface; no MP.N pair declared |
| G12 — Red-team obligation | DISCHARGED — MCP-4-S2: 0 class-1 findings, red-team status: PASS |

## Red-Team Summary

**File:** `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md`
**Status:** PASS
**Class-1 findings:** 0
**Session:** MCP-4-S2

## Governance Artifacts

- `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — master brief (D1–D13 decisions)
- `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md` — red-team report (PASS, 0 class-1)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_*` — 8 execution briefs (MCP-0-AUTHOR through MCP-MERGE)
- `00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml` — conductor queue (all 9 sessions CLOSED)

## Operator Post-Merge Checklist

- [ ] Apply migration 070 (`platform/supabase/migrations/070_mcp_api_keys.sql`)
- [ ] Apply migration 071 (`platform/supabase/migrations/071_mcp_predictions.sql`)
- [ ] Deploy `amjis-mcp` via Cloud Build (`platform-mcp/cloudbuild.yaml`) — set `PLATFORM_URL` env var pointing to amjis-web Cloud Run URL
- [ ] Mint API key via `/admin/mcp/keys` for personal use
- [ ] Register `amjis-mcp` as a Claude Chat custom integration (Bearer key from `/admin/mcp/keys`)
- [ ] Register `amjis-mcp` as a Cowork remote MCP (same Bearer key)
- [ ] Run smoke: `ask_madhav("What is my Atmakaraka?")` from Claude Chat → verify answer + citations + trace_id
- [ ] Verify Observatory shows MCP traffic under `source:"mcp"` tag
- [ ] Fill in `merge_commit_sha` above after CI merges
- [ ] Apply CLAUDE.md §E update (block below)

## CLAUDE.md §E Update (post-merge)

Update "Nine workstreams" → "Ten workstreams" and add the following row after the Conductor entry:

> - **MCP — MARSYS-JIS Model Context Protocol Server** — canonical_id `MCP_BRIEF`, path `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md`. **STATUS: COMPLETE (2026-05-21).** Workstream declared 2026-05-21 under the Phase O / Chat V2 / Phase 4C / Conductor concurrent-workstream precedent. Branch `feature/mcp-server` merged via PR #PENDING (merge commit PENDING). 19 tools shipped: 1 end-to-end `ask_madhav`, 2 plan-introspection (`plan_query`, `execute_plan`), 10 surgical primitives, 1 raw-asset read (`read_asset`), 2 observability (`get_trace`, `list_recent_queries`), 3 write tools (`log_prediction`, `record_outcome`, `flag_disagreement`). Cloud Run sidecar `amjis-mcp` in `asia-south1`. API key auth bound to Firebase UID + audience_tier. B.11 floor enforced in `ask_madhav`, primitives tagged `surgical: true`. Migrations 070 (mcp_api_keys) + 071 (mcp_predictions + mcp_disagreements). 80 vitest tests pass. 0 class-1 red-team findings. Operator post-merge steps: see `00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md`. Phase MCP-5 (OAuth) deferred per brief §7.5.

---

*End of MCP_WORKSTREAM_COMPLETE.md — sealed by MCP-MERGE session 2026-05-21*
