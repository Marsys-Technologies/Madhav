---
canonical_id: CHAT_V2_R8_S6_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S6
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_SLASH
authored: 2026-05-20
depends_on: []
---

## Context

R8-S6 wires an inline `/` slash command menu into the chat composer. When the user types `/` at the start of their input or at a word boundary, a floating overlay appears above the textarea listing available commands, filterable by the text following `/`. The menu reuses the `Command[]` type already defined in `CommandPalette.tsx` and shares a single source-of-truth commands array extracted to `lib/chat-commands.ts`. This avoids duplicating command definitions between the palette (⌘K) and the inline trigger path.

The slash menu is a keyboard-first surface: arrow keys navigate, Enter selects and runs the command (or inserts its template into the composer), and Escape dismisses without side effects. Styling mirrors the existing `CommandPalette` aesthetic (zinc-900 background, amber accent on the active item, zinc-700 border) so both surfaces feel like a unified command system.

The feature is guard-flagged under `MARSYS_FLAG_R8_SLASH` so it can be enabled per-environment independently of other R8 work.

## Files in scope

| Path | Action |
|---|---|
| `platform/src/components/chat/SlashCommandMenu.tsx` | CREATE — new floating menu component |
| `platform/src/lib/chat-commands.ts` | CREATE — shared `COMMANDS` const + re-export of `Command` type |
| `platform/src/components/chat/CommandPalette.tsx` | MODIFY — import `COMMANDS` from `lib/chat-commands.ts`; remove inline commands array; re-export `Command` type if not already exported |
| `platform/src/components/consume/ConsumeChatV2.tsx` | MODIFY — pass `COMMANDS` into `Composer` via prop; wire `MARSYS_FLAG_R8_SLASH` gate |
| `platform/src/components/chat/Composer.tsx` | MODIFY — add slash-detection logic, `SlashCommandMenu` rendering, `useRef` anchor computation, command dispatch |
| `platform/src/lib/feature_flags.ts` | MODIFY — add `MARSYS_FLAG_R8_SLASH` boolean flag (default `false`) |

## Files must not touch

- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `06_LEARNING_LAYER/**`
- `00_ARCHITECTURE/**` (except this brief — no governance artifact mutations during execution)
- `platform/src/server/**`
- `platform/src/app/api/**`
- `platform/scripts/**`
- `platform/tests/**` (test additions permitted only if the session has remaining capacity; do not break existing tests)
- Any file not listed in the "Files in scope" table above

## Acceptance criteria

1. **Trigger condition — word boundary only.** Typing `/` as the first character of the composer input, or immediately after a space, opens `SlashCommandMenu`. Typing `/` in the middle of a word (e.g. `path/to/file`) does NOT trigger the menu.

2. **Filter behavior.** After the trigger `/`, any additional characters narrow the displayed list: typing `/dasha` shows only commands whose `name` starts with `"dasha"` (case-insensitive) OR whose `description` includes `"dasha"` (case-insensitive). An unmatched query shows an empty list (menu remains open but empty is acceptable; alternatively hide it — implementation choice, but must not crash).

3. **Maximum visible items.** The menu renders at most 6 items in the visible viewport. If the filtered list exceeds 6, the container is scrollable.

4. **Keyboard navigation.** Arrow-Down and Arrow-Up cycle through list items. The active item receives the amber accent style. Enter on the active item: if `cmd.run` exists, call `cmd.run()`; otherwise insert `cmd.template` at the cursor position in the composer textarea. Either action also closes the menu and, where template insertion occurred, positions the cursor at the end of the inserted text.

5. **Escape dismissal.** Pressing Escape while the menu is open closes it without clearing or modifying the composer input.

6. **Blur dismissal.** If the composer textarea loses focus, the menu closes after a 150 ms debounce (to allow click-selection of a menu item before blur fires).

7. **Positioning.** The menu is absolutely positioned so its bottom edge aligns with (or sits just above) the top of the textarea. It must not overlap the textarea content. If the viewport is too short, the menu clips upward rather than downward.

8. **Flag gate.** The slash menu feature is entirely absent (not rendered, no event listeners wired) when `MARSYS_FLAG_R8_SLASH` evaluates to `false`. The `CommandPalette` (⌘K) continues to function regardless of the flag.

9. **Shared command source.** `CommandPalette.tsx` and `SlashCommandMenu.tsx` both import commands from `platform/src/lib/chat-commands.ts`. There are zero inline command literal arrays remaining in either component file after this session.

10. **TypeScript clean.** `tsc --noEmit` exits 0. No `any` types introduced in new or modified files. The `Command` type is imported from `lib/chat-commands.ts` wherever used; no re-declaration.

11. **No regressions.** The existing `CommandPalette` (⌘K trigger) continues to open and function identically to its pre-session behavior. Existing composer behavior (send on Enter, multiline on Shift+Enter, stop button, synthesis-done stage display) is unaffected.

## Pre-commit gates

Run all of the following and confirm each exits 0 (or produces no new errors beyond pre-existing known residuals) before committing:

```bash
# 1. TypeScript
cd platform && npx tsc --noEmit

# 2. ESLint (scoped to modified files)
npx eslint src/components/chat/SlashCommandMenu.tsx \
           src/components/chat/CommandPalette.tsx \
           src/components/chat/Composer.tsx \
           src/components/consume/ConsumeChatV2.tsx \
           src/lib/chat-commands.ts \
           src/lib/feature_flags.ts \
           --max-warnings=0

# 3. Unit tests (if any exist for chat components)
npx jest --testPathPattern="chat" --passWithNoTests

# 4. Build smoke
npx next build --no-lint 2>&1 | tail -20
```

If `next build` fails on a pre-existing error unrelated to this session's changes, document the error in the commit message body under `known_residuals:` and proceed. Do not introduce new build errors.

## Commit message template

```
feat(chat): R8-S6 inline slash command menu in composer

- New SlashCommandMenu.tsx: floating overlay above textarea, max-6
  visible items, keyboard nav (↑↓ Enter Escape), blur-dismiss 150ms
- New lib/chat-commands.ts: shared COMMANDS const + Command type export
- CommandPalette.tsx: import COMMANDS from lib/chat-commands (no dupe)
- Composer.tsx: slash-detection at word boundary, anchorRect via useRef,
  cmd.run() or template insertion on select
- ConsumeChatV2.tsx: pass COMMANDS prop; gate on MARSYS_FLAG_R8_SLASH
- feature_flags.ts: add MARSYS_FLAG_R8_SLASH (default false)

Acceptance: AC1-AC11 verified. tsc clean. No any types.

brief: CHAT_V2_R8_S6_BRIEF v1.0
round: R8 | session: R8-S6
flag: MARSYS_FLAG_R8_SLASH (default off)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
