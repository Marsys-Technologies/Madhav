---
artifact: CLAUDECODE_BRIEF_MCPT_V32_FINAL_MERGE.md
session: MCPT-V32-FINAL-MERGE
workstream: MCPT v3.2 Quality Tightening (final close-out)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (/Users/Dev/Vibe-Coding/Apps/Madhav)
target_branch: feature/mcpt-v32-postprod-reconcile (already pushed; this brief adds commits then merges)
target_pr: https://github.com/amonty84/Madhav/pull/155
estimated_duration: 15-20 minutes
---

# Claude Code Brief — MCPT v3.2 Final Merge

## Scope Principle (READ FIRST)

This brief touches **only MCPT v3.2 files**. Other untracked or modified files in the working tree belong to other streams (R11 multi-provider parity, Ganga mopup, sidebar work, etc.) and MUST NOT be touched, committed, or otherwise affected by this session.

**Explicit must-not-touch list:**
- `platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts` — R11 stream artifact
- `eval-results/answer_eval_*.log`, `eval-results/runner_gemini_*.log`, `eval-results/runner_mopup_*.log` — Ganga/Mopup arc artifacts (pre-existing files from May 10-11)
- Any uncommitted modification to `platform/src/components/consume/*` or `platform/src/components/chat/*` — chat UI stream
- Anything under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/` — governance must-not-touch

If you encounter any of the above in `git status`, leave them alone. They are not in scope.

## Context

PR #155 (`feature/mcpt-v32-postprod-reconcile` → `main`) is open. It contains the main↔tag reconcile merge and `chore: track eval-results + diagnose 2 routing-eval failures`. Three small additions remain before merge:

1. **4 CLAUDECODE_BRIEF MDs** authored in Cowork during the v3.2 sweep — they're MCPT v3.2 artifacts that belong on main as governance records.
2. **`chart_summary` description tune** — closes the second of the 2 misrouted prompts (DESC_TUNE classification from `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md`). After this lands, re-running R3 should yield 30/30.
3. **`.gitignore` tightening** — `eval-results/*.log` to suppress legacy log noise while keeping JSON results trackable. Refines the v3.2 eval-results untrack.

Then merge PR #155, push main, trigger deploy.

## Preconditions

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD                    # main
git fetch --tags origin && git pull --ff-only origin main
test -n "$(gh pr view 155 --json number --jq .number 2>/dev/null)" || echo "STOP: PR 155 missing"
gh pr view 155 --json state --jq .state            # OPEN
```

If anything fails, STOP and report.

## Task A — Add the 4 MCPT v3.2 brief MDs to PR #155

### A.1 — Switch to the PR branch

```bash
git fetch origin feature/mcpt-v32-postprod-reconcile
git checkout feature/mcpt-v32-postprod-reconcile
git pull --ff-only origin feature/mcpt-v32-postprod-reconcile
```

### A.2 — Stage ONLY the 4 MCPT v3.2 brief files

```bash
# Exhaustive list — stage these and ONLY these:
git add CLAUDECODE_BRIEF_MCPT_V32_PROD_APPROVAL.md
git add CLAUDECODE_BRIEF_MCPT_V32_R3_POSTPROD_ROUTING_EVAL.md
git add CLAUDECODE_BRIEF_MCPT_V32_CLOSEOUT.md
git add CLAUDECODE_BRIEF_MCPT_V32_POSTPROD_RECONCILE.md
git add CLAUDECODE_BRIEF_MCPT_V32_FINAL_MERGE.md   # this file

# Verify staging — must be exactly 5 files, all CLAUDECODE_BRIEF_MCPT_V32_*
git diff --cached --name-only
# Expected output: the 5 brief files above. NOTHING ELSE.
# If anything else appears, unstage it with `git restore --staged <file>` and investigate.
```

DO NOT commit yet — bundle with Tasks B and C.

## Task B — `chart_summary` DESC_TUNE

### B.1 — Locate the tool file

```bash
ls -la platform-mcp/src/tools/chart_summary.ts
```

If absent, STOP — this is a Phase 4 file and should exist on the reconcile branch.

### B.2 — Update the description

Edit `platform-mcp/src/tools/chart_summary.ts`. Find the `description` argument or `buildToolDescription({ baseDescription: ... })` call. Modify the `baseDescription` (or equivalent) so it includes explicit mention of divisional charts including navamsa/D9.

Suggested phrasing (adapt to the existing tone of the file):

> "FIRST CALL when interpreting any chart end-to-end. Returns 30-60 canonical facts in one round-trip — birth metadata, planet placements, house occupancy, yogas, arudhas, current dasha, sensitive points — across requested divisional charts (defaults to D1 + D9 navamsa + D10 dasamsa). Prefer over query_chart_facts unless you know the exact single category you need."

Key phrase to ensure is present: **"navamsa"** AND **"D9"** (both terms — the eval prompt that misrouted asked for "my D9 chart" without using the word "navamsa", and there are dialects of Jyotish that prefer "navamsa" so future prompts may use either).

### B.3 — Stage

```bash
git add platform-mcp/src/tools/chart_summary.ts
```

### B.4 — Update `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md`

Add a closing note to the existing failures doc:

```markdown
## Update — 2026-05-23 (post-merge follow-up)

The DESC_TUNE failure for `chart_summary_d9_request` was addressed in commit `<sha-of-this-commit>` by adding explicit "navamsa" and "D9" mentions to the `chart_summary` tool description. Re-running R3 against post-merge prod should yield 30/30 (29/30 was the ceiling before this change, after the AMBIGUOUS fix from this PR's earlier commit).
```

```bash
git add Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md
```

## Task C — `.gitignore` tightening for `eval-results/*.log`

### C.1 — Add the log-suppression pattern

```bash
cat .gitignore | tail -20
# Look for any existing eval-results pattern (should be absent after the prior reconcile PR removed it)

# Add a tighter, log-only pattern
printf '\n# MCPT v3.2: track eval-results/ JSON, suppress legacy log noise\neval-results/*.log\n' >> .gitignore

# Verify it landed correctly
tail -5 .gitignore
```

### C.2 — Confirm the effect

```bash
# These should now disappear from `git status` (they were untracked before)
git status eval-results/ 2>&1 | grep -c "\.log" || echo "no log entries in eval-results status"
```

### C.3 — Stage

```bash
git add .gitignore
```

## Final — Single commit and PR update

### F.1 — Final staging verification

```bash
git diff --cached --name-only
# EXPECTED EXACTLY:
#   .gitignore
#   CLAUDECODE_BRIEF_MCPT_V32_CLOSEOUT.md
#   CLAUDECODE_BRIEF_MCPT_V32_FINAL_MERGE.md
#   CLAUDECODE_BRIEF_MCPT_V32_POSTPROD_RECONCILE.md
#   CLAUDECODE_BRIEF_MCPT_V32_PROD_APPROVAL.md
#   CLAUDECODE_BRIEF_MCPT_V32_R3_POSTPROD_ROUTING_EVAL.md
#   Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md
#   platform-mcp/src/tools/chart_summary.ts
#
# If the list contains anything outside this set, STOP and unstage.
# Common contamination to watch for:
#   - PROBE_anthropic_tools_forwarding.test.ts → unstage
#   - Any platform/src/components/consume/* or chat/* → unstage
#   - Any eval-results/*.log → unstage (the gitignore should suppress, but verify)
```

### F.2 — Commit

```bash
git commit -m "chore(mcpt-v32): final close-out — briefs, chart_summary DESC_TUNE, log gitignore

Three MCPT-v3.2-scoped additions to bring this PR to a clean close:

1. Cowork session briefs (5 files) — governance record of the v3.2 sweep:
   - PROD_APPROVAL: prod gate handoff
   - R3_POSTPROD_ROUTING_EVAL: live routing eval brief
   - CLOSEOUT: combined R3 + description-changes + issue close
   - POSTPROD_RECONCILE: main↔tag reconcile (this PR's origin)
   - FINAL_MERGE: this brief
2. chart_summary description tuned to mention navamsa/D9 explicitly
   (closes DESC_TUNE failure from Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md).
   Re-running R3 after merge should yield 30/30 (was 29/30 after the
   AMBIGUOUS fix earlier in this PR).
3. .gitignore: suppress eval-results/*.log noise while keeping JSON
   results trackable. Refines the v3.2 eval-results untrack.

Scope discipline: this commit touches ONLY MCPT v3.2 files. Other
untracked items in the working tree (PROBE_anthropic_tools_forwarding,
legacy answer_eval/runner_gemini logs) belong to other streams (R11
multi-provider parity, Ganga mopup) and are explicitly out of scope.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### F.3 — Push

```bash
git push origin feature/mcpt-v32-postprod-reconcile
```

### F.4 — Update PR body

```bash
gh pr edit 155 --body-file - <<'EOF'
## Scope

Final close-out of MCPT v3.2. Combines:

1. **Main reconciliation** (original PR scope) — merge mcpt-v32-prod tag into main; bring evals/mcp-routing/ + 49 other files into parity.
2. **eval-results/ tracked** — removed from .gitignore so future eval runs commit cleanly.
3. **Routing-eval failure diagnosis** — 2 of 30 prompts misrouted (now 1 of 30 fixed via prompts.json; 1 of 30 fixed via chart_summary DESC_TUNE in the final commit).
4. **Cowork governance briefs** — 5 CLAUDECODE_BRIEF_MCPT_V32_*.md files documenting the full v3.2 sweep.
5. **.gitignore refinement** — `eval-results/*.log` suppresses legacy log noise while keeping JSON results trackable.

## Files touched (MCPT v3.2 only)

See `git diff --name-only main` on this branch. Scope is strictly v3.2.

Explicit out-of-scope (left untouched in working tree):
- `platform/tests/providers/anthropic/PROBE_*` — R11 stream
- Legacy `eval-results/*.log` from Ganga mopup arc (May 10-11)
- Any chat UI / sidebar / Dockerfile changes — separate streams

## Acceptance

- [ ] `git diff main..mcpt-v32-prod` returns empty after merge (parity).
- [ ] `evals/mcp-routing/` exists on main.
- [ ] `chart_summary` description includes "navamsa" + "D9".
- [ ] All 5 Cowork briefs present at repo root.
- [ ] CI passes (pre-existing failures noted).
- [ ] Re-running R3 against post-merge prod should yield 30/30.

## Risks

- Re-running R3 to verify 30/30 is a follow-up task, not part of this PR.
- No code-path changes; only a description string change in chart_summary (no runtime risk).

## Rollback

- `git revert <merge-commit-sha>` reverses the reconcile.
- `git revert <final-commit-sha>` reverses the briefs/DESC_TUNE/gitignore.

## Mirror impact

None. No CLAUDE.md or .geminirules changes in this PR.
EOF
```

### F.5 — Wait for CI

```bash
gh pr checks 155 --watch
# Wait for all checks. Expected pre-existing failures:
#   - Coverage Gate (COV-S7): retrieval_capability_spec.test.ts — known per KNOWN_PRE_EXISTING_FAILURES.md
#   - Bench + Accuracy Harness gh-comment step: workflow permissions issue, not a test failure
# Required to pass:
#   - TypeScript
#   - Planner Regression
#   - ICR PR Gate
#   - Unit Tests (was pending in prior run)
```

### F.6 — Merge

When CI is green (or only the documented pre-existing failures remain):

```bash
gh pr merge 155 --merge --delete-branch
# Use --merge (not --squash) so the merge commit from reconcile preserves its semantics.
```

### F.7 — Verify post-merge state

```bash
git checkout main
git pull --ff-only origin main
git log --oneline -5
# Should show the merge commit at HEAD
git diff main..mcpt-v32-prod --stat
# Expected: empty (parity)
```

### F.8 — Deploy trigger

The merge to main should auto-trigger `.github/workflows/deploy.yml`. Verify:

```bash
gh workflow list
gh run list --workflow=deploy.yml --limit=3
gh run watch
```

If the deploy workflow doesn't auto-trigger on the MCP server path, manually invoke:

```bash
gh workflow run deploy.yml --ref main
```

Verify post-deploy:
```bash
gcloud run services describe amjis-mcp --region asia-south1 \
  --format='value(status.latestReadyRevisionName,status.url)'
# Should show a new revision built from the post-merge main commit
```

## Acceptance — done when

- [ ] Branch `feature/mcpt-v32-postprod-reconcile` merged to main.
- [ ] Branch deleted on origin.
- [ ] `git diff main..mcpt-v32-prod` returns empty.
- [ ] `evals/mcp-routing/` exists on main.
- [ ] `chart_summary.ts` description contains "navamsa" AND "D9".
- [ ] `.gitignore` contains `eval-results/*.log`.
- [ ] All 5 `CLAUDECODE_BRIEF_MCPT_V32_*.md` files committed on main.
- [ ] Deploy workflow ran on main; new Cloud Run revision is live.
- [ ] Native has been notified with the report below.

## Final report to Cowork (the native)

Report:
1. **Final commit SHA** added to the PR.
2. **PR #155 merge SHA** (the merge commit on main).
3. **Cloud Run revision name + URL** after deploy.
4. **CI status** at merge time (which checks passed, which were documented pre-existing).
5. **Any contamination warnings** — files that almost got staged that shouldn't have, and confirmation they were unstaged.
6. **Confirmation** that PROBE test, legacy logs, and other-stream artifacts are still in the working tree, untouched, untracked.

## Failure modes

| Failure | Action |
|---|---|
| Staging picks up a file outside the expected 8 | STOP. Unstage with `git restore --staged <file>`. Investigate why it was modified by a prior step |
| `chart_summary.ts` already mentions navamsa/D9 | Skip Task B.2; log "DESC_TUNE already in place" and proceed |
| CI fails with a new (not pre-existing) failure | STOP. Surface the failure to native. Do not merge |
| Deploy workflow doesn't auto-trigger after merge | Manually trigger per F.8 |
| Cloud Run deploy fails | STOP. Surface gcloud error. Previous revision still serves traffic — no immediate damage |

## Out of scope (do NOT do these in this session)

- Re-running R3 against the new revision (follow-up brief if needed).
- Touching any chat UI, sidebar, or Dockerfile work.
- Adopting or rejecting `PROBE_anthropic_tools_forwarding.test.ts` (R11 stream).
- Committing or deleting `eval-results/*.log` legacy files (Ganga/Mopup stream).
- Re-tagging `mcpt-v32-prod` (cosmetic only).
- Modifying CLAUDE.md, .geminirules, or anything under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`.

## Cost

Free — git + gh + gcloud read-only verifications. Deploy is a normal CI/CD trigger, no extra cost.
