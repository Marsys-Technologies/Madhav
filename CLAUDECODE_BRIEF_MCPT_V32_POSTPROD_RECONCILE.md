---
artifact: CLAUDECODE_BRIEF_MCPT_V32_POSTPROD_RECONCILE.md
session: MCPT-V32-POSTPROD-RECONCILE
workstream: MCPT v3.2 Quality Tightening (post-prod governance debt)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (/Users/Dev/Vibe-Coding/Apps/Madhav)
plan: Plans/MCPT_V32_OPTIMIZATION_PLAN_v3.md
estimated_duration: 20-40 minutes (depends on cherry-pick complexity)
---

# Claude Code Brief — MCPT v3.2 Post-Prod Reconcile

## Context

The MCPT v3.2 close-out surfaced three issues:

1. **Main is missing commits that prod has.** The conductor cherry-picked specific commits to `main` instead of merging the feature branch. `evals/mcp-routing/` (and possibly other files) exist on the `mcpt-v32-prod` tag but not on `main`. This violates "main reflects prod" and makes the harness fragile (next eval requires another tag checkout).
2. **`eval-results/` is gitignored.** The R3 results were force-added with `git add -f`. Native has decided to track `eval-results/` going forward.
3. **2 of 30 routing-eval prompts were misrouted.** Need diagnosis: ambiguous prompt? wrong gold? description-tuning opportunity?

This brief addresses all three in a single PR.

## Preconditions

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD       # main
git status --porcelain                # empty
test -n "$(git tag --list mcpt-v32-prod)" && echo "tag ok" || echo "STOP: tag missing"
git fetch --tags origin
git pull --ff-only origin main
```

If anything fails, STOP and surface.

---

## Task A — Identify the Gap Between `main` and `mcpt-v32-prod`

### A.1 — Diff the histories

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "=== Commits on mcpt-v32-prod but NOT on main ==="
git log mcpt-v32-prod --not main --oneline

echo ""
echo "=== Commits on main but NOT on mcpt-v32-prod ==="
git log main --not mcpt-v32-prod --oneline

echo ""
echo "=== File-level diff ==="
git diff --stat main..mcpt-v32-prod

echo ""
echo "=== Files only on mcpt-v32-prod ==="
git diff --name-only --diff-filter=A main..mcpt-v32-prod

echo ""
echo "=== Files only on main (unique to main) ==="
git diff --name-only --diff-filter=D main..mcpt-v32-prod
```

Write the output to `/tmp/mcpt-v32-gap.txt` for reference.

### A.2 — Choose an approach based on what you find

**Decision tree:**

| Finding | Approach |
|---|---|
| Main has zero unique commits; tag has N commits not on main | **Fast-forward merge**: `git merge mcpt-v32-prod` (creates a clean merge or FF) |
| Main has 1-3 unique commits; tag has a small number not on main | **Merge** with merge commit (preserves both histories) |
| Main has unique commits that conflict with tag commits | **STOP and surface** to native. Conflict resolution needs human judgment |
| Main and tag have diverged significantly (>10 unique commits each) | **STOP and surface**. This is bigger than a routine reconcile |

For the most likely case (tag ahead, main unchanged or trivially ahead), use:

```bash
git checkout main
git merge mcpt-v32-prod --no-ff -m "merge: reconcile main with mcpt-v32-prod tag

The conductor cherry-picked select commits to main during the v3.2 sweep,
leaving main missing files (notably evals/mcp-routing/) that exist on the
prod tag. This merge brings main into parity with what's deployed.

Files added by this merge (per git diff main..mcpt-v32-prod):
<paste the file list from A.1 here>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

DO NOT push yet — we'll batch with Tasks B and C.

### A.3 — Sanity check

```bash
# After the merge, verify main == tag in file content
git diff main..mcpt-v32-prod --stat
# Expect: empty output (no diffs)
```

If diffs remain, the merge didn't cleanly reconcile — STOP and surface.

---

## Task B — Untrack `eval-results/` from `.gitignore`

### B.1 — Edit .gitignore

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Find the eval-results entry
grep -n "eval-results" .gitignore

# Remove it (use sed for in-place edit; verify after)
sed -i.bak '/^eval-results\/\?$/d' .gitignore
rm .gitignore.bak

grep -n "eval-results" .gitignore && echo "STOP: still in gitignore" || echo "removed"
```

