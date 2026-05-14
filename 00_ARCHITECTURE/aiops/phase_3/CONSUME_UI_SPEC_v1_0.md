---
artifact: CONSUME_UI_SPEC_v1_0.md
canonical_id: AIOPS_PHASE3_CONSUME_UI_SPEC
version: 1.0
status: CURRENT
authored_at: 2026-05-14
authored_by: CO.0 (AIOPS_CO_0 session)
phase: CO.0 — UX research + design spec authoring
purpose: >
  Target-state specification for every component in the Consume UI overhaul.
  Each entry drives one or more sub-phases CO.1–CO.6. CO.N implementors must
  read this spec before touching any file listed under "Files implicated."
  Design rationale lives in UX_RESEARCH_v1_0.md §1–§5.
changelog:
  - v1.0 (2026-05-14): initial authoring from CO.0. 10 component entries + §X tokens audit.
---

# AIOps Phase 3 — Consume UI Spec v1.0

---

## Overview

This spec covers ten component target states:

| # | Component | Bug fixed | Phase |
|---|---|---|---|
| C1 | Status indicator | — | CO.1 |
| C2 | Input panel (composer area) | Bug 3.1 | CO.2 |
| C3 | Stack selector | Bug 3.1 | CO.2 |
| C4 | Per-message metadata badge | Bug 3.1 | CO.2 |
| C5 | Reasoning slot | Bugs 3.3, 3.4 | CO.3 |
| C6 | Tool calls panel | — | CO.3 |
| C7 | Sidebar | Bug 3.2 | CO.4 |
| C8 | Message bubble | — | CO.5 |
| C9 | Scroll behavior | — | CO.6 |
| C10 | Focus management | — | CO.6 |

---

## C1 — Status indicator

**Implementing sub-phase:** CO.1

**Files implicated:**
- `platform/src/components/consume/ConsumeChat.tsx` (host)
- `platform/src/components/consume/StatusBadge.tsx` (new, CO.1)
- `platform/src/hooks/useChatLifecycle.ts` (new, CO.1)

**Current behavior:**
There is no dedicated status indicator. During streaming, the only feedback is
a pulsing dot + text inside `LiveReasoningCard` ("Thinking…") and the
`PendingAssistantBubble` (animated dots). Neither maps to the actual pipeline
stage; both disappear or shift when content begins rendering.

**Target behavior:**
A `StatusBadge` component renders inline between the user message and the
pending assistant area from the moment a query is submitted. It displays the
current pipeline stage label (see UX_RESEARCH_v1_0.md §4 label table) driven
by `ModelInteractionEvent` status events via the `useChatLifecycle` hook. On
`status: complete` or when answer text begins (`text_delta`), the badge
dissolves with a 250ms ease-out fade. The badge uses `aria-live="polite"` and
`aria-atomic="true"` so screen readers announce each stage change without
interrupting reading.

**Acceptance hook (CO.1):**
`StatusBadge` renders for every pipeline stage from `queued` through
`composing`; dissolves on `complete`; never renders after streaming ends.

---

## C2 — Input panel (composer area)

**Implementing sub-phase:** CO.2

