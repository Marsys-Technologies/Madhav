---
canonical_id: CHAT_V2_R7_S6_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S6
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_DRAFT
authored: 2026-05-20
depends_on: []
---

## Context

R7 is the polish round for Chat V2 (post-cutover, post-§M.16 legacy deletion). R7-S6 adds per-conversation draft persistence so that a user who types a partial message, navigates away, and returns finds their draft restored from localStorage. This is a UX quality-of-life feature with no backend dependency.

Two files are touched: `useChatPreferences.ts` gains a new `useDraft` hook export, and `Composer.tsx` is wired to read, write, and clear the draft on mount, input change, and send respectively. No new feature flag is introduced — this behaviour is always-on once shipped, consistent with Chat V2's post-cutover flag-free posture.

## Files in scope

- `platform/src/hooks/useChatPreferences.ts` — add exported `useDraft` hook
- `platform/src/components/chat/Composer.tsx` — wire `conversationId` prop + draft read/write/clear

## Files must not touch

- `platform/src/components/chat/ConsumeChatV2.tsx`
- `platform/src/components/chat/ChatSidebar.tsx`
- `platform/src/components/chat/MessageList.tsx`
- `platform/src/hooks/useConversation.ts`
- `platform/src/lib/feature_flags.ts`
- `platform/src/app/consume/[chartId]/page.tsx`
- `platform/src/app/consume/[chartId]/layout.tsx`
- Any file under `platform/src/components/consume/` not listed in scope
- Any file under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `00_ARCHITECTURE/` (governance layer — read-only for this session)
- `platform/deploy.yml`
- `platform/tests/` (test files may be read for reference but must not be modified in this session)

## Acceptance criteria

### AC-1 — `useDraft` hook exported from `useChatPreferences.ts`

- `useDraft(conversationId: string | null)` is a named export.
- Signature returns a three-element tuple: `[draft: string, setDraft: (v: string) => void, clearDraft: () => void]`.
- Storage key is `madhav:draft:v1:${conversationId}` when `conversationId` is a non-empty string, and `madhav:draft:v1:__new__` when `conversationId` is `null`.
- On mount, `draft` is initialised from `localStorage.getItem(key) ?? ''` with an SSR guard (`typeof window !== 'undefined'`); when the guard is false, initial value is `''`.
- `setDraft(v)` writes `v` to localStorage via `localStorage.setItem(key, v)` and updates React state; it is a no-op when `v.length > 10000` (does not throw, does not write, does not update state).
- `clearDraft()` calls `localStorage.removeItem(key)` and resets React state to `''`.
- When `conversationId` changes (e.g. the component re-renders with a new id), the hook re-reads from localStorage for the new key and re-initialises `draft` accordingly. The previous key's localStorage entry is left untouched.

### AC-2 — `Composer.tsx` accepts `conversationId` prop

- `Composer` component interface gains `conversationId?: string | null` defaulting to `null`.
- Internally calls `useDraft(conversationId ?? null)` to obtain `[draft, setDraft, clearDraft]`.

### AC-3 — Mount restoration

- On mount (or whenever `conversationId` changes), `setInputValue(draft)` is called so the textarea is pre-populated with any persisted draft.
- If no draft exists for the key, the textarea initialises to `''` (existing behaviour preserved).

### AC-4 — Debounced write on change

- The `onChange` handler (or equivalent input event handler) calls `setDraft(value)` debounced by 400 ms.
- Debounce is implemented with `useRef<ReturnType<typeof setTimeout>>` + `clearTimeout` + `setTimeout` — no external debounce library is imported.
- The debounce timer is cleared on component unmount to prevent setState-after-unmount warnings.

### AC-5 — Clear on send

- When the form submit fires (message dispatched successfully), `clearDraft()` is called. Order relative to message dispatch is: clear draft first, then dispatch, or dispatch then clear — either is acceptable provided no draft lingers after a successful send.
- If the send fails (error thrown before dispatch resolves), `clearDraft()` is NOT called — the draft is preserved so the user can retry.

### AC-6 — New conversation edge case (`null` conversationId)

- When `conversationId` is `null`, draft is stored under the `__new__` key.
- On first successful send that produces a real conversation ID, the parent component is expected to pass the new `conversationId` down; at that point the hook re-initialises from the new key (which will be `''` for a brand-new conversation), and the `__new__` key entry is not automatically removed by the hook.
- `clearDraft()` called at send time operates on whichever key was active at send time (i.e. `__new__` for a new conversation), which effectively clears it.

### AC-7 — Switching conversations

- When the user navigates to a different conversation and `conversationId` prop changes, the textarea updates to reflect the stored draft (or empty string) for the new conversation within the same render cycle triggered by the prop change.
- The prior conversation's draft remains intact in localStorage and is restored if the user navigates back.

### AC-8 — Draft length guard

- Calling `setDraft` with a string longer than 10,000 characters is a no-op: localStorage is not written, React state is not updated, no error is thrown, no console warning is emitted.
- Characters typed beyond 10,000 are still visible in the textarea (controlled by local `inputValue` state), but are not persisted. The textarea itself imposes no hard maxLength attribute — the guard is in the hook only.

### AC-9 — SSR safety

- No `localStorage` access occurs during server-side rendering. The `typeof window !== 'undefined'` guard is present in the hook initialiser and in any `useEffect` or event handler that touches `localStorage`.
- The component tree renders without error in a Node.js/SSR environment (relevant for Next.js page pre-rendering).

### AC-10 — TypeScript — no new type errors

- `tsc --noEmit` passes across the two modified files with zero new errors introduced by this session's changes.

## Pre-commit gates

1. **TypeScript** — `cd platform && npx tsc --noEmit` exits 0. No new errors in `useChatPreferences.ts` or `Composer.tsx`.
2. **ESLint** — `cd platform && npx eslint src/hooks/useChatPreferences.ts src/components/chat/Composer.tsx --max-warnings 0` exits 0.
3. **Unit smoke** — if a Jest/Vitest test file for `useChatPreferences` exists, run it and confirm it passes; if none exists, this gate is waived for this session (test authoring is out of scope).
4. **Dev build** — `cd platform && npm run build` exits 0 (Next.js production build; confirms no import resolution failures or SSR-incompatible code paths).
5. **Manual spot-check** — in dev server, type a partial message, navigate away via sidebar, return; draft is restored. Submit a message; draft is cleared. Confirm localStorage key is present/absent via browser DevTools → Application → Local Storage.

## Commit message template

```
feat(composer): per-conversation localStorage draft persistence (R7-S6)

- Add useDraft(conversationId) hook to useChatPreferences.ts
  - Key: madhav:draft:v1:<id> (or __new__ for null id)
  - SSR-safe init; setDraft no-ops above 10 000 chars
  - clearDraft() removes key and resets state
- Wire Composer.tsx: mount restore, 400ms debounced write, clear on send
- Edge cases: null id → __new__ key; conversation switch re-reads new key

Refs: R7-S6 · CHAT_V2_R7_S6_BRIEF v1.0
```
