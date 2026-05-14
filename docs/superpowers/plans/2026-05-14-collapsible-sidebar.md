# Collapsible Dashboard Sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the fixed-width dashboard sidebar rail into a hover-activated collapsible sidebar — collapsed (icons only, 56px) by default, expanding to icons + labels (176px) on hover, floating over content with no layout shift.

**Architecture:** `AppShellRail` gains hover state and renders icons in collapsed mode + icons with labels in expanded mode. `AppShell` wraps the rail in a `relative` containing block with a `w-14` spacer div so the absolute-positioned expanding nav doesn't shift the main content. All existing `aria-label` attributes are preserved for accessibility.

**Tech Stack:** Next.js (App Router), React, Tailwind CSS, lucide-react v1.8.0, Vitest + @testing-library/react

---

## File Map

| File | Change |
|------|--------|
| `platform/src/components/shared/AppShellRail.tsx` | Add icons to `NAV_ITEMS`, replace `label.slice(0,2)` with icon + conditional label, add hover expand state, absolute positioning |
| `platform/src/components/shared/AppShell.tsx` | Wrap `<AppShellRail>` in `relative` div with `w-14` spacer |
| `platform/tests/components/AppShell.test.tsx` | Update existing tests + add expand/collapse + icon tests |

---

## Task 1: Update tests to cover new behavior

Update the test file before touching the implementation so every test run gives a clean red → green signal.

**Files:**
- Modify: `platform/tests/components/AppShell.test.tsx`

- [ ] **Step 1: Add import for `fireEvent`**

At the top of the test file, change:
```ts
import { render } from '@testing-library/react'
```
to:
```ts
import { render, fireEvent } from '@testing-library/react'
```

- [ ] **Step 2: Add test — nav items have aria-labels in collapsed state**

Append inside the `describe('AppShell', ...)` block:
```ts
it('nav items have aria-label in collapsed state', () => {
  const { getByRole } = render(
    <AppShell user={BASE_USER} profile={BASE_PROFILE} />
  )
  expect(getByRole('link', { name: 'Roster' })).toBeTruthy()
  expect(getByRole('link', { name: 'Cockpit' })).toBeTruthy()
  expect(getByRole('link', { name: 'Audit' })).toBeTruthy()
})
```

- [ ] **Step 3: Add test — nav labels visible when expanded (mouseenter)**

```ts
it('shows nav labels when sidebar is hovered', () => {
  const { getByRole, getByText } = render(
    <AppShell user={BASE_USER} profile={BASE_PROFILE} />
  )
  const nav = getByRole('navigation', { name: 'Primary navigation' })
  fireEvent.mouseEnter(nav)
  expect(getByText('Roster')).toBeTruthy()
  expect(getByText('Cockpit')).toBeTruthy()
})
```

- [ ] **Step 4: Add test — nav labels hidden after mouseleave**

```ts
it('hides nav labels after sidebar hover ends', () => {
  const { getByRole, queryByText } = render(
    <AppShell user={BASE_USER} profile={BASE_PROFILE} />
  )
  const nav = getByRole('navigation', { name: 'Primary navigation' })
  fireEvent.mouseEnter(nav)
  fireEvent.mouseLeave(nav)
  expect(queryByText('Roster')).toBeNull()
})
```

- [ ] **Step 5: Add test — Performance label is "Performance" not "Perf"**

```ts
it('shows full Performance label when expanded', () => {
  const { getByRole, getByText } = render(
    <AppShell user={BASE_USER} profile={BASE_PROFILE} />
  )
  const nav = getByRole('navigation', { name: 'Primary navigation' })
  fireEvent.mouseEnter(nav)
  expect(getByText('Performance')).toBeTruthy()
})
```

- [ ] **Step 6: Add test — username shown in avatar row when expanded**

```ts
it('shows username in avatar row when expanded', () => {
  const { getByRole, getByText } = render(
    <AppShell
      user={{ uid: 'u1', email: 'test@example.com', name: 'Abhisek' }}
      profile={BASE_PROFILE}
    />
  )
  const nav = getByRole('navigation', { name: 'Primary navigation' })
  fireEvent.mouseEnter(nav)
  expect(getByText('Abhisek')).toBeTruthy()
})
```

- [ ] **Step 7: Run all tests — expect new tests to fail, existing to pass**

```bash
cd platform && npx vitest run tests/components/AppShell.test.tsx
```

Expected: existing 8 tests PASS, new 5 tests FAIL (implementation not updated yet).

---

## Task 2: Update `AppShellRail` — icons, expand state, overlay positioning

**Files:**
- Modify: `platform/src/components/shared/AppShellRail.tsx`

- [ ] **Step 1: Add lucide-react icon imports**

Replace the existing import block at the top. After the existing imports, add:
```ts
import {
  Users,
  Gauge,
  FileText,
  Bot,
  ChartColumn,
  Settings2,
  type LucideIcon,
} from 'lucide-react'
```

- [ ] **Step 2: Add `icon` field to `NAV_ITEMS` and fix Performance label**

