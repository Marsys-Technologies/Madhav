# Consume UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken consume chat layout and deliver a Modern Dark Pro shell with a 44px icon rail, full-width AI messages with gold avatar, and all locked behaviors preserved.

**Architecture:** `consume/layout.tsx` gains a `fixed inset-0 z-50` wrapper that creates a full-viewport overlay over AppShell — no route restructuring, no auth duplication. Two new components (`ConsumeShell`, `ConsumeRail`) replace `ChatShell` for the consume route only. All 20+ inner consume sub-components are untouched.

**Tech Stack:** Next.js 16.2.4 App Router, Tailwind CSS v4 (arbitrary values via `[]`, no `tailwind.config.js`), shadcn/ui + Radix primitives, `framer-motion`, Lucide icons, OKLCH color tokens (`--brand-gold`, `--brand-gold-rgb`).

**Spec:** `docs/superpowers/specs/2026-05-15-consume-ui-redesign-design.md`

---

## File Map

| Status | File | Purpose |
|---|---|---|
| MODIFY | `platform/src/app/clients/[id]/consume/layout.tsx` | Add `fixed inset-0 z-50` wrapper |
| CREATE | `platform/src/components/consume/ConsumeRail.tsx` | 44px icon rail + hover-expand overlay panel |
| CREATE | `platform/src/components/consume/ConsumeShell.tsx` | Full-screen shell with header, scroll area, composer slots |
| MODIFY | `platform/src/components/consume/ConsumeChat.tsx` | Swap ChatShell → ConsumeShell; drop collapse state; update toggle-sidebar command |
| MODIFY | `platform/src/components/chat/AssistantMessage.tsx` | Gold `✦` avatar, full-width layout, action row below last turn |
| MODIFY | `platform/src/components/consume/EmptyState.tsx` | Re-centre, tab underline, suggestion button gold hover |
| MODIFY | `platform/src/app/globals.css` | Rail hover transition, scrollbar, composer ring, avatar-pulse keyframe |
| UNTOUCHED | `platform/src/components/chat/ChatShell.tsx` | Used by build/ route — must not change |
| UNTOUCHED | `platform/src/components/chat/Composer.tsx` | LOCKED per AGENTS.md |
| UNTOUCHED | `platform/src/components/chat/ConversationSidebar.tsx` | Rendered inside ConsumeRail panel |

---

## Task 1: Fix `consume/layout.tsx` — full-viewport overlay

**Files:**
- Modify: `platform/src/app/clients/[id]/consume/layout.tsx`

**Context:** Currently `ZoneRoot` uses `display: contents` which makes it transparent. `ChatShell` inside it declares `h-[100dvh]`, but AppShell's `<main class="overflow-auto">` ancestor breaks this into page scroll. The fix: wrap ZoneRoot in `fixed inset-0 z-50` so consume owns the full viewport.

- [ ] **Step 1: Verify current file before change**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | head -20`
  Expected: zero errors (clean baseline).

- [ ] **Step 2: Apply the layout fix**

  Replace the entire contents of `platform/src/app/clients/[id]/consume/layout.tsx` with:

  ```tsx
  import type { ReactNode } from "react";
  import { ZoneRoot } from "@/components/shared/ZoneRoot";

  export default function ConsumeLayout({ children }: { children: ReactNode }) {
    return (
      <div className="fixed inset-0 z-50 bg-background">
        <ZoneRoot zone="ink" style={{ height: "100%" }}>
          {children}
        </ZoneRoot>
      </div>
    );
  }
  ```

  **Critical:** The `fixed inset-0` div must *wrap* ZoneRoot, not be inside it. ZoneRoot uses `display: contents` — any fixed element placed inside it would be trapped by AppShell's ancestor stacking context.

- [ ] **Step 3: TypeScript check**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | head -30`
  Expected: zero errors.

- [ ] **Step 4: Browser spot-check**

  Navigate to `http://localhost:3000/clients/[any-chartId]/consume`.
  Expected: AppShell rail + breadcrumb no longer visible. Consume fills full viewport. (Will look raw/broken until ConsumeShell lands — that is normal.)

- [ ] **Step 5: Commit**

  ```bash
  cd platform && git add src/app/clients/\[id\]/consume/layout.tsx
  git commit -m "fix(consume): full-viewport overlay via fixed inset-0 z-50 on layout wrapper"
  ```

---

## Task 2: Build `ConsumeRail.tsx` — icon rail + hover-expand panel

**Files:**
- Create: `platform/src/components/consume/ConsumeRail.tsx`

**Context:** 44px-wide icon-only nav rail. Hovering (or clicking on touch) opens a 240px overlay panel (`position: absolute; left: 44px`). The panel renders the existing `ConversationSidebar`. Nav items: Consume (active), Reports, Timeline, Dashboard.

