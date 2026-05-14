# Consume Module UI Redesign — Design Spec

**Date:** 2026-05-15  
**Status:** Approved — awaiting implementation (prescriptive, not yet applied to code)  
**Scope:** Consume chat interface — layout fix + full shell redesign  

---

## 1. Problem Statement

The consume chat interface is completely broken from a layout standpoint. The root cause is a double-height conflict: `ChatShell` declares `h-[100dvh]` but is nested inside `AppShell → <main class="overflow-auto">`. The chat overflows its container and scrolls as a page rather than maintaining a fixed-height shell with internal scrolling. Every other visual issue (sidebar collapse strip, EmptyState blank, message stream invisible) cascades from this structural fault.

Additionally, the UI modernisation work done in AIOps Phase 3 (CO.5/CO.6) targeted the `consumeUiV2Enabled` lifecycle-slot path, which remains empty (CO.2/CO.3 never wired the event stream). The legacy streaming path — which is what users actually see — received no visual update.

---

## 2. Design Decisions

| Decision | Choice |
|---|---|
| **Layout approach** | Option C — Consume bypasses AppShell entirely |
| **Visual mood** | Option B — Modern Dark Pro (gold as precise accent, no ornament) |
| **Sidebar structure** | Option C — Icon rail (44px) + hover-expand overlay panel |
| **Message layout** | Option B — Full-width AI with gold `✦` avatar, right-aligned user card |

---

## 3. Root Fix

`platform/src/app/clients/[id]/consume/layout.tsx` wraps the `ZoneRoot` itself in a `position: fixed; inset: 0; z-index: 50` div. This creates a full-viewport overlay that visually replaces AppShell for the consume route without:
- touching `clients/[id]/layout.tsx` (auth + DB queries stay there)
- restructuring routes or creating route groups
- duplicating auth checks

AppShell still renders underneath (preserved for accessibility), but ConsumeShell owns the full viewport.

**Critical implementation note — stacking context safety:** The fixed div must be the *outermost* element in the layout, wrapping ZoneRoot rather than being a child inside it. The current `layout.tsx` uses `ZoneRoot` with `display: contents`, which means any fixed element placed *inside* it would be treated as a child of AppShell's `<main>`. If any ancestor element in AppShell ever applies `transform`, `filter`, `will-change`, or `contain: paint`, it would create a new stacking context that traps `position: fixed` and breaks the overlay. The correct structure is:

```tsx
// consume/layout.tsx — correct
export default function ConsumeLayout({ children }: { children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-background">
      <ZoneRoot zone="ink" style={{ height: '100%' }}>
        {children}
      </ZoneRoot>
    </div>
  )
}
```

**Before (broken):**
```
AppShell (h-[100dvh])
  Rail w-14
  Column (overflow-hidden)
    Breadcrumb (40px)
    main (overflow-auto)          ← breaks chat
      ChatShell (h-[100dvh])      ← double height → page scroll
        ConsumeChat …
```

**After (fixed):**
```
AppShell (h-[100dvh]) — renders, hidden under overlay
ConsumeLayout (fixed inset-0 z-50)
  ConsumeShell (h-full flex)
    ConsumeRail (44px, hover-expand)
    Main (flex-1, flex-col)
      ConsumeHeader (48px)
      Scroll area (flex-1, overflow-y-auto)
      Composer zone (shrink-0, measured via ResizeObserver)
```

---

## 4. Architecture

### 4.1 Files Created

| File | Purpose |
|---|---|
| `platform/src/components/consume/ConsumeShell.tsx` | Full-screen shell — replaces ChatShell for the consume route. Full prop surface: `children`, `rightPanel`, `rightPanelLabel`, `rightPanelBadge`, `headerTitle`, `headerMeta`, `headerActions`, `conversationId`, `onRenameConversation`. Collapse state (`desktopSidebarCollapsed`, `mobileSidebarOpen`, the three toggle callbacks) is removed from the prop surface — ConsumeRail owns its own panel-open state internally. |
| `platform/src/components/consume/ConsumeRail.tsx` | 44px icon rail with hover-expand overlay panel. Renders existing `ConversationSidebar` inside the panel. Exposes an imperative `open()` / `close()` handle (or a controlled `panelOpen` + `onPanelOpenChange` prop) so the ConsumeHeader hamburger button can toggle the panel. |

