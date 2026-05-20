'use client'

import { useEffect, useRef, useState, type ReactNode } from 'react'
import Link from 'next/link'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { PanelLeft, FileText, X, Pencil, ChevronLeft } from 'lucide-react'
import { ExportDropdown } from './ExportDropdown'
import { cn } from '@/lib/utils'
import { getHighlighter } from '@/lib/shiki'

interface Props {
  sidebar: ReactNode
  children: ReactNode
  rightPanel?: ReactNode
  rightPanelLabel?: string
  rightPanelBadge?: number
  headerTitle?: string
  headerMeta?: string
  headerActions?: ReactNode
  desktopSidebarCollapsed: boolean
  mobileSidebarOpen: boolean
  onToggleDesktopSidebar: () => void
  onToggleMobileSidebar: () => void
  setMobileSidebarOpen: (open: boolean) => void
  conversationId?: string
  onRenameConversation?: (id: string, title: string) => Promise<void>
}

export function ChatShell({
  sidebar,
  children,
  rightPanel,
  rightPanelLabel = 'Reports',
  rightPanelBadge,
  headerTitle,
  headerMeta,
  headerActions,
  desktopSidebarCollapsed,
  mobileSidebarOpen,
  onToggleDesktopSidebar,
  onToggleMobileSidebar,
  setMobileSidebarOpen,
  conversationId,
  onRenameConversation,
}: Props) {
  const [rightOpen, setRightOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [titleDraft, setTitleDraft] = useState(headerTitle ?? '')
  const inputRef = useRef<HTMLInputElement>(null)

  // Keep draft in sync when the title changes externally (e.g. after nav)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTitleDraft(headerTitle ?? '')
  }, [headerTitle])

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  // Warm the Shiki highlighter bundle on idle so the first code block post-stream
  // renders with zero cold-start delay. CodeBlock skips Shiki during streaming.
  useEffect(() => {
    const ric =
      (window as unknown as { requestIdleCallback?: (cb: () => void) => number })
        .requestIdleCallback
    const run = () => {
      getHighlighter().catch(() => {})
    }
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

  function cancelTitle() {
    setTitleDraft(headerTitle ?? '')
    setEditing(false)
  }

  const canRename = !!conversationId && !!onRenameConversation

  return (
    <div
      className="relative flex h-[100dvh] w-full bg-background"
      style={{ ['--composer-h' as string]: '160px' }}
    >
      <a
        href="#chat-main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-3 focus:py-2 focus:bg-zinc-900 focus:text-amber-400 focus:rounded"
      >
        Skip to chat
      </a>
      <aside
        aria-label="Conversations"
        className={cn(
          'hidden h-full shrink-0 border-r border-sidebar-border bg-sidebar transition-[width] duration-200 md:flex',
          desktopSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-[260px]'
        )}
        aria-hidden={desktopSidebarCollapsed}
      >
        {!desktopSidebarCollapsed && <div className="flex h-full w-[260px] flex-col">{sidebar}</div>}
      </aside>

      {/* Collapsed sidebar hover strip — desktop only */}
      {desktopSidebarCollapsed && (
        <button
          type="button"
          onClick={onToggleDesktopSidebar}
          aria-label="Expand sidebar"
          className="hidden md:flex fixed left-0 top-1/2 z-10 -translate-y-1/2 h-24 w-2 hover:w-8 transition-all duration-200 rounded-r bg-[rgba(var(--brand-gold-rgb),0.25)] hover:bg-[rgba(var(--brand-gold-rgb),0.6)] items-center justify-center overflow-hidden"
        >
          <PanelLeft className="h-4 w-4 text-[var(--brand-charcoal)] opacity-0 group-hover:opacity-100 shrink-0" />
        </button>
      )}

      <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
        <SheetContent side="left" className="w-[78%] max-w-[300px] bg-sidebar p-0 md:hidden">
          <SheetTitle className="sr-only">Conversations</SheetTitle>
          <div className="flex h-full flex-col">{sidebar}</div>
        </SheetContent>
      </Sheet>

      <main id="chat-main" className="relative flex h-full flex-1 flex-col overflow-hidden" aria-label="Chat">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-border/60 bg-background/60 px-3 backdrop-blur supports-backdrop-filter:bg-background/40">
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            aria-label="Toggle sidebar"
            className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:hidden"
          >
            <PanelLeft className="size-4" />
          </button>
          <button
            type="button"
            onClick={onToggleDesktopSidebar}
            aria-label={desktopSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
            className="hidden size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:inline-flex"
          >
            <PanelLeft className="size-4" />
          </button>

          {/* Dashboard breadcrumb — desktop only; mobile uses sidebar drawer */}
          <Link
            href="/dashboard"
            aria-label="Back to dashboard"
            className="hidden md:inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground shrink-0"
          >
            <ChevronLeft className="size-3.5" />
            <span>Dashboard</span>
          </Link>

          {/* Title area — stacked: h1 title + chartMeta always visible */}
          <div className="flex min-w-0 flex-1 items-center gap-2">
            {headerTitle && (
              <div className="group/title flex min-w-0 flex-col leading-tight">
                {editing ? (
                  <input
                    ref={inputRef}
                    value={titleDraft}
                    onChange={e => setTitleDraft(e.target.value)}
                    onBlur={saveTitle}
                    onKeyDown={e => {
                      if (e.key === 'Enter') { e.preventDefault(); saveTitle() }
                      if (e.key === 'Escape') { e.preventDefault(); cancelTitle() }
                    }}
                    className="truncate rounded bg-transparent text-sm font-medium text-foreground outline-none ring-1 ring-[var(--brand-gold)]/60 px-1 min-w-0 max-w-[200px]"
                    aria-label="Conversation title"
                  />
                ) : (
                  <div className="flex items-center gap-1">
                    <h1
                      className="truncate text-sm font-medium text-foreground max-w-[200px]"
                      onDoubleClick={canRename ? () => setEditing(true) : undefined}
                      title={canRename ? 'Double-click to rename' : undefined}
                    >
                      {headerTitle}
                    </h1>
                    {canRename && (
                      <button
                        type="button"
                        onClick={() => setEditing(true)}
                        aria-label="Rename conversation"
                        className="shrink-0 opacity-0 group-hover/title:opacity-100 transition-opacity inline-flex size-5 items-center justify-center rounded text-[var(--brand-gold-hairline)] hover:text-[var(--brand-gold)]"
                      >
                        <Pencil className="size-3" />
                      </button>
                    )}
                  </div>
                )}
                {headerMeta && (
                  <p className="truncate text-[10px] uppercase tracking-[0.24em] text-[var(--brand-cream)]/50">
                    {headerMeta}
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="ml-auto flex items-center gap-1">
            {conversationId && <ExportDropdown conversationId={conversationId} />}
            {headerActions}
            {rightPanel && (
              <button
                type="button"
                onClick={() => setRightOpen(true)}
                aria-label={rightPanelLabel}
                className="inline-flex h-8 items-center gap-1.5 rounded-md px-2 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <FileText className="size-3.5" />
                <span className="hidden sm:inline">{rightPanelLabel}</span>
                {typeof rightPanelBadge === 'number' && rightPanelBadge > 0 && (
                  <span className="inline-flex min-w-[18px] justify-center rounded-full bg-muted px-1.5 text-[10px] font-medium text-muted-foreground">
                    {rightPanelBadge}
                  </span>
                )}
              </button>
            )}
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1 flex-col">{children}</div>
      </main>

      {rightPanel && (
        <Sheet open={rightOpen} onOpenChange={setRightOpen}>
          <SheetContent
            side="right"
            className="w-[92%] max-w-2xl lg:max-w-3xl overflow-hidden p-0"
            showCloseButton={false}
          >
            <div className="flex h-full flex-col">
              <div className="flex h-12 shrink-0 items-center justify-between border-b border-border/60 px-3">
                <SheetTitle className="text-sm font-medium">{rightPanelLabel}</SheetTitle>
                <button
                  type="button"
                  onClick={() => setRightOpen(false)}
                  aria-label="Close"
                  className="inline-flex size-7 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <X className="size-4" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">{rightPanel}</div>
            </div>
          </SheetContent>
        </Sheet>
      )}
    </div>
  )
}
