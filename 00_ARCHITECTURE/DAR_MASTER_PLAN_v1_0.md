---
canonical_id: DAR_MASTER_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-25
author: Claude (Cowork session)
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
conductor_queue: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml
purpose: >
  Master implementation plan for the Data Asset Reconciliation (DAR) workstream.
  Covers all 19 findings from DATA_ASSET_AUDIT_AND_RECONCILIATION_v1_0.md v1.1.
  Target state: every canonical data asset fully correct, pipeline-connected,
  DB-populated from current canonical version, tested, and available equally
  to MCP and internal portal.
total_sessions: 26
total_phases: 7
execution_model: Conductor-driven autonomous sub-agents with --dangerously-skip-permissions
human_gates: 4 (DB migrations apply, ephemeris rebuild run, final merge to main, prod deploy)
---

# Data Asset Reconciliation — Master Plan v1.0

## §0 — Execution model

All implementation runs autonomously via the Conductor methodology on branch
`feature/data-asset-reconciliation` in worktree `/Users/Dev/Vibe-Coding/Apps/MadhavDataAsset`.

Sub-agents launched by Conductor use `--dangerously-skip-permissions` so no
session pauses for tool approvals. Context is controlled via the briefing
system (each session gets exactly the scope it needs — no more).

### Human gates (4 total)

| Gate | Triggered after | Required human action |
|---|---|---|
| HG-1 | Phase 2 S5 | Apply migrations 116 + 117 to production DB |
| HG-2 | Phase 2 S6 | Confirm migration application + run DB baseline queries to verify msr_signals source |
| HG-3 | Phase 6 S22 | Run `bootstrap_ephemeris.py` (~4–6 h wall clock) |
| HG-4 | Phase 7 S26 | Review test report → approve merge to main → deploy |

### Conductor rules (inherited from project standard)
- Conductor commits touch ONLY `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/`
- Application + data code changes commit on the feature branch normally
- Each session brief (CLAUDECODE_BRIEF_DAR_*.md) is the complete governing document for that session
- `session_queue.yaml` is the live progress tracker
- Conductor halts on any failing gate_commands; human must resolve before resuming

---

## §1 — Worktree and environment setup (run ONCE on main before switching)

Run the following single prompt in a Claude Code session on `main`:

```
SETUP PROMPT (paste into Claude Code on main branch):
---
You are setting up the environment for the Data Asset Reconciliation (DAR) workstream.
Execute exactly the following steps with no deviations:

1. Create the git worktree:
   git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset feature/data-asset-reconciliation 2>/dev/null || (git checkout -b feature/data-asset-reconciliation && git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset feature/data-asset-reconciliation)

2. Create the Conductor infrastructure directories:
   mkdir -p /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/
   mkdir -p /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/
   mkdir -p /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/99_ARCHIVE/025_HOLISTIC_SYNTHESIS/

3. Copy DAR_MASTER_PLAN_v1_0.md to the worktree:
   cp /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md \
      /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/

4. Create the Conductor session_queue.yaml, CONDUCTOR_LOG.md, and all 26 CLAUDECODE_BRIEF_DAR_*.md files
   as specified in DAR_MASTER_PLAN_v1_0.md §3 (session queue) and §4 (brief templates).
   These files land in: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/

5. Verify setup:
   git -C /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset worktree list
   ls /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/
   echo "SETUP COMPLETE"

6. Commit the infrastructure to the feature branch:
   cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
   git add 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/
   git add 00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md
   git commit -m "dar: conductor infrastructure + session queue for DAR workstream [governance]"
---
```

After this prompt completes, switch to the worktree and run the Conductor kickoff per §2.

---

## §2 — Conductor kickoff prompt (run in worktree after setup)

