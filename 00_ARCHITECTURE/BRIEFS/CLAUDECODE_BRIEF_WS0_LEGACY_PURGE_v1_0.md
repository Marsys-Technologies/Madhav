---
artifact: CLAUDECODE_BRIEF_WS0_LEGACY_PURGE_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS0_LEGACY_PURGE
version: 1.2
status: READY_FOR_EXECUTION
project_codename: Brahma — Legacy Residue Purge v2
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code extension running inside Google Antigravity IDE
execution_surface: >
  Claude Code (the extension), hosted inside Google Antigravity IDE. CC has Read/Write/Edit + an
  integrated bash terminal + git tooling, all rooted at the repo `/Users/Dev/Vibe-Coding/Apps/Madhav`.
  Every command in this brief is paste-ready into CC's bash; no external terminal, no separate IDE
  switch. Prod DB access via the Cloud SQL Auth Proxy started by `platform/scripts/start_db_proxy.sh`
  (binds local 5433). Cowork plans; CC-in-Antigravity executes.
native_approved: true  # native confirmed 2026-06-04 session
no_backup: true        # explicit native directive — no export, no snapshot before destructive steps
changelog:
  - v1.2 (2026-06-04): Execution-surface clarification — explicitly written for the Claude Code
    extension running inside Google Antigravity IDE (not the CLI, not Antigravity standalone). Adds
    §1a Prerequisites with Cloud SQL Auth Proxy startup + `psql_prod`/`psql_local` helper idiom that
    every SQL block in §2 invokes. No semantic changes to Steps 0–7; the brief is now end-to-end
    paste-ready into CC's integrated bash.
  - v1.1 (2026-06-04): Thoroughness upgrade per native directive. Adds Steps 1c/1d/1e (categorical
    allowlist sweep with DRY-RUN safety + orphan-object cleanup for sequences/views/functions/types),
    Step 2-PRE (exhaustive code-citation audit auto-derived from the §2 DROP list — replaces the
    "high-volume only" grep), Step 3d (Cloud Run env-var sweep for orphan MARSYS_FLAG_*), an
    expanded Step 4 grep covering EVERY dropped table name, AC-9 + AC-10. Also fixes the bugged
    WHERE-precedence in Step 1 verification (line 304 in v1.0). §8 lists items deliberately out of
    WS-0 scope (GCS bucket contents, CAPABILITY_MANIFEST.json scan, historical migrations).
  - v1.0 (2026-06-04): initial executable brief — hand-curated DROP list + targeted grep.
may_touch:
  - "platform/supabase/migrations/**"
  - "platform/python-sidecar/**"
  - "platform/src/lib/tools/structured/**"
  - "platform/src/lib/config/feature_flags.ts"
  - "platform/src/app/api/citations/preview/route.ts"
  - "platform/src/app/api/admin/mcp/health/calibration/route.ts"
  - "platform/src/app/api/mcp/asset/route.ts"
  - "platform/scripts/bootstrap/**"
  - "platform/scripts/grounding/**"
  - "platform/scripts/integrity/**"
  - "platform/src/scripts/etl/**"
  - "platform-mcp/src/audit.ts"
  - ".github/workflows/deploy.yml"
  - ".github/workflows/cloudbuild.yaml"
must_not_touch:
  - "platform/python-sidecar/brahmagyan/**"  # Brahma layers — except specific re-points listed in §4
  - "platform/python-sidecar/ganita/**"
  - "platform/python-sidecar/bodha/**"
  - "platform/python-sidecar/kala/**"
  - "platform/python-sidecar/phala/**"       # except re-point listed in §4
  - "platform/python-sidecar/mimamsa/**"     # except re-point listed in §4
  - "platform/supabase/migrations/brahma_*"  # any migration prefixed brahma_
  - "01_FACTS_LAYER/**"
  - "00_ARCHITECTURE/**"
  - ".github/workflows/ci.yml"
  - ".github/workflows/brahma-conductor.yml"
  - ".github/workflows/icr_weekly_scan.yml"
  - ".github/workflows/chat-v2-ci.yml"
  - ".github/workflows/chat-v2-smoke.yml"
acceptance_criteria:
  - "AC-1: `SELECT count(*) FROM brahmagyan_*` (all Brahma tables) returns same row counts as pre-purge baseline"
  - "AC-2: `SELECT count(*) FROM charts` unchanged from pre-purge baseline"
  - "AC-3: zero code files contain SELECT/FROM/INSERT referencing any legacy table listed in §2 (verified by the auto-derived exhaustive grep in Step 4)"
  - "AC-4: `grep -r '025_HOLISTIC_SYNTHESIS\\|035_DISCOVERY_LAYER' platform/python-sidecar/rag/` returns no results (directory deleted)"
  - "AC-5: `npm run typecheck` exits 0 (or known-pre-existing failures only)"
  - "AC-6: `python -m pytest platform/python-sidecar/tests/ --ignore=platform/python-sidecar/tests/integration` exits 0"
  - "AC-7: deploy.yml no longer references marsys-build-pipeline-job, CONSUME_UI_V2_ENABLED, 025_HOLISTIC_SYNTHESIS copy step, 035_DISCOVERY_LAYER copy step"
  - "AC-8: feature_flags.ts contains no R8_*, R9_*, R10_*, R11* flag constants"
  - "AC-9: Categorical allowlist sweep (Step 1d) leaves zero public.* tables outside the Brahma-prefix + shell allowlist on BOTH prod and localhost"
  - "AC-10: Orphan object sweep (Step 1e) leaves zero public sequences/views/materialized-views/functions/types whose name encodes a dropped legacy table"
project_facts:
  gcp_project: madhav-astrology
  region: asia-south1
  cloud_sql_conn: madhav-astrology:asia-south1:amjis-postgres
  db: amjis
  db_user: amjis_app
  prod_url: madhav.marsys.in
---

# CLAUDECODE_BRIEF — WS-0 Legacy Residue Purge v2

## §1 Mission

Full wipe of pre-Brahma residue from three surfaces: production + localhost DB data, codebase, and deploy/CI pipeline. The Brahma 6-layer model (L0 Brahmagyan → L5 Mīmāṃsā) is the sole live data and computation stack. All pre-Brahma artifacts — FORENSIC-derived live tables, MSR v5.0 synthesis, RAG corpus, Discovery Layer, l25_* tables, A1–A14 DAG build tables — are hereby retired permanently.

**No backup. No export. No restore path.** This is a forward-only commit to the Brahma architecture.

**Execution context — Claude Code extension in Google Antigravity IDE.** CC drives the entire run from its integrated bash terminal + file tools. All commands below are paste-ready as-is. No "switch to another terminal" or "open a separate IDE" steps. The repo root is `/Users/Dev/Vibe-Coding/Apps/Madhav` — every relative path resolves from there.

## §1a Prerequisites — connect to prod DB once, at the top of the run

CC opens the Cloud SQL Auth Proxy in a backgrounded bash invocation, then uses `psql` against the local socket for every prod SQL block in this brief.

```bash
# Start the Cloud SQL Auth Proxy in the background (binds 127.0.0.1:5433).
# The repo's helper script handles credentials + connection string.
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3  # let the proxy bind

# Verify the proxy is up
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "SELECT current_database(), current_user, now();" || {
  echo "ERROR: Cloud SQL proxy failed to start. Halt — report to native."
  exit 1
}

# Export the prod connection string for the rest of the run
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"

# Try to detect a local Postgres (optional second target — Step 1 also runs against this if present)
if psql "postgresql://localhost:5432/amjis" -c "SELECT 1" >/dev/null 2>&1; then
  export LOCAL_DB_URL="postgresql://localhost:5432/amjis"
  echo "Localhost Postgres detected — will run Step 1, 1b, 1c-DRY-RUN, 1d, 1e against it too."
else
  export LOCAL_DB_URL=""
  echo "No localhost Postgres detected — localhost sweep will be skipped (logged, not halted)."
fi

# Helper alias for every SQL block below: pipe the SQL via stdin → psql against prod
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
psql_local() { [ -n "$LOCAL_DB_URL" ] && psql "$LOCAL_DB_URL" -v ON_ERROR_STOP=1 "$@" || true; }

# At the end of the run (Step 7 closeout), CC kills the proxy:
#   kill $PROXY_PID
```

