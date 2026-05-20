---
canonical_id: R10_X_S4
version: 1.0
status: CURRENT
session_id: X-S4
title: Still-working indicator after 25s of streaming silence
depends_on: [X-S3]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — client-only timer component"
authored: 2026-05-20
---

# X-S4 — Still-Working Indicator

## Context

Astrological synthesis queries can take 30–90 seconds. During long server-side processing there may be periods of streaming silence (no new tokens arriving). Users currently have no feedback that the system is still working and not stuck. A "still working" indicator — a subtle animated message like "Still working…" or a spinner with elapsed time — reassures the user.

Implementation:
- New `StillWorkingIndicator.tsx` component: shows when `isStreaming && isLastMessage && elapsed > 25s`.
- Wired in `AssistantMessage.tsx` (or wherever the streaming assistant bubble is rendered).
- Auto-hides when the next token arrives or streaming ends.

**Amendment 3:** FLAGLESS — additive component, shown only during long streaming gaps, no behavior change.

**Amendment 2:** Visible component → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/messages/StillWorkingIndicator.tsx` (new)
- `platform/src/components/chat-v2/messages/AssistantMessage.tsx` — wire indicator
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side streaming code
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: send a complex query in Chat V2 → after 25 seconds of streaming silence, a "Still working…" (or equivalent) indicator appears below the streaming response. When the next token arrives the indicator disappears. Document in commit body.
2. **`StillWorkingIndicator` component:** Renders an animated message (dots, spinner, or progress text) with optional elapsed time display. Accessible: `aria-live="polite"`.
3. **Threshold:** Indicator appears only after 25 seconds of no new streaming tokens arriving, when the message is both `isStreaming` and `isLastMessage`. Not shown on complete messages.
4. **Auto-hide:** Clears immediately when (a) new token arrives, (b) streaming ends (success or error).
5. **Timer cleanup:** `clearInterval`/`clearTimeout` on unmount to prevent memory leaks.
6. **Parent-context integration test (Amendment 2):** At least one test mounts `AssistantMessage` within the ChatShell or ConsumeChat V2 shell (real isStreaming context, not props-injected mock) and asserts: (a) indicator is NOT visible at T<25s, (b) indicator IS visible at T>25s of simulated streaming silence (advance fake timers). Leaf-with-props test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
npx jest --testPathPattern="StillWorking|stillWorking|still-working|AssistantMessage" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): still-working indicator after 25s of streaming silence

StillWorkingIndicator.tsx mounted in AssistantMessage when isStreaming
&& isLastMessage && elapsed > 25s. Auto-clears on next token or stream
end. Accessible aria-live. Flagless per §M.16.

Click-path: long query → 25s silence → indicator appears → token arrives → clears.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
