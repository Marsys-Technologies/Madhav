---
artifact: AIOPS_PHASE_3_MASTER_PLAN_v1_0.md
canonical_id: AIOPS_PHASE_3_MASTER_PLAN
version: 1.0
status: SCOPING_AWAITING_PHASE_2
phase: AIOps-CO (Consume UI Overhaul)
authored_at: 2026-05-14
authored_by: Cowork brainstorm session (Opus 4.7)
predecessors:
  - 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md (Phase 1 — SHIPPED 2026-05-13)
  - 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md (Phase 2 — pending)
execution_rules: 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md (reused from Phase 1)
note: >
  This is a SCOPING master plan only. Executable per-phase briefs
  (CO.0 → CO.7) will be authored after Phase 2 ships, because Phase 3's
  UI implementations consume Phase 2's ModelInteractionEvent contract.
  Authoring the briefs against a hypothetical (rather than shipped)
  contract would risk pre-deciding decisions that should depend on
  Phase 2's actual deliverables.
changelog:
  - v1.0 (2026-05-14): initial scoping; native-approved Q1–Q10 decisions baked in including Q7 expansion (best-in-class visual + behavioral polish IN SCOPE).
---

# AIOps Phase 3 — Consume UI Overhaul
## Master Plan v1.0 (Scoping)

---

## §0 — TL;DR

Phase 3 modernizes the `/consume` chat interface to best-in-class standards
while fixing four specific bugs the native has identified. It also performs
a comprehensive visual + behavioral polish pass — typography, spacing,
color, motion, transitions, scroll behavior, focus management, a11y —
benchmarked against ChatGPT, Claude.ai, Gemini, Perplexity, and Cursor.

Eight sub-phases CO.0 → CO.7. The UX research artifact authored in CO.0 is
the design-level source of truth for everything that follows. Phase 3
consumes Phase 2's `ModelInteractionEvent` stream — the typed event stream
that's the only sane way to fix the reasoning-placement flicker (Bug 3.3).

---

## §1 — The four named bugs

| Bug | Native's description | Files implicated |
|---|---|---|
| 3.1 | Model names appear in the input panel area (next to LLM stack selector / Archeria-style picker) and break alignment when a query is triggered | `ConsumeChat.tsx` input area, `TierPicker.tsx`, `PostAnswerProvenance.tsx` |
| 3.2 | Left side panel doesn't auto-expand on hover / auto-collapse on mouse-out | `ConversationSidebar.tsx`, parent layout |
| 3.3 | Reasoning panel renders at top of chat during streaming, then snaps to correct position (between query and response) when response arrives. Interim layout flicker. | `LiveReasoningCard.tsx`, `StreamingAnswer.tsx`, `ConsumeChat.tsx` parent |
| 3.4 | Reasoning shows for some queries but not others. Should be model-aware: present iff `reasoning_via !== 'none'`. | Same as 3.3 + `single_model_strategy.ts` event emission |

---

## §2 — Best-in-class research (target patterns)

CO.0 authors `00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md` capturing
patterns from these references and explicitly mapping which we adopt:

### Reference set

| Product | Pattern worth borrowing |
|---|---|
| **ChatGPT (o1, o3, GPT-5)** | "Thought for N seconds" collapsible header between query + response; stable DOM slot from submission; live reasoning text streams in |
| **Claude.ai** | Single inline pulse "Claude is thinking…" — minimal but very polished transitions; no reasoning surface for user |
| **Gemini 2.5 (gemini.google.com)** | "Thinking…" with live spinner; reasoning streams into collapsible accordion; auto-collapses on response arrival |
| **Perplexity** | Inline progressive status: "Searching the web…" → "Reading 8 sources…" → "Composing answer…" replaced by final answer with inline source chips |
| **Cursor / Aider** | Tool calls as collapsible cards in chronological order; apply-edits inline; persistent audit trail |
| **Mistral Le Chat** | Model badge per assistant message; expandable for token counts + latency |
| **Phind** | Model picker pinned cleanly to input panel without alignment issues |

### Unifying pattern

The model produces a stream of typed events. The UI has a stable DOM slot
per event type, populated as events arrive. This is exactly what Phase 2's
`ModelInteractionEvent` stream provides. Phase 3's UI builds on it.

### What we adopt

- Stable reasoning slot present from query submission (ChatGPT pattern).
- Live status indicator during processing (Claude / Perplexity).
- Tool calls as collapsible chronological cards (Cursor pattern).
- Per-message model badge with cost/latency (Mistral pattern).
- Hover-expand sidebar (common pattern across most modern chat UIs).
- Smooth transitions, no layout jumps (any best-in-class polish bar).