- [ ] **Step 1: Write the component**

  Create `platform/src/components/consume/ConsumeRail.tsx`:

  ```tsx
  'use client'

  import { useCallback, useEffect, useRef, useState } from 'react'
  import Link from 'next/link'
  import { usePathname } from 'next/navigation'
  import { MessageSquare, FileText, Clock, LayoutDashboard } from 'lucide-react'
  import { cn } from '@/lib/utils'
  import { ConversationSidebar } from '@/components/chat/ConversationSidebar'

  interface ConversationRow {
    id: string
    title: string | null
    created_at: string
    chart_id: string
    user_id: string
    module: string
  }

  interface Props {
    panelOpen: boolean
    onPanelOpenChange: (open: boolean) => void
    chartId: string
    chartName: string
    conversations: ConversationRow[]
    currentConversationId?: string
    onConversationRenamed: (id: string, title: string) => void
    onConversationDeleted: (id: string) => void
  }

  export function ConsumeRail({
    panelOpen,
    onPanelOpenChange,
    chartId,
    chartName,
    conversations,
    currentConversationId,
    onConversationRenamed,
    onConversationDeleted,
  }: Props) {
    const pathname = usePathname()
    const panelRef = useRef<HTMLDivElement>(null)
    const railRef = useRef<HTMLDivElement>(null)
    const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // Debounced close — prevents panel from snapping shut when cursor
    // crosses the gap between rail and panel on hover.
    function openPanel() {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
      onPanelOpenChange(true)
    }
    function scheduleClose() {
      closeTimerRef.current = setTimeout(() => onPanelOpenChange(false), 80)
    }

    // Close panel on click-outside (both rail and panel excluded)
    useEffect(() => {
      if (!panelOpen) return
      function handleClick(e: MouseEvent) {
        if (
          panelRef.current?.contains(e.target as Node) ||
          railRef.current?.contains(e.target as Node)
        ) return
        onPanelOpenChange(false)
      }
      document.addEventListener('mousedown', handleClick)
      return () => document.removeEventListener('mousedown', handleClick)
    }, [panelOpen, onPanelOpenChange])

    const isConsume = pathname?.includes('/consume') ?? false

    const navItems = [
      {
        icon: MessageSquare,
        label: 'Consume',
        href: `/clients/${chartId}/consume`,
        active: isConsume,
      },
      {
        icon: FileText,
        label: 'Reports',
        href: `/clients/${chartId}/consume`,
        active: false,
        onClick: () => onPanelOpenChange(!panelOpen),
      },
      {
        icon: Clock,
        label: 'Timeline',
        href: `/clients/${chartId}/timeline`,
        active: false,
      },
      {
        icon: LayoutDashboard,
        label: 'Dashboard',
        href: '/dashboard',
        active: false,
      },
    ]

    return (
      <div
        ref={railRef}
        className="relative z-20 flex h-full w-11 shrink-0 flex-col items-center border-r border-[rgba(var(--brand-gold-rgb),0.08)] bg-[oklch(0.07_0.010_70)] py-3"
        onMouseEnter={openPanel}
        onMouseLeave={scheduleClose}
      >
        {/* Logo */}
        <div className="mb-4 flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--brand-gold)] to-[oklch(0.65_0.15_70)] text-[13px] font-bold text-[oklch(0.08_0.010_70)] shadow-[0_0_12px_rgba(var(--brand-gold-rgb),0.3)]">
          M
        </div>

        {/* Nav items */}
        <nav className="flex flex-1 flex-col items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const content = (
              <span
                className={cn(
                  'relative flex size-8 items-center justify-center rounded-[7px] transition-colors',
                  item.active
                    ? 'bg-[rgba(var(--brand-gold-rgb),0.12)] text-[var(--brand-gold)]'
                    : 'text-[var(--brand-gold-cream)]/40 hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[var(--brand-gold-cream)]/80'
                )}
              >
                {item.active && (
                  <span className="absolute -left-[11px] h-4 w-[3px] rounded-r-full bg-[var(--brand-gold)]" />
                )}
                <Icon className="size-4" />
              </span>
            )
            if (item.onClick) {
              return (
                <button key={item.label} type="button" onClick={item.onClick} aria-label={item.label}>
                  {content}
                </button>
              )
            }
            return (
              <Link key={item.label} href={item.href} aria-label={item.label}>
                {content}
              </Link>
            )
          })}
        </nav>

        {/* User avatar — bottom of rail */}
        <div
          className="mb-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-[rgba(var(--brand-gold-rgb),0.15)] text-[9px] font-bold uppercase text-[var(--brand-gold)]/70"
          aria-label="User"
        >
          U
        </div>

        {/* Hover-expand panel — uses debounced open/close so cursor can
            move from rail to panel without the panel snapping shut */}
        <div
          ref={panelRef}
          onMouseEnter={openPanel}
          onMouseLeave={scheduleClose}
          className={cn(
            'consume-rail-panel absolute left-11 top-0 h-full w-60 overflow-hidden',
            'border-r border-[rgba(var(--brand-gold-rgb),0.08)]',
            'bg-[#0b0804] shadow-[4px_0_32px_rgba(0,0,0,0.7)]',
            panelOpen ? 'opacity-100 translate-x-0 pointer-events-auto' : 'opacity-0 -translate-x-2 pointer-events-none'
          )}
          style={{ zIndex: 19 }}
        >
          <ConversationSidebar
            chartId={chartId}
            chartName={chartName}
            conversations={conversations}
            currentConversationId={currentConversationId}
            onRenamed={onConversationRenamed}
            onDeleted={onConversationDeleted}
            onClose={() => onPanelOpenChange(false)}
          />
        </div>
      </div>
    )
  }
  ```

