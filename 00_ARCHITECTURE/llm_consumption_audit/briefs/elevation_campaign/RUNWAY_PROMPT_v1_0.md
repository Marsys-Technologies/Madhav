---
artifact: RUNWAY_PROMPT (Elevation Campaign v2.1) — reconcile · cleanup · campaign Phase 0
version: 1.0
status: CURRENT
purpose: >
  The single serial session that precedes the campaign. Reconciles the worktree layout change
  (sibling → in-repo .worktrees/), lands the outstanding charter amendment, removes every artifact
  abandoned by the plan revisions, and then performs the WHOLE of campaign Phase 0 — so that all
  three streams can launch simultaneously afterwards, and so the baseline and the graded test assets
  are authored by a non-participant rather than by one of the competing streams.
run_from: /Users/Dev/Vibe-Coding/Apps/Madhav (project root)
---

# Runway session — paste into Claude Code from the PROJECT ROOT

```
You are the RUNWAY session for the Elevation Campaign v2.1. You do three things: reconcile the
plan revisions, clean up what they abandoned, and then perform the WHOLE of campaign Phase 0.

THE THREE STREAM SESSIONS ARE ALREADY RUNNING RIGHT NOW, IN PARALLEL WITH YOU. They were pasted at
the same moment you were. They are polling for ~/elev-v2-shared/PHASE0_COMPLETE.flag and touching
NOTHING until you write it — no cd, no reads, no git. Their ceiling is 3 HOURS. So:
- Work briskly; every minute you take is a minute three sessions sit idle.
- RETRY each step up to 3 times before giving up. A step you abandon too early costs the whole run.
- If something is genuinely unrecoverable, write ~/elev-v2-shared/PHASE0_FAILED.flag immediately so
  the three streams abort cleanly instead of burning their full 3-hour ceiling.
- Write PHASE0_COMPLETE.flag LAST and only when every field of its manifest is genuinely true. The
  streams validate every field and abort if any is wrong — an optimistic flag is worse than none.
THE HUMAN IS ASLEEP AND WILL NOT ANSWER ANYTHING. Make every call yourself and log it.

You are NOT a stream and you are not competing in the campaign. That is deliberate and load-bearing:
you author the baseline and the frozen test assets that will GRADE the three streams, and a
participant cannot credibly author its own grader (charter M2.4).

PREPARATION ONLY. Do NOT begin any lane work, do NOT fix any EL item, do NOT deploy or rebuild
anything beyond what Phase 0 requires.

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

7. NOW PERFORM CAMPAIGN PHASE 0 (charter §7.1 + M2.4). Read charter §5 first — you need every
   lane's verification recipe for the baseline. In this order:
   a. SNAPSHOT: create and push git tag elev-v2-run-start, AND take a real DB snapshot. Record both
      IDs. The streams will refuse to start without them in your manifest, by design — this is the
      restore point for the whole night.
   b. BASELINE: capture the shared Verifier baseline against LIVE PRODUCTION — every §5 lane recipe
      plus the §0.2 depth probes (plan_retrieval + intent_classify on "How is my wealth?", the
      graha_portrait Venus starvation probe, bodha_mechanisms_get, argala, ref_planet_position_get),
      on BOTH canonical charts (482012f1-710e-4a25-994a-93821f5871aa and 1c826d5a). Raw payloads to
      ledgers/ELEVATION_V2_BASELINE.md. Record its sha256. THIS IS IRREPLACEABLE — once the streams
      fix prod it can never be recaptured, and every before/after claim in the morning report
      depends on it.
   c. CONTRACT SPECS: author and FREEZE C1 (budget_kb request param + paging response fields),
      C2 (per-category receipt shape), C3 (schema-map output shape), C6 (mechanisms row shape + the
      returns-200 guarantee), C8 (registry handler signature + post-trim envelope shape incl. the
      four receipt states, pivoted-row shape, immune honesty-field set). These are INTERFACE SPECS,
      not implementations — you are authoring them rather than α precisely so the interface everyone
      depends on is not defined at one participant's convenience. Ground each in the current code so
      it is feasible. Record each in ~/elev-v2-shared/contracts/CONTRACT_STATUS.md as FROZEN with
      path + sha. Enter C4/C5 (β, deadline T0+3h) and C7 (γ, T0+4h) as DRAFT with owner and deadline
      — those are rulings requiring investigation and you must NOT pre-author them.
   d. SCHEMA-MAP GENERATOR: build the C3 generator (mechanical: every fact_category × fact_subjects
      × fact_keys, paginated, plus the concept-alias table seeded from the Phase-0.7 census). γ's
      TCI is generated from its output and may NEVER be stubbed, so this must genuinely work.
   e. FROZEN TEST ASSETS — author these as a NON-PARTICIPANT and commit them read-only:
      - The SEALED EVALUATOR HARNESS (charter §2 Ω-Verification): a fresh sub-agent given the MCP
        tools and a fixed system prompt containing NO charter text, NO EL vocabulary, NO concept
        names, and no mention of dossier or Lane Ω. One user turn. Full transcript captured. Plus
        the mechanical grader: score the transcript against a frozen list of required concept_ids
        with a numeric pass threshold, substance required (a passing mention does not count).
      - The 60-ITEM ROUTING SUITE (§2 Ω4): ≥4 per domain across narrow/deep, INCLUDING ≥15 items
        labelled NARROW — the suite must be able to fail a degenerate "always deepdive" classifier.
      - The DARK-CORPUS REPLAY SET (§2 Ω7): ≥20 questions per flagship domain spanning naive,
        narrow and expert phrasings.
      - OVERFLOW_QUEUE.md (charter §7.6).
   f. Merge everything from (c)–(e) to main via the PR + auto-merge path.
   g. LAST, write ~/elev-v2-shared/PHASE0_COMPLETE.flag containing the full JSON manifest specified
      in charter M2.4 (run_start_tag, db_snapshot_id, baseline_ledger_path + sha256, contracts with
      shas, sealed_harness_path, routing_suite_path, dark_replay_set_path, overflow_queue_path,
      branch_heads). If ANY step above failed, write PHASE0_FAILED.flag instead so the streams fail
      fast rather than starting on a broken runway.

THEN REPORT BACK in this shape, nothing longer:

  GO / NO-GO  (one word, then one sentence)

  RELOCATED        - worktree paths now in use
  MERGED           - what landed on main, and the PR number(s)
  CLEANED          - what you deleted, with sizes; and what you deliberately did NOT touch
  CONCURRENCY      - what you observed in step 6
  PHASE 0          - snapshot IDs · baseline path + probe count · contracts frozen · test assets
                     frozen (with the routing suite's narrow/deep split) · flag written
  WHAT WILL BITE   - anything a stream will hit at 2am that you could not fix
  ADDENDUM         - any correction the three kickoff prompts need. If none, say "none needed".

If something is genuinely broken and unfixable, say NO-GO rather than papering over it.
```

## After it finishes

Nothing to do — the three streams pick themselves up the moment the flag lands. Your GO/NO-GO
report is for the native to read in the morning alongside the run report, not a gate anyone waits on.
- End-of-run cleanup is charter **§16**, executed by α at Phase 5 and Verifier-gated (§16.6).