### 4.2 Files Modified

| File | Change |
|---|---|
| `platform/src/app/clients/[id]/consume/layout.tsx` | Add `fixed inset-0 z-50 bg-background` wrapper div around ZoneRoot. |
| `platform/src/components/consume/ConsumeChat.tsx` | Swap `<ChatShell …>` → `<ConsumeShell …>`. Same props. Remove mobile Sheet sidebar (ConsumeRail handles overlay). Update root wrapper to `h-full flex flex-col`. |
| `platform/src/components/chat/AssistantMessage.tsx` | Add gold `✦` avatar column. Shift from bubble to full-width layout. Add model chip + action row (regenerate, thumbs) below last-turn only. |
| `platform/src/components/consume/EmptyState.tsx` | Re-centre for new shell width. Update tab + button styling to Modern Dark Pro tokens. |
| `platform/src/app/globals.css` | Append ConsumeRail hover transition, hover-panel backdrop, scrollbar, composer card focus ring. No existing rules removed. |

### 4.3 Files Untouched (preserved exactly)

- `platform/src/app/clients/[id]/layout.tsx` — auth + AppShell unchanged
- `platform/src/components/chat/ChatShell.tsx` — used by build/ and other routes
- `platform/src/components/chat/Composer.tsx` — **LOCKED** per `platform/AGENTS.md`
- `platform/src/components/chat/ConversationSidebar.tsx` — rendered inside ConsumeRail panel; all rename/delete/search logic preserved
- All other consume sub-components (StreamingAnswer, LiveReasoningCard, TraceDrawer, ReportLibrary, ReportReader, CorrectionNotice, OutOfDomainBanner, PostAnswerProvenance, ConversationHistoryDrawer, ValidatorFailureView, TierPicker, lifecycle/*, **ShortcutsDialog**, **CommandPalette**, etc.)
  - **Note on CommandPalette `toggle-sidebar` command:** the existing command calls `setDesktopSidebarCollapsed`. Because ConsumeRail now owns panel state internally, this command handler in `ConsumeChat.tsx` must be updated to call the ConsumeRail toggle instead (via the `onPanelOpenChange` prop or ref). The command label and hotkey (`⌘B`) remain unchanged.

---

## 5. Component Designs

### 5.1 ConsumeRail

```
[44px wide, full height, z-20]
├─ Logo: 28px rounded square, gold gradient, "M"
├─ Nav icons (32px each, 7px border-radius):
│   ├─ Consume  — active state: gold left-bar (3px × 16px) + rgba(gold,0.12) bg
│   ├─ Reports  — navigates to consume + opens right panel
│   ├─ Timeline — navigates to /clients/[id]/timeline
│   └─ Dashboard — navigates to /dashboard (below separator)
├─ Spacer (flex-1)
└─ User avatar (26px circle, initials)
```

**Hover panel** — `position: absolute; left: 44px; top: 0; bottom: 0; width: 240px; z-[19]` (arbitrary value — `z-19` is not a Tailwind v4 scale class):
- Backdrop: `#0b0804`, `box-shadow: 4px 0 32px rgba(0,0,0,0.7)`
- Header: chart name + meta (birth date · place)
- New Conversation button: gold-border card, `+ New Conversation`
- Search input: `rgba(gold,0.03)` bg, `rgba(gold,0.12)` border
- Grouped conversation list (Today / This week / Earlier) — renders `ConversationSidebar` content
- Footer: theme toggle, settings icon, MARSYS-JIS label
- Dismiss: click-outside handler; on mobile falls back to tap-toggle

### 5.2 ConsumeShell

```
[h-full flex, no overflow on root]
├─ ConsumeRail (44px, shrink-0)
└─ Main column (flex-1, flex-col, overflow-hidden)
    ├─ ConsumeHeader (h-12, shrink-0)
    │   ├─ Left: hamburger button (toggles rail panel on all sizes)
    │   ├─ Center: chart name (font-medium, truncate) + meta line (9px uppercase gold/40)
    │   └─ Right: headerActions slot (History, Share, Trace)
    ├─ Scroll area (flex-1, min-h-0, overflow-y-auto, [scrollbar-gutter:stable])
    │   └─ children (EmptyState or message stream)
    ├─ ScrollToBottomButton (absolute, above composer)
    └─ Composer zone (shrink-0, border-t)
        ├─ [slot: error banner]
        ├─ [slot: archived branch notice]
        ├─ Toolbar row: ModelStylePicker | LEL toggle | Panel checkbox
        ├─ [slot: LEL-off notice]
        └─ Composer (existing, untouched)
```

> **Trace button placement (LOCKED):** Trace does NOT appear in the toolbar row. It is passed via the `headerActions` prop and renders in ConsumeHeader's right slot — visible only when `activeTier === 'super_admin'`. This matches locked behavior #2.



**`--composer-h` CSS variable**: measured via ResizeObserver on the composer zone div (same mechanism already in ConsumeChat). Initial value `160px` retained as fallback.

### 5.3 AssistantMessage — Restyle

**Before:** rounded bubble, `bg-card`, `rounded-2xl`, left-aligned within max-width container.

**After:**
```
[flex gap-14px align-items-start, full width, max-w-3xl mx-auto px-6]
├─ Avatar: 28px circle, gold gradient, "✦" glyph, box-shadow gold glow
│   (pulses during streaming via keyframe)
└─ Body (flex-1)
    ├─ Name label: "MARSYS" — 10px, 700, gold/50, tracking-wide uppercase
    ├─ Content: existing MarkdownContent — unchanged
    ├─ [last turn only] Meta chips: model label · provider · planner latency
    └─ [last turn only] Action row: Regenerate | 👍 | 👎
```

**User message** (unchanged structure, updated classes):
```
[flex justify-end px-6]
└─ Card: max-w-[65%], bg rgba(gold,0.08), border rgba(gold,0.15),
         rounded-[14px_14px_4px_14px], px-4 py-2.5, text-13px
```

### 5.4 EmptyState — Restyle

- Remove sidebar-width offset (no fixed left margin needed)
- Centre content in full available width using `mx-auto max-w-2xl`
- Tab underline: `border-b-2 border-[var(--brand-gold)]` on active
- Suggestion buttons: `border border-border hover:border-[var(--brand-gold)]/40 hover:bg-[var(--brand-gold)]/5` — gold border on hover, no fill

---

## 6. Z-Index Stack


| Layer | Value | Element |
|---|---|---|
| AppShell (hidden behind) | — | `h-[100dvh]` under overlay |
| Consume overlay root | `z-50` | `fixed inset-0` in `consume/layout.tsx` |
| ConsumeRail | `z-20` | `position: relative` within overlay |
| ConsumeRail hover panel | `z-19` | `position: absolute; left: 44px` |
| ScrollToBottomButton | `z-20` | `absolute`, within scroll area |
| Radix Sheet portals (TraceDrawer, ConversationHistoryDrawer, right panel) | `z-50` via Radix portal to `<body>` — renders above all in-tree z-index |
| CommandPalette, ShortcutsDialog | `z-50` via Radix portal |

> Radix portal-based components (`Sheet`, `Dialog`) always render at the body root, outside the consume overlay tree entirely. No z-index conflict with ConsumeRail panel.

---

## 7. Visual Design Tokens (additions to globals.css)

```css
/* ConsumeRail hover panel transition */
.consume-rail-panel {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

/* Scrollbar styling in consume shell */
.consume-shell .scroll-area {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--brand-gold-rgb), 0.12) transparent;
}