**Every SQL block in §2 below is run by piping the SQL into `psql_prod`** (and `psql_local` when applicable). E.g. `cat <<'EOF' | psql_prod ... EOF`. CC handles this idiom natively.

---

## §2 Surface 1 — Database DROP LIST

Run against **both prod (Cloud SQL `amjis`)** and **localhost** (if a local Postgres is running — check with `psql $LOCAL_DB_URL -c "SELECT 1" 2>/dev/null`).

### WS-0 Step 0 (Prologue): Pre-checks — run first, block on failures

```sql
-- 1. Baseline Brahma row counts (capture before any DROP)
SELECT 'ganita_positions' AS tbl, count(*) FROM ganita_positions
UNION ALL SELECT 'ganita_dashas', count(*) FROM ganita_dashas
UNION ALL SELECT 'bodha_signals', count(*) FROM bodha_signals
UNION ALL SELECT 'kala_timeline', count(*) FROM kala_timeline
UNION ALL SELECT 'phala_anchors', count(*) FROM phala_anchors
UNION ALL SELECT 'mimamsa_predictions', count(*) FROM mimamsa_predictions;

-- 2. Baseline shell row counts
SELECT 'charts', count(*) FROM charts
UNION ALL SELECT 'conversations', count(*) FROM conversations
UNION ALL SELECT 'life_events', count(*) FROM life_events
UNION ALL SELECT 'mcp_predictions', count(*) FROM mcp_predictions;

-- 3. Predictions table — conditional migration decision
SELECT count(*) AS prediction_count,
       min(created_at) AS earliest,
       max(created_at) AS latest
FROM predictions;
-- Rule: if count=0 → DROP directly (Step 1 handles it)
-- Rule: if count>0 → execute the migration block in §2a BEFORE Step 1
```

### §2a Conditional migration: `predictions` → `mcp_predictions`

**Execute this block ONLY if `predictions` count > 0 from Step 0 check #3.**

```sql
-- Migrate real prospective bets into mcp_predictions before drop
INSERT INTO mcp_predictions (
  prediction_text,
  confidence,
  horizon,
  falsifier,
  created_at,
  source_note
)
SELECT
  prediction_text,
  confidence::text,
  horizon,
  falsifier,
  created_at,
  'MIGRATED from predictions table (WS-0 legacy purge 2026-06-04)'
FROM predictions
WHERE prediction_text IS NOT NULL;

-- Verify migration row count matches source
DO $$
DECLARE
  src_count INTEGER;
  dst_new   INTEGER;
BEGIN
  SELECT count(*) INTO src_count FROM predictions WHERE prediction_text IS NOT NULL;
  -- Check at least src_count rows were inserted recently
  SELECT count(*) INTO dst_new FROM mcp_predictions
    WHERE source_note LIKE 'MIGRATED from predictions%';
  IF dst_new < src_count THEN
    RAISE EXCEPTION 'Migration count mismatch: src=% dst=%', src_count, dst_new;
  END IF;
END $$;
```

### WS-0 Step 1: DROP all legacy tables (CASCADE handles FK order)

