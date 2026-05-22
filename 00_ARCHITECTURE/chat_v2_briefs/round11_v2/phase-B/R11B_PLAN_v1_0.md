---
canonical_id: R11B_LOOK_AND_FEEL_PHASE_PLAN
project_name: Claude Takeover
version: 1.0
status: CURRENT
phase: R11.B — Visual + Look-and-Feel (project: Claude Takeover)
parent_arc: Claude Takeover — Multi-Provider Parity (R11 v2)
parallel_stream: stream-1 (parallel with R11.CDE stream-2)
owner: Abhisek Mohanty
branch: chat-v2/round11-b-look-and-feel
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11B
execution: sequential-single-stream-via-conductor
authored: 2026-05-22
depends_on_phase: R11.A (must merge to main before R11.B launches)
---

# R11.B — Look-and-Feel Phase

## §1 — Mission

Bring Claude's content rendering inside the Marsys palette. UI restyling — typography, message containers, composer, sidebar, markdown scale — all gated behind `useMultiProviderParity()` (the hook A-S11 introduced). Marsys brand preserved per `NATIVE_RULINGS §1+§2`: gold-on-charcoal palette + brand-cta gold send button + glassmorphic speech-tail user bubble all stay.

R11.B runs **in parallel with R11.CDE** as the Pattern 2+ launch topology. File-scope discipline: R11.B touches UI components + globals.css; CDE touches provider adapters + route.ts. Minimal overlap on ConsumeChatV2.tsx (manageable with surgical edits).

## §2 — Sessions (10 total, sequential within phase)

| # | Session ID | Brief | Flag | Risk |
|---|-----------|-------|------|------|
| 1 | B-S0 | adapter-health-check | FLAGLESS | low |
| 2 | B-S1 | typography-stack | gated by useMultiProviderParity() | low |
| 3 | B-S2 | user-bubble-dimensions | gated | low |
| 4 | B-S3 | message-container-shape | gated | medium |
| 5 | B-S4 | composer-chrome | gated | low |
| 6 | B-S5 | sidebar-chrome | gated | low |
| 7 | B-S6 | markdown-content-typescale | gated | low |
| 8 | B-S7 | inline-citation-parity | gated | medium |
| 9 | B-S8 | brand-preservation-audit | FLAGLESS | low |
| 10 | R11B-MERGE | auto-pr-merge | — | terminal |

## §3 — Carry-forward from NATIVE_RULINGS

- §1 brand preservation — applies to every visual session
- §2 accent stays `var(--brand-gold)` (NOT coral) in composer/send button
- §3 citation idiom — full Claude inline pivot lands in B-S7; CitationSidePanel + CitationCtx retired
- §5 sacred components — never touched (PerMessageDetailsDrawer, PanelMember, Cost Visibility)

## §4 — File scope discipline (for parallel safety with R11.CDE)

R11.B touches:
- `platform/src/app/globals.css` — `.consume-shell` block extensions
- `platform/src/components/chat/AssistantMessage.tsx`
- `platform/src/components/chat/UserMessage.tsx`
- `platform/src/components/chat/MarkdownContent.tsx`
- `platform/src/components/chat/Composer.tsx`
- `platform/src/components/chat/MessageActionBar.tsx`
- `platform/src/components/chat/NumberedCitation.tsx` (B-S7 extension)
- `platform/src/components/consume/ConversationSidebarV2.tsx`
- `platform/src/components/consume/ConsumeChatV2.tsx` (small touch — mount the toggle; retire CitationSidePanel + CitationCtx provider)
- `platform/src/lib/feature_flags.ts` — optionally NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL (one umbrella flag for the visual changes; default false)
- `.github/workflows/deploy.yml` — build-arg for the umbrella flag

R11.B MUST NOT touch:
- `platform/src/lib/providers/**` (R11.A + R11.CDE territory)
- `platform/src/app/api/chat/consume/route.ts` (R11.CDE territory)
- `platform/src/lib/streaming/**` (R11.CDE C-stream territory)
- `platform/src/lib/synthesis/**` (R11.CDE D/E-stream territory)
- Sacred components (PerMessageDetailsDrawer, PanelMember, Cost Visibility)

If R11.CDE merges to main BEFORE R11.B, R11.B's branch rebases against the new main. Conflicts unlikely given the disjoint scope, but if they happen on ConsumeChatV2.tsx, manual conflict resolution + push.

## §5 — Conductor + queue

- Conductor: `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11B_v1_0.md`
- Queue: `00_ARCHITECTURE/CONDUCTOR/session_queue_R11B.yaml` (10 entries)
- Setup + KICKOFF: `phase-B/CLAUDE_CODE_SETUP_PROMPT.md` + `CLAUDE_CODE_KICKOFF_PROMPT.md`

---

*End of R11B_PLAN_v1_0.md.*
