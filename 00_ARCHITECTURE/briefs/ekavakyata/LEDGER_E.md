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

### EKV-R-01 RESOLVED (EKV-R-2 Option A implemented by CONDUCTOR)

Gate PROD-SYNC fix applied: gate compares `manifest["deployed_main_sha"]` vs `git rev-parse origin/main`.
E writes `deployed_main_sha` after each merge+deploy cycle.

**FINAL deployed_main_sha:** `b2dc6be8ebbbeb72b5bc5df70ac5b8b4fbcace9f` (A-13 FINAL drain, deploy run 31913806187 web+MCP SUCCESS ~23:15Z)
**FINAL origin/main:** `b2dc6be8ebbbeb72b5bc5df70ac5b8b4fbcace9f` (A-13 merged ~22:55Z)
**PROD-SYNC: PASS** (deployed_main_sha == origin/main)

---

## SS3 MERGE LOG

| Time (UTC) | Lane | PR# | Merged SHA | Deploy Run | Status |
|------------|------|-----|-----------|-----------|--------|
| ~19:38Z | A-01 | #1289 | 55a476fbd28f16abfaae756633a4729a23016379 | — | **LIVE** (A-01+A-05 co-deploy ~20:09Z) |
| ~20:00Z | A-05 | #1290 | 3deb54180deeb2f6141f189899da29284638ac54 | 31906219... | **LIVE** (evidence: a01_a05_deploy.json) |
| ~20:10Z | A-03 | #1293 | 12cbf5e14dd26b4a36ac44ffbe88efec67674f06 | 31906422500 | **LIVE** (A-03+A-06 co-deploy ~20:31Z; evidence: a03_a06_deploy.json) |
| ~20:18Z | A-06 | #1291 | cfc37fc381661fd2671b299978d28cb5a9f13aad | 31906422500 | **LIVE** |
| ~20:28Z | C-01/C-02 | #1295 | 20266702ada941565569dac8fc76b0b89b5ae88d | 31907248672 | **LIVE** (EKV-R-1 4/4 PASS ~20:50Z; evidence: c01_a04_deploy.json) |
| ~20:51Z | A-04 | #1292 | a2ce6dc37ef3f460cabefa7e76287750a565441c | 31907248672 | **LIVE** (web+MCP deployed) |
| ~20:55Z | A-02 | #1294 | 33dfb2ba1a2a900ef641d82755f8cc14426c2104 | 31908358001 | **LIVE** (A-02 evidence: a02_whitelist_probe.json; 4-tool MCP probe PASS ~21:54Z) |
| ~21:05Z | B-02 | #1297 | 33289b579a00f73e191d12964d285dea9bff2270 | 31908884289 | **LIVE** (evidence: b02_b03_deploy.json) |
| ~21:11Z | B-03 | #1298 | bdc27ccdfabdea33e4620a9b80de186f359171d7 | 31908884289 | **LIVE** |
| ~21:20Z | B-04 | #1299 | 44d5ff5a76094aac4deaa148f1f3f3b43bd7845e | 31909264034 | **LIVE** (evidence: b04_a09_deploy.json) |
| ~21:29Z | A-09 | #1301 | 6a0f8c9d284118f9758eaaa1fd3f4b411b6ce1aa | 31909647552 | **LIVE** (EKV-R-8: CI SC/TAP non-blocking; merged by conductor per PRATINIDHI ruling) |
| ~21:38Z | B-05 | #1303 | 0a056aec841ad4be65714d1c2d2e3793a63861a3 | 31910024692 | **LIVE** (evidence: b05_classical_spec.json) |
| ~21:45Z | A-15 | #1300 | 7a1c79bf4da000f1c09f5a468d24ce262afcfcc0 | 31910678712 | **LIVE** (MCP smoke flap on first run 31910398270; retry SUCCESS; evidence: a15_ayanamsha.json) |
| ~21:55Z | A-11 | #1302 | c75400b231f95b2933f736d1630cc5b920fee8e9 | 31911459360 | **LIVE** (co-deployed with C-03; 1st deploy 31911149433 Google Fonts flap; retry SUCCESS) |
| ~22:03Z | C-03 | #1287 | b1ea4cdab35393961837ad0af953b23195a623cf | 31911459360 | **LIVE** (co-deployed with A-11; evidence: c03_standing_predictions.json) |
| — | B-01 | #1296 | — | — | **DIRTY** — E-LEAD fix dfbdfe620 pushed; add/add conflicts in ga_vargas_writer.py + test_dignity_oracle.py; ŚĀSTRA-LEAD must rebase onto b2dc6be8e (current main) |
| ~22:12Z | A-07 | #1304 | 9b09835033e5cdb4ddf7d68eed529a9f1efa0be9 | 31911942143 | **LIVE** (co-deployed with A-16; run 31911942143 SUCCESS ~22:32Z) |
| ~22:21Z | A-16 | #1308 | fb6e4185b197c248a460d259075c8a187c039e32 | 31911942143 | **LIVE** (co-deployed with A-07; web+MCP SUCCESS ~22:32Z) |
| ~22:30Z | A-17 | #1309 | 46e59ac990df67bb2ae8fc329dc9b853b6730b7f | 31912688002 | **LIVE** (1st deploy MCP flap; covered by A-08 deploy run 31912688002 MCP SUCCESS ~22:43Z) |
| ~22:37Z | A-08 | #1305 | 84c6d55867b43b7a9f44ec9d682591ef2dbc73a9 | 31912688002 | **LIVE** (deploy run 31912688002 web+MCP SUCCESS ~22:45Z; also covers A-17) |
| ~22:46Z | A-12 | #1306 | cd7653855d02111f742cc1bd9a4d059cb98bc773 | 31913055119 | **LIVE** (deploy run 31913055119 web-only SUCCESS ~23:00Z; MCP not changed by A-12) |
| ~22:55Z | A-13 | #1307 | b2dc6be8ebbbeb72b5bc5df70ac5b8b4fbcace9f | 31913806187 | **LIVE** (FINAL drain; 1st MCP flap 31913429332; retry 31913806187 web+MCP SUCCESS ~23:15Z) |

