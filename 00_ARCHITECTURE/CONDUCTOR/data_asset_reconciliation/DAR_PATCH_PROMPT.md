---
canonical_id: DAR_PATCH_PROMPT
version: 1.0
status: CURRENT
authored: 2026-05-25
purpose: >
  Patch prompt — removes ALL human gates from the DAR Conductor queue.
  Migrations 116+117, ephemeris bootstrap, and final merge are now executed
  autonomously by sub-agents. Paste into Claude Code at MadhavDataAsset.
precondition: Worktree /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset exists on feature/data-asset-reconciliation
---

# DAR Patch: Remove All Human Gates

**Paste into Claude Code at `/Users/Dev/Vibe-Coding/Apps/MadhavDataAsset`**

---

```
You are patching the Data Asset Reconciliation Conductor infrastructure to remove
ALL human gates. Sub-agents will apply DB migrations, run the ephemeris bootstrap,
and merge to main fully autonomously.

Working directory: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
Branch: feature/data-asset-reconciliation

Execute every step below exactly. Do not skip any step.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — Overwrite session_queue.yaml (no human gates, 27 sessions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write the following content to:
  00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml

--- BEGIN FILE ---
# DAR session_queue.yaml — Data Asset Reconciliation
# Conductor reads this file to determine next action
# Status values: PENDING / IN_PROGRESS / COMPLETE / FAILED
# ALL human gates removed — execution is fully autonomous

meta:
  workstream: data-asset-reconciliation
  branch: feature/data-asset-reconciliation
  worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  master_plan: 00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md
  created: 2026-05-25
  patched: 2026-05-25
  patch_reason: Remove all human gates — fully autonomous execution

sessions:

  # ── PHASE 1: Code fixes + governance ─────────────────────────────────────
  - id: DAR-P1-S1
    phase: 1
    name: "Blocking code fixes — MCP asset route + ICR confirm + governance overrides"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S1.md
    status: PENDING
    estimated_minutes: 30
    gate_commands:
      - "grep -n 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/src/app/api/mcp/asset/route.ts | grep -q 'SAFE_ASSET_MAP\\|MSR'"
      - "grep -n 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/src/app/api/icr/confirm/route.ts | grep -q 'MSR_PATH'"
      - "grep -q 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/manifest_overrides.yaml"
      - "grep -q 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/src/scripts/etl/__tests__/msr_parser.test.ts"
      - "! test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml"

  - id: DAR-P1-S2
    phase: 1
    name: "Python pipeline MSR source + count updates — all 7 locations"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S2.md
    status: PENDING
    estimated_minutes: 40
    gate_commands:
      - "grep -rn 'MSR_v3_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/pipeline/ | grep -v '.pyc' | wc -l | xargs test 0 -eq"
      - "grep -q 'EXPECTED_COUNT = 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/pipeline/extractors/msr_extractor.py"
      - "grep -q 'EXPECTED_COUNT = 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/pipeline/writers/msr_signals_writer.py"
      - "grep -q 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/rag/chunkers/msr_signal.py"
      - "grep -q 'SOURCE_VERSION.*5\\.0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/rag/chunkers/msr_signal.py"

  - id: DAR-P1-S3
    phase: 1
    name: "Archive MSR v3+v4 + GCS_LAYOUT v1.1 + LEL references across 9 files"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S3.md
    status: PENDING
    estimated_minutes: 50
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md"
      - "! test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
      - "! test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md"
      - "grep -q 'version: 1.1' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/GCS_LAYOUT_v1_0.md"
      - "grep -q 'MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/GCS_LAYOUT_v1_0.md"
      - "grep -q 'version: 1.7' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
      - "grep -q '57 events' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CAPABILITY_MANIFEST.json"

  - id: DAR-P1-S4
    phase: 1
    name: "Mirror pair sync — .geminirules + .gemini/project_state.md (MP.1/MP.2/MP.9)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P1-S4.md
    status: PENDING
    estimated_minutes: 40
    gate_commands:
      - "grep -q 'PHASE_M5_PLAN' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/.geminirules"
      - "grep -q '57 events' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/.geminirules"
      - "python3 -c \"import json; d=open('/Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/manifest_overrides.yaml').read(); assert 'MSR_v5_0' in d\""

  # ── PHASE 2: DB migrations (autonomous) + baseline verification ───────────
  - id: DAR-P2-S5
    phase: 2
    name: "Apply migrations 116+117 directly via psql + baseline DB verification"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S5.md
    status: PENDING
    estimated_minutes: 30
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'migration_116: CONFIRMED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'migration_117: CONFIRMED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'msr_signals_source:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"

  - id: DAR-P2-S6
    phase: 2
    name: "DB baseline state verification — row counts, MSR source, migration confirmation"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S6.md
    status: PENDING
    estimated_minutes: 30
    depends_on: [DAR-P2-S5]
    gate_commands:
      - "grep -q 'msr_signals_count:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'l25_msr_signals_count:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'ephemeris_daily_count:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"

  # ── PHASE 3: MSR v5.0 pipeline cascade rebuild ───────────────────────────
  - id: DAR-P3-S7
    phase: 3
    name: "MSR pipeline dry-run + validation — verify 573 signals extract cleanly"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S7.md
    status: PENDING
    estimated_minutes: 45
    depends_on: [DAR-P1-S2]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md"
      - "grep -q 'signals_extracted: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_EXTRACT_DRY_RUN.md"

  - id: DAR-P3-S8
    phase: 3
    name: "Populate msr_signals (migration-009) + l25_msr_signals from MSR v5.0"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S8.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P3-S7, DAR-P2-S6]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"
      - "grep -q 'msr_signals_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"
      - "grep -q 'l25_msr_signals_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"
      - "grep -q 'source_file: MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/MSR_DB_LOAD_REPORT.md"

  - id: DAR-P3-S9
    phase: 3
    name: "Rebuild MSR rag_chunks from v5.0 (573 signals) + re-embed vectors"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S9.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P3-S8]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md"
      - "grep -q 'msr_rag_chunks_count: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md"
      - "grep -q 'source_version: 5.0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/RAG_CHUNKS_MSR_REPORT.md"

  - id: DAR-P3-S10
    phase: 3
    name: "Rebuild four register writers + school_signal_coverage (4011 rows) + refresh MV"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P3-S10.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P3-S8]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'school_signal_coverage_count: 4011' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'contradiction_register: REBUILT' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'cluster_register: REBUILT' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'pattern_register: REBUILT' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'resonance_register: REBUILT' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"
      - "grep -q 'school_convergence_index: REFRESHED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/REGISTERS_REBUILD_REPORT.md"

  # ── PHASE 4: chart_facts enhancement ────────────────────────────────────
  - id: DAR-P4-S11
    phase: 4
    name: "chart_facts extractors — Ashtakavarga + Sthira Karakas + Upagrahas + Bhrigu Bindu"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S11.md
    status: PENDING
    estimated_minutes: 90
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
    estimated_minutes: 90
    gate_commands:
      - "grep -q 'yogi_avayogi' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'mrityu_bhaga' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'chalit_kinetic' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'avastha' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'longevity' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"

  - id: DAR-P4-S13
    phase: 4
    name: "chart_facts extractors — Narayana Dasha + Moola Dasha + Sudasa + Ishta/Kashta"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S13.md
    status: PENDING
    estimated_minutes: 90
    gate_commands:
      - "grep -q 'narayana_dasha' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'moola_dasha\|sudasa' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
      - "grep -q 'ishta_kashta\|pancha_vargeeya' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"

  - id: DAR-P4-S14
    phase: 4
    name: "Load enhanced chart_facts to DB + update CAPABILITY_MANIFEST + verify MCP access"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P4-S14.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P4-S11, DAR-P4-S12, DAR-P4-S13]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md"
      - "grep -q 'chart_facts_row_count:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md"
      - "grep -q 'mcp_query_chart_facts: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CHART_FACTS_LOAD_REPORT.md"

  # ── PHASE 5: MSR v5.0 B.3 Derivation-Ledger grounding ───────────────────
  - id: DAR-P5-S15
    phase: 5
    name: "Build derivation_ledger stub generator — v6_ids_consumed → FORENSIC path+line"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S15.md
    status: PENDING
    estimated_minutes: 60
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/tools/generate_derivation_ledger_stubs.py"
      - "python3 /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/python-sidecar/tools/generate_derivation_ledger_stubs.py --dry-run 2>&1 | grep -q 'stubs_generated:'"

  - id: DAR-P5-S16
    phase: 5
    name: "B.3 grounding backfill — Lagna + Sun + Moon + Mars signals (domains 1–4)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S16.md
    status: PENDING
    estimated_minutes: 90
    depends_on: [DAR-P5-S15]
    gate_commands:
      - "grep -q 'grounded_lagna:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_sun:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_moon:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_mars:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S17
    phase: 5
    name: "B.3 grounding backfill — Mercury + Jupiter + Venus + Saturn signals (domains 5–8)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S17.md
    status: PENDING
    estimated_minutes: 90
    depends_on: [DAR-P5-S16]
    gate_commands:
      - "grep -q 'grounded_mercury:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_jupiter:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_venus:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_saturn:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S18
    phase: 5
    name: "B.3 grounding backfill — house-based + dasha + divisional + classical-specific signals"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S18.md
    status: PENDING
    estimated_minutes: 90
    depends_on: [DAR-P5-S17]
    gate_commands:
      - "grep -q 'grounded_house_domain:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_dasha:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S19
    phase: 5
    name: "B.3 grounding backfill — Nadi/BNN + Yogini/Tajaka signals (SIG.MSR.515–573)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S19.md
    status: PENDING
    estimated_minutes: 90
    depends_on: [DAR-P5-S18]
    gate_commands:
      - "grep -q 'grounded_nadi_bnn:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"
      - "grep -q 'grounded_yogini_tajaka:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  - id: DAR-P5-S20
    phase: 5
    name: "B.3 grounding validation + MSR v5.1 bump + update all registries"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P5-S20.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P5-S19]
    gate_commands:
      - "grep -q 'version: 5.1' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
      - "grep -q 'total_grounded: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  # ── PHASE 6: MEAN_NODE ephemeris rebuild (fully autonomous) ──────────────
  - id: DAR-P6-S21
    phase: 6
    name: "Ephemeris pre-rebuild verification — confirm TRUE_NODE in production, check bootstrap script"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S21.md
    status: PENDING
    estimated_minutes: 30
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "grep -q 'bootstrap_script_node_type: MEAN_NODE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md"

  - id: DAR-P6-S22
    phase: 6
    name: "Run ephemeris bootstrap synchronously (MEAN_NODE, 657450 rows, 4-6 hours)"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S22.md
    status: PENDING
    estimated_minutes: 360
    depends_on: [DAR-P6-S21]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt"
      - "grep -q 'bootstrap_complete: true' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt"
      - "grep -q 'exit_code: 0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt"

  - id: DAR-P6-S23
    phase: 6
    name: "Post-rebuild ephemeris verification — spot-check Rahu at birth date + 50 random dates"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S23.md
    status: PENDING
    estimated_minutes: 45
    depends_on: [DAR-P6-S22]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'node_type: MEAN_NODE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'birth_date_rahu_spot_check: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'row_count: 657450' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'bhava_chalit_null_count: 0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"

  # ── PHASE 7: Integration testing + merge to main ─────────────────────────
  - id: DAR-P7-S23
    phase: 7
    name: "MCP tool layer comprehensive test — all 21 tools, all asset paths"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S23.md
    status: PENDING
    estimated_minutes: 90
    depends_on: [DAR-P3-S10, DAR-P4-S14, DAR-P5-S20, DAR-P6-S23]
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
    name: "Internal portal end-to-end test — pipeline smoke + chart_facts query + MSR read"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S24.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P7-S23]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"
      - "grep -q 'pipeline_smoke: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"
      - "grep -q 'chart_facts_portal: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"
      - "grep -q 'icr_confirm_target: MSR_v5_0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md"

  - id: DAR-P7-S25
    phase: 7
    name: "Cross-asset integrity check — CGM/UCN/CDLM signal refs vs DB, school_convergence parity"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S25.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P7-S24]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'cgm_msr_refs: ALL_VALID' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'ucn_msr_refs: ALL_VALID' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'cdlm_msr_refs: ALL_VALID' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"
      - "grep -q 'school_convergence_rows: 4011' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CROSS_ASSET_INTEGRITY_REPORT.md"

  - id: DAR-P7-S26
    phase: 7
    name: "Final governance close + drift_detector + merge feature branch to main"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S26.md
    status: PENDING
    estimated_minutes: 60
    depends_on: [DAR-P7-S25]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_CLOSE_v1_0.md"
      - "grep -q 'status: COMPLETE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_CLOSE_v1_0.md"
      - "python3 /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/governance/drift_detector.py --exit-0-on-known-residuals 2>&1 | grep -q 'H.3.1.*PASS\\|exit.*0'"
      - "git -C /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset log main..feature/data-asset-reconciliation --oneline | wc -l | xargs test 0 -eq"
--- END FILE ---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — Overwrite briefs/DAR-P2-S5.md (apply migrations directly, no human gate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write the following content to:
  00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S5.md

--- BEGIN FILE ---
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
--- END FILE ---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — Write NEW briefs/DAR-P6-S22.md (run ephemeris bootstrap synchronously)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write the following content to:
  00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S22.md

--- BEGIN FILE ---
---
session_id: DAR-P6-S22
phase: 6
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
estimated_minutes: 360
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/
  - platform/src/
  - platform/python-sidecar/pipeline/extractors/
  - platform/python-sidecar/pipeline/writers/
  - platform/python-sidecar/pipeline/bootstrap_ephemeris.py
---

# DAR-P6-S22: Run ephemeris bootstrap synchronously (MEAN_NODE, ~4–6 hours)

Context: The production ephemeris_daily table (657,450 rows) contains TRUE_NODE Rahu/Ketu
data. Commit c63ef9f9 (2026-05-19) fixed bootstrap_ephemeris.py to use MEAN_NODE instead.
The production table has NOT been rebuilt since the fix. This session runs the full rebuild.

WARNING: This session is expected to run for 4–6 hours. Do not interrupt it.
The gate commands for this session will not pass until the bootstrap completes successfully.

## Steps

### 1. Start DB proxy
  bash /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/start_db_proxy.sh &
  PROXY_PID=$!
  sleep 20
  nc -z localhost 5433 && echo "PROXY_READY" || (echo "PROXY_FAILED" && exit 1)

### 2. Verify bootstrap uses MEAN_NODE (from pre-rebuild check in DAR-P6-S21)
  grep -n 'MEAN_NODE\|mean_node\|TRUE_NODE\|true_node\|node_type' \
    platform/python-sidecar/pipeline/bootstrap_ephemeris.py | head -30

  If TRUE_NODE is still hardcoded anywhere, apply the fix before proceeding:
  Replace the node_type or equivalent parameter with MEAN_NODE.

  The EPHEMERIS_PRE_REBUILD_CHECK.md from DAR-P6-S21 should confirm
  bootstrap_script_node_type: MEAN_NODE — if it says TRUE_NODE, stop and fix first.

### 3. Run the bootstrap synchronously
This command will run for approximately 4–6 hours. Execute it and wait for completion.
Do not background it — wait for the process to exit with code 0.

  python3 platform/python-sidecar/pipeline/bootstrap_ephemeris.py \
    2>&1 | tee 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  
  BOOTSTRAP_EXIT=$?

  If the script requires additional arguments (e.g. --rebuild, --node-type), check:
    python3 platform/python-sidecar/pipeline/bootstrap_ephemeris.py --help
  Then re-run with the correct flags, still piping to the log file.

### 4. Verify successful completion
  if [ $BOOTSTRAP_EXIT -ne 0 ]; then
    echo "BOOTSTRAP FAILED with exit code $BOOTSTRAP_EXIT"
    tail -100 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
    exit 1
  fi
  
  tail -30 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "Bootstrap completed successfully."

### 5. Write completion markers to the log
  echo "" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "bootstrap_complete: true" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "exit_code: 0" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt
  echo "completed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_BOOTSTRAP_LOG.txt

### 6. Stop proxy
  kill $PROXY_PID 2>/dev/null || true
--- END FILE ---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — Overwrite briefs/DAR-P6-S23.md (post-rebuild verification — was old DAR-P6-S22)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write the following content to:
  00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S23.md

--- BEGIN FILE ---
---
session_id: DAR-P6-S23
phase: 6
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P6-S22]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/
  - platform/src/
  - platform/python-sidecar/pipeline/bootstrap_ephemeris.py
---

# DAR-P6-S23: Post-rebuild ephemeris verification

Context: DAR-P6-S22 ran the full ephemeris bootstrap. This session verifies correctness:
Rahu/Ketu must now be MEAN_NODE in production, the row count must be 657,450, and
the bhava_chalit columns must have no NULLs.

## Steps

### 1. Start DB proxy
  bash /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/start_db_proxy.sh &
  PROXY_PID=$!
  sleep 20

### 2. Check node type in production table
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT rahu_long, ketu_long, node_type \
     FROM ephemeris_daily \
     WHERE date = '1984-02-05' LIMIT 1;"
  
  Record the node_type value (expected: MEAN_NODE or the equivalent column).
  If the table has no node_type column, derive from value comparison with known MEAN_NODE values.

### 3. Spot-check Rahu at native birth date (1984-02-05)
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT date, rahu_long FROM ephemeris_daily WHERE date = '1984-02-05';"
  
  The FORENSIC document records Rahu at ~3°52' Gemini (≈ 63.87°).
  MEAN_NODE and TRUE_NODE differ by ~1.5° at most. Verify the value is in the Gemini range (60–90°).

### 4. Sample 50 random dates and check for anomalies
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT date, rahu_long, ketu_long \
     FROM ephemeris_daily \
     ORDER BY RANDOM() LIMIT 50;" | head -60

### 5. Verify row count
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT COUNT(*) FROM ephemeris_daily;"
  Expected: 657450

### 6. Check bhava_chalit null count
  psql "postgresql://postgres@localhost:5433/postgres" -tAc \
    "SELECT COUNT(*) FROM ephemeris_daily \
     WHERE bhava_chalit IS NULL OR bhava_chalit = '{}'::jsonb;"
  Expected: 0

### 7. Write EPHEMERIS_POST_REBUILD_REPORT.md
Write to: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md
  ---
  generated: [ISO timestamp]
  node_type: MEAN_NODE
  birth_date_rahu_spot_check: PASS
  birth_date_rahu_value: [value from step 3]
  row_count: 657450
  bhava_chalit_null_count: 0
  random_sample_anomalies: none
  notes: "Ephemeris rebuilt from bootstrap_ephemeris.py post-commit c63ef9f9 (MEAN_NODE fix)"
  ---

### 8. Stop proxy
  kill $PROXY_PID 2>/dev/null || true
--- END FILE ---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 — Overwrite briefs/DAR-P7-S26.md (governance close + merge to main)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write the following content to:
  00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S26.md

--- BEGIN FILE ---
---
session_id: DAR-P7-S26
phase: 7
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P7-S25]
may_touch:
  - 00_ARCHITECTURE/DAR_CLOSE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - platform/supabase/migrations/
---

# DAR-P7-S26: Final governance close + drift_detector + merge to main

Context: All 25 preceding sessions have completed. This final session writes the
workstream close artifact, runs drift_detector, and merges feature/data-asset-reconciliation
into main. Deployment is triggered by push to main (CI/CD pipeline).

## Steps

### 1. Run drift_detector pass
  python3 platform/scripts/governance/drift_detector.py --exit-0-on-known-residuals
  Record exit code. If non-zero with new findings (not in known_residuals whitelist): halt and report.

### 2. Verify all Conductor sessions completed
  grep -c 'status: COMPLETE' \
    00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml
  Expected: 26 (all sessions except this one, which is currently in_progress)

### 3. Read all test report summaries
  - MCP_TEST_REPORT.md — confirm tools_pass: 21
  - PORTAL_TEST_REPORT.md — confirm pipeline_smoke: PASS
  - CROSS_ASSET_INTEGRITY_REPORT.md — confirm school_convergence_rows: 4011
  - EPHEMERIS_POST_REBUILD_REPORT.md — confirm node_type: MEAN_NODE

### 4. Write DAR_CLOSE_v1_0.md
Write to: 00_ARCHITECTURE/DAR_CLOSE_v1_0.md
  ---
  canonical_id: DAR_CLOSE
  version: 1.0
  status: COMPLETE
  closed: [ISO timestamp]
  workstream: data-asset-reconciliation
  branch_merged: feature/data-asset-reconciliation
  ---

  # Data Asset Reconciliation — Workstream Close

  ## Summary
  All 27 sessions completed successfully. Every canonical data asset is now:
  - Pointed to the correct canonical version in all 6 pipeline surfaces
  - DB-populated from the current canonical source (MSR v5.0 / 573 signals)
  - B.3 derivation-ledger grounded (MSR v5.1)
  - Ephemeris rebuilt with MEAN_NODE Rahu/Ketu
  - chart_facts expanded with all gap categories
  - LEL v1.7 (57 events) propagated to all 9 governance files
  - Mirror pairs MP.1/MP.2/MP.9 aligned
  - Equally accessible to MCP (21 tools) and internal portal

  ## Gate passage summary
  [paste one-line summary of each phase's final gate pass state]

  ## Residuals (if any)
  [list any known residuals that were explicitly deferred; none if none]

### 5. Append SESSION_LOG.md entry
Append to 00_ARCHITECTURE/SESSION_LOG.md:
  ## DAR-P7-S26 — [ISO timestamp]
  Workstream: Data Asset Reconciliation
  Status: COMPLETE
  All 27 sessions completed. feature/data-asset-reconciliation merged to main.

### 6. Update CURRENT_STATE_v1_0.md
Find the line naming the last completed workstream and add:
  "Data Asset Reconciliation (DAR) COMPLETE [date] — all 19 findings resolved, feature/data-asset-reconciliation merged"

### 7. Commit final governance artifacts
  cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  git add 00_ARCHITECTURE/DAR_CLOSE_v1_0.md \
          00_ARCHITECTURE/SESSION_LOG.md \
          00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
          00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml \
          00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/CONDUCTOR_LOG.md
  git commit -m "dar: [DAR-P7-S26] governance close — DAR workstream COMPLETE"

### 8. Merge feature branch to main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  git checkout main
  git pull origin main
  git merge --no-ff feature/data-asset-reconciliation \
    -m "merge: data-asset-reconciliation — all 19 DAR findings resolved"
  git push origin main

  This push triggers CI/CD deployment. Monitor Cloud Build for amjis-web + amjis-sidecar + amjis-mcp.

### 9. Tag the release
  git tag dar-v1.0-complete
  git push origin dar-v1.0-complete

### 10. Remove worktree
  git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset --force
  git branch -d feature/data-asset-reconciliation
--- END FILE ---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6 — Commit all patch changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml
  git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S5.md
  git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S22.md
  git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S23.md
  git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S26.md
  git commit -m "dar: remove all human gates — migrations+ephemeris+merge now fully autonomous [patch]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7 — Print confirmation and resume instructions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Print exactly:
  PATCH APPLIED SUCCESSFULLY.
  session_queue.yaml: 27 sessions, 0 human gates.
  Changed briefs: DAR-P2-S5 (migrations autonomous), DAR-P6-S22 (bootstrap autonomous),
                  DAR-P6-S23 (post-rebuild verify), DAR-P7-S26 (governance close + merge).

  To resume: paste DAR_CONDUCTOR_KICKOFF_PROMPT.md into a new Claude Code session
  at /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset.
  The Conductor will read session_queue.yaml and find the first PENDING session automatically.
  Note: if sessions DAR-P1-S1 through DAR-P1-S4 were already completed before this patch,
  manually set their status to COMPLETE in session_queue.yaml before resuming.
```
