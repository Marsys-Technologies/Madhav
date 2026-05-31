# Kickoff prompt — STREAM A (Build hardening + CI/CD automation)

Paste the block below into a fresh Antigravity Claude Code window opened
in `/Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI`.

---

```
You are Claude Code running in Google Antigravity IDE.

ARC: build_e2e_arc · Stream A
PROJECT: MARSYS-JIS
WORKTREE: /Users/Dev/Vibe-Coding/Apps/MadhavHardeningCI (already on feat/hardening-ci)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

REQUIRED READS at session open (in order, full files):
  1. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md
  2. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/session_queue.yaml
  3. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/briefs/STREAM_A_HARDENING_CI_v1_0.md
  4. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/CLAIM_LEDGER.yaml (current state)

GOAL:
  Execute all 9 sessions for Stream A (A-S1 through A-S9). Walk the queue
  in declared order. Claim → execute → release per CLAIM_LEDGER protocol
  in STREAM_COORDINATION §4. Cherry-pick each session to main per §5.
  Auto-fix CI up to 5 attempts per §6. Halt only on conditions in §8.

CRITICAL CONTEXT — A-S8 is load-bearing:
  When A-S8 cherry-picks to main, .github/workflows/deploy.yml triggers
  the FIRST auto-deploy with the new chain (deploy + migrate + IaC + smoke
  + traffic flip). If anything in that pipeline fails, that's a real CI
  failure to fix via the auto-fix loop. Don't let it sit broken.

HARD GATES:
  - Stay in the assigned worktree. Do NOT cd to other streams' worktrees.
  - Do NOT touch files outside Stream A's owned paths (see STREAM_COORDINATION §9).
  - Do NOT invoke gcloud builds submit / gcloud run deploy directly. Deploy
    is GitHub-Actions-only; you push code, CI does the rest.
  - Do NOT use Anthropic models.
  - Do NOT halt on a single CI failure. Auto-fix loop = 5 attempts.

WHEN DONE (queue empty for Stream A):
  Print the §10 STREAM REPORT block. Exit.

If session-open required reads fail or any blocker hits, STOP and write a
one-paragraph blocker note. Do not improvise on auth, prod DB, or scope.
```
