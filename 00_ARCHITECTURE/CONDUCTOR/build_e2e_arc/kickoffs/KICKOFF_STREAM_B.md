# Kickoff prompt — STREAM B (Data plumbing)

Paste the block below into a fresh Antigravity Claude Code window opened
in `/Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing`.

---

```
You are Claude Code running in Google Antigravity IDE.

ARC: build_e2e_arc · Stream B
PROJECT: MARSYS-JIS
WORKTREE: /Users/Dev/Vibe-Coding/Apps/MadhavDataPlumbing (already on feat/data-plumbing)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

REQUIRED READS at session open (in order, full files):
  1. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md
  2. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/session_queue.yaml
  3. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/briefs/STREAM_B_DATA_PLUMBING_v1_0.md
  4. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/CLAIM_LEDGER.yaml

GOAL:
  Execute all 7 sessions for Stream B (B-S1 through B-S7). Walk the queue
  in declared order. Claim → execute → release per CLAIM_LEDGER protocol
  in STREAM_COORDINATION §4. Cherry-pick each session to main per §5.
  Auto-fix CI up to 5 attempts per §6.

CRITICAL CONTEXT — B-S1 must merge cleanly:
  B-S1 merges fix/chart-dedupe into feat/data-plumbing. If merge conflicts,
  HALT — do NOT improvise resolution across arcs. The chart-dedupe branch
  is sealed at commit a5845e22; it touches /api/clients/create + a new
  migration + a new script. None of these overlap with sidecar files.

CRITICAL CONTEXT — payload shape:
  B-S5 adds discriminated-union variants to sse_events.ts. BEFORE writing
  the variants, grep LiveBuildGraph.tsx for what fields it actually consumes:
    grep -n "node_added\|edge_added\|addEventListener" platform/src/components/cockpit/LiveBuildGraph.tsx
  Stream C may have authored the consumer with specific field names. If
  they differ from your Python payload, adapt the Python payload (in B-S2/B-S3),
  never the FE.

HARD GATES:
  - Stay in the assigned worktree.
  - Do NOT touch writer files under python-sidecar/pipeline/writers/.
  - Do NOT add any schema migration. build_events.chart_id already exists.
  - If a column referenced doesn't exist, DROP that line — never invent.
  - Do NOT use Anthropic models.

WHEN DONE (queue empty):
  Print the §10 STREAM REPORT block. Exit.

If any blocker hits, STOP and write a one-paragraph blocker. Do not improvise.
```
