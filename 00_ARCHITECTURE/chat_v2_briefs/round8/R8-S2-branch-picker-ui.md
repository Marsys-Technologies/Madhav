---
canonical_id: CHAT_V2_R8_S2_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S2
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_BRANCHES
authored: 2026-05-20
depends_on: [R8-S1]
---

## Context

R8-S2 implements the `BranchPicker` UI component and wires it into the message render tree. R8-S1 established the `useBranches` hook with in-memory branch state; R8-S2 surfaces that state to the user as a compact `‹ 2/3 ›` inline control that appears beneath edited user message bubbles. All navigation logic lives in the hook; `BranchPicker` is a pure display component with no internal state.

This component is the primary interaction surface for the multi-branch edit capability introduced in R8. It must be fully keyboard-accessible and screen-reader-friendly because branch navigation is a core part of reviewing how an edited conversation diverged.

## Files in scope

- `platform/src/components/chat/BranchPicker.tsx` — **new file** — pure display component
- `platform/src/components/chat/BranchPicker.test.tsx` — **new file** — unit tests
- `platform/src/components/chat/UserMessage.tsx` — integrate `BranchPicker` below the message bubble when branches > 1
- `platform/src/hooks/useBranches.ts` — read-only integration (consume `branchesForMessage` + `activeBranch`; do not alter hook internals unless strictly required for wiring)
- `platform/src/components/chat/index.ts` — export `BranchPicker` if a barrel export file exists

## Files must not touch

- `platform/src/components/consume/ConsumeChatV2.tsx`
- `platform/src/hooks/useMessages.ts`
- `platform/src/hooks/useChat.ts`
- `platform/src/lib/pipeline/**`
- `platform/src/components/chat/AssistantMessage.tsx`
- `platform/src/app/**` (route files)
- `platform/src/feature_flags.ts`
- Any file under `00_ARCHITECTURE/` except this brief (no governance artifacts to be modified during execution)
- Any file outside `platform/src/components/chat/` and `platform/src/hooks/` not listed above

## Acceptance criteria

1. **BranchPicker renders on edited messages** — when `useBranches().branchesForMessage(messageId)` returns an array with `length > 1`, a `<BranchPicker>` element appears inline below the corresponding user message bubble; it does not render for single-branch or never-edited messages.
2. **Display format** — the component renders `‹ {currentBranch}/{totalBranches} ›` where `currentBranch` is 1-indexed and `totalBranches` is the array length; the fraction is a `<span>` between two `<button>` elements, all on one line.
3. **Prev navigation** — clicking `‹` calls `onPrev` which invokes the `useBranches` switch action to move the active branch index backward by one; the conversation thread view reflects the preceding branch content.
4. **Next navigation** — clicking `›` calls `onNext` which invokes the `useBranches` switch action to move the active branch index forward by one; the conversation thread view reflects the next branch content.
5. **Disabled on boundary — prev** — the `‹` button has `disabled` attribute set and is not interactive when `currentBranch === 1`.
6. **Disabled on boundary — next** — the `›` button has `disabled` attribute set and is not interactive when `currentBranch === totalBranches`.
7. **Keyboard accessibility** — both buttons are reachable via Tab; Enter and Space activate them; disabled buttons are skipped in tab order (`disabled` attribute handles this natively).
8. **Screen reader** — `‹` button carries `aria-label="Previous branch"`; `›` button carries `aria-label="Next branch"`; disabled state is communicated via the native `disabled` attribute (no `aria-disabled` needed alongside it).
9. **Styling** — component is compact and inline: container uses `inline-flex items-center gap-1`; fraction span uses `text-xs text-zinc-400`; separator between fraction digits uses `text-zinc-600`; active buttons use `hover:text-zinc-100 transition-colors`; disabled buttons use `opacity-40 cursor-not-allowed`.
10. **TypeScript strict** — no `any` types anywhere in `BranchPicker.tsx`; props interface explicitly typed; component is compatible with `strict: true` in `tsconfig.json`.
11. **No regressions** — existing message rendering for non-branched conversations is unaffected; no layout shift introduced on messages without branches.
12. **Test suite passes** — `npm test -- --filter=BranchPicker` exits 0; all three rendering states (first branch, last branch, middle branch) are covered with assertions on disabled attribute and aria-labels.

## Pre-commit gates

1. `npx tsc --noEmit` — must exit 0 with no new type errors.
2. `npm test -- --filter=BranchPicker` — must exit 0; all test cases green.
3. `npm run lint` (or `npx eslint platform/src/components/chat/BranchPicker.tsx platform/src/components/chat/UserMessage.tsx`) — must exit 0 with no new lint errors.
4. Manual smoke: open the app with `MARSYS_FLAG_R8_BRANCHES=true`, edit a user message to create at least two branches, confirm `‹ 1/2 ›` appears below the edited bubble, confirm `‹` is disabled on branch 1, click `›` to advance to branch 2, confirm `›` is disabled, confirm conversation thread reflects branch 2 content.
5. Manual a11y: Tab to `‹`, press Enter — verify branch switches; Tab to `›`, press Enter — verify branch switches; confirm screen reader announces button labels (use VoiceOver on macOS or axe DevTools).

## Commit message template

```
feat(chat-v2/r8-s2): BranchPicker component + UserMessage integration

- Add BranchPicker.tsx: pure display component rendering ‹ N/M › with
  disabled states on boundaries and full keyboard/a11y support
- Wire BranchPicker into UserMessage.tsx via useBranches hook;
  renders only when branchesForMessage().length > 1
- Add BranchPicker.test.tsx: first/last/middle branch rendering states,
  disabled attribute assertions, aria-label coverage

Depends-on: R8-S1 (useBranches hook)
Flag: MARSYS_FLAG_R8_BRANCHES=true
```