- [ ] **Step 2: TypeScript check**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | grep -E "ConsumeRail|error TS" | head -20`
  Expected: zero errors.

- [ ] **Step 3: Commit**

  ```bash
  cd platform && git add src/components/consume/ConsumeRail.tsx
  git commit -m "feat(consume): ConsumeRail — 44px icon rail with hover-expand ConversationSidebar panel"
  ```

---

## Task 3: Build `ConsumeShell.tsx` — full-screen shell

**Files:**
- Create: `platform/src/components/consume/ConsumeShell.tsx`

**Context:** Replaces `ChatShell` for the consume route. `h-full flex` root — ConsumeRail (44px) + main column (flex-1). Main column: ConsumeHeader (48px) | scroll area (flex-1, overflow-y-auto) | composer zone (shrink-0). Exposes `togglePanel()` imperatively via `React.forwardRef` so `ConsumeChat` can call it from the command palette and hotkeys without prop-drilling.

- [ ] **Step 1: Write the component**

  Create `platform/src/components/consume/ConsumeShell.tsx`:

  ```tsx
  'use client'

  import {
    forwardRef,
    useEffect,
    useImperativeHandle,
    useRef,
    useState,
    type ReactNode,
  } from 'react'
  import { PanelLeft } from 'lucide-react'
  import { cn } from '@/lib/utils'
  import { ConsumeRail } from './ConsumeRail'
  import { getHighlighter } from '@/lib/shiki'

  interface ConversationRow {
    id: string
    title: string | null
    created_at: string
    chart_id: string
    user_id: string
    module: string
  }

  interface Props {
    children: ReactNode
    rightPanel?: ReactNode
    rightPanelLabel?: string
    rightPanelBadge?: number
    headerTitle?: string
    headerMeta?: string
    headerActions?: ReactNode
    conversationId?: string
    onRenameConversation?: (id: string, title: string) => Promise<void>
    // Rail / sidebar data
    chartId: string
    chartName: string
    conversations: ConversationRow[]
    currentConversationId?: string
    onConversationRenamed: (id: string, title: string) => void
    onConversationDeleted: (id: string) => void
  }

  export interface ConsumeShellHandle {
    togglePanel: () => void
  }

  export const ConsumeShell = forwardRef<ConsumeShellHandle, Props>(function ConsumeShell(
    {
      children,
      rightPanel,
      rightPanelLabel = 'Reports',
      rightPanelBadge,
      headerTitle,
      headerMeta,
      headerActions,
      conversationId,
      onRenameConversation,
      chartId,
      chartName,
      conversations,
      currentConversationId,
      onConversationRenamed,
      onConversationDeleted,
    },
    ref
  ) {
    // LOCKED: panelOpen = false → sidebar starts collapsed (spec §8 lock #1)
    const [panelOpen, setPanelOpen] = useState(false)
    const [editing, setEditing] = useState(false)
    const [titleDraft, setTitleDraft] = useState(headerTitle ?? '')
    const inputRef = useRef<HTMLInputElement>(null)

    useImperativeHandle(ref, () => ({
      togglePanel: () => setPanelOpen(o => !o),
    }))

    useEffect(() => {
      setTitleDraft(headerTitle ?? '')
    }, [headerTitle])

    useEffect(() => {
      if (editing) inputRef.current?.focus()
    }, [editing])

    // Warm Shiki highlighter on idle (same as ChatShell)
    useEffect(() => {
      const ric =
        (window as unknown as { requestIdleCallback?: (cb: () => void) => number })
          .requestIdleCallback
      const run = () => { getHighlighter().catch(() => {}) }
      if (ric) ric(run)
      else setTimeout(run, 200)
    }, [])

    function saveTitle() {
      const trimmed = titleDraft.trim()
      setEditing(false)
      if (!trimmed || trimmed === headerTitle || !conversationId || !onRenameConversation) return
      onRenameConversation(conversationId, trimmed).catch(() => {
        setTitleDraft(headerTitle ?? '')
      })
    }

    return (
      <div className="flex h-full w-full overflow-hidden">
        <ConsumeRail
          panelOpen={panelOpen}
          onPanelOpenChange={setPanelOpen}
          chartId={chartId}
          chartName={chartName}
          conversations={conversations}
          currentConversationId={currentConversationId}
          onConversationRenamed={onConversationRenamed}
          onConversationDeleted={onConversationDeleted}
        />

        {/* Main column */}
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          {/* ConsumeHeader — 48px */}
          <header className="flex h-12 shrink-0 items-center gap-2 border-b border-[rgba(var(--brand-gold-rgb),0.08)] bg-[oklch(0.08_0.010_70)] px-3">
            <button
              type="button"
              onClick={() => setPanelOpen(o => !o)}
              aria-label="Toggle sidebar"
              className="flex size-7 items-center justify-center rounded-md text-[var(--brand-gold-cream)]/40 transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[var(--brand-gold-cream)]/80"
            >
              <PanelLeft className="size-4" />
            </button>

            <div className="min-w-0 flex-1">
              {editing ? (
                <input
                  ref={inputRef}
                  value={titleDraft}
                  onChange={e => setTitleDraft(e.target.value)}
                  onBlur={saveTitle}
                  onKeyDown={e => {
                    if (e.key === 'Enter') saveTitle()
                    if (e.key === 'Escape') {
                      setEditing(false)
                      setTitleDraft(headerTitle ?? '')
                    }
                  }}
                  className="w-full bg-transparent text-sm font-medium text-foreground outline-none"
                />
              ) : (
                <button
                  type="button"
                  onDoubleClick={() => conversationId && onRenameConversation && setEditing(true)}
                  className="flex min-w-0 flex-col items-start text-left"
                >
                  <span className="truncate text-sm font-medium text-foreground leading-tight">
                    {headerTitle}
                  </span>
                  {headerMeta && (
                    <span className="truncate text-[9px] font-bold uppercase tracking-[0.14em] text-[var(--brand-gold)]/40 leading-none mt-0.5">
                      {headerMeta}
                    </span>
                  )}
                </button>
              )}
            </div>

            {headerActions && (
              <div className="flex shrink-0 items-center gap-1">
                {headerActions}
              </div>
            )}
          </header>

          {/* Scroll area */}
          {children}
        </div>

        {/* Right panel (Reports) — Sheet via Radix portal, caller manages open state */}
        {rightPanel}
      </div>
    )
  })
  ```

- [ ] **Step 2: TypeScript check**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | grep -E "ConsumeShell|error TS" | head -20`
  Expected: zero errors.

