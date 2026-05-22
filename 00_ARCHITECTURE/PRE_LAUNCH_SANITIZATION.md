---
artifact: PRE_LAUNCH_SANITIZATION.md
project_name: Claude Takeover
status: ACTION_REQUIRED
authored: 2026-05-22
authored_by: Cowork
companion: CLEANUP_PLAN_2026-05-22.md (comprehensive inventory; this doc is the minimum-required pre-launch subset)
role: >
  Minimum-required workspace sanitization before Claude Takeover launches.
  Distinguishes blocking-for-launch cleanup from optional-deferred cleanup
  so the native can sanitize confidently without accidentally removing
  Claude Takeover dependencies or any other active workstream.
---

# Claude Takeover — Pre-Launch Sanitization

## §1 — TL;DR

Three categories:

- **MUST DO before Claude Takeover launches** — 4 things (§2).
- **MUST NOT TOUCH** — Claude Takeover bundle + MCP Transformation worktrees + active branches (§3).
- **OPTIONAL — can defer** — branch hygiene, M6/ICR worktree decisions, native-decision items from `CLEANUP_PLAN_2026-05-22.md §7` (§4).

## §2 — MUST DO before launch (4 actions)

These four steps unblock Claude Takeover launch. Without them, the Meta-Conductor either can't run (collision with stale state) or risks losing the planning work.

### 2.1 Commit the Claude Takeover planning bundle to main

The Claude Takeover governance (CAPABILITY_MATRIX, ROADMAP, R11 v2 brief bundle, Meta-Conductor + Level-1 Conductor prompts + queues, Claude Code prompts) sits as **uncommitted untracked files in main's working tree.** If you accidentally `git clean -fd` or `git checkout .`, the entire Claude Takeover plan disappears.

**Resolution:** commit them on main in one coherent commit. The Meta-Conductor's `§3.A — Bootstrap` step does this automatically when it runs, so this is actually pre-staged inside the Meta-Conductor — but committing now means recovery via `git reflog` instead of "hope" if something goes wrong before launch.

### 2.2 Remove the stale `MadhavR11` worktree + `chat-v2/round11-claude-parity` branch

A worktree exists at `/Users/Dev/Vibe-Coding/Apps/MadhavR11` on branch `chat-v2/round11-claude-parity`. This is the **R11 v1** worktree — superseded by Claude Takeover. The branch is **fully merged to main** (HEAD `2cabdbbd` = origin/main tip); safe to remove.

Why this matters for launch: Claude Takeover uses worktree names `MadhavR11A`, `MadhavR11B`, `MadhavR11CDE`. The stale `MadhavR11` doesn't collide by name, but its existence is confusing and the dangling chat-v2/round11-claude-parity branch is noise.

**Resolution:** `git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavR11` + `git branch -d chat-v2/round11-claude-parity`.

### 2.3 Verify no stale Claude Takeover worktrees exist

The Meta-Conductor's `§3.B.1` fails if `MadhavR11A` already exists on disk. The Phase 2 setup (`§3.C.1`) fails if `MadhavR11B` or `MadhavR11CDE` exist.