```
CONDUCTOR KICKOFF (paste into Claude Code from /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset):
---
You are the Conductor for the Data Asset Reconciliation (DAR) workstream.
Working directory: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
Branch: feature/data-asset-reconciliation

Your governing documents:
- 00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md — master plan
- 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/session_queue.yaml — live queue

Execution rules:
1. Read session_queue.yaml at the top of every turn
2. Spawn the next PENDING session as a sub-agent using the corresponding CLAUDECODE_BRIEF_DAR_*.md
3. Sub-agents run with --dangerously-skip-permissions (do not interrupt for tool approvals)
4. After each sub-agent returns, run that session's gate_commands. If all pass: mark COMPLETE,
   advance to next session. If any fail: mark FAILED, halt and report to human.
5. At each HG-* (human gate): halt, print the exact human action required, wait for confirmation
   before resuming.
6. Context budget: 20 sub-agents per Conductor context. If you approach 18 sub-agents, halt
   cleanly, write your position to CONDUCTOR_LOG.md, and instruct the human to re-kick
   in a fresh Conductor context from the saved position.
7. Commit after every session: the session's changes go into a commit titled
   "dar: [session_id] [one-line description]"

Begin by reading session_queue.yaml and spawning DAR-P1-S1.
---
```

---

## §3 — Session queue (session_queue.yaml content)

```yaml
# DAR session_queue.yaml — Data Asset Reconciliation
# Conductor reads this file to determine next action
# Status values: PENDING / IN_PROGRESS / COMPLETE / FAILED / HUMAN_GATE

meta:
  workstream: data-asset-reconciliation
  branch: feature/data-asset-reconciliation
  worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
  master_plan: 00_ARCHITECTURE/DAR_MASTER_PLAN_v1_0.md
  created: 2026-05-25

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

  # ── PHASE 2: DB migrations + baseline verification ───────────────────────
  - id: DAR-P2-S5
    phase: 2
    name: "Migration safety scripts + apply instructions for migrations 116+117"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S5.md
    status: PENDING
    estimated_minutes: 20
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/migrations/116_trace_mcp_tool_column.sql"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/migrations/117_audience_tier_acharya_enum.sql"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md"

  - id: DAR-HG-1
    phase: 2
    name: "HUMAN GATE 1 — Apply migrations 116+117 to production"
    type: human_gate
    status: PENDING
    human_action: |
      psql "$DATABASE_URL" -f platform/migrations/116_trace_mcp_tool_column.sql
      psql "$DATABASE_URL" -f platform/migrations/117_audience_tier_acharya_enum.sql
      Then append confirmed entries to 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
      Signal ready by running: touch 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_COMPLETE

  - id: DAR-P2-S6
    phase: 2
    name: "DB baseline state verification — confirm msr_signals source, row counts, migration status"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P2-S6.md
    status: PENDING
    estimated_minutes: 30
    depends_on: [DAR-HG-1]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'migration_116: CONFIRMED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'migration_117: CONFIRMED' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"
      - "grep -q 'msr_signals_source:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md"

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
    name: "B.3 grounding backfill — Nadi/BNN + Yogini/Tajaka signals (SIG.MSR.515–573, new in v4+v5)"
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
      - "python3 -c \"import re; c=open('/Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/025_HOLISTIC_SYNTHESIS/MSR_v5_0.md').read(); gaps=[l for l in c.split('\\n') if 'derivation_ledger' not in c[max(0,c.find(l)-500):c.find(l)+500] and 'SIG.MSR.' in l]; print(len(gaps))\" | xargs -I{} test {} -lt 10"
      - "grep -q 'total_grounded: 573' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/GROUNDING_PROGRESS.yaml"

  # ── PHASE 6: MEAN_NODE ephemeris rebuild ─────────────────────────────────
  - id: DAR-P6-S21
    phase: 6
    name: "Ephemeris pre-rebuild verification — confirm TRUE_NODE in production, prepare runbook check"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S21.md
    status: PENDING
    estimated_minutes: 30
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "grep -q 'current_node_type:' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "grep -q 'bootstrap_script_node_type: MEAN_NODE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_PRE_REBUILD_CHECK.md"
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md"

  - id: DAR-HG-3
    phase: 6
    name: "HUMAN GATE 3 — Run ephemeris bootstrap (4–6 hours)"
    type: human_gate
    status: PENDING
    depends_on: [DAR-P6-S21]
    human_action: |
      cd /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
      Follow instructions in 00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md
      Estimated time: 4–6 hours
      Signal ready by running: touch 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG3_COMPLETE

  - id: DAR-P6-S22
    phase: 6
    name: "Post-rebuild ephemeris verification — spot-check Rahu at birth date + 50 random dates"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P6-S22.md
    status: PENDING
    estimated_minutes: 45
    depends_on: [DAR-HG-3]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'node_type: MEAN_NODE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'birth_date_rahu_spot_check: PASS' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'row_count: 657450' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"
      - "grep -q 'bhava_chalit_null_count: 0' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/EPHEMERIS_POST_REBUILD_REPORT.md"

  # ── PHASE 7: Integration testing + sign-off ───────────────────────────────
  - id: DAR-P7-S23
    phase: 7
    name: "MCP tool layer comprehensive test — all 21 tools, all asset paths"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S23.md
    status: PENDING
    estimated_minutes: 90
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
    name: "Internal portal end-to-end test — pipeline re-run smoke + chart_facts query + MSR read"
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
    name: "Final governance close — DAR_CLOSE artifact + drift_detector pass + SESSION_LOG entry"
    brief: 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/briefs/DAR-P7-S26.md
    status: PENDING
    estimated_minutes: 45
    depends_on: [DAR-P7-S25]
    gate_commands:
      - "test -f /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_CLOSE_v1_0.md"
      - "grep -q 'status: COMPLETE' /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/00_ARCHITECTURE/DAR_CLOSE_v1_0.md"
      - "python3 /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset/platform/scripts/governance/drift_detector.py --exit-0-on-known-residuals 2>&1 | grep -q 'H.3.1.*PASS\\|exit.*0'"

  - id: DAR-HG-4
    phase: 7
    name: "HUMAN GATE 4 — Review test reports, approve merge to main, deploy"
    type: human_gate
    status: PENDING
    depends_on: [DAR-P7-S26]
    human_action: |
      Review all test reports in 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/
      If satisfied: git merge feature/data-asset-reconciliation into main
      Deploy: standard gcloud run deploy for amjis-web + amjis-sidecar + amjis-mcp
      Signal complete: git tag dar-v1.0-complete
```

