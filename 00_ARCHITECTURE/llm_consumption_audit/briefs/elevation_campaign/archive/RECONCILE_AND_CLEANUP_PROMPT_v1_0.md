---
artifact: RECONCILE_AND_CLEANUP_PROMPT (Elevation Campaign v2.1)
version: 1.0
status: CURRENT
purpose: >
  Run AFTER the worktree pre-flight and BEFORE the three stream kickoffs. Reconciles the worktree
  layout change (sibling → in-repo .worktrees/), lands the outstanding charter amendment, and
  removes every artifact abandoned by the plan revisions so the streams start on a clean runway.
run_from: /Users/Dev/Vibe-Coding/Apps/Madhav (project root)
---

# Reconcile + cleanup — paste into Claude Code from the PROJECT ROOT

```
You are finishing the runway for the Elevation Campaign v2.1. The plan was revised twice while it
was being prepared, so some artifacts on disk belong to abandoned versions and the worktree layout
changed after pre-flight had already built it. Your job is to reconcile that and leave a clean
runway. The three stream sessions launch immediately after you finish.

PREPARATION ONLY. Do NOT start the campaign, do NOT begin lane work, do NOT deploy or rebuild.

CURRENT STATE (verified — trust it, but confirm before acting on anything destructive):
- main is at bed662c4 (PR #763). Branch protection is ON: 4 required checks, enforce_admins:true.
  Direct push to main is REJECTED. The only merge path is:
  git push origin <branch> → gh pr create --base main → gh pr merge --auto --squash
- gc.auto is already 0. Branches elev/alpha, elev/beta, elev/gamma exist locally and on origin.
- Worktrees were created at the OLD SIBLING paths:
  /Users/Dev/Vibe-Coding/Apps/madhav-wt-{alpha,beta,gamma}
- Branch docs/elevation-campaign-worktree-preflight holds commit 1da2a039 (charter amendment),
  pushed but NOT merged to main.
- The working tree has uncommitted edits to ELEVATION_CAMPAIGN_CHARTER_v2_1.md and
  KICKOFF_PROMPTS_v2_1.md, plus untracked PREFLIGHT_WORKTREE_PROMPT_v1_0.md. These are the NEWER
  versions and they supersede what is on the docs branch. They add charter §16 (cleanup) and move
  the worktrees in-repo.

Do all of the following, in order.

1. RELOCATE THE THREE WORKTREES, sibling → in-repo.
   Target layout:
     /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/alpha   -> elev/alpha
     /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/beta    -> elev/beta
     /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/gamma   -> elev/gamma
   WHY: the three streams run as Claude Code extension windows opened on this project folder. An
   IDE-hosted session may scope file access to the opened workspace; a sibling worktree sits outside
   it, and every operation would be blocked or prompt for permission — fatal for an unattended
   overnight run. `.worktrees/` is inside the workspace by construction and is already the repo's
   reserved, gitignored path.
   FIRST confirm `.worktrees/` is genuinely matched by .gitignore (expect a "Git worktrees" section).
   If it is not, add it and include that in the PR in step 3.
   Use `git worktree move` if the worktrees are clean and it works; otherwise `git worktree remove`
   then re-add at the new path. The branches must survive either way — verify each new worktree is
   on its intended branch afterwards.
   NOTE ON PRUNING: run `git worktree prune` ONLY from this canonical path. Run from any other mount
   or alias of the same repo, git cannot resolve the recorded paths and reports EVERY worktree as
   prunable — pruning there would deregister live worktrees, including other sessions'.

2. RE-INSTALL DEPENDENCIES AND ENV FILES in the relocated worktrees if the move did not carry
   node_modules (it is gitignored, so a remove-and-re-add loses it). Each worktree needs platform +
   platform-mcp deps and the env files (.env.rag, platform/.env, platform/.env.local). Verify
   `npm run typecheck` passes in platform-mcp in all three. Do these in parallel.

3. LAND THE OUTSTANDING DOC CHANGES AS ONE PR.
   The working-tree versions of the charter and kickoff prompts supersede commit 1da2a039 on
   docs/elevation-campaign-worktree-preflight. Reconcile so main ends up with the NEWER content —
   either update that branch with the current working-tree files, or open a fresh branch and close
   the stale one. Include the untracked PREFLIGHT_WORKTREE_PROMPT_v1_0.md. Merge via the PR +
   auto-merge path. Confirm main contains charter §16 (CLEANUP) and the `.worktrees/` layout when
   done, and that no stale docs branch is left open.

4. CLEAN UP ABANDONED PLAN ARTIFACTS. These are all superseded by later revisions:
   a. The three pre-run CLONES: ~/madhav-alpha, ~/madhav-beta, ~/madhav-gamma. Superseded by
      worktrees. Report their combined size, then delete them — they contain campaign docs and would
      badly confuse a future session that stumbled into one.
   b. The now-empty sibling worktree directories at ~/../Apps/madhav-wt-* if the relocation left
      anything behind.
   c. In 00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/: move
      PREFLIGHT_PROMPT_v1_0.md (the CLONE-based pre-flight, superseded by the worktree edition) into
      archive/ alongside the v1.0/v2.0 charters, KICKOFF_PROMPTS_v2_0.md and elev_setup.sh that are
      already there. After this, the live folder should contain exactly four files: the charter
      v2.1, KICKOFF_PROMPTS_v2_1.md, PREFLIGHT_WORKTREE_PROMPT_v1_0.md, this file, and archive/.
   d. Prune the stale worktree registrations left by past sessions — but ONLY genuinely dead ones.
      Verify each path really does not exist on disk before pruning it. Do NOT remove
      ../madhav-wave-vidhi-purnata or anything under .claude/worktrees/ unless you have confirmed on
      disk that it is gone. A previous pre-flight deleted 7 tracked files with an over-broad rm -rf
      and had to restore them — that is the standing warning for this step.
   e. Reverse-citation before ANY deletion: grep the live codebase and the campaign docs for
      references to each thing you are about to remove. A still-referenced target becomes
      keep-or-repoint, and you say so.

5. VERIFY THE RUNWAY. For each of the three worktrees: correct branch, clean status, typecheck
   passes, env files present, all six required reading files present (CLAUDECODE_BRIEF.md, charter
   v2.1, KICKOFF_PROMPTS_v2_1.md, the ELEVATION_REGISTER, CLAUDE.md, CURRENT_STATE_v1_0.md),
   `git push --dry-run origin <its branch>` succeeds. Root checkout still on main, clean, at the new
   merged head. `gh` authenticated. gc.auto still 0. ~/elev-v2-shared subdirs intact — do NOT touch
   anything inside it; it is the run's evidence store.
   Update ~/elev-v2-shared/PREFLIGHT.json with the new worktree paths and what you cleaned.

6. CONCURRENCY PROOF, since the worktrees moved. From two different worktrees at the same time, run
   `git fetch --no-write-fetch-head` and a trivial commit/amend cycle on their own branches. Confirm
   no index.lock contention and neither HEAD moved unexpectedly. Report what you actually observed —
   the whole three-stream design rests on this.

THEN REPORT BACK in this shape, nothing longer:

  GO / NO-GO  (one word, then one sentence)

  RELOCATED        - worktree paths now in use
  MERGED           - what landed on main, and the PR number
  CLEANED          - what you deleted, with sizes; and what you deliberately did NOT touch
  CONCURRENCY      - what you observed in step 6
  WHAT WILL BITE   - anything a stream will hit at 2am that you could not fix
  ADDENDUM         - any correction the three kickoff prompts need. If none, say "none needed".

If something is genuinely broken and unfixable, say NO-GO rather than papering over it.
```

## After it finishes

- **GO** → Session 1 on the project root, paste the **α** prompt. Wait for "PHASE 0 COMPLETE".
- Then Sessions 2 and 3, paste **β** and **γ**.
- End-of-run cleanup is charter **§16**, executed by α at Phase 5 and Verifier-gated (§16.6).
