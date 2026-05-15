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
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [rightOpen, setRightOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [titleDraft, setTitleDraft] = useState(headerTitle ?? '')
  const inputRef = useRef<HTMLInputElement>(null)

  useImperativeHandle(ref, () => ({
    togglePanel: () => setSidebarOpen(o => !o),
    toggleRightPanel: () => setRightOpen(o => !o),
  }))

  useEffect(() => {
    if (!editing) {
      setTitleDraft(headerTitle ?? '')
    }
  }, [headerTitle, editing])

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  // Warm Shiki highlighter on idle
  useEffect(() => {
    const ric =
      (window as unknown as { requestIdleCallback?: (cb: () => void) => number })
        .requestIdleCallback
    const run = () => { getHighlighter().catch(() => {}) }
    let timeoutId: ReturnType<typeof setTimeout> | undefined
    if (ric) ric(run)
    else timeoutId = setTimeout(run, 200)
    return () => {
      if (timeoutId) clearTimeout(timeoutId)
    }
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
    <div className="flex h-full w-full flex-col overflow-hidden">
      {/* Header — 48px */}
      <header className="flex h-12 shrink-0 items-center gap-2 border-b border-[rgba(var(--brand-gold-rgb),0.08)] px-3">
        <button
          type="button"
          onClick={() => setSidebarOpen(o => !o)}
          aria-label="Toggle sidebar"
          className="flex size-7 items-center justify-center rounded-md text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.06)] hover:text-[color-mix(in_oklch,var(--brand-gold-cream)_80%,transparent)]"
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
              aria-label={headerTitle ? `Conversation title: ${headerTitle}. Double-click to rename.` : 'Untitled conversation'}
            >
              <span
                role="heading"
                aria-level={1}
                className="truncate text-sm font-medium text-foreground leading-tight"
              >
                {headerTitle}
              </span>
              {headerMeta && (
                <span className="truncate text-[9px] font-bold uppercase tracking-[0.14em] text-[rgba(var(--brand-gold-rgb),0.4)] leading-none mt-0.5">
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

      {/* Scroll area + composer — passed as children */}
      {children}

      {/* ── Left sidebar (Gemini-style slide-over) ── */}

      {/* Backdrop — fades with sidebar; click outside closes */}
      <div
        className={cn(
          'fixed inset-0 z-[59] bg-black/20 transition-opacity duration-200',
          sidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setSidebarOpen(false)}
        aria-hidden
      />

      {/* Panel — overflow-hidden clips ConversationSidebar; extra 2px in closed
          translate ensures the border-r is fully off-screen (not at x=0) */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-[60] w-[280px] overflow-hidden',
          'border-r border-[rgba(var(--brand-gold-rgb),0.12)] bg-[#0b0804]',
          'transition-[translate] duration-200 ease-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-[calc(100%+2px)]'
        )}
      >
        <ConversationSidebar
          chartId={chartId}
          chartName={chartName}
          conversations={conversations}
          currentConversationId={currentConversationId}
          onRenamed={onConversationRenamed}
          onDeleted={onConversationDeleted}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

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