---

## §4 — Session brief templates

Each brief below is a complete governing document for its session. The Conductor reads and passes the full brief to the sub-agent.

---

### DAR-P1-S1: Blocking code fixes

```markdown
---
session_id: DAR-P1-S1
phase: 1
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - platform/src/app/api/mcp/asset/route.ts
  - platform/src/app/api/icr/confirm/route.ts
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - platform/src/scripts/etl/__tests__/msr_parser.test.ts
  - 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/python-sidecar/
  - platform/supabase/migrations/
  - .geminirules
---

# DAR-P1-S1: Blocking code fixes

Context: This is the Data Asset Reconciliation workstream. MSR has been upgraded to v5.0
(573 signals) but five pipeline surfaces still reference MSR_v3_0.md. This session fixes
the two blocking surfaces and two governance files.

## Steps

1. Read platform/src/app/api/mcp/asset/route.ts
   Find the SAFE_ASSET_MAP constant. Change the MSR entry:
   From: any reference to 'MSR_v3_0.md'
   To:   'MSR_v5_0.md' (or whatever key-value structure holds it)
   Verify: grep -n MSR route.ts — no v3 or v4 references remain

2. Read platform/src/app/api/icr/confirm/route.ts
   Find MSR_PATH constant (line ~24). Change:
   From: '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'
   To:   '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md'

3. Read 00_ARCHITECTURE/manifest_overrides.yaml
   Find MP.5 enforcement_rule and path_pattern. Change:
   From: anything referencing 'MSR_v3_0'
   To:   'MSR_v5_0'

4. Read platform/src/scripts/etl/__tests__/msr_parser.test.ts
   Find the fixture file path (line ~5). Change:
   From: absolute path ending in MSR_v3_0.md
   To:   absolute path ending in MSR_v5_0.md
   Verify: the assertion on line ~45 (expects source_file = 'MSR_v5_0.md') is now consistent

5. Delete the stale PROPOSED patch:
   git rm 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml
   The RESOLVED copy at CONFLICT_PATCHES/RESOLVED/ is the canonical record.

6. Run vitest for the affected test file to confirm it passes.

7. Commit: "dar: P1-S1 fix read_asset + ICR + manifest_overrides + test fixture; rm stale PROPOSED patch"

## Acceptance criteria
- grep 'MSR_v3_0' platform/src/app/api/mcp/asset/route.ts → 0 results
- grep 'MSR_v3_0' platform/src/app/api/icr/confirm/route.ts → 0 results
- grep 'MSR_v3_0' 00_ARCHITECTURE/manifest_overrides.yaml → 0 results
- grep 'MSR_v3_0' platform/src/scripts/etl/__tests__/msr_parser.test.ts → 0 results
- test -f 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml → FALSE (deleted)
- vitest msr_parser.test → PASS
```