/* Composer card focus-within ring */
.consume-composer-card:focus-within {
  border-color: rgba(var(--brand-gold-rgb), 0.4);
  box-shadow: 0 0 0 3px rgba(var(--brand-gold-rgb), 0.08);
}

/* AI avatar streaming pulse */
@keyframes avatar-pulse {
  0%, 100% { box-shadow: 0 0 8px rgba(var(--brand-gold-rgb), 0.2); }
  50%       { box-shadow: 0 0 20px rgba(var(--brand-gold-rgb), 0.5); }
}
```

---

## 8. Locked Behaviors (preserved verbatim)

Per `platform/AGENTS.md`:

| # | Behavior | How preserved |
|---|---|---|
| 1 | Sidebar default-collapsed | ConsumeRail `panelOpen` initialises to `false` — icon-only on fresh load. **Note:** `AGENTS.md` documents the canonical value as `desktopSidebarCollapsed = useState(true)` (collapsed = `true`). The live code regressed to `useState(false)`. ConsumeRail inverts the polarity: `panelOpen = false` means the panel is *closed* (i.e. collapsed) — semantically identical to `desktopSidebarCollapsed = true`. `panelOpen = false` on load is the correct canonical behaviour. The old `desktopSidebarCollapsed` state in `ConsumeChat.tsx` is removed entirely. |
| 2 | Trace button in header | Passed via `headerActions` prop to ConsumeShell → renders in ConsumeHeader right slot. Not in composer toolbar row. |
| 3 | Composer fixed-size textarea | `Composer.tsx` untouched; only outer wrapping card restyled |

---

## 9. Implementation Order

1. **`consume/layout.tsx`** — `fixed inset-0 z-50` wrapper. Immediately unblocks layout. Verify in browser before continuing.
2. **`ConsumeRail.tsx`** — icon rail + hover expand + ConversationSidebar inside panel.
3. **`ConsumeShell.tsx`** — shell layout, header, accepts ConsumeRail + children + composer slot.
4. **`ConsumeChat.tsx`** — swap ChatShell → ConsumeShell, same props, same children.
5. **`AssistantMessage.tsx`** — avatar column, full-width layout, action row.
6. **`EmptyState.tsx`** — centre alignment, tab + button polish.
7. **`globals.css`** — rail hover transition, scrollbar, composer ring.
8. **Browser verification** — all test cases below.

---

## 10. Test Plan

### Layout contract
- Chat fills full viewport; AppShell rail + breadcrumb invisible
- No outer-page scroll; only message area scrolls internally
- Composer pinned at bottom at all viewport sizes
- ScrollToBottomButton positioned correctly above composer
- Verified at: 1440px, 1280px, 1024px, 768px (tablet), 375px (mobile)

### ConsumeRail
- Default: 44px icon-only, no labels
- Hover: panel slides in; ConversationSidebar renders inside with full functionality
- Click-outside: panel dismisses
- Active item: gold left-bar indicator
- Reports icon opens right panel (ReportLibrary)
- Dashboard icon navigates to `/dashboard`

### Conversation flow
- New chat: messages clear, URL → `/consume`
- Send: streams, avatar pulses during streaming
- Navigate to existing conversation: messages load, scroll to bottom
- Rename: double-click title in header → inline edit → save on Enter/blur
- Regenerate: last AI turn re-streams
- Branch / edit: archived branch view, Return to latest button

### Locked behaviors
- Rail starts collapsed (icon-only) on fresh load
- Trace button in header (super_admin only), not in toolbar
- Composer textarea fixed 3-row, does not auto-grow

### Feature flags
- `consumeUiV2Enabled=true`: lifecycle slot path renders inside ConsumeShell
- `panelModeEnabled=true`: Panel checkbox in toolbar
- `activeTier=super_admin`: Trace + TierPicker visible

### Other routes — regression
- `/clients/[id]/build`: AppShell renders correctly, unchanged
- `/dashboard`: unaffected
- `/login`: unaffected

---

## 11. Known Risks + Mitigations

| Risk | Mitigation |
|---|---|
| `position: fixed` + iOS virtual keyboard | `env(safe-area-inset-bottom)` on composer padding (already present); test on iOS Safari |
| Hover panel on touch devices | ConsumeRail tap-toggles panel on touch (same UX as current hamburger + Sheet) |
| AssistantMessage restyle breaks markdown | Only outer wrapper `className` changes; `MarkdownContent`, code blocks, citation pills, Sanskrit spans structurally intact |
