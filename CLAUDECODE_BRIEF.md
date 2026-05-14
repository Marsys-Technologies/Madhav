---
status: OPEN
session_id: AIOPS_CO_6
phase: CO.6
phase_name: "Behavioral polish — scroll, focus, keyboard, a11y, edge states"
next_session: AIOPS_CO_7
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_6
## AIOps Phase 3, Step 6 — Behavioral polish

---

## §0 — Executor orientation

CO.6 is the behavioral polish pass. Per native Q7: best-in-class
behavioral experience is IN SCOPE. Anchor reference: ChatGPT
(scroll anchoring + smooth transitions); Claude.ai (focus management).

Seven targets:
  1. Scroll anchoring during streaming
  2. Focus management (submit → assistant area; Esc → input; Cmd+K → input)
  3. Keyboard shortcuts
  4. Mid-stream interrupts ("Stop generating")
  5. Error / empty / loading states
  6. Accessibility (WCAG 2.1 AA)
  7. Mobile responsiveness

Behind `CONSUME_UI_V2_ENABLED`.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md (components 9, 10)
3. 00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md
4. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
5. design:accessibility-review skill SKILL.md (if available — see Phase 1's CP.4 for example)
6. All consume/ components after CO.1–CO.5 deliverables
7. platform/src/components/consume/EmptyState.tsx
8. platform/src/components/consume/SharedConsumeError.tsx
9. platform/src/components/consume/ValidatorFailureView.tsx (existing error surface)
```

---

## §2 — Scope

### may_touch
```
platform/src/components/consume/**                      # behavioral wiring
platform/src/lib/hooks/useScrollAnchor.ts                # NEW
platform/src/lib/hooks/useKeyboardShortcuts.ts           # NEW
platform/src/components/consume/__tests__/**             # a11y + behavior tests
00_ARCHITECTURE/aiops/phase_3/CO6_A11Y_AUDIT.md          # NEW report
CLAUDECODE_BRIEF.md
```

### must_not_touch
- adapters/, synthesis/, models/  (Phase 1+2 sealed)
- API routes
- Visual design tokens (CO.5 sealed)

---

## §3 — Work plan

### 3.1 — Scroll anchoring

`useScrollAnchor.ts`:
- If user is scrolled to the bottom (within 100px) AND new content arrives,
  auto-scroll to follow.
- If user has scrolled up (> 100px from bottom), do NOT auto-scroll.
- On new user message submit, always scroll to bottom.
- Mimics ChatGPT precisely.

Wire to ConsumeChat's scroll container.

### 3.2 — Focus management

- Submit query → focus moves to the assistant message area (specifically the
  first reasoning or status indicator that mounts).
- Esc → focus returns to composer; collapses any expanded panels.
- Cmd+K → focus composer from anywhere.
- Tab through interactive elements: composer → send → stack picker → 
  history button → sidebar → message metadata expand → next message.

### 3.3 — Keyboard shortcuts

`useKeyboardShortcuts.ts`:
- `Cmd/Ctrl+Enter` — submit (likely exists; verify)
- `Esc` — collapse panels + return focus
- `Cmd/Ctrl+K` — focus composer
- `Cmd/Ctrl+/` — show shortcuts help overlay (small modal)

### 3.4 — Mid-stream interrupts

While `lifecycle.state` is anything other than `complete | idle | error`:
- Show a "Stop generating" button near the message.
- Clicking it cancels the SSE stream (AbortController) and transitions the
  lifecycle to `cancelled`.
- In cancelled state, show partial output + a "Regenerate" button.

### 3.5 — Error / empty / loading states

- `EmptyState`: keep existing but verify with new visual treatment.
- Error from adapter: surface via `ValidatorFailureView` or `SharedConsumeError` depending on error class. Include "Try again" button.
- Loading skeletons for the initial message-list fetch (sidebar conversation history).

### 3.6 — A11y (WCAG 2.1 AA)

Run accessibility audit using the design:accessibility-review skill pattern (see Phase 1 CP.4):
- Color contrast: every text vs background ≥ 4.5:1 (body), ≥ 3:1 (large text).
- Keyboard nav: every interactive element reachable via Tab; visible focus ring.
- ARIA: dropdowns, modals, tab strips, status indicators all have appropriate ARIA roles + states.
- Touch targets ≥ 44×44 px.
- Screen reader: `aria-live="polite"` on the status indicator and reasoning slot.
- Semantic HTML throughout.

Author findings in `CO6_A11Y_AUDIT.md`. Acceptance: `OUTSTANDING: 0`.

### 3.7 — Mobile (< 640px)

- Sidebar collapses to overlay (CO.4 already wired).
- Composer sticks to bottom of viewport.
- Reasoning slot collapses to a one-line summary by default; tap to expand.
- Tool call chronology shows one card at a time (carousel-style) instead of stacked.
- Touch targets ≥ 44 px throughout.

### 3.8 — Tests

- Scroll anchoring: simulate user scroll position; assert auto-follow behavior.
- Keyboard shortcuts: simulate key events; assert focus/state changes.
- Stop-generating: cancel mid-stream; lifecycle transitions to cancelled.
- A11y assertions in component tests for every interactive element.
- ≥25 cases.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO6.1 | useScrollAnchor mimics ChatGPT pattern correctly | scroll-pos tests |
| AC.CO6.2 | Focus management covers submit/esc/cmd-k/tab paths | a11y tests |
| AC.CO6.3 | 4 keyboard shortcuts work + help modal shows | UI tests |
| AC.CO6.4 | Mid-stream "Stop generating" cancels + leaves regenerate option | UI test |
| AC.CO6.5 | CO6_A11Y_AUDIT.md shows OUTSTANDING: 0 | grep |
| AC.CO6.6 | CLS < 0.05 during normal interaction (re-measured post-CO.5) | manual + doc |
| AC.CO6.7 | Mobile (< 640px) viewport tests pass | parametrized test |
| AC.CO6.8 | typecheck + lint + full suite green | exit 0 |
| AC.CO6.9 | ≥25 new tests | count |
| AC.CO6.10 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
feat(aiops-CO.6): behavioral polish — scroll, focus, keyboard, a11y, edges

- useScrollAnchor: ChatGPT-style follow-at-bottom; no auto-scroll when scrolled up
- useKeyboardShortcuts: Cmd+Enter submit, Esc collapse, Cmd+K focus, Cmd+/ help
- Focus management: submit → assistant area; Esc → composer; Tab order audited
- Mid-stream Stop generating button + cancelled-state regenerate
- Error/empty/loading states polished
- A11y WCAG 2.1 AA: CO6_A11Y_AUDIT.md OUTSTANDING: 0
- Mobile (< 640px) viewport: composer-sticky, reasoning-collapse, 44px targets
- 25+ new tests; CLS < 0.05 verified

AC summary: 10/10 PASS
```

Rotate → CO.7.

---

## §6 — BAIL OUT

- A11y issue with no clean fix (e.g., contrast requires a new color token; CO.5 should have handled it).
- Mobile viewport tests reveal a fundamental layout issue requiring a bigger refactor.

---

*End of PHASE_CO_6_BRIEF.md*
