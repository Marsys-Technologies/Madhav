# MCPT v3.2 — Residuals

## Open items at close

### R1 — Phase 7a: data_source_expected seed load (BLOCKED — human gate)
**Status:** Pending `.conductor-approve-prod` tripwire
**Action:** Drop `.conductor-approve-prod` at worktree root, conductor resumes
**Command:** `cd platform-mcp && psql $DATABASE_URL < ../00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql`

### R2 — Phase 7b: nightly audit job (BLOCKED — human gate)
**Status:** Pending `.conductor-approve-prod` tripwire + R1 seed load
**Action:** After R1, create Cloud Run job:
```
gcloud run jobs create amjis-mcp-audit \
  --image gcr.io/madhav-astrology/amjis-mcp:latest \
  --region asia-south1 \
  --command node,audit.js

gcloud scheduler jobs create http nightly-mcp-audit \
  --schedule="0 3 * * *" \
  --uri="$(gcloud run jobs describe amjis-mcp-audit --format='value(status.url)')/run" \
  --http-method=POST \
  --oidc-service-account-email=audit@madhav-astrology.iam.gserviceaccount.com \
  --location asia-south1
```

### R3 — Phase 9b routing eval live run
**Status:** Dry-run verified. Live run requires ANTHROPIC_API_KEY.
**Action:** `ANTHROPIC_API_KEY=<key> npx tsx evals/mcp-routing/runner.ts`
**Goal:** ≥80% gold-or-acceptable first-tool recall under super_admin tier

### R4 — kp_significator 7/9 residual
**Status:** Upstream FORENSIC §4.3 source gap (5 houses absent). Not a v3.2 concern.
**Per:** MCPT_V33_CLOSE.md RESIDUAL documentation

### R5 — Phase 10 prod deployment
**Status:** Pending `.conductor-approve-prod` tripwire + Phase 7a/7b completion
**When ready:** Drop `.conductor-approve-prod` at worktree root; conductor will:
- Deploy staging: `gcloud builds submit --config=cloudbuild.yaml --substitutions=_TAG=mcpt-v32-staging`
- Post summary to PR #153
- Await human approval in PR comment
- Promote to prod via traffic split
- Tag `mcpt-v32-prod`
- Open 7-day observation window issue
