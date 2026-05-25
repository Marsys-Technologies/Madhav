# DAR Setup Prompt
# Run this ONCE in a Claude Code session on the MAIN branch
# Purpose: create worktree, conductor infrastructure, all 26 session briefs
# After this completes, switch to the worktree and run DAR_CONDUCTOR_KICKOFF_PROMPT.md

---

You are a setup agent for the Data Asset Reconciliation (DAR) workstream on the MARSYS-JIS project.
Working directory: /Users/Dev/Vibe-Coding/Apps/Madhav (main branch)

Your job is to create the worktree and all conductor infrastructure so that the Conductor can run autonomously. Execute every step below completely. Do not stop early.

---

## STEP 1 — Create the worktree and branch

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout -b feature/data-asset-reconciliation 2>/dev/null || echo "branch exists"
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset feature/data-asset-reconciliation 2>/dev/null || echo "worktree exists"
git worktree list
```

## STEP 2 — Create all required directories

```bash
mkdir -p /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs
mkdir -p /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/99_ARCHIVE/025_HOLISTIC_SYNTHESIS
```

## STEP 3 — Copy the master plan into the worktree

```bash
cp /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md \
   /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md
cp /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/DATA_ASSET_AUDIT_AND_RECONCILIATION_v1_0.md \
   /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DATA_ASSET_AUDIT_AND_RECONCILIATION_v1_0.md
```

## STEP 4 — Create session_queue.yaml

Write the following file to /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml:

```yaml
# DAR session_queue.yaml — Data Asset Reconciliation
# Conductor reads this file before every turn
# Status: PENDING / IN_PROGRESS / COMPLETE / FAILED / HUMAN_GATE / HUMAN_GATE_DONE

meta:
  workstream: data-asset-reconciliation
  branch: feature/data-asset-reconciliation
  worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  master_plan: 00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md
  conductor_log: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CONDUCTOR_LOG.md
  created: 2026-05-25
  total_sessions: 26

phases:
  - id: 1
    name: "Code fixes + governance"
    sessions: [DAR-P1-S1, DAR-P1-S2, DAR-P1-S3, DAR-P1-S4]
  - id: 2
    name: "DB migrations + baseline"
    sessions: [DAR-P2-S5, DAR-HG-1, DAR-P2-S6]
  - id: 3
    name: "MSR v5.0 pipeline cascade"
    sessions: [DAR-P3-S7, DAR-P3-S8, DAR-P3-S9, DAR-P3-S10]
  - id: 4
    name: "chart_facts enhancement"
    sessions: [DAR-P4-S11, DAR-P4-S12, DAR-P4-S13, DAR-P4-S14]
  - id: 5
    name: "MSR B.3 grounding"
    sessions: [DAR-P5-S15, DAR-P5-S16, DAR-P5-S17, DAR-P5-S18, DAR-P5-S19, DAR-P5-S20]
  - id: 6
    name: "MEAN_NODE ephemeris rebuild"
    sessions: [DAR-P6-S21, DAR-HG-3, DAR-P6-S22]
  - id: 7
    name: "Integration testing + sign-off"
    sessions: [DAR-P7-S23, DAR-P7-S24, DAR-P7-S25, DAR-P7-S26, DAR-HG-4]

