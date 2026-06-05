# Migration Squash Sentinel — Brahma Baseline

**squash_date:** 2026-06-05
**squash_session:** wsmisc-wave-close / migration-squash
**baseline_file:** `platform/supabase/migrations/0001_brahma_baseline.sql`
**squash_sentinel:** BRAHMA_BASELINE_v1.0

## What was squashed

All historical migrations from:
- `057_school_signal_coverage.sql` through `157_charts_natural_key_uniq.sql`
- 30 migration files total archived to `_archive/`

Pre-squash snapshot: `_pre_squash_schema_snapshot.sql` (taken before WS-2 tag)

## Verification

Manual structural diff against `_pre_squash_schema_snapshot.sql`:
- Tables: 81/81 PASS
- Indexes: 202/202 PASS
- Foreign keys: 38/38 PASS
- Functions: 18/18 PASS
- Owner statements: 0 PASS
- Idempotency (IF NOT EXISTS): APPLIED

Docker live-DB diff: AMBER — Docker Desktop not running at squash time.
Structural manual diff is authoritative for this session.

## Squash stats

```json
{
  "migration": "0001_brahma_baseline",
  "squashed_from": "all historical 0NNN_*.sql migrations (057 through 157)",
  "squashed_at": "2026-06-05",
  "table_count": 81,
  "index_count": 202,
  "foreign_key_count": 38,
  "function_count": 18,
  "archived_files": 30,
  "sentinel": "BRAHMA_BASELINE_v1.0"
}
```

## Instructions for new migrations

New migrations must start at `0002_` or higher.
The `_archive/` directory is read-only historical record.
The `_pre_squash_schema_snapshot.sql` is the authoritative pre-squash reference.
