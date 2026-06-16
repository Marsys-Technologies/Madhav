---
artifact: WORKTREE_SPLIT_BRIEF_v1_0.md
canonical_id: WORKTREE_SPLIT_ANALYSIS_FROM_CHAT_V2
version: 1.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session — analysis stream)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
purpose: >
  One-shot migration. Move the analysis-stream branch
  (analysis/backend-data-pipeline-perf-audit) out of the shared main worktree
  into a dedicated git worktree at /Users/Dev/Vibe-Coding/Apps/Madhav-analysis.
  Leave the Chat V2 stream's state in the main worktree (/Users/Dev/Vibe-Coding/Apps/Madhav)
  exactly as it was — modified files, untracked files, stashes, branches all
  intact. After this brief executes successfully, the two streams are
  physically isolated and cross-contamination becomes impossible.
end_state:
  - /Users/Dev/Vibe-Coding/Apps/Madhav-analysis is a new git worktree on branch analysis/backend-data-pipeline-perf-audit, clean
  - /Users/Dev/Vibe-Coding/Apps/Madhav (main worktree) is on a Chat V2 fix branch (fix/chat-v2-r5/A1-chat-column-offset) with its dirty file restored and all Chat V2 untracked files intact
  - The analysis Cowork session reconfigures its selected folder to the new worktree path (manual UI step by the native)
  - The Chat V2 Cowork session is unaffected — it sees the same /Madhav working tree as before
---

# Worktree Split — Analysis Stream Migration

## §A — Pre-flight diagnostic (run FIRST, no state changes)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

echo "============ Where we are ============"
echo "Current branch:"
git branch --show-current
echo ""

echo "Modified + untracked files:"
git status --short
echo ""

echo "============ Existing worktrees ============"
git worktree list
echo ""

echo "============ Existing stashes ============"
git stash list
echo ""

echo "============ Recent branches (last 10) ============"
git for-each-ref --sort=-committerdate --count=10 --format='%(refname:short) | %(committerdate:short)' refs/heads/
echo ""

echo "============ Disk check — does target path exist? ============"
ls -la /Users/Dev/Vibe-Coding/Apps/Madhav-analysis 2>&1 | head -3
echo ""

echo "============ Decision tree ============"
echo "If the target path /Users/Dev/Vibe-Coding/Apps/Madhav-analysis EXISTS,"
echo "STOP and report. Do not create the worktree on top of an existing directory."
```

**Hard stops:**
- If `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis` already exists → STOP and report. Native will decide whether to clean up or pick a different path.
- If `git worktree list` already shows a worktree at that path → STOP (something is half-done from a previous attempt).
- If there are uncommitted changes you DON'T recognize as either Chat V2 WIP or expected untracked files → STOP and report.

## §B — Identify what is "Chat V2 WIP" vs "analysis-stream commitments"

Expected state (based on conversation history 2026-05-17):
- **Main worktree branch:** `analysis/backend-data-pipeline-perf-audit`
- **Modified file:** `platform/src/components/consume/ConsumeChatV2.tsx` (Chat V2 stream's A1 sidebar-offset fix; belongs on `fix/chat-v2-r5/A1-chat-column-offset`)
- **Untracked files (all Chat V2 stream artifacts that stay in the main worktree):**
  - `00_ARCHITECTURE/CHAT_V2_ROUND_5_PLAN_v1_0.md`
  - `platform/tests/components/chat-v2/`
  - `platform/tests/e2e/chat-v2/r5/`
  - `test-results/` (gitignored)

If `git status` from §A shows ANYTHING that doesn't match this expected list, STOP and report. Do not improvise.

## §C — Move Chat V2 WIP back to its proper branch

This is conditional. Only run §C.1 if `ConsumeChatV2.tsx` is currently modified on the analysis branch.

### C.1 — Stash the modification with a clear label

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git stash push \
  -m "chat-v2-r5-A1-column-offset WIP — stashed during worktree split 2026-05-17" \
  platform/src/components/consume/ConsumeChatV2.tsx

# Verify
git stash list | head -3
git status --short
```