### What we do NOT adopt (per Q7)

- Slash commands palette (deferred to Phase 3+1).
- Voice input (deferred).
- Multimodal input (deferred).
- Inline artifacts à la Claude.ai (deferred — separate scope).
- Conversation forking / branching (deferred).

---

## §3 — Design philosophy

Five principles:

1. **Stable layout slots from submission.** The DOM positions for every state (user message, status indicator, reasoning panel, tool calls, final answer) exist from the moment the query is submitted. Content streams in; the slot does not move. No layout shift.

2. **Event-driven UI from Phase 2's stream.** Every UI state transition is triggered by a typed `ModelInteractionEvent`. No ad-hoc state derivations from substring matching or polling.

3. **Model-awareness via Phase 2's quirks.** Reasoning slot present iff `model.quirks.reasoning_via !== 'none'`. Tool-call slot present iff `quirks.tool_use_format !== 'none'`. No empty panels.

4. **Visual + behavioral polish as a first-class scope item.** Per native Q7 expansion: typography scale, spacing rhythm, color discipline, motion language, micro-interactions, edge-case states (loading, error, empty, mid-stream) all get dedicated sub-phases (CO.5 visual, CO.6 behavioral). Match best-in-class polish bar (Claude.ai is the closest aesthetic reference).

5. **Forward-only.** Old chat history renders with legacy logic. New messages use the new event stream. No migration of old conversations.

---

## §4 — State machine for chat lifecycle

CO.1 introduces a single state machine driving the chat lifecycle:

```
idle → queued → planning → retrieving → reasoning → tool_calling → composing → complete
                                                                                   ↓
                                                                                error / cancelled
```

State transitions are driven exclusively by `ModelInteractionEvent.status`
events from Phase 2's stream. Each state has a stable UI representation:

| State | UI surface |
|---|---|
| `idle` | Input panel ready, no pending message |
| `queued` | Input shows submitted message; processing badge appears below it |
| `planning` | Status: "Planning the response…" |
| `retrieving` | Status: "Retrieving relevant context…" with count when available |
| `reasoning` | Reasoning panel appears (collapsible, expanded by default during streaming); shows reasoning text live |
| `tool_calling` | Tool-call cards appear chronologically below reasoning |
| `composing` | Final answer area starts populating; reasoning auto-collapses (still expandable) |
| `complete` | Final state with per-message metadata badge |
| `error` | Error state with retry button |
| `cancelled` | User-cancelled with regenerate button |

---

## §5 — Sub-phase arc (CO.0 → CO.7)

| Phase | Scope | Notes |
|---|---|---|
| **CO.0** | Branch + UX research catalog (`UX_RESEARCH_v1_0.md`) + design spec (`CONSUME_UI_SPEC_v1_0.md`) | Design-doc-only; no code |
| **CO.1** | State machine + event subscription wiring. Replace ad-hoc state in `ConsumeChat.tsx` + `StreamingAnswer.tsx` with a `useChatLifecycle` hook that subscribes to Phase 2's stream. | Foundation for all subsequent work |
| **CO.2** | Bug 3.1: input panel cleanup. Remove model names from input area; reposition stack selector cleanly; per-message model badge in `PostAnswerProvenance`-style capsules at end of response. | Visible UX improvement |
| **CO.3** | Bugs 3.3 + 3.4: reasoning panel anchored slot; model-aware emission. `LiveReasoningCard` rewritten; uses Phase 2's `reasoning_delta` events. | The core fix |
| **CO.4** | Bug 3.2: sidebar UX. Hover-expand / hover-collapse / click-to-pin. Smooth transitions; mobile fallback. | `ConversationSidebar.tsx` refactor |
| **CO.5** | Visual design pass. Typography scale, spacing rhythm, color palette discipline, motion language, component library audit. Match Claude.ai aesthetic bar. | Q7 expansion — first-class scope |
| **CO.6** | Behavioral polish. Transitions, scroll-anchoring during streaming, focus management, keyboard shortcuts, error states, empty states, mid-stream interrupts, accessibility (WCAG 2.1 AA). | Q7 expansion — first-class scope |
| **CO.7** | Cutover. Behind `CONSUME_UI_V2_ENABLED` flag default false through CO.6; flip in CO.7. Old components stay until follow-up flag-removal PR. 48h watch on engagement metrics. | Same playbook as Phase 1 CP.5 |

---

## §6 — Visual design pass (CO.5 detail)