```sql
-- L2.5 synthesis (MSR v5.0, UCN, CDLM, CGM, RM)
DROP TABLE IF EXISTS l25_msr_signals CASCADE;
DROP TABLE IF EXISTS l25_msr_signals_staging CASCADE;
DROP TABLE IF EXISTS l25_ucn_sections CASCADE;
DROP TABLE IF EXISTS l25_ucn_sections_staging CASCADE;
DROP TABLE IF EXISTS l25_ucn_digests CASCADE;
DROP TABLE IF EXISTS l25_ucn_digests_staging CASCADE;
DROP TABLE IF EXISTS l25_cdlm_links CASCADE;
DROP TABLE IF EXISTS l25_cdlm_links_staging CASCADE;
DROP TABLE IF EXISTS l25_cdlm_cells CASCADE;
DROP TABLE IF EXISTS l25_cdlm_cells_staging CASCADE;
DROP TABLE IF EXISTS l25_cgm_nodes CASCADE;
DROP TABLE IF EXISTS l25_cgm_nodes_staging CASCADE;
DROP TABLE IF EXISTS l25_cgm_edges CASCADE;
DROP TABLE IF EXISTS l25_cgm_edges_staging CASCADE;
DROP TABLE IF EXISTS l25_rm_resonances CASCADE;
DROP TABLE IF EXISTS l25_rm_resonances_staging CASCADE;
DROP TABLE IF EXISTS msr_signals CASCADE;
DROP TABLE IF EXISTS signal_states CASCADE;

-- L2.5 META synthesis
DROP TABLE IF EXISTS l25_chart_lattice_snapshots CASCADE;
DROP TABLE IF EXISTS l25_vedha_anchor_interactions CASCADE;
DROP TABLE IF EXISTS l25_derivation_graph_nodes CASCADE;
DROP TABLE IF EXISTS l25_derivation_graph_edges CASCADE;
DROP TABLE IF EXISTS l25_pattern_catalog CASCADE;
DROP TABLE IF EXISTS l25_divergence_ledger CASCADE;
DROP TABLE IF EXISTS l25_negative_space_map CASCADE;

-- L1 chart facts (FORENSIC-derived)
DROP TABLE IF EXISTS chart_facts_supersedence CASCADE;
DROP TABLE IF EXISTS chart_facts_history CASCADE;
DROP TABLE IF EXISTS chart_facts_staging CASCADE;
DROP TABLE IF EXISTS chart_facts CASCADE;
DROP TABLE IF EXISTS divisional_charts CASCADE;
DROP TABLE IF EXISTS varshaphala CASCADE;

-- L1 temporal (pre-Brahma build outputs)
DROP TABLE IF EXISTS dasha_periods CASCADE;
DROP TABLE IF EXISTS chart_dashas CASCADE;
DROP TABLE IF EXISTS l1_time_synchronicity CASCADE;
DROP TABLE IF EXISTS l1_phase_locked_anchors CASCADE;
DROP TABLE IF EXISTS l1_bhrigu_bindu_transits CASCADE;
DROP TABLE IF EXISTS l1_graha_aspects_lifetime CASCADE;
DROP TABLE IF EXISTS l1_vedha_extended CASCADE;
DROP TABLE IF EXISTS l1_varsha_digest CASCADE;
DROP TABLE IF EXISTS l1_tajik_varsha_year_lords CASCADE;

-- Reference chakra tables
DROP TABLE IF EXISTS l1_sarvatobhadra_positions CASCADE;
DROP TABLE IF EXISTS l1_sarvatobhadra_vedha CASCADE;
DROP TABLE IF EXISTS l1_sapta_shalaka CASCADE;
DROP TABLE IF EXISTS l1_kalanala_chakra CASCADE;
DROP TABLE IF EXISTS l1_kota_chakra CASCADE;
DROP TABLE IF EXISTS l1_ckn_chakra CASCADE;

-- Astronomical / panchanga (Phase 4C superseded by L0 Brahmagyan)
DROP TABLE IF EXISTS ephemeris_daily CASCADE;
DROP TABLE IF EXISTS ephemeris_daily_staging CASCADE;
DROP TABLE IF EXISTS panchanga_daily CASCADE;
DROP TABLE IF EXISTS panchanga_daily_staging CASCADE;
DROP TABLE IF EXISTS eclipses_retrogrades CASCADE;
DROP TABLE IF EXISTS eclipses CASCADE;
DROP TABLE IF EXISTS eclipses_staging CASCADE;
DROP TABLE IF EXISTS retrogrades CASCADE;
DROP TABLE IF EXISTS retrogrades_staging CASCADE;

-- RAG / corpus (MCP Transformation v3.1 superseded by Brahma)
DROP TABLE IF EXISTS rag_chunks CASCADE;
DROP TABLE IF EXISTS rag_chunks_staging CASCADE;
DROP TABLE IF EXISTS rag_embeddings CASCADE;
DROP TABLE IF EXISTS rag_embeddings_staging CASCADE;
DROP TABLE IF EXISTS rag_graph_nodes CASCADE;
DROP TABLE IF EXISTS rag_graph_edges CASCADE;
DROP TABLE IF EXISTS rag_queries CASCADE;
DROP TABLE IF EXISTS rag_retrievals CASCADE;
DROP TABLE IF EXISTS rag_feedback CASCADE;
DROP TABLE IF EXISTS rag_reproducibility_failures CASCADE;

-- Classical text store
DROP TABLE IF EXISTS classical_texts CASCADE;
DROP TABLE IF EXISTS classical_chunks CASCADE;
DROP TABLE IF EXISTS classical_attributions CASCADE;

-- Discovery registers
DROP TABLE IF EXISTS pattern_register CASCADE;
DROP TABLE IF EXISTS pattern_register_staging CASCADE;
DROP TABLE IF EXISTS resonance_register CASCADE;
DROP TABLE IF EXISTS resonance_register_staging CASCADE;
DROP TABLE IF EXISTS cluster_register CASCADE;
DROP TABLE IF EXISTS cluster_register_staging CASCADE;
DROP TABLE IF EXISTS contradiction_register CASCADE;
DROP TABLE IF EXISTS contradiction_register_staging CASCADE;

-- Multi-school / convergence
DROP TABLE IF EXISTS school_signal_coverage CASCADE;
DROP TABLE IF EXISTS school_analysis_runs CASCADE;
DROP TABLE IF EXISTS convergence_scores CASCADE;
DROP TABLE IF EXISTS school_disagreements CASCADE;
DROP TABLE IF EXISTS multi_school_stances CASCADE;
DROP TABLE IF EXISTS school_convergence_index CASCADE;
DROP TABLE IF EXISTS data_source_expected CASCADE;
DROP TABLE IF EXISTS tool_caveats CASCADE;

-- Build orchestration (A1–A14 DAG era)
DROP TABLE IF EXISTS build_dependencies CASCADE;
DROP TABLE IF EXISTS build_checkpoints CASCADE;
DROP TABLE IF EXISTS build_steps CASCADE;
DROP TABLE IF EXISTS build_events CASCADE;
DROP TABLE IF EXISTS build_notifications CASCADE;
DROP TABLE IF EXISTS notification_views CASCADE;
DROP TABLE IF EXISTS build_engine_versions CASCADE;
DROP TABLE IF EXISTS engine_versions CASCADE;
DROP TABLE IF EXISTS chart_documents CASCADE;
DROP TABLE IF EXISTS chart_ayanamsha_reports CASCADE;
DROP TABLE IF EXISTS builds CASCADE;
DROP TABLE IF EXISTS builds_staging CASCADE;
DROP TABLE IF EXISTS build_manifests CASCADE;

-- Computed legacy astro
DROP TABLE IF EXISTS sade_sati_phases CASCADE;
DROP TABLE IF EXISTS sade_sati_phases_staging CASCADE;
DROP TABLE IF EXISTS sade_sati_cycles CASCADE;
DROP TABLE IF EXISTS shadbala CASCADE;
DROP TABLE IF EXISTS tajaka_annual CASCADE;
DROP TABLE IF EXISTS sankranti_table CASCADE;
DROP TABLE IF EXISTS saturn_sign_changes CASCADE;
DROP TABLE IF EXISTS ayanamsha_registry CASCADE;
DROP TABLE IF EXISTS kp_sublords CASCADE;
DROP TABLE IF EXISTS g29_timing_rules CASCADE;

-- Old MCP / audit infra
DROP TABLE IF EXISTS mcp_bundle_cache CASCADE;
DROP TABLE IF EXISTS mcp_audit_findings CASCADE;
DROP TABLE IF EXISTS audit_job_runs CASCADE;

-- AI-ops stack (never deployed)
DROP TABLE IF EXISTS llm_model_health CASCADE;
DROP TABLE IF EXISTS llm_param_override CASCADE;
DROP TABLE IF EXISTS llm_stack_routing_override CASCADE;
DROP TABLE IF EXISTS llm_catalog_snapshot CASCADE;
DROP TABLE IF EXISTS llm_config_audit CASCADE;

-- v1 messaging era
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS message_feedback CASCADE;
DROP TABLE IF EXISTS chat_attachments CASCADE;

-- Misc orphans
DROP TABLE IF EXISTS pyramid_layers CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS gate_change_log CASCADE;
DROP TABLE IF EXISTS prediction_ledger CASCADE;
DROP TABLE IF EXISTS query_plans CASCADE;
DROP TABLE IF EXISTS context_assembly_log CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;  -- migrated above if had rows

-- Step 1 verification: confirm Brahma + shell tables still intact
-- (fixed WHERE precedence bug from v1.0 — parens required)
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND (
       table_name LIKE 'brahmagyan_%'
    OR table_name LIKE 'ganita_%'
    OR table_name LIKE 'bodha_%'
    OR table_name LIKE 'kala_%'
    OR table_name LIKE 'phala_%'
    OR table_name LIKE 'mimamsa_%'
    OR table_name = 'event_chart_state_index'
    OR table_name IN (
         'charts', 'conversations', 'life_events', 'mcp_predictions',
         'mcp_api_keys', 'profiles', 'conversation_messages'
       )
  )
ORDER BY table_name;
-- Expected: all Brahma + shell tables present; none of the dropped tables
```

### WS-0 Step 1b: Post-drop Brahma baseline re-check

```sql
-- Confirm Brahma row counts are identical to pre-purge baseline from Step 0
SELECT 'ganita_positions' AS tbl, count(*) FROM ganita_positions
UNION ALL SELECT 'ganita_dashas', count(*) FROM ganita_dashas
UNION ALL SELECT 'bodha_signals', count(*) FROM bodha_signals
UNION ALL SELECT 'kala_timeline', count(*) FROM kala_timeline
UNION ALL SELECT 'phala_anchors', count(*) FROM phala_anchors
UNION ALL SELECT 'mimamsa_predictions', count(*) FROM mimamsa_predictions;
-- Must match Step 0 baseline exactly. Any row count drop = HALT immediately.
```

### WS-0 Step 1c: Categorical allowlist sweep — DRY-RUN (safety review)

The explicit DROP list in Step 1 covers ~100 known legacy tables. **Step 1c catches anything else** — straggler tables that aren't Brahma and aren't shell. The allowlist is **prefix-based for Brahma** (so new Brahma tables added later auto-protect) **+ enumerated for shell** (so the shell list is auditable).

**Run on prod AND localhost. DRY-RUN first — print the candidate list. Halt for the executor to confirm zero Brahma/shell tables are in the candidate list before proceeding to Step 1d.**

```sql
-- DRY-RUN: enumerate public.* tables that are neither Brahma-prefix nor in the shell allowlist
WITH shell_allowlist AS (
  SELECT unnest(ARRAY[
    -- Auth + accounts
    'profiles', 'access_requests',
    -- Charts + sharing
    'charts', 'chart_grants',
    -- Conversations + chat substrate
    'conversations', 'conversation_messages', 'conversation_message_embeddings',
    'conversation_branches', 'conversation_shares',
    'conversation_folders', 'conversation_folder_members',
    'pending_streams',
    -- Projects + personas
    'projects', 'project_files', 'project_conversations', 'personas',
    -- Life events (LEL) — Mīmāṃsā's isolated event log
    'life_events', 'life_events_staging',
    -- Audit + observability
    'audit_log', 'audit_events',
    'query_trace_steps', 'llm_call_log', 'tool_execution_log',
    'query_plan_log', 'context_assembly_item_log',
    'synthesis_quality_scorecard', 'plan_alternatives_log',
    -- LLM cost + budget
    'llm_pricing_versions', 'llm_usage_events',
    'llm_provider_cost_reports', 'llm_cost_reconciliation',
    'llm_budget_rules', 'llm_stack_config',
    -- Performance + evals
    'performance_queries', 'eval_runs', 'performance_judge_verdict',
    -- MCP substrate (current, Brahma-aligned)
    'mcp_api_keys', 'mcp_predictions', 'mcp_prediction_outcomes',
    'mcp_disagreements', 'mcp_alerts_config',
    -- Tool registries
    'tool_registry', 'capability_tool_registry', 'capability_asset_tool_bindings',
    -- Runtime config
    'runtime_config',
    -- Mīmāṃsā cross-cutting index (kept by handoff)
    'event_chart_state_index',
    -- Migration tracker (Supabase internal)
    '_migrations_applied'
  ]) AS table_name
)
SELECT t.table_name
FROM information_schema.tables t
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND t.table_name NOT LIKE 'brahmagyan_%'
  AND t.table_name NOT LIKE 'ganita_%'
  AND t.table_name NOT LIKE 'bodha_%'
  AND t.table_name NOT LIKE 'kala_%'
  AND t.table_name NOT LIKE 'phala_%'
  AND t.table_name NOT LIKE 'mimamsa_%'
  AND t.table_name NOT IN (SELECT table_name FROM shell_allowlist)
ORDER BY t.table_name;
```