### B.2 — Confirm previously force-added files are recognized normally

```bash
# These should NOT appear as untracked or modified after the gitignore change
git status eval-results/
# Expect: no changes
```

### B.3 — Stage the .gitignore change

```bash
git add .gitignore
```

DO NOT commit yet — batch with Tasks A and C.

---

## Task C — Diagnose the 2 Misrouted Prompts

### C.1 — Read the result JSON

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
ls eval-results/routing_eval_postprod_*.json
# Find the most recent

# Use jq to extract the failures
RESULT_FILE=$(ls -t eval-results/routing_eval_postprod_*.json | head -1)
jq '[.results[] | select(.passed == false)]' $RESULT_FILE > /tmp/misrouted_prompts.json
cat /tmp/misrouted_prompts.json
```

The exact field names may differ — adapt to the actual JSON shape. Aim to extract for each failure:
- `prompt` (the input)
- `gold_first_tool` (what should have been called)
- `acceptable_alternatives` (other ok answers)
- `actual_first_tool` (what the model called instead)
- `reasoning` (if the harness captured it)

### C.2 — Classify each failure

For each of the 2 failures, write a one-line classification:

| Class | Meaning | Action |
|---|---|---|
| AMBIGUOUS | The prompt could reasonably be answered by multiple tools | Add the chosen tool to `acceptable_alternatives` in `evals/mcp-routing/prompts.json` |
| GOLD_WRONG | The `gold_first_tool` in the eval data is itself wrong | Fix the gold in `evals/mcp-routing/prompts.json` |
| DESC_TUNE | The chosen tool's description plausibly misled the model | Note as a follow-up; do NOT fix descriptions in this brief |
| MODEL_ERROR | The model just made a clear mistake despite good descriptions | Accept; note as a follow-up |

Write the classifications + the prompt details into `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md` with this structure:

```markdown
---
artifact: MCPT_V32_ROUTING_EVAL_FAILURES.md
created: 2026-05-23
context: 2 of 30 prompts misrouted in the v3.2 prod routing eval (28/30 PASS)
---

# Misrouted Prompts — Diagnosis

## Failure 1
- Prompt: "<text>"
- Gold tool: <tool>
- Acceptable: <list>
- Actual: <tool>
- Classification: <CLASS>
- Recommendation: <one line>

## Failure 2
(same shape)

## Summary
N AMBIGUOUS, N GOLD_WRONG, N DESC_TUNE, N MODEL_ERROR.

Recommended action:
- (if AMBIGUOUS or GOLD_WRONG): update prompts.json now in this PR.
- (if DESC_TUNE or MODEL_ERROR): defer to a follow-up; document only.
```

### C.3 — Apply AMBIGUOUS / GOLD_WRONG fixes only

If any classifications are AMBIGUOUS or GOLD_WRONG, edit `evals/mcp-routing/prompts.json` accordingly:
- For AMBIGUOUS: add the chosen tool to that prompt's `acceptable_alternatives` array.
- For GOLD_WRONG: change `gold_first_tool` to the correct value.

DO NOT touch any tool description in `platform-mcp/src/tools/` — that's out of scope.

### C.4 — Stage the changes

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md
git add evals/mcp-routing/prompts.json  # if you made any AMBIGUOUS/GOLD_WRONG fixes
```

---

## Final — Commit and Open PR

### F.1 — Single batched commit for Tasks B and C

Task A's merge commit is already in place from A.2. Now add a single follow-up commit for Tasks B and C:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git commit -m "chore(mcpt-v32): track eval-results + diagnose 2 routing-eval failures

- .gitignore: remove eval-results/ entry; the directory is now tracked
  in repo so future eval runs do not require git add -f.
- Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md: diagnosis of the 2 of 30
  prompts that misrouted in the v3.2 prod routing eval.
- evals/mcp-routing/prompts.json: <describe any fixes applied or 'no fixes
  applied — both failures classified as DESC_TUNE/MODEL_ERROR follow-ups'>.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### F.2 — Open the PR

```bash
git push origin main

# Wait — main is the target. We want a PR, not a direct push.
# Actually, since we committed directly to main locally, we need a different approach.
```

**Correction — use a feature branch for the reconcile work:**