sessions:
  - id: DAR-P1-S1
    phase: 1
    name: "Blocking code fixes — MCP asset route + ICR confirm + manifest_overrides + test fixture"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S1.md
    status: PENDING
    type: code
    gate_commands:
      - "! grep -q 'MSR_v3_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/src/app/api/mcp/asset/route.ts"
      - "! grep -q 'MSR_v3_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/src/app/api/icr/confirm/route.ts"
      - "! grep -q 'MSR_v3_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/manifest_overrides.yaml"
      - "! grep -q 'MSR_v3_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/src/scripts/etl/__tests__/msr_parser.test.ts"
      - "! test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml"

  - id: DAR-P1-S2
    phase: 1
    name: "Python pipeline MSR source + EXPECTED_COUNT — all 7 hardcoded locations"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S2.md
    status: PENDING
    type: code
    gate_commands:
      - "! grep -rn 'MSR_v3_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/pipeline/ --include='*.py'"
      - "grep -q 'EXPECTED_COUNT = 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/pipeline/extractors/msr_extractor.py"
      - "grep -q 'EXPECTED_COUNT = 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/pipeline/writers/msr_signals_writer.py"
      - "grep -q 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/rag/chunkers/msr_signal.py"

  - id: DAR-P1-S3
    phase: 1
    name: "Archive MSR v3+v4 + GCS_LAYOUT v1.1 + LEL count corrections across 9 files"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S3.md
    status: PENDING
    type: code
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md"
      - "! test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
      - "! test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md"
      - "grep -q 'version: 1.1' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/GCS_LAYOUT_v1_0.md"
      - "grep -q '57 events' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CAPABILITY_MANIFEST.json"

  - id: DAR-P1-S4
    phase: 1
    name: "Mirror pair sync — .geminirules + .gemini/project_state.md (MP.1/MP.2/MP.9)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S4.md
    status: PENDING
    type: governance
    gate_commands:
      - "grep -q 'PHASE_M5_PLAN' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/.geminirules"
      - "grep -q '57 events' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/.geminirules"
      - "grep -q 'MCP Transformation' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/.geminirules"

  - id: DAR-P2-S5
    phase: 2
    name: "Migration safety analysis + HG-1 apply instructions document"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S5.md
    status: PENDING
    type: code
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md"
      - "grep -q 'migration_116' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md"
      - "grep -q 'migration_117' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md"
      - "grep -q 'rollback' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md"

  - id: DAR-HG-1
    phase: 2
    name: "HUMAN GATE — Apply migrations 116+117 to production DB"
    type: human_gate
    status: PENDING
    human_action: |
      Read: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md
      Run:
        psql "$DATABASE_URL" -f platform/migrations/116_trace_mcp_tool_column.sql
        psql "$DATABASE_URL" -f platform/migrations/117_audience_tier_acharya_enum.sql
      Append confirmed rows to: 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
      Signal done:
        touch /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_COMPLETE
    resume_signal: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_COMPLETE

  - id: DAR-P2-S6
    phase: 2
    name: "DB baseline state report — confirm migrations + msr_signals source + row counts"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S6.md
    status: PENDING
    type: data
    depends_on: [DAR-HG-1]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'migration_116: CONFIRMED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'migration_117: CONFIRMED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'msr_signals_source:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"

  - id: DAR-P3-S7
    phase: 3
    name: "MSR v5.0 pipeline dry-run — verify 573 signals extract without gate rejection"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S7.md
    status: PENDING
    type: data
    depends_on: [DAR-P1-S2]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md"
      - "grep -q 'signals_extracted: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md"
      - "grep -q 'gate_check: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md"

  - id: DAR-P3-S8
    phase: 3
    name: "Load MSR v5.0 into msr_signals (migration-009) + l25_msr_signals (migration-018)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S8.md
    status: PENDING
    type: data
    depends_on: [DAR-P3-S7, DAR-P2-S6]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"
      - "grep -q 'msr_signals_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"
      - "grep -q 'l25_msr_signals_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"
      - "grep -q 'source_file: MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"

  - id: DAR-P3-S9
    phase: 3
    name: "Rebuild MSR rag_chunks from v5.0 (573 chunks) + re-embed vectors"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S9.md
    status: PENDING
    type: data
    depends_on: [DAR-P3-S8]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md"
      - "grep -q 'msr_rag_chunks_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md"
      - "grep -q 'embed_status: COMPLETE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md"

  - id: DAR-P3-S10
    phase: 3
    name: "Rebuild four registers + school_signal_coverage (4011 rows) + refresh school_convergence_index MV"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S10.md
    status: PENDING
    type: data
    depends_on: [DAR-P3-S8]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'school_signal_coverage_count: 4011' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'contradiction_register: REBUILT' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'school_convergence_index: REFRESHED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"

  - id: DAR-P4-S11
    phase: 4
    name: "chart_facts extractors — Ashtakavarga + Sthira Karakas + Upagrahas + Bhrigu Bindu"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S11.md
    status: PENDING
    type: code
    gate_commands:
      - "grep -q 'ashtakavarga' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'sthira_karaka' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'upagraha' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'bhrigu_bindu' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"

  - id: DAR-P4-S12
    phase: 4
    name: "chart_facts extractors — Yogi/Avayogi + Mrityu Bhaga + Chalit kinetic + Avastha + longevity"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S12.md
    status: PENDING
    type: code
    gate_commands:
      - "grep -q 'yogi_avayogi' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'mrityu_bhaga' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'avastha' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"

  - id: DAR-P4-S13
    phase: 4
    name: "chart_facts extractors — Narayana Dasha + Moola + Sudasa + Ishta/Kashta + Pancha-Vargeeya"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S13.md
    status: PENDING
    type: code
    gate_commands:
      - "grep -q 'narayana_dasha' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'moola_dasha\|sudasa' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'ishta_kashta\|pancha_vargeeya' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"

  - id: DAR-P4-S14
    phase: 4
    name: "Load enhanced chart_facts to DB + update CAPABILITY_MANIFEST + verify MCP access"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S14.md
    status: PENDING
    type: data
    depends_on: [DAR-P4-S11, DAR-P4-S12, DAR-P4-S13]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md"
      - "grep -q 'chart_facts_row_count:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md"
      - "grep -q 'mcp_query_chart_facts: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md"

  - id: DAR-P5-S15
    phase: 5
    name: "Build derivation_ledger stub generator — v6_ids_consumed → FORENSIC path+line mapping"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S15.md
    status: PENDING
    type: code
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/tools/generate_derivation_ledger_stubs.py"
      - "python3 /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/tools/generate_derivation_ledger_stubs.py --dry-run 2>&1 | grep -q 'stubs_generated'"

  - id: DAR-P5-S16
    phase: 5
    name: "B.3 grounding backfill — Lagna + Sun + Moon + Mars signal domains"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S16.md
    status: PENDING
    type: data
    depends_on: [DAR-P5-S15]
    gate_commands:
      - "grep -q 'grounded_lagna: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_sun: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_moon: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_mars: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S17
    phase: 5
    name: "B.3 grounding backfill — Mercury + Jupiter + Venus + Saturn signal domains"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S17.md
    status: PENDING
    type: data
    depends_on: [DAR-P5-S16]
    gate_commands:
      - "grep -q 'grounded_mercury: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_jupiter: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_venus: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_saturn: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S18
    phase: 5
    name: "B.3 grounding backfill — house-based + dasha + divisional signal domains"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S18.md
    status: PENDING
    type: data
    depends_on: [DAR-P5-S17]
    gate_commands:
      - "grep -q 'grounded_house_domain: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_dasha: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S19
    phase: 5
    name: "B.3 grounding backfill — Nadi/BNN + Yogini/Tajaka new signals (SIG.MSR.515–573)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S19.md
    status: PENDING
    type: data
    depends_on: [DAR-P5-S18]
    gate_commands:
      - "grep -q 'grounded_nadi_bnn: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_yogini_tajaka: DONE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S20
    phase: 5
    name: "B.3 grounding validation + MSR v5.1 version bump + update all registries"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S20.md
    status: PENDING
    type: data
    depends_on: [DAR-P5-S19]
    gate_commands:
      - "grep -q 'version: 5.1' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
      - "grep -q 'total_grounded: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P6-S21
    phase: 6
    name: "Ephemeris pre-rebuild — confirm TRUE_NODE in production + verify runbook ready"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S21.md
    status: PENDING
    type: data
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "grep -q 'bootstrap_script_node_type: MEAN_NODE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md"

  - id: DAR-HG-3
    phase: 6
    name: "HUMAN GATE — Run ephemeris bootstrap (4–6 hours)"
    type: human_gate
    status: PENDING
    depends_on: [DAR-P6-S21]
    human_action: |
      Read: 00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md
      Run the bootstrap script as instructed. Estimated 4–6 hours.
      Signal done:
        touch /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG3_COMPLETE
    resume_signal: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG3_COMPLETE

  - id: DAR-P6-S22
    phase: 6
    name: "Post-ephemeris rebuild verification — spot-check Rahu at birth date + 50 random dates"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S22.md
    status: PENDING
    type: data
    depends_on: [DAR-HG-3]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'node_type_in_db: MEAN_NODE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'birth_date_rahu_spot_check: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'row_count: 657450' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'bhava_chalit_null_count: 0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"

  - id: DAR-P7-S23
    phase: 7
    name: "MCP tool layer comprehensive test — all 21 tools, all asset paths, all key counts"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S23.md
    status: PENDING
    type: test
    depends_on: [DAR-P3-S10, DAR-P4-S14, DAR-P5-S20, DAR-P6-S22]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'read_asset_MSR: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'query_signals_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'holistic_bundle: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'query_chart_facts: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'query_ephemeris_rahu: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'lel_count: 57' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"
      - "grep -q 'tools_pass: 21' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MCP_TEST_REPORT.md"

  - id: DAR-P7-S24
    phase: 7
    name: "Internal portal end-to-end smoke — pipeline re-run + chart_facts query + ICR target check"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S24.md
    status: PENDING
    type: test
    depends_on: [DAR-P7-S23]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"
      - "grep -q 'pipeline_smoke: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"
      - "grep -q 'icr_confirm_target: MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"

  - id: DAR-P7-S25
    phase: 7
    name: "Cross-asset integrity — validate all CGM/UCN/CDLM signal refs exist in DB; school_convergence parity"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S25.md
    status: PENDING
    type: test
    depends_on: [DAR-P7-S24]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'cgm_msr_refs: ALL_VALID' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'ucn_msr_refs: ALL_VALID' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'school_convergence_rows: 4011' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"

  - id: DAR-P7-S26
    phase: 7
    name: "Governance close — DAR_CLOSE_v1_0.md + drift_detector pass + SESSION_LOG entry"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S26.md
    status: PENDING
    type: governance
    depends_on: [DAR-P7-S25]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_CLOSE_v1_0.md"
      - "grep -q 'status: COMPLETE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_CLOSE_v1_0.md"
      - "python3 /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/governance/drift_detector.py 2>&1 | grep -qE 'exit.*0|PASS|no.*drift'"

  - id: DAR-HG-4
    phase: 7
    name: "HUMAN GATE — Review all test reports, approve merge to main, deploy"
    type: human_gate
    status: PENDING
    depends_on: [DAR-P7-S26]
    human_action: |
      Review reports in: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/
      Review DAR_CLOSE_v1_0.md
      If satisfied:
        cd /Users/Dev/Vibe-Coding/Apps/Madhav
        git merge feature/data-asset-reconciliation
        git push origin main
        Deploy: gcloud run deploy (amjis-web + amjis-sidecar + amjis-mcp)
        git tag dar-v1.0-complete
    resume_signal: none  # final gate — no automation after this
