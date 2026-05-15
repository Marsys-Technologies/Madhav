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
              >
                <span className="truncate text-sm font-medium text-foreground leading-tight">
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
      </div>

      {/* Right panel (Reports) — Sheet via Radix portal, caller manages open state */}
      {rightPanel}
    </div>
  )
})
