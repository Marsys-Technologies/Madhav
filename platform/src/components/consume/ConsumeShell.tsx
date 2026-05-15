'use client'

import { createPortal } from 'react-dom'
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useState,
  type ReactNode,
} from 'react'
import Link from 'next/link'
import { PanelLeft, ArrowLeft } from 'lucide-react'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { ConversationSidebar } from '@/components/chat/ConversationSidebar'
import { cn } from '@/lib/utils'
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
  chartId: string
  chartName: string
  conversations: ConversationRow[]
  currentConversationId?: string
  onConversationRenamed: (id: string, title: string) => void
  onConversationDeleted: (id: string) => void
}

export interface ConsumeShellHandle {
  togglePanel: () => void
  toggleRightPanel: () => void
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
    chartId,
    chartName,
    conversations,
    currentConversationId,
    onConversationRenamed,
    onConversationDeleted,
  },
  ref
) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [rightOpen, setRightOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  // Close sidebar on Escape
  useEffect(() => {
    if (!sidebarOpen) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setSidebarOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [sidebarOpen])

  // Warm Shiki highlighter on idle
  useEffect(() => {
    const ric =
      (window as unknown as { requestIdleCallback?: (cb: () => void) => number })
        .requestIdleCallback
    const run = () => { getHighlighter().catch(() => {}) }
    let timeoutId: ReturnType<typeof setTimeout> | undefined
    if (ric) ric(run)
    else timeoutId = setTimeout(run, 200)
    return () => { if (timeoutId) clearTimeout(timeoutId) }
  }, [])

  useImperativeHandle(ref, () => ({
    togglePanel: () => setSidebarOpen(o => !o),
    toggleRightPanel: () => setRightOpen(o => !o),
  }))

  const iconBtn = cn(
    'flex size-8 items-center justify-center rounded-md',
    'text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)]',
    'transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.06)]',
    'hover:text-[color-mix(in_oklch,var(--brand-gold-cream)_80%,transparent)]'
  )

  const sidebarOverlay = (
    <>
      {/* Click-away catch — transparent so gradient shows through unobstructed */}
      <div
        className={cn(
          'fixed inset-0 z-[59] transition-[pointer-events] duration-200',
          sidebarOpen ? 'pointer-events-auto' : 'pointer-events-none'
        )}
        onClick={() => setSidebarOpen(false)}
        aria-hidden
      />
      {/* Slide-over panel — translate off-screen when closed; extra 2px hides border-r */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-[60] w-72 overflow-hidden',
          'border-r border-[rgba(var(--brand-gold-rgb),0.18)]',
          'backdrop-blur-xl',
          'transition-[translate] duration-200 ease-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-[calc(100%+2px)]'
        )}
        style={{ backgroundColor: 'rgba(10,7,2,0.30)' }}
      >
        <ConversationSidebar
          simple
          chartId={chartId}
          chartName={chartName}
          conversations={conversations}
          currentConversationId={currentConversationId}
          onRenamed={onConversationRenamed}
          onDeleted={onConversationDeleted}
          onClose={() => setSidebarOpen(false)}
          onNavigate={() => setSidebarOpen(false)}
        />
      </div>
    </>
  )

  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      {/* Header — 48px */}
      <header className="flex h-12 shrink-0 items-center gap-1 px-2">
        {/* Conversations sidebar toggle */}
        <button
          type="button"
          onClick={() => setSidebarOpen(o => !o)}
          aria-label="Toggle conversations"
          aria-expanded={sidebarOpen}
          className={iconBtn}
        >
          <PanelLeft className="size-4" />
        </button>

        {/* Back to dashboard */}
        <Link href="/dashboard" aria-label="Back to dashboard" className={iconBtn}>
          <ArrowLeft className="size-4" />
        </Link>

        {/* Title + meta */}
        <div className="min-w-0 flex-1 px-1.5">
          <span
            role="heading"
            aria-level={1}
            className="truncate font-serif text-[15px] font-medium text-foreground leading-tight block"
          >
            {headerTitle}
          </span>
          {headerMeta && (
            <span className="truncate text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)] leading-none block mt-0.5">
              {headerMeta}
            </span>
          )}
        </div>

        {/* Right-side actions (History, Trace, etc.) */}
        {headerActions && (
          <div className="flex shrink-0 items-center gap-1">
            {headerActions}
          </div>
        )}
      </header>

      {/* Scroll area + composer — passed as children */}
      {children}

      {/* Sidebar overlay — portaled to body after mount to escape any stacking context */}
      {mounted ? createPortal(sidebarOverlay, document.body) : null}

      {/* Right panel (Reports) — Sheet via portal */}
      {rightPanel && (
        <Sheet open={rightOpen} onOpenChange={setRightOpen}>
          <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto p-0">
            <SheetTitle className="sr-only">
              {rightPanelLabel}{typeof rightPanelBadge === 'number' ? ` (${rightPanelBadge})` : ''}
            </SheetTitle>
            {rightPanel}
          </SheetContent>
        </Sheet>
      )}
    </div>
  )
})
