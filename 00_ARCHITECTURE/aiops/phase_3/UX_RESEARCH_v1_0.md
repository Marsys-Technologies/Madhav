---
artifact: UX_RESEARCH_v1_0.md
canonical_id: AIOPS_PHASE3_UX_RESEARCH
version: 1.0
status: CURRENT
authored_at: 2026-05-14
authored_by: CO.0 (AIOPS_CO_0 session)
phase: CO.0 — UX research + design spec authoring
purpose: >
  Establishes the design-level source of truth for Phase 3 (Consume UI Overhaul).
  §1–§5 govern all subsequent sub-phases CO.1–CO.7. The pattern adoption matrix
  in §2 is the explicit record of what we borrow, adapt, or reject — it must be
  consulted before any design decision in CO.1–CO.7.
changelog:
  - v1.0 (2026-05-14): initial authoring from CO.0.
---

# AIOps Phase 3 — UX Research v1.0

---

## §1 — Reference set

Eight best-in-class chat UIs surveyed. For each, 2–4 sentences capturing the
borrowable pattern and why it matters for Consume.

### 1.1 ChatGPT (o1 / o3 / GPT-5 reasoning UI)

ChatGPT's reasoning UX is the clearest prior art for Bug 3.3: from the moment
a query is submitted, a "Thought for N seconds" collapsible block occupies a
stable DOM slot between the user message and the final answer. Reasoning text
streams live into that slot; when the model switches to composing, the block
auto-collapses (but remains expandable). The slot never moves — there is no
layout shift. Per-token streaming into the collapsed header keeps the user
informed without demanding attention.

### 1.2 Claude.ai (artifact pattern, minimal status pulse)

Claude.ai forgoes a full reasoning surface for users but demonstrates
exceptional polish in its processing indicator: a single animated pulse with
"Claude is thinking…" renders inline with the assistant message stream, then
dissolves when text begins. The artifact-panel pattern (right-side popout for
code / documents) is Claude.ai's signature feature; it is NOT adopted for this
phase (explicitly out of scope per Q7), but the minimal-status-pulse pattern is
adopted. The dark-mode typography and reading-focused layout are the primary
aesthetic reference for CO.5.

### 1.3 Gemini 2.5 (thinking indicator + collapsible reasoning)

Gemini 2.5 renders a "Thinking…" spinner with live step text streaming inside
a collapsible accordion. On response arrival the accordion auto-collapses,
preserving expand access. The per-step granularity is close to what we already
produce from Phase 2's `reasoning_delta` events. Gemini's behavior on models
without reasoning: the accordion is simply absent — model-aware rendering at
its simplest. The auto-collapse-on-compose transition is worth adopting.

### 1.4 Perplexity (progressive status: searching → reading → composing)

Perplexity's status indicator is the best-in-class reference for multi-stage
query pipelines: it cycles through inline copy ("Searching the web…" →
"Reading 8 sources…" → "Composing answer…") driven by backend lifecycle events.
The copy replaces itself on each stage transition rather than accumulating,
keeping the interface clean. Crucially, Perplexity's stages map 1:1 to its
backend events — which is exactly what Phase 2's `ModelInteractionEvent` status
field enables for Consume. Source chips appear inline after the answer.

### 1.5 Cursor / Aider (tool-call chronology + apply-edits)

Cursor renders each tool call as a collapsible card in chronological order,
with tool name, arguments summary, and result. The audit trail persists after
the response is complete, giving the user a full view of the agent's work.
Aider's terminal-style step-by-step output is cruder but demonstrates the same
principle: tool calls are first-class content, not hidden plumbing. This is the
reference for the Phase 3 tool-calls panel (CO.3).

### 1.6 Mistral Le Chat (per-message model badge)

Le Chat attaches a compact badge to every assistant message showing the model
that produced it. Clicking expands to token counts and latency. This is the
direct reference for fixing Bug 3.1's model-name misplacement: instead of
showing the model in the input panel (which breaks alignment), show it as a
post-response metadata capsule. Le Chat's badge also works correctly in
multi-model conversations — each message shows its own model, not a global
setting.

### 1.7 Phind (model picker placement + source chips)

Phind pins its model picker cleanly to the input panel's right edge without
spilling into the text area or breaking alignment on mobile. The picker is
compact (icon + short label), consistent across all interaction states (idle,
streaming, error). Source chips appear below the answer as clickable pills.
Phind's picker placement is the reference for fixing Bug 3.1 and for the
repositioned stack selector in CO.2.

### 1.8 DeepSeek Chat (reasoning between query and response)

DeepSeek Chat's reasoning UI is minimal: a collapsible "Thinking" block appears
between the user message and the assistant response, streams the model's chain
of thought, and collapses on completion. Critically, DeepSeek's reasoning block
is anchored in the DOM from query submission — it does not snap into place when
the response arrives. This is the simplest correct implementation of the stable
slot pattern and serves as a secondary reference alongside ChatGPT for Bug 3.3.

---

## §2 — Pattern adoption matrix

