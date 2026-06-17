---
title: "BHISMA Wave 2 — Session S-C: Database Migration Apply"
brief_id: BHISMA_SC
version: 1.0
status: COMPLETE
created_date: 2026-05-03
session_id: BHISMA-W2-S-C
executor: claude-opus-4-6
active_phase: "BHISMA Wave 2 — Migrations 032–036 live apply"
isolation_tier: BHISMA_ONLY
blocked_by: BHISMA_SA, BHISMA_SB
must_complete_before: BHISMA_SD
---

# BHISMA Wave 2 — Session S-C
## Database Migration Apply

**PREREQUISITE (native action required before starting):**
Start the Cloud SQL Auth Proxy in a terminal:
```bash
cloud-sql-proxy --port 5433 madhav-astrology:asia-south1:amjis-postgres
# Leave this terminal running throughout this session.
# NOTE: proxy runs on 5433 (not 5432) — local Postgres holds 5432.
```

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

S-A and S-B are both COMPLETE. Migrations 032–036 in `platform/migrations/` are written but not yet applied to the live Cloud SQL instance. This session applies them, verifies schema, and validates the monitoring tables are live and accepting writes.

**LLM_FIRST_PLANNER_ENABLED is NOT flipped in this session.** That is a native decision pending Lever 2 re-evaluation after NIM recovery (see §5).

---

## §1 Pre-Work Audit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# Verify proxy is reachable
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "\l" 2>&1 | head -10

# List pending migrations (check which have already been applied vs pending)
ls migrations/ | sort | tail -20

# Confirm the 5 target migrations exist
ls migrations/032_llm_call_log.sql
ls migrations/033_query_plan_log.sql
ls migrations/034_tool_execution_log.sql
ls migrations/035_context_assembly_log.sql
ls migrations/036_analytics_views.sql

# Load DB URL from .env.local
export DB_URL=$(grep '^DATABASE_URL=' .env.local | cut -d'=' -f2-)

# Check current DB schema — are any of these tables already present?
psql "$DB_URL" \
  -c "\dt *log*" \
  -c "\dt *plan*" \
  -c "\dt *analytics*" 2>&1

# Find the migration runner (drizzle-kit, prisma migrate, or raw psql)
cat package.json | grep -A2 '"migrate"'
ls drizzle.config.ts 2>/dev/null || ls prisma/schema.prisma 2>/dev/null || echo "No ORM config found"
```

**If any of the 5 target tables already exist**: verify schema matches the migration file before proceeding. If schema matches → table was already applied; skip that migration. If schema differs → report to native; do NOT overwrite with ALTER TABLE.

---

## §2 Scope of Work

### Apply Migrations 032–036

Apply each migration in order. Use the project's existing migration mechanism. If the project uses raw psql (most likely based on prior session evidence of numbered SQL files):

```bash
DB_URL=$(grep '^DATABASE_URL=' .env.local | cut -d'=' -f2-)

# Apply in strict order; stop immediately if any migration fails
psql $DB_URL -f migrations/032_llm_call_log.sql 2>&1 && echo "032 OK"
psql $DB_URL -f migrations/033_query_plan_log.sql 2>&1 && echo "033 OK"
psql $DB_URL -f migrations/034_tool_execution_log.sql 2>&1 && echo "034 OK"
psql $DB_URL -f migrations/035_context_assembly_log.sql 2>&1 && echo "035 OK"
psql $DB_URL -f migrations/036_analytics_views.sql 2>&1 && echo "036 OK"
```

If the project uses a migration runner (drizzle, prisma), use that instead and confirm all 5 are marked applied.

### Verify Schema

After applying, verify each table and its key columns:

```bash
psql "$DB_URL" -c "
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN
  ('llm_call_log','query_plan_log','tool_execution_log',
   'context_assembly_log')