### Integration notes
- **A-02 GUARDIAN gap closed**: GUARDIAN (22:10Z) flagged that a02_deploy.json only proved deploy, not function. E-LEAD ran live MCP probe ~21:54Z: all 4 tools (list_classical_texts, find_verses_about, search_classical_texts, read_chapter) callable; evidence: a02_whitelist_probe.json.
- **A-09 EKV-R-8**: PRATINIDHI authorized A-09 merge despite SC-17/18/19+TAP-5/7/S-13 CI failures (non-blocking checks per EKV-R-8). merge_log status=LIVE is a EKV-R-8 deviation per CONDUCTOR note.
- **A-15 MCP smoke flap**: First deploy run 31910398270 MCP smoke failed (bearer-auth 401; transient). Retry deploy 31910678712 MCP=SUCCESS at ~22:00Z.
- **B-01 DIRTY signal** posted to CAMPAIGN_COORDINATION ~21:57Z (commit 53de31d6e). Conflicts: ga_vargas_writer.py (B-02 Rahu/Ketu vs B-01 dignity wiring) + brahmagyan/__tests__/test_dignity_oracle.py (add/add semantic: exaltation vs MT priority for Moon at 10° Taurus).
- **CL-00 EKV-R-5/R-9**: PRATINIDHI authorized NOT-RUN. ekv_controls.py exists only in dharma worktree (not on main). Permanent for this wave. Gate will fail on CL-00; failure is authorized (wave closes PARTIAL).
- **A-02 merged SHA corrected**: Earlier manifest had wrong SHA; corrected to 33dfb2ba1a2a900ef641d82755f8cc14426c2104.
- **A-03 merged SHA corrected**: gate reported 12cbf5e14c15 NOT ancestor; corrected to 12cbf5e14dd26b4a36ac44ffbe88efec67674f06.

---

## SS4 RULINGS

### EKV-R-1 (PRATINIDHI, 2026-08-16T01:15+05:30) — C-01 AUTHORIZED
C-01 migration AUTHORIZED. 4 post-deploy assertions ALL PASSED at 2026-08-15T20:50Z.
Evidence: c01_a04_deploy.json. EKV-R-1 CLOSED.

