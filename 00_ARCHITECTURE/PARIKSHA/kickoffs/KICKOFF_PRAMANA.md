# Kickoff prompt — PRAMANA-DRASHTA (standalone)

Use this only if you want to run Pramana directly without a full Drashta
walk (e.g., after a manual build trigger, or to re-run the battery after
a Vaidya fix). Otherwise paste KICKOFF_PARIKSHA_ORCHESTRATOR.md.

---

```
You are Claude Code running in Google Antigravity IDE.

ROLE: Pramana-Drashta (proof witness) for chart_id $CHART_ID, build_id $BUILD_ID
PROJECT: MARSYS-JIS (/Users/Dev/Vibe-Coding/Apps/Madhav)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

OPERATOR INPUTS:
  CHART_ID:   <fill>
  BUILD_ID:   <fill — the completed build whose chart_facts to audit>

REQUIRED READS at session open (full files):
  1. 00_ARCHITECTURE/PARIKSHA/PARIKSHA_MASTER_PLAN_v1_0.md
  2. 00_ARCHITECTURE/PARIKSHA/briefs/PRAMANA_DRASHTA_v1_0.md
  3. 00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml
  4. 00_ARCHITECTURE/PARIKSHA/ASSET_REGISTRY.md
  5. 00_ARCHITECTURE/PARIKSHA/ISSUE_LEDGER_SCHEMA.md
  6. 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/manifest.yaml
  7. 00_ARCHITECTURE/PARIKSHA/builds/$CHART_ID/issues.yaml
  8. Optional: 00_ARCHITECTURE/PARIKSHA/native_oracles/$CHART_ID.yaml (if exists)

GOAL:
  Run the 7-category internal-consistency battery on the completed build's
  chart_facts. Emit data_integrity issues for failures. Write the pramana{}
  summary block to resume_state.yaml.

EXECUTION SEQUENCE:

§1 Confirm STOP file absent.

§2 Start Cloud SQL proxy:
   bash platform/scripts/start_db_proxy.sh &
   sleep 5

§3 Verify build is complete:
   psql "$DATABASE_URL" -c "SELECT status FROM builds WHERE build_id='$BUILD_ID';"
   Must return 'complete'. If 'running' or 'failed', halt with note.

§4 Category 1 — Row-count checks (per asset × ayanamsha)
   For each asset in EXPECTED_ROW_COUNTS.yaml × each ayanamsha:
     - Skip if expected_rows starts with "tbd:"
     - Run row-count SQL against target_tables
     - Emit data_integrity issue if outside tolerance

§5 Category 2 — Schema-compliance checks (NOT NULL, FK)

§6 Category 3 — Structural invariants per asset (per ASSET_REGISTRY.md)

§7 Category 4 — Cross-asset structural integrity

§8 Category 5 — Layer-completion gate verification

§9 Category 7 — Operator oracle (if native_oracles file exists)
   Otherwise skip — Pramana works without it.

§10 Write summary block to resume_state.yaml:
    pramana:
      ran_at: <ISO>
      pass: <bool>
      checks_run: <count>
      issues_emitted: <count>
      by_category: {row_count, schema, structural, cross_asset, layer_gate, oracle}

§11 Print summary to console:
    PRAMANA COMPLETE for build $BUILD_ID
    Verdict:        {PASS|FAIL}
    Checks run:     {count}
    Issues emitted: {count} (by severity)
    Next: orchestrator writes final REPORT.md

HARD GATES (PRAMANA_DRASHTA_v1_0.md §"Hard gates"):
  - NO writes to any application table; DB access is read-only
  - NO Anthropic models
  - NO requiring a per-chart oracle; battery must pass on its own
  - NO spawning Vaidya from inside Pramana (Pratisamhita handles triage)
  - Do NOT skip checks because they're inconvenient

WHEN DONE:
  Print §11 summary. Exit.
```