**Executor safety check (mandatory before Step 1d):**
- Read the dry-run output table by table.
- Confirm zero entries match a Brahma layer (ganita_/bodha_/kala_/phala_/mimamsa_/brahmagyan_) or a known shell table.
- If even one Brahma/shell row appears → HALT, do not proceed to Step 1d, report to native.
- If the list contains only legacy strays → proceed to Step 1d.

### WS-0 Step 1d: Categorical allowlist sweep — EXECUTE

```sql
-- Drop every public.* table that's neither Brahma-prefix nor in the shell allowlist
DO $$
DECLARE
  tbl RECORD;
  dropped INTEGER := 0;
BEGIN
  FOR tbl IN
    WITH shell_allowlist AS (
      SELECT unnest(ARRAY[
        'profiles','access_requests',
        'charts','chart_grants',
        'conversations','conversation_messages','conversation_message_embeddings',
        'conversation_branches','conversation_shares',
        'conversation_folders','conversation_folder_members',
        'pending_streams',
        'projects','project_files','project_conversations','personas',
        'life_events','life_events_staging',
        'audit_log','audit_events',
        'query_trace_steps','llm_call_log','tool_execution_log',
        'query_plan_log','context_assembly_item_log',
        'synthesis_quality_scorecard','plan_alternatives_log',
        'llm_pricing_versions','llm_usage_events',
        'llm_provider_cost_reports','llm_cost_reconciliation',
        'llm_budget_rules','llm_stack_config',
        'performance_queries','eval_runs','performance_judge_verdict',
        'mcp_api_keys','mcp_predictions','mcp_prediction_outcomes',
        'mcp_disagreements','mcp_alerts_config',
        'tool_registry','capability_tool_registry','capability_asset_tool_bindings',
        'runtime_config',
        'event_chart_state_index',
        '_migrations_applied'
      ]) AS table_name
    )
    SELECT t.table_name
    FROM information_schema.tables t
    WHERE t.table_schema = 'public'
      AND t.table_type = 'BASE TABLE'
      AND t.table_name NOT LIKE 'brahmagyan_%'
      AND t.table_name NOT LIKE 'ganita_%'
      AND t.table_name NOT LIKE 'bodha_%'
      AND t.table_name NOT LIKE 'kala_%'
      AND t.table_name NOT LIKE 'phala_%'
      AND t.table_name NOT LIKE 'mimamsa_%'
      AND t.table_name NOT IN (SELECT table_name FROM shell_allowlist)
  LOOP
    EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', tbl.table_name);
    dropped := dropped + 1;
    RAISE NOTICE 'Step 1d dropped straggler: %', tbl.table_name;
  END LOOP;
  RAISE NOTICE 'Step 1d total stragglers dropped: %', dropped;
END $$;

-- AC-9 final assertion: zero stragglers remain
SELECT count(*) AS stragglers_remaining
FROM information_schema.tables t
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND t.table_name NOT LIKE 'brahmagyan_%'
  AND t.table_name NOT LIKE 'ganita_%'
  AND t.table_name NOT LIKE 'bodha_%'
  AND t.table_name NOT LIKE 'kala_%'
  AND t.table_name NOT LIKE 'phala_%'
  AND t.table_name NOT LIKE 'mimamsa_%'
  AND t.table_name NOT IN (
    'profiles','access_requests','charts','chart_grants',
    'conversations','conversation_messages','conversation_message_embeddings',
    'conversation_branches','conversation_shares',
    'conversation_folders','conversation_folder_members','pending_streams',
    'projects','project_files','project_conversations','personas',
    'life_events','life_events_staging',
    'audit_log','audit_events','query_trace_steps','llm_call_log','tool_execution_log',
    'query_plan_log','context_assembly_item_log',
    'synthesis_quality_scorecard','plan_alternatives_log',
    'llm_pricing_versions','llm_usage_events',
    'llm_provider_cost_reports','llm_cost_reconciliation',
    'llm_budget_rules','llm_stack_config',
    'performance_queries','eval_runs','performance_judge_verdict',
    'mcp_api_keys','mcp_predictions','mcp_prediction_outcomes',
    'mcp_disagreements','mcp_alerts_config',
    'tool_registry','capability_tool_registry','capability_asset_tool_bindings',
    'runtime_config','event_chart_state_index','_migrations_applied'
  );
-- Expected: 0
```

### WS-0 Step 1e: Orphan-object sweep (sequences / views / functions / types)

CASCADE on Step 1 + 1d drops most dependent objects, but standalone sequences (manual nextval-only), views (built over now-dropped tables before the FK cascade), materialized views, functions, and custom types can survive. Catch them by name pattern.