Working tree should now be clean of modifications (untracked files remain — they're fine).

### C.2 — Switch main worktree to the Chat V2 branch where the change belongs

```bash
git checkout fix/chat-v2-r5/A1-chat-column-offset

# Verify
git branch --show-current
git status --short
```

The branch switch should succeed cleanly since the working tree has no modifications (only untracked files, which don't block checkouts).

### C.3 — Pop the stash back onto the Chat V2 branch

```bash
git stash pop stash@{0}
# This restores ConsumeChatV2.tsx as modified on its proper branch.

# Verify
git status --short
# Expected: modified ConsumeChatV2.tsx + the Chat V2 untracked files
```

**Note:** there may be OTHER stashes from earlier in the day (the previous "chat-v2/A1-chat-column-offset WIP" stash from when the analysis stream first did this dance). Leave those alone — they're the Chat V2 stream's to manage. `git stash list` should still show them; only `stash@{0}` (the freshly-pushed one) gets popped.

## §D — Create the new worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git worktree add \
  /Users/Dev/Vibe-Coding/Apps/Madhav-analysis \
  analysis/backend-data-pipeline-perf-audit

# Verify
git worktree list
# Expected output (two entries):
#   /Users/Dev/Vibe-Coding/Apps/Madhav          <SHA> [fix/chat-v2-r5/A1-chat-column-offset]
#   /Users/Dev/Vibe-Coding/Apps/Madhav-analysis <SHA> [analysis/backend-data-pipeline-perf-audit]
```

## §E — Verify the new worktree contents

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis

echo "============ New worktree state ============"
git branch --show-current
git status --short
git log --oneline -5
echo ""

echo "============ Verify analysis-stream artifacts are present ============"
ls -la 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md
ls -la 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
ls -la 00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md
ls -la 00_ARCHITECTURE/briefs/BRANCH_HYGIENE_RECOVERY_BRIEF_v1_0.md
ls -la 00_ARCHITECTURE/briefs/SLA_PROBE_BRIEF_v2_0.md
ls -la platform/src/lib/router/retrieval_capability_spec.ts
ls -la platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts
ls -la platform/scripts/sla_probe_planner_blind_tools.ts
ls -la platform/tests/eval/planner_blind_fix_smoke.ts

echo ""
echo "============ Verify Chat V2 untracked files are NOT present ============"
ls -la 00_ARCHITECTURE/CHAT_V2_ROUND_5_PLAN_v1_0.md 2>&1 | head -2
# Expected: "No such file or directory" — Chat V2 untracked files are physically
# located in the main worktree only. The new worktree starts clean.
ls -la platform/tests/components/chat-v2/ 2>&1 | head -2
ls -la platform/tests/e2e/chat-v2/r5/ 2>&1 | head -2
```

All analysis-stream artifacts should be present (they're committed on the branch). All Chat V2 untracked files should be absent (they're physically in the other worktree).

## §F — node_modules + .next setup in the new worktree

`node_modules/`, `.next/`, `test-results/` are NOT shared between worktrees. The new worktree needs its own dependency install before any test or build runs:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform
npm install
# Expected: ~2-3 minute install. node_modules created here, independent of /Madhav.

# Verify
ls -la node_modules/ | head -3
```

## §G — Final state verification

```bash
echo "============ Both worktrees ============"
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree list
echo ""

echo "============ Main worktree state ============"
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git branch --show-current
git status --short
# Expected: on Chat V2 branch (fix/chat-v2-r5/A1-chat-column-offset), modified
# ConsumeChatV2.tsx + Chat V2 untracked files present
echo ""

echo "============ Analysis worktree state ============"
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git branch --show-current
git status --short
# Expected: on analysis/backend-data-pipeline-perf-audit, clean (no modifications)
# Untracked: maybe node_modules-related cruft if any; should be minimal.
```

## §H — Report back

Deliver to native in this exact Markdown shape:

```markdown
# Worktree Split — Report

## Pre-flight (§A)
- Starting branch: <branch>
- Starting modified files: <list>
- Starting untracked files: <list>
- Existing worktrees: <list>
- Existing stashes: <count>

## Chat V2 WIP restoration (§C)
- Stash created: <yes/no — if yes, label>
- Switched main worktree to: fix/chat-v2-r5/A1-chat-column-offset
- Stash popped on Chat V2 branch: <yes/no>
- Chat V2 working tree restored: <yes/no>

## New worktree creation (§D)
- Path: /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
- Branch checked out: analysis/backend-data-pipeline-perf-audit
- `git worktree list` output: <paste>

## Worktree contents (§E)
- All 9 analysis-stream artifacts present: <yes/no>
- Chat V2 untracked files absent from new worktree: <yes/no>

## Dependencies (§F)
- npm install in new worktree: <yes/no, duration>
- node_modules created: <yes/no>

## Final state (§G)
- Main worktree: branch=<X>, working tree=<clean/dirty as expected>
- Analysis worktree: branch=analysis/..., working tree=clean

## Anything anomalous
[any deviations, conflicts, decisions deferred to native]

## Next step for native (NOT for executor)
Update Cowork's selected folder for the analysis-stream conversation to
/Users/Dev/Vibe-Coding/Apps/Madhav-analysis. This is a one-time UI action
in the Cowork app and is not something the executor performs. After
this is done, the next message in the analysis conversation operates
on the new worktree.
```

## §I — Hard rules

- Diagnose §A BEFORE any state-changing operation.
- Do NOT delete or move any Chat V2 untracked files (`CHAT_V2_ROUND_5_PLAN_v1_0.md`, `platform/tests/components/chat-v2/`, `platform/tests/e2e/chat-v2/r5/`, `test-results/`). They live in the main worktree forever as far as we're concerned; the Chat V2 stream will commit them when ready.
- Do NOT pop any stash other than the one created in §C.1. Earlier stashes (from previous worktree-split dances) belong to the Chat V2 stream and they manage them.
- Do NOT commit anything during this migration. No commits, no pushes.
- Do NOT force-delete or `--prune` worktrees without explicit native approval.
- If §A's diagnostic reveals state that doesn't match the expected baseline in §B, STOP and report. Do not improvise.
- If `git worktree add` fails (e.g., the branch is checked out elsewhere, or the target path exists), STOP and report.

---

*End WORKTREE_SPLIT_BRIEF_v1_0.md. After successful execution, the analysis stream operates from /Users/Dev/Vibe-Coding/Apps/Madhav-analysis. The Chat V2 stream is unaffected.*
