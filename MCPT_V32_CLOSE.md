---
artifact: MCPT_V32_CLOSE.md
version: 1.0
status: CLOSED
project: MCP Transformation
phase: v3.2 — Quality Tightening
sessions: v3.2-S1, v3.2-S2, v3.2-S3, v3.2-S4, v3.2-S5 (10 phases total)
closed_at: '2026-05-23'
author: Claude Code (MCPT-V32-CLOSEOUT session)
---

# v3.2 Phase Close — Quality Tightening

## Result: PASS

All 10 phases of MCPT v3.2 Quality Tightening complete. Production live at
`amjis-mcp-00011-9zv` (tag `mcpt-v32-prod` @ b9f372a3). R3 routing eval PASS
(93.3%, 28/30 prompts — first live eval; prior runs were dry-run only).

---

## Acceptance Summary

| Criterion | Status |
|---|---|
| Tests: 257/257 | PASS |
| Bench: canonical_d9_workflow -60% round-trips, -71% bytes | PASS |
| Accuracy: 100% cross-scenario agreement (2,717 chart_facts) | PASS |
| R3 routing eval: 93.3% live (goal ≥80%) | PASS |
| Phase 9.5b: +93.3pp vs 0% baseline (goal ≥15pp) | PASS |
| Prod revision 100% traffic | PASS |

---

## User-Facing Changes for External MCP Clients

MCPT v3.2 changed the description strings emitted by the MCP `list_tools` endpoint. External clients (Claude Desktop, Claude Code in IDEs, Cowork, third-party MCP consumers) may have cached the v3.1 descriptions and will benefit from re-fetching `list_tools` to pick up the new versions.

### What changed

1. **All 21 tools** now use a standardized description format produced by `description_builder.ts`. Each description leads with a single disambiguator sentence and includes a "When to prefer" section. Total length ≤ 1200 chars.

2. **`data_coverage` description** — removed false claim that "KP, Tajaka, Shadbala, Ashtakavarga categories are pending v3.3 backfill." All v3.3 categories have been populated since 2026-05-22 (`MCPT_V33_CLOSE.md`). The description now accurately reports current state.

3. **`tool_health` data_note** — removed the fallback string `"Apply migrations 073-076 and run nightly audit"`. Migrations 073-076 were applied 2026-05-22; the tool now returns real metrics from the materialized views.

4. **New tool: `chart_summary`** — wide-by-default tool that returns the canonical 30-60-fact bundle in one round-trip. Prefer this over `query_chart_facts` when interpreting a chart end-to-end. Saves ~60% of round-trips on typical workflows.

5. **`query_chart_facts`** — gained two new optional parameters:
   - `divisional_chart: string` — filter to a specific divisional (e.g. "D9"). Prunes irrelevance.
   - `categories: string[]` — batch fetch multiple categories in one call.

6. **Tier-aware ordering** — `list_tools` now varies tool ordering per `audience_tier`:
   - `super_admin` and `acharya`: full catalog, `chart_summary` first.
   - `client`: ops tools (`data_coverage`, `tool_health`, `log_prediction`, `record_outcome`, `flag_disagreement`) hidden.

7. **Trace alignment** — `list_recent_queries` now returns MCP-facing tool names (e.g. `query_chart_facts`) rather than retrieval-side internal names (e.g. `chart_facts_query`). `get_trace(name)` works with either form. `query_summary` now carries real param representation.

### Recommended client action

- Clients that cache `list_tools` for the session lifetime: re-fetch once to pick up new descriptions. No code changes required.
- Clients that fetch `list_tools` per-session anyway (most): no action.
- Clients relying on retrieval-side tool names in trace audits: update to expect MCP-facing names (the rename map in `platform/src/lib/mcp/primitives_registry.ts:47-59` documents the alias).

### No behavior change

Tool semantics, request/response shapes, error formats, and authentication are unchanged. Only descriptions and a few additive parameters changed.
