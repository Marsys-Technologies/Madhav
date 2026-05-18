---
artifact: BRANCH_HYGIENE_RECOVERY_BRIEF_v1_0.md
canonical_id: BRANCH_HYGIENE_RECOVERY_PLANNER_BLIND
version: 1.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session — analysis/backend-data-pipeline-perf-audit branch)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
purpose: >
  One-shot recovery to ensure (a) planner-blind fix da140c8 lives on main and
  is deployed to production, (b) analysis/backend-data-pipeline-perf-audit
  branch is synced with main, (c) Chat V2 parity branches are not touched
  by this conversation, (d) two-branch isolation policy is recorded so future
  Cowork sessions on each stream stay segregated.
end_state:
  - main has da140c8 (planner-blind fix) deployed via Cloud Run
  - analysis/backend-data-pipeline-perf-audit branch is up to date with main
  - fix/chat-v2-parity-c-ext/F-W4W8-panel-trace is left alone (different conversation owns it)
  - going-forward branch policy is recorded in memory so this contamination doesn't recur
---

# Branch Hygiene Recovery — Planner-Blind Fix da140c8

## §A — Two-stream policy (the going-forward rule)

MARSYS-JIS currently has two concurrent Cowork conversations operating on
two separate branches:

| Conversation | Branch | Scope |
|---|---|---|
| **This conversation** (audit / data assets / pipeline / perf) | `analysis/backend-data-pipeline-perf-audit` | Backend audit, data-asset inventory, query-pipeline fixes (planner-blind tools and successors), retrieval SLA, metrics. **Owns all work merged from here.** |
| **Chat V2 parity conversation** | `fix/chat-v2-parity-c-ext/*` and friends | Frontend Chat V2 chrome parity, sidebar fixes, W3/W4/W5/W8/W10 case repairs. **This conversation must not modify any commit on these branches.** |

**Hard rule** for this conversation's executor sessions going forward:
- ALWAYS start by `git checkout analysis/backend-data-pipeline-perf-audit`
  unless explicitly working on a release to main.
- NEVER commit to `fix/chat-v2-parity-*` or `chore/chat-v2-*` branches.
- NEVER rebase or rewrite history on those branches.
- If a fix is somehow on the wrong branch (like da140c8), follow §C's
  cherry-pick-to-main recovery, NOT a rebase-on-the-original-branch.

---

## §B — Diagnose: where does `da140c8` actually live?

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Where is da140c8?
echo "============ Branches containing da140c8 ============"
git branch -a --contains da140c8

echo ""
echo "============ Commit details ============"
git show --stat --no-color da140c8 | head -40

echo ""
echo "============ Is da140c8 in main's history? ============"
if git merge-base --is-ancestor da140c8 origin/main 2>/dev/null; then
  echo "YES — da140c8 is already an ancestor of main. No recovery needed; skip §C."
else
  echo "NO — da140c8 is NOT on main. Proceed with §C cherry-pick recovery."
fi
```

**Interpretation:**

| Output | What it means | Next step |
|---|---|---|
| `is already an ancestor of main` | da140c8 is on main, my diagnosis was wrong | Skip §C, go to §D (sync the audit branch) |
| `is NOT on main` + only Chat V2 branches contain it | The expected scenario — commit was made on a Chat V2 branch by accident | Execute §C cherry-pick |
| `is NOT on main` + no branches contain it | Hash is wrong or commit was rebased away | STOP and report — needs investigation |

---

## §C — Recovery: cherry-pick `da140c8` to main (only if §B says it's missing)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# 1. Make sure working tree is clean.
git status
# Acceptance: "nothing to commit, working tree clean" (untracked test-results/ ok)
# If anything is modified, STOP and report.

# 2. Switch to main and update.
git checkout main
git pull origin main

# 3. Cherry-pick the planner-blind fix.
git cherry-pick da140c8

# Expected: clean cherry-pick, new commit on main with the same content as da140c8
# (the new commit will have a different SHA — that's fine; the change is what matters).
#
# If you see conflicts: STOP. Conflicts here would indicate main has diverged
# from the Chat V2 branch in a way I didn't anticipate. Run:
#   git cherry-pick --abort
# and report the conflicting files. Do NOT resolve conflicts unilaterally.

# 4. Verify the cherry-pick landed.
git log --oneline -5
git show --stat HEAD | head -10

# 5. Push main — this triggers Cloud Run deploy via .github/workflows/deploy.yml.
git push origin main

# 6. Watch the deploy. Wait for it to complete before proceeding to §D.
gh run watch --workflow=deploy.yml || gh run list --workflow=deploy.yml --limit=1
```

