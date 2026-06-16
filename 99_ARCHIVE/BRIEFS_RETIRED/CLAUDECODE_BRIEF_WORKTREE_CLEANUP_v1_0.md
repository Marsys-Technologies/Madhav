---
artifact: CLAUDECODE_BRIEF_WORKTREE_CLEANUP_v1_0.md
version: "1.0"
status: READY_FOR_EXECUTION
produced_during: WORKTREE_AUDIT_2026-06-08
role: Executable brief for Claude Code (Antigravity) to clean up stale worktrees + branches after a content-verified audit. Each branch was tested for unique-vs-main content; this brief acts only on verified-safe items and gates the one residual risk.
executor: Claude Code in Google Antigravity IDE (NOT the CLI)
hard_constraints:
  - "Recover before delete: ws3's 4 governance smriti files are cherry-picked to main BEFORE feature/ws3-rule-base is deleted."
  - "The 3 feat/* branch deletions are GATED on the A3/A4/A5 writer-coverage check (Step 4). If coverage is NOT confirmed, recover the writers first — do NOT delete."
  - "feature/v13-prod-data (Prod3) contains a plaintext prod DB password on a pushed origin branch. Deleting the branch does NOT undo the leak — the operator MUST rotate the password (Step 6). Flag this prominently."
  - "Use 'git branch -d' (lowercase, merge-safe) wherever the branch is merged; only use -D for the verified-stale/throwaway branches, and only after this brief's checks pass."
  - "Worktree folders already appear gone from disk (prunable). 'git worktree prune' only removes bookkeeping for non-existent paths — it cannot touch a live folder or any branch/commit."
audit_source: in-session WORKTREE_AUDIT 2026-06-08 (content-verified per branch)
---

# Brief — Worktree + Stale-Branch Cleanup

Every branch below was tested by CONTENT (files absent from main, and whether main
superseded/deleted them), not by commit count. Squash-merges make "commits ahead" unreliable;
this brief trusts file-content verification only.

Repo root: `/Users/Dev/Vibe-Coding/Apps/Madhav`. origin/main fetched fresh.

## Verified disposition (from the audit)

| Branch | Verdict | Why |
|---|---|---|
| feature/m6-prospective-testing | DELETE | Native pre-cleared. |
| fix/make-everything-work | DELETE | Merged (L0FR seal e18153a8), 0 ahead. |
| feature/legacy-teardown | DELETE | 303 absent files, ALL main-deleted staleness, 0 authored. |
| feature/ws2-depth-build | DELETE | Merged #211; only the superseded common-6 absent. |
| feature/wsmisc-cleanup | DELETE | Merged; only superseded common-6. |
| feature/ws3-rule-base | CHERRY-PICK 4 → DELETE | Merged #210; 4 smriti files genuinely absent. |
| feature/v13-prod-data | DELETE + ROTATE PW | Throwaway scratch + plaintext prod password leaked. |
| feat/data-plumbing | DELETE (gated) | Superseded; shares the 15-file v1-cockpit set. |
| feat/funnel-polish | DELETE (gated) | Same superseded 15-file set. |
| feat/visual-v2 | DELETE (gated) | Same superseded 15-file set. |

