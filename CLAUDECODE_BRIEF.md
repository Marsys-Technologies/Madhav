---
status: OPEN
session_id: AIOPS_CO_4
phase: CO.4
phase_name: "Sidebar UX — hover-expand / click-pin (Bug 3.2)"
next_session: AIOPS_CO_5
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_4
## AIOps Phase 3, Step 4 — Sidebar hover-expand + click-pin (Bug 3.2)

---

## §0 — Executor orientation

CO.4 fixes Bug 3.2 — left side panel doesn't auto-expand on hover or
collapse on mouse-out. Target behavior: hover to expand, mouse-out to
collapse, click to pin (locks in expanded state). Mobile fallback: tap-to-open as an overlay.

Behind `CONSUME_UI_V2_ENABLED`.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md (component 3 — sidebar)
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/components/chat/ConversationSidebar.tsx (target component)
5. platform/src/components/consume/ConversationHistoryDrawer.tsx (existing drawer pattern)
6. platform/src/components/shared/AppShell.tsx (parent layout — verify no conflict)
7. platform/src/lib/utils.ts (cn() class helper)
```

---

## §2 — Scope

### may_touch
```
platform/src/components/chat/ConversationSidebar.tsx     # primary refactor
platform/src/components/consume/ConsumeChat.tsx           # parent layout hook-up if needed
platform/src/components/chat/__tests__/**                 # tests
platform/src/lib/hooks/useSidebarState.ts                 # NEW small hook for pin state
CLAUDECODE_BRIEF.md
```

### must_not_touch
- ConsumeChat content area (CO.1/CO.2/CO.3 sealed)
- StreamingAnswer, lifecycle/* (CO.1/CO.3 sealed)
- AppShell parent navigation (separate concern)
- adapters/, synthesis/

---

## §3 — Work plan

### 3.1 — Sidebar state machine

`platform/src/lib/hooks/useSidebarState.ts`:

```ts
export type SidebarState =
  | 'collapsed'        // narrow rail; only icons visible
  | 'hover-expanded'   // expanded due to mouse hover; will collapse on mouse-out
  | 'pinned-expanded'  // user clicked pin; stays expanded
  | 'mobile-closed'    // overlay closed
  | 'mobile-open'      // overlay open (full-width slide-in)

export function useSidebarState(): {
  state: SidebarState
  isMobile: boolean
  onMouseEnter: () => void
  onMouseLeave: () => void
  onPinToggle: () => void
  onMobileToggle: () => void
}
```

State transitions:
- Desktop (≥ 640px):
  - `collapsed` + mouseEnter → `hover-expanded`
  - `hover-expanded` + mouseLeave → `collapsed`
  - any state + pinToggle → `pinned-expanded`
  - `pinned-expanded` + pinToggle → `collapsed`
- Mobile (< 640px):
  - `mobile-closed` + mobileToggle → `mobile-open`
  - `mobile-open` + mobileToggle → `mobile-closed`
  - hover events are ignored on mobile

The pin state persists in `localStorage` so it survives page refresh.

### 3.2 — Sidebar component

`ConversationSidebar.tsx` refactor:

- Read state from `useSidebarState()`.
- Wire `onMouseEnter` / `onMouseLeave` to the sidebar's outermost div.
- Wire `onPinToggle` to a small pin icon (top of sidebar; corner).
- Apply Tailwind classes per state:
  - `collapsed`: `w-14` (narrow rail; icons only)
  - `hover-expanded` / `pinned-expanded`: `w-64` (full width)
  - `mobile-open`: `fixed inset-0 w-full z-50` (overlay)
- Transition: `transition-[width] duration-200 ease-out`.
- Pin icon: filled when pinned, outlined when not.
- Conversation list, action buttons, etc. — preserve existing content.

### 3.3 — Layout impact

When sidebar expands, the chat area should NOT shift right. The sidebar
should overlay the chat content (z-index above) OR the chat area should
have stable margin (the chat width is sized for the collapsed sidebar
width, and hover-expansion overlays). Pick whichever the existing layout
already uses; favor "overlay on hover, push on pin" for best UX.

### 3.4 — Mobile breakpoint

At viewport < 640px:
- Sidebar collapses to mobile-closed state.
- A hamburger button in the chat header opens it as a full-screen overlay.
- Tap outside the sidebar (overlay backdrop) closes it.
- Hover transitions are disabled (no hover on touch devices).

### 3.5 — Tests

- State machine: every transition tested.
- Hover open/close timing (assume instant; no debounce).
- Pin persistence: localStorage write/read.
- Mobile breakpoint: viewport at 639/640/641 px boundary.
- Accessibility: keyboard `Tab` reaches pin button; `Enter` toggles.
- ≥15 cases.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO4.1 | useSidebarState hook exists with 5 states + 4 actions | grep |
| AC.CO4.2 | Hover transitions work at ≥640px viewport | UI test |
| AC.CO4.3 | Click-to-pin locks expanded state; reload preserves it | localStorage test |
| AC.CO4.4 | Mobile (< 640px) shows hamburger + overlay; no hover | UI test |
| AC.CO4.5 | Sidebar transition is smooth (200ms, no jank) | manual + commented test |
| AC.CO4.6 | Keyboard navigation reaches pin button via Tab | a11y test |
| AC.CO4.7 | typecheck + lint clean | exit 0 |
| AC.CO4.8 | ≥15 new tests | count |
| AC.CO4.9 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
feat(aiops-CO.4): fix Bug 3.2 — sidebar hover-expand + click-pin

- useSidebarState hook: 5-state machine (collapsed, hover-expanded,
  pinned-expanded, mobile-closed, mobile-open)
- Hover open/close on desktop; pin state persists via localStorage
- Mobile (< 640px) falls back to hamburger + full-screen overlay
- 200ms width transition; no layout shift in chat area
- 15+ tests covering state machine, persistence, mobile breakpoint, a11y

AC summary: 9/9 PASS
```

Rotate → CO.5.

---

## §6 — BAIL OUT

- ConversationSidebar is rendered inside a parent layout that fights the new state machine (e.g., parent forces width via grid columns).
- localStorage is not available (test environment quirk); falls back to in-memory but tests need an env shim.

---

*End of PHASE_CO_4_BRIEF.md*
