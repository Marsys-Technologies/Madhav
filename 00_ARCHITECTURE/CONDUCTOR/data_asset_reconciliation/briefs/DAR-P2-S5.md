---
session_id: DAR-P2-S5
phase: 2
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md  # create
must_not_touch:
  - platform/migrations/116_trace_mcp_tool_column.sql
  - platform/migrations/117_audience_tier_acharya_enum.sql
  - platform/src/
  - 025_HOLISTIC_SYNTHESIS/
---

# DAR-P2-S5: Migration safety analysis + HG-1 apply instructions

## Context

Migrations 116 and 117 were authored (per the DAR audit) but never applied to production.
This session reads both migration files, verifies their safety (idempotency, reversibility,
blast radius), and produces the human-operator runbook (`HG1_APPLY_MIGRATIONS.md`) that the
human gate reads before applying.

## Steps

1. Read `platform/migrations/116_trace_mcp_tool_column.sql` completely.
   Note: what table it touches, column type, whether it has IF NOT EXISTS guard.

2. Read `platform/migrations/117_audience_tier_acharya_enum.sql` completely.
   Note: what constraint it alters, whether it has safe ALTER TYPE syntax.

3. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md`
   with the following sections:

   **§1 — Pre-flight checks**
   - Confirm you are connected to the PRODUCTION database (not staging)
   - Check `SELECT version();` — record PostgreSQL version
   - Confirm current column/constraint state (SELECT to verify column/constraint does not yet exist)

   **§2 — Apply migration 116**
   Exact command:
   ```bash
   psql "$DATABASE_URL" -f platform/migrations/116_trace_mcp_tool_column.sql
   ```
   Verify:
   ```sql
   SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name='query_trace_steps' AND column_name='mcp_tool';
   ```
   Expected: 1 row returned.

   **§3 — Apply migration 117**
   Exact command:
   ```bash
   psql "$DATABASE_URL" -f platform/migrations/117_audience_tier_acharya_enum.sql
   ```
   Verify:
   ```sql
   SELECT pg_get_constraintdef(oid) FROM pg_constraint
   WHERE conname='mcp_api_keys_audience_tier_check';
   ```
   Expected: constraint definition includes 'acharya'.

   **§4 — Rollback commands** (if needed)
   For 116: `ALTER TABLE query_trace_steps DROP COLUMN IF EXISTS mcp_tool;`
   For 117: provide the inverse ALTER TYPE or constraint drop.

   **§5 — MIGRATIONS_APPLIED_LOG.md entries to append**
   Provide exact row format to add to `00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md`.

   **§6 — Signal completion**
   ```bash
   touch 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_COMPLETE
   ```

4. Commit:
   ```
   dar: P2-S5 create HG1 apply instructions for migrations 116+117
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md` → TRUE
- `grep 'migration_116' HG1_APPLY_MIGRATIONS.md` → match
- `grep 'migration_117' HG1_APPLY_MIGRATIONS.md` → match
- `grep 'rollback' HG1_APPLY_MIGRATIONS.md` → match
