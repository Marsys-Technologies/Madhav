---
canonical_id: CHAT_V2_R7_S7_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S7
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_A11Y
authored: 2026-05-20
depends_on: []
---

## Context

R7-S7 delivers the accessibility polish layer for Chat V2. Four discrete improvements are in scope: (1) a screen-reader live-region announcement when streaming ends, (2) a skip-to-content link at the top of the chat layout, (3) keyboard message navigation via `j`/`k` hotkeys, and (4) keyboard shortcuts for per-message actions (copy, edit, regenerate) when a message row holds focus. All four changes target WCAG 2.1 AA conformance and must not introduce regressions in the existing tab order or hotkey surface.

The Chat V2 Big Bang workstream was declared COMPLETE at sealing-merge `6c431f9` (PR #82, 2026-05-18). R7 is the post-cutover polish round. There is no legacy code path; `ConsumeChatLegacy.tsx` is deleted. The flag `MARSYS_FLAG_R7_A11Y` does not gate the feature in production — it exists solely as a CI environment-variable sentinel for the a11y test suite. All four changes ship unconditionally.

---

## Files in scope

```
platform/src/components/chat/AssistantMessage.tsx
platform/src/components/chat/ChatShell.tsx
platform/src/components/chat/MessageActions.tsx
platform/src/components/chat/MessageList.tsx
platform/src/components/chat/VirtualizedMessageList.tsx   # if this file exists; else MessageList.tsx only
platform/src/hooks/useHotkeys.ts
```

Supporting test files (create or extend as needed):

```
platform/tests/unit/a11y/stream-end-announcement.test.tsx
platform/tests/unit/a11y/skip-link.test.tsx
platform/tests/unit/a11y/keyboard-nav.test.tsx
platform/tests/unit/a11y/message-action-shortcuts.test.tsx
```

---

## Files must not touch

```
platform/src/components/chat/ConsumeChatLegacy.tsx        # deleted; must not be recreated
platform/src/feature_flags.ts                             # R7 ships no new feature flags
platform/src/components/chat/ConsumeChat.tsx              # re-export shim; do not modify
platform/src/components/consume/ConsumeChatV2.tsx         # out of R7-S7 scope; modified separately
platform/deploy.yml
platform/chat-v2-ci.yml
00_ARCHITECTURE/**                                        # governance docs; brief is self-contained
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**
```

---

## Acceptance criteria

### AC-1 — Stream-end screen-reader announcement

- `AssistantMessage.tsx` (or `ChatShell.tsx` if the streaming state is owned there) contains a `<span role="status" aria-live="polite" className="sr-only">` that is always present in the DOM.
- A `useEffect` watching the `isStreaming` boolean updates the span's text content to `"Response complete"` on the `false` → `true` transition (i.e., when streaming stops).
- The span is empty while streaming is in progress or before the first stream.
- Verified by a unit test that uses an `aria-live` spy (e.g., `@testing-library/react` + `jest-axe` or a manual mock) confirming the text update fires exactly once per stream completion.
- No new WCAG 2.1 AA violations introduced (axe-core or equivalent).

### AC-2 — Skip-to-content link

- `ChatShell.tsx` renders the following as the first focusable element in the DOM:
  ```tsx
  <a
    href="#chat-main"
    className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-3 focus:py-2 focus:bg-zinc-900 focus:text-amber-400 focus:rounded"
  >
    Skip to chat
  </a>
  ```
- The `<main>` element wrapping the chat message area carries `id="chat-main"`. If the id is not already present, it is added in this session.
- Tab order verified manually: Tab from page load focuses the skip link first; activating it moves focus to `#chat-main`; subsequent Tab presses reach the composer input.
- Unit test asserts the anchor is the first child of the shell root and that `href="#chat-main"` resolves to an element in the rendered tree.

### AC-3 — Keyboard message navigation (`j` / `k`)

- `useHotkeys.ts` registers `j` and `k` handlers that are no-ops when `document.activeElement` is an input, textarea, or contenteditable element.
- Each message row rendered by `MessageList.tsx` (or `VirtualizedMessageList.tsx`) carries:
  - `data-message-index={index}` attribute.
  - `tabIndex={-1}` on the outermost container div so it is programmatically focusable but not in the natural tab sequence.
- `j` focuses the next message row (by incrementing the currently-tracked index); `k` focuses the previous row. Wrapping at list boundaries is not required but must not throw.
- Focus is applied via `ref.focus()` or `element.focus()` called on the target row's DOM node.
- Unit test: renders a list of three messages, simulates `j` twice, asserts `document.activeElement` equals the third message container.

### AC-4 — Message action keyboard shortcuts

- When a message row holds focus (i.e., the row's container div is `document.activeElement`):
  - `c` triggers the copy action (same handler as the existing copy button in `MessageActions.tsx`).
  - `e` triggers edit (user messages only; no-op on assistant messages).
  - `r` triggers regenerate (assistant messages only; no-op on user messages).
- Implemented via an `onKeyDown` handler on the focused message container div. The handler ignores events when a modifier key (`ctrlKey`, `metaKey`, `altKey`) is held.
- `MessageActions.tsx` exposes the copy/edit/regenerate handlers so the container can call them without duplicating logic.
- Unit test: for a focused user message row, simulates `KeyboardEvent` with `key="c"` and asserts the copy handler was called; simulates `key="e"` and asserts edit handler called; simulates `key="r"` and asserts it is not called (user message).

### AC-5 — No regression

- Existing hotkey registrations in `useHotkeys.ts` (if any) continue to function.
- Tab order in the composer area is unchanged.
- The `axe-core` audit (run in CI via `jest-axe` or a Playwright a11y snapshot) reports zero new violations compared to the pre-R7-S7 baseline.

---

## Pre-commit gates

All of the following must pass before the commit is created:

```bash
# 1. TypeScript — no new type errors
cd platform && npx tsc --noEmit

# 2. Lint
cd platform && npx eslint src/components/chat/AssistantMessage.tsx \
  src/components/chat/ChatShell.tsx \
  src/components/chat/MessageActions.tsx \
  src/components/chat/MessageList.tsx \
  src/hooks/useHotkeys.ts \
  --max-warnings 0

# 3. Unit tests (a11y suite)
cd platform && npx jest tests/unit/a11y/ --passWithNoTests

# 4. Axe-core snapshot (if jest-axe is available)
cd platform && npx jest --testPathPattern="a11y" --passWithNoTests

# 5. Full unit suite — no regressions
cd platform && npx jest --passWithNoTests
```

Gate failure on any of the above blocks the commit. Fix before proceeding.

---

## Commit message template

```
feat(a11y): R7-S7 accessibility polish — stream-end announcement, skip link, keyboard nav, message shortcuts

- AssistantMessage/ChatShell: aria-live polite region announces "Response complete" on stream end
- ChatShell: skip-to-content link (#chat-main) as first focusable element; main gets id="chat-main"
- useHotkeys + MessageList: j/k keyboard navigation between message rows (tabIndex=-1 + data-message-index)
- MessageActions + message containers: onKeyDown c/e/r shortcuts for copy, edit, regenerate
- Unit tests: stream-end spy, skip-link resolution, j/k focus assertion, action shortcut guards
- No new WCAG 2.1 AA violations (axe-core clean)

Session: R7-S7 | Brief: CHAT_V2_R7_S7_BRIEF v1.0
```
