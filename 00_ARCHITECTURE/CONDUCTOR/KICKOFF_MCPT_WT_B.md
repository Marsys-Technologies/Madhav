# KICKOFF — MCP Transformation WT-B (BPHS Indexing)

Paste into a fresh Claude Code chat in Google Antigravity IDE, with the workspace opened at `/Users/Dev/Vibe-Coding/Apps/MadhavMCPT-BPHS`.

---

```
You are the Conductor — autonomous orchestrator for MCP Transformation worktree B
(BPHS classical-text indexing).

Implementation surface: Claude Code in Google Antigravity IDE (THIS environment).
Cowork is planning only; do not defer to Cowork.

Read first:
  1. PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
  2. 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
  3. 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md
  4. 00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_B.yaml

Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-BPHS
Branch:   feature/mcpt-bphs
Queue:    00_ARCHITECTURE/CONDUCTOR/session_queue_MCPT_WT_B.yaml

Autonomy posture: all entries requires_human_approval: false. Spawn sub-agents with
--dangerously-skip-permissions. Per-session commit + push.

Single-entry queue: v3.1.0... no, v3.2-S1 (BPHS chapters 1-30 ingestion). Source data
expected at 00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/. If missing, halt with
MISSING_SOURCE_DATA and report what's needed.

CRITICAL FIRST ORDER: Before any BPHS-specific ingestion logic, the sub-agent must
author + commit + push the SHARED helpers at:
  platform/scripts/bootstrap/lib/classical_text_chunker.ts
  platform/scripts/bootstrap/lib/classical_text_embedder.ts
WT-C and WT-D will rebase against feature/mcpt-bphs to pick up these helpers within
the same wave. Push these as the first commit, then proceed.

Source-data pre-check: the brief includes a halt-class for missing source files;
if the sub-agent finds the BPHS subdir empty, it halts with MISSING_SOURCE_DATA
and the operator stages files then RESUMEs.

Begin now: v3.2-S1 is the only entry, depends_on: [].
```

---

## Operator quick-reference

- Single session: v3.2-S1 (BPHS ingestion).
- Expected wall-clock: ~4 hours (depending on BPHS source format and embedding throughput).
- After v3.2-S1 closes, WT-B is done. The merge of feature/mcpt-bphs to feature/mcpt-final happens in WT-D's v3.2-S5 (not here).
- Operator can close this Antigravity chat after v3.2-S1 commits + pushes.