Replace the `NAV_ITEMS` constant:
```ts
const NAV_ITEMS: { href: string; label: string; icon: LucideIcon; roles: readonly string[] }[] = [
  { href: '/dashboard',   label: 'Roster',      icon: Users,       roles: ['super_admin', 'admin', 'client'] },
  { href: '/cockpit',     label: 'Cockpit',     icon: Gauge,       roles: ['super_admin'] },
  { href: '/audit',       label: 'Audit',       icon: FileText,    roles: ['super_admin'] },
  { href: '/aiops',       label: 'AIOps',       icon: Bot,         roles: ['super_admin'] },
  { href: '/performance', label: 'Performance', icon: ChartColumn, roles: ['super_admin'] },
  { href: '/admin',       label: 'Admin',       icon: Settings2,   roles: ['super_admin', 'admin'] },
]
```

- [ ] **Step 3: Add hover expand state**

Inside `AppShellRail`, before the `return`, add:
```ts
const [expanded, setExpanded] = useState(false)
```

Add the import at the top if not already present:
```ts
import { useState } from 'react'
```

- [ ] **Step 4: Update `<nav>` element — absolute positioning + width transition**

Replace the `<nav>` opening tag (currently line 51–54):
```tsx
<nav
  aria-label="Primary navigation"
  onMouseEnter={() => setExpanded(true)}
  onMouseLeave={() => setExpanded(false)}
  className={cn(
    'absolute inset-y-0 left-0 z-50 hidden flex-col items-center border-r border-sidebar-border bg-sidebar py-3 md:flex',
    'overflow-hidden transition-all duration-150 ease-in-out',
    expanded ? 'w-44' : 'w-14'
  )}
>
```

- [ ] **Step 5: Update nav item rendering — icon + conditional label**

Replace the nav link body (currently `{label.slice(0, 2)}`):
```tsx
<Link
  key={href}
  href={href}
  aria-label={label}
  className={cn(
    'flex h-11 w-full items-center gap-3 rounded px-3 text-xs font-medium transition-colors',
    isActive
      ? 'bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]'
      : 'text-[rgba(212,175,55,0.28)] hover:bg-[rgba(212,175,55,0.08)] hover:text-[#d4af37]'
  )}
>
  <Icon className="h-[18px] w-[18px] shrink-0" />
  {expanded && <span className="truncate">{label}</span>}
</Link>
```

Note: destructure `icon: Icon` from the map: `{visibleItems.map(({ href, label, icon: Icon }) => {`

- [ ] **Step 6: Update avatar row — show username when expanded**

Replace the `DropdownMenuTrigger` block (currently lines 89–94):
```tsx
<DropdownMenuTrigger
  aria-label="User menu"
  className="flex h-11 w-full items-center gap-3 rounded-full border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.07)] px-3 text-xs font-medium text-[rgba(212,175,55,0.6)] transition-colors hover:bg-[rgba(212,175,55,0.12)]"
>
  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-center leading-7">
    {userInitial}
  </span>
  {expanded && (
    <span className="truncate text-xs">
      {user.name ?? user.email}
    </span>
  )}
</DropdownMenuTrigger>
```

- [ ] **Step 7: Run tests**

```bash
cd platform && npx vitest run tests/components/AppShell.test.tsx
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add platform/src/components/shared/AppShellRail.tsx platform/tests/components/AppShell.test.tsx
git commit -m "feat(sidebar): hover-expand rail with icons and full labels"
```

---

## Task 3: Update `AppShell` — relative wrapper + spacer div

**Files:**
- Modify: `platform/src/components/shared/AppShell.tsx`

- [ ] **Step 1: Wrap `<AppShellRail>` in a containing block**

Replace:
```tsx
{/* Desktop sidebar rail — hidden on mobile */}
<AppShellRail user={user} profile={profile} />
```

With:
```tsx
{/* Desktop sidebar rail — hidden on mobile. relative+w-14 gives the absolute rail a containing block. */}
<div className="relative hidden w-14 shrink-0 md:block">
  <div className="h-full w-14" /> {/* spacer — holds the gutter height while rail is absolute */}
  <AppShellRail user={user} profile={profile} />
</div>
```

- [ ] **Step 2: Run the full test suite**

```bash
cd platform && npx vitest run tests/components/AppShell.test.tsx
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add platform/src/components/shared/AppShell.tsx
git commit -m "feat(sidebar): wrap rail in relative containing block for overlay expansion"
```

---

## Task 4: Smoke test in the browser

- [ ] **Step 1: Start the dev server**

```bash
cd platform && npm run dev
```

- [ ] **Step 2: Open the dashboard**

Navigate to `http://localhost:3000/dashboard` (or the port printed by the dev server).

- [ ] **Step 3: Verify collapsed state**

Sidebar should be 56px wide showing only icons. No text labels visible.

- [ ] **Step 4: Verify expanded state**

Hover over the sidebar. It should smoothly expand to ~176px showing icons + labels. Main content should not shift.

- [ ] **Step 5: Verify collapse on mouse-out**

Move mouse away from sidebar. It should smoothly collapse back to 56px.

- [ ] **Step 6: Verify active state styling**

The active page's nav item should have the gold highlight border.

- [ ] **Step 7: Verify avatar row**

Hover: username should appear beside the avatar initial. Mouse out: it disappears.

- [ ] **Step 8: Verify no mobile regression**

Resize browser below `md` breakpoint (< 768px). Sidebar should be hidden; mobile nav sheet should still work.
