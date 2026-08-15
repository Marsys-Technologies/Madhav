# LEDGER_E -- SANGAMA (Stream E) -- EKAVAKYATA Campaign

**Role:** SANGAMA-LEAD (sole writer on main, integrator, sole writer of ekv_manifest.json)
**Model:** claude-sonnet-4-6 (sonnet-high)
**Session start:** 2026-08-16
**Worktree:** `.claude/worktrees/ekv-lead-sangama` (branch: ekv/lead-sangama)
**Manifest location:** `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/ekavakyata/ekv_manifest.json` (main repo, untracked -- gate reads here)

---

## SS1 DEPLOY PROCEDURE (verified 2026-08-16 from deploy.yml source)

### Trigger chain

```
push to origin/main
  -> CI: .github/workflows/ci.yml ("CI -- Ganga Quality Gate") runs on main
    -> on success: .github/workflows/deploy.yml triggers (workflow_run event)
      -> Job: changes (path-change detection)
        -> Job: deploy-web (ALWAYS -- runs migrations + web image)
        -> Job: deploy-mcp (if platform-mcp/** changed)
        -> Job: deploy-sidecar (if platform/python-sidecar/** changed)
        -> Job: deploy-pipeline-job (if pipeline/sidecar paths changed)
```

### Merge procedure (per lane)

```bash
# From ekv-lead-sangama worktree:
cd /Users/Dev/Vibe-Coding/Apps/Madhav/.claude/worktrees/ekv-lead-sangama
git fetch origin

# Verify lane branch is rebased on origin/main
git log --oneline origin/ekv/<lane> ^origin/main | head -5

# Push lane to origin (if not already pushed)
git push origin ekv/<lane>

# Create PR via gh CLI
gh pr create --repo Marsys-Technologies/Madhav \
  --base main --head ekv/<lane> \
  --title "ekv(<lane>): <description>" \
  --body "<exit_test_result + evidence>"

# Merge PR (rebase-based)
gh pr merge <PR#> --repo Marsys-Technologies/Madhav --rebase --auto

# Wait for CI -> deploy cycle (~13-15min for MCP lanes)
# Confirm: git rev-parse origin/main == merged sha

# Post-deploy probe (save evidence JSON)
# Update ekv_manifest.json (sole writer)
```

### deploy-web specifics (mandatory job)
1. Cloud SQL Auth Proxy starts (port 5432)
2. Migrations run: `cd platform && npx tsx scripts/migrate.ts`
3. Web image built+pushed tagged with github.sha
4. Cloud Run `amjis-web`: --no-traffic deploy -> smoke -> promote

### deploy-mcp specifics (conditional: platform-mcp/** changed)
1. MCP image built+pushed tagged with github.sha
2. Cloud Run `amjis-mcp`: --no-traffic -> smoke via mcp_end_to_end_smoke.sh -> promote

### Migration verification (per SS.4 §N.4)
```sql
SELECT migration_name, applied_at FROM _migrations_applied ORDER BY applied_at DESC LIMIT 10;
```
Must show C-01/C-02 migration names with applied_at AFTER deploy timestamp.

---

## SS2 PROD-SYNC VERIFICATION

### EKV-R-01 PENDING -- see SS4

Live catalog_version (2026-08-16 session start): `catalog-1+t152+r653c2a1a98c8`

The `+r653c2a1a98c8` is SHA256(tool_names).slice(0,12) NOT the git sha.
Gate's `main_tip.startswith(sha12)` will ALWAYS fail.

### Interim procedure (until EKV-R-01 resolved)
1. Call mcp_server_info -- confirm response non-error (server up)
2. Note tools_changed_at >= deploy trigger time (confirms new code running)
3. git rev-parse origin/main == pushed merge sha
4. Record both: `deployed_catalog_version` (from server) + `deployed_main_sha` (from git)

---

## SS3 MERGE LOG