**Files implicated:**
- `platform/src/components/consume/ConsumeChat.tsx` (toolbar strip)
- `platform/src/components/chat/Composer.tsx` (read-only; LOCKED item #3)

**Current behavior (Bug 3.1):**
The input toolbar strip under the composer shows the `ModelStylePicker`
(stack selector + style picker) on the left, and to its right an
inline `<span>` that displays `lastAssistantMeta` — a string containing
the full model name, provider label, and planner details. This span
appears inside the toolbar at the same visual level as the controls,
causing alignment breakage on narrower viewports and visual clutter during
query entry. Model information belongs in the post-response metadata capsule,
not the input area.

**Target behavior:**
The `lastAssistantMeta` span is removed from the input toolbar. Model + cost
+ latency information migrates to the per-message metadata badge (C4). The
toolbar strip retains: `ModelStylePicker` (left), control buttons (right:
Life Events toggle, TierPicker if super_admin, Panel mode if enabled, Trace
button if super_admin). All controls remain vertically centered, consistent
height, no spillover on mobile. The Trace button stays in the header via
`ChatShell headerActions` per the AGENTS.md LOCKED item #2 — it does NOT
move to the toolbar.

**Acceptance hook (CO.2):**
No model-name or provider-label text visible in the composer toolbar at any
viewport width; screenshot diff confirms clean alignment.

---

## C3 — Stack selector

**Implementing sub-phase:** CO.2

**Files implicated:**
- `platform/src/components/chat/ModelStylePicker.tsx`
- `platform/src/components/consume/ConsumeChat.tsx`

**Current behavior:**
`ModelStylePicker` renders the stack selector and style picker as a compact
control group. It is correctly positioned in the input toolbar. However, the
adjacent `lastAssistantMeta` span (Bug 3.1) creates misalignment because the
span's content width varies (short stack label vs. long model+planner string).
On narrow viewports the span wraps or overflows the toolbar boundary.

**Target behavior:**
After removing `lastAssistantMeta` from the toolbar (C2), `ModelStylePicker`
stands as the sole left-side control. Its internal layout remains unchanged;
CO.2 only ensures consistent alignment across all viewports by removing the
variable-width sibling. `ModelStylePicker` is disabled during streaming and
when viewing archived branches (existing behavior preserved). The component
renders with `hidden sm:flex` (or equivalent) for mobile ergonomics — on
`viewport < 640px` the stack label may truncate to icon-only (assess in CO.2;
use Phind's pattern as reference).

**Acceptance hook (CO.2):**
`ModelStylePicker` aligns consistently at mobile (375px), tablet (768px), and
desktop (1440px) breakpoints; no overflow or wrapping.

---

## C4 — Per-message metadata badge

**Implementing sub-phase:** CO.2

**Files implicated:**
- `platform/src/components/consume/PostAnswerProvenance.tsx` (evolve, not replace)
- `platform/src/components/consume/MessageMetaBadge.tsx` (new, CO.2)
- `platform/src/components/chat/AssistantMessage.tsx`

**Current behavior:**
`PostAnswerProvenance` renders a pill cluster (N models · N sources · N signals)
below the last assistant message when provenance SSE data is available. It does
NOT show the synthesis model name, cost in USD, or latency. Model information
is displayed in the input toolbar `lastAssistantMeta` span (Bug 3.1), which is
the wrong location. Historical messages show no metadata at all.

**Target behavior:**
A `MessageMetaBadge` component attaches to each completed assistant message,
rendering compact capsules:
- Model label (e.g., "Gemini 2.5 Pro")
- Provider label (e.g., "Google")
- Cost in USD (e.g., "$0.003")
- Latency in seconds (e.g., "4.2s")
The data comes from the `finish` event's `ModelInteraction.usage` (cost, latency)
and `ModelInteraction.modelId` (model + provider lookup) emitted by Phase 2's
stream. For messages produced before CO.7, the badge is absent (forward-only
commitment, UX_RESEARCH_v1_0.md §5). `PostAnswerProvenance` is retained and
rendered below `MessageMetaBadge` when provenance data is available — the two
are siblings, not replacements. Badge expands on click to show full token
breakdown (inputTokens, outputTokens, reasoningTokens, cacheReadTokens).

**Acceptance hook (CO.2):**
`MessageMetaBadge` renders on every new assistant message in flag-ON path;
absent from historical messages; `PostAnswerProvenance` pills still present.

---

## C5 — Reasoning slot

**Implementing sub-phase:** CO.3

**Files implicated:**
- `platform/src/components/consume/LiveReasoningCard.tsx` (refactor)
- `platform/src/components/consume/ConsumeChat.tsx` (placement logic)
- `platform/src/hooks/useChatLifecycle.ts` (event source)

**Current behavior (Bugs 3.3 + 3.4):**
Bug 3.3: `LiveReasoningCard` is rendered unconditionally at the top of the
message list (`session.isStreaming && <LiveReasoningCard ... />`), above all
messages. When the response arrives and streaming ends, the component either
disappears or re-renders in a different DOM position — causing visible layout
shift (CLS violation).

Bug 3.4: `LiveReasoningCard` renders whenever `session.isStreaming` is true,
regardless of whether the active model produces reasoning. Models with
`reasoning_via: 'none'` cause the card to show "Thinking…" placeholder
indefinitely with no actual content, then disappear — a false affordance.

**Target behavior:**
`LiveReasoningCard` is anchored in the DOM as a stable slot immediately below
the in-flight user message and above the answer area from query submission
onwards. It does not move when the `composing` state begins. Presence is gated
on `model.quirks.reasoning_via !== 'none'` — checked via `useChatLifecycle`
before rendering. On `composing` state entry, the card auto-collapses (still
expandable). On `complete`, the card remains collapsed but accessible. If no
`reasoning_delta` events were emitted for a model that has `reasoning_via !==
'none'`, the card renders a minimal "Reasoning not surfaced" placeholder rather
than the "Thinking…" indefinitely. CLS target: < 0.05 during a full turn.

**Acceptance hook (CO.3):**
No layout shift during reasoning → composing transition (measured by
PerformanceObserver CLS); reasoning slot absent when `reasoning_via === 'none'`.

---

## C6 — Tool calls panel

**Implementing sub-phase:** CO.3

**Files implicated:**
- `platform/src/components/consume/ToolCallsPanel.tsx` (new)
- `platform/src/hooks/useChatLifecycle.ts`
- `platform/src/components/consume/ConsumeChat.tsx`

**Current behavior:**
Tool calls and tool results are not surfaced in the Consume UI at all. The
`ModelInteractionEvent` stream emits `tool_call` and `tool_result` events
(Phase 2 contract), but ConsumeChat discards them without rendering.

**Target behavior:**
A `ToolCallsPanel` component renders as a collapsible chronological list of
tool-call cards between the reasoning slot and the answer area. Each card
shows: tool name, abbreviated args (expandable to full JSON), and the
result summary (first 200 chars, expandable). Cards appear in emission order
as `tool_call` events arrive and are updated with result data when the
matching `tool_result` event arrives (matched by `callId`). The panel is
present only when at least one `tool_call` event has been emitted during
the current turn. At `composing` state, the panel collapses (still
expandable). At `complete`, the panel persists collapsed. For `client` tier,
the panel is hidden by default (collapsed, non-expandable) to avoid
information overload; `acharya_reviewer` and `super_admin` see it expanded.
Tier gating uses the existing `activeTier` from ConsumeChat's state.

**Acceptance hook (CO.3):**
Tool-call cards render for queries that trigger tools; absent for direct
synthesis queries; tier-gated visibility confirmed.

---

## C7 — Sidebar

**Implementing sub-phase:** CO.4

**Files implicated:**
- `platform/src/components/chat/ConversationSidebar.tsx`
- `platform/src/components/chat/ChatShell.tsx`
- `platform/src/components/consume/ConsumeChat.tsx`

**Current behavior (Bug 3.2):**
The sidebar is toggled only by clicking the `PanelLeft` icon button or
pressing `⌘B`. There is no hover-expand / hover-collapse behavior. The sidebar
does not auto-expand when the cursor hovers the left edge, and it does not
auto-collapse when the cursor leaves. On desktop, the sidebar state is
sticky — if collapsed, it stays collapsed until the user explicitly toggles.

**Target behavior:**
`ChatShell` gains hover-expand semantics for the desktop sidebar:
- A 4px-wide "hover strip" is always visible at the left edge when the sidebar
  is collapsed. Hovering this strip expands the sidebar with a 250ms ease-out
  transition. A short 150ms hover intent delay prevents accidental triggers.
- Moving the cursor outside the expanded sidebar (or its hover strip) after
  more than 100ms collapses the sidebar automatically (250ms ease-in), unless
  the user has "pinned" it.
- Clicking anywhere inside the expanded sidebar while it was hover-expanded
  "pins" it (sidebar stays expanded until the user clicks `PanelLeft` or
  presses `⌘B` to explicitly collapse).
- Pin state is NOT persisted to localStorage (intentionally ephemeral per
  session; native decision; revisit in Phase 3+1).
- Mobile (viewport ≤ 640px): sidebar renders as an overlay sheet (existing
  behavior via `mobileSidebarOpen`); hover behavior does NOT apply on touch
  devices (detected via CSS `@media (hover: none)`).
- Existing LOCKED item #1 (`desktopSidebarCollapsed` initial state) is
  respected — only the hover behavior is new, not the initial state.

**Acceptance hook (CO.4):**
Hover-expand triggers within 150ms hover-intent on the strip; hover-collapse
triggers within 100ms of leaving; click-pin prevents auto-collapse.

---

## C8 — Message bubble

**Implementing sub-phase:** CO.5

**Files implicated:**
- `platform/src/components/chat/AssistantMessage.tsx`
- `platform/src/components/consume/StreamingAnswer.tsx`
- `platform/src/styles/` (if global CSS; otherwise inline Tailwind)

**Current behavior:**
User messages render as right-aligned rounded rectangles (`rounded-2xl
border border-border/80 bg-muted/50 px-4 py-2.5`). Assistant messages
render as full-width prose via `StreamingMarkdown`. The visual contrast
between user bubbles and assistant prose is inconsistent with best-in-class
polish: user bubbles use different border-radius than surrounding cards;
line-height and spacing vary by component; no consistent vertical rhythm.

**Target behavior:**
- **User bubbles:** retain right-alignment and rounded treatment; standardize
  to `rounded-2xl`, `max-w-[72%]`, `px-4 py-3`, `bg-muted/60`, `text-sm`
  (body size from §3 type scale). Border softened to `border-border/50`.
- **Assistant prose:** full-width, `text-sm` body size, consistent `leading-7`
  (comfortable for long Jyotish content). Heading levels in markdown get the
  type-scale sizes from §3. Code blocks get `font-mono text-[11px]` and a
  subtle `bg-muted/40` background.
- **Vertical rhythm:** 8px base grid throughout the message list. User messages
  separated from assistant messages by `py-3`; same-role consecutive messages
  share tighter `py-1.5` gap (not applicable in current turn model but future-
  proofed in layout).
- **Streaming state:** during `composing`, the assistant area uses the same
  styling as complete messages — no visual difference between streaming and
  complete prose (just the presence of the streaming cursor).

**Acceptance hook (CO.5):**
Side-by-side screenshot comparison (before / after CO.5) shows consistent
spacing, matching Claude.ai's reading density; no font-size or weight
regressions.

---

## C9 — Scroll behavior

**Implementing sub-phase:** CO.6

**Files implicated:**
- `platform/src/hooks/useScrollAnchor.ts`
- `platform/src/components/consume/ConsumeChat.tsx`

**Current behavior:**
`useScrollAnchor` tracks `isAtBottom` within a 96px threshold. When streaming
is active and the user is at the bottom, the hook auto-scrolls to the new
content via the `bottomRef` intersection observer. However, if the user scrolls
up to read prior context during a streaming response, the current
implementation continues to auto-scroll, pulling the user back to the bottom.
This is the opposite of ChatGPT's semantics.

**Target behavior (ChatGPT semantics):**
When the user scrolls up more than 96px from the bottom during active streaming,
auto-scroll is suspended. A "Jump to bottom" button appears (already implemented
via `ScrollToBottomButton`) — its behavior is unchanged. When the user clicks
"Jump to bottom" or scrolls back within 96px of the bottom, auto-scroll resumes.
When streaming ends (`status: complete`), auto-scroll is NOT re-enabled
automatically — the user's scroll position is respected. When the user submits
a new query, scroll anchors to the bottom before the new user message renders,
then auto-scroll resumes for the new turn.

`useScrollAnchor` gains two new exported values: `suspendedByUser` (boolean)
and `resumeScroll` (callback). ConsumeChat uses these to conditionally pass
them to the "Jump to bottom" button.

**Acceptance hook (CO.6):**
Scrolling up during streaming suspends auto-scroll; submitting a new query
resets scroll to bottom; CLS < 0.05 throughout.

---

## C10 — Focus management

**Implementing sub-phase:** CO.6

**Files implicated:**
- `platform/src/components/consume/ConsumeChat.tsx`
- `platform/src/hooks/useHotkeys.ts`
- `platform/src/components/chat/Composer.tsx` (read-only; LOCKED item #3)

**Current behavior:**
After submit, focus stays in the composer textarea (because `composerRef.focus()`
is called when `session.isStreaming` becomes false — i.e., on stream end, not
on submit). The `useHotkeys` hook handles `⌘⇧O` (new chat), `⌘B` (sidebar),
`⌘/` (shortcuts), and `Escape` (stop streaming). There is no explicit focus
management on query submit (focus-to-assistant-area) or Escape-to-input
behavior.

**Target behavior:**
- **Submit → assistant area:** when the user submits a query, focus moves to
  the in-flight assistant area (the `StatusBadge` or the pending bubble) so
  screen readers announce the processing state. This is implemented by setting
  `tabIndex={-1}` on the pending area and programmatically calling `.focus()`
  after submission. Sighted users see no visible focus ring change (use
  `focus:outline-none` on the pending area).
- **Escape → input:** pressing Escape when focus is anywhere other than the
  composer moves focus back to the composer and, if streaming is active, stops
  the stream (existing behavior) or collapses any expanded panels. Updated in
  `useHotkeys`.
- **Cmd+K → input:** Cmd+K moves focus to the composer from anywhere in the
  interface. Added to `useHotkeys` (non-conflicting with existing `⌘/` for
  shortcuts). Note: the existing CommandPalette opens on `⌘K` — verify no
  conflict; if conflict, map focus-to-input to a different shortcut in CO.6.
- **Stream end → input:** existing behavior (focus composer after streaming
  ends) is preserved unchanged.
- **ARIA:** the scroll container already has `role="log"` and `aria-live="polite"`.
  The `StatusBadge` (C1) adds `aria-live="polite" aria-atomic="true"`.
  Each assistant message gets `aria-label` from the message ID for direct
  linking. No other ARIA changes in CO.6.

**Acceptance hook (CO.6):**
Keyboard-only nav covers every interactive element; screen reader announces
stage changes without interrupting answer reading; WCAG 2.1 AA pass.

---

## §X — Design tokens audit

Hardcoded color values found in `platform/src/components/consume/**` and
`platform/src/components/chat/**` that must be replaced with design tokens
in CO.5. Each entry: file, line (approximate), value, recommended replacement.

| # | File | Value | Recommended token |
|---|---|---|---|
| T1 | `ConsumeChat.tsx` ~L718 | `bg-[oklch(0.11_0.010_70)]` | `bg-[var(--brand-charcoal-deep)]` or `bg-muted/20` (verify contrast in CO.5) |
| T2 | `ConsumeChat.tsx` ~L718 | `text-[#fce29a]/85` | `text-[var(--brand-gold-light)]/85` |
| T3 | `TraceDrawer.tsx` ~L30 | `bg-[#211c0a]` | `bg-[var(--brand-charcoal-deep)]` |
| T4 | `SharedConsumeError.tsx` ~L12 | `shadow-[0_30px_80px_-30px_rgba(0,0,0,0.6)]` | `shadow-2xl` or define `--shadow-deep` CSS variable |
| T5 | `ValidatorFailureView.tsx` ~L77 | `shadow-[0_30px_80px_-30px_rgba(0,0,0,0.6)]` | Same as T4 — consolidate |

**rgba(var(--...-rgb), N) patterns** (already using tokens correctly, no
change needed):
- `rgba(var(--brand-gold-rgb), 0.4 / 0.6)` — ConsumeChat, TraceDrawer
- `rgba(var(--status-warn-rgb), 0.4 / 0.6)` — ConsumeChat, AnswerView
- `rgba(0, 0, 0, 0.6)` — shadow only (T4/T5 above; replace with token in CO.5)

**Additional audit items for CO.5:**
- Verify all `border-border/60`, `border-border/80` usages use consistent
  opacity levels (not a mix of 40/50/60/80 for same semantic purpose).
- Audit `bg-muted/30`, `bg-muted/40`, `bg-muted/50` — consolidate to a
  maximum of 2 opacity levels per semantic layer.
- Audit `text-xs` vs `text-[11px]` vs `text-[10px]` vs `text-[9px]` in
  consume/ — map to type scale from §3 and eliminate fractional sizes not
  in the approved scale.

---

*End of CONSUME_UI_SPEC_v1_0.md*
*Phase: CO.0 | Governs: CO.1–CO.6 | Feature flag: CONSUME_UI_V2_ENABLED*