```sql
-- 1. Orphan SEQUENCES (auto-created sequences die with CASCADE; standalone ones survive)
SELECT sequence_schema, sequence_name
FROM information_schema.sequences
WHERE sequence_schema = 'public'
  AND (
       sequence_name LIKE 'l25_%'
    OR sequence_name LIKE 'rag_%'
    OR sequence_name LIKE 'msr_%'
    OR sequence_name LIKE 'chart_facts%'
    OR sequence_name LIKE 'panchanga_daily%'
    OR sequence_name LIKE 'build_manifests%'
    OR sequence_name LIKE 'classical_%'
    OR sequence_name LIKE 'school_%'
    OR sequence_name LIKE 'multi_school_%'
    OR sequence_name LIKE 'cluster_register%'
    OR sequence_name LIKE 'pattern_register%'
    OR sequence_name LIKE 'resonance_register%'
    OR sequence_name LIKE 'contradiction_register%'
    OR sequence_name LIKE 'ephemeris_daily%'
    OR sequence_name LIKE 'eclipses%'
    OR sequence_name LIKE 'retrogrades%'
    OR sequence_name LIKE 'l1_%'  -- legacy L1 codenames; Brahma uses ganita_/etc.
    OR sequence_name LIKE 'dasha_periods%'
    OR sequence_name LIKE 'chart_dashas%'
    OR sequence_name LIKE 'sade_sati%'
    OR sequence_name LIKE 'tajaka_%'
    OR sequence_name LIKE 'predictions%'
    OR sequence_name LIKE 'pyramid_layers%'
    OR sequence_name LIKE 'mcp_bundle_cache%'
    OR sequence_name LIKE 'mcp_audit_findings%'
    OR sequence_name LIKE 'llm_model_health%'
    OR sequence_name LIKE 'llm_param_override%'
    OR sequence_name LIKE 'llm_stack_routing_override%'
    OR sequence_name LIKE 'llm_catalog_snapshot%'
    OR sequence_name LIKE 'llm_config_audit%'
  );

DO $$
DECLARE seq RECORD;
BEGIN
  FOR seq IN
    SELECT sequence_name FROM information_schema.sequences
    WHERE sequence_schema = 'public'
      AND (sequence_name LIKE 'l25_%' OR sequence_name LIKE 'rag_%'
        OR sequence_name LIKE 'msr_%' OR sequence_name LIKE 'chart_facts%'
        OR sequence_name LIKE 'panchanga_daily%' OR sequence_name LIKE 'build_manifests%'
        OR sequence_name LIKE 'classical_%' OR sequence_name LIKE 'school_%'
        OR sequence_name LIKE 'multi_school_%' OR sequence_name LIKE 'cluster_register%'
        OR sequence_name LIKE 'pattern_register%' OR sequence_name LIKE 'resonance_register%'
        OR sequence_name LIKE 'contradiction_register%' OR sequence_name LIKE 'ephemeris_daily%'
        OR sequence_name LIKE 'eclipses%' OR sequence_name LIKE 'retrogrades%'
        OR sequence_name LIKE 'l1_%' OR sequence_name LIKE 'dasha_periods%'
        OR sequence_name LIKE 'chart_dashas%' OR sequence_name LIKE 'sade_sati%'
        OR sequence_name LIKE 'tajaka_%' OR sequence_name LIKE 'predictions%'
        OR sequence_name LIKE 'pyramid_layers%' OR sequence_name LIKE 'mcp_bundle_cache%'
        OR sequence_name LIKE 'mcp_audit_findings%' OR sequence_name LIKE 'llm_model_health%'
        OR sequence_name LIKE 'llm_param_override%' OR sequence_name LIKE 'llm_stack_routing_override%'
        OR sequence_name LIKE 'llm_catalog_snapshot%' OR sequence_name LIKE 'llm_config_audit%')
  LOOP
    EXECUTE format('DROP SEQUENCE IF EXISTS public.%I CASCADE', seq.sequence_name);
    RAISE NOTICE 'Step 1e dropped sequence: %', seq.sequence_name;
  END LOOP;
END $$;

-- 2. Orphan VIEWS + MATERIALIZED VIEWS over dropped tables
DO $$
DECLARE v RECORD;
BEGIN
  FOR v IN
    SELECT table_schema, table_name FROM information_schema.views
    WHERE table_schema = 'public'
      AND (table_name LIKE 'v_msr%' OR table_name LIKE 'v_chart_facts%'
        OR table_name LIKE 'v_rag%' OR table_name LIKE 'v_l25%'
        OR table_name LIKE 'v_classical%' OR table_name LIKE 'v_panchanga%'
        OR table_name LIKE 'v_school%' OR table_name LIKE 'v_multi_school%'
        OR table_name LIKE 'v_build_manifests%' OR table_name LIKE 'v_predictions%')
  LOOP
    EXECUTE format('DROP VIEW IF EXISTS public.%I CASCADE', v.table_name);
    RAISE NOTICE 'Step 1e dropped view: %', v.table_name;
  END LOOP;

  FOR v IN
    SELECT schemaname, matviewname FROM pg_matviews
    WHERE schemaname = 'public'
      AND (matviewname LIKE 'mv_msr%' OR matviewname LIKE 'mv_chart_facts%'
        OR matviewname LIKE 'mv_rag%' OR matviewname LIKE 'mv_l25%'
        OR matviewname LIKE 'mv_panchanga%' OR matviewname LIKE 'mv_school%'
        OR matviewname LIKE 'mv_classical%')
  LOOP
    EXECUTE format('DROP MATERIALIZED VIEW IF EXISTS public.%I CASCADE', v.matviewname);
    RAISE NOTICE 'Step 1e dropped matview: %', v.matviewname;
  END LOOP;
END $$;

-- 3. Orphan FUNCTIONS encoding a legacy table name
DO $$
DECLARE f RECORD;
BEGIN
  FOR f IN
    SELECT n.nspname AS schema_name, p.proname AS function_name,
           pg_get_function_identity_arguments(p.oid) AS args
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
      AND (p.proname LIKE 'fn_msr%' OR p.proname LIKE 'fn_chart_facts%'
        OR p.proname LIKE 'fn_rag%' OR p.proname LIKE 'fn_l25%'
        OR p.proname LIKE 'fn_panchanga_daily%' OR p.proname LIKE 'fn_classical%'
        OR p.proname LIKE 'fn_multi_school%' OR p.proname LIKE 'fn_school_convergence%'
        OR p.proname LIKE 'fn_predictions%' OR p.proname LIKE 'fn_build_manifests%'
        OR p.proname LIKE 'trg_msr%' OR p.proname LIKE 'trg_chart_facts%'
        OR p.proname LIKE 'trg_rag%' OR p.proname LIKE 'trg_l25%')
  LOOP
    EXECUTE format('DROP FUNCTION IF EXISTS public.%I(%s) CASCADE',
                   f.function_name, f.args);
    RAISE NOTICE 'Step 1e dropped function: %(%)', f.function_name, f.args;
  END LOOP;
END $$;

-- 4. Orphan TYPES / ENUMS encoding a legacy table name
DO $$
DECLARE t RECORD;
BEGIN
  FOR t IN
    SELECT typname FROM pg_type t
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public'
      AND t.typtype = 'e'  -- enum types only; composite types are usually dropped with their table
      AND (t.typname LIKE 'msr_%' OR t.typname LIKE 'rag_%'
        OR t.typname LIKE 'chart_facts_%' OR t.typname LIKE 'l25_%'
        OR t.typname LIKE 'school_%' OR t.typname LIKE 'multi_school_%'
        OR t.typname LIKE 'classical_%' OR t.typname LIKE 'panchanga_%'
        OR t.typname LIKE 'discovery_%' OR t.typname LIKE 'predictions_%')
  LOOP
    EXECUTE format('DROP TYPE IF EXISTS public.%I CASCADE', t.typname);
    RAISE NOTICE 'Step 1e dropped type: %', t.typname;
  END LOOP;
END $$;
```

**AC-10 verification:** re-run each of the 4 SELECT queries above — every result set must return 0 rows.

---

## §3 Surface 2 — Code DELETE list

### WS-0 Step 2-PRE: Exhaustive code citation audit (auto-derived from §2 DROP list)

Before touching any code, enumerate every file in the repo that still cites a dropped legacy table. This becomes the input to Steps 2a–2h (curated targets) **and** the residual list for hand-disposition.

