---
artifact: MIGRATION_DIRECTORY_POLICY_v1_0.md
canonical_id: MIGRATION_DIRECTORY_POLICY
version: 1.0
status: CURRENT
produced_on: 2026-05-22
produced_during: CLOSEOUT-2026-05-22
---

# Migration Directory Policy

## Background

The project has two parallel migration directories that both apply to the same prod Cloud SQL Postgres instance (`madhav-astrology:asia-south1:amjis-postgres` / DB `amjis`):

- **`platform/migrations/`** — original, holds 001–061, 069, 110–114
- **`platform/supabase/migrations/`** — historical (Supabase-CLI naming convention before the project moved fully to Cloud SQL); holds 057–071 from Chat-V2/M5-Coverage/MCP workstreams

**Numbering is per-directory, not global.** Operator applies migrations manually via `psql` + cloud-sql-proxy; idempotency relies on `CREATE … IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` in every migration. State is doc-tracked in `MIGRATIONS_APPLIED_LOG.md` at the project root.

---

## Policy (effective 2026-05-22)

1. **`platform/migrations/` is CANONICAL.** All new migrations land here, using the next available number after **114**. Next migration is `115_<description>.sql`.

2. **`platform/supabase/migrations/` is FROZEN.** No new files. No edits to existing files except to fix bugs in not-yet-applied migrations (and only with an explicit governance note).

3. **Every migration apply session must append a row to `MIGRATIONS_APPLIED_LOG.md`** in the same commit that applies the migration. The log is the source of truth for what is actually in prod — there is no Flyway/sqitch schema_migrations table.

4. **The "supabase" directory name is misleading but retained for now.** A full rename + file relocation is deferred to a future governance hygiene session (the rename would break `git log --follow` on those files; needs careful planning and `git mv` per-file).

5. **Idempotency is mandatory.** Every migration uses `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`. A re-apply must be a no-op and must not error.

---

## Operator quick reference

```bash
# Apply a migration
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f platform/migrations/<file>.sql

# Verify: table exists
psql "$DATABASE_URL" -c "SELECT to_regclass('public.<table>');"

# Verify: column exists
psql "$DATABASE_URL" -c "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='<table>' AND column_name='<col>';"

# After apply: update MIGRATIONS_APPLIED_LOG.md in the same commit
```

---

## Known unapplied migrations (as of 2026-05-22)

The following five `platform/supabase/migrations/` files are NOT applied in prod. They are R8 feature migrations (branches, search, pin/archive) and M5-PERF wiring. They should be applied in a dedicated follow-up session.

| File | Feature | Apply Notes |
|------|---------|-------------|
| 064_query_trace_steps_user_id.sql | R8-adjacent: /api/predictions ownership | Safe; ADD COLUMN IF NOT EXISTS |
| 066_conversation_branches.sql | R8-S1: branches persistence | Safe; CREATE TABLE IF NOT EXISTS |
| 067_pg_trgm_conversation_messages.sql | R8-S3: conversation search | CREATE EXTENSION IF NOT EXISTS + GIN index |
| 068_pin_archive_folders.sql | R8-S4: pin/archive/folders | ADD COLUMN + CREATE TABLE IF NOT EXISTS |
| 069_performance_wiring_fixes.sql | PERF-S1: performance_queries columns | Safe; ADD COLUMN IF NOT EXISTS; wrapped in BEGIN/COMMIT |

**Recommended apply order:** 064 → 066 → 067 → 068 → 069. Apply individually; verify each before proceeding. Append row to `MIGRATIONS_APPLIED_LOG.md` for each.

---

## Future work (deferred)

- **Rename `platform/supabase/migrations/` → `platform/migrations/`** with files renumbered to ≥115 (one-time governance hygiene session; requires `git mv` for each file to preserve history in `--follow` mode)
- **Optional: adopt a real migration runner** (Flyway, sqitch, dbmate) with a `schema_migrations` table in Postgres for automated apply-state tracking
