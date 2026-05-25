---
session_id: DAR-P2-S5
phase: 2
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md
  - 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/
  - platform/src/
  - platform/python-sidecar/pipeline/extractors/
  - platform/python-sidecar/pipeline/writers/
---

# DAR-P2-S5: Apply migrations 116+117 directly + baseline DB verification

Context: Both migrations are idempotent and safe:
- Migration 116: ADD COLUMN IF NOT EXISTS mcp_tool TEXT on query_trace_steps (brief table lock, ~ms)
- Migration 117: DO block extending audience_tier CHECK to add 'acharya'; pre-checks existence before altering
Neither migration destroys data or requires downtime. Apply them autonomously.

## Steps

### 1. Locate migration SQL files
Check both locations (project may use either):
  ls platform/migrations/116_trace_mcp_tool_column.sql 2>/dev/null || \
  ls platform/supabase/migrations/*116*.sql 2>/dev/null
  ls platform/migrations/117_audience_tier_acharya_enum.sql 2>/dev/null || \
  ls platform/supabase/migrations/*117*.sql 2>/dev/null

If files are missing, write them from memory:

Migration 116 content:
  ALTER TABLE query_trace_steps
    ADD COLUMN IF NOT EXISTS mcp_tool TEXT;

Migration 117 content:
  DO $$
  BEGIN
    IF NOT EXISTS (
      SELECT 1 FROM pg_constraint
      WHERE conname = 'mcp_api_keys_audience_tier_check'
        AND consrc LIKE '%acharya%'
    ) THEN
      ALTER TABLE mcp_api_keys
        DROP CONSTRAINT IF EXISTS mcp_api_keys_audience_tier_check;
      ALTER TABLE mcp_api_keys
        ADD CONSTRAINT mcp_api_keys_audience_tier_check
        CHECK (audience_tier IN ('super_admin', 'acharya', 'client'));
    END IF;
  END $$;

### 2. Start DB proxy
  bash /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/start_db_proxy.sh &
  PROXY_PID=$!
  sleep 20
  nc -z localhost 5433 && echo "PROXY_READY" || (echo "PROXY_FAILED" && exit 1)

The DB is accessible at: postgresql://postgres@localhost:5433/postgres
If start_db_proxy.sh does not exist, check platform/scripts/ for an equivalent (cloud_sql_proxy, etc.)

### 3. Apply migration 116
  psql "postgresql://postgres@localhost:5433/postgres" \
    -f platform/migrations/116_trace_mcp_tool_column.sql
  
  Verify column exists:
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT column_name FROM information_schema.columns \
     WHERE table_name='query_trace_steps' AND column_name='mcp_tool';" \
  | grep -q "mcp_tool" && echo "M116_VERIFIED" || (echo "M116_FAILED" && exit 1)

### 4. Apply migration 117
  psql "postgresql://postgres@localhost:5433/postgres" \
    -f platform/migrations/117_audience_tier_acharya_enum.sql
  
  Verify constraint includes 'acharya':
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT pg_get_constraintdef(oid) FROM pg_constraint \
     WHERE conrelid='mcp_api_keys'::regclass AND contype='c';" \
  | grep -q "acharya" && echo "M117_VERIFIED" || (echo "M117_FAILED" && exit 1)

### 5. Query DB baseline state
Run each query and record results:
  a. SELECT COUNT(*) FROM msr_signals;
  b. SELECT COUNT(*) FROM l25_msr_signals;
  c. SELECT DISTINCT source_file FROM msr_signals LIMIT 1;
  d. SELECT COUNT(*) FROM ephemeris_daily;
  e. SELECT COUNT(*) FROM chart_facts;
  f. SELECT COUNT(*) FROM rag_chunks WHERE source_type='msr_signal';

### 6. Write DB_BASELINE_REPORT.md
Write to: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md
Content (fill in values from step 5):
  ---
  generated: [ISO timestamp]
  migration_116: CONFIRMED
  migration_117: CONFIRMED
  msr_signals_source: [value from query c — e.g. MSR_v3_0.md or MSR_v5_0.md]
  msr_signals_count: [value from query a]
  l25_msr_signals_count: [value from query b]
  ephemeris_daily_count: [value from query d]
  chart_facts_count: [value from query e]
  msr_rag_chunks_count: [value from query f]
  notes: "Baseline captured before MSR v5.0 DB rebuild. msr_signals_source expected MSR_v3_0.md at this stage."
  ---

### 7. Append to MIGRATIONS_APPLIED_LOG.md
If the file does not exist, create it. Append:
  - migration_116: applied [timestamp] — query_trace_steps.mcp_tool column added
  - migration_117: applied [timestamp] — audience_tier 'acharya' added to CHECK constraint

### 8. Stop proxy
  kill $PROXY_PID 2>/dev/null || true
