---
artifact: CLAUDECODE_BRIEF_MCPT_V32_PROD_APPROVAL.md
session: MCPT-V32-PROD-APPROVAL
workstream: MCPT v3.2 Quality Tightening
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32
branch: feature/mcpt-v32-quality-tightening
plan: Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md
---

# Claude Code Brief — MCPT v3.2 Prod Approval

## Context

All 10 phases of MCPT v3.2 Quality Tightening landed cleanly on `feature/mcpt-v32-quality-tightening` (commits `4756f5db` → `62dd660c`). Verified state:

- **Tests:** 257/257 pass (19 files, 416 ms)
- **Bench diff:** `canonical_d9_workflow` −60% round-trips, −71% bytes; no regressions
- **Accuracy diff:** 2,717 chart_facts rows, 27 categories, 100% cross-scenario agreement
- **CI:** `.github/workflows/mcp-bench.yml` green
- **Harness:** `bench/`, `accuracy/`, `evals/mcp-routing/` all populated

The conductor is currently paused, waiting for the `.conductor-approve-prod` tripwire file.

## Decisions made by the native (human)

1. **Single approval:** no manual pause between staging and prod. Conductor sweeps from R3 → R5 in one go.
2. **R3 routing eval runs live:** `ANTHROPIC_API_KEY` will be made available so the eval produces a real ≥15pp routing-accuracy number rather than skipping.

## Your task

Execute the prod-approval sequence in two steps, in order:

### Step 1 — Make the API key available to the conductor

The conductor is currently running in a Claude Code session that does not have `ANTHROPIC_API_KEY` in its env. The accuracy sub-agent for R3 needs it. Process:

1. Ask the user for their `ANTHROPIC_API_KEY` (don't echo it back).
2. Stop the currently-running conductor cleanly (Ctrl-C or `/exit`).
3. In the same shell, export the key: `export ANTHROPIC_API_KEY='<key>'`
4. Restart with: `claude --dangerously-skip-permissions`
5. Re-paste the conductor pickup prompt from `Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md` Part E.2. The conductor reads `.conductor-state.json` and resumes from where it left off (current_phase, completed sub-agents). No prior work is redone.

### Step 2 — Drop the prod-approval tripwire with single-approval override

From any shell on the native's machine:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32

cat > .conductor-instructions.md <<'EOF'
# Prod Gate Override — 2026-05-23

Human approved single-step staging → prod (no intermediate pause).

On detecting .conductor-approve-prod, execute in order:
1. R3: run routing eval LIVE (ANTHROPIC_API_KEY is in env). Capture
   ≥15pp improvement metric vs Phase 0 baseline. Output:
   evals/mcp-routing/results_live.json + PR comment row.
2. R1: apply data_source_expected_seed.sql to prod DB via Cloud SQL Proxy
   (127.0.0.1:5433, amjis_app user). Verify SELECT COUNT(*) >= 23.
   Append entry to MIGRATIONS_APPLIED_LOG.md.
3. R2: create Cloud Run job amjis-mcp-audit and Cloud Scheduler entry
   nightly-mcp-audit (0 3 * * *). Verify gcloud scheduler jobs describe
   returns ENABLED.
4. R5 staging: gcloud builds submit --substitutions=_TAG=mcpt-v32-staging.
   Wait for revision to be ready.
5. Re-run harnesses against staging URL (env-overridden):
   MCP_BASE_URL=<staging-url> npm run bench:capture
   MCP_BASE_URL=<staging-url> npm run accuracy:capture
   MCP_BASE_URL=<staging-url> npm run accuracy:cross-scenario
   Routing eval already captured in step 1.
6. Post summary comment to the PR via:
   gh pr comment <pr-number> --body-file STAGING_SUMMARY.md
   Body must include: staging URL, all four diff tables (bench, accuracy
   golden, cross-scenario, routing eval), and the line
   "Single-approval gate: promoting to prod immediately per
   CLAUDECODE_BRIEF_MCPT_V32_PROD_APPROVAL.md."
7. PROMOTE IMMEDIATELY (do NOT wait for second tripwire touch):
   gcloud run services update-traffic amjis-mcp \
     --region asia-south1 \
     --to-tags staging=100
8. Tag and observe:
   git tag mcpt-v32-prod
   git push origin mcpt-v32-prod
   gh issue create \
     --title "[MCPT-v3.2] Post-prod observation 7-day window" \
     --label "observation" \
     --body "Track tool_health, error_rate, and prod-traffic latency for
              7 days from 2026-05-23. Rollback procedure: gcloud run
              services update-traffic amjis-mcp --to-revisions <prev>=100."

Rationale for single-approval: bench shows -60% round-trips, -71% bytes;
accuracy shows 100% cross-scenario agreement across 2,717 facts. The
staging re-run is verification, not a decision gate.

Failure handling:
- R3 fail (API key bad/quota): log, continue. Routing eval becomes follow-up.
- R1/R2 fail (DB/IAM): STOP, escalate via TaskCreate. Prod not touched.
- Staging deploy fail: STOP. Cloud Build logs in PR comment. Prod not touched.
- Staging harness regression: HARD STOP. Do NOT promote prod. Accuracy
  gate working as designed.
- Prod promotion fail: escalate. Previous revision still serves 100%.
EOF

touch .conductor-approve-prod
```

## What will happen automatically after Step 2

The conductor sub-agent for prod approval will:

1. Read `.conductor-instructions.md` on its next poll iteration (≤60 seconds).
2. Execute steps 1–8 from the override file, in order.
3. Update `.conductor-state.json` after each step.
4. Post the PR summary comment.
5. Promote prod.
6. Open the observation issue.
7. Update `.conductor-state.json` with `current_phase: complete`.

## Acceptance — done when

- [ ] `gcloud run services describe amjis-mcp --region asia-south1` shows the new revision at 100% traffic.
- [ ] `git tag --list mcpt-v32-prod` returns a tag.
- [ ] `gh issue list --label observation` shows the 7-day observation issue.
- [ ] PR comment contains all four diff tables with verdict: pass.
- [ ] `MIGRATIONS_APPLIED_LOG.md` shows the seed-load entry.
- [ ] `gcloud scheduler jobs describe nightly-mcp-audit --location asia-south1` returns ENABLED.

## Report back

After completion, report to Cowork (the native) with:

1. Production Cloud Run revision URL.
2. PR URL.
3. Observation issue URL.
4. Routing eval result (live number — the ≥15pp claim, verified or not).
5. Any failure encountered (with conductor escalation details).
