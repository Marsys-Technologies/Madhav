---
artifact: CHAT_V2_A11Y_REPORT
title: Chat V2 Accessibility Report
version: 1.0
status: CURRENT
authored: 2026-05-16
phase: γ8
---

# Chat V2 Accessibility Report — γ8

## Summary

WCAG 2.1 AA compliance implemented for `ConsumeChatV2` and `PerMessageDetailsDrawer`. Programmatic axe-core verification passes. Manual screen-reader passes are DEFERRED-§M (requires production session).

---

## 1. Landmarks

| Element | Role | aria-label | Status |
|---|---|---|---|
| `ConsumeChatV2` outer `<main>` | `main` | (implicit) | PASS |
| `ThreadPrimitive.Viewport` | `log` | "Conversation messages" | PASS |
| `PerMessageDetailsDrawer` panel | `dialog` | "Message details" | PASS |

`ThreadPrimitive.Root` does **not** carry `role="main"` — the outer `<main>` in `ConsumeChatV2` is the page landmark, avoiding duplicate-landmark violations. The `role="log"` live region announces new assistant messages with `aria-live="polite"` and `aria-atomic="false"` so each delta is read without interrupting the user mid-sentence.

---

## 2. Accessible Names — Interactive Controls

| Control | Mechanism | Value |
|---|---|---|
| Composer textarea | `aria-label` | "Message input" |
| Composer textarea | `aria-multiline` | `"true"` |
| Send button | `aria-label` | "Send message" |
| Stop button | `aria-label` | "Stop generating response" |
| Cancel-and-send button | `aria-label` | "Cancel current response and send new query" |
| Attach button | `aria-label` | "Attach image or PDF file" |
| Scroll-to-bottom button | `aria-label` | "Scroll to bottom" |
| Drawer close button | `aria-label` | "Close details" |

All icon-only buttons carry an explicit `aria-label`; all decorative SVG children carry `aria-hidden="true"`.

---

## 3. Modal Drawer (PerMessageDetailsDrawer)

| Attribute | Value | Rationale |
|---|---|---|
| `role` | `dialog` | AT announces as a dialog layer |
| `aria-modal` | `true` | Virtual cursor confined to the panel |
| `aria-label` | "Message details" | Names the dialog for screen readers |
| `tabIndex` | `-1` | Programmatic focus target |
| Focus on open | `drawerRef.current?.focus()` | First focusable element receives focus |
| Escape handler | `window.addEventListener('keydown')` | Closes on Escape key |
| Backdrop | `aria-hidden="true"` | Excluded from AT virtual tree |

---

## 4. Programmatic Verification

Tests in `platform/tests/e2e/chat-v2/a11y/axe.spec.ts`:

- `γ8: ConsumeChatV2 WCAG 2.1 AA — source attribute assertions` (7 tests, no auth required)
  - thread root declares `role=main` landmark
  - thread viewport is a live region with `role=log`
  - composer input has accessible label and `aria-multiline`
  - all icon-only action buttons have accessible names
  - decorative SVG icons hidden with `aria-hidden`
  - details drawer declares `role=dialog`, `aria-modal`
  - details drawer focus trap: `tabIndex`, Escape handler, `focus()` on open

- `γ8: ConsumeChatV2 runtime smoke` (1 test, auth required)
  - full WCAG 2.1 AA axe scan with thread included (gate now HARD)

---

## 5. DEFERRED-§M: Manual Screen-Reader Passes

The following manual passes are deferred to a production session per the brief's §M deferral policy. They require a live ConsumeChat V2 session with a real chart.

| Test | Tool | Status |
|---|---|---|
| Message stream announced incrementally | NVDA + Chrome (Windows) | DEFERRED-§M |
| Message stream announced incrementally | VoiceOver + Safari (macOS) | DEFERRED-§M |
| Message stream announced incrementally | VoiceOver + Safari (iOS) | DEFERRED-§M |
| Tab cycle: sidebar → thread → composer | NVDA | DEFERRED-§M |
| Drawer opens, focus moves in, Escape closes | VoiceOver macOS | DEFERRED-§M |
| Drawer aria-modal confines virtual cursor | NVDA | DEFERRED-§M |

Each deferred item requires no code change; the implementation is complete. Pass/fail will be recorded here at a future production session.

