---
canonical_id: R10_X_S6
version: 1.0
status: CURRENT
session_id: X-S6
title: Auto-scroll discipline — suppress when user scrolled away
depends_on: [X-S5]
blocked_on: []
flag: MARSYS_FLAG_R10_SCROLL_DISCIPLINE
flag_default: true
client_side: "yes — NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE"
authored: 2026-05-20
---

# X-S6 — Auto-Scroll Discipline

## Context

Current Chat V2 auto-scroll behavior forces the scroll position to the bottom whenever new streaming tokens arrive, even if the user manually scrolled up to read earlier parts of the response. This is disruptive. Industry-standard behavior: auto-scroll only when the user is already near the bottom; if the user has scrolled away, stop auto-scrolling and show a "scroll to bottom" button with an unread-chunk count.

**Amendment 1 (HARD GATE):** `NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE` is a client-side flag. It MUST be added to `.github/workflows/deploy.yml` `--build-arg` block. The session is NOT complete until deploy.yml contains the flag with `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true`.

**Amendment 3:** FLAGGED — behavior-changing; fast rollback desired.

**Amendment 2:** Visible component (ScrollToBottomButton + scroll behavior in chat viewport) → click-path and parent-context test required.

## Files in Scope

- `platform/src/hooks/chat-v2/useScrollAnchor.ts` — add IntersectionObserver sentinel logic
- `platform/src/components/chat-v2/messages/ScrollToBottomButton.tsx` (new)
- `platform/src/components/chat-v2/messages/MessageList.tsx` (or chat viewport component) — wire sentinel + button
- `.github/workflows/deploy.yml` — add `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true`
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side streaming
- Phase 4C files
- `platform/src/components/chat-v2/ConsumeChatV2.tsx` (unless it owns the scroll container — executor confirms)

## Acceptance Criteria

1. **deploy.yml (Amendment 1 — HARD GATE):** `.github/workflows/deploy.yml` contains `--build-arg NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true` in the Docker build step. Session is NOT complete until this is present.
2. **Flag classification documented:** Brief (this file) declares flag as client-side NEXT_PUBLIC — executor confirms via grep before commit: `grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE" platform/src --include="*.ts*"`.
3. **click-path (Amendment 2):** User path: send a long query → while streaming, scroll up to read earlier content → auto-scroll stops → a "↓ N new" button appears at bottom right → clicking it scrolls to bottom and resumes auto-scroll. Document in commit body.
4. **IntersectionObserver sentinel:** A sentinel element at the bottom of the message list is observed. When sentinel is visible (user is at bottom), auto-scroll is enabled. When sentinel exits viewport (user scrolled away), auto-scroll is suppressed.
5. **ScrollToBottomButton:** Shows when auto-scroll is suppressed and new tokens are arriving. Displays unread chunk count (number of streaming token batches received while scrolled away). Clicking scrolls to bottom, hides button, re-enables auto-scroll.
6. **Flag guard:** When `NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE=false`, the old always-scroll behavior is preserved exactly.
7. **Parent-context integration test (Amendment 2):** At least one test mounts the full message list in its real scroll container/provider chain and asserts: (a) sentinel in viewport → auto-scroll fires, (b) sentinel out of viewport → auto-scroll suppressed + ScrollToBottomButton visible. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Amendment 1 gate — HARD
grep "NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE" .github/workflows/deploy.yml && echo "PASS: deploy.yml has flag" || echo "FAIL: HARD GATE — add to deploy.yml"

# Amendment 1 — classify client-side usage
grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE" platform/src --include="*.ts*" && echo "PASS: client-side usage confirmed" || echo "WARN: no usage found"

npx jest --testPathPattern="scroll|ScrollAnchor|ScrollToBottom" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): auto-scroll discipline — suppress when user scrolled away

useScrollAnchor gains IntersectionObserver sentinel. Auto-scroll fires
only when near bottom. ScrollToBottomButton shows unread count when
suppressed. Flagged MARSYS_FLAG_R10_SCROLL_DISCIPLINE=true (NEXT_PUBLIC +
deploy.yml build-arg per Amendment 1).

Click-path: streaming → scroll up → auto-scroll stops → "↓ N new" button → click → resumes.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
