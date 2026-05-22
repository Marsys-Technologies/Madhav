---
canonical_id: R11A_A_S11
session_id: A-S11
title: Runtime user toggle — Classic ⇄ Multi-Provider-Parity chat shell
phase: R11.A — Foundation
depends_on: [A-S10]
flag: MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY
flag_default: false
client_side: "yes — NEXT_PUBLIC env-var + localStorage user-pref"
authored: 2026-05-22
---

# A-S11 — Runtime User Toggle

## Context

Adapted from R11 v1's V-S0 design (per `SUPERSESSION_NOTE.md §2` carry-forward). The user can flip between the **Classic Chat V2** surface and the **Multi-Provider-Parity** surface at runtime, without redeploy.

A new hook `useMultiProviderParity()` returns boolean. Returns true iff:
1. `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY === 'true'` (build-time master kill-switch)
2. `localStorage['marsys.chatShellMode'] === 'multi-provider'` (per-browser user preference)

A `MultiProviderParityToggle` settings UI (visible only when env-var is true) lets the user flip the preference live.

After A-S11 lands, the adapter layer is reachable from the chat surface IFF this hook returns true. Subsequent phases (R11.B, R11.C, …) gate THEIR changes on this hook so the entire arc rolls out behind one umbrella opt-in.

## Files in Scope

### Add

- `platform/src/lib/chat-v2/useMultiProviderParity.ts` — exports:
  - `useMultiProviderParity()` hook returning boolean.
  - `useChatShellMode()` hook returning `{ mode: 'classic' | 'multi-provider', setMode: (m) => void, envEnabled: boolean }`.
  - SSR-safe (no `localStorage` access during render until `useEffect` mounts).
  - Cross-tab sync via `storage` event.
- `platform/src/components/consume/MultiProviderParityToggle.tsx` — settings toggle. Hidden when env-var false; visible + labeled when true ("Use Multi-Provider Parity interface — try the redesigned chat with best-of-each-provider capabilities").
- `platform/tests/lib/chat-v2/useMultiProviderParity.test.tsx` — parent-context tests on the truth table (4 cells).
- `platform/tests/components/consume/MultiProviderParityToggle.test.tsx` — mount-verification.

### Modify

- `platform/src/lib/config/feature_flags.ts` — register `MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` (default false, NEXT_PUBLIC).
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` to `--build-arg` block (Amendment 1).
- `platform/src/components/consume/ConsumeChatV2.tsx` — mount `<MultiProviderParityToggle />` in the existing settings affordance slot.

## Files MUST NOT Touch

- Any visual / streaming code yet (R11.B/R11.C own those)
- `.consume-shell` styling
- Sacred components

## Acceptance Criteria

1. Flag client-side + deploy.yml (Amendment 1): `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` in both `feature_flags.ts` and `deploy.yml --build-arg`. R11A-MERGE Amendment 5 coverage check passes.
2. Hook truth table: returns true iff BOTH env-var true AND user-pref `'multi-provider'`. Tests cover all 4 cells.
3. Toggle UI gated on env-var: hidden when false; visible when true.
4. Persistence: flipping toggle writes localStorage; page refresh respects.
5. SSR safety: hook returns false during server render; correct on client hydration; no hydration warnings.
6. Cross-tab sync: flipping in one tab updates other open consume tabs (storage event).
7. Click-path (Amendment 2): env=true → open consume → find toggle → flip on → localStorage updates; no visual change to chat (visual changes ship in R11.B).
8. Parent-context integration test: mount ConsumeChatV2 with env stub'd true; assert toggle renders; click; assert hook returns true.
9. No regression with env-var=false: existing chat renders byte-identical; toggle not in DOM.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/chat-v2/useMultiProviderParity.ts && echo "PASS"
test -f src/components/consume/MultiProviderParityToggle.tsx && echo "PASS"
grep -n "MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY" src/lib/config/feature_flags.ts && echo "PASS: flag registered"
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY" ../.github/workflows/deploy.yml && echo "PASS: deploy.yml"
grep -n "MultiProviderParityToggle" src/components/consume/ConsumeChatV2.tsx && echo "PASS: toggle mounted"
npx jest --testPathPattern="useMultiProviderParity|MultiProviderParityToggle|A-S11" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): runtime user toggle for Multi-Provider Parity arc (A-S11)

useMultiProviderParity() hook ANDs env-var kill-switch with per-browser
user-pref localStorage. MultiProviderParityToggle UI lets users opt into
the new chat shell; env-var gates toggle visibility.

Subsequent R11 v2 phases (R11.B..R11.K) gate their changes on this hook so
the arc rolls out behind a single user-facing opt-in.

Guarded by MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=false (NEXT_PUBLIC;
deploy.yml --build-arg added). Default user-pref 'classic'.

Carry-forward from R11 v1 V-S0 design per SUPERSESSION_NOTE §2.

Click-path: env=true → open consume → toggle → opt in; later phases swap
rendering live based on hook state.
```

## Decision Log

*(Executor: paste toggle placement choice, screenshots in both states; document the storage-event cross-tab sync implementation.)*