```bash
# The complete list of dropped legacy table names from §2 + Step 1d (alphabetized for grep).
# Update this list if any DROP is added/removed in §2.

LEGACY_TABLES='audit_job_runs|ayanamsha_registry|build_checkpoints|build_dependencies|build_engine_versions|build_events|build_manifests|build_notifications|build_steps|builds|builds_staging|chart_ayanamsha_reports|chart_dashas|chart_documents|chart_facts|chart_facts_history|chart_facts_staging|chart_facts_supersedence|chat_attachments|classical_attributions|classical_chunks|classical_texts|cluster_register|cluster_register_staging|context_assembly_log|contradiction_register|contradiction_register_staging|convergence_scores|data_source_expected|dasha_periods|divisional_charts|documents|eclipses|eclipses_retrogrades|eclipses_staging|engine_versions|ephemeris_daily|ephemeris_daily_staging|g29_timing_rules|gate_change_log|kp_sublords|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_chart_lattice_snapshots|l25_derivation_graph_edges|l25_derivation_graph_nodes|l25_divergence_ledger|l25_msr_signals|l25_msr_signals_staging|l25_negative_space_map|l25_pattern_catalog|l25_rm_resonances|l25_rm_resonances_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_vedha_anchor_interactions|llm_catalog_snapshot|llm_config_audit|llm_model_health|llm_param_override|llm_stack_routing_override|mcp_audit_findings|mcp_bundle_cache|message_feedback|messages|msr_signals|multi_school_stances|notification_views|panchanga_daily|panchanga_daily_staging|pattern_register|pattern_register_staging|prediction_ledger|predictions|pyramid_layers|query_plans|rag_chunks|rag_chunks_staging|rag_embeddings|rag_embeddings_staging|rag_feedback|rag_graph_edges|rag_graph_nodes|rag_queries|rag_reproducibility_failures|rag_retrievals|reports|resonance_register|resonance_register_staging|retrogrades|retrogrades_staging|sade_sati_cycles|sade_sati_phases|sade_sati_phases_staging|sankranti_table|saturn_sign_changes|school_analysis_runs|school_convergence_index|school_disagreements|school_signal_coverage|shadbala|signal_states|tajaka_annual|tool_caveats|varshaphala'

# Find every file (any extension) citing any legacy table
grep -rEn "(${LEGACY_TABLES})" \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  --include="*.sql" --include="*.json" --include="*.yaml" --include="*.yml" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git \
  --exclude-dir=00_ARCHITECTURE --exclude-dir=025_HOLISTIC_SYNTHESIS \
  --exclude-dir=035_DISCOVERY_LAYER --exclude-dir=01_FACTS_LAYER \
  platform/ platform-mcp/ brahmagyan/ panchang_engine/ . \
  2>/dev/null | tee /tmp/ws0_legacy_citations.txt

# Categorize the output: every file is either
#  (a) being DELETED by Step 2a-2d (rag/, query_*.ts, etc.) → expected to disappear after Steps 2a-2d
#  (b) being RE-POINTED by Step 2e-2g (mcp/asset, audit.ts, etc.) → expected to lose those refs after the edit
#  (c) historical SQL migration in platform/supabase/migrations/ → frozen history, IGNORE (see §8)
#  (d) UNKNOWN — a file we didn't anticipate that still cites a legacy table → MUST be disposed before Step 4 passes

# Print the count of citations per file (helps prioritize)
awk -F: '{print $1}' /tmp/ws0_legacy_citations.txt | sort | uniq -c | sort -rn | head -50

# Print the (d) "unknown" candidates — anything not under the rag/, query_*, scripts/, route paths Steps 2a-2g delete/re-point
grep -v -E '(platform/python-sidecar/rag/|platform/src/lib/tools/structured/query_|platform/src/scripts/etl/|platform/scripts/grounding/|platform/scripts/integrity/|platform/scripts/bootstrap/|platform/src/app/api/citations/preview/|platform/src/app/api/admin/mcp/health/calibration/|platform/src/app/api/mcp/asset/|platform-mcp/src/audit\.ts|platform/python-sidecar/main\.py|platform/supabase/migrations/)' \
  /tmp/ws0_legacy_citations.txt | awk -F: '{print $1}' | sort -u | tee /tmp/ws0_unknown_citers.txt

# Executor decision rule for each file in /tmp/ws0_unknown_citers.txt:
#  - If the citation is in a TEST file (*.test.ts, *_test.py, tests/, __tests__/) → either delete the test or rewrite against a Brahma table
#  - If the citation is in CI/build tooling (*.config.ts, dockerfile, etc.) → re-point or remove
#  - If the citation is in active product code → re-point to Brahma equivalent; if no equivalent, halt and report to native
#  - SQL migrations under platform/supabase/migrations/ are frozen history — IGNORE
#  - Markdown / governance docs are IGNORED (the --exclude-dir flags above handle 00_ARCHITECTURE; everything else is product code)
```

The auto-derived legacy-table list anchors everything: Steps 2a–2h, the Step 4 final grep, and the AC-3 assertion all use **this same list** so they stay in sync.

### WS-0 Step 2a: Delete entire legacy Python sidecar RAG module

```bash
# Delete entire rag/ module
rm -rf platform/python-sidecar/rag/

# Verify the rag/ endpoints are unmounted from main.py
grep -n "rag" platform/python-sidecar/main.py
# If any rag router imports remain, remove them from main.py now.
# Expected pattern: lines like `from routers.rag_retrieve import router`
# or `app.include_router(rag_router, prefix="/rag")`
# Delete those lines.
```

### WS-0 Step 2b: Delete orphaned TypeScript structured query tools

```bash
rm -f platform/src/lib/tools/structured/query_msr_signals.ts
rm -f platform/src/lib/tools/structured/query_cgm.ts
rm -f platform/src/lib/tools/structured/query_ucn_section.ts
rm -f platform/src/lib/tools/structured/query_cdlm_link.ts
rm -f platform/src/lib/tools/structured/query_resonance.ts
rm -f platform/src/lib/tools/structured/query_chart_fact.ts
rm -f platform/src/lib/tools/structured/query_dasha.ts
rm -f platform/src/lib/tools/structured/query_patterns.ts
rm -f platform/src/lib/tools/structured/query_contradictions.ts
rm -f platform/src/lib/tools/structured/query_clusters.ts
rm -f platform/src/lib/tools/structured/query_resonances_l3.ts
```

### WS-0 Step 2c: Delete legacy ETL, bootstrap, and integrity scripts

```bash
rm -f platform/src/scripts/etl/msr_etl.ts
rm -f platform/src/scripts/etl/msr_loader.ts
rm -f platform/scripts/grounding/msr_grounding_pipeline.ts
rm -f platform/scripts/grounding/apply_grounded_citations.ts
rm -f platform/scripts/grounding/seed_and_ground_msr.py
rm -f platform/scripts/integrity/audit_msr_forensic.py
rm -f platform/scripts/integrity/audit_ucn_msr.py
rm -f platform/scripts/integrity/audit_cgm_supports.py
rm -f platform/scripts/bootstrap/bootstrap_chart_facts_kp.ts
rm -f platform/scripts/bootstrap/bootstrap_chart_facts_shadbala.ts
rm -f platform/scripts/bootstrap/bootstrap_chart_facts_bhava_bala.ts
rm -f platform/scripts/bootstrap/bootstrap_chart_facts_ashtakavarga.ts
rm -f platform/scripts/bootstrap/bootstrap_chart_facts_varshphal.ts
rm -f platform/scripts/bootstrap/bootstrap_chart_facts_upagraha.ts
rm -f platform/scripts/bootstrap/lib/chart_facts_ingester.ts
rm -f platform/scripts/bootstrap/bootstrap_multi_school_kp.ts
rm -f platform/scripts/bootstrap/bootstrap_multi_school_jaimini.ts
rm -f platform/scripts/bootstrap/lib/classical_text_embedder.ts
rm -f platform/scripts/bootstrap/lib/classical_text_chunker.ts
```

### WS-0 Step 2d: Delete legacy API routes

```bash
rm -f platform/src/app/api/citations/preview/route.ts
rm -f platform/src/app/api/admin/mcp/health/calibration/route.ts
```

### WS-0 Step 2e: Edit — strip MSR/UCN/CDLM/CGM/RM keys from SAFE_ASSET_MAP

File: `platform/src/app/api/mcp/asset/route.ts`

Remove the following keys from `SAFE_ASSET_MAP` (keep `FORENSIC`, `LEL`, `MACRO_PLAN`, `PROJECT_ARCHITECTURE`, `GOVERNANCE_*`, and any other governance/canonical archive keys):
- `MSR` → `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`
- `UCN` → `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md`
- `CDLM` → `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`
- `CGM` → `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md`
- `RM` → `025_HOLISTIC_SYNTHESIS/RM_v2_0.md`

These synthesis artifacts are superseded by the Brahma L2 Bodha layer. The `read_asset` tool should not serve them as live data sources.

### WS-0 Step 2f: Edit — remove rag/ router mounts from main.py

File: `platform/python-sidecar/main.py`

Remove any `include_router` calls and imports for:
- `rag_retrieve`, `rag_router`, `rag_synthesize` routers (prefixed `/rag/*`)

These endpoints are dead after Step 2a deletes the rag/ module.

### WS-0 Step 2g: Edit — re-point audit.ts legacy table row counts

File: `platform-mcp/src/audit.ts`

Replace any `chart_facts` and `msr_signals` row-count queries with Brahma equivalents:
- `chart_facts` counts → `ganita_positions`, `ganita_dashas` (or whichever Brahma table is the logical successor)
- `msr_signals` counts → `bodha_signals`

Keep the audit structure; only change the table names queried.

### WS-0 Step 2h: Edit — strip dead feature flags from feature_flags.ts

File: `platform/src/lib/config/feature_flags.ts`

