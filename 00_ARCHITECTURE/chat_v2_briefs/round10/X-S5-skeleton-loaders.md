---
canonical_id: R10_X_S5
version: 1.0
status: CURRENT
session_id: X-S5
title: Skeleton loaders for sidebar and chat header
depends_on: [X-S4]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — client-only loading state components"
authored: 2026-05-20
---

# X-S5 — Skeleton Loaders

## Context

Chat V2 has loading states (conversations list loading, header conversation title loading) that currently render blank space or a simple spinner. Skeleton loaders — animated placeholder UI matching the shape of the real content — provide a better perceived performance experience.

Two skeleton components needed:
1. **SidebarSkeleton** — replaces the conversation list while it loads.
2. **HeaderSkeleton** — replaces the conversation title + toolbar while loading.

Both are mounted in their respective layout slots, conditional on the data-loading state flag from existing hooks/contexts.

**Amendment 3:** FLAGLESS — purely additive visual components, no data or behavior change.

**Amendment 2:** Visible components → click-path and parent-context test required.

## Files in Scope

- `platform/src/components/chat-v2/sidebar/SidebarSkeleton.tsx` (new)
- `platform/src/components/chat-v2/header/HeaderSkeleton.tsx` (new)
- `platform/src/components/chat-v2/sidebar/ConversationSidebar.tsx` — mount SidebarSkeleton when loading
- `platform/src/components/chat-v2/header/ChatHeader.tsx` (or equivalent) — mount HeaderSkeleton when loading
- `platform/tests/` — integration tests

## Files Must NOT Touch

- Server-side files
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: navigate to Chat V2 on a slow/throttled network → before the conversation list loads, the sidebar shows animated skeleton rows matching the approximate height/width of conversation items. Similarly the header shows a skeleton title placeholder. Document in commit body.
2. **SidebarSkeleton:** Renders 5–7 animated skeleton rows resembling conversation list items (avatar + two text lines each). Uses CSS animation (pulse/shimmer) or Tailwind `animate-pulse`.
3. **HeaderSkeleton:** Renders a skeleton title bar matching the height of the real header, with a short skeleton rectangle where the conversation title appears.
4. **Conditional mount:** Skeletons shown only when `isLoading === true` from the respective data hook. Not shown on loaded or error states.
5. **No layout shift:** Skeleton dimensions approximate real content dimensions to prevent layout shift on reveal.
6. **Accessibility:** Skeleton containers have `aria-hidden="true"` (decorative; real content loads in).
7. **Parent-context integration test (Amendment 2):** At least one test mounts `ConversationSidebar` within its real provider chain (ConvListCtx or equivalent, with `isLoading: true`) and asserts `SidebarSkeleton` renders. At least one test mounts `ChatHeader` within its real provider chain (`isLoading: true`) and asserts `HeaderSkeleton` renders. Leaf-with-props tests alone do NOT satisfy this AC.

## Pre-commit Gates

```bash
npx jest --testPathPattern="Skeleton|skeleton|SidebarSkeleton|HeaderSkeleton" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): skeleton loaders for sidebar and header loading states

SidebarSkeleton + HeaderSkeleton components replace blank/spinner states
during data load. Mounted conditionally on isLoading from existing context.
Animate-pulse shimmer, aria-hidden. Flagless per §M.16.

Click-path: load Chat V2 on slow network → skeleton appears → content loads in.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
