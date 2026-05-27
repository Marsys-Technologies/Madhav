# GISMCP Remediation — Deploy + Cleanup Prompt
# Paste this ENTIRE prompt into a Claude Code chat session.
# Folder: /Users/Dev/Vibe-Coding/Apps/Madhav
# Branch: main (merge target)
# Purpose: Merge both GISMCP streams → deploy → post-deploy verify → cleanup → governance seal
# ─────────────────────────────────────────────────────────────────────────────

You are the GISMCP Remediation Operator executing the final deployment and cleanup arc.
`dangerouslySkipPermissions` is already set in `.claude/settings.local.json`.
No human confirmation gates during execution.
Execute all 8 phases in order. STOP at any failure and print `OPERATOR_HALT: <phase> — <error>`.

---

## CONTEXT

Two streams completed on their worktree branches:

| Stream | Branch | Worktree | What it delivers |
|--------|--------|----------|-----------------|
| 1 | `fix/gismcp-r1-r2` | `/Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1` | R1: server.ts tier gate removed; R2: 4 retrieval engine aliases |
| 2 | `fix/gismcp-r3`    | `/Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2` | R3: MSR grounding VERIFIED_NO_GAP (573/573) |

Stream 1 commits: `d5ba6774` (R1-S1), `feec914f` (R1-T1), `9b001bcc` (R2-S1/S2/T1), `4c83257f` (R2-T2)
Stream 2 commits: `747518fb` (R3-S1), `463a6b9f` (R3-S2), `871b3b15` (R3-T1), `969849de` (R3-SEAL)

---

## PHASE 1 — Pre-merge state check

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Main branch status (must be clean) ==="
git status --short

echo "=== Current main HEAD ==="
git log --oneline -5

echo "=== Worktree list ==="
git worktree list

echo "=== Stream 2 branch tip (fix/gismcp-r3) ==="
git log fix/gismcp-r3 --oneline -5

echo "=== Stream 1 branch tip (fix/gismcp-r1-r2) ==="
git log fix/gismcp-r1-r2 --oneline -5
```

**Expected:** `git status --short` returns empty (no staged/modified tracked files).
Both branches show at least 4 commits.
**If main has uncommitted changes:** HALT. Do not proceed.

---

## PHASE 2 — Merge both streams into main

Merge order: R3 first (data + tests only), then R1-R2 (server.ts + engines).

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Merging Stream 2 (R3 — data/tests, no server changes) ==="
git merge --no-ff fix/gismcp-r3 \
  -m "merge: GISMCP R3 — MSR grounding audit VERIFIED_NO_GAP (573/573)"
echo "Stream 2 merge exit: $?"

echo "=== Merging Stream 1 (R1+R2 — server.ts de-gating + retrieval engines) ==="
git merge --no-ff fix/gismcp-r1-r2 \
  -m "merge: GISMCP R1+R2 — server.ts tier gate removed; RETRIEVAL_TOOLS 51→55"
echo "Stream 1 merge exit: $?"

echo "=== Pushing to origin/main ==="
git push origin main
echo "Push exit: $?"

echo "=== main HEAD after merge ==="
MAIN_HEAD=$(git rev-parse --short HEAD)
echo "main HEAD: $MAIN_HEAD"
git log --oneline -10
```

**If any merge produces conflicts:** HALT immediately. Run `git merge --abort`, report which files conflicted.

---

## PHASE 3 — Deploy amjis-web (new retrieval engines — R2)

This deploys the 4 new retrieval aliases so `query_tara_balam`, `query_chandra_balam`,
`jaimini_chara_dasha`, `jaimini_chara_dasha_full` no longer 500 at the platform layer.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Building + deploying amjis-web ==="
gcloud builds submit --config cloudbuild.yaml --project madhav-astrology
WEB_EXIT=$?
echo "amjis-web build exit: $WEB_EXIT"

if [ $WEB_EXIT -ne 0 ]; then
  echo "OPERATOR_HALT: Phase 3 — amjis-web build failed (exit $WEB_EXIT)"
  exit 1
fi

echo "=== amjis-web latest revision ==="
gcloud run revisions list \
  --service=amjis-web \
  --region=asia-south1 \
  --project=madhav-astrology \
  --limit=3 \
  --format='table(name,status.conditions[0].type,createTime)'
```

Wait for the build to fully complete before proceeding to Phase 4.

---

## PHASE 4 — Deploy amjis-mcp sidecar (server.ts de-gating — R1)

This deploys the de-gated server.ts so all 40 tools are unconditionally visible
for all tiers (including the 5 ops tools now accessible to super_admin).

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Building + deploying amjis-mcp sidecar ==="
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_DEPLOY_TARGET=sidecar \
  --project madhav-astrology
SIDECAR_EXIT=$?
echo "amjis-mcp build exit: $SIDECAR_EXIT"

if [ $SIDECAR_EXIT -ne 0 ]; then
  echo "OPERATOR_HALT: Phase 4 — amjis-mcp sidecar build failed (exit $SIDECAR_EXIT)"
  exit 1
fi

echo "=== amjis-mcp latest revision ==="
gcloud run revisions list \
  --service=amjis-mcp \
  --region=asia-south1 \
  --project=madhav-astrology \
  --limit=3 \
  --format='table(name,status.conditions[0].type,createTime)'
```

