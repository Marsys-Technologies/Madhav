---
status: OPEN
session_id: AIOPS_CO_0
phase: CO.0
phase_name: "UX research + design spec authoring"
next_session: AIOPS_CO_1
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_0
## AIOps Phase 3, Step 0 — Research + Design Doc

---

## §0 — Executor orientation

CO.0 is design-document-only. No code, no production changes. Produces
two artifacts that govern the seven subsequent sub-phases:

  1. `00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md` — explicit pattern
     adoption decisions distilled from 8–10 best-in-class chat UIs.
  2. `00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md` — target state
     per component (input panel, reasoning slot, sidebar, message bubble,
     scroll behavior, etc.) referenced by CO.1 onward.

Master plan: `00_ARCHITECTURE/aiops/phase_3/AIOPS_PHASE_3_MASTER_PLAN_v1_0.md`
Execution rules: `00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md` (reused)

YOU MUST NOT modify any code in this phase. Only docs.
YOU MUST NOT call any LLM provider (no model-driven research — use your
training knowledge of these public UIs).

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/AIOPS_PHASE_3_MASTER_PLAN_v1_0.md (full)
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/lib/adapters/types.ts (Phase 2 shipped contract — read ModelInteractionEvent fully)
5. platform/src/components/consume/ConsumeChat.tsx
6. platform/src/components/consume/StreamingAnswer.tsx
7. platform/src/components/consume/LiveReasoningCard.tsx
8. platform/src/components/consume/AnswerView.tsx
9. platform/src/components/consume/PostAnswerProvenance.tsx
10. platform/src/components/chat/ConversationSidebar.tsx
11. platform/src/components/consume/TierPicker.tsx
12. platform/src/app/api/chat/consume/route.ts (the SSE producer)
```

---

## §2 — Scope

### may_touch
```
00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md       # NEW
00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md   # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- Any code (platform/src/**, platform/scripts/**)
- 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**, 06_LEARNING_LAYER/**
- Phase 2 sealed artifacts (00_ARCHITECTURE/aiops/phase_2/**)

---

## §3 — Work plan

### 3.1 — UX_RESEARCH_v1_0.md

Author with the following sections:

**§1 — Reference set.** Patterns from these 8 products, each in 2–4 sentences
covering what's worth borrowing:
- ChatGPT (o1/o3/GPT-5 reasoning UI)
- Claude.ai (artifact pattern, minimal status pulse)
- Gemini 2.5 (thinking indicator + collapsible reasoning)
- Perplexity (progressive status: searching → reading → composing)
- Cursor / Aider (tool-call chronology + apply-edits)
- Mistral Le Chat (per-message model badge)
- Phind (model picker placement + source chips)
- DeepSeek Chat (reasoning between query and response)

**§2 — Pattern adoption matrix.** Explicit Adopt / Adapt / Reject per pattern,
with one-line rationale. Examples:
- Stable reasoning slot from submission → ADOPT (ChatGPT pattern; fixes Bug 3.3)
- Inline progressive status → ADAPT (Perplexity pattern, with our pipeline stages)
- Per-message model badge → ADOPT (Mistral pattern; fixes Bug 3.1's capsule requirement)
- Slash command palette → REJECT (Q7 — deferred to Phase 3+1)
- Voice input → REJECT (Q7)
- Multimodal input → REJECT (Q7)
- Inline artifacts (Claude-style) → REJECT (separate scope; defer)

**§3 — Visual aesthetic anchor.** Single reference choice with rationale.
Recommend Claude.ai (closest to existing Madhav dark-theme + reading-focused
content). Note typography scale (target 5–6 sizes max), color discipline
(no new tokens), motion language (150ms micro, 250ms standard, 400ms entry/exit).

**§4 — State machine source.** The Phase 2 `ModelInteractionEvent` stream is
the authoritative event source. The chat lifecycle states map 1:1 to event
types:
```
event 'status: queued'      → state 'queued'
event 'status: planning'    → state 'planning'
event 'status: retrieving'  → state 'retrieving'
event 'status: reasoning'   → state 'reasoning'
event 'reasoning_delta'     → (stay in 'reasoning', append text)
event 'status: tool_calling'→ state 'tool_calling'
event 'tool_call'           → (append to chronology)
event 'tool_result'         → (append to chronology)
event 'status: composing'   → state 'composing'
event 'text_delta'          → (stay in 'composing', append text)
event 'status: complete'    → state 'complete'
event 'finish'              → (capture interaction; commit to history)
event 'error'               → state 'error'
```

**§5 — Forward-only commitment.** Old assistant messages render with the
existing AnswerView component (legacy path). New messages use the new
event-driven components. No migration of historical chat data.

### 3.2 — CONSUME_UI_SPEC_v1_0.md

Author with one section per component target state. For each, capture:
- Current behavior (1–2 sentences)
- Target behavior (1–2 sentences)
- Implementing sub-phase (CO.N)
- Files implicated

Components to cover:
1. **Input panel** (CO.2) — TierPicker + composer; remove model name display
2. **Stack selector** (CO.2) — repositioned, consistent alignment under all states
3. **Sidebar** (CO.4) — ConversationSidebar; hover-expand/collapse, click-pin, mobile overlay
4. **Reasoning slot** (CO.3) — LiveReasoningCard refactored; anchored DOM position from submission
5. **Tool calls panel** (CO.3) — new component; collapsible chronology of tool_call + tool_result events
6. **Status indicator** (CO.1, CO.3) — inline progressive status driven by `status: <state>` events
7. **Per-message metadata badge** (CO.2) — PostAnswerProvenance evolved; model + cost + latency capsules
8. **Message bubble** (CO.5) — visual treatment; typography, spacing, color
9. **Scroll behavior** (CO.6) — anchoring rules during streaming (ChatGPT semantics)
10. **Focus management** (CO.6) — submit → assistant area; Esc → input; Cmd+K → input

Add a §X — Design tokens audit subsection summarizing the current Tailwind
tokens in use across consume/ components, flagging any hardcoded hex values
that need replacement with tokens during CO.5.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO0.1 | `UX_RESEARCH_v1_0.md` exists with §1–§5 populated | grep section headers |
| AC.CO0.2 | Pattern adoption matrix has explicit Adopt/Adapt/Reject for ≥15 patterns | count |
| AC.CO0.3 | Reject set includes slash commands, voice, multimodal, inline artifacts (per Q7) | grep |
| AC.CO0.4 | State machine in §4 maps to Phase 2's actual ModelInteractionEvent type union | cross-reference |
| AC.CO0.5 | `CONSUME_UI_SPEC_v1_0.md` exists with ≥10 component target-state entries | count |
| AC.CO0.6 | Every entry names its implementing sub-phase (CO.1–CO.6) | grep |
| AC.CO0.7 | Design tokens audit identifies ≥3 hardcoded values flagged for CO.5 cleanup | grep |
| AC.CO0.8 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Standard procedure. Commit message:
```
docs(aiops-CO.0): UX research + consume UI spec

- UX_RESEARCH_v1_0.md: 8-product reference set, ≥15-pattern adoption matrix,
  Claude.ai aesthetic anchor, state machine mapped to ModelInteractionEvent.
- CONSUME_UI_SPEC_v1_0.md: ≥10 component target states, each named for its
  implementing CO.N sub-phase, design tokens audit flagging hardcoded values
  for CO.5 cleanup.
- Q7 reject set captured: slash commands, voice, multimodal, inline artifacts.
- Forward-only commitment: old messages render with legacy AnswerView.

AC summary: 8/8 PASS
```

Rotate `CLAUDECODE_BRIEF.md` → `PHASE_CO_1_BRIEF.md`.

---

## §6 — BAIL OUT triggers

- The Phase 2 ModelInteractionEvent type isn't where expected (the cross-reference in §4 fails to map cleanly).
- The consume components have evolved since Phase 2 shipped (new components added that aren't in mandatory reads list).

---

*End of PHASE_CO_0_BRIEF.md*
