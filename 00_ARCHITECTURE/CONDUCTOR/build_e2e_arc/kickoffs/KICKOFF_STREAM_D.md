# Kickoff prompt — STREAM D (Front-of-funnel + functional polish)

Paste the block below into a fresh Antigravity Claude Code window opened
in `/Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish`.

---

```
You are Claude Code running in Google Antigravity IDE.

ARC: build_e2e_arc · Stream D
PROJECT: MARSYS-JIS
WORKTREE: /Users/Dev/Vibe-Coding/Apps/MadhavFunnelPolish (already on feat/funnel-polish)
MODEL: Gemini Pro or DeepSeek. Anthropic banned.

REQUIRED READS at session open (in order, full files):
  1. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/STREAM_COORDINATION_v1_0.md
  2. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/session_queue.yaml
  3. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/briefs/STREAM_D_FUNNEL_POLISH_v1_0.md
  4. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/VISUAL_CONTRACT_v2.md (Page 1 functional spec only)
  5. /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_e2e_arc/CLAIM_LEDGER.yaml

GOAL:
  Execute all 6 sessions for Stream D (D-S1 through D-S6). Walk the queue
  in declared order. Ship the functional gaps in the New Client → Cockpit
  handoff and verify the Cancel button works (the L1-guard footgun protection).

CRITICAL CONTEXT — NewClientForm boundary:
  D edits state + validation + submit handler + fetch call ONLY. NEVER
  touch JSX layout / className / inline styles / typography — that belongs
  to Stream C. If a functional change requires touching the visual layer,
  HALT — that's a coordination question.

CRITICAL CONTEXT — Cancel button (D-S4):
  Without a working Cancel, the L1 start-guard from Stream A becomes a
  user lockout. This session is essential. If you find no Cancel UI and
  no /api/build/<id>/cancel route, BUILD BOTH. D's button can be unstyled —
  Stream C can polish it later via cherry-pick.

CRITICAL CONTEXT — Places API:
  D-S3 verifies wiring. Three branches per brief (wired+key / wired+no-key /
  not-wired). Pick the right branch based on what grep returns; document
  in commit body.

HARD GATES:
  - Stay in the assigned worktree.
  - Do NOT touch JSX visual elements in NewClientForm.tsx.
  - Do NOT hardcode any API key. If env key missing, document + fallback path.
  - Do NOT use Anthropic models.

WHEN DONE (queue empty):
  Print the §10 STREAM REPORT block. Exit.

If any blocker hits, STOP and write a one-paragraph blocker.
```
