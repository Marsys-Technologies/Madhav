# KICKOFF — MCP Transformation FINAL (Red-Team + Main Merge)

**Open this LAST.** Only after Wave 4 has completed — i.e., all six implementation worktrees (WT-A through WT-F) have merged their work into `feature/mcpt-final`.

Paste into a fresh Claude Code chat in Google Antigravity IDE, workspace at `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FIN`.

---

```
You are the Conductor — autonomous orchestrator for MCP Transformation FINAL phase.
Single session: v3.4-S2 (red-team + project-level sealing artifact + merge to main).

This is the FINAL session of MCP Transformation. It is the SOLE entry across the project
with requires_human_approval: true — the native (Abhisek Mohanty) must explicitly
approve the main merge after red-team clears.

Implementation surface: Claude Code in Google Antigravity IDE.

Read first:
  1. PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
  2. 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md (esp. §7 merge protocol)
  3. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md
  4. 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_FINAL.yaml
  5. MCP_ARCH_v3_PROPOSAL_2026-05-22.md §11 (security threat model — the red-team agenda)
  6. MACRO_PLAN_v2_0.md §IS.8(b) (red-team cadence requirements)
  7. ALL prior MCPT_*_CLOSE.md artifacts (you're aggregating their evidence into MCPT_CLOSE_v1_0.md)

Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FIN
Branch:   feature/mcpt-final
Queue:    00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_FINAL.yaml

PRE-FLIGHT VERIFICATION (do this BEFORE spawning v3.4-S2 sub-agent):
  1. git fetch origin feature/mcpt-final
  2. git checkout feature/mcpt-final && git pull
  3. Verify all 4 phase-close artifacts exist on feature/mcpt-final:
       - 00_ARCHITECTURE/MCPT_V310_CLOSE.md   (foundation seal)
       - 00_ARCHITECTURE/MCPT_V32_CLOSE.md    (classical-grounding seal)
       - 00_ARCHITECTURE/MCPT_V33_CLOSE.md    (depth seal)
       - 00_ARCHITECTURE/MCPT_V34_S1_CLOSE.md (grounding seal)
  4. If any close artifact missing, halt with CROSS_WT_DEPENDENCY_NOT_MERGED and report
     which worktree hasn't completed.

THE HUMAN-GATED STEP:
v3.4-S2's brief specifies that after red-team passes (0 class-1 findings) and the
sealing artifacts are committed to feature/mcpt-final, the sub-agent:
  1. Prepares the merge commit: git checkout main && git merge --no-ff feature/mcpt-final
  2. Does NOT push.
  3. Halts with REQUIRES_NATIVE_APPROVAL.
  4. Outputs in the halt: the merge commit SHA, diff summary, MCPT_CLOSE_v1_0.md link.

Operator (native) replies with one of:
  - APPROVE_MAIN_MERGE → sub-agent runs git push origin main, triggers deploy, runs smoke.
  - REJECT → sub-agent halts permanently; v3.5 follow-up tickets opened.

Begin now: pre-flight check, then v3.4-S2.
```

---

## Operator quick-reference

- Single session: v3.4-S2.
- Three phases within the session:
  1. Red-team probes (T.1–T.8 per MCP_ARCH §11). Must achieve 0 class-1 findings.
  2. Project-level sealing artifact (MCPT_CLOSE_v1_0.md).
  3. Main merge + production deploy + smoke (gated by your APPROVE_MAIN_MERGE).
- Expected wall-clock: ~3 hours including your review time.
- After APPROVE_MAIN_MERGE: production v3.1 MCP is live; MCP Transformation closes.
- This is the ONLY session in MCP Transformation where you (the native) explicitly approve. Everything else was autonomous.
