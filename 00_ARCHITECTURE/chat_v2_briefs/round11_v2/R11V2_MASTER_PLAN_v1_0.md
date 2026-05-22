---
canonical_id: CHAT_V2_R11V2_MASTER_PLAN
project_name: Claude Takeover
version: 1.0
status: CURRENT
owner: Abhisek Mohanty
arc: Multi-Provider Parity (R11.A through R11.K)
codename: Claude Takeover (project-level identifier; R11.A/B/CDE phase names + chat-v2/round11-* branches preserved for technical continuity)
execution: sequential-phase-by-phase, sequential-within-phase
authored: 2026-05-22
companion_docs:
  - 00_ARCHITECTURE/CAPABILITY_MATRIX.md
  - 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md
  - 00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md (R11 v1 supersession)
  - 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md (carry-forward rulings)
supersedes:
  - 00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md (status: SUPERSEDED_BY_MULTI_PROVIDER_ROADMAP 2026-05-22)
---

# Claude Takeover — Multi-Provider Parity (Chat V2 R11 v2 Umbrella Master Plan)

> **Project codename:** Claude Takeover. Bringing Marsys consume chat to best-in-class capability across all 5 LLM providers — visual + streaming + caching + adaptive-tool-sequencing parity with Claude.ai, agnostic by construction.

## §1 — Scope

R11 v2 is the umbrella for the **Multi-Provider Parity arc** — a multi-phase workstream that brings Marsys consume chat to best-in-class capability across all 5 active LLM providers (Anthropic, Google, OpenAI, DeepSeek, NVIDIA).

This umbrella plan governs the entire arc R11.A through R11.K. Per-phase plans (`R11A_PLAN_v1_0.md`, `R11B_PLAN_v1_0.md`, ...) detail per-session work within each phase.

Read these three documents in order before reading individual phase plans:
1. `00_ARCHITECTURE/CAPABILITY_MATRIX.md` — what capability lands where, per provider
2. `00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md` — phase sequencing and dependencies
3. This file — umbrella governance + per-phase launch pattern

## §2 — Phase inventory (sequential)

**Active commitment (2026-05-22, amended to drop R11.F):** R11.A through R11.E only. R11.F through R11.K are DEFERRED to a future arc per native scope decision 2026-05-22; their scope content remains in `MULTI_PROVIDER_PARITY_ROADMAP.md` as future planning material.

| Phase | Scope | Sessions | Est. hours | Status |
|---|---|---|---|---|
| **R11.A** | Foundation (capability adapter substrate + 5 provider skeletons + dispatcher + telemetry + runtime toggle) | 14 | 14-18 | **PLAN_AUTHORED — ready to launch** |
| R11.B | Visual + Look-and-Feel parity (Marsys-skin + Claude-rendering) | 10 | 10-13 | PLAN_PENDING (authored just-before-launch after R11.A merges) |
| R11.C | Streaming + Thinking (per-provider) | 8 | 8-12 | PLAN_PENDING |
| R11.D | Caching + Cache-aware prompt layout (per-provider) | 7 | 8-12 | PLAN_PENDING |
| R11.E | Adaptive Tool Sequencing (per-provider) | 10 | 12-16 | PLAN_PENDING — terminal active phase |
| R11.F | Server-Side Tools (web search, fetch, code execution per-provider) | 14 | 16-22 | **DEFERRED 2026-05-22** — future arc |
| R11.G | Memory + Projects + Deep Context | 11 | 12-16 | **DEFERRED 2026-05-22** — future arc |
| R11.H | Learning-Layer Adaptation | ~12-15 | TBD | **DEFERRED 2026-05-22** + BLOCKED on Learning Layer scaffold |
| R11.I | Multi-Modal Input + Voice Output | 14 | 16-22 | **DEFERRED 2026-05-22** — future arc |
| R11.J | Artifacts (live-rendered, editable) | 11 | 12-16 | **DEFERRED 2026-05-22** — future arc |
| R11.K | Computer Use / Agentic Browsing + Image Gen | 13 | 16-22 | **DEFERRED 2026-05-22** — future arc |
| **Active subtotal (R11.A through R11.E)** | **49 sessions** | **52-71 hours** | — | — |
| Full-arc total (incl. deferred R11.F-K, excl. R11.H) | 112 sessions | 124-169 hours | — | future-state reference |

## §3 — Carry-forward of R11 v1 native rulings

The 8 rulings in `00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md` (status: `SUPERSEDED_BUT_REFERENCED_FOR_AUDIT`) remain **authoritative native rulings** for R11 v2. Specifically:

