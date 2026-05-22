---
canonical_id: R11B_B_S0
session_id: B-S0
title: Adapter health check + hook integration verification
phase: R11.B — Look-and-Feel
depends_on: []
flag: FLAGLESS
client_side: "yes — read-only verification"
authored: 2026-05-22
---

# B-S0 — Adapter Health Check

## Context

Confirm that R11.A's foundation is healthy from R11.B's perspective. Verify the `useMultiProviderParity()` hook exists, the dispatcher is reachable, and the `CapabilityHint` component is mountable. This session writes a small smoke component (mounted in dev-only) that renders the active provider's manifest summary — useful for debugging during the subsequent R11.B sessions.

## Files in Scope

- `platform/src/components/dev/R11BHealthCheck.tsx` (new, dev-only) — renders the active manifest as a small debug panel. Mounted conditionally when `NODE_ENV !== 'production'`.
- `platform/tests/dev/R11BHealthCheck.test.tsx` — asserts the component reads the dispatcher manifest correctly.

## Files MUST NOT Touch

- Production UI components (subsequent B sessions own those)
- `platform/src/lib/providers/**` (R11.A territory)
- Phase 4C files

## Acceptance Criteria

1. `R11BHealthCheck` renders the active provider's manifest summary (capability count, manifest hash).
2. Component is dev-only — production bundle excludes it.
3. Test passes verifying manifest read.
4. `useMultiProviderParity()` hook is reachable and returns expected boolean.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
test -f src/components/dev/R11BHealthCheck.tsx && echo "PASS"
npx jest --testPathPattern="R11BHealthCheck|B-S0" --passWithNoTests
```

## Commit Template

```
chore(chat-v2): R11.B foundation health check (B-S0)

Dev-only component verifies R11.A adapter substrate is healthy from R11.B's
perspective. Flagless per §M.16.
```

## Decision Log

*(Executor: paste manifest read output for each of the 5 stacks.)*