Explicit Adopt / Adapt / Reject for each identified pattern. 21 patterns.
Reference source in parentheses. Phase implementing in brackets.

| # | Pattern | Decision | Rationale | Phase |
|---|---|---|---|---|
| P1 | Stable reasoning DOM slot present from submission | **ADOPT** | ChatGPT + DeepSeek; directly fixes Bug 3.3 — no layout shift | CO.3 |
| P2 | Reasoning auto-collapses when composing begins | **ADOPT** | Gemini 2.5; cleaner reading experience; still expandable | CO.3 |
| P3 | Reasoning slot absent when model has no reasoning capability | **ADOPT** | Gemini 2.5 (implicit); fixes Bug 3.4 — `reasoning_via !== 'none'` gate | CO.3 |
| P4 | Per-step text streaming into reasoning slot | **ADOPT** | ChatGPT; live `reasoning_delta` events from Phase 2 stream enable this directly | CO.3 |
| P5 | Inline progressive status copy (stage-by-stage) | **ADAPT** | Perplexity; adapt with Consume's pipeline stage labels rather than Perplexity's web-search copy | CO.1 |
| P6 | Status copy disappears when answer text begins | **ADOPT** | Perplexity; status is transitional, not permanent | CO.1 |
| P7 | Tool calls as collapsible chronological cards | **ADOPT** | Cursor; Phase 2 emits `tool_call` + `tool_result` events — wire them to cards | CO.3 |
| P8 | Tool-call audit trail persists after response completes | **ADOPT** | Cursor; useful for the super_admin / acharya tier; collapsed by default for client tier | CO.3 |
| P9 | Per-message model badge (compact capsule below response) | **ADOPT** | Mistral Le Chat; directly fixes Bug 3.1 model-name misplacement | CO.2 |
| P10 | Model badge expands to token counts + latency | **ADOPT** | Mistral Le Chat; evolves existing PostAnswerProvenance toward richer metadata | CO.2 |
| P11 | Model picker pinned to input panel right edge | **ADOPT** | Phind; fixes Bug 3.1 alignment breakage — compact icon + short label | CO.2 |
| P12 | Sidebar hover-expand / hover-collapse | **ADOPT** | Common pattern (ChatGPT, Claude.ai, Phind); fixes Bug 3.2 | CO.4 |
| P13 | Sidebar click-to-pin (stays expanded after click) | **ADOPT** | ChatGPT; prevents accidental collapse during active navigation | CO.4 |
| P14 | Mobile sidebar as overlay | **ADOPT** | Claude.ai; already partially implemented; polish and complete in CO.4 | CO.4 |
| P15 | Minimal status pulse ("Thinking…") | **ADAPT** | Claude.ai; adapt to show pipeline stage name instead of generic copy | CO.1 |
| P16 | Source / provenance chips below answer | **ADAPT** | Perplexity + Phind; existing PostAnswerProvenance pills evolved, not replaced | CO.2 |
| P17 | Dark reading-focused typography (Claude.ai aesthetic) | **ADOPT** | Closest aesthetic to existing Madhav dark theme; detailed in §3 | CO.5 |
| P18 | Motion language: ease-out entry, spring exit | **ADOPT** | Claude.ai; 150ms micro / 250ms standard / 400ms entry-exit | CO.5 |
| P19 | Slash command palette (Cmd+/) | **REJECT** | Q7 — deferred to Phase 3+1; adds scope complexity without core bug fixes | — |
| P20 | Voice input | **REJECT** | Q7 — out of scope for Phase 3 v1 | — |
| P21 | Multimodal input (image / file upload beyond current) | **REJECT** | Q7 — out of scope for Phase 3 v1 | — |
| P22 | Inline artifacts à la Claude.ai | **REJECT** | Q7 — separate scope; would require right-panel architecture change | — |
| P23 | Conversation forking / branching | **REJECT** | Q7 — deferred | — |

---

## §3 — Visual aesthetic anchor

**Primary reference: Claude.ai.**

Rationale: Claude.ai's dark reading experience is the closest existing analogue
to Madhav's dark theme, serif-inflected typography, and long-form content focus.
ChatGPT's default light mode diverges too far; Gemini's material design
vocabulary conflicts with the existing token set; Perplexity's high-density
information architecture doesn't suit Jyotish reading depth.

### Typography scale (target)

Maximum 6 distinct type sizes in the consume interface:

| Role | Size | Weight | Usage |
|---|---|---|---|
| Display | `text-xl` / `text-2xl` | `font-semibold` | Section headers (rare) |
| Body | `text-sm` | `font-normal` | Answer prose, sidebar items |
| Caption | `text-xs` | `font-normal` | Metadata, timestamps, hints |
| Label | `text-[11px]` | `font-medium` | Badges, capsules, status copy |
| Micro | `text-[10px]` | `font-mono` | Token counts, IDs, trace detail |
| *(reserved)* | `text-[9px]` | `font-mono` | Icon-adjacent labels (rare) |

Font-weight discipline: maximum 3 weights — `font-normal` (400), `font-medium`
(500), `font-semibold` (600). No `font-bold` or `font-extrabold` in the consume
interface.