| Ruling | Where it lives in R11 v2 |
|---|---|
| §1 — Brand identity (preserve Marsys palette + components) | EVERY phase honors this |
| §2 — Accent color (keep brand-gold) | R11.B B-S4, B-S5; future UI phases |
| §3 — Citation idiom (full Claude pivot; retire CitationSidePanel) | R11.B B-S7 |
| §4 — Cache breakpoints (canonical Anthropic 4-breakpoint) | R11.D D-S1 (Anthropic); D-S2..D-S4 (other providers) |
| §5 — Sacred components (PerMessageDetailsDrawer + Cost Visibility + PanelMember) | EVERY phase honors this |
| §6 — Conductor STRICT halt + auto-merge override | EVERY phase's Conductor inherits this |
| §7 — Flag rename (renamed again in v2 — see §4 below) | R11.A introduces new top-level flag |
| §8 — Runtime user toggle | R11.A A-S11 |

## §4 — R11 v2 governing flag taxonomy

R11 v2 introduces a **top-level master flag** + per-phase sub-flags + per-capability adapter gates.

### Top-level (NEXT_PUBLIC, env-var)
- `MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` — default **false**. Master kill-switch for the new chat shell. UI toggle gates on this AND a user-pref (per R11.A A-S11 design).

### Per-phase (NEXT_PUBLIC or server-side as appropriate)
Each phase ships at most ONE phase-level flag for the user-perceivable bundle:
- `MARSYS_FLAG_R11B_LOOK_AND_FEEL` — visual changes (R11.B)
- `MARSYS_FLAG_R11C_STREAMING_THINKING` — streaming behavior changes (R11.C)
- `MARSYS_FLAG_R11D_PROMPT_CACHING` — caching (R11.D)
- `MARSYS_FLAG_R11E_AGENTIC_TOOLS` — agentic loops (R11.E)
- `MARSYS_FLAG_R11F_SERVER_TOOLS` — server-side tools (R11.F)
- `MARSYS_FLAG_R11G_MEMORY_PROJECTS` — memory (R11.G)
- `MARSYS_FLAG_R11I_MULTIMODAL` — audio/video (R11.I)
- `MARSYS_FLAG_R11J_ARTIFACTS` — artifacts (R11.J)
- `MARSYS_FLAG_R11K_COMPUTER_USE` — computer use (R11.K)

### Per-capability adapter gates (server-side, finer-grained)
Inside each phase, individual capabilities may have their own gate (e.g., `MARSYS_FLAG_R11D_ANTHROPIC_CACHE_4BP`, `MARSYS_FLAG_R11D_GEMINI_CACHED_CONTENT`). These are surfaced in per-phase plans.

## §5 — Per-phase launch pattern

Every phase follows the same launch ritual:

1. **Phase plan authored** in `00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-<X>/R11<X>_PLAN_v1_0.md`.
2. **Sub-session briefs authored** in the same directory.
3. **Conductor prompt + queue** authored in `00_ARCHITECTURE/CONDUCTOR/`:
   - `CONDUCTOR_PROMPT_R11<X>_v1_0.md`
   - `session_queue_R11<X>.yaml`
4. **Claude Code SETUP + KICKOFF prompts** authored in the phase directory.
5. **Worktree creation** via paste-prompt: `/Users/Dev/Vibe-Coding/Apps/MadhavR11<X>` on branch `chat-v2/round11-<x>-<scope-tag>`.
6. **Conductor run** kicks off; STRICT halt + Cowork triage on failure.
7. **Phase-MERGE** at queue end: push, open PR, auto-merge to main.
8. **Phase-close governance**:
   - Update `CAPABILITY_MATRIX.md` cells from 🚧 to ✓.
   - Update `MULTI_PROVIDER_PARITY_ROADMAP.md` §5 table with `closed_on` + merge SHA.
   - Update this umbrella `R11V2_MASTER_PLAN_v1_0.md` §2 status.
   - Append entry to `SESSION_LOG.md`.
9. **Next phase** authored once native confirms readiness.

## §6 — Inherited amendments (from R11 v1)

R11 v2 re-asserts all five governing amendments inherited from R11 v1, with one addition:

1. **NEXT_PUBLIC build-arg discipline** — HARD GATE at phase-MERGE.
2. **Mount-verification + parent-context integration test** — HARD GATE for visible components.
3. **§M.16 flagless precedent** — purely-additive sessions carry no flag.
4. **Preserved prompt blocks** — R7-S2 footnote and Y-S4 step-marker instructions byte-identical (unless the phase explicitly retires them, e.g., R11.B B-S7 retires the footnote system as part of full Claude citation pivot).
5. **Per-phase deploy.yml coverage gate** — HARD at phase-close.
6. **(NEW for R11 v2) Hide-and-hint fallback policy** — when a provider doesn't support a capability, the UI hides the affordance and shows a "Switch to <stack>" hint. No silent polyfills; no auto-routing without explicit user consent.

