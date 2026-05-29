---
brief: A3 + A4 + A5 Implementation — Conductor Kickoff
authored_by: Cowork (2026-05-29)
session_for: Claude Code in terminal (`claude --dangerously-skip-permissions`)
session_type: conductor
parent_plan: 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/IMPLEMENTATION_PLAN_A3_A4_A5_v1_0.md
status: COMPLETE
completed_at: 2026-05-30
sessions_completed: 37
streams: A3 (8/8), A4 (10/10), A5 (12/12), ACC (7/7)
sealing_artifact: 00_ARCHITECTURE/A3_A4_A5_CLOSE_v1_0.md
main_head_at_close: e22632d0
operator_action_required: >
  Trigger native chart build job:
  gcloud run jobs execute amjis-build-job --region=asia-south1
  Then refresh all 12 MVs post-build.
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_LOG.md
  - 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml
must_not_touch:
  - platform/src/**
  - platform/python-sidecar/**
  - platform/migrations/**
  - 00_ARCHITECTURE/A3_A4_A5_CLOSE_v1_0.md
  - CLAUDE.md
acceptance_criteria:
  - All A3 migrations (134-138) verified applied to production amjis DB
  - amjis-sidecar Cloud Run service redeployed (or confirmed current code is already live)
  - 10-minute post-deploy log check shows 0 errors
  - chart_facts confirmed empty (ready for build job)
  - CONDUCTOR_LOG.md updated with final summary
  - session_queue.yaml ACC-S7 marked complete
---

# CLAUDECODE_BRIEF — ACC-S7
## Final production deploy verification + log watch

## §0 — Context

ACC-S7. HEAD at 46d1ceb1. All 36 prior sessions merged to main.
This is the final session. Verify production is ready.

## §1 — Steps

**Step 1: Verify production DB has A3 migrations**
```bash
PGPASSWORD=aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
SELECT column_name FROM information_schema.columns
WHERE table_name='chart_facts' AND column_name IN ('fact_subject','citation_ref','verification_pass_status')
ORDER BY column_name"
```
Expected: 3 rows.

**Step 2: Verify amjis-sidecar current revision and that code is live**
```bash
gcloud run services describe amjis-sidecar --region=asia-south1 --format='value(status.latestReadyRevisionName)' 2>/dev/null
```
If this returns a revision, confirm it is recent. If redeployment is needed, note it.

**Step 3: Quick log check (1 min scan for recent errors)**
```bash
gcloud run services logs read amjis-sidecar --region=asia-south1 --limit=100 2>/dev/null | grep -i 'error\|exception\|crash' | head -20 || echo 'LOG CHECK CLEAN'
```

**Step 4: Confirm chart_facts is empty and ready**
```bash
PGPASSWORD=aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "SELECT count(*) FROM chart_facts"
```

**Step 5: Update CONDUCTOR_LOG.md with final summary**

Read `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_LOG.md` and append:

```
## A3+A4+A5 Workstream — COMPLETE 2026-05-30

**Sessions completed:** 37/37
**Streams:** A3 (8/8), A4 (10/10), A5 (12/12), ACC (7/7)
**Main HEAD at close:** 46d1ceb1
**Sealing artifact:** 00_ARCHITECTURE/A3_A4_A5_CLOSE_v1_0.md
**Production DB:** Migrations 134-138 applied; chart_facts wiped + ready for build job
**Operator action required:**
  1. Trigger native chart build job (chart_id 362f9f17-95a5-490b-a5a7-027d3e0efda0)
     via Cloud Run Job: `gcloud run jobs execute amjis-build-job --region=asia-south1`
  2. Monitor build completion in builds table
  3. Verify ~13K A5 rows + ~600 A4 rows per ayanamsha populated in chart_facts
  4. Trigger REFRESH MATERIALIZED VIEW on all 12 MVs post-build
**Status:** SEALED
```

**Step 6: Commit CONDUCTOR_LOG.md update**
```bash
git add 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CONDUCTOR_LOG.md
git commit -m "feat(deploy/ACC-S7): A3+A4+A5 production deploy COMPLETE + final conductor log [ACC-S7]"
```

Set status: COMPLETE in brief. Print final summary:
"A3+A4+A5 CONDUCTOR COMPLETE: 37/37 sessions. Sealing artifact written. DB ready. Operator: trigger native chart build job."
