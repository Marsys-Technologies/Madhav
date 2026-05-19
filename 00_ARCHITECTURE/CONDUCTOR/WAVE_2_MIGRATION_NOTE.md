# WAVE 2 MIGRATION NOTE

**Target audience:** Future-you (or future-Cowork) at the moment Wave 1 closes.
**Purpose:** Remind you exactly how to get the Conductor onto main before opening Wave 2.

Authored: 2026-05-19, session CONDUCTOR-S0.

---

## §1 — Why this note exists

The Conductor was built on `feature/phase-4c-panchang` for Wave 1 convenience:
one worktree, one branch, no IDE-window switching during Phase 4C development.

Wave 2 needs it on main so M5-A, Phase 4B, and Phase 4D sessions running on their
own worktrees can consume it. The Conductor must land on main BEFORE Wave 2's first
session runs.

Additionally, keeping Conductor on `feature/phase-4c-panchang` forever creates a
review problem: the Phase 4C close PR would be muddied by orchestrator infrastructure,
making it hard to review the Panchang application code properly.

The solution is the **split-PR strategy**: cherry-pick Conductor commits to main FIRST
as their own small standalone PR (PR 1), then open the Phase 4C application-code PR
(PR 2) separately. The Conductor cherry-pick PR is small (~10–15 commits, all in
`00_ARCHITECTURE/CONDUCTOR/`), fast to review, and lands on main immediately.

---

## §2 — The cherry-pick procedure

Run this from the Madhav clone (canonical main-branch repository):

```bash
# Step 1 — Start from a clean main
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main
git pull origin main

# Step 2 — Create the migration branch
git checkout -b feature/conductor-to-main

# Step 3 — Identify Conductor commits on feature/phase-4c-panchang
# These are commits that ONLY touch 00_ARCHITECTURE/CONDUCTOR/ paths
# AND/OR 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_*.md
git log origin/feature/phase-4c-panchang --oneline \
  -- 00_ARCHITECTURE/CONDUCTOR/ \
     00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md

# The output shows the cherry-pickable Conductor commits. Verify:
# - Every commit in the list touches ONLY Conductor paths (not platform/ or app code)
# - The list is complete (no Conductor commit was accidentally bundled with app code)

# Step 4 — Cherry-pick each Conductor commit in chronological order (oldest first)
# Note: git log above shows newest-first; reverse before cherry-picking
git cherry-pick <oldest-sha> <second-sha> ... <newest-sha>

# Step 5 — Resolve conflicts (expect none; Conductor is scoped to its own directory)
# If conflicts appear, they are almost certainly because a governance file was
# touched by both a Conductor commit and an unrelated commit — investigate before
# force-resolving.

# Step 6 — Verify the cherry-pick result
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py   # must exit 0
git log --oneline -15 -- 00_ARCHITECTURE/CONDUCTOR/  # shows Conductor commits only

# Step 7 — Push and open PR
git push -u origin feature/conductor-to-main
gh pr create \
  --title "Conductor — autonomous session orchestrator (Wave 1 → main)" \
  --body "$(cat <<'EOF'
## Summary

- Adds the MARSYS-JIS Conductor: autonomous session orchestrator for Wave 1 (Phase 4C)
- Orchestrator walks session_queue.yaml, spawning sub-agents per brief, gated on shell tests
- Smoke test (SMOKE-S0) executed and PASSED during CONDUCTOR-S0 session on 2026-05-19
- All Conductor files live in 00_ARCHITECTURE/CONDUCTOR/ — no application code included

## Contents

- CONDUCTOR_PROMPT_v1_0.md — orchestrator system prompt (the meta-prompt)
- session_queue.yaml — 11-entry Wave 1 queue (Phase 4C sessions 4C-1-S1 through 4C-9)
- CONDUCTOR_LOG.md — run history (SMOKE-S0 PASS already recorded)
- CONDUCTOR_HALT_LOG.md — halt log (empty)
- schemas/ — JSON schemas for queue entries and halt entries
- validate_queue.py — queue validation script
- smoke/ — smoke test brief + queue + SMOKE_HEARTBEAT.md (proof of life)
- README.md — operator documentation
- WAVE_2_MIGRATION_NOTE.md — this file (cherry-pick procedure)
- CLAUDE_MD_AMENDMENT_PROPOSAL.md — deferred CLAUDE.md amendment (apply AFTER this PR merges)

## Test plan

- [x] validate_queue.py exits 0 on both session_queue.yaml and smoke/smoke_queue.yaml
- [x] SMOKE-S0 heartbeat commit exists (ef3d14d) on feature/phase-4c-panchang
- [x] All Conductor commits touch ONLY 00_ARCHITECTURE/CONDUCTOR/ paths
- [ ] Reviewer verifies no application code leaked into cherry-picked commits

🤖 Generated with Claude Code (CONDUCTOR-S0, 2026-05-19)
EOF
)"
```