Re-run Tasks A, B, C on a feature branch instead of directly on main. Restart with:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull --ff-only origin main
git checkout -b feature/mcpt-v32-postprod-reconcile
# Re-run Task A.2 (the merge), Task B.1-3, Task C.1-4 on this branch
# Then commit as in F.1 above, but on the feature branch
git push -u origin feature/mcpt-v32-postprod-reconcile

gh pr create \
  --base main \
  --head feature/mcpt-v32-postprod-reconcile \
  --title "[MCPT-v3.2] post-prod reconcile: main parity + eval-results tracking + routing-eval diagnosis" \
  --body-file PR_BODY.md
```

`PR_BODY.md` content:

```markdown
## Scope

Three post-prod close-out items consolidated:

1. **Main reconciliation** — merge mcpt-v32-prod tag into main to bring evals/mcp-routing/ and any other tag-only files into main. Fixes the divergence created by the conductor's selective cherry-picks during v3.2.
2. **eval-results/ tracked** — removed from .gitignore so future eval runs commit cleanly without git add -f.
3. **Routing-eval failure diagnosis** — 2 of 30 prompts misrouted; diagnosis at Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md. <Applied N fixes / No code fixes; deferred>.

## Files touched

- (from merge): <paste git diff --name-only main..mcpt-v32-prod output here>
- .gitignore (1 line removed)
- Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md (new)
- evals/mcp-routing/prompts.json (if any AMBIGUOUS/GOLD_WRONG fixes)

## Acceptance

- [ ] git diff main..mcpt-v32-prod returns empty after this PR merges.
- [ ] eval-results/ is tracked (next eval run does not need git add -f).
- [ ] All 2 misrouted prompts are diagnosed and classified.
- [ ] Tests still pass: cd platform-mcp && npm test (expect 257/257).

## Risks

- Merge from the tag may include changes that diverge from main's own minor drift (if any). The merge commit preserves history of both lines.
- AMBIGUOUS/GOLD_WRONG fixes (if applied) inflate the eval pass rate slightly — re-running the eval after this PR should yield 29-30 of 30 instead of 28 of 30. That is the intended effect.

## Rollback

- git revert <merge-commit-sha> on main to reverse the reconcile.
- git revert <chore-commit-sha> to put eval-results/ back in .gitignore.

## Mirror impact

None. No CLAUDE.md or .geminirules changes.
```

Then:

```bash
gh pr ready
gh pr checks
# Wait for CI green
```

DO NOT auto-merge. The PR is for human review by the native.

---

## Acceptance — done when

- [ ] Feature branch `feature/mcpt-v32-postprod-reconcile` pushed.
- [ ] PR open against main with the body above.
- [ ] CI green on the PR.
- [ ] `Plans/MCPT_V32_ROUTING_EVAL_FAILURES.md` committed with classifications.
- [ ] Native has been notified with the report below.

## Final report to Cowork (the native)

Report:
1. **Gap size**: number of commits on tag-not-on-main; number on main-not-on-tag; files affected.
2. **Approach taken**: merge / cherry-pick / other; with rationale.
3. **PR URL**.
4. **CI status**.
5. **Misrouted prompts**: 2 classifications + whether any fixes applied in this PR.
6. **Anomalies**: any conflicts, surprises, or things the native should look at before approving.

## Failure modes

| Failure | Action |
|---|---|
| Main has divergent commits that conflict with tag | STOP. Surface conflict files to native. Do not resolve without explicit guidance |
| Tag commits include must_not_touch paths | STOP. Surface to native. This shouldn't happen for v3.2 work but is theoretically possible |
| jq missing on the system | Use python or node to parse the JSON instead |
| eval-results/routing_eval_postprod_*.json absent | STOP. The previous brief should have committed it; if missing, the prior session has a bug |
| CI fails on the PR | Read the failure, fix forward if trivial, escalate if not |

## Out of scope

- Re-running R3 (the result stands).
- Tuning any tool description (separate brief if classifications surface a real DESC_TUNE).
- Touching CLAUDE.md / .geminirules.
- Modifying anything under 01_FACTS_LAYER, 025_HOLISTIC_SYNTHESIS, 04_REMEDIAL_CODEX, 06_LEARNING_LAYER.
- Closing or re-opening issue #154 (already closed).

## Cost

Free — pure git + file operations + gh API calls. No LLM tokens, no GCP charges.
