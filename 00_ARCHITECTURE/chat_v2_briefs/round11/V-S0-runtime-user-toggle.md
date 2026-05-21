---
canonical_id: R11_V_S0
version: 1.0
status: CURRENT
session_id: V-S0
title: Runtime user toggle — Classic Chat V2 ⇄ Claude-parity mode
depends_on: []
blocked_on: []
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — NEXT_PUBLIC env-var + localStorage user-pref"
authored: 2026-05-21
---

# V-S0 — Runtime User Toggle

## Context

Per native request 2026-05-21: users should be able to flip between the current
Chat V2 surface and the R11 Claude-parity surface **at runtime via a settings
toggle**, not only via a build-time env-var.

This session lands FIRST in R11 so that V-S1..V-S6 can wire to a unified
`useClaudeRendering()` hook from the start. The hook returns true iff
**both** are true:
- `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING === 'true'`
  (build-time kill-switch — the team's master switch)
- `userPref.chatRenderingMode === 'claude'`
  (per-browser preference — the user's choice)

With either false, the user sees the existing Chat V2. Defaults: env-var
**false** during initial rollout (kill-switch off so nothing is visible to
users); user-pref **'classic'** (even after env-var is flipped to true,
existing users stay on Classic until they opt in).

A small settings affordance (toggle in the user menu or sidebar header — the
executor picks the right surface) lets the user flip the preference live.

## Files in Scope

### Add

- `platform/src/lib/chat-v2/useClaudeRendering.ts` (new) — exports:
  - `useClaudeRendering()` React hook returning boolean.
  - `useChatRenderingMode()` hook returning `{ mode: 'classic' | 'claude', setMode: (m) => void, envEnabled: boolean }`.
  - Reads the env-var via `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING`.
  - Reads the user-pref via `localStorage.getItem('marsys.chatRenderingMode')`.
  - Writes via `localStorage.setItem(...)` AND dispatches a `storage`-style custom event so other tabs/components react.
  - SSR-safe (no `localStorage` access during render until `useEffect` mounts; sensible default fallback).
- `platform/src/components/consume/ChatRenderingToggle.tsx` (new) — small UI component:
  - When `envEnabled === false`: renders nothing (hidden).
  - When `envEnabled === true`: renders a labelled toggle "Use new Claude-parity interface" with current mode indicator and a help tooltip.
  - Uses the existing Marsys settings-component shape (border-radius, brand-gold focus, etc. — match existing settings affordances).
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_CLAUDE_RENDERING` flag (default false, NEXT_PUBLIC).
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING` to `--build-arg` block (Amendment 1 HARD GATE).
- `platform/tests/lib/chat-v2/useClaudeRendering.test.tsx` (new) — parent-context tests:
  - Hook returns false when env-var false (regardless of user-pref).
  - Hook returns false when user-pref 'classic' (regardless of env-var).
  - Hook returns true only when both gates are true.
  - `setMode('claude')` updates localStorage AND triggers re-render in other mounted components.
  - SSR rehydration: server-render returns false, client mount returns correct value (no hydration mismatch).
- `platform/tests/components/consume/ChatRenderingToggle.test.tsx` (new) — mount-verification:
  - When env-var stubbed false, toggle is not in DOM.
  - When env-var stubbed true and user-pref 'classic', toggle visible, switch off.
  - Clicking switch flips localStorage; assert subsequent read returns 'claude'.

### Modify

- `platform/src/components/consume/ConsumeChatV2.tsx` — mount `<ChatRenderingToggle />` in the existing settings surface (executor identifies the right slot — likely inside `ConversationSidebarV2` header or a settings dropdown). NO behavioral change yet — V-S1 onward wire actual rendering switching.

### Decision points the executor makes

1. **Toggle placement** — sidebar header / user menu / settings modal. Pick the
   surface that already exists and feels natural. Document choice in Decision Log.
2. **First-visit nudge** — optionally render a one-time tooltip / banner when the
   env-var is true and user-pref is still default ('classic') prompting the user
   to try the new interface. Optional; skip if it adds risk. Document choice.

## Files Must NOT Touch

- Any V-S1..V-S6 component yet (they will use the hook in their own sessions)
- `.consume-shell` styling
- PerMessageDetailsDrawer, PanelMember (sacred per NATIVE_RULINGS §5)
- Phase 4C files

## Acceptance Criteria

1. **Flag client-side + deploy.yml (Amendment 1):** `NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING` in both `feature_flags.ts` and `deploy.yml --build-arg`. Amendment 5 coverage check passes for this flag.
2. **Hook contract:** `useClaudeRendering()` returns `boolean`. True iff env-var === 'true' AND user-pref === 'claude'. Tests cover all four truth-table cells.
3. **Toggle UI gated on env-var:** With env-var=false, the toggle is not in the DOM. With env-var=true, the toggle is visible and functional.
4. **Persistence:** Flipping the toggle writes `'classic'` or `'claude'` to `localStorage['marsys.chatRenderingMode']`. Page refresh respects the saved value.
5. **Cross-tab sync (nice-to-have, not blocking):** Flipping the toggle in one tab updates other open tabs of the consume route via the `storage` event. If implementation cost is high, skip this AC and document in Decision Log.
6. **SSR safety:** `useClaudeRendering()` returns `false` during server render; on client hydration it returns the correct value. No React hydration-mismatch warnings in console.
7. **Click-path (Amendment 2):** With env-var=true: open consume route → find the settings affordance → toggle switch from off to on → page state updates (toggle stays on; localStorage updated). No visual change to chat content yet (V-S1 onward).
8. **Parent-context integration test (Amendment 2):** Mount `<ConsumeChatV2 />` with env-var stub'd true, assert `<ChatRenderingToggle />` renders inside it; simulate click on toggle; assert `useClaudeRendering()` consumers re-render with the new value.
9. **No regression when env-var=false:** ConsumeChatV2 renders byte-identical to pre-R11. The toggle is not in DOM. localStorage may have a stale value but it has no effect.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11/platform
test -f src/lib/chat-v2/useClaudeRendering.ts && echo "PASS: hook file exists"
test -f src/components/consume/ChatRenderingToggle.tsx && echo "PASS: toggle file exists"
grep -n "MARSYS_FLAG_R11_CLAUDE_RENDERING" src/lib/feature_flags.ts && echo "PASS: flag registered"
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING" ../.github/workflows/deploy.yml && echo "PASS: deploy.yml build-arg"
grep -n "ChatRenderingToggle" src/components/consume/ConsumeChatV2.tsx && echo "PASS: toggle mounted"
npx jest --testPathPattern="useClaudeRendering|ChatRenderingToggle|V-S0" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): runtime user toggle for R11 Claude-parity (V-S0)

Adds useClaudeRendering() hook AND-ing the env-var kill-switch with a per-browser
user-pref localStorage key. ChatRenderingToggle UI lets users opt into the R11
interface; env-var gates whether the toggle is even visible.

V-S1 onward wire their conditional to useClaudeRendering() rather than reading
the env-var directly, so flipping the toggle live (without redeploy) switches
the surface between Classic Chat V2 and Claude-parity mode.

Guarded by MARSYS_FLAG_R11_CLAUDE_RENDERING=false (NEXT_PUBLIC; deploy.yml
--build-arg added). Default user-pref 'classic'.

Click-path: env=true → open consume → settings → "Use new Claude-parity
interface" toggle → flip on → localStorage persists; V-S1 onward will swap
rendering live based on this state.
```

## Decision Log

*(Executor: paste the toggle placement choice (sidebar/menu/modal), whether
first-visit nudge was implemented, screenshot of the toggle in both states.)*