---

## PHASE 5 — Post-deploy smoke verification

```bash
echo "=== Error log watch — amjis-web (last 5 minutes) ==="
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-web" AND severity>=ERROR' \
  --project=madhav-astrology \
  --freshness=5m \
  --limit=20 \
  --format='table(timestamp,textPayload)'

echo ""
echo "=== Error log watch — amjis-mcp sidecar (last 5 minutes) ==="
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-mcp" AND severity>=ERROR' \
  --project=madhav-astrology \
  --freshness=5m \
  --limit=20 \
  --format='table(timestamp,textPayload)'

echo ""
echo "=== Capture revision IDs for governance record ==="
WEB_REV=$(gcloud run revisions list \
  --service=amjis-web --region=asia-south1 --project=madhav-astrology \
  --limit=1 --format='value(name)')
MCP_REV=$(gcloud run revisions list \
  --service=amjis-mcp --region=asia-south1 --project=madhav-astrology \
  --limit=1 --format='value(name)')
echo "amjis-web revision:  $WEB_REV"
echo "amjis-mcp revision:  $MCP_REV"
```

**If ERROR logs contain tool-registration failures or import errors:** HALT and report.
Note the revision IDs — needed for the governance entry in Phase 8.

If `SMOKE_SESSION_COOKIE` is available in the environment, also run:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform
DB_PROXY_PORT=5433 npx vitest run \
  src/__tests__/integration/mcp_stub_engines.integration.test.ts \
  2>&1 | tail -15
```

---

## PHASE 6 — Retire worktrees

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Removing Stream 1 worktree (MadhavGISMCP-S1) ==="
git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
echo "S1 remove exit: $?"

echo "=== Removing Stream 2 worktree (MadhavGISMCP-S2) ==="
git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
echo "S2 remove exit: $?"

echo "=== Pruning stale worktree refs ==="
git worktree prune -v

echo "=== Remaining worktrees ==="
git worktree list
```

**If `git worktree remove` fails with "contains modified or untracked files":**
The worktrees committed everything — this should not happen. Verify with
`git -C /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1 status --short` first.
If the worktree is genuinely clean, use `--force` flag.

---

## PHASE 7 — Delete branches (local + remote)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Deleting local branches ==="
git branch -d fix/gismcp-r1-r2
echo "fix/gismcp-r1-r2 local delete exit: $?"

git branch -d fix/gismcp-r3
echo "fix/gismcp-r3 local delete exit: $?"

echo "=== Deleting remote branches ==="
git push origin --delete fix/gismcp-r1-r2
echo "fix/gismcp-r1-r2 remote delete exit: $?"

git push origin --delete fix/gismcp-r3
echo "fix/gismcp-r3 remote delete exit: $?"

echo "=== Verify gone (should return nothing) ==="
git branch -a | grep gismcp
echo "(empty = clean)"
```

---

## PHASE 8 — Governance seal

### 8a — Add GISMCP Remediation entry to CLAUDE.md §E

Read `CLAUDE.md`. Locate this exact bullet in §E:

```
- **Universal Parity Campaign — Three-channel tool parity**
```

**After** the closing text of that bullet (the line ending in `PR #164 merged at 79a8168f...`),
insert the following new bullet. Insert it BEFORE the closing `## §F` header:

```markdown
- **GISMCP Remediation — MCP sidecar tool visibility + retrieval engine fixes** — canonical_id `GISMCP_REMEDIATION_PLAN`, plan at `00_ARCHITECTURE/BRIEFS/GISMCP_REMEDIATION_PLAN_v1_0.md`, conductor artifacts at `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/`. **STATUS: COMPLETE (2026-05-26).** Two-stream autonomous execution (10 sessions total). Stream 1 `fix/gismcp-r1-r2`: (R1) removed `if (tier !== 'client')` tier gate from `platform-mcp/src/server.ts` — all 40 MCP tools now unconditionally registered for all API key tiers (client/acharya/super_admin); secondary runtime tier gates inside `tool_health.ts` + `data_coverage.ts` also removed; 5 ops tools (`tool_health`, `data_coverage`, `log_prediction`, `record_outcome`, `flag_disagreement`) that were hidden from super_admin now always visible; (R2) 4 canonical-name retrieval aliases created (`query_tara_balam`, `query_chandra_balam`, `jaimini_chara_dasha`, `jaimini_chara_dasha_full`) — thin wrappers to existing engines (`tara_balam_for_native`, `chandra_balam_for_native`, `query_jaimini_chara_dasha`); RETRIEVAL_TOOLS count 51 → 55; FORENSIC-grounded integration tests (birth date 1984-02-05 assertions) + MCP smoke tests. Stream 2 `fix/gismcp-r3`: (R3) MSR grounding confirmed VERIFIED_NO_GAP — 573/573 signals have non-null `source_citation` containing FORENSIC/LEL refs; `msr_grounding.integration.test.ts` asserts 0 null rows. Both branches merged to main (2026-05-26). **Worktrees MadhavGISMCP-S1 + MadhavGISMCP-S2 retired. Branches deleted.**
```