---

### DAR-P1-S2: Python pipeline MSR updates

```markdown
---
session_id: DAR-P1-S2
phase: 1
status: PENDING
may_touch:
  - platform/python-sidecar/pipeline/main.py
  - platform/python-sidecar/pipeline/extractors/msr_extractor.py
  - platform/python-sidecar/pipeline/writers/msr_signals_writer.py
  - platform/python-sidecar/rag/chunkers/msr_signal.py
  - platform/python-sidecar/pipeline/ingest_msr.py
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/src/
  - platform/supabase/migrations/
---

# DAR-P1-S2: Python pipeline MSR source + count updates

Context: The Python build pipeline hardcodes MSR_v3_0.md as source and EXPECTED_COUNT=514.
MSR v5.0 has 573 signals. This session updates all 7 hardcoded locations.

## Steps (read each file before editing)

1. platform/python-sidecar/pipeline/main.py — change the MSR source path constant
2. platform/python-sidecar/pipeline/extractors/msr_extractor.py:
   - SOURCE_FILE: MSR_v3_0.md → MSR_v5_0.md
   - EXPECTED_COUNT: 514 → 573
3. platform/python-sidecar/pipeline/writers/msr_signals_writer.py:
   - SOURCE_FILE: MSR_v3_0.md → MSR_v5_0.md
   - EXPECTED_COUNT: 514 → 573
4. platform/python-sidecar/rag/chunkers/msr_signal.py:
   - SOURCE_FILE: MSR_v3_0.md → MSR_v5_0.md
   - SOURCE_VERSION: "3.1" → "5.0"
5. platform/python-sidecar/pipeline/ingest_msr.py (docstring): update reference

6. Run: python3 -c "from pipeline.extractors.msr_extractor import MSRExtractor; e = MSRExtractor(); print(e.SOURCE_FILE, e.EXPECTED_COUNT)" — verify 573 prints

7. Commit: "dar: P1-S2 update Python pipeline MSR source + EXPECTED_COUNT to v5.0/573"

## Acceptance criteria
- grep -rn 'MSR_v3_0' platform/python-sidecar/pipeline/ → 0 results
- grep 'EXPECTED_COUNT = 573' msr_extractor.py → matches
- grep 'EXPECTED_COUNT = 573' msr_signals_writer.py → matches
- grep 'SOURCE_VERSION.*5.0' msr_signal.py → matches
```

---

### DAR-P1-S3: Archive MSR + GCS_LAYOUT + LEL references