### Color discipline

No new Tailwind tokens or CSS variables introduced in CO.5. All color
expressions must resolve to an existing token from the set:
`--brand-gold`, `--brand-gold-light`, `--brand-gold-faint`, `--brand-gold-hairline`,
`--brand-gold-rgb`, `--brand-charcoal`, `--brand-charcoal-deep`, `--brand-cream`,
`--brand-ink`, `--status-warn`, `--status-warn-bg`, `--status-warn-rgb`,
or standard Tailwind semantic tokens (`border`, `muted`, `foreground`,
`background`, `sidebar`, `sidebar-accent`, etc.).

Hardcoded hex, oklch(), rgb(), and rgba() values are flagged in §X of
CONSUME_UI_SPEC_v1_0.md for replacement in CO.5.

### Motion language

| Duration | Class | Usage |
|---|---|---|
| 150ms | `duration-150` | Micro-interactions (button hover, icon swap) |
| 250ms | `duration-[250ms]` | Standard transitions (sidebar expand, panel open) |
| 400ms | `duration-[400ms]` | Entry / exit animations (reasoning card, status banner) |

Easing: `ease-out` for entries, `ease-in` for exits, `ease-in-out` for
state transitions. No animation exceeds 400ms. Use `transition-colors`,
`transition-opacity`, `transition-transform` as Tailwind utilities; avoid
custom keyframes unless `@keyframes animate-pulse` already exists in
global styles.

---

## §4 — State machine source

Phase 2's `ModelInteractionEvent` type union (from
`platform/src/lib/adapters/types.ts`) is the authoritative event source.
Chat lifecycle states map 1:1 to event types:

```
event  { type: 'status', status: 'queued' }        → state 'queued'
event  { type: 'status', status: 'planning' }       → state 'planning'
event  { type: 'status', status: 'retrieving' }     → state 'retrieving'
event  { type: 'status', status: 'reasoning' }      → state 'reasoning'
event  { type: 'reasoning_delta', text: string }    → (stay in 'reasoning'; append text to reasoning slot)
event  { type: 'status', status: 'tool_calling' }   → state 'tool_calling'
event  { type: 'tool_call', ... }                   → (append tool-call card to chronology)
event  { type: 'tool_result', ... }                 → (append result to corresponding tool-call card)
event  { type: 'status', status: 'composing' }      → state 'composing' (reasoning auto-collapses)
event  { type: 'text_delta', text: string }         → (stay in 'composing'; append to final answer)
event  { type: 'status', status: 'complete' }       → state 'complete'
event  { type: 'finish', interaction: ModelInteraction } → (capture interaction; commit to history)
event  { type: 'error', error: ... }                → state 'error'
```

The full `ModelInteractionEvent` union (confirmed from Phase 2's shipped
`platform/src/lib/adapters/types.ts`):

```typescript
type ModelInteractionEvent =
  | { type: 'status'; ts: number; status: 'queued' | 'planning' | 'retrieving' | 'reasoning' | 'tool_calling' | 'composing' | 'complete' }
  | { type: 'reasoning_delta'; ts: number; text: string }
  | { type: 'tool_call'; ts: number; name: string; args: unknown; callId: string }
  | { type: 'tool_result'; ts: number; callId: string; result: unknown }
  | { type: 'text_delta'; ts: number; text: string }
  | { type: 'finish'; ts: number; interaction: ModelInteraction }
  | { type: 'error'; ts: number; error: { message: string; code?: string } }
```

Every UI state transition in CO.1–CO.7 is driven by these events. No state
is derived from substring matching, polling, or ad-hoc heuristics.

Status labels for the progressive status indicator (P5 / P15 adapt):

| Phase 2 status value | UI display copy |
|---|---|
| `queued` | "Queuing request…" |
| `planning` | "Planning the response…" |
| `retrieving` | "Retrieving context…" |
| `reasoning` | "Reasoning…" |
| `tool_calling` | "Consulting sources…" |
| `composing` | "Composing answer…" |
| `complete` | *(status banner dissolves; answer is visible)* |

---

## §5 — Forward-only commitment

Old assistant messages (existing chat history) render with the existing
`AnswerView` component (legacy path). New messages — those produced after
CO.7 ships with `CONSUME_UI_V2_ENABLED=true` — use the new event-driven
components (`useChatLifecycle` hook, reasoning slot, tool-call cards,
per-message metadata badge).

No migration of historical chat data. The legacy `AnswerView` and
`LiveReasoningCard` components are preserved in the codebase for the
flag-off path throughout the CO.0–CO.6 arc and are not deleted in CO.7;
they remain as fallbacks until a follow-up flag-removal PR.

Rationale: historical messages carry no `ModelInteractionEvent` stream
metadata and cannot be replayed through the new state machine. Attempting
to retrofit them would risk silent rendering regressions across thousands
of stored conversations.

---

*End of UX_RESEARCH_v1_0.md*
*Phase: CO.0 | Next: CONSUME_UI_SPEC_v1_0.md*
