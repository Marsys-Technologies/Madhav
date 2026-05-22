---
canonical_id: R11CDE_COMPOSITE_PHASE_PLAN
project_name: Claude Takeover
version: 1.0
status: CURRENT
phase: R11.C + R11.D + R11.E composite (project: Claude Takeover)
parent_arc: Claude Takeover — Multi-Provider Parity (R11 v2)
parallel_stream: stream-2 (parallel with R11.B stream-1)
owner: Abhisek Mohanty
branch: chat-v2/round11-cde (one shared branch; intermediate MERGEs push to phase-specific branches at merge time)
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE
execution: sequential-single-stream-via-conductor, 27 entries, 3 intermediate PRs
authored: 2026-05-22
depends_on_phase: R11.A (must merge to main before R11.CDE launches)
---

# R11.CDE — Composite Phase (Streaming + Caching + Adaptive Tools)

## §1 — Mission

Three phases (R11.C, R11.D, R11.E) walked by one Conductor in one worktree. Per-phase MERGE entries push intermediate PRs to main so granular rollback is preserved. This is **stream-2** of the Pattern 2+ parallel launch.

R11.C: Streaming + Thinking parity per-provider (8 entries: 7 impl + R11C-MERGE).
R11.D: Prompt caching across all 5 providers (8 entries: 7 impl + R11D-MERGE).
R11.E: Adaptive Tool Sequencing — agentic loops per-provider (11 entries: 10 impl + R11E-MERGE).

Total: **27 entries**, ~36-50 hours autonomous Claude Code time.

## §2 — Sessions (27 total, sequential)

### R11.C — Streaming + Thinking (8 entries)

| # | Session ID | Brief slug | Flag | Risk |
|---|-----------|-----------|------|------|
| 1 | C-S0 | streaming-capability-check | FLAGLESS | low |
| 2 | C-S1 | pre-token-thinking-indicator | FLAGLESS | low |
| 3 | C-S2 | smooth-stream-rate-target | MARSYS_FLAG_R11C_SMOOTH_STREAM_V3 (server) | medium |
| 4 | C-S3 | ext-thinking-auto-collapse | FLAGLESS | low |
| 5 | C-S4 | adaptive-thinking-budgets | per-provider, FLAGLESS | medium |
| 6 | C-S5 | inline-tool-cards | MARSYS_FLAG_R11C_TOOL_CARDS (NEXT_PUBLIC) | medium |
| 7 | C-S6 | stop-and-retain-partial | FLAGLESS | low |
| 8 | R11C-MERGE | auto-pr-merge | — | terminal |

### R11.D — Caching (8 entries)

| # | Session ID | Brief slug | Flag | Risk |
|---|-----------|-----------|------|------|
| 9 | D-S0 | caching-capability-check | FLAGLESS | low |
| 10 | D-S1 | anthropic-4bp-cache | MARSYS_FLAG_R11D_ANTHROPIC_CACHE (server) | medium |
| 11 | D-S2 | gemini-cachedcontent | MARSYS_FLAG_R11D_GEMINI_CACHE (server) | medium |
| 12 | D-S3 | openai-automatic-cache-telemetry | FLAGLESS | low |
| 13 | D-S4 | deepseek-implicit-cache-telemetry | FLAGLESS | low |
| 14 | D-S5 | cache-aware-prompt-layout | MARSYS_FLAG_R11D_PROMPT_LAYOUT (server) | medium |
| 15 | D-S6 | observatory-cache-tile | FLAGLESS | low |
| 16 | R11D-MERGE | auto-pr-merge | — | terminal |

### R11.E — Adaptive Tool Sequencing (11 entries)

| # | Session ID | Brief slug | Flag | Risk |
|---|-----------|-----------|------|------|
| 17 | E-S0 | tool-loop-capability-check | FLAGLESS | low |
| 18 | E-S1 | anthropic-stop-reason-loop | MARSYS_FLAG_R11E_ANTHROPIC_LOOP (server, default false) | HIGH |
| 19 | E-S2 | gemini-function-calls-loop | MARSYS_FLAG_R11E_GEMINI_LOOP (server, default false) | HIGH |
| 20 | E-S3 | openai-tool-calls-loop | MARSYS_FLAG_R11E_OPENAI_LOOP (server, default false) | HIGH |
| 21 | E-S4 | deepseek-loop | MARSYS_FLAG_R11E_DEEPSEEK_LOOP (server, default false) | medium |
| 22 | E-S5 | nvidia-loop | MARSYS_FLAG_R11E_NVIDIA_LOOP (server, default false) | medium |
| 23 | E-S6 | interleaved-text-tool | FLAGLESS (handled in per-provider loops above) | medium |
| 24 | E-S7 | tool-error-recovery | FLAGLESS | medium |
| 25 | E-S8 | iteration-cap-safety | FLAGLESS | low |
| 26 | E-S9 | tool-loop-observability | FLAGLESS | low |
| 27 | R11E-MERGE | auto-pr-merge | — | terminal |

## §3 — Branch + PR strategy

Single working branch `chat-v2/round11-cde`. At each phase-MERGE entry:
- R11C-MERGE: `git push -u origin chat-v2/round11-cde-c` (cherry-pick or push as new branch); open PR #N; auto-merge. Then in-place stays on chat-v2/round11-cde for D.
- R11D-MERGE: same pattern with `chat-v2/round11-cde-d`.
- R11E-MERGE: same with `chat-v2/round11-cde-e` — the terminal merge of stream-2.

ALTERNATIVE (simpler if cherry-pick is fragile): single composite branch `chat-v2/round11-cde` for all 27 sessions, single composite PR at R11E-MERGE only (no intermediate MERGEs). The executor decides at R11C-MERGE which pattern is operationally easier. Document in commit body.

## §4 — File-scope discipline (stream-2 vs stream-1)

R11.CDE touches:
- `platform/src/lib/providers/**` — all 5 provider adapters (D/E heavy editing)
- `platform/src/lib/streaming/smooth_stream.ts` (C-S2)
- `platform/src/components/chat/ReasoningProgress.tsx`, `ToolCallCard.tsx` (C-S3, C-S5)
- `platform/src/app/api/chat/consume/route.ts` (heavy editing throughout)
- `platform/src/lib/synthesis/**` (prompt layout, agentic loop integration)
- `platform/src/lib/observatory/**` (cache + tool-loop telemetry)
- `platform/src/lib/config/feature_flags.ts` (multiple new flags)
- `.github/workflows/deploy.yml` (NEXT_PUBLIC flag build-args where applicable — most R11.CDE flags are server-side though)

R11.CDE MUST NOT touch:
- UI components: `AssistantMessage.tsx`, `UserMessage.tsx`, `MarkdownContent.tsx`, `Composer.tsx`, `MessageActionBar.tsx`, `NumberedCitation.tsx`, `ConversationSidebarV2.tsx` (R11.B stream-1 territory)
- `platform/src/app/globals.css` (R11.B territory)
- Sacred components per NATIVE_RULINGS §5
- Phase 4C files

## §5 — Conductor + queue

- Conductor: `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11CDE_v1_0.md`
- Queue: `00_ARCHITECTURE/CONDUCTOR/session_queue_R11CDE.yaml` (27 entries)
- Setup + KICKOFF: `phase-CDE/CLAUDE_CODE_SETUP_PROMPT.md` + `CLAUDE_CODE_KICKOFF_PROMPT.md`

---

*End of R11CDE_PLAN_v1_0.md.*