```markdown
---
session_id: DAR-P1-S3
phase: 1
status: PENDING
may_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md (git mv only — move to 99_ARCHIVE)
  - 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md (git mv only — move to 99_ARCHIVE)
  - 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/ (create + receive MSR v3/v4)
  - 00_ARCHITECTURE/GCS_LAYOUT_v1_0.md
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  - CLAUDE.md (§D + §E LEL entries only)
  - 00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md
  - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
  - 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md (backfill 072–082)
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/
---

# DAR-P1-S3: Archive MSR v3+v4 + GCS_LAYOUT v1.1 + LEL count corrections

## Steps

1. Create archive directory and move superseded MSR files:
   mkdir -p 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/
   git mv 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
   git mv 025_HOLISTIC_SYNTHESIS/MSR_v4_0.md 99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v4_0.md

2. Update GCS_LAYOUT_v1_0.md:
   - Bump version frontmatter: 1.0 → 1.1, add changelog entry
   - In the L2_5/ section: mark MSR_v3_0.md as SUPERSEDED, set MSR_v5_0.md as PRIMARY
   - Update ephemeris note from "coverage gap not yet generated" to document actual state
   - Remove the trailing annotation (incorporate into the main table)

3. Update LEL count in ALL NINE stale files:
   For each file: find "36 events + 5 period summaries + 6 chronic patterns" (or variant)
   Replace with: "57 events + 5 period summaries + 8 chronic patterns (v1.7)"
   Also update version references from "1.6" to "1.7" where present.
   Files: CAPABILITY_MANIFEST.json, CANONICAL_ARTIFACTS_v1_0.md, CLAUDE.md (×2),
   GOVERNANCE_STACK_v1_0.md, MACRO_PLAN_v2_0.md

4. Backfill MIGRATIONS_APPLIED_LOG.md for migrations 072–082 (MCP Transformation batch):
   Add one row per migration with confirmed_method: inferred_from_workstream_close and
   description sourced from the migration file headers.

5. Move RED_TEAM_L2_5_v1_0.md from 025_HOLISTIC_SYNTHESIS/ to 00_ARCHITECTURE/:
   git mv 025_HOLISTIC_SYNTHESIS/RED_TEAM_L2_5_v1_0.md 00_ARCHITECTURE/RED_TEAM_L2_5_v1_0.md

6. Commit: "dar: P1-S3 archive MSR v3+v4; GCS_LAYOUT v1.1; LEL v1.7 count corrections across 9 files"
```

---

### DAR-P1-S4: Mirror pair sync

```markdown
---
session_id: DAR-P1-S4
phase: 1
status: PENDING
may_touch:
  - .geminirules
  - .gemini/project_state.md
must_not_touch:
  - platform/
  - 025_HOLISTIC_SYNTHESIS/
---

# DAR-P1-S4: Mirror pair sync — MP.1 + MP.2 + MP.9

Context: .geminirules has M9 as active phase (should be M5); lists 7 workstreams (should be 15).
.gemini/project_state.md has multi-era misalignment.

## Steps

1. Read CLAUDE.md §C, §D, §E fully to understand current state
2. Read .geminirules fully — understand its structure
3. Update .geminirules:
   - §C item #5: phase pointer → PHASE_M5_PLAN_v1_0.md (M5 active)
   - §D: LEL version → 1.7
   - §E: Add all 8 missing workstreams with COMPLETE status:
     R11.F, R11.G, MCP Transformation, Chat V2 R10, R11v2, Phase 4C, M5 Coverage Campaign, MCP sidecar
   - Update workstream count header
4. Update .gemini/project_state.md §F:
   - macro-phase: M5 ACTIVE
   - last_session: M4-D-S1 (per CURRENT_STATE)
   - Add close records for 8 missing workstreams
5. Commit: "dar: P1-S4 sync .geminirules + .gemini/project_state.md — MP.1/MP.2/MP.9 (mirror pairs)"
   Note: mirror pair sync counts as a CLAUDE.md §K mirror update; record in commit message.
```

---

### DAR-P2-S5: Migration safety + apply instructions

