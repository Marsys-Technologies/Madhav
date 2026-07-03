---
canonical_id: CLAUDECODE_BRIEF_BA_PM1_SYNC_FREEZE
version: 1.0
status: COMPLETE
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program) — for execution by Claude Code in Antigravity
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P-1 (precedes P0)
objective: >
  CLEAN SLATE: every open thread in the repo resolved — uncommitted work committed, branches dispositioned
  and merged, GitHub + prod + localhost brought into exact sync, cruft pruned — so the unified program
  starts from ONE branch (main), ZERO dirty files, ZERO stashes, ZERO stale worktrees, and a prod revision
  that equals origin/main HEAD.
may_touch: [".git (branch/stash/worktree ops)", "00_ARCHITECTURE/**", "root brief files", "package-lock.json", ".claude/worktrees/**", ".worktrees/**", "deploy.yml execution (deploy only, no edits unless deploy fails)"]
must_not_touch: ["platform/migrations/** content", "platform/supabase/migrations/** content", "any writer/engine source (this brief is hygiene-only — NO functional changes)", "prod database (no DDL/DML)", "secrets"]
audit_snapshot_2026_07_03: >
  HEAD on fix/sidecar-startup-probe-flags (ec2dedc7, 1 ahead); local main df2dfacc = 1 ahead of
  origin/main 40a7f0d1; local branches unmerged-by-ancestry: chore/mcp-elevation-run-report(5),
  docs/cowork-session-artifacts(4), fix/e2e-audit-remediation(1), fix/sidecar-ephemeris-thresholds(2),
  fix/sidecar-startup-probe-flags(1); 2 stashes (stash@{1} is WIP on main); 4 prunable worktrees
  (.claude/worktrees ×3 + .worktrees/fix/e2e-audit-remediation); ~8 stale origin feature/mcp-m* branches;
  14 untracked files (9 = 00_ARCHITECTURE strategy/audit docs incl. BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN,
  3 = root CLAUDECODE briefs, + accuracy/7d1c2135.json + package-lock.json). History uses SQUASH merges —
  ancestry checks are unreliable; compare by content.
---

# BRIEF BA-P-1 — SYNC FREEZE (clean slate before the unified run)

## Step 0 — Inventory (read-only; paste output into the close report)
`git fetch --all --prune` · `git status` · `git branch -vv -a` · `git stash list` · `git worktree list` ·
for each local branch: `git cherry origin/main <branch>` AND `git diff origin/main...<branch> --stat`
(squash-aware: a branch whose diff vs origin/main is empty-or-docs-only is CONTENT-MERGED regardless of
ancestry).

## Step 1 — Untracked file disposition
1. COMMIT to main (docs commit `docs(ba): strategic + audit corpus 2026-07-02/03`): the 9
   `00_ARCHITECTURE/*.md` (RATIFICATION_GUIDANCE, UNIFIED_EXECUTION_PLAN, MCP_E2E_TEST_REPORT,
   NAMING_STANDARD, ASTRO_COVERAGE, COVERAGE_MAP, RETRIEVAL_MODERNIZATION, TOOL_BLUEPRINT,
   RETRIEVAL_TO_SYNTHESIS) + this brief + the 3 root CLAUDECODE_BRIEF_* files — **check ROOT_FILE_POLICY
   §2 first**: if loose briefs are not root-permitted, `git mv` them to the policy's brief folder in the
   same commit.
2. `accuracy/7d1c2135.json`: inspect — if a build/test artifact, add to .gitignore; if meaningful, commit
   with a README line.
3. `package-lock.json` (root): determine why untracked — if the repo intentionally tracks per-package
   locks only, gitignore it; if it belongs, commit it. Do NOT regenerate.

## Step 2 — Stash triage (nothing dies uninspected)
For each stash: `git stash show -p stash@{n}` → (a) valuable → apply onto a rescue branch
`rescue/stash-<n>-<desc>`, commit, include in Step 3 dispositions; (b) superseded/noise → record the
one-line summary + file list in the close report, then drop. **Reverse-citation gate:** stash@{1} is WIP
on main — diff it against current main before judging superseded.

## Step 3 — Branch dispositions (content-based, squash-aware)
For each of the 5 local branches (+ any rescue/*): classify
- **CONTENT-MERGED** (empty effective diff) → delete local (+ delete remote twin if exists).
- **DOCS/GOVERNANCE-ONLY delta** (e.g. chore/mcp-elevation-run-report, docs/cowork-session-artifacts) →
  merge to main via PR (squash), fast review, delete branch.
- **CODE delta** (e.g. sidecar fixes ec2dedc7, ephemeris-thresholds remainder, e2e-audit remainder) →
  verify the delta is INTENDED-current (not superseded by a later merged PR — check origin/main log for
  the same paths); if intended: PR → CI green → merge; if superseded: record + delete.
- NOTHING is force-deleted while carrying a unique diff without a close-report entry listing that diff.
Then: delete the ~8 stale `origin/feature/mcp-m*` + other content-merged remote branches
(`git push origin --delete …`) — reverse-citation gate: confirm each is content-merged first.

## Step 4 — Worktree + cruft cleanup
`git worktree prune` + remove the 3 `.claude/worktrees/*` and `.worktrees/*` dirs (safe: no Antigravity
session active during this brief — CONFIRM before rm). Verify `.gcloudignore`/`.gitignore` cover
`.claude/`. Report disk reclaimed.

## Step 5 — Push + CI + deploy + PROD TRUTH
1. Push main (now containing Steps 1–3) to origin. NO force-push anywhere.
2. CI fully green (exit-code-3 known_residuals whitelist applies per hygiene policy §F).
3. Deploy web + sidecar via the standing pipeline (deploy.yml jobs). Apply NO new migrations (none should
   be pending from this brief — if any pending pre-existing migrations surface, STOP and report; do not
   auto-apply).
4. **Deploy truth:** `gcloud run services describe amjis-web --format='value(status.traffic[0].revisionName)'`
   (+ sidecar equivalent) — revision SHA == new origin/main HEAD. Wait out CDN (30–60s) before smoke.
5. Prod smoke: /api/health path per runbook + one MCP tool round-trip (list_my_charts) + one bounded
   serving check (get_domain_reading default ≤ its cap on 482012f1) `[verify-against: prod]`.

## Step 6 — Localhost sync + final state
`git checkout main && git pull && git remote prune origin`; delete all dispositioned local branches;
`git stash list` empty; `git worktree list` = main only; `git status` clean.
**ACCEPTANCE (all `[verify-against: prod|repo]`):**
- [ ] exactly ONE local branch (main) == origin/main == Cloud Run revision SHA
- [ ] zero untracked/dirty, zero stashes, zero worktrees, stale remote branches pruned
- [ ] close report lists EVERY disposition (file/stash/branch → action + rationale)
- [ ] CURRENT_STATE_v1_0.md appended: P-1 SYNC-FREEZE complete entry naming main HEAD as the program's
      start SHA; SESSION_LOG entry per governance
- [ ] this brief's frontmatter status → COMPLETE

*On completion, the unified program triggers at P0 from the recorded start SHA.*
