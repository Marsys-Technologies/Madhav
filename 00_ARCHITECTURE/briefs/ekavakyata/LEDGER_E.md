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
| -- | -- | -- | -- | -- | Awaiting VERIFIED markers |

---

## SS4 PENDING RULINGS

### EKV-R-01 (filed 2026-08-16 ~00:50 IST)

**Issue:** Gate PROD-SYNC check extracts `sha12` from catalog_version `+r` suffix and checks
`origin/main.startswith(sha12)`. The `+r` is SHA256(tool_names).slice(12), never a git sha.

**Evidence:**
- Live catalog_version: `catalog-1+t152+r653c2a1a98c8`
- origin/main tip: `63049a6e327e46a552496d7fc3a66f87a67d5ee8`
- Code: `mcp_catalog_version.ts:catalogContentHash()` = SHA256(JSON.stringify(tool_names)).slice(0,12)
- Check always fails: `"63049a6e327e...".startswith("653c2a1a98c8")` = FALSE

**Recommendation (Option A):** Change gate to check `deployed_main_sha` manifest field
(E-owned) against `git rev-parse origin/main` instead of parsing catalog_version.
One-line fix to ekv_gate.py; no source code changes needed.

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