- [ ] **Step 3: Commit**

  ```bash
  cd platform && git add src/components/consume/ConsumeShell.tsx
  git commit -m "feat(consume): ConsumeShell — full-screen shell with inline ConsumeRail and imperative togglePanel handle"
  ```

---

## Task 4: Wire `ConsumeChat.tsx` — swap ChatShell → ConsumeShell

**Files:**
- Modify: `platform/src/components/consume/ConsumeChat.tsx`

**Context:** Four changes: (1) remove `desktopSidebarCollapsed` + `mobileSidebarOpen` state; (2) add `consumeShellRef` to drive panel toggle from command palette and hotkeys; (3) swap `<ChatShell>` → `<ConsumeShell>` with updated props; (4) remove the local `sidebar` variable (ConsumeShell owns it now).

- [ ] **Step 1: Add the ConsumeShell import and remove ChatShell import**

  In `platform/src/components/consume/ConsumeChat.tsx`:

  Replace:
  ```tsx
  import { ChatShell } from '@/components/chat/ChatShell'
  ```
  With:
  ```tsx
  import { ConsumeShell, type ConsumeShellHandle } from './ConsumeShell'
  ```

- [ ] **Step 2: Add `consumeShellRef`, remove collapsed/mobile state**

  Around line 113 (`composerEl` ref), add after it:
  ```tsx
  const consumeShellRef = useRef<ConsumeShellHandle>(null)
  ```

  Remove these two state declarations (lines ~136–137):
  ```tsx
  const [desktopSidebarCollapsed, setDesktopSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  ```

