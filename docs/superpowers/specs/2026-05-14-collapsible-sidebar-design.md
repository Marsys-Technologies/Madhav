# Collapsible Dashboard Sidebar — Design Spec

**Date:** 2026-05-14  
**Status:** Approved  
**File scope:** `platform/src/components/shared/AppShellRail.tsx`

---

## Overview

Replace the fixed-width dashboard sidebar rail with a hover-activated collapsible sidebar. Collapsed by default (56px, icons only); expands to ~176px on hover (icons + labels), floating over main content with no layout shift.

---

## Behaviour

| State | Trigger | Width | Content |
|---|---|---|---|
| Collapsed (default) | — | 56px | Icon only |
| Expanded | `mouseenter` on nav | 176px | Icon + label |
| Collapse | `mouseleave` from nav | 56px | Icon only |

- Transition: `transition-all duration-150 ease-in-out` on width
- Overlay: nav uses `absolute` positioning + `z-50`; the parent layout shell retains a fixed `w-14` gutter so the main content never shifts

---

## Icon Mapping

| Tab | Label | Lucide Icon |
|---|---|---|
| `/dashboard` | Roster | `Users` |
| `/cockpit` | Cockpit | `Gauge` |
| `/audit` | Audit | `FileText` |
| `/aiops` | AIOps | `Bot` |
| `/performance` | Performance | `ChartColumn` |
| `/admin` | Admin | `Settings2` |

---

## Visual States

### Collapsed nav item
```
[ icon ]   ← 44×44 touch target, icon centered
```

### Expanded nav item
```
[ icon ]  Label text   ← icon + label side by side, same 44px height
```

Active item: existing gold highlight (`bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]`)  
Inactive item: existing muted gold (`text-[rgba(212,175,55,0.28)] hover:bg-[rgba(212,175,55,0.08)]`)

### Bottom avatar
- Collapsed: avatar initial only (unchanged)
- Expanded: avatar + **user's name** (not email) — truncated with `truncate` if long

---

## Implementation Plan

### 1. Layout shell adjustment (`AppShell.tsx`)
The `<nav>` currently contributes to flex layout via `w-14 shrink-0`. Change the shell so the nav's gutter is a separate `w-14 shrink-0` spacer div, allowing the nav itself to be `absolute`-positioned without collapsing the layout.

Wrap the spacer + nav pair in a `relative` div so the `absolute` nav has a correct containing block and does not escape to the viewport:

```tsx
<div className="relative hidden md:block w-14 shrink-0">
  <div className="w-14 h-full" /> {/* spacer — holds the gutter */}
  <AppShellRail ... />            {/* absolute, z-50, overlays on hover */}
</div>
```

### 2. `AppShellRail` changes

**State:**
```tsx
const [expanded, setExpanded] = useState(false)
```

**Nav element:**
```tsx
<nav
  onMouseEnter={() => setExpanded(true)}
  onMouseLeave={() => setExpanded(false)}
  className={cn(
    'absolute left-0 top-0 z-50 h-full hidden flex-col items-center border-r border-sidebar-border bg-sidebar py-3 md:flex',
    'transition-all duration-150 ease-in-out overflow-hidden',
    expanded ? 'w-44' : 'w-14'
  )}
>
```

**Nav items:** Replace `{label.slice(0, 2)}` with the icon + conditional label. Keep `aria-label={label}` on the `<Link>` in all states so screen readers have text in the collapsed icon-only view:
```tsx
// aria-label stays on <Link> regardless of expanded state
<Icon className="h-[18px] w-[18px] shrink-0" />
{expanded && <span className="truncate text-xs font-medium">{label}</span>}
```

**Avatar row:** In expanded state, show `user.name ?? user.email` truncated beside the avatar.

### 3. Props change
Add `icon: LucideIcon` to each `NAV_ITEMS` entry. Also rename the `/performance` entry's label from `'Perf'` to `'Performance'` to match the Icon Mapping table — this is the string that appears in expanded state and as `aria-label`.

---

## Out of Scope

- Mobile nav (`MobileNavSheet.tsx`) — unchanged
- Consume module sidebar (`ConsumeChat.tsx`) — separate locked component, not touched
- Tooltip on hover (not needed since expanded state shows label)