---

## §3 — Trigger conditions (run this procedure when ANY one is true)

1. **Wave 1 closes** (all of 4C-1 through 4C-9 have `status: passed` or `status: skipped`)
   — the natural moment. Execute the cherry-pick, open PR 1, then open PR 2 (Phase 4C close).

2. **Wave 2 expansion is requested mid-Phase-4C** — if you want to start M5-A or Phase 4B
   autonomously before all of Phase 4C closes, cherry-pick early. Cleaner than waiting, and
   Wave 2 sessions on other worktrees can start immediately after PR 1 merges.

3. **Red-team finding** — if a Phase 4C red-team pass (IS.8(b)) flags branch contamination
   (Conductor commits mixed with application code in a way that complicates review), resolve
   by cherry-picking immediately.

---

## §4 — What to verify post-merge

After PR 1 merges to main:

```bash
# From the Madhav clone (now on main after the merge)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main && git pull

# Verify Conductor files exist on main
ls 00_ARCHITECTURE/CONDUCTOR/

# Verify validator works on main
python3 00_ARCHITECTURE/CONDUCTOR/validate_queue.py
# Expected: OK — 11 entries valid (session_queue.yaml)

# Verify SMOKE_HEARTBEAT.md exists (confirms smoke test commit cherry-picked correctly)
ls 00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md
```

After these checks pass, proceed to the CLAUDE.md amendment (§5 below).

---

## §5 — CLAUDE.md amendment (apply AFTER PR 1 merges)

A CLAUDE.md amendment is queued in `CLAUDE_MD_AMENDMENT_PROPOSAL.md`. Apply it
in a dedicated Cowork session AFTER PR 1 merges to main:

1. Open a Cowork session on the Madhav clone (main branch).
2. Read `00_ARCHITECTURE/CONDUCTOR/CLAUDE_MD_AMENDMENT_PROPOSAL.md`.
3. Apply the proposed text block to `CLAUDE.md §E` (Five → Six workstreams).
4. Version-bump CLAUDE.md (v2.6 → v2.7 or current version → +1 minor).
5. Propagate MP.1 to `.geminirules` (add Conductor to the concurrent workstreams block).
6. Commit: `Apply CLAUDE.md §E Conductor workstream amendment post-Wave-1-cherry-pick`.
7. MP.2 update: reflect in `.gemini/project_state.md`.

**Do NOT apply the amendment before PR 1 merges.** Applying it on
`feature/phase-4c-panchang` creates a CLAUDE.md state that references a workstream
not yet visible on main, which confuses sessions running on other worktrees.

---

## §6 — Anti-pattern warning: the fat-merge trap

**DO NOT** merge `feature/phase-4c-panchang` to main as a single PR if the Conductor
is still on that branch. Two failure modes follow:

1. **Phase 4C review is muddied.** The reviewer must mentally separate orchestration
   infrastructure from the Panchang application code in a single pass. This is the
   exact dilution that drives review fatigue and missed bugs.

2. **Wave 2 is gated on Phase 4C completion.** If Conductor only reaches main after
   Phase 4C closes, Wave 2 (M5-A, 4B, 4D autonomy) cannot start until then — defeating
   the purpose of building the Conductor at all.

The cherry-pick PR (PR 1) takes under 30 minutes to review because it is entirely
infrastructure. Do it first. Phase 4C code review (PR 2) gets the focused attention
it deserves, uncontaminated by Conductor noise.

---

*End of WAVE_2_MIGRATION_NOTE.md — authored 2026-05-19, session CONDUCTOR-S0.*