- [ ] **Step 3: Update `useHotkeys` `onToggleSidebar`**

  Find (around line 273):
  ```tsx
  onToggleSidebar: () => setDesktopSidebarCollapsed(c => !c),
  ```
  Replace with:
  ```tsx
  onToggleSidebar: () => consumeShellRef.current?.togglePanel(),
  ```

- [ ] **Step 4: Update `toggle-sidebar` command in `paletteCommands`**

  Find (around line 300–307):
  ```tsx
  {
    id: 'toggle-sidebar',
    label: desktopSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar',
    hint: '⌘B',
    icon: PanelLeft,
    section: 'View',
    run: () => setDesktopSidebarCollapsed(c => !c),
  },
  ```
  Replace with:
  ```tsx
  {
    id: 'toggle-sidebar',
    label: 'Toggle sidebar',
    hint: '⌘B',
    icon: PanelLeft,
    section: 'View',
    run: () => consumeShellRef.current?.togglePanel(),
  },
  ```

  Also remove `desktopSidebarCollapsed` from the `useMemo` deps array at the end of `paletteCommands`. This is safe because Step 4 changes the label to the static string `'Toggle sidebar'` — no stale closure risk remains.
  Find: `}, [chartId, router, desktopSidebarCollapsed, setStack, setStyle, handleReportViewChange])`
  Replace: `}, [chartId, router, setStack, setStyle, handleReportViewChange])`

- [ ] **Step 5: Remove `sidebar` variable, remove Trace from toolbar, rewrite return JSX**

  **5a — Delete the `sidebar` variable** (lines ~480–492):
  ```tsx
  // DELETE this entire block:
  const sidebar = (
    <ConversationSidebar
      chartId={chartId}
      ...
    />
  )
  ```

  **5b — Remove ONLY the Trace button from the toolbar** (lines ~775–791). Inside the composer zone `div ref={composerEl}`, find and delete this sub-block — the surrounding `(panelModeEnabled || initialAudienceTier === 'super_admin') && (<>...</>)` conditional and the `TierPicker` and `Panel` checkbox inside it must stay:
  ```tsx
  // DELETE only this sub-block (leave TierPicker and Panel checkbox):
  {/* Trace — opens drawer instead of inline panel */}
  {activeTier === 'super_admin' && (
    <button
      type="button"
      onClick={() => setTraceDrawerOpen(o => !o)}
      className={[...].join(' ')}
      aria-label="Toggle query trace drawer"
    >
      <Zap className="h-3 w-3" />
      Trace
    </button>
  )}
  ```

  **5c — Replace the `return (` block** starting at line ~510. The new return has this tree:
  - Outer `<div>` (consume-shell wrapper)
    - `<ConsumeShell>` (replaces `<ChatShell>`) — receives all scroll/composer content as `children`
      - scroll area div (unchanged)
      - ScrollToBottomButton div (unchanged)
      - error banner (unchanged)
      - composerEl div (unchanged, minus the Trace button removed in 5b)
    - `<ShortcutsDialog />` — sibling of ConsumeShell, NOT inside it
    - `<CommandPalette />` — sibling
    - `<TraceDrawer />` — sibling
    - `<ConversationHistoryDrawer />` — sibling

  ```tsx
  return (
    <div className="consume-shell h-full flex flex-col">
      <ConsumeShell
        ref={consumeShellRef}
        rightPanel={rightPanel}
        rightPanelLabel="Reports"
        rightPanelBadge={reports.length}
        headerTitle={chartName}
        headerMeta={chartMeta}
        headerActions={
          <div className="flex items-center gap-1">
            <ConversationHistoryButton
              onClick={() => setHistoryDrawerOpen(true)}
              count={conversations.length}
            />
            <ShareButton conversationId={session.conversationId} />
            {/* LOCKED: Trace in header, not toolbar (AGENTS.md lock #2) */}
            {activeTier === 'super_admin' && (
              <button
                type="button"
                onClick={() => setTraceDrawerOpen(o => !o)}
                className={[
                  'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors',
                  traceDrawerOpen
                    ? 'border-[rgba(var(--status-warn-rgb),0.6)] bg-[var(--status-warn-bg)] text-[var(--status-warn)]'
                    : 'border-border text-muted-foreground hover:border-[rgba(var(--status-warn-rgb),0.4)] hover:bg-[var(--status-warn-bg)] hover:text-[var(--status-warn)]',
                ].join(' ')}
                aria-label="Toggle query trace drawer"
              >
                <Zap className="h-3 w-3" />
                Trace
              </button>
            )}
          </div>
        }
        conversationId={session.conversationId}
        onRenameConversation={handleRenameConversation}
        chartId={chartId}
        chartName={chartName}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onConversationRenamed={(id, title) =>
          setConversations(prev => prev.map(c => (c.id === id ? { ...c, title } : c)))
        }
        onConversationDeleted={id =>
          setConversations(prev => prev.filter(c => c.id !== id))
        }
      >
        {/* ── Scroll area — unchanged content ─────────────────────────── */}
        <div
          ref={scrollRef}
          role="log"
          aria-label="Conversation"
          aria-live="polite"
          className="relative flex-1 min-h-0 overflow-y-auto overflow-x-hidden [scrollbar-gutter:stable]"
        >
          {/* ...all existing EmptyState / message stream JSX unchanged... */}
          <div ref={bottomRef} className="h-1" />
        </div>

        {/* ── ScrollToBottomButton — unchanged ────────────────────────── */}
        <div className="pointer-events-none absolute inset-x-0 bottom-[var(--composer-h)] z-20 flex justify-center">
          <ScrollToBottomButton
            visible={!isAtBottom && !messagesEmpty}
            onClick={() => scrollToBottom('smooth')}
          />
        </div>

        {/* ── Error banner — unchanged ─────────────────────────────────── */}
        {session.error && !validatorFailures && (() => {
          // ...existing error banner JSX unchanged...
        })()}

        {/* ── Composer zone — unchanged, minus Trace button (removed in 5b) */}
        <div ref={composerEl} className="relative shrink-0 border-t border-border/60 bg-background/80 backdrop-blur supports-backdrop-filter:bg-background/60 pb-[env(safe-area-inset-bottom)]">
          {/* ...archived branch notice, toolbar row, LEL-off notice, Composer — unchanged... */}
        </div>
      </ConsumeShell>

      {/* ── Portal-rendered overlays — siblings of ConsumeShell ─────── */}
      <ShortcutsDialog open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        commands={paletteCommands}
      />
      <TraceDrawer
        open={traceDrawerOpen}
        onOpenChange={setTraceDrawerOpen}
        conversationId={session.conversationId}
      />
      <ConversationHistoryDrawer
        open={historyDrawerOpen}
        onOpenChange={setHistoryDrawerOpen}
        conversations={conversations}
        chartId={chartId}
        currentConversationId={currentConversationId}
      />
    </div>
  )
  ```

  > **Note:** The `...unchanged...` comments mean "keep the existing JSX from the old `<ChatShell>` children verbatim." Do not retype it — just retain it when doing the structural replacement. The only structural changes are: (a) `<ChatShell>` → `<ConsumeShell>`, (b) four portal siblings moved from being siblings of `<ChatShell>` to being siblings of `<ConsumeShell>` (they were already outside `<ChatShell>` in the live code, so their position in the outer `<div>` is unchanged), (c) Trace button removed from toolbar (Step 5b).

