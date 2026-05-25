---
session_id: DAR-P7-S24
phase: 7
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
depends_on: [DAR-P7-S23]
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md  # create
must_not_touch:
  - platform/migrations/
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
---

# DAR-P7-S24: Internal portal end-to-end smoke test

## Context

MCP tool layer passed (S23). This session verifies the internal web portal (ConsumeChat)
correctly uses the reconciled data: the pipeline re-run produces correct output,
the ICR confirm endpoint targets MSR_v5_0, and chart_facts queries work from the portal
API surface.

## Steps

1. Pipeline smoke — trigger a representative pipeline run and verify it uses MSR v5.0:
   ```bash
   # If there's a test endpoint or CLI trigger:
   curl -X POST "$APP_URL/api/pipeline/run" \
     -H "Authorization: Bearer $TEST_API_KEY" \
     -d '{"query": "What is my Lagna?", "chart_id": "test"}' 2>&1 | head -50
   ```
   Or run the pipeline unit tests:
   ```bash
   cd platform && npx vitest run src/app/api/ 2>&1 | tail -20
   ```

2. ICR confirm target check — verify the ICR confirm endpoint references MSR_v5_0:
   ```bash
   grep 'MSR_PATH\|MSR_v5_0' platform/src/app/api/icr/confirm/route.ts
   ```
   Expected: `MSR_v5_0.md` in the path.

3. chart_facts portal check — verify the chart_facts API route returns new categories:
   ```bash
   psql "$DATABASE_URL" -c "SELECT DISTINCT category FROM chart_facts WHERE category='ashtakavarga';"
   ```
   Expected: 1 row.

4. MSR read via portal route:
   ```bash
   curl "$APP_URL/api/mcp/asset?asset=MSR" \
     -H "Authorization: Bearer $MCP_API_KEY" 2>&1 | python3 -c "
   import sys, json
   d = json.load(sys.stdin)
   print('version:', d.get('version', 'NOT_FOUND'))"
   ```
   Expected: version 5.1 or content confirms 573 signals.

5. Create `00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md`:
   ```yaml
   # Portal End-to-End Test Report — Phase 7 S24
   # Generated: [timestamp]

   pipeline_smoke: PASS
   chart_facts_portal: PASS
   icr_confirm_target: MSR_v5_0
   msr_read_portal: PASS
   notes: [any observations]
   ```

6. Commit:
   ```
   dar: P7-S24 portal E2E smoke PASS — pipeline + chart_facts + ICR target MSR_v5_0 confirmed
   ```

## Acceptance criteria

- `test -f 00_ARCHITECTURE/CONDUCTOR/data_asset_reconciliation/PORTAL_TEST_REPORT.md` → TRUE
- `grep 'pipeline_smoke: PASS' PORTAL_TEST_REPORT.md` → match
- `grep 'icr_confirm_target: MSR_v5_0' PORTAL_TEST_REPORT.md` → match
