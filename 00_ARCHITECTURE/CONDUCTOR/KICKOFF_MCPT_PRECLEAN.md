# KICKOFF — MCP Transformation PRE-CLEAN (MCPT-stream only)

**Purpose:** commit the three MCPT-stream planning amendments to main so MCP Transformation can launch with its own artifacts safely in git history. **Scope: MCPT files only.** All R11 / Claude Takeover / v1-era uncommitted files are explicitly left untouched — those are separate workstreams the native manages independently.

**Open this Claude Code chat in Google Antigravity IDE, with the workspace opened at `/Users/Dev/Vibe-Coding/Apps/Madhav` (the main repo).** Launch with `--dangerously-skip-permissions`.

This is a short-lived session — it executes 1 commit + 1 push and exits. Not a long-running Conductor.

---

## Paste this into the chat

```
You are a Claude Code sub-agent running in Google Antigravity IDE, opened at
/Users/Dev/Vibe-Coding/Apps/Madhav (the main MARSYS-JIS repo). Your single
job is to execute the MCP Transformation PRE-CLEAN.

══════════════════════════════════════════════════════════════════════════════
HARD SCOPE CONSTRAINT (native ruling)
══════════════════════════════════════════════════════════════════════════════

You handle ONLY the three MCPT-stream files listed below. Every other
uncommitted file in the working tree (R11 v1 modifications, R11 v2 / Claude
Takeover untracked files, the MCP v1 deploy runbook, prior cleanup audit
docs, etc.) belongs to other workstreams that the native manages
INDEPENDENTLY. You do NOT touch them. You do NOT stage them. You do NOT
comment on them.

If you notice non-MCPT files in the working tree at STEP 0, that is
EXPECTED. Do NOT halt. Proceed with the MCPT-only commit. The working tree
will remain dirty after your work — that is BY DESIGN.

══════════════════════════════════════════════════════════════════════════════
THE THREE MCPT FILES IN YOUR SCOPE
══════════════════════════════════════════════════════════════════════════════

  1. 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md   (M — §12/§13 additions)
  2. 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md              (?? — new file)
  3. 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_PRECLEAN.md          (?? — this very prompt; self-committing)

That is the entire scope. Three files. One commit. Then push. Then exit.

══════════════════════════════════════════════════════════════════════════════
READ FIRST (context, do not skip)
══════════════════════════════════════════════════════════════════════════════

  1. 00_ARCHITECTURE/PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
       Cowork = plan. Claude Code = impl. Full autonomy on MCPT.
  2. 00_ARCHITECTURE/USER_INTERACTION_PREFERENCES.md
       Native interaction preferences. Note §1 — you report back in Claude
       Code prompt style, not raw shell output.

══════════════════════════════════════════════════════════════════════════════
STEP 0 — Pre-flight verification (MCPT-scoped only)
══════════════════════════════════════════════════════════════════════════════

Run:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  git rev-parse --abbrev-ref HEAD
  git log --oneline -1
  git status --short -- 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md \
                       00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md \
                       00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_PRECLEAN.md

Expected:
  - Branch: main
  - HEAD: c98537e8 "MCP Transformation: planning artifacts (master plan, 17
    briefs, 7 queues, 7 kickoffs, setup script)"
  - Status output shows all three files: one as M, two as ??.

If branch is NOT main, or HEAD is NOT c98537e8 (or a descendant of it that
already includes the 3 MCPT files committed — in which case you're already
done; report PASS and exit), or any of the 3 MCPT files is missing from
disk: HALT and report to the operator. Do not proceed.

If non-MCPT files appear in `git status` (no --) — IGNORE THEM. Do not
mention them in your halt criteria. They are out of scope.

══════════════════════════════════════════════════════════════════════════════
STEP 1 — Commit the three MCPT files (the only commit you make)
══════════════════════════════════════════════════════════════════════════════

Stage exactly these three files (no more, no less):

  git add 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
  git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md
  git add 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_PRECLEAN.md

Verify the staged set:
  git diff --cached --stat

Expected output: exactly 3 files staged, all under 00_ARCHITECTURE/CONDUCTOR/.
If any 4th file is staged: HALT, run `git reset` to unstage, report to
operator. Something is wrong.

Commit with message:

  MCP Transformation: meta-Conductor (Strategy 3) + pre-clean runbook

  Adds KICKOFF_MCPT_META.md: single meta-Conductor that orchestrates all
  5 in-scope worktrees (A/B/C/D/E + FINAL) from one Antigravity chat via
  cd-prefixed sub-agent spawns and batch parallelism. WT-F runs as a
  sibling chat for the long v3.4-S1 grounding pipeline. Operator workflow
  shifts from 7 chats (distributed) to 2 chats (meta + WT-F sibling).

  Adds KICKOFF_MCPT_PRECLEAN.md: the Claude Code paste-prompt that
  executes this very commit. MCPT-stream only — other workstreams (R11 v1,
  Claude Takeover / R11 v2, MCP v1 deploy artifacts, etc.) are handled
  independently by the native and explicitly out of scope here.

  Updates MCP_TRANSFORMATION_PLAN_v1_0.md:
   - New §12: meta-Conductor mode (Strategy 3) — protocol, 2-chat workflow,
     log paths, invariants, fallback to distributed mode.
   - §13: TL;DR updated to recommend meta-mode as primary launch path.

  Distributed mode (the original §3) preserved as fallback via the
  per-worktree kickoffs KICKOFF_MCPT_WT_{A..F}.md.

══════════════════════════════════════════════════════════════════════════════
STEP 2 — Verify the MCPT files are no longer dirty (other files may remain)
══════════════════════════════════════════════════════════════════════════════

Run:
  git status --short -- 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md \
                       00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md \
                       00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_PRECLEAN.md

Expected: empty output (all 3 files now committed; no longer in the diff
or untracked set).

If any of the 3 files still shows in the output: HALT, report.

Then run:
  git log --oneline -2

Expected:
  <new-sha>  MCP Transformation: meta-Conductor (Strategy 3) + pre-clean runbook
  c98537e8   MCP Transformation: planning artifacts (master plan, 17 briefs, 7 queues, 7 kickoffs, setup script)

══════════════════════════════════════════════════════════════════════════════
STEP 3 — Push to origin/main
══════════════════════════════════════════════════════════════════════════════

Run:
  git push origin main

Expected: push succeeds. origin/main now contains the c98537e8 commit + the
new meta-Conductor commit.

══════════════════════════════════════════════════════════════════════════════
STEP 4 — Report
══════════════════════════════════════════════════════════════════════════════

Output to chat:

  ══════════════════════════════════════════════════════════════
   MCPT PRE-CLEAN COMPLETE (MCPT-stream only)
  ══════════════════════════════════════════════════════════════

  Commit authored:
    <new-sha>  MCP Transformation: meta-Conductor (Strategy 3) + pre-clean runbook  (3 files)

  Files committed:
    1. 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md (M → committed)
    2. 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md            (?? → committed)
    3. 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_PRECLEAN.md        (?? → committed)

  Pushed to: origin/main (2 commits ahead via c98537e8 + new commit)

  Note: working tree intentionally still contains uncommitted files from
  other workstreams (R11 v1 modifications, Claude Takeover / R11 v2 untracked
  files, MCP v1 deploy runbook, etc.). The native manages those independently
  and they are explicitly out of MCPT scope.

  Worktrees (verify still present):
    /Users/Dev/Vibe-Coding/Apps/Madhav            → main          (this)
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN   → feature/mcpt-foundation
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-BPHS  → feature/mcpt-bphs
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK    → feature/mcpt-jaim-kp
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ   → feature/mcpt-tajaka
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-DPT   → feature/mcpt-depth
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD   → feature/mcpt-grounding
    /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FIN   → feature/mcpt-final

  READY FOR MCP TRANSFORMATION KICKOFF.

  Next operator action:
    1. (Optional) Stage source data into 00_ARCHITECTURE/SOURCE_DATA/
       subdirs per MCP_TRANSFORMATION_PLAN §6.
    2. Open the META chat in Antigravity at /Users/Dev/Vibe-Coding/Apps/Madhav
       and paste 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_META.md.
    3. Open the WT-F sibling chat at /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-GRD
       and paste 00_ARCHITECTURE/CONDUCTOR/KICKOFF_MCPT_WT_F.md.

Then exit. This session has no further work.
```

---

## Operator quick-reference

- One commit. Three files. Then push. Then exit.
- ~15 seconds wall-clock.
- After completion: MCPT planning is fully committed and pushed; non-MCPT working-tree state is untouched (your separate workstream concern).
- If the session HALTs at STEP 0 (e.g., HEAD has already advanced past `c98537e8` because you committed manually in between, or the 3 MCPT files have already been moved/renamed), paste the chat output back into Cowork and I'll diagnose.