Remove the following flag constants entirely (and all their usages — search with `grep -rn FLAG_NAME platform/src`; for each usage, inline the hardcoded value: R8/R9/R10 flags that were permanently true → inline `true`; flags that were permanently false → inline `false`):

**R8 (COMPLETE, all permanently true):**
`R8_BRANCHES_ENABLED`, `R8_SEARCH_ENABLED`, `R8_FOLDERS_ENABLED`, `R8_TOKENS_ENABLED`, `R8_SLASH_ENABLED`, `R8_VISION_ENABLED`, `R8_EXPORT_ENABLED`

**R9 (COMPLETE, all permanently true):**
`R9_PROJECTS`, `R9_SEMANTIC_SEARCH`, `R9_PERSONAS`, `R9_TOOL_FLOW`

**R10 (COMPLETE — inline values as noted):**
- `R10_EDIT_WHILE_STREAMING` → inline `false` (default false, high-risk, hardcode off)
- `R10_SMOOTH_STREAM_V2` → inline `true`
- `R10_REASONING_STEPS` → inline `true`
- `R10_AUTO_RETRY` → inline `false`

**R11 (COMPLETE, all permanently true or dead):**
`R11V2_MULTI_PROVIDER_PARITY`, `R11V2_USE_ADAPTERS`, `R11V2_CAPABILITY_TELEMETRY`
`R11B_LOOK_AND_FEEL`
`R11C_SMOOTH_STREAM_V3`, `R11C_TOOL_CARDS`
`R11D_ANTHROPIC_CACHE`, `R11D_GEMINI_CACHE` (dead — NOT_IMPLEMENTED), `R11D_PROMPT_LAYOUT`
`R11E_ANTHROPIC_LOOP`, `R11E_GEMINI_LOOP`, `R11E_OPENAI_LOOP`, `R11E_DEEPSEEK_LOOP`, `R11E_NVIDIA_LOOP`

**Inline `process.env` checks (not in feature_flags.ts, in components):**
Grep for and inline these:
- `NEXT_PUBLIC_MARSYS_FLAG_R10_SELECTIVE_SHARE` → `true`
- `NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE` → `true`
- `NEXT_PUBLIC_MARSYS_FLAG_R10_CITATION_FRESHNESS` → `true`
- `NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES` → `true`
- `NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID` → `true`
- `NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES` → `true`

**Verification after flag removal:**
```bash
npm run typecheck 2>&1 | tail -20
# Expect: 0 errors (or only known-pre-existing errors from KNOWN_PRE_EXISTING_FAILURES.md)
```

---

## §4 Surface 3 — Deploy/CI pipeline STRIP

### WS-0 Step 3a: Edit `.github/workflows/deploy.yml`

**Remove these sections/lines:**

1. **`cp -r 025_HOLISTIC_SYNTHESIS` copy step** in `deploy-web` build context preparation block (both occurrences — `build-check` job and `deploy-web` job)
2. **`cp -r 035_DISCOVERY_LAYER` copy step** in `deploy-web` build context preparation block
3. **`cp -r 025_HOLISTIC_SYNTHESIS` copy step** in `deploy-mcp` build context preparation block
4. **`marsys-build-pipeline-job` timeout/max-retries step** — the `gcloud run jobs update marsys-build-pipeline-job` step in `deploy-web` (it runs `|| true`; the job is deleted)
5. **`CONSUME_UI_V2_ENABLED: 'true'`** from the `env_vars:` block in `deploy-web` job

**Graduate these build-args (remove from `build-args:` block, add as Dockerfile ENV or hardcode):**

Remove from the rotating `build-args` list in both `build-check` and `deploy-web`:
- `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=true`
- `NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL=true`
- `NEXT_PUBLIC_MARSYS_FLAG_R9_SEMANTIC_SEARCH=true`
- `NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW=true`
- `NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS=true`
- `NEXT_PUBLIC_MARSYS_ANTHROPIC_HIDDEN=true` (permanent product decision)

For each removed build-arg, either:
- Add to `platform/Dockerfile` as `ENV NEXT_PUBLIC_MARSYS_FLAG_xxx=true` (if the flag still has code gates after Step 2h — i.e., only if Step 2h did NOT inline these), **OR**
- Confirm they are already inlined in Step 2h → no Dockerfile change needed.

**Add missing build-arg:**
- `NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS=true` (currently undeclared in build-args, ARG in Dockerfile — add explicitly to close the gap)

### WS-0 Step 3b: Delete `cloudbuild.yaml`

```bash
rm cloudbuild.yaml
```

The file is intentionally `steps: []`. The active pipeline is 100% in `deploy.yml`. Leaving it risks accidental Cloud Build trigger wiring.

### WS-0 Step 3c: Verify no load-bearing gate was touched

```bash
# Confirm all load-bearing CI steps still present in ci.yml
grep -E "typecheck|unit-tests|secret-scan|coverage-gate|naming-lint|governance-gates|planner-regression|icr-pr-gate" .github/workflows/ci.yml
# Expected: all 8 job names present

# Confirm brahma-conductor.yml untouched
git diff HEAD -- .github/workflows/brahma-conductor.yml
# Expected: no diff

# Confirm deploy jobs still present
grep -E "deploy-web|deploy-sidecar|deploy-mcp" .github/workflows/deploy.yml
# Expected: all three present
```

### WS-0 Step 3d: Cloud Run env-var sweep (orphan MARSYS_FLAG_*)

Cloud Run env-vars are a separate persistence surface from `deploy.yml` — `deploy-cloudrun@v2` merges new vars rather than replacing them (lesson `deploy_cloudrun_env_merge`). So a flag inlined in Step 2h + removed from deploy.yml may still be live on the running revision. Sweep it.

```bash
# List every env-var on the live amjis-web revision
gcloud run services describe amjis-web \
  --region=asia-south1 \
  --format='value(spec.template.spec.containers[0].env[].name)' \
  | tr ';' '\n' \
  | grep -E '^MARSYS_FLAG_|^NEXT_PUBLIC_MARSYS_FLAG_|^CONSUME_UI_V2_ENABLED$' \
  | sort -u | tee /tmp/ws0_live_flags.txt

# Cross-check against feature_flags.ts: any live env-var whose flag constant no longer exists in
# feature_flags.ts post-Step-2h is orphaned and should be removed from Cloud Run.
while IFS= read -r flag; do
  if ! grep -q "$(echo "$flag" | sed 's/^NEXT_PUBLIC_//')" platform/src/lib/config/feature_flags.ts 2>/dev/null; then
    echo "ORPHAN (no constant in feature_flags.ts): $flag"
  fi
done < /tmp/ws0_live_flags.txt | tee /tmp/ws0_orphan_flags.txt

# Remove each orphan flag from Cloud Run (one --remove-env-vars per flag, or comma-sep)
# Native review the list first; execute when approved.
ORPHANS=$(awk '{print $NF}' /tmp/ws0_orphan_flags.txt | tr '\n' ',' | sed 's/,$//')
if [ -n "$ORPHANS" ]; then
  gcloud run services update amjis-web \
    --region=asia-south1 \
    --remove-env-vars="$ORPHANS"
fi

# Same sweep for amjis-sidecar and amjis-mcp
for svc in amjis-sidecar amjis-mcp; do
  gcloud run services describe $svc --region=asia-south1 \
    --format='value(spec.template.spec.containers[0].env[].name)' \
    | tr ';' '\n' | grep -E '^MARSYS_FLAG_|^NEXT_PUBLIC_MARSYS_FLAG_' \
    | sort -u | tee /tmp/ws0_live_flags_$svc.txt
done
# Manual review; remove orphans the same way.
```

---

## §5 Surface 4 — Final verification

### WS-0 Step 4: Zero-legacy-citation scan (auto-derived from §2 DROP list)

This grep uses the **same `LEGACY_TABLES` alternation from Step 2-PRE** so the audit and the final assertion are guaranteed identical.