Specific visual targets (informed by Claude.ai's aesthetic discipline):

- **Typography.** Single typeface family (current Madhav stack). Type scale: 5–6 distinct sizes maximum. Line heights consistent. No font-weight inflation (3 weights max: regular, medium, semibold).
- **Spacing rhythm.** 4px or 8px base grid. Component padding consistent. Vertical rhythm aligned.
- **Color palette.** Limited to existing Tailwind tokens + theme CSS variables. No new colors. Audit for hardcoded hex values; replace with tokens.
- **Motion language.** Spring physics for layout shifts. Ease-out for entries. Ease-in-out for transitions. Duration scale: 150ms (micro), 250ms (standard), 400ms (entry/exit). No animations exceed 400ms.
- **Component library audit.** Identify every UI primitive in consume/. Consolidate duplicates (e.g., if there are 3 different button styles, pick one). Document the kept set in `CONSUME_UI_SPEC_v1_0.md`.
- **Iconography.** Use one icon set throughout (likely Lucide if it's already in deps). No mixed icon styles.
- **Cards + chrome.** Border radius consistent. Shadow scale 2-step (subtle, prominent). Background opacity discipline.

Acceptance: side-by-side screenshots of before / after, with the after looking like it could be on Claude.ai or chat.openai.com.

---

## §7 — Behavioral polish (CO.6 detail)

Specific behavioral targets:

- **Scroll anchoring during streaming.** When response is streaming and user has scrolled up to read prior context, do NOT auto-scroll. When user is at bottom and response streams, auto-follow. Match ChatGPT's behavior precisely.
- **Focus management.** Submit query → focus moves to assistant message area. ESC → focus returns to input. Cmd+K → focus input from anywhere.
- **Keyboard shortcuts.** Cmd+Enter to submit (already may exist). Esc to collapse all expanded panels. Cmd+/ for help.
- **Mid-stream interrupts.** "Stop generating" button visible during streaming. Cancellation propagates through Phase 2's stream cleanly.
- **Error states.** Network error → retry button. Validator failure → existing `ValidatorFailureView` reused. Provider auth_fail → clear error message with stack-switch suggestion.
- **Empty states.** Empty conversation → `EmptyState.tsx` already exists but audit + polish.
- **Loading skeletons.** Where appropriate, show skeletons instead of spinners. Match Claude.ai's polish bar.
- **Accessibility.** WCAG 2.1 AA: color contrast, keyboard nav, focus rings, ARIA, semantic HTML, screen-reader announcements for state changes. `aria-live="polite"` on the status indicator.
- **Mobile (viewport ≤ 640px).** Sidebar collapses to overlay; input panel sticks to bottom; reasoning panel collapses by default.

Acceptance: a11y audit `OUTSTANDING: 0`. CLS (Cumulative Layout Shift) < 0.05 during normal interaction. Keyboard-only nav covers every interactive element.

---

## §8 — Out of scope (per Q7)

Explicitly NOT in Phase 3 v1:

- Slash command palette
- Voice input
- Multimodal input (image upload, file upload beyond what exists today)
- Inline artifacts (Claude.ai-style)
- Conversation forking / branching
- Real-time collaboration

Captured here so future-Phase 3+1 brainstorms can pick them up.

---

## §9 — Acceptance criteria themes

Per sub-phase:

- **CO.0:** UX_RESEARCH_v1_0.md + CONSUME_UI_SPEC_v1_0.md authored with explicit pattern adoption decisions.
- **CO.1:** All ad-hoc state derivations in `ConsumeChat.tsx` + `StreamingAnswer.tsx` replaced by `useChatLifecycle`; subscribes to Phase 2's stream; state machine tests.
- **CO.2:** Bug 3.1 closed. Screenshot diffs in evidence dir. No model names in input area; capsules at end of response.
- **CO.3:** Bugs 3.3 + 3.4 closed. No layout shift during state transitions (CLS measured). Reasoning slot present iff `reasoning_via !== 'none'`.
- **CO.4:** Bug 3.2 closed. Sidebar hover-expand verified across all interaction patterns.
- **CO.5:** Visual audit complete; before/after screenshots; no new colors; type scale ≤ 6.
- **CO.6:** Behavioral targets met; a11y audit passes WCAG 2.1 AA; CLS < 0.05.
- **CO.7:** `CONSUME_UI_V2_ENABLED=true` in production; 48h engagement metrics stable.

---

## §10 — Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Phase 2's event stream doesn't match what Phase 3's spec assumes | HIGH | CO.0 authors the spec AFTER Phase 2 ships; briefs authored against real contract |
| Visual polish drift — too much subjective opinion | MED | CO.5 anchored to specific reference (Claude.ai); side-by-side comparison enforced in acceptance |
| Mobile viewport breaks discovered late | MED | CO.6 includes explicit mobile target ≤ 640px; tests in BrowserStack or local emulator |
| Old chat history rendering breaks with new components | HIGH | Forward-only commitment from §3 principle #5; legacy renderer preserved as fallback |
| Panel mode (3 LLMs in parallel) UI design ambiguous | MED | Defer to CO.0 design doc; not pre-decided in this scoping plan |
| Hover-expand sidebar breaks click-to-navigate on touch devices | MED | CO.4 includes explicit touch-target handling; click-to-pin behavior preserved |
| Reasoning rendering for Bayesian / DBN content (M5-related) breaks | LOW | M5 outputs render through same answer view as other content; CO.3 doesn't change response rendering, only reasoning panel placement |

---

## §11 — Branch + scope boundaries

**Branch:** `feature/aiops-phase-3-consume-ui`, cut from main AFTER Phase 2 merges.

```yaml
may_touch:
  - platform/src/components/consume/**           # primary work
  - platform/src/components/chat/**              # shared chat primitives
  - platform/src/components/shared/**            # if shared primitives need updates
  - platform/src/app/api/chat/consume/**         # SSE stream shape if needed (small surface)
  - platform/src/app/(consume)/**                # routing if any
  - platform/src/styles/**                       # if a styles dir exists
  - 00_ARCHITECTURE/aiops/phase_3/**             # docs
  - .github/workflows/deploy.yml                 # add CONSUME_UI_V2_ENABLED env var (CO.7)
  - platform/src/lib/config/feature_flags.ts     # add CONSUME_UI_V2_ENABLED

must_not_touch:
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - platform/src/lib/adapters/**                 # Phase 2 — sealed
  - platform/src/lib/synthesis/**                # Phase 2 territory
  - platform/src/lib/models/**                   # Phase 1 + 2 territory
  - platform/src/lib/components/observatory/**   # sealed
  - platform/src/lib/aiops/**                    # Phase 1 — sealed
  - platform/src/app/(super-admin)/aiops/**      # sealed
  - 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
  - 00_ARCHITECTURE/aiops/phase_briefs/**        # Phase 1 — sealed
  - 00_ARCHITECTURE/aiops/phase_2/**             # Phase 2 territory
```

---

## §12 — Dependencies on Phase 2

Phase 3 cannot start CO.1 (state machine wiring) until Phase 2 ships its
`ModelInteractionEvent` stream. The CO.0 design doc IS possible in
parallel — gathering UX research, sketching the spec, identifying which
components need refactor. Concretely:

- **CO.0 may start when:** Phase 2's AD.3 closes (adapter implementations exist; we know the event shape).
- **CO.1 may start when:** Phase 2's AD.5 closes (production-confirmed adapter contract).
- **CO.2–CO.7 sequence after CO.1.**

Recommended sequence:

1. Phase 2 runs to completion (AD.0 → AD.5; ~1 working day).
2. Native reviews Phase 2 outputs.
3. Author Phase 3 executable briefs (CO.0 → CO.7) against the actual Phase 2 contract.
4. Trigger Phase 3.

---

## §13 — Forward-look (Phase 3+1 and beyond)

Items deferred from Phase 3 v1, captured for future scoping:

- Slash commands palette (Cmd+/)
- Voice input
- Multimodal input
- Inline artifacts (Claude-style)
- Conversation forking / branching
- Real-time collaboration
- Custom themes
- Persistent search across conversations

Each can become its own mini-phase when prioritized.

---

## §14 — Native acceptance checklist (review before authoring executable briefs)

When Phase 2 ships and you're ready to commission Phase 3's briefs:

- [ ] The eight-sub-phase split (CO.0 → CO.7) covers all the bugs + Q7 polish
- [ ] CO.5 visual + CO.6 behavioral splits are the right granularity
- [ ] Reference set in §2 captures the products I'd benchmark against
- [ ] What we adopt / don't adopt in §2 is correct
- [ ] State machine in §4 is the right model
- [ ] Forward-only commitment for old chat history is acceptable
- [ ] Branch name `feature/aiops-phase-3-consume-ui` is acceptable
- [ ] Risk register is complete enough; no missing risks

When checked, native confirms and Cowork authors the eight executable
briefs against Phase 2's shipped contract.

---

*End of AIOPS_PHASE_3_MASTER_PLAN_v1_0.md (Scoping)*
*Executable briefs deferred until Phase 2 ships.*