"common-6" (superseded on main, do NOT treat as unique): platform-mcp/cloudbuild.yaml
(deleted PR #217 dd0cbebe), platform/src/lib/build/trigger.ts + events.ts +
__tests__/trigger.test.ts (retired by Cockpit-v2 go-live 1fbef119),
platform/tests/components/TierPicker.test.tsx + BuildChat.test.tsx (deleted by test-hygiene 1f2f83a8).

---

## STEP 0 — Branch + safety snapshot

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin && git switch main && git pull --ff-only origin main
git switch -c chore/worktree-cleanup

# Safety net: tag every branch tip before any deletion, so nothing is unrecoverable
# even if a verdict is wrong. Tags are cheap and can be deleted later.
for b in feature/m6-prospective-testing fix/make-everything-work feature/legacy-teardown \
         feature/ws2-depth-build feature/wsmisc-cleanup feature/ws3-rule-base \
         feature/v13-prod-data feat/data-plumbing feat/funnel-polish feat/visual-v2; do
  git rev-parse --verify "$b" >/dev/null 2>&1 && \
    git tag "archive/pre-cleanup/$(echo $b | tr '/' '-')" "$b" && echo "tagged $b"
done
# These archive/ tags mean any branch can be restored with: git branch <name> <tag>
# Delete the tags after you're satisfied (Step 7).
```

---

## STEP 1 — Prune dead worktree registrations (zero risk)

The 10 sibling folders are gone from disk; this clears git's stale bookkeeping only.

```bash
git worktree prune --verbose   # removes registrations for non-existent paths only
git worktree list              # should show only the Madhav worktree afterwards
```

---

## STEP 2 — Recover ws3's 4 governance smriti files to main (BEFORE deleting ws3)

```bash
for f in \
  00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_C/sample.md \
  00_ARCHITECTURE/CONDUCTOR/ws3/acharya_eval_gate_C/verdict.md \
  00_ARCHITECTURE/CONDUCTOR/ws3/smriti/gate-c-pass.md \
  00_ARCHITECTURE/CONDUCTOR/ws3/smriti/wave-close-pass.md ; do
  git checkout feature/ws3-rule-base -- "$f"
done
git add 00_ARCHITECTURE/CONDUCTOR/ws3/
git commit -m "chore(ws3): recover 4 Gate-C / wave-close governance smriti from feature/ws3-rule-base

These landed on the branch after PR #210 merged and were never on main. Recovered before
deleting the stale branch. Docs only, no code."
```

---

## STEP 3 — (Optional) Archive Prod3's one smriti, then it's clear to delete

The only non-throwaway file on feature/v13-prod-data is its STREAM3_COMPLETE smriti. The
6 Python files are throwaway (plaintext password + hardcoded MadhavProd3 paths — do NOT
commit them anywhere). Optionally preserve the smriti:

```bash
mkdir -p 00_ARCHITECTURE/_archive/v13-prod-3
git checkout feature/v13-prod-data -- \
  00_ARCHITECTURE/CONDUCTOR/v13-prod-3-data/smriti/STREAM3_COMPLETE.md 2>/dev/null && \
  git mv 00_ARCHITECTURE/CONDUCTOR/v13-prod-3-data/smriti/STREAM3_COMPLETE.md \
         00_ARCHITECTURE/_archive/v13-prod-3/STREAM3_COMPLETE.md 2>/dev/null
git add 00_ARCHITECTURE/_archive/ 2>/dev/null
git commit -m "chore(archive): preserve Prod3 STREAM3_COMPLETE smriti before deleting throwaway branch" 2>/dev/null || echo "nothing to archive — skip"
```
DO NOT recover check_tables.py / lean_pipeline.py / run_data_pipeline.py / seed_kala_*.py —
they carry a plaintext prod credential and worktree-absolute paths.

---

## STEP 4 — GATE: verify A3/A4/A5 pipeline-writer coverage before deleting the feat/* branches

The 3 feat branches share an identical 15-file v1-cockpit set, superseded by the Cockpit-v2
rewrite. 12 of 15 are clearly-replaced UI/API. THREE are engine writers that need a coverage
confirm before deletion:
- platform/python-sidecar/pipeline/writers/chart_facts_writer_a3.py
- platform/python-sidecar/pipeline/writers/panchanga_writer_a4_adapter.py
- platform/python-sidecar/pipeline/writers/sensitive_points_writer_a5_adapter.py
(+ __tests__/test_a3_writer.py)

Verify main's CURRENT pipeline produces the same A3/A4/A5 facts (chart_facts, panchanga,
sensitive points) those writers wrote:

```bash
# What writer/loader code does main have for these layers now?
git ls-tree -r --name-only origin/main | grep -iE "writer|chart_facts|panchanga|sensitive" | grep -i "python-sidecar"
# Inspect the branch versions to know what logic to look for:
git show feat/visual-v2:platform/python-sidecar/pipeline/writers/chart_facts_writer_a3.py | head -60
```

DECISION:
- IF main has equivalent writer/loader coverage for A3 (chart_facts), A4 (panchanga), A5
  (sensitive points) — the L0FR / Multi-Ayanamsha rewrite almost certainly does — then the
  3 writers are SUPERSEDED. Record which main files cover them in the commit message and
  proceed to Step 5 (delete all 3 feat branches).
- IF main has NO equivalent for any of the three → HALT on that writer. Recover it to main
  (git checkout feat/visual-v2 -- <path>, commit) BEFORE deleting the feat branches. Report
  which writer lacked coverage.

(The other 12 v1-cockpit files are confirmed superseded — no per-file check needed.)

---

## STEP 5 — Delete the cleared branches + their worktree registrations

Only after Steps 2 + 4 pass. Use -d for merged branches (refuses if not merged = safety);
-D only for the verified-stale/throwaway ones.

```bash
# Merged → -d (git refuses if somehow not merged):
git branch -d fix/make-everything-work

# Verified-stale / merged-via-squash / throwaway → -D (content-verified safe above).
# The archive/ tags from Step 0 are the recovery net.
for b in feature/m6-prospective-testing feature/legacy-teardown feature/ws2-depth-build \
         feature/wsmisc-cleanup feature/ws3-rule-base feature/v13-prod-data \
         feat/data-plumbing feat/funnel-polish feat/visual-v2 ; do
  git branch -D "$b" && echo "deleted $b"
done

# If any of these branches also exist on origin and should be removed there:
# (confirm with the native first if these were ever shared/PR'd)
# for b in <list>; do git push origin --delete "$b"; done

git worktree prune --verbose
git worktree list   # only Madhav remains
```

---

## STEP 6 — ⚠ OPERATOR: rotate the leaked prod DB password (URGENT, independent of git)

feature/v13-prod-data committed the prod DB password in plaintext
(`postgresql://amjis_app:<PW>@127.0.0.1:5433/amjis`) across 6 Python files on a branch that
was PUSHED to origin. Deleting the branch does NOT remove it from origin's reflog/history or
from anyone's clone. The password must be rotated.

```bash
# 1. Rotate the amjis_app DB user password in Cloud SQL:
gcloud sql users set-password amjis_app \
  --instance=amjis-postgres --project=madhav-astrology --prompt-for-password
# 2. Update the amjis-db-password secret with the new value (new version):
printf '%s' '<NEW_PASSWORD>' | gcloud secrets versions add amjis-db-password \
  --project=madhav-astrology --data-file=-
# 3. deploy.yml pins DB_PASSWORD=amjis-db-password:3 (and similar). After adding a new
#    version, bump the pin in deploy.yml to the new version number and redeploy, OR
#    repin to :latest. Confirm web + sidecar pick up the new secret.
# 4. Confirm the old password no longer works.
```
Record the rotation in OPERATOR_ACTIONS_PENDING.md.

---

## STEP 7 — Commit doc updates, push, PR; clean up archive tags when satisfied

```bash
# Update governance docs:
#  - 00_ARCHITECTURE/OPERATOR_ACTIONS_PENDING.md: add the DB-password rotation as a HIGH
#    item (done/pending); note the worktree cleanup.
#  - Update the Tier-3 merge-queue memory/tracking: all listed branches were stale/merged,
#    not pending merges — the queue is effectively empty now.
git add -A && git commit -m "chore(governance): worktree cleanup record + DB-password rotation note"
git push -u origin chore/worktree-cleanup
# Open PR to main.

# After the PR merges AND you've confirmed nothing was needed from the deleted branches,
# remove the safety tags:
# git tag -l 'archive/pre-cleanup/*' | xargs -n1 git tag -d
# (and push --delete if you pushed them)
```

---

## FINAL REPORT
Report: which branches deleted, ws3 cherry-pick commit SHA, Step-4 writer-coverage result
(superseded vs recovered + which main files cover A3/A4/A5), Prod3 smriti archived y/n,
DB-password rotation status, and the cleanup PR number. List any HALT (writer lacking
coverage) explicitly.
```