### 8b — Update CURRENT_STATE_v1_0.md

Read `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`.
Find the most recent `## Recent completions` or equivalent recent-events block.
Append:

```
- GISMCP Remediation COMPLETE (2026-05-26): all 40 MCP tools unconditional; RETRIEVAL_TOOLS 51→55; MSR 573/573 VERIFIED_NO_GAP; amjis-web <WEB_REV> + amjis-mcp <MCP_REV> deployed; worktrees + branches cleaned.
```

Replace `<WEB_REV>` and `<MCP_REV>` with the actual revision IDs captured in Phase 5.

### 8c — Append to SESSION_LOG.md

Append to `00_ARCHITECTURE/SESSION_LOG.md`:

```markdown
---
session_id: GISMCP-DEPLOY-2026-05-26
type: operator_deploy
date: 2026-05-26
phases_completed:
  - merge: fix/gismcp-r3 + fix/gismcp-r1-r2 → main
  - deploy: amjis-web (R2 retrieval engines)
  - deploy: amjis-mcp sidecar (R1 server.ts de-gating)
  - cleanup: worktrees MadhavGISMCP-S1 + MadhavGISMCP-S2 retired
  - cleanup: branches fix/gismcp-r1-r2 + fix/gismcp-r3 deleted
  - governance: CLAUDE.md §E + CURRENT_STATE + SESSION_LOG updated
deliverables:
  R1: All 40 MCP tools unconditional (tier gate removed)
  R2: RETRIEVAL_TOOLS 51→55 (4 canonical-name aliases)
  R3: MSR signals 573/573 VERIFIED_NO_GAP
cloud_run:
  amjis_web: REPLACE_WITH_WEB_REV
  amjis_mcp: REPLACE_WITH_MCP_REV
outcome: COMPLETE
---
```

Replace `REPLACE_WITH_WEB_REV` and `REPLACE_WITH_MCP_REV` with actual revision IDs.

### 8d — Update CLAUDE.md version line

Find the line at the very end of `CLAUDE.md` that begins:
```
*End of CLAUDE.md v4.5
```

Change `v4.5` to `v4.6` and prepend the following to the amendment list inside that line:
```
v4.6 (amended 2026-05-26 — GISMCP Remediation COMPLETE: all 40 MCP tools unconditional; RETRIEVAL_TOOLS 51→55; MSR 573/573 VERIFIED_NO_GAP; worktrees + branches cleaned; workstream added to §E. Prior: 
```

Then close the original `v4.5` content after `Prior: `.

### 8e — Commit and push governance changes

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git add CLAUDE.md \
        00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
        00_ARCHITECTURE/SESSION_LOG.md

git commit -m "governance: GISMCP Remediation COMPLETE — CLAUDE.md v4.6 + CURRENT_STATE + SESSION_LOG sealed"

git push origin main

echo "Governance commit: $(git rev-parse --short HEAD)"
```

---

## FINAL REPORT

After all 8 phases complete, print:

```
╔══════════════════════════════════════════════════════════════════╗
║        GISMCP REMEDIATION — OPERATOR DEPLOY COMPLETE            ║
╠══════════════════════════════════════════════════════════════════╣
║  Phase 1: [PASS/FAIL]  Pre-merge state check                    ║
║  Phase 2: [PASS/FAIL]  Merge R3 + R1-R2 → main                  ║
║  Phase 3: [PASS/FAIL]  Deploy amjis-web (R2 engines)            ║
║  Phase 4: [PASS/FAIL]  Deploy amjis-mcp sidecar (R1 de-gating)  ║
║  Phase 5: [PASS/FAIL]  Post-deploy log watch + smoke            ║
║  Phase 6: [PASS/FAIL]  Worktrees retired                        ║
║  Phase 7: [PASS/FAIL]  Branches deleted (local + remote)        ║
║  Phase 8: [PASS/FAIL]  Governance sealed (CLAUDE.md v4.6)       ║
╠══════════════════════════════════════════════════════════════════╣
║  main HEAD:          <git hash>                                  ║
║  amjis-web revision: <revision-id>                              ║
║  amjis-mcp revision: <revision-id>                              ║
║  Governance commit:  <git hash>                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  MCP tools visible:  40 / 40 (all tiers, unconditional)         ║
║  RETRIEVAL_TOOLS:    55                                          ║
║  MSR signals:        573 / 573 VERIFIED_NO_GAP                  ║
║  Worktrees:          RETIRED                                     ║
║  Branches:           DELETED                                     ║
╚══════════════════════════════════════════════════════════════════╝
```

Execute phases 1–8 now. STOP at any `OPERATOR_HALT`.