## §7 — Multi-stack execution discipline

Every R11 v2 phase that touches provider-specific code MUST:

1. **Test on all 5 providers** that the capability is meant to land on. The adapter pattern means tests exist per-provider; CI runs all five.
2. **Declare hide-and-hint behavior** for providers that don't support the capability (in the brief's "Files in Scope" section).
3. **Honor the manifest** — capability declarations in each provider's `manifest.ts` are the source of truth for UI affordance visibility.

A phase that ships a capability without testing all 5 providers AND without documenting hide-and-hint for unsupported ones is **incomplete** and cannot pass phase-MERGE.

## §8 — Acceptance — R11 v2 active arc close (terminal)

R11 v2 active arc is complete when:
1. R11.A, R11.B, R11.C, R11.D, R11.E have `status: passed`. (R11.F-K deferred; see §2.)
2. `CAPABILITY_MATRIX.md` reflects all shipped cells with ✓ status for the active phases.
3. `MULTI_PROVIDER_PARITY_ROADMAP.md` §5 table shows close dates + merge SHAs for R11.A-E.
4. `CLAUDE.md §E` gets one final entry: "Chat V2 R11 v2 — Multi-Provider Parity (active arc R11.A-E) — COMPLETE on <DATE>."

## §9 — Parallel topology (Pattern 2+)

Per native ruling 2026-05-22 (Cowork chat), the active arc R11.A-E runs in a Pattern 2+ parallel topology to minimize wall-clock:

**Phase 1: R11.A foundation (serial; intra-phase parallel within)**
- R11.A runs in `MadhavR11A` worktree on branch `chat-v2/round11-a-foundation`.
- 14 entries sequential by default, EXCEPT A-S2..A-S6 (5 provider adapter skeletons) which are marked `parallel_group: provider-adapters` and run as a concurrent batch. They touch separate provider directories — collision-free.
- R11A-MERGE auto-merges to main.

**Phase 2: R11.B + R11.CDE parallel streams (after R11.A merges)**
- Stream-1: `MadhavR11B` worktree on `chat-v2/round11-b-look-and-feel`. R11.B Conductor walks 10 entries serially. Touches ONLY UI components + globals.css. R11B-MERGE.
- Stream-2: `MadhavR11CDE` worktree on `chat-v2/round11-cde`. R11.CDE Conductor walks 27 entries serially across R11.C → R11C-MERGE → R11.D → R11D-MERGE → R11.E → R11E-MERGE. Touches ONLY provider adapters + route.ts + streaming/synthesis/observatory.
- File-scope is DISJOINT between streams. Both streams' Conductors run autonomously in their own Antigravity sessions; the native (in Cowork) watches both.

**Merge serialization to main**
- Up to 4 PRs in flight at any moment: R11B-MERGE, R11C-MERGE, R11D-MERGE, R11E-MERGE.
- Each enables auto-merge with squash + delete-branch.
- If R11B-MERGE lands first, R11.CDE's subsequent MERGE entries rebase against new main — likely clean given disjoint scopes; possible conflict only on `ConsumeChatV2.tsx` if both streams edited it. Conflict → Conductor HALT → Cowork triage.

**Wall-clock estimate (Pattern 2+)**
- R11.A: ~10-14h (down from ~14-18h via intra-phase parallel)
- R11.B + R11.CDE concurrent: max(~10-13h, ~28-40h) = ~28-40h
- Total: ~38-54h, spread across ~3.5-4.5 calendar weeks.

**Per-phase launch artifacts**
- R11.A: `phase-A/R11A_PLAN_v1_0.md` + 14 briefs + Conductor + queue + Claude Code prompts (in `phase-A/`)
- R11.B: `phase-B/R11B_PLAN_v1_0.md` + 10 briefs + Conductor + queue + Claude Code prompts (in `phase-B/`)
- R11.CDE composite: `phase-CDE/R11CDE_PLAN_v1_0.md` + 27 briefs + Conductor + queue + Claude Code prompts (in `phase-CDE/`)

---

*End of R11V2_MASTER_PLAN_v1_0.md v1.0.*
*Authored 2026-05-22 in Cowork session that scoped Multi-Provider Parity.*
*Multi-phase arc spanning ~10-14 weeks of autonomous Claude Code time.*