### EKV-R-2 / EKV-R-01 (PRATINIDHI, 2026-08-16T01:15+05:30) — GATE FIX APPROVED
Gate PROD-SYNC fix applied: compare `deployed_main_sha` vs `git rev-parse origin/main`. IMPLEMENTED.

### EKV-R-5 (PRATINIDHI, ~2026-08-15T21:40Z) — CL-00 NOT-RUN AUTHORIZED
ekv_controls.py not on main; Stream D dead. CL-00 must remain NOT-RUN (null). Wave closes PARTIAL. Gate failure on CL-00 is authorized. E must NOT run CL-00 from dharma worktree.

### EKV-R-8 (PRATINIDHI, ~2026-08-15T21:40Z) — A-09 FORCE-MERGE
A-09 SC-17/18/19+TAP-5/7/S-13 CI failures are non-blocking. CONDUCTOR authorized to merge A-09 without fixing them. A-09 manifest status=LIVE is an EKV-R-8 deviation.

### EKV-R-9 (PRATINIDHI, ~2026-08-15T21:40Z) — CL-00 OVERRIDE
CONDUCTOR Step 4 OVERRIDDEN. CL-00 must NOT be run from dharma worktree. Stream E: SKIP Step 4 entirely. Permanent for this wave.

### EKV-SENTINEL-BLOCK-001 — CLEARED
C-01 merge block cleared: EKV-R-1 now in PRATINIDHI ledger.

---

## SS5 OPERATIONAL NOTES

- CWD WARNING: Bash commands default to `/Users/Dev/Vibe-Coding/Apps/Madhav/` (main repo,
  branch `audit/paripurna2-evidence`). ALL git ops must `cd` to worktree first.
- ekv_manifest.json lives at main repo path (untracked) for gate readability.
- LEDGER_E.md lives in THIS worktree (ekv-lead-sangama), committed to ekv/lead-sangama.
- gh CLI: authenticated as amonty84. Repo: Marsys-Technologies/Madhav
- origin/main at session start: `63049a6e327e46a552496d7fc3a66f87a67d5ee8`
- origin/main at ~22:00Z: `c75400b231f95b2933f736d1630cc5b920fee8e9` (A-11)

## SS6 COST: $0 running / $35 budget

## SS7 GATE STATUS — FINAL (~23:18Z)

### W0 Gate run result:
```
EKV-GATE: FAILED
  ✗ CL-00 cheap subset not PASS (got None) — regression baseline unproven
1 blocking problem(s). Terminal marker MUST NOT be posted.
```

**1 failure — CL-00 only** — authorized per EKV-R-5/R-9 (permanent).
**PROD-SYNC: PASS** — deployed_main_sha = origin/main = b2dc6be8ebbb.
**Wave status: CLOSED-PARTIAL per EKV-R-5.**

### Gate result posted:
- Commit 733ebe2be to `campaign-coordination` branch → pushed to origin/campaign-coordination
- CONDUCTOR/SENTINEL will pick up for countersign

### Drain MCP smoke flap summary:
| Lane | First Deploy | Outcome | Resolution |
|------|-------------|---------|------------|
| A-15 | 31910398270 | MCP flap (401) | Retry 31910678712 SUCCESS |
| A-11+C-03 | 31911149433 | Google Fonts failure | Retry 31911459360 SUCCESS |
| A-17 | 31912330035 | MCP flap (401) | Covered by A-08 deploy 31912688002 |
| A-13 | 31913429332 | MCP flap (401) | Retry 31913806187 SUCCESS |

All transient — same bearer-auth 401 pattern. Not code issues.

### C-03 lease_ok correction:
C-03 `lease_ok` was `null` (tracking gap from HANDOFF era). Set to `true` after LIVE confirm — files (`prospective_ledger.ts`, `query_prospective_ledger.ts`) are unique to C-03; no other lane touches them.

### Remaining open items (post-CLOSED-PARTIAL):
- **B-01**: ŚĀSTRA-LEAD must rebase onto b2dc6be8e + resolve 2 conflicts → re-queue
- **SENTINEL re-run**: Awaiting
- **PRATINIDHI countersign**: Awaiting → formal CLOSED-PARTIAL declaration