- [ ] **Step 6: TypeScript check**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | head -40`
  Expected: zero errors. Fix any prop-mismatch errors before proceeding.

- [ ] **Step 7: Browser verification — golden path**

  At `http://localhost:3000/clients/[chartId]/consume`:
  - [ ] Rail renders 44px wide, icon-only on fresh load (sidebar starts collapsed)
  - [ ] Hover over rail → 240px panel slides in, ConversationSidebar visible
  - [ ] Click outside panel → panel closes
  - [ ] `⌘B` / command-palette "Toggle sidebar" → panel opens/closes
  - [ ] Header shows chart name + meta; History + Share buttons in right slot
  - [ ] Trace button in header (only when `?tier=super_admin`), not in toolbar
  - [ ] Composer pinned at bottom; no page-level scroll

- [ ] **Step 8: Commit**

  ```bash
  cd platform && git add src/components/consume/ConsumeChat.tsx
  git commit -m "feat(consume): wire ConsumeShell — swap ChatShell, imperative panel toggle, Trace moved to header"
  ```

---

## Task 5: Restyle `AssistantMessage.tsx` — gold avatar + full-width layout

**Files:**
- Modify: `platform/src/components/chat/AssistantMessage.tsx`

**Context:** Currently uses a small circular border-only avatar with `AssistantSigil` inside it. Spec calls for: 28px solid gold-gradient circle with `✦` glyph (pulses during streaming), full-width layout (no bubble), model chip + action row below last turn. All inner markdown rendering stays intact.