These should not exist (we haven't created them yet), but verify there's nothing stale from an aborted earlier attempt.

**Resolution:** check + remove any stale `/Users/Dev/Vibe-Coding/Apps/MadhavR11{A,B,CDE}/` paths.

### 2.4 Verify no stale Claude Takeover branches exist

Same as 2.3 for branches: `chat-v2/round11-a-foundation`, `chat-v2/round11-b-look-and-feel`, `chat-v2/round11-cde` (and the sub-branches `chat-v2/round11-cde-c`, `-d`, `-e`).

**Resolution:** `git branch -D` any stale Claude Takeover branches.

## §3 — MUST NOT TOUCH

The native must not delete, archive, or move these:

### 3.1 Claude Takeover bundle (61 files in `round11_v2/` + governance docs)
Every file under `00_ARCHITECTURE/chat_v2_briefs/round11_v2/` is the active arc. `00_ARCHITECTURE/CAPABILITY_MATRIX.md`, `MULTI_PROVIDER_PARITY_ROADMAP.md`, `USER_INTERACTION_PREFERENCES.md` are top-level governance. The 4 Conductor prompts (META + R11A + R11B + R11CDE) in `00_ARCHITECTURE/CONDUCTOR/` and the 3 R11 queue YAMLs are launch infrastructure.

### 3.2 MCP Transformation (MCPT) workstream
The 7 worktrees `MadhavMCPT-{FDN,BPHS,JK,TAJ,DPT,GRD,FIN}` and their feature branches are ACTIVE per CLAUDE.md §E (declared 2026-05-22). Different workstream from Claude Takeover; runs in parallel.

### 3.3 R11 v1 archive in `chat_v2_briefs/round11/`
Per `SUPERSESSION_NOTE.md §5`: "Do NOT delete R11 v1 files — they are audit trail." 24 files marked SUPERSEDED in frontmatter; preserved as historical record. Claude Takeover's NATIVE_RULINGS_v1_0.md carries forward into v2 by reference.

### 3.4 main branch + its full history
Main is at `c98537e8 MCP Transformation: planning artifacts`. The 7 MCPT branches all sit at this same SHA. Do not rewrite or reset main.

### 3.5 Wave 1 Conductor (`CONDUCTOR_PROMPT_v1_0.md` + `session_queue.yaml`)
The Phase 4C Wave 1 Conductor. Status: COMPLETE 2026-05-20. Preserved as audit trail per the project's hygiene discipline.

### 3.6 Native-decision branches (open questions in `CLEANUP_PLAN §7`)
- `icr/s2-l1-truth-index` + `MadhavICR` worktree
- `feature/m6-prospective-testing` + `marsys-m6-prospective` worktree
- `chat-v2/pr-111-remediation`
- `chore/root-cleanup-r7-r10`
- `cov/s4-sidecar-wrappers`
- `feature/conductor-to-main`

These need native decisions before disposition. **Do not delete during pre-launch sanitization.** They're orthogonal to Claude Takeover and won't interfere with the launch.

## §4 — OPTIONAL (can defer to post-launch)

These are nice-to-have cleanups that don't block Claude Takeover. Do them later when convenient.

| Item | From | Action |
|---|---|---|
| 5 fully-merged branches | CLEANUP_PLAN §4a | `git branch -d` each |
| 6 squash-merged branches | CLEANUP_PLAN §4b | `git branch -D` each (force needed; content is on main) |
| 4 upstream-gone branches | CLEANUP_PLAN §4c | `git branch -D` each |
| Lock files | CLEANUP_PLAN §5.1 | `rm .git/*.lock` if no live git process |
| MCPT remote pushes | CLEANUP_PLAN §5.4d | `git push -u origin feature/mcpt-*` for the 6 non-`final` MCPT branches |

## §5 — Paste-prompt — minimum-required pre-launch sanitization

Paste this into an Antigravity Claude Code session pointed at `/Users/Dev/Vibe-Coding/Apps/Madhav` BEFORE you paste the META_CONDUCTOR_KICKOFF_PROMPT. It does the 4 must-do steps from §2 and verifies the workspace is launch-ready.

```
You are performing pre-launch sanitization for Claude Takeover. Do not
proceed to the Meta-Conductor until this completes cleanly.

Working directory: /Users/Dev/Vibe-Coding/Apps/Madhav.
STOP on any failure and tell me what happened.

# Step 1 — Verify no live git process owns the lock
cd /Users/Dev/Vibe-Coding/Apps/Madhav
ls -la .git/index.lock .git/packed-refs.lock 2>&1 || echo "(no lock files — good)"
# If lock files exist AND no other git process is running:
# rm -f .git/index.lock .git/packed-refs.lock

# Step 2 — Verify Claude Takeover bundle is on disk
test -f 00_ARCHITECTURE/CAPABILITY_MATRIX.md && echo "PASS: CAPABILITY_MATRIX"
test -f 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md && echo "PASS: ROADMAP"
test -d 00_ARCHITECTURE/chat_v2_briefs/round11_v2 && echo "PASS: round11_v2/"
test -f 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_META_R11_v1_0.md && echo "PASS: META prompt"
test -f 00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml && echo "PASS: R11A queue"
test -f 00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml && echo "PASS: R11B queue"
test -f 00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml && echo "PASS: R11CDE queue"

# Step 3 — Commit Claude Takeover bundle on a planning branch (so it's preserved before any worktree manipulation)
git checkout -b chat-v2/round11-v2-planning 2>&1 | head -3
git add 00_ARCHITECTURE/CAPABILITY_MATRIX.md \
        00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md \
        00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md \
        00_ARCHITECTURE/CLEANUP_PLAN_2026-05-22.md \
        00_ARCHITECTURE/PRE_LAUNCH_SANITIZATION.md \
        00_ARCHITECTURE/chat_v2_briefs/round11_v2/ \
        00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/O-S1-system-prompt-layout-audit.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/O-S2-prompt-cache-breakpoints.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/O-S3-agentic-tool-loop.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/O-S4-inline-citation-parity.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/O-S5-adaptive-thinking-effort.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/S-S2-smooth-stream-v3-rate-target.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/S-S4-inline-tool-cards.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/V-S0-runtime-user-toggle.md \
        00_ARCHITECTURE/chat_v2_briefs/round11/V-S1-claude-typography-stack.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_META_R11_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11B_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11CDE_v1_0.md \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11.yaml \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml \
        00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml \
        00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md

git commit -m "plan(claude-takeover): Claude Takeover R11 v2 planning bundle + R11 v1 supersession + cleanup plan

Project codename: Claude Takeover. R11 v2 Multi-Provider Parity active arc
across all 5 LLM providers (anthropic, google, openai, deepseek, nvidia).

Active arc (R11.A-E only; R11.F-K deferred):
- R11.A Foundation (14 entries; A-S2..A-S6 parallel_group)
- R11.B Look-and-Feel (10 entries)
- R11.CDE composite C+D+E (27 entries with intermediate MERGEs)

Total: 49 sessions, ~38-54h wall-clock, ~3.5-4.5 weeks via Meta-Conductor
single-session orchestration (primary) or Pattern 2+ 3-session (backup).

Includes:
- CAPABILITY_MATRIX.md (per-capability per-provider source of truth)
- MULTI_PROVIDER_PARITY_ROADMAP.md (phase sequencing)
- USER_INTERACTION_PREFERENCES.md (Cowork interaction rules)
- R11V2_MASTER_PLAN_v1_0.md (umbrella)
- 51 brief files across 3 phase directories
- 4 Conductor prompts (META + R11A + R11B + R11CDE)
- 3 queue YAMLs (R11A 14, R11B 10, R11CDE 27)
- Claude Code KICKOFF prompts + Pattern 2+ launch guide
- R11 v1 SUPERSEDED with SUPERSESSION_NOTE carrying rulings forward

R11 v1 marked SUPERSEDED_BY_MULTI_PROVIDER_ROADMAP per native ruling 2026-05-22.
NATIVE_RULINGS §1-8 carry forward into R11 v2.

MCP_TRANSFORMATION_PLAN_v1_0 amendments folded in."

# Step 4 — Push the planning branch (so the work is also on remote, not just local)
git push -u origin chat-v2/round11-v2-planning

# Step 5 — Return to main + verify clean
git checkout main
git status

# Step 6 — Verify no stale Claude Takeover worktrees/branches
for w in MadhavR11A MadhavR11B MadhavR11CDE; do
  if [ -e /Users/Dev/Vibe-Coding/Apps/$w ]; then
    echo "WARN: /Users/Dev/Vibe-Coding/Apps/$w exists — remove before Meta-Conductor launches"
  else
    echo "PASS: /Users/Dev/Vibe-Coding/Apps/$w does not exist"
  fi
done
for b in chat-v2/round11-a-foundation chat-v2/round11-b-look-and-feel chat-v2/round11-cde; do
  if git show-ref --verify --quiet refs/heads/$b; then
    echo "WARN: branch $b exists — remove before Meta-Conductor launches: git branch -D $b"
  else
    echo "PASS: branch $b does not exist"
  fi
done

# Step 7 — Retire the stale R11 v1 MadhavR11 worktree + branch
if [ -e /Users/Dev/Vibe-Coding/Apps/MadhavR11 ]; then
  git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavR11
  echo "Removed MadhavR11 worktree"
fi
if git show-ref --verify --quiet refs/heads/chat-v2/round11-claude-parity; then
  git branch -d chat-v2/round11-claude-parity 2>&1 | head -3
  echo "Removed chat-v2/round11-claude-parity branch"
fi
git worktree prune

# Step 8 — Final readiness banner
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo " CLAUDE TAKEOVER PRE-LAUNCH SANITIZATION COMPLETE"
echo "─────────────────────────────────────────────────────────────────────"
echo " main HEAD:             $(git rev-parse --short main)"
echo " planning branch:       chat-v2/round11-v2-planning (pushed to origin)"
echo " stale MadhavR11:       removed"
echo " stale chat-v2/round11-claude-parity branch: removed"
echo " Claude Takeover bundle: committed on planning branch"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo " Active worktrees on disk:"
git worktree list 2>&1 | head -15
echo ""
echo " NEXT: paste the body of META_CONDUCTOR_KICKOFF_PROMPT.md in this same"
echo "       Antigravity session to launch the Claude Takeover Meta-Conductor."
echo "       Or open a fresh session for clean context."
echo ""
echo " The Meta-Conductor will then commit the planning branch back to main as"
echo " its §3.A bootstrap step."
```

## §6 — What happens if I skip this and just launch?

The Meta-Conductor's `§3.A — Bootstrap` step DOES handle the planning bundle commit itself. So technically you can skip §2.1 — the Meta-Conductor catches it. But that means:

- If something goes wrong between now and the Meta-Conductor reaching §3.A, the planning work is at risk (uncommitted).
- The Meta-Conductor commits everything to `main` directly, not to a planning branch. Less reversible.

§2.2 (stale `MadhavR11` worktree) doesn't block launch but adds noise — strongly recommended.

§2.3 and §2.4 (stale Claude Takeover worktrees/branches) WOULD block launch. Run them as verification.

## §7 — Native-decision items (deferred per CLEANUP_PLAN §7)

These 6 questions remain open from the earlier audit. Answer them when you're ready (post-Claude-Takeover launch is fine):

1. `chat-v2/pr-111-remediation` — drop or cherry-pick? (5 governance docs commits not on main)
2. `chore/root-cleanup-r7-r10` — drop or land? (1 commit archiving 54 root files)
3. `cov/s4-sidecar-wrappers` — drop or land? (WIP carrying ICR/s2 scaffolding)
4. `icr/s2-l1-truth-index` + `MadhavICR` worktree — does the v1.3 carry-forward MSR-grounding work land via this branch or a fresh one?
5. `feature/m6-prospective-testing` + `marsys-m6-prospective` worktree — drop (premature per CLAUDE.md §L), defer (rebase later), or land (M5 implicitly done)?
6. `feature/conductor-to-main` (23 commits, 265 behind) — cherry-pick to main soon, or hold until after MCPT Wave 0 ships?

None of these block Claude Takeover. They can wait.

---

*End of PRE_LAUNCH_SANITIZATION.md.*