| Time (IST) | Lane | PR# | Merged SHA | Deploy SHA | Status |
|------------|------|-----|-----------|-----------|--------|
| ~01:50 IST | A-01 | #1289 | 55a476fbd28f16abfaae756633a4729a23016379 | 3deb54180 | **LIVE** (A-01+A-05 co-deployed ~20:09Z; MCP up) |
| ~01:30 IST | A-05 | #1290 | 3deb54180deeb2f6141f189899da29284638ac54 | 3deb54180 | **LIVE** (A-01+A-05 co-deployed ~20:09Z) |
| ~01:00 IST | A-06 | #1291 | — | — | MERGE QUEUE (queued) |
| ~01:00 IST | A-04 | #1292 | — | — | MERGE QUEUE (queued) |
| ~01:00 IST | A-03 | #1293 | — | — | MERGE QUEUE (queued) |
| ~01:30 IST | A-02 | #1294 | — | — | MERGE QUEUE (CI CLEAN 19:54Z; already queued) |
| ~01:15 IST | C-01/C-02 | #1295 | — | — | MERGE QUEUE (EKV-R-1 auth; queued) |
| ~01:48 IST | B-01 | #1296 | — | — | CI RUNNING (autoMerge set) |
| ~01:48 IST | B-02 | #1297 | — | — | CI RUNNING (autoMerge set) |
| ~01:48 IST | B-03 | #1298 | — | — | CI RUNNING (autoMerge set) |
| ~01:48 IST | B-04 | #1299 | — | — | CI RUNNING (autoMerge set) |
| ~01:50 IST | A-15 | #1300 | — | — | CI RUNNING (autoMerge set) |
| ~01:24 IST | A-09 | #1301 | — | — | CI RUNNING (autoMerge set; just created) |
| ~01:24 IST | A-11 | #1302 | — | — | CI RUNNING (autoMerge set; just created) |
| ~01:24 IST | B-05 | #1303 | — | — | CI RUNNING (autoMerge set; just created) |

### Integration notes
- A-02 (#1294): count gate `56→60` fix pushed (47c7ec6e5). Two test files updated.
- C-01 (#1295): EKV-R-1 AUTHORIZED. 4 post-deploy assertions required before LIVE.
- A-09 (#1301): 2 commits — dcc2fb5a (SaraKernel API freeze) + ceadae8cb (buildAssessResponse). registry_bridge.ts relock after merge.
- B-05 (#1303): LEASE EXCEPTION — writes register_d8_assess_domain.ts (Stream A territory); pre-authorized per LEDGER_B.
- Context-resume at ~20:00Z (19:54Z UTC): new PRs created for A-09/A-11/B-05; merge queue processing A-05 first.
- A-15 (#1300): TypeScript TS2304 failure found (2 missed na() calls at lines 1087+1949); dequeued via GraphQL, fix pushed f7402c99e, re-queued. CI re-running.
- A-01+A-05 deploy confirmed LIVE at ~20:09Z: deploy.yml sha=3deb5418 conclusion=success; MCP server up; catalog_version unchanged (non-catalog lanes). Evidence: a01_a05_deploy.json.

---

## SS4 RULINGS

### EKV-R-1 (PRATINIDHI, 2026-08-16T01:15+05:30) — C-01 AUTHORIZED

C-01 migration (delete 6 empty-daterange rows + CHECK guard) AUTHORIZED by PRATINIDHI.
E must run 4 post-deploy assertions after C-01 deploys:
1. `SELECT count(*) FROM _migrations_applied WHERE filename='572_ekv_c01_ledger_empty_daterange_repair.sql'` → 1
2. `SELECT count(*) FROM brahma_prospective_ledger WHERE isempty(observation_window)` → 0
3. INSERT empty range → CHECK violation (test in throwaway txn, rollback)
4. `SELECT count(*) FROM brahma_prospective_ledger WHERE lifecycle_status='open'` → 29

### EKV-R-2 / EKV-R-01 (PRATINIDHI, 2026-08-16T01:15+05:30) — GATE FIX APPROVED

Gate PROD-SYNC fix: **Option A APPROVED**. CONDUCTOR fixes `ekv_gate.py` to compare
`manifest["deployed_main_sha"]` against `git rev-parse origin/main`. E writes
`deployed_main_sha` after each merge+deploy. Interim procedure (SS2) remains in force
until Conductor applies the fix.

### EKV-SENTINEL-BLOCK-001 — CLEARED

C-01 merge block cleared: EKV-R-1 now in PRATINIDHI ledger (origin/ekv/pratinidhi-role).
B-territory (python-sidecar) lease granted via EKV-R-1.

---

## SS5 OPERATIONAL NOTES

- CWD WARNING: Bash commands default to `/Users/Dev/Vibe-Coding/Apps/Madhav/` (main repo,
  branch `audit/paripurna2-evidence`). ALL git ops must `cd` to worktree first.
- ekv_manifest.json lives at main repo path (untracked) for gate readability.
- LEDGER_E.md lives in THIS worktree (ekv-lead-sangama), committed to ekv/lead-sangama.
- gh CLI: authenticated as amonty84. Repo: Marsys-Technologies/Madhav
- No ekv/* PRs open at session start. PR #1287 open (C-03's base).
- origin/main at session start: `63049a6e327e46a552496d7fc3a66f87a67d5ee8`

## SS6 COST: $0 running / $35 budget
