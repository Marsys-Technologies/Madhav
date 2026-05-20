---
canonical_id: R10_X_S2
version: 1.0
status: CURRENT
session_id: X-S2
title: Recall last prompt via ArrowUp in empty composer
depends_on: [X-S1]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — client-only localStorage/hook behavior"
authored: 2026-05-20
---

# X-S2 — Recall Last Prompt

## Context

A common UX pattern in chat interfaces: pressing `ArrowUp` in an empty composer input restores the user's last sent message for that conversation. This allows quick re-send or minor edits without retyping.

Implementation: `useChatPreferences` (or a new dedicated hook `useLastPrompt`) maintains a `lastSent: Record<conversationId, string>` cache in `localStorage`. On `keydown ArrowUp` when the composer value is empty string, restore the last sent value for the active conversation.

**Amendment 3:** FLAGLESS — additive UX behavior, no backend, no schema. Was originally considered for flagging but §M.16 classifies it as safe additive polish.

**Amendment 2:** Visible component (Composer textarea) → click-path and parent-context test required.

## Files in Scope

- `platform/src/hooks/chat-v2/useChatPreferences.ts` — add `lastSent` cache management (OR new `platform/src/hooks/chat-v2/useLastPrompt.ts`)
- `platform/src/components/chat-v2/composer/Composer.tsx` — wire `onKeyDown` handler
- `platform/tests/` — integration test mounting ChatShell/ConsumeChatV2

## Files Must NOT Touch

- Any server-side files
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: open a Chat V2 conversation → send a message → clear the composer → press ArrowUp → previous message text appears in the composer. Document in commit body.
2. **Per-conversation cache:** `lastSent` is keyed by `conversationId` so switching conversations does not bleed prompts across conversations.
3. **Empty-composer guard:** ArrowUp only recalls when the composer is empty (value `=== ""`). If the composer has text, ArrowUp behaves normally (cursor up, or no-op).
4. **localStorage persistence:** The cache survives page refresh (stored in localStorage, not just React state). Key pattern: `marsys_chat_v2_last_prompt_<conversationId>` or equivalent under `useChatPreferences` namespace.
5. **No ArrowUp conflicts:** Does not interfere with multiline textarea cursor navigation when there is text in the composer.
6. **Parent-context integration test (Amendment 2):** At least one test mounts the full ChatShell or ConsumeChatV2 (providing ChatPrefsCtx/conversation context) and asserts: (a) composing and "sending" a message updates lastSent, (b) ArrowUp in empty composer restores the message. Leaf test with props injected directly does NOT satisfy this AC.

## Pre-commit Gates

```bash
npx jest --testPathPattern="recall|lastPrompt|last-prompt|useChatPreferences" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): ArrowUp in empty composer recalls last sent prompt

Per-conversation lastSent cache in useChatPreferences (localStorage).
ArrowUp restores last message only when composer is empty; no-op
otherwise. Flagless per §M.16.

Click-path: send message → clear composer → ArrowUp → message restored.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