- [ ] **Step 1: Replace the outer wrapper and avatar**

  In `platform/src/components/chat/AssistantMessage.tsx`, find the `return (` block at line 86. Replace the outer `motion.div` and the first `div.flex.gap-4` + avatar `div` with:

  ```tsx
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="group/message mx-auto w-full max-w-3xl px-6"
    >
      <div className="flex items-start gap-3.5">
        {/* Gold ✦ avatar — pulses during streaming */}
        <div
          className={cn(
            'mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-[13px] font-bold',
            'bg-gradient-to-br from-[var(--brand-gold)] to-[oklch(0.65_0.15_70)]',
            'text-[oklch(0.08_0.010_70)]',
            isStreaming && isLast && 'animate-[avatar-pulse_1.5s_ease-in-out_infinite]'
          )}
          style={{
            boxShadow: isStreaming && isLast
              ? undefined
              : '0 0 8px rgba(var(--brand-gold-rgb), 0.2)',
          }}
        >
          ✦
        </div>
  ```

  After the avatar div, keep the `<div className="min-w-0 flex-1 pt-0.5">` body div. Inside it, add a name label as the first child:

  ```tsx
        <div className="min-w-0 flex-1">
          <p className="mb-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--brand-gold)]/50">
            MARSYS
          </p>
  ```

  Remove the old avatar div (the `size-8 shrink-0 items-center justify-center rounded-full border border-[rgba(var(--brand-gold-rgb),0.35)] bg-muted` one) entirely.

- [ ] **Step 2: Import `cn` if not already imported**

  Check line 1–14 of the file. `cn` is imported from `@/lib/utils` in most components. Add if missing:
  ```tsx
  import { cn } from '@/lib/utils'
  ```

- [ ] **Step 3: TypeScript check**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | grep -E "AssistantMessage|error TS" | head -20`
  Expected: zero errors.

- [ ] **Step 4: Browser spot-check**

  Send a test message. Verify:
  - [ ] Gold `✦` filled circle appears left of AI response
  - [ ] "MARSYS" label above content in small gold uppercase
  - [ ] No bubble background on AI message (full-width text)
  - [ ] Avatar glows/pulses during streaming
  - [ ] Model chip, timestamp, and action row still render below completed response

- [ ] **Step 5: Commit**

  ```bash
  cd platform && git add src/components/chat/AssistantMessage.tsx
  git commit -m "feat(consume): AssistantMessage — gold ✦ avatar, full-width layout, streaming pulse"
  ```

---

## Task 6: Restyle `EmptyState.tsx` — centre + token polish

**Files:**
- Modify: `platform/src/components/consume/EmptyState.tsx`

**Context:** Currently `max-w-3xl`. With new shell width (no fixed sidebar offset), re-centre to `max-w-2xl`. Tab active indicator: gold bottom border. Suggestion button hover: gold border, no fill. All tab logic and API call preserved.

- [ ] **Step 1: Update container width**

  In `platform/src/components/consume/EmptyState.tsx` at line 51:
  Find: `className={cn('mx-auto w-full max-w-3xl px-4 py-12', className)}`
  Replace: `className={cn('mx-auto w-full max-w-2xl px-4 py-12', className)}`

- [ ] **Step 2: Confirm tab styling (already correct in live code)**

  The active tab in `EmptyState.tsx` already uses `border-b-2 border-[var(--brand-gold)]`. Verify this is present and add `border-b-2 border-transparent` to the inactive tab if it's missing — this ensures height stability (both tabs have equal border-bottom regardless of active state):
  ```tsx
  // Active tab (verify exists):
  'border-b-2 border-[var(--brand-gold)] text-foreground'
  // Inactive tab (add border-transparent if missing):
  'border-b-2 border-transparent text-muted-foreground hover:text-foreground'
  ```

- [ ] **Step 3: Update suggestion button hover**

  Find suggestion buttons (the `onPick` call buttons). Add:
  ```tsx
  className="... border border-border hover:border-[rgba(var(--brand-gold-rgb),0.4)] hover:bg-[rgba(var(--brand-gold-rgb),0.05)] transition-colors"
  ```
  Remove any existing `hover:bg-muted` or solid fill on hover.

- [ ] **Step 4: TypeScript check**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | grep -E "EmptyState|error TS" | head -10`
  Expected: zero errors.

- [ ] **Step 5: Browser verification**

  Navigate to `http://localhost:3000/clients/[chartId]/consume` (no conversation):
  - [ ] EmptyState is centred in the full available width (no sidebar offset)
  - [ ] Active tab has gold bottom border
  - [ ] Suggestion buttons show gold border on hover, no fill

- [ ] **Step 6: Commit**

  ```bash
  cd platform && git add src/components/consume/EmptyState.tsx
  git commit -m "feat(consume): EmptyState — re-centre max-w-2xl, gold tab underline, suggestion button hover"
  ```

---

## Task 7: Append CSS additions to `globals.css`

**Files:**
- Modify: `platform/src/app/globals.css`

