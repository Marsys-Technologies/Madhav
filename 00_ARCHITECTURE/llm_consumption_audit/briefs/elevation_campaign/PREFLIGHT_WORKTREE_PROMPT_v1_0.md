---
artifact: PREFLIGHT_WORKTREE_PROMPT (Elevation Campaign v2.1 — Mode 2, worktree conversion)
version: 1.0
status: CURRENT
purpose: >
  Converts the runway from three clones to three in-repo git worktrees under .worktrees/, and
  lands the charter
  amendment. Run AFTER the original pre-flight (which already established branch protection, the
  green CI baseline and prod health — those findings stand and are not re-derived here).
run_from: /Users/Dev/Vibe-Coding/Apps/Madhav (project root)
---

# Worktree pre-flight — paste into Claude Code from the PROJECT ROOT

```
You are the PRE-FLIGHT engineer for the Elevation Campaign v2.1, converting the runway from three
separate clones to three GIT WORKTREES inside this repo under .worktrees/. The three stream sessions
launch immediately after you finish, each one a Claude Code extension window opened on this project
root.

YOUR JOB IS PREPARATION ONLY. Do NOT start the campaign, do NOT begin any lane work, do NOT touch
application code, do NOT deploy or rebuild anything.

Established already by the earlier pre-flight — treat as given, do not re-derive:
- main is branch-protected: 4 required checks, enforce_admins:true, direct push REJECTED (GH006).
  PR + `gh pr merge --auto --squash` works and is the only merge path.
- CI baseline on main is ALL GREEN; detail in ~/elev-v2-shared/PREEXISTING_CI_STATE.md.
- Prod is healthy; both canonical charts present; the three known-broken surfaces confirmed unchanged.
- ~/elev-v2-shared/{locks,implementations,heartbeat,proxy,contracts} exists.
- Repo is clean on main at bed662c4 (PR #763 merged). Git is 2.34.1.

Do all of the following.

1. LAND THE CHARTER AMENDMENT.
   00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/ELEVATION_CAMPAIGN_CHARTER_v2_1.md
   and KICKOFF_PROMPTS_v2_1.md in that same directory have been updated on disk (M2.0 converted from
   clones to worktrees; M2.2 gains a `worktree` lock plus concurrent-worktree git hygiene; new M2.3b
   records the PR-only merge path; M2.4 notes Phase 0 verifies rather than creates). A new file
   PREFLIGHT_WORKTREE_PROMPT_v1_0.md is also present. Verify they are on disk, then commit and merge
   them to main via the PR + auto-merge path. Do NOT attempt a direct push.

2. WORKTREE HYGIENE FIRST.
   `git worktree list` shows many stale/prunable entries from past sessions (.claude/worktrees/agent-*
   and others). Run `git worktree prune` and report how many were cleared. Do NOT delete the live
   sibling ../madhav-wave-vidhi-purnata unless it is prunable — check before acting.
   Set `git config gc.auto 0` (a background auto-gc under three concurrent writers can lock refs).
   Record the previous value so it can be restored at close.

3. CREATE THE THREE BRANCHES AND THREE WORKTREES, IN-REPO UNDER .worktrees/.
   Branches off current main: elev/alpha, elev/beta, elev/gamma. Push all three to origin.
   Worktrees at:
     /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/alpha   -> elev/alpha
     /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/beta    -> elev/beta
     /Users/Dev/Vibe-Coding/Apps/Madhav/.worktrees/gamma   -> elev/gamma
   IN-REPO, not sibling directories: the streams run as Claude Code extension windows opened on this
   project folder, and an IDE-hosted session may scope file access to the opened workspace — a
   sibling worktree would sit outside it and every operation would be blocked or prompt for
   permission, which is fatal unattended. `.worktrees/` is already the repo's reserved, gitignored
   path (.gitignore section "Git worktrees"), so it is inside the workspace AND invisible to git
   status and to every .gitignore-respecting search.
   CONFIRM `.worktrees/` is genuinely matched by .gitignore before creating anything — if for any
   reason it is not, add it and include that in the amendment PR.
   Verify each worktree is on its intended branch and that the ROOT checkout is still on main,
   untouched.

4. DEPENDENCIES IN EACH WORKTREE.
   node_modules is gitignored, so a fresh worktree has none and the first typecheck or test in each
   stream would fail. Install platform and platform-mcp deps in all three worktrees, plus the root
   .venv convention if the sidecar needs it — in parallel where you can. You MAY copy node_modules
   from the existing ~/madhav-{alpha,beta,gamma} clones if that is faster, but only if you then
   verify it actually works (`npm run typecheck` in platform-mcp must pass in each worktree); if
   verification fails, fall back to a clean install. Confirm typecheck passes in all three.

5. ENV FILES INTO EACH WORKTREE.
   Copy every env file the root has (.env.rag, platform/.env, platform/.env.local — check for
   others). Confirm presence in each worktree, not just that cp returned zero.
   Note: platform-mcp has no populated .env anywhere (only .env.example) — pre-existing, expected.

6. THE OLD CLONES.
   ~/madhav-alpha, ~/madhav-beta and ~/madhav-gamma are now superseded. Do NOT delete them — just
   report their location and total size so I can remove them myself later. Leaving stale checkouts
   that contain campaign docs is a real confusion risk for a future session, so note it clearly, but
   destructive cleanup is not your call tonight.

7. CONCURRENCY PROOF — actually test it, do not assume.
   With all three worktrees present, demonstrate that concurrent git operations are safe: from two
   different worktrees simultaneously, run a `git fetch --no-write-fetch-head` and a trivial
   commit-and-amend cycle on their own branches, and confirm no index.lock or ref contention and
   that neither worktree's HEAD moved unexpectedly. Report what you observed. If anything contends,
   say so plainly — this is the assumption the whole three-stream design rests on.

8. FINAL VERIFICATION.
   For each of the three worktrees confirm: correct branch; clean status; all six required reading
   files present and readable (CLAUDECODE_BRIEF.md, the charter v2.1, KICKOFF_PROMPTS_v2_1.md, the
   ELEVATION_REGISTER, CLAUDE.md, 00_ARCHITECTURE/CURRENT_STATE_v1_0.md); typecheck passes; env files
   present; `git push --dry-run origin <its branch>` succeeds; and `gh` is available and authenticated
   (every stream needs it for the PR merge path).
   Update ~/elev-v2-shared/PREFLIGHT.json with: worktree paths and branches, deps_installed per
   worktree, gc_auto_previous_value, prunes_performed, concurrency_proof result, old_clone_paths.

THEN REPORT BACK in this shape, and nothing longer:

  GO / NO-GO  (one word, then one sentence of why)

  WHAT I DID          - terse bullets
  CONCURRENCY PROOF   - what you actually observed in step 7
  WHAT WILL BITE      - anything a stream will hit at 2am that you could not fix
  ADDENDUM            - any correction the three kickoff prompts need before I paste them.
                        If none, say "none needed" and nothing else.

If something is genuinely broken and unfixable, say NO-GO rather than papering over it.
```

## After it finishes

- **GO** → Terminal 1: open on the project root, paste the **α** prompt. Wait for "PHASE 0 COMPLETE".
- Then Terminals 2 and 3 on the project root, paste **β** and **γ**.
- All three prompts are in `KICKOFF_PROMPTS_v2_1.md` (worktree edition).