**Hard stops in §C:**
- Conflict during cherry-pick → abort + report (don't resolve)
- Push fails → report (don't force-push without explicit approval)
- Deploy fails → report status; don't roll back without instruction

---

## §D — Sync the audit branch with the updated main

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Switch to the audit branch.
git checkout analysis/backend-data-pipeline-perf-audit

# Since this branch has zero unique commits (just created from main), fast-forward
# is safe — no rebase or merge commit needed. If --ff-only fails it means the
# branch has diverged somehow and you should STOP and report.
git merge main --ff-only

# Verify.
git log --oneline -5
# Expected: the new cherry-pick commit AND cce852a AND the prior 3 Chat V2 commits.

# Push the updated audit branch upstream.
git push origin analysis/backend-data-pipeline-perf-audit
```

---

## §E — Leave Chat V2 branches alone

**Explicit DO-NOT:**

- Do NOT switch to `fix/chat-v2-parity-c-ext/F-W4W8-panel-trace` or any
  `chore/chat-v2-*` / `fix/chat-v2-*` branch in this session.
- Do NOT attempt to remove `da140c8` from the Chat V2 branch via interactive
  rebase. That branch belongs to a different Cowork conversation; its
  hygiene is their concern. The eventual merge of Chat V2 to main will see
  da140c8 already there and de-duplicate the changes automatically.

If a future Chat V2 merge encounters conflicts on planner-blind files
(retrieval_capability_spec.ts, planner_golden_set.json, etc.), that's a
signal for the Chat V2 conversation to rebase their branch on the new main.
That's their decision to make, not this conversation's.

---

## §F — Verify end state

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "============ Final state ============"
echo ""
echo "Current branch:"
git branch --show-current
# Expected: analysis/backend-data-pipeline-perf-audit

echo ""
echo "Working tree:"
git status --short
# Expected: empty (or only untracked test-results/)

echo ""
echo "Last 3 commits on this branch:"
git log --oneline -3

echo ""
echo "Last 3 commits on main:"
git log main --oneline -3

echo ""
echo "Is da140c8 (or its cherry-picked equivalent) on main?"
if git log main --oneline | grep -qE "(wire 4 planner-blind tools|F\.PIPE\.1)"; then
  echo "✅ YES — planner-blind fix is on main."
else
  echo "❌ NO — recovery incomplete. STOP and report."
fi

echo ""
echo "Is the audit branch tracking origin?"
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
# Expected: origin/analysis/backend-data-pipeline-perf-audit
```

---

## §G — Report back

Deliver to Abhisek in this exact Markdown shape:

```markdown
# Branch Hygiene Recovery — Report

## Diagnosis (§B)
- da140c8 found on branches: <list>
- da140c8 on main before recovery: <yes/no>

## Recovery actions taken
- Cherry-picked da140c8 to main: <yes/no — if yes, new commit SHA>
- Pushed main to origin: <yes/no>
- Cloud Run deploy: <revision id + duration, or "not run">
- Synced analysis/backend-data-pipeline-perf-audit with main: <yes/no>
- Pushed audit branch: <yes/no>

## End state
- main HEAD: <SHA + subject>
- analysis branch HEAD: <SHA + subject>
- Working tree: <clean / dirty>

## Anything anomalous
[any deviations, conflicts encountered, decisions deferred to native]
```

---

## §H — Hard rules

- Diagnose §B before any state-changing operation in §C/§D.
- Do not run §C if §B says da140c8 is already on main.
- Do not modify Chat V2 branches.
- Do not force-push anything without explicit approval.
- Do not run `git rebase --interactive` against any commit older than HEAD~3 without approval.
- If anything unexpected happens, STOP and report — don't improvise.

---

*End BRANCH_HYGIENE_RECOVERY_BRIEF_v1_0.md. After successful execution, this brief is a one-shot — archive intent goes to `00_ARCHITECTURE/briefs/` per ROOT_FILE_POLICY. The going-forward two-stream policy lives in memory.*
