---
status: OPEN
session_id: AIOPS_CO_2
phase: CO.2
phase_name: "Input panel cleanup + per-message model capsules (Bug 3.1)"
next_session: AIOPS_CO_3
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_2
## AIOps Phase 3, Step 2 — Bug 3.1 fix

---

## §0 — Executor orientation

CO.2 fixes Bug 3.1 — model names appearing in the input panel area and
breaking alignment when a query is triggered. The fix has two parts:

  1. **Remove model names from the input panel.** The current input area
     (composer + TierPicker / stack selector) crams the active model's name
     into the same row, breaking horizontal alignment when long names land.
     Strip that out. The stack selector stays; the model display goes.

  2. **Add per-message model capsules at the end of each response.** Same
     information, better location. Capsule shows: model_id + cost + latency.
     Implemented by extending `PostAnswerProvenance.tsx` (or replacing it
     with a new `MessageMetadata.tsx` if cleaner).

All edits behind `CONSUME_UI_V2_ENABLED` flag (CO.1 deliverable).

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md (CO.0 — components 1, 2, 7)
3. 00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md (CO.0 — Mistral pattern reference)
4. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
5. platform/src/lib/hooks/useChatLifecycle.ts (CO.1 — snapshot.modelMeta is the data source)
6. platform/src/components/consume/lifecycle/MetadataBadge.tsx (CO.1 — placeholder; evolve here)
7. platform/src/components/consume/ConsumeChat.tsx (input area location)
8. platform/src/components/consume/TierPicker.tsx (stack selector — keep, but verify alignment)
9. platform/src/components/consume/PostAnswerProvenance.tsx (current model attribution location)
```

---

## §2 — Scope

### may_touch
```
platform/src/components/consume/ConsumeChat.tsx                # input panel cleanup
platform/src/components/consume/TierPicker.tsx                 # alignment verification only
platform/src/components/consume/PostAnswerProvenance.tsx       # evolve for new capsule shape
platform/src/components/consume/lifecycle/MetadataBadge.tsx    # finalize design
platform/src/components/consume/__tests__/**                   # tests
CLAUDECODE_BRIEF.md
```

### must_not_touch
- LiveReasoningCard, StreamingAnswer reasoning logic — CO.3
- ConversationSidebar — CO.4
- Visual design tokens (colors, typography) — CO.5
- platform/src/lib/adapters/**, synthesis/**, models/**

---

## §3 — Work plan

### 3.1 — Remove model names from input panel

In `ConsumeChat.tsx`, locate where the active model name is rendered inside
the input panel layout (typically near or inside `TierPicker`). Remove the
rendering. The stack selector stays — only the per-model display goes.

Verify alignment in all states:
- Empty composer
- Typing (composer expanding)
- Submitted (composer disabled, awaiting response)
- Streaming (composer disabled, response building)
- Complete (composer ready for next message)

In each state, the input panel row should have stable height and the stack
selector + send button should not shift.

### 3.2 — Per-message metadata capsule

Extend `MetadataBadge.tsx` (CO.1 placeholder) to display:

```
[ Gemini 2.5 Pro · $0.012 · 4.2s ]
```

Three pieces, separated by a thin divider character. Information sourced
from `useChatLifecycle().modelMeta` which is populated from the `finish`
event's `interaction.usage`.

Per CO.0 spec §X (per-message metadata badge): the capsule sits at the END
of the assistant message, flush right or right-aligned. Click-to-expand
reveals full token counts + provider request_id (for audit/debugging).

Reuse Observatory's existing badge/capsule visual treatment if available —
do not introduce new visual primitives in CO.2 (that's CO.5 territory).

### 3.3 — Legacy compatibility

Old messages (rendered via `AnswerView.tsx` legacy renderer) keep their
existing model attribution. The new capsule appears only on new messages
that flow through `useChatLifecycle`. Forward-only commitment from CO.0.

### 3.4 — Tests

- Input panel alignment: snapshot tests for the 5 states above.
- MetadataBadge: render with sample modelMeta, assert text content.
- Click-to-expand on the capsule reveals token counts.
- ≥12 cases.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO2.1 | No model name renders in input panel area | grep + UI test |
| AC.CO2.2 | Stack selector + send button alignment stable across all 5 input states | snapshot tests |
| AC.CO2.3 | MetadataBadge renders model + cost + latency for new messages | render test |
| AC.CO2.4 | Capsule click-to-expand reveals token counts + request_id | UI test |
| AC.CO2.5 | Old messages render unchanged (forward-only) | snapshot |
| AC.CO2.6 | typecheck + lint clean | exit 0 |
| AC.CO2.7 | ≥12 new tests pass | test count |
| AC.CO2.8 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
feat(aiops-CO.2): fix Bug 3.1 — input panel cleanup + per-message capsules

- Removed model name display from input panel area (was breaking alignment)
- Verified stack selector + send button alignment in all 5 input states
- MetadataBadge now shows [ model_id · cost · latency ] at end of each
  assistant message; click-to-expand reveals token counts + request_id
- Data source: useChatLifecycle().modelMeta (Phase 2 finish event)
- Old messages unchanged (forward-only commitment from CO.0)
- 12+ new tests

AC summary: 8/8 PASS
```

Rotate → CO.3.

---

## §6 — BAIL OUT

- The model name in the input panel turns out to be a deeply-coupled piece of state used by other components (not just display).
- TierPicker has its own model display logic that's hard to disentangle without rewriting the component (CO.5 territory).

---

*End of PHASE_CO_2_BRIEF.md*
