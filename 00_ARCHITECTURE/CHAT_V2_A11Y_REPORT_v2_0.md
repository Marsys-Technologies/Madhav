---
artifact: CHAT_V2_A11Y_REPORT_v2_0
name: Chat V2 a11y Report v2.0
canonical_id: CHAT_V2_A11Y_REPORT_v2_0
version: 2.0
status: PARTIAL — awaiting manual screen-reader testing
authored: 2026-05-17
author: Claude Code executor (remediation session)
remediation_item: C.6
---

# Chat V2 Accessibility Report — v2.0

## §1 Programmatic Results (executor-complete)

Programmatic axe-core scan: **PASS** — 0 critical/serious violations.  
Source attribute assertions: **8/8 PASS** (see `CHAT_V2_STAGING_E2E_REPORT_v2_0.md §3`).

WCAG criteria verified programmatically:
- Single `<main>` landmark
- `role=log` + `aria-live=polite` on thread viewport
- `aria-label="Message input"` + `aria-multiline="true"` on composer
- `aria-label` on all icon-only buttons (send, stop, cancel-send, attach, scroll-to-bottom, details-close)
- `aria-hidden="true"` on decorative SVGs
- `role=dialog` + `aria-modal="true"` on details drawer
- `aria-hidden="true"` on drawer backdrop
- `tabIndex` + Escape handler present for focus trap

## §2 Manual Screen-Reader Testing (OPERATOR ACTION REQUIRED)

The following require physical assistive technology hardware. Mark each as PASS/FAIL/NOTE.

### NVDA + Firefox (Windows)
- [ ] Tab order: composer → send → message list → details toggle → close
- [ ] Screen reader announces "Message input" on focus
- [ ] Each assistant message is announced when streaming completes
- [ ] Details drawer announced as dialog on open
- [ ] Escape dismisses drawer and returns focus to trigger
- [ ] Stage names ("Classify", "Compose bundle") announced during streaming

**Tester**: _______________  **Date**: _______________  **Verdict**: _______________

### VoiceOver + Safari (macOS)
- [ ] Same checklist as NVDA above
- [ ] Swipe navigation reaches all interactive elements
- [ ] Drawer trap confirmed

**Tester**: _______________  **Date**: _______________  **Verdict**: _______________

### VoiceOver + Safari (iOS)
- [ ] Touch navigation: tap targets ≥44px confirmed
- [ ] Composer announces character count / placeholder
- [ ] iOS home-indicator area not occluded (safe-area-inset-bottom)
- [ ] Bottom-sheet citation panel accessible

**Tester**: _______________  **Date**: _______________  **Verdict**: _______________

## §3 Overall Verdict

Programmatic: **PASS**  
Manual: **PENDING OPERATOR ACTION** — fill §2 before marking C.6 COMPLETE.
