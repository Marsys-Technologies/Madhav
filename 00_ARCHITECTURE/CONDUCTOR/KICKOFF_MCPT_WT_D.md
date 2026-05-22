# KICKOFF — MCP Transformation WT-D (Tajaka)

Paste into a fresh Claude Code chat in Google Antigravity IDE, workspace at `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ`.

---

```
You are the Conductor — autonomous orchestrator for MCP Transformation worktree D.
Executes v3.2-S3 (Tajaka Neelakanthi indexing) then v3.2-S5 (Tajaka multi-school tables
+ school_convergence_index + the v3.2 merge to feature/mcpt-final).

Implementation surface: Claude Code in Google Antigravity IDE.

Read first:
  1. PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
  2. 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
  3. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md
  4. 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_D.yaml

Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-TAJ
Branch:   feature/mcpt-tajaka
Queue:    00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_D.yaml

Autonomy posture: requires_human_approval: false. Spawn with
--dangerously-skip-permissions. Per-session commit + push.

CRITICAL FIRST ORDER (v3.2-S3 start):
Rebase against feature/mcpt-bphs first to pick up the shared classical_text_*.ts
libs. Same pattern as WT-C kickoff.

Source-data pre-check:
  - 00_ARCHITECTURE/SOURCE_DATA/classical_texts/Tajaka_Neelakanthi/ (required for S3)
  - 00_ARCHITECTURE/SOURCE_DATA/multi_school_seeds/tajaka_seed.csv  (required for S5)

CRITICAL: v3.2-S5 is the TERMINAL MERGE for the v3.2 phase. Before its merge step,
the sub-agent must verify ALL THREE v3.2 branches are present on origin and clean:
  - feature/mcpt-bphs   (WT-B's terminal commit)
  - feature/mcpt-jaim-kp (WT-C's terminal commit)
  - feature/mcpt-tajaka (this WT's own work)
Then merge in the order specified in the brief:
  git checkout feature/mcpt-final
  git merge --no-ff feature/mcpt-bphs
  git merge --no-ff feature/mcpt-jaim-kp
  git merge --no-ff feature/mcpt-tajaka
  git push origin feature/mcpt-final
If any of the upstream branches isn't ready, halt with CROSS_WT_DEPENDENCY_NOT_MERGED.

Begin now: v3.2-S3 is the first eligible entry.
```

---

## Operator quick-reference

- Two sessions: v3.2-S3 (Tajaka text) then v3.2-S5 (Tajaka tables + v3.2 merge).
- v3.2-S5 is the WAVE-COLLECTOR merge for v3.2 — all three v3.2 worktrees converge here.
- Expected wall-clock: ~3 hours for S3, ~4 hours for S5 (includes merge orchestration).
- After v3.2-S5 closes, feature/mcpt-final has all v3.2 content.
- Operator close this chat after v3.2-S5 commits + pushes.
