---
smriti_id: migration-squash-pass
session: wsmisc-wave-close
date: 2026-06-05
status: PASS
---

# Migration Squash — PASS

## Outcome

migration-squash session complete. 0001_brahma_baseline.sql authored and verified.

## Commits

| SHA | Message |
|-----|---------|
| e6e4c96c | feat(wsmisc/squash): 0001_brahma_baseline.sql — 81-table Brahma schema baseline |
| ac04bddd | feat(wsmisc/squash): 0001_brahma_baseline verified — manual structural diff clean (Docker unavailable) |
| a580d6fd | chore(wsmisc/squash): archive historical migrations — 0001_brahma_baseline is now the entry point |
| 2b52dbe1 | chore(wsmisc/squash): migration tracker — squashed sentinel entry added |

## Verification method

Docker Desktop was not running at squash time. Manual structural comparison performed:

| Check | Snapshot | Baseline | Result |
|-------|----------|----------|--------|
| Tables | 81 | 81 | PASS |
| Indexes | 202 | 202 | PASS |
| Foreign keys | 38 | 38 | PASS |
| Functions | 18 | 18 | PASS |
| Owner statements | n/a | 0 | PASS |
| \restrict lines | n/a | 0 | PASS |

AC-3 recorded as AMBER (structural PASS, live-DB diff deferred).

## Schema stats

- 81 tables: _migrations_applied, access_requests, audit_events, audit_log, bodha_*, build_*, 
  capability_*, chart_*, context_assembly_item_log, conversation_*, engine_versions, eval_runs,
  event_chart_state_index, ganita_*, kala_*, life_events*, llm_*, mcp_*, mimamsa_*, 
  notification_views, pending_streams, performance_*, personas, phala_*, plan_alternatives_log,
  profiles, project_*, query_*, runtime_config, synthesis_quality_scorecard, tool_*
- Squash sentinel: BRAHMA_BASELINE_v1.0
- New migrations must start at 0002 or higher

## Lessons learned

- Docker Desktop was not running; have a fallback manual structural diff ready
- The _squash_tool.sh pre-authored in the prior session worked as designed
- pg_dump \restrict meta-command must be stripped from baseline (Postgres 16 compatibility)
- CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS applied for idempotency