**Context:** Append only — do not remove or modify any existing rules. Four additions: ConsumeRail panel transition, consume-shell scrollbar, composer card focus ring, avatar streaming pulse keyframe.

- [ ] **Step 1: Append the CSS block**

  At the end of `platform/src/app/globals.css`, append:

  ```css
  /* ── Consume UI Redesign additions (2026-05-15) ─────────────────────── */

  /* ConsumeRail hover-panel slide transition */
  .consume-rail-panel {
    transition: opacity 0.15s ease, transform 0.15s ease;
  }

  /* Scrollbar inside consume shell scroll area */
  .consume-shell .scroll-area {
    scrollbar-width: thin;
    scrollbar-color: rgba(var(--brand-gold-rgb), 0.12) transparent;
  }

  /* Composer card focus-within ring */
  .consume-composer-card:focus-within {
    border-color: rgba(var(--brand-gold-rgb), 0.4);
    box-shadow: 0 0 0 3px rgba(var(--brand-gold-rgb), 0.08);
  }

  /* AI avatar streaming pulse — referenced as animate-[avatar-pulse_...] in JSX */
  @keyframes avatar-pulse {
    0%, 100% { box-shadow: 0 0 8px rgba(var(--brand-gold-rgb), 0.2); }
    50%       { box-shadow: 0 0 20px rgba(var(--brand-gold-rgb), 0.5); }
  }
  ```

- [ ] **Step 2: Verify no existing rules broken**

  Run: `npx tsc --noEmit -p platform/tsconfig.json 2>&1 | head -10`
  Expected: zero errors (CSS changes don't affect TS, but ensures no accidental file corruption).

- [ ] **Step 3: Commit**

  ```bash
  cd platform && git add src/app/globals.css
  git commit -m "feat(consume): globals.css — rail panel transition, scrollbar, composer ring, avatar-pulse keyframe"
  ```

---

## Task 8: Browser verification — full test plan

**Files:** None (browser-only verification)

**Context:** End-to-end verification of all spec test cases from `docs/superpowers/specs/2026-05-15-consume-ui-redesign-design.md §10`. Dev server must be running (`npm run dev` in `platform/`).

- [ ] **Layout contract**
  - [ ] Chat fills full viewport — AppShell rail + breadcrumb invisible at `http://localhost:3000/clients/[chartId]/consume`
  - [ ] No outer-page scroll; only message area scrolls internally
  - [ ] Composer pinned at bottom; `ScrollToBottomButton` appears above it when scrolled up
  - [ ] Verified at: 1440px → 1280px → 1024px → 768px → 375px (use DevTools device toolbar)

- [ ] **ConsumeRail**
  - [ ] Default: 44px icon-only, no labels visible
  - [ ] Hover: panel slides in; ConversationSidebar renders inside with conversation list
  - [ ] Click-outside: panel dismisses
  - [ ] Active nav item (Consume): gold 3px left-bar indicator + gold icon tint
  - [ ] Dashboard icon navigates to `/dashboard`

- [ ] **Conversation flow**
  - [ ] New chat: messages clear, URL resets to `/clients/[chartId]/consume`
  - [ ] Send a message: avatar pulses during streaming; stops on completion
  - [ ] Navigate to existing conversation from sidebar panel: messages load, scroll to bottom
  - [ ] Rename: double-click title in header → inline input → Enter saves
  - [ ] Regenerate: last AI turn re-streams

- [ ] **Locked behaviors (AGENTS.md)**
  - [ ] Rail starts icon-only on fresh load (panel closed)
  - [ ] Trace button appears in header right slot (when `?tier=super_admin`), not in toolbar
  - [ ] Composer textarea is fixed 3-row, does not auto-grow

- [ ] **Feature flags**
  - [ ] `consumeUiV2Enabled=true` (if testable): lifecycle slot renders inside ConsumeShell scroll area
  - [ ] `panelModeEnabled=true`: Panel checkbox appears in toolbar
  - [ ] `?tier=super_admin`: Trace in header + TierPicker in toolbar visible

- [ ] **Other routes — regression**
  - [ ] `/clients/[id]/build`: AppShell renders correctly — rail + breadcrumb visible, no overlay
  - [ ] `/clients/[id]/build`: AI messages on build route use the updated `AssistantMessage` — verify gold avatar + `max-w-3xl` width are acceptable (this component is shared; Task 5 changes it globally, narrowing from `max-w-4xl`)
  - [ ] `/dashboard`: unaffected
  - [ ] `http://localhost:3000/login`: unaffected

- [ ] **Final commit (if any CSS/JSX tweaks applied during verification)**

  ```bash
  cd platform && git add -p
  git commit -m "fix(consume): browser verification tweaks"
  ```