```

## STEP 5 — Create CONDUCTOR_LOG.md

Write the following file to /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CONDUCTOR_LOG.md:

```markdown
# DAR Conductor Log
# Append one entry per Conductor run (not per session)

## Run 1 — [DATE TO BE FILLED]
- Started: [timestamp]
- Sessions completed this run: []
- Halted at: [session_id or human_gate]
- Reason: [first run / human gate / failure]
- Resume from: [next session_id]
```

## STEP 6 — Create GROUNDING_PROGRESS.yaml (Phase 5 progress tracker)

Write to /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml:

```yaml
# MSR v5.0 B.3 Derivation-Ledger grounding progress
# Each session writes its domain key as DONE when complete
# S20 reads this to validate all domains complete before MSR v5.1 bump

grounded_lagna: PENDING
grounded_sun: PENDING
grounded_moon: PENDING
grounded_mars: PENDING
grounded_mercury: PENDING
grounded_jupiter: PENDING
grounded_venus: PENDING
grounded_saturn: PENDING
grounded_house_domain: PENDING
grounded_dasha: PENDING
grounded_nadi_bnn: PENDING
grounded_yogini_tajaka: PENDING
total_grounded: 0
last_updated: ~
```

## STEP 7 — Create all 22 session brief files

Create one .md file per code/data/governance session in /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/

Each brief follows this structure exactly:
- Frontmatter: session_id, phase, status, branch, worktree, may_touch list, must_not_touch list
- Context paragraph (why this session exists, what came before)
- Numbered steps (explicit, file-path-precise, no ambiguity)
- Acceptance criteria (grep/test commands matching the session's gate_commands in session_queue.yaml)
- Commit message template

Create briefs for: DAR-P1-S1, DAR-P1-S2, DAR-P1-S3, DAR-P1-S4, DAR-P2-S5, DAR-P2-S6,
DAR-P3-S7, DAR-P3-S8, DAR-P3-S9, DAR-P3-S10,
DAR-P4-S11, DAR-P4-S12, DAR-P4-S13, DAR-P4-S14,
DAR-P5-S15, DAR-P5-S16, DAR-P5-S17, DAR-P5-S18, DAR-P5-S19, DAR-P5-S20,
DAR-P6-S21, DAR-P6-S22,
DAR-P7-S23, DAR-P7-S24, DAR-P7-S25, DAR-P7-S26

Use the full brief content from DAR_MASTER_PLAN_v1_0.md §4 as the template for each.
For sessions not fully specified in §4, derive the brief from the session name and
the master plan's phase description, maintaining the same level of detail and precision.

## STEP 8 — Commit everything to the feature branch

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/
git add 00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md
git add 00_ARCHITECTURE/DATA_ASSET_AUDIT_AND_RECONCILIATION_v1_0.md
git add 99_ARCHIVE/
git status
git commit -m "dar: conductor infrastructure + session queue + 26 briefs for DAR workstream [governance]"
git log --oneline -3
```

## STEP 9 — Verify and report

```bash
echo "=== Worktree check ==="
git worktree list

echo "=== Session count check ==="
grep -c "id: DAR-" /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml

echo "=== Brief files check ==="
ls /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/ | wc -l

echo "=== SETUP COMPLETE ==="
echo "Next step: switch to worktree at /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset"
echo "Then paste the Conductor kickoff prompt from DAR_CONDUCTOR_KICKOFF_PROMPT.md"
```

Expected output:
- Worktree list shows both main and MadhavDataAsset
- Session count: 29 (26 code/data/test sessions + 3 human gates)
- Brief files: 26
```