ORDER BY table_name, ordinal_position;" 2>&1
```

Confirm:
- `llm_call_log` has columns: `query_id`, `call_stage`, `model_id`, `input_tokens`, `output_tokens`, `reasoning_tokens`, `latency_ms`, `cost_usd`, `fallback_used`, `created_at`
- `query_plan_log` has columns: `query_id`, `raw_plan_json` (JSONB), `tool_count`, `planning_confidence`, `fallback_used`, `parsing_success`, `parse_error`, `planner_model_id`, `planner_latency_ms`, `created_at`
- `tool_execution_log` has columns: `query_id`, `tool_name`, `params_json`, `execution_status`, `rows_returned`, `latency_ms`, `data_asset_id`, `error_code`, `created_at`
- `context_assembly_log` has columns: `query_id`, `l1_tokens`, `l2_signal_tokens`, `l2_pattern_tokens`, `l4_tokens`, `vector_tokens`, `cgm_tokens`, `total_tokens`, `citation_count`, `b3_compliant`, `created_at`

### Verify Analytics Views (036)

```bash
psql "$DB_URL" -c "\dv" 2>&1 | grep -E "cost_by_model|tool_health|grounding_health"
psql "$DB_URL" -c "SELECT * FROM cost_by_model LIMIT 1;" 2>&1
psql "$DB_URL" -c "SELECT * FROM tool_health LIMIT 1;" 2>&1
psql "$DB_URL" -c "SELECT * FROM grounding_health LIMIT 1;" 2>&1
```

Views should return 0 rows (no data yet) but must not error.

### Smoke-Write Test

Insert a test row into each table to confirm the instrumentation code from S-A will be able to write:

```bash
psql "$DB_URL" -c "
INSERT INTO llm_call_log
  (query_id, call_stage, model_id, input_tokens, output_tokens,
   reasoning_tokens, latency_ms, cost_usd, fallback_used, created_at)
VALUES ('smoke-test-sc', 'test', 'test-model', 100, 50, NULL, 200, 0.001, false, NOW());
SELECT count(*) FROM llm_call_log WHERE query_id='smoke-test-sc';
DELETE FROM llm_call_log WHERE query_id='smoke-test-sc';
" 2>&1

psql "$DB_URL" -c "
INSERT INTO query_plan_log
  (query_id, raw_plan_json, tool_count, planning_confidence,
   fallback_used, parsing_success, parse_error, planner_model_id,
   planner_latency_ms, created_at)
VALUES ('smoke-test-sc', '{\"test\":true}', 0, NULL, false, true, NULL, 'test-model', 100, NOW());
SELECT count(*) FROM query_plan_log WHERE query_id='smoke-test-sc';
DELETE FROM query_plan_log WHERE query_id='smoke-test-sc';
" 2>&1
```

---

## §3 File Scope

### may_touch
```
platform/migrations/032_llm_call_log.sql        [read-only — apply only, do not modify]
platform/migrations/033_query_plan_log.sql       [read-only]
platform/migrations/034_tool_execution_log.sql   [read-only]
platform/migrations/035_context_assembly_log.sql [read-only]
platform/migrations/036_analytics_views.sql      [read-only]
```

### must_not_touch
```
# Everything — this is a DB-only session
platform/src/**
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
CLAUDE.md
/Users/Dev/Vibe-Coding/Apps/Ustad/**
```

---

## §4 Acceptance Criteria

- [ ] Cloud SQL Auth Proxy reachable at 127.0.0.1:5433 (verified in §1)
- [ ] All 5 migrations applied without error (032–036)
- [ ] All 4 monitoring tables exist with correct schema (column names and types match §2)
- [ ] Analytics views exist (cost_by_model, tool_health, grounding_health) and return without error
- [ ] Smoke-write INSERT/SELECT/DELETE passes for `llm_call_log` and `query_plan_log`

---

## §5 Open Decision Note (do NOT act on — for native awareness)

**Lever 2 (LLM_FIRST_PLANNER_ENABLED):** EVAL-2 was BLOCKED in S-B because the NIM provider (meta/llama-3.1-8b-instruct) returned HTTP 500 on all 25 golden set queries. This is provider health, not planner quality. Scores recall=0.000 / precision=0.000 are meaningless in this state.

**Native action required before Lever 2 can be evaluated:**
1. Verify NIM provider health via GCP console or `curl` against the NIM endpoint
2. When NIM is healthy: re-run `npm run eval:planner` from `platform/`
3. If tool_recall ≥ 0.80 AND tool_precision ≥ 0.90 → consider flipping `LLM_FIRST_PLANNER_ENABLED=true` in `.env.production`
4. If below threshold → review specific failure cases in `platform/tests/eval/` results JSON

This session (S-C) does NOT flip the flag.

---

## §6 Hard Constraints

1. **Never ALTER TABLE** — if a table already exists with a different schema, stop and report. Do not attempt ALTER.
2. **Never modify migration files** — they are the source of truth. If a migration fails, report the exact error; do not edit the SQL to work around it.
3. **No application code changes** — this session touches the database only.
4. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §7 How to Start

**First:** Start Cloud SQL Auth Proxy (see §0 prerequisite above).

Then open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_SC_v1_0.md and execute it.
```
