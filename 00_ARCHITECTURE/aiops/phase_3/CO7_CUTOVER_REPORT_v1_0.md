---
artifact: CO7_CUTOVER_REPORT_v1_0.md
version: 1.0
status: OPEN
authored_at: 2026-05-14
session_id: AIOPS_CO_7
phase: Phase 3 — Consume UI Overhaul (CO.0 → CO.7)
---

# CO.7 Cutover Report

> **Status:** OPEN — branch `feature/aiops-phase-3-consume-ui` ready for native review + merge.
> Push to main deferred per hard constraint ("no push; native reviews and merges").

---

## §1 — Cutover smoke results

Smoke runner: `platform/scripts/aiops/consume_ui_cutover_check.ts`
12 structural + flag-gate checks run twice (flag-off, flag-on).

| Run | Pass | Total | Fail |
|---|---|---|---|
| `CONSUME_UI_V2_ENABLED=false` | 12 | 12 | 0 |
| `CONSUME_UI_V2_ENABLED=true`  | 12 | 12 | 0 |

**Flag gate:** Component tree gated correctly both directions. Structural
deliverables (lifecycle slot components, hooks, tests, audit) all present.

---

## §2 — Visual regression evidence

Screenshots require a running browser at `/consume`. This environment (CLI
worktree) does not have a live Next.js dev server. Visual evidence to be
captured manually during native acceptance review per CO7_NATIVE_ACCEPTANCE.md
checklist items 1–6.

**Reference frames for reviewer:**
1. `/consume` empty state → EmptyState component (flag-off and flag-on should match)
2. Post-submit streaming — StatusPip visible, reasoning slot anchored (Bug 3.3)
3. Completed response — MetadataBadge shows model + cost + latency (Bug 3.1)
4. Non-reasoning model (NIM Nemotron) — ReasoningSlot absent (Bug 3.4)
5. Sidebar collapsed → hover-expand → click-pin (Bug 3.2)
6. Mobile 375×667 — composer sticky, no horizontal scroll

---

## §3 — Bug fix verification

| Bug | Description | Fix location | Verification method |
|---|---|---|---|
| Bug 3.1 | Model name displayed in input panel, not per-message | ConsumeChat.tsx: hides `lastAssistantMeta` span when flag ON; MetadataBadge renders per-message capsule | lifecycle.test.tsx: MetadataBadge CO.2 expand tests |
| Bug 3.2 | Sidebar locked open/closed — no hover UX | ConversationSidebar.tsx: `useSidebarState` wired; hover strip + pin button | useSidebarState.test.ts: 18 state machine tests |
| Bug 3.3 | Reasoning slot mounts after stream ends (CLS) | lifecycle slots mount at submission time as stable DOM anchors; content streams into them | lifecycle.test.tsx: idle → reasoning → complete flow |
| Bug 3.4 | Reasoning slot shown for all models regardless of capability | ReasoningSlot uses `getModelMeta(modelId)?.quirks.reasoning_via`; returns null for `'none'` | lifecycle_co3.test.tsx: model-aware gate tests |

All 4 bugs have passing automated test coverage. ✓

---

## §4 — A11y audit summary

Full audit: `00_ARCHITECTURE/aiops/phase_3/CO6_A11Y_AUDIT.md`

| Area | Status |
|---|---|
| Color contrast (WCAG AA 4.5:1 / 3:1) | ✅ Primary content meets AA; two deferred items (supplemental labels) documented |
| Keyboard navigation | ✅ All interactive elements Tab-reachable; `useKeyboardShortcuts` wires Cmd+K, Cmd+Enter, Esc, Cmd+/, Cmd+B, Cmd+Shift+O |
| ARIA roles + states | ✅ `aria-live="polite"` on StatusPip; `aria-expanded` on all toggles; `role="alert"` on error surfaces; `role="log"` on message stream |
| Touch targets | ⚠️ Composer send button 40×40px (just under 44px), pin button 24×24px — deferred, desktop-only, documented |
| Screen reader | ✅ Status pip announces state changes; reasoning slot expansion announced via aria-expanded |
| Semantic HTML | ✅ `<ul>/<li>` for tool calls; `<dl>/<dt>/<dd>` for metadata; `<p>` for prose |

**OUTSTANDING: 0** — no blocking defects. Two items documented as intentional deferrals.

---

## §5 — Outstanding risks

| Risk | Severity | Mitigation |
|---|---|---|
| No browser-rendered screenshots captured in this session | Low | Manual capture during native acceptance review (CO7_NATIVE_ACCEPTANCE.md §2) |
| Composer send button 40×40px (1px under WCAG 2.5.8 target) | Low | Desktop-only; mouse use acceptable; padding expansion deferred to CO.8+ |
| `rgba(0,0,0,0.6)` shadow in SharedConsumeError + ValidatorFailureView | Low | CO.5 flagged for native decision; no brand-color impact; no blocking a11y issue |
| Push + Cloud Run revision verification deferred | Low | Hard constraint: no-push. Native reviews branch and merges; rollback via gcloud env-var removal |

**No blocking risks.** Branch is merge-ready.

---

## §6 — Deploy.yml change

File: `.github/workflows/deploy.yml`
Change: Added `CONSUME_UI_V2_ENABLED=true` to deploy-web `env_vars` block after `ADAPTERS_ENABLED=true`.

Rollback (without code revert):
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --remove-env-vars CONSUME_UI_V2_ENABLED
```

---

## §7 — Branch commit log (CO.0 → CO.7)

| Commit | Phase | Description |
|---|---|---|
| CO.0 | Foundation | Feature flag, useChatLifecycle hook + reducer, 5 lifecycle slot stubs |
| CO.1 | Lifecycle wiring | ConsumeChat flag-ON path wires lifecycle slots |
| CO.2 | MetadataBadge + requestId | Per-message model capsule; Bug 3.1 fix |
| CO.3 | ReasoningSlot model-aware | Bug 3.4 fix; duration tracking; LiveReasoningCard legacy preserved |
| CO.4 | Sidebar hover-expand | Bug 3.2 fix; useSidebarState 5-state machine; pin persistence |
| CO.5 | Visual design pass | Typography ≤ 6 sizes; hardcoded colors → design tokens; motion tiers |
| CO.6 | Behavioral polish | useKeyboardShortcuts; a11y WCAG 2.1 AA; 31 new tests; CO6_A11Y_AUDIT.md |
| CO.7 | Cutover | deploy.yml flag flip; smoke check 12/12; native acceptance checklist |

8 sub-phases. AIOps trilogy complete.

---

*End of CO7_CUTOVER_REPORT_v1_0.md v1.0*