```markdown
---
session_id: DAR-P2-S5
phase: 2
status: PENDING
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/HG1_APPLY_MIGRATIONS.md (create)
must_not_touch:
  - platform/migrations/116_trace_mcp_tool_column.sql
  - platform/migrations/117_audience_tier_acharya_enum.sql
---

# DAR-P2-S5: Migration apply instructions document

Read both migration files completely. Verify their idempotency and safety.
Create HG1_APPLY_MIGRATIONS.md with:
- Exact psql commands to apply each
- What to verify after each (SELECT COUNT, DESCRIBE)
- Rollback commands if needed
- What to append to MIGRATIONS_APPLIED_LOG.md

Commit: "dar: P2-S5 create HG1 apply instructions for migrations 116+117"
```

---

### DAR-P2-S6: DB baseline verification

```markdown
---
session_id: DAR-P2-S6
phase: 2
depends_on: HG-1 complete
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/DB_BASELINE_REPORT.md (create)
  - 00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
---

# DAR-P2-S6: Post-migration DB baseline state report

Run the following queries and record results in DB_BASELINE_REPORT.md:
1. SELECT source_file, COUNT(*) FROM msr_signals GROUP BY source_file; → records msr_signals source
2. SELECT source_file, COUNT(*) FROM l25_msr_signals GROUP BY source_file; → l25_msr_signals source
3. SELECT COUNT(*) FROM rag_chunks WHERE canonical_id = 'MSR'; → MSR rag_chunks count
4. Verify migration_116 applied: SELECT column_name FROM information_schema.columns WHERE table_name='query_trace_steps' AND column_name='mcp_tool';
5. Verify migration_117 applied: SELECT consrc FROM pg_constraint WHERE conname='mcp_api_keys_audience_tier_check';
6. SELECT COUNT(*) FROM chart_facts; → chart_facts row count
7. SELECT COUNT(*) FROM school_signal_coverage; → school coverage rows
8. SELECT COUNT(*) FROM ephemeris_daily; → ephemeris rows

Format the report as:
  migration_116: CONFIRMED / NOT_APPLIED
  migration_117: CONFIRMED / NOT_APPLIED
  msr_signals_source: MSR_v3_0.md / MSR_v5_0.md
  msr_signals_count: <N>
  l25_msr_signals_count: <N>
  msr_rag_chunks_count: <N>
  chart_facts_count: <N>
  school_signal_coverage_count: <N>
  ephemeris_daily_count: <N>

Commit: "dar: P2-S6 DB baseline state report"
```

---

*(Sessions DAR-P3-S7 through DAR-P7-S26 follow the same brief template structure — each has a focused scope, explicit steps, exact gate conditions, and a single commit. Full briefs are generated by the setup prompt in §1.)*

---

## §5 — Phase summary

| Phase | Sessions | Focus | Human gates | Est. wall time |
|---|---|---|---|---|
| 1 | S1–S4 | Code fixes, archive, LEL corrections, mirror sync | None | 3–4 hours |
| 2 | S5–S6 + HG-1/HG-2 | DB migrations + baseline | HG-1, HG-2 | 1 hour code + operator time |
| 3 | S7–S10 | MSR v5.0 pipeline cascade (both tables, rag_chunks, registers, school_convergence) | None | 4–5 hours |
| 4 | S11–S14 | chart_facts enhancement (15 missing FORENSIC sections) | None | 6–7 hours |
| 5 | S15–S20 | MSR v5.0 B.3 Derivation-Ledger grounding (formal derivation_ledger blocks) | None | 9–10 hours |
| 6 | S21–S22 + HG-3 | MEAN_NODE ephemeris rebuild (4–6h rebuild) | HG-3 | 0.5h code + 4–6h operator |
| 7 | S23–S26 + HG-4 | End-to-end testing, cross-asset integrity, governance close | HG-4 | 4–5 hours |

**Total autonomous session time:** ~27–31 hours of Claude Code execution (non-blocking, runs in series)
**Total human gate time:** Migrations apply (~15 min) + DB queries (~15 min) + ephemeris rebuild (~5h) + final review (~30 min)

---

## §6 — Target state (what "done" looks like)

At DAR workstream close, every canonical data asset satisfies ALL of the following:

