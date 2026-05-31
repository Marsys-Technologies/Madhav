# Kickoff prompt — STREAM C (Visual v2 implementation)

Paste the block below into a fresh Antigravity Claude Code window opened
in `/Users/Dev/Vibe-Coding/Apps/MadhavVisualV2`.

---

```
You are Claude Code running in Google Antigravity IDE.

ARC: build_e2e_arc · Stream C
PROJECT: MARSYS-JIS
WORKTREE: /Users/Dev/Vibe-Coding/Apps/MadhavVisualV2 (already on feat/visual-v2)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

REQUIRED READS at session open (in order, full files):
  1. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md
  2. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/session_queue.yaml
  3. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/briefs/STREAM_C_VISUAL_V2_v1_0.md
  4. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/VISUAL_CONTRACT_v2.md ← the spec, native-approved
  5. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/CLAIM_LEDGER.yaml

GOAL:
  Execute all 9 sessions for Stream C (C-S1 through C-S9). Walk the queue
  in declared order. Match VISUAL_CONTRACT_v2.md exactly; elevate further
  on typography, animation polish, and microcopy where natural.

CRITICAL CONTEXT — NewClientForm boundary:
  C-S8 polishes NewClientForm.tsx VISUAL ONLY. NEVER touch the form's
  useState, validation, submit handler, or fetch call — those belong to
  Stream D. If a visual change requires touching state, HALT — that's a
  coordination question, not something to resolve inline.

CRITICAL CONTEXT — SSE consumer:
  LiveDependencyGraph (C-S3) subscribes to /api/build/events/<buildId>
  expecting node_added + edge_added events from Stream B. If your component
  is authored before Stream B's R1 lands on main, the graph will just
  receive the existing event types — it should degrade gracefully (no
  errors, just no live accretion). Document this in the component header.

HARD GATES:
  - Stay in the assigned worktree.
  - Do NOT inline any color hex outside lib/styles/theme_tokens.ts.
  - Do NOT inline Sanskrit names — always source from lib/jyotish/asset_names.ts (created in C-S1).
  - Do NOT touch NewClientForm.tsx state / validation / submit / fetch.
  - Do NOT use Anthropic models.

WHEN DONE (queue empty):
  Print the §10 STREAM REPORT block. Exit.

If any blocker hits, STOP and write a one-paragraph blocker.
```
