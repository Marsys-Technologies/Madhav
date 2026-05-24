---
artifact: CLAUDECODE_BRIEF_MCPT_V32_FINAL_WRAPUP.md
session: MCPT-V32-FINAL-WRAPUP
workstream: MCPT v3.2 Quality Tightening (final wrap-up + worktree cleanup)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (/Users/Dev/Vibe-Coding/Apps/Madhav) + Madhav-mcpt-v32 (cleanup target)
estimated_duration: 20-40 minutes (depends on what's in the worktree)
---

# Claude Code Brief — MCPT v3.2 Final Wrap-Up

## Scope Principle (BINDING)

This session does three things, in strict scope:

1. **Commit any remaining MCPT v3.2 artifacts** on main (the 2 untracked v3.2 brief MDs, possibly the 4 evals/mcp-routing/results_*.json scratch).
2. **Investigate and clean the Madhav-mcpt-v32 worktree** — characterize the 150+ uncommitted changes, decide per-file what's MCPT v3.2 vs other-stream vs scratch, handle accordingly, then remove the worktree.
3. **Push, verify deploy state, report.**

**Explicit must-NOT-touch list:**
- Any other worktree (MadhavR11A/B/CDE/F/FBound/G, MadhavICR, marsys-m6-prospective, .claude/worktrees/agent-*) — leave them prunable or active as-is.
- `platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts` in main — R11 stream artifact.
- Any file or commit outside MCPT v3.2 scope inside the Madhav-mcpt-v32 worktree — copy/move to a side note for the relevant stream's owner; do NOT commit it to MCPT v3.2 or to main from this session.
- `CLAUDE.md`, `.geminirules`, anything under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`.

When in doubt about whether a file is MCPT v3.2 scope, the answer is: **don't touch it**, write it to a manifest at `/tmp/madhav-mcpt-v32-leftovers.md` for the native to decide later.

---

## Phase 1 — Commit Remaining MCPT v3.2 Briefs on Main

### 1.1 — Preflight

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD                # main
git pull --ff-only origin main
git status --porcelain
```

Expect 7 untracked items (or fewer if any were committed since the prior session):
- `CLAUDECODE_BRIEF_MCPT_V32_HAIKU_TIER_NOTE.md`
- `CLAUDECODE_BRIEF_MCPT_V32_R3_VERIFICATION.md`
- `CLAUDECODE_BRIEF_MCPT_V32_FINAL_WRAPUP.md` (this file)
- `evals/mcp-routing/results_10f84df6.json`
- `evals/mcp-routing/results_4cdf5a77.json`
- `evals/mcp-routing/results_b9f372a3.json`
- `evals/mcp-routing/results_d802639d.json`
- `platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts`

### 1.2 — Stage the 3 MCPT v3.2 briefs

```bash
git add CLAUDECODE_BRIEF_MCPT_V32_HAIKU_TIER_NOTE.md
git add CLAUDECODE_BRIEF_MCPT_V32_R3_VERIFICATION.md
git add CLAUDECODE_BRIEF_MCPT_V32_FINAL_WRAPUP.md   # this brief

git diff --cached --name-only
# Expected: exactly those 3 files.
```

### 1.3 — Decide on the 4 evals/mcp-routing/results_*.json files

These look like per-run outputs from the routing-eval runner. Check whether the runner deliberately writes these to disk per run, and whether they belong tracked or gitignored:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Quick look — what's the file shape?
head -20 evals/mcp-routing/results_b9f372a3.json

# Is the runner configured to write these as artifacts or scratch?
grep -rn "results_" evals/mcp-routing/runner.ts platform-mcp/test/bench/ 2>/dev/null | head
```

**Decision rule:**
- If they're **per-run scratch** (the runner writes to a content-hashed filename and we don't need history): add `evals/mcp-routing/results_*.json` to `.gitignore` and do NOT commit them.
- If they're **deliberate artifact outputs** that the eval workflow expects to find later: commit them.

Recommend **gitignore** unless there's evidence the runner depends on these files persisting. If gitignored, also add `evals/mcp-routing/results_*.json` line to `.gitignore`. Stage `.gitignore` if so.

### 1.4 — Commit + push (Phase 1)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Final staging check
git diff --cached --name-only
# Expected (max): 3 brief MDs + optionally .gitignore. NOTHING ELSE.

git commit -m "docs(mcpt-v32): final wrap-up — remaining briefs + evals scratch gitignore

Three Cowork-authored briefs that missed the prior final-merge commit:
- CLAUDECODE_BRIEF_MCPT_V32_HAIKU_TIER_NOTE.md
- CLAUDECODE_BRIEF_MCPT_V32_R3_VERIFICATION.md
- CLAUDECODE_BRIEF_MCPT_V32_FINAL_WRAPUP.md

<If .gitignore was updated:>
.gitignore: suppress evals/mcp-routing/results_*.json per-run scratch.
</If>

Scope discipline preserved: PROBE_anthropic_tools_forwarding.test.ts
(R11 stream) and other-stream working-tree items are untouched.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main
```

---

## Phase 2 — Investigate Madhav-mcpt-v32 Worktree

### 2.1 — Switch to the worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32
ls -la                                          # verify accessible
git rev-parse --abbrev-ref HEAD                # feature/mcpt-v32-quality-tightening
git log --oneline -5
```

If the path doesn't exist (already removed by hand), skip Phase 2 entirely and proceed to Phase 3.

### 2.2 — Characterize the 150+ changes

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32

# How many?
git status --porcelain | wc -l

# What types?
git status --porcelain | awk '{print $1}' | sort | uniq -c | sort -rn

# Modified files (committed-tracked but locally edited)
git status --porcelain | awk '/^.M/ {print $2}' > /tmp/wt-modified.txt
wc -l /tmp/wt-modified.txt

# Untracked files
git status --porcelain | awk '/^\?\?/ {print $2}' > /tmp/wt-untracked.txt
wc -l /tmp/wt-untracked.txt

# How does this worktree's HEAD compare to main?
git log feature/mcpt-v32-quality-tightening --not main --oneline | head -20
git log main --not feature/mcpt-v32-quality-tightening --oneline | head -20
```

### 2.3 — Classify each modified/untracked path

For each path in `/tmp/wt-modified.txt` and `/tmp/wt-untracked.txt`, classify it:

| Class | Examples | Action |
|---|---|---|
| **MCPT v3.2 — already-on-main** | A file you've already merged via PR #155 / final commits | Discard local changes: `git checkout -- <path>` |
| **MCPT v3.2 — genuinely new** | A v3.2-scope change not yet on main | Stage, commit, push to main directly (small docs/config) OR open follow-up PR (if substantive code) |
| **Conductor scratch** | `.conductor-state.json`, `.conductor-instructions.md`, `.conductor-approve-prod`, etc. | Discard. These are operational, not artifacts |
| **Other stream artifact** | Anything matching `platform/tests/providers/anthropic/PROBE_*`, R11 chat UI files, etc. | LEAVE UNTOUCHED. Write to `/tmp/madhav-mcpt-v32-leftovers.md` with stream owner and path |
| **Generic scratch** | `node_modules/`, build outputs, log files | Discard or rely on .gitignore |

For efficiency, use directory-level heuristics on the lists:
- `node_modules/`, `dist/`, `.next/`, `*.log`, `coverage/`, `playwright-report/` → scratch, discard
- `.conductor-*` → conductor scratch, discard
- `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/` etc. → must-not-touch — write to manifest
- `platform-mcp/**`, `platform/src/lib/mcp/**`, `platform/src/app/api/mcp/**`, `evals/mcp-routing/**`, `Plans/MCPT_V32_*.md`, `MCPT_V32_*.md`, `CLAUDECODE_BRIEF_MCPT_V32_*.md` → MCPT v3.2 candidates

### 2.4 — Build the action manifest

Write `/tmp/madhav-mcpt-v32-leftovers.md` with this structure:

```markdown
# Madhav-mcpt-v32 Worktree Cleanup Manifest

Date: 2026-05-23
Worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32 at <SHA>
Total changes: <N modified + M untracked>

## Files to DISCARD (already on main, or scratch)

<list>

## Files to COMMIT to main (genuinely new MCPT v3.2 work)

<list with classification and recommended commit grouping>

## Files for OTHER STREAMS (must not touch, surfaced for stream owners)

<list grouped by stream: R11.x, ICR, M6, sidebar, etc.>

## Decision points needing native input

<list any files where classification was ambiguous>
```

If the manifest's "Files for OTHER STREAMS" section is non-empty, STOP here and surface the manifest to the native. Do not delete the worktree until they confirm those files have homes.

### 2.5 — Apply discards

For everything classified as DISCARD:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32

# Modified files — restore to HEAD state
xargs -a /tmp/discard-modified.txt git checkout --

# Untracked files — remove
xargs -a /tmp/discard-untracked.txt rm -f
# For directories: xargs -a /tmp/discard-dirs.txt rm -rf

git status --porcelain | wc -l
# Should be dramatically smaller — only the COMMIT-to-main and OTHER-STREAM items remain
```

### 2.6 — Commit any genuinely-new MCPT v3.2 work

If Phase 2.3 identified any "genuinely new MCPT v3.2" files, commit them in a separate session-aware commit on this branch, push the branch, and consider whether they need to land on main:

- If trivial (docs / config): cherry-pick to main directly with `git cherry-pick <sha>` from main worktree.
- If substantive: open a small follow-up PR from this branch.

**If everything from 2.3 was DISCARD or OTHER STREAM, skip this step — nothing to commit.**

---

## Phase 3 — Remove the Worktree

Only do this after Phase 2 has either (a) confirmed everything is DISCARD/OTHER-STREAM and the other-stream items have been documented in the manifest, OR (b) successfully committed genuinely-new MCPT v3.2 work.

### 3.1 — Verify worktree is clean of un-handled changes

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-mcpt-v32
git status --porcelain
# Acceptable: empty, OR only files in the OTHER-STREAM manifest that we agreed to leave
```

If there are any DISCARD items still present, re-run Phase 2.5. If there's MCPT v3.2 work uncommitted, STOP and surface.

### 3.2 — Remove the worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git worktree remove ../Madhav-mcpt-v32
# If git refuses because of remaining changes, force only after confirming
# everything was DISCARD or copied to manifest:
#   git worktree remove --force ../Madhav-mcpt-v32

git worktree prune
git worktree list
# Madhav-mcpt-v32 should no longer appear
```

### 3.3 — Decide on the branch

`feature/mcpt-v32-quality-tightening` exists on origin. Options:

- **Keep on origin** (recommended) — branch is a historical record of the conductor's work; the merge commit on main preserves history, but having the branch makes it easy to inspect specific commits.
- **Delete from origin** — `git push origin --delete feature/mcpt-v32-quality-tightening`. Only if you're confident the history isn't needed; the merge commit on main + the `mcpt-v32-prod` tag are sufficient references.

Default: **keep**. Note in the report which you chose.

---

## Phase 4 — Final Verification

### 4.1 — Main state

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status                                      # should show clean OR only PROBE + non-discarded items
git log --oneline -5                            # latest is the Phase 1 commit
git ls-remote origin refs/heads/main            # confirm pushed
```

### 4.2 — Deploy state

```bash
gcloud run services describe amjis-mcp --region asia-south1 \
  --format='value(status.latestReadyRevisionName,status.url)'
# Expected: amjis-mcp-00011-9zv (or newer if CI re-deployed on the Phase 1 commit)

# Check the latest deploy workflow run
gh run list --workflow=deploy.yml --limit=3
```

If a deploy auto-triggered on the Phase 1 commit and succeeded, a new revision will be visible. Docs-only changes are no-op for the MCP server but the revision number increments. That's expected and harmless.

If deploy didn't trigger (because docs-only paths are filtered): no action needed.

### 4.3 — Worktree state

```bash
git worktree list
# Should NOT contain Madhav-mcpt-v32 anymore.
# Should still contain all other worktrees (untouched).
```

---

## Acceptance — done when

- [ ] Main has 3 new untracked v3.2 briefs committed.
- [ ] (Optional) `.gitignore` updated for `evals/mcp-routing/results_*.json` if those were classified as scratch.
- [ ] Main pushed; in sync with origin.
- [ ] Madhav-mcpt-v32 worktree removed (or, if not removable due to genuine other-stream files in it, the manifest is written and surfaced to native).
- [ ] No other worktree was touched. `git worktree list` still shows all the MadhavR11*, MadhavICR, marsys-m6-prospective, and .claude/worktrees/agent-* entries.
- [ ] PROBE_anthropic_tools_forwarding.test.ts on main still untracked, untouched.
- [ ] Manifest `/tmp/madhav-mcpt-v32-leftovers.md` written and shared with native if non-trivial.

## Final report to Cowork (the native)

1. **Phase 1 commit SHA** (the briefs/gitignore commit).
2. **Worktree state**: removed cleanly / removed with --force / kept (and why).
3. **Manifest contents**: paste the `/tmp/madhav-mcpt-v32-leftovers.md` if it has any non-trivial entries. Especially:
   - Other-stream files surfaced (so the stream owners can be told).
   - Decision points the native should resolve.
4. **Deploy state**: whether the Phase 1 commit triggered a re-deploy; new revision name if so.
5. **Branch fate**: kept `feature/mcpt-v32-quality-tightening` on origin or deleted it.
6. **Anomalies**: anything surprising in the worktree (unexpected commits ahead of main, files outside MCPT v3.2 scope, etc.).

## Failure modes

| Failure | Action |
|---|---|
| Madhav-mcpt-v32 path doesn't exist | Skip Phase 2, proceed to Phase 3.2 (`git worktree remove --force` may still be needed to clean the metadata) |
| Worktree has genuine MCPT v3.2 commits not on main | STOP. Surface the commit list. We may need a follow-up cherry-pick before removing the worktree |
| Worktree has substantial other-stream uncommitted work | STOP. Surface to native via manifest. DO NOT discard other-stream work without explicit go-ahead |
| `git worktree remove` fails | Try `git worktree remove --force` ONLY if Phase 2 confirmed nothing of value remains |
| Push to main rejected | Pull first, re-push. If rejected for protected-branch reasons, open PR for the docs commit |
| Deploy re-triggered and failed | Surface gcloud build/run logs. Previous revision still serves; this is not urgent |

## Out of scope

- Any other worktree's cleanup (MadhavR11*, etc. — their respective streams).
- Running R3 again.
- Tuning any tool description.
- Modifying CLAUDE.md, .geminirules, or anything under the must-not-touch globs.
- Pruning the `feature/mcpt-v32-quality-tightening` branch from origin without explicit go-ahead (default: keep).
- Touching the locked `.claude/worktrees/agent-*` worktrees (those are active Claude Code agent sessions; locking is intentional).