### MSR
- Single canonical version on disk: `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` (573 signals)
- Superseded versions: `99_ARCHIVE/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` + `_v4_0.md`
- DB `msr_signals` (migration 009): 573 rows, source_file = MSR_v5_0.md
- DB `l25_msr_signals` (migration 018): 573 rows, source_file = MSR_v5_0.md
- DB `rag_chunks` (canonical_id=MSR): 573 chunks, source_version = 5.0, re-embedded
- DB `school_signal_coverage`: 4,011 rows (573 × 7)
- DB `school_convergence_index`: MATERIALIZED VIEW refreshed at 4,011 base rows
- Four registers (contradiction, cluster, pattern, resonance): rebuilt against 573 signals
- `read_asset(MSR)` via MCP: returns 573-signal v5.0 file
- ICR confirm endpoint: patches v5.0 file
- All pipeline code: zero references to MSR_v3_0.md
- B.3 Derivation-Ledger: every signal has `derivation_ledger.l1_sources` entries
- GCS: `L2_5/MSR_v5_0.md` confirmed as primary; v3 + v4 marked superseded in GCS_LAYOUT

### LEL
- Declared version: 1.7, 57 events, 5 summaries, 8 patterns — consistent across ALL 9 files
- `CAPABILITY_MANIFEST.json`, `CANONICAL_ARTIFACTS_v1_0.md`, `CLAUDE.md`, `GOVERNANCE_STACK`, `MACRO_PLAN`, `.geminirules`, `.gemini/project_state.md` all updated

### chart_facts
- YAML v1.2 (enhanced): all 15 previously missing FORENSIC sections now have categories
- DB `chart_facts`: row count > 2,717 (enhanced)
- MCP `query_chart_facts`: accessible for all new categories
- Internal portal pipeline: loads from updated YAML

### Ephemeris
- `ephemeris_daily`: 657,450 rows, all Rahu/Ketu computed with MEAN_NODE
- `bhava_chalit_house` column: populated (not null) for all rows
- Spot-check at FORENSIC birth date (1984-02-05): Rahu nakshatra matches FORENSIC declaration
- `build_manifests`: Phase 4B entry present with correct row count and timestamp
- GCS_LAYOUT: ephemeris section updated

### Migrations
- 116: `query_trace_steps.mcp_tool` column confirmed present
- 117: `mcp_api_keys.audience_tier` CHECK constraint includes 'acharya'
- MIGRATIONS_APPLIED_LOG.md: complete entries for 072–082 and 116–117

### Governance
- `drift_detector.py` H.3.1: PASS (no canonical path disagreement)
- Mirror pairs MP.1/MP.2/MP.9: synced
- `manifest_overrides.yaml`: MSR_v5_0 reference
- `GCS_LAYOUT_v1_0.md`: v1.1 with correct MSR + ephemeris entries

---

## §7 — Risks and mitigations

| Risk | Mitigation |
|---|---|
| EXPECTED_COUNT gate in msr_signals_writer rejects load | Fixed in P1-S2; dry-run gate in P3-S7 confirms before live load |
| Ephemeris bootstrap fails mid-run (power/network) | Runbook has resume instructions; staging table protects production until atomic swap |
| B.3 grounding adds incorrect FORENSIC citations | Each grounding session validates `v6_ids_consumed` against actual FORENSIC content; FORENSIC is read-only ground truth |
| chart_facts extractor produces wrong values | Every extractor validated against FORENSIC v8.0 before YAML write; P4-S14 runs MCP query_chart_facts spot-check |
| school_convergence_index out of sync after MSR rebuild | P3-S10 gate explicitly checks `REFRESH MATERIALIZED VIEW school_convergence_index` completed and row count = 4,011 |
| Sub-agent context overflow on heavy sessions | Each brief is scoped to < 5 files; heavy data-load sessions (P3-S8, P3-S9) call shell scripts rather than reading large files into context |

---

*DAR_MASTER_PLAN_v1_0.md — authored 2026-05-25. This document is the single source of truth for the DAR workstream. Update session statuses in session_queue.yaml, not here. Issue DAR_CLOSE_v1_0.md at Phase 7 completion.*