```bash
# Re-use the LEGACY_TABLES env-var from Step 2-PRE (or paste it again if a fresh shell)
LEGACY_TABLES='audit_job_runs|ayanamsha_registry|build_checkpoints|build_dependencies|build_engine_versions|build_events|build_manifests|build_notifications|build_steps|builds|builds_staging|chart_ayanamsha_reports|chart_dashas|chart_documents|chart_facts|chart_facts_history|chart_facts_staging|chart_facts_supersedence|chat_attachments|classical_attributions|classical_chunks|classical_texts|cluster_register|cluster_register_staging|context_assembly_log|contradiction_register|contradiction_register_staging|convergence_scores|data_source_expected|dasha_periods|divisional_charts|documents|eclipses|eclipses_retrogrades|eclipses_staging|engine_versions|ephemeris_daily|ephemeris_daily_staging|g29_timing_rules|gate_change_log|kp_sublords|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_chart_lattice_snapshots|l25_derivation_graph_edges|l25_derivation_graph_nodes|l25_divergence_ledger|l25_msr_signals|l25_msr_signals_staging|l25_negative_space_map|l25_pattern_catalog|l25_rm_resonances|l25_rm_resonances_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_vedha_anchor_interactions|llm_catalog_snapshot|llm_config_audit|llm_model_health|llm_param_override|llm_stack_routing_override|mcp_audit_findings|mcp_bundle_cache|message_feedback|messages|msr_signals|multi_school_stances|notification_views|panchanga_daily|panchanga_daily_staging|pattern_register|pattern_register_staging|prediction_ledger|predictions|pyramid_layers|query_plans|rag_chunks|rag_chunks_staging|rag_embeddings|rag_embeddings_staging|rag_feedback|rag_graph_edges|rag_graph_nodes|rag_queries|rag_reproducibility_failures|rag_retrievals|reports|resonance_register|resonance_register_staging|retrogrades|retrogrades_staging|sade_sati_cycles|sade_sati_phases|sade_sati_phases_staging|sankranti_table|saturn_sign_changes|school_analysis_runs|school_convergence_index|school_disagreements|school_signal_coverage|shadbala|signal_states|tajaka_annual|tool_caveats|varshaphala'

# No active code may cite any legacy table (migrations excluded — they're frozen history)
grep -rEn "(${LEGACY_TABLES})" \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git \
  --exclude-dir=00_ARCHITECTURE --exclude-dir=025_HOLISTIC_SYNTHESIS \
  --exclude-dir=035_DISCOVERY_LAYER --exclude-dir=01_FACTS_LAYER \
  --exclude-dir=migrations \
  platform/src platform/python-sidecar platform-mcp/src \
  brahmagyan/ panchang_engine/ \
  2>/dev/null

# Expected: ZERO results
# If any results → AC-3 fails. Disposition each per the Step 2-PRE rules. Re-run until 0.
```

```bash
# No code may read 025_HOLISTIC_SYNTHESIS or 035_DISCOVERY_LAYER as live data
grep -rn "025_HOLISTIC_SYNTHESIS\|035_DISCOVERY_LAYER" \
  platform/src platform/python-sidecar platform-mcp/src \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  -l 2>/dev/null

# Expected: zero results (governance .md files in 00_ARCHITECTURE may reference them — that's OK; CODE files must not)
```

### WS-0 Step 5: TypeScript compile check

```bash
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error"
# Expected: 0 errors (or only errors in KNOWN_PRE_EXISTING_FAILURES.md)
```

### WS-0 Step 6: Python sidecar unit tests

```bash
cd platform && python -m pytest python-sidecar/tests/ \
  --ignore=python-sidecar/tests/integration \
  -q 2>&1 | tail -10
# Expected: all pass
```

### WS-0 Step 7: Final Brahma integrity assertion

```sql
-- Run on prod after all steps complete
-- Brahma tables must be alive and populated
SELECT table_name, 
       (xpath('/row/c/text()', query_to_xml('SELECT count(*) AS c FROM '||table_name, false, true, '')))[1]::text::int AS row_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'ganita_positions', 'ganita_dashas',
    'bodha_signals', 'bodha_graph',
    'kala_timeline', 'phala_anchors',
    'mimamsa_predictions'
  )
ORDER BY table_name;

-- Dropped tables must be gone
SELECT count(*) AS legacy_tables_remaining
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'chart_facts', 'msr_signals', 'rag_chunks', 'panchanga_daily',
    'l25_msr_signals', 'build_manifests', 'school_convergence_index',
    'ephemeris_daily', 'classical_texts', 'predictions'
  );
-- Expected: 0
```

---

## §6 Commit discipline

- **One commit per surface**: Surface 1 (migration SQL), Surface 2 (code), Surface 3 (pipeline)
- Commit message format: `chore(legacy-purge): WS-0 Surface N — <summary>`
- Do NOT squash the three surface commits — they must be individually revertable (even though no backup exists, the commit history is the audit trail)
- Tag the final commit: `git tag legacy-purge-v2-complete`

---

## §7 Known fallback activations (safe, expected)

These code paths will silently activate their fallback logic after the purge — this is correct behavior:

| File | Change | Fallback |
|------|--------|---------|
| `panchang_engine/panchang_daily_reader.py` | `panchanga_daily` table gone | falls back to engine-direct computation |
| `brahmagyan/phala/muhurta.py` | `panchanga_daily` table gone | `Defaults when panchanga_daily is unavailable` branch |

Both fallbacks were verified present before this brief was authored. No user-facing degradation expected — engine-direct panchanga is the Brahma-native path anyway.

---

## §8 Out of WS-0 scope — flagged for follow-up

These are legacy surfaces this brief deliberately does **not** touch. Each is tracked here so a follow-up brief picks them up; failing to enumerate them is how legacy leaks back in later.

| # | Surface | Why deferred | Follow-up |
|---|---------|--------------|-----------|
| 1 | **GCS bucket contents** — `madhav-marsys-build-artifacts` legacy JSONL, chart-documents bucket residue | INFRA_RECONCILIATION says "KEEP · purge contents" — needs an `gsutil` sweep with a path allowlist (Brahma `brahmagyan/_/`, `ganita/_/`, … prefixes vs legacy `l25/_/`, `rag/_/`, etc.). Outside DB+code+pipeline scope. | Author `CLAUDECODE_BRIEF_WS0B_GCS_PURGE_v1_0.md` before WS-2 starts ingesting GCS-sourced data. |
| 2 | **`CAPABILITY_MANIFEST.json` legacy asset entries** | The manifest is governance metadata (canonical-path catalog), not live product code. Editing it touches `00_ARCHITECTURE/` which is `must_not_touch` in this brief. | Re-base the manifest onto the L0–L5 + new-asset set as the first step of the M5 governance re-base (CLAUDE.md §C item 2). |
| 3 | **Historical SQL migrations under `platform/supabase/migrations/`** | Migrations 001–~170 are frozen history — they CREATE tables that now don't exist, but they aren't *executed* against a fresh DB (the DB already exists). They're a paper trail. | Once WS-2 is closed, take a baseline snapshot and squash to a single `0001_brahma_baseline.sql`. Not before — keeping history is cheap insurance during the depth build. |
| 4 | **Cloud Tasks queue `amjis-build-queue`** | INFRA_RECONCILIATION lists it as decommissioned; verify it's actually gone. | One-liner check: `gcloud tasks queues describe amjis-build-queue --location=asia-south1 2>&1 \| grep -E "NOT_FOUND\|state:"`. Delete if it still exists. |
| 5 | **Memorystore `amjis-cache` (Redis)** | INFRA_RECONCILIATION says DROP for cost; not a *legacy data* problem — purely cost. | INFRA provisioning session item, not WS-0. |
| 6 | **The `ANTHROPIC_API_KEY` secret in Secret Manager** | Removing it touches secret-manager IAM, separate from this brief's surfaces. | One-liner: `gcloud secrets delete ANTHROPIC_API_KEY --quiet` after confirming zero callers. |
| 7 | **Legacy MARSYS_FLAG_* env vars on the Cloud Run revision** | Now *in scope* via Step 3d (this v1.1 amendment). Listing here as "moved from out-of-scope to in-scope" for the change record. | Step 3d. |
