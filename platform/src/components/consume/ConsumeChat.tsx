'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import type { UIMessage } from 'ai'
import {
  Plus,
  PanelLeft,
  FileText,
  Keyboard,
  Database,
  Zap,
  FileQuestion,
  BookOpen,
  BookOpenText,
  Info,
  User,
  Columns3,
  LayoutGrid,
  List,
} from 'lucide-react'
import { stackPicker, getModelMeta, PROVIDER_LABEL } from '@/lib/models/registry'
import { ChatShell } from '@/components/chat/ChatShell'
import { ConversationSidebar } from '@/components/chat/ConversationSidebar'
import { PendingAssistantBubble } from '@/components/chat/PendingAssistantBubble'
import { Composer, type ComposerHandle } from '@/components/chat/Composer'
// WelcomeGreeting retired in favor of Gate III EmptyState; kept import-free.
import { ScrollToBottomButton } from '@/components/chat/ScrollToBottomButton'
import { ShortcutsDialog } from '@/components/chat/ShortcutsDialog'
import { CommandPalette, type Command } from '@/components/chat/CommandPalette'
import { ReportLibrary } from './ReportLibrary'
import { ReportReader } from './ReportReader'
import { TraceDrawer } from './TraceDrawer'
import { TierPicker } from './TierPicker'
import { LiveReasoningCard } from './LiveReasoningCard'
import { CorrectionNotice } from './CorrectionNotice'
import { ContextUsageCue } from './ContextUsageCue'
import { OutOfDomainBanner } from './OutOfDomainBanner'
import { PostAnswerProvenance } from './PostAnswerProvenance'
import { EmptyState } from './EmptyState'
import { ConversationHistoryDrawer } from './ConversationHistoryDrawer'
import { ConversationHistoryButton } from './ConversationHistoryButton'
import type {
  ReasoningStepEvent,
  SanskritTerm,
  CorrectionEvent,
  OutOfDomainEvent,
  ContextUsageEvent,
  ProvenanceEvent,
} from '@/types/sse_events'
import { useChatSession } from '@/hooks/useChatSession'
import { useScrollAnchor } from '@/hooks/useScrollAnchor'
import { useHotkeys } from '@/hooks/useHotkeys'
import { useFeedback } from '@/hooks/useFeedback'
import { useChatPreferences } from '@/hooks/useChatPreferences'
import { useAttachments, type Attachment } from '@/hooks/useAttachments'
import { useBranches } from '@/hooks/useBranches'
import { classifyChatError } from '@/lib/chat/classify-error'
import { ModelStylePicker } from '@/components/chat/ModelStylePicker'
import { ShareButton } from '@/components/chat/ShareButton'
import type { Report, ConversationModule } from '@/lib/db/types'
import { StreamingAnswer } from './StreamingAnswer'
import { ValidatorFailureView } from './ValidatorFailureView'
import { parseValidatorError } from '@/lib/ui/validator-error'
import type { AudienceTier } from '@/lib/prompts/types'

const REPORT_VIEW_KEY = 'marsys.consume.reportView'

interface ConversationRow {
  id: string
  title: string | null
  created_at: string
  chart_id: string
  user_id: string
  module: ConversationModule
}

interface Props {
  chartId: string
  chartName: string
  chartMeta?: string
  reports: Report[]
  conversations: ConversationRow[]
  currentConversationId?: string
  initialMessages?: UIMessage[]
  panelModeEnabled?: boolean
  audienceTier?: AudienceTier
}

export function ConsumeChat({
  chartId,
  chartName,
  chartMeta,
  reports,
  conversations: initialConversations,
  currentConversationId,
  initialMessages,
  panelModeEnabled = false,
  audienceTier: initialAudienceTier = 'client',
}: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const composerRef = useRef<ComposerHandle>(null)
  const composerEl = useRef<HTMLDivElement>(null)

  const [conversations, setConversations] = useState(initialConversations)
  const [panelOptIn, setPanelOptIn] = useState(false)
  const [traceDrawerOpen, setTraceDrawerOpen] = useState(false)
  // ── Gate III: per-turn state for the new surfaces ─────────────────────────
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStepEvent[]>([])
  const [correction, setCorrection] = useState<CorrectionEvent | null>(null)
  const [outOfDomain, setOutOfDomain] = useState<OutOfDomainEvent | null>(null)
  const [sanskritTerms, setSanskritTerms] = useState<SanskritTerm[]>([])
  const [contextUsage, setContextUsage] = useState<ContextUsageEvent | null>(null)
  const [provenance, setProvenance] = useState<ProvenanceEvent | null>(null)
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false)
  const [activeAssistantId, setActiveAssistantId] = useState<string | null>(null)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [desktopSidebarCollapsed, setDesktopSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)
  const [lelContextEnabled, setLelContextEnabled] = useState(true)

  // View preference persisted to localStorage
  const [reportView, setReportView] = useState<'list' | 'gallery'>(() => {
    if (typeof window === 'undefined') return 'gallery'
    return (localStorage.getItem(REPORT_VIEW_KEY) as 'list' | 'gallery') ?? 'gallery'
  })

  const handleReportViewChange = useCallback((v: 'list' | 'gallery') => {
    setReportView(v)
    localStorage.setItem(REPORT_VIEW_KEY, v)
  }, [])

  // Audience tier — super_admin can flip via URL ?tier=... or TierPicker
  const tierFromUrl = searchParams?.get('tier') as AudienceTier | null
  const [activeTier, setActiveTier] = useState<AudienceTier>(
    tierFromUrl ?? initialAudienceTier
  )

  const handleTierChange = useCallback((tier: AudienceTier) => {
    setActiveTier(tier)
    const url = new URL(window.location.href)
    url.searchParams.set('tier', tier)
    window.history.replaceState(window.history.state, '', url.toString())
  }, [])

  const { scrollRef, bottomRef, isAtBottom, scrollToBottom } = useScrollAnchor({ thresholdPx: 96 })

  const [validatorFailures, setValidatorFailures] = useState<
    ReturnType<typeof parseValidatorError>
  >(null)

  const { stack, style, setStack, setStyle } = useChatPreferences(chartId)

  const session = useChatSession({
    chartId,
    conversationId: currentConversationId,
    initialMessages,
    stack,
    style,
    onConversationCreated: id => {
      router.replace(`/clients/${chartId}/consume/${id}`, { scroll: false })
      setConversations(prev => [
        {
          id,
          title: null,
          created_at: new Date().toISOString(),
          chart_id: chartId,
          user_id: '',
          module: 'consume',
        } as ConversationRow,
        ...prev,
      ])
    },
  })

  useEffect(() => {
    const el = composerEl.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      const h = Math.ceil(entry.contentRect.height)
      document.documentElement.style.setProperty('--composer-h', `${h}px`)
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (session.error) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setValidatorFailures(parseValidatorError(session.error))
    } else {
      setValidatorFailures(null)
    }
  }, [session.error])

  const attachmentsApi = useAttachments()

  const handleSend = useCallback(
    (text: string, attachments?: Attachment[]) => {
      const files = (attachments ?? [])
        .filter(a => a.status === 'ready' && a.url)
        .map(a => ({
          type: 'file' as const,
          filename: a.filename,
          mediaType: a.mime,
          url: a.url!,
        }))
      // Gate III: reset per-turn marker state on new submission.
      setReasoningSteps([])
      setCorrection(null)
      setOutOfDomain(null)
      setSanskritTerms([])
      setProvenance(null)
      session.send(text, files, {
        lel_context_enabled: lelContextEnabled,
        ...(panelOptIn ? { panel_opt_in: true } : {}),
      })
      setPanelOptIn(false)
      if (files.length > 0) attachmentsApi.clear()
    },
    [session, attachmentsApi, panelOptIn, lelContextEnabled]
  )

  const handleRegenerate = useCallback(() => {
    session.regenerate()
  }, [session])

  const branches = useBranches(session.conversationId)

  const handleEdit = useCallback(
    (id: string, text: string) => {
      branches.archiveBranch(id, session.messages)
      session.editAndResubmit(id, text)
    },
    [branches, session]
  )

  const { ratings, rate } = useFeedback(session.conversationId)

  useHotkeys({
    onPalette: () => setPaletteOpen(o => !o),
    onNewChat: () => router.push(`/clients/${chartId}/consume`),
    onToggleSidebar: () => setDesktopSidebarCollapsed(c => !c),
    onShortcutsHelp: () => setShortcutsOpen(true),
    onEscape: () => {
      if (session.isStreaming) session.stop()
    },
  })

  const paletteCommands = useMemo<Command[]>(() => {
    const stackCommands: Command[] = stackPicker().map(s => ({
      id: `stack-${s.stack}`,
      label: `Stack: ${s.label}`,
      icon: Database,
      section: 'Stack',
      keywords: `${s.stack} ${s.synthesisModelId}`,
      run: () => setStack(s.stack),
    }))

    return [
      {
        id: 'new-chat',
        label: 'New chat',
        hint: '⌘⇧O',
        icon: Plus,
        section: 'Actions',
        keywords: 'create start fresh',
        run: () => router.push(`/clients/${chartId}/consume`),
      },
      {
        id: 'toggle-sidebar',
        label: desktopSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar',
        hint: '⌘B',
        icon: PanelLeft,
        section: 'View',
        run: () => setDesktopSidebarCollapsed(c => !c),
      },
      {
        id: 'toggle-reports',
        label: 'Open reports panel',
        icon: FileText,
        section: 'View',
        keywords: 'library domains',
        run: () => setSelectedDomain(null),
      },
      {
        id: 'report-view-gallery',
        label: 'Reports: Gallery view',
        icon: LayoutGrid,
        section: 'View',
        run: () => handleReportViewChange('gallery'),
      },
      {
        id: 'report-view-list',
        label: 'Reports: List view',
        icon: List,
        section: 'View',
        run: () => handleReportViewChange('list'),
      },
      {
        id: 'shortcuts',
        label: 'Keyboard shortcuts',
        hint: '⌘/',
        icon: Keyboard,
        section: 'Help',
        run: () => setShortcutsOpen(true),
      },
      ...stackCommands,
      {
        id: 'style-acharya',
        label: 'Style: Acharya depth',
        icon: BookOpenText,
        section: 'Style',
        keywords: 'full technical jyotish',
        run: () => setStyle('acharya'),
      },
      {
        id: 'style-brief',
        label: 'Style: Brief',
        icon: FileQuestion,
        section: 'Style',
        keywords: 'short concise terse',
        run: () => setStyle('brief'),
      },
      {
        id: 'style-client',
        label: 'Style: Client-facing',
        icon: User,
        section: 'Style',
        keywords: 'plain no sanskrit jargon',
        run: () => setStyle('client'),
      },
    ]
  }, [chartId, router, desktopSidebarCollapsed, setStack, setStyle, handleReportViewChange])

  useEffect(() => {
    if (!session.isStreaming) composerRef.current?.focus()
  }, [session.isStreaming, currentConversationId])

  const handleRenameConversation = useCallback(
    async (id: string, title: string) => {
      const res = await fetch(`/api/conversations/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      if (res.ok) {
        setConversations(prev => prev.map(c => (c.id === id ? { ...c, title } : c)))
      }
    },
    []
  )

  const displayMessages = branches.viewingMessages ?? session.messages
  const messagesEmpty = displayMessages.length === 0

  // Gate III: callback for StreamingAnswer's marker parser.
  const handleMarkers = useCallback((m: {
    reasoning: ReasoningStepEvent[]
    sanskrit: SanskritTerm[]
    correction: CorrectionEvent | null
    outOfDomain: OutOfDomainEvent | null
    messageId: string | null
  }) => {
    // Reset state when assistant message id changes (new turn).
    if (m.messageId !== activeAssistantId) setActiveAssistantId(m.messageId)
    setReasoningSteps(m.reasoning)
    setSanskritTerms(m.sanskrit)
    if (m.correction) setCorrection(m.correction)
    if (m.outOfDomain) setOutOfDomain(m.outOfDomain)
    // NOTE: sanskritTerms intentionally NOT in deps and NOT read here.
    // It is SET here; reading it would create a circular setState→render→callback
    // dependency that causes an infinite render loop. Children receive sanskrit
    // terms via the StreamingAnswer parsed prop, not via this callback's state.
  }, [activeAssistantId])

  // Gate III: read context_usage / provenance / conversation_title from the
  // latest assistant message metadata.
  useEffect(() => {
    const msg = [...displayMessages].reverse().find(m => m.role === 'assistant')
    const meta = (msg?.metadata ?? {}) as Record<string, unknown>
    const usage = meta.context_usage as ContextUsageEvent | undefined
    const prov = meta.provenance as ProvenanceEvent | undefined
    const newTitle = meta.conversation_title as string | undefined
    const newConversationId = meta.conversationId as string | undefined
    // Sync state from streamed message metadata — this is the
    // external-system case (the assistant message's metadata payload arrives
    // over SSE), which is what the rule explicitly permits.
    /* eslint-disable react-hooks/set-state-in-effect */
    if (usage) setContextUsage(usage)
    if (prov) setProvenance(prov)
    if (newTitle && newConversationId) {
      setConversations(prev =>
        prev.map(c => (c.id === newConversationId ? { ...c, title: newTitle } : c)),
      )
    }
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [displayMessages])

  const lastAssistantMeta = useMemo(() => {
    const msg = [...displayMessages].reverse().find(m => m.role === 'assistant')
    const meta = msg?.metadata as Record<string, unknown> | undefined
    if (!meta) return null
    const modelId = meta.model as string | undefined
    const stackLabel = meta.stack as string | undefined
    if (!modelId) return stackLabel ?? null
    const synthesisM = getModelMeta(modelId)
    if (!synthesisM) return stackLabel ?? null
    const plannerId = (meta.planning_model_id as string | null | undefined) ?? null
    const plannerLatencyMs = (meta.planning_latency_ms as number | null | undefined) ?? null
    const plannerM = plannerId ? getModelMeta(plannerId) : null
    return `${synthesisM.label} · ${PROVIDER_LABEL[synthesisM.provider]}${
      plannerM ? `  •  Planner: ${plannerM.label}${plannerLatencyMs ? ` (${(plannerLatencyMs / 1000).toFixed(1)}s)` : ''}` : ''
    }`
  }, [displayMessages])

  const lastMessage = displayMessages[displayMessages.length - 1]
  const showPendingAssistant =
    session.isStreaming &&
    !branches.isViewingArchived &&
    lastMessage?.role === 'user'

  const sidebar = (
    <ConversationSidebar
      chartId={chartId}
      chartName={chartName}
      conversations={conversations}
      currentConversationId={currentConversationId}
      onClose={() => setMobileSidebarOpen(false)}
      onRenamed={(id, title) =>
        setConversations(prev => prev.map(c => (c.id === id ? { ...c, title } : c)))
      }
      onDeleted={id => setConversations(prev => prev.filter(c => c.id !== id))}
    />
  )

  const rightPanel =
    selectedDomain == null ? (
      <ReportLibrary
        reports={reports}
        selectedDomain={null}
        onSelect={d => setSelectedDomain(d)}
        view={reportView}
      />
    ) : (
      <ReportReader
        chartId={chartId}
        domain={selectedDomain}
        onBack={() => setSelectedDomain(null)}
      />
    )

  return (
    <div className="consume-shell flex h-full flex-1 min-h-0 flex-col">
      <ChatShell
        sidebar={sidebar}
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
          </div>
        }
        desktopSidebarCollapsed={desktopSidebarCollapsed}
        mobileSidebarOpen={mobileSidebarOpen}
        onToggleDesktopSidebar={() => setDesktopSidebarCollapsed(c => !c)}
        onToggleMobileSidebar={() => setMobileSidebarOpen(o => !o)}
        setMobileSidebarOpen={setMobileSidebarOpen}
        conversationId={session.conversationId}
        onRenameConversation={handleRenameConversation}
      >
        <div
          ref={scrollRef}
          role="log"
          aria-label="Conversation"
          aria-live="polite"
          className="relative flex-1 min-h-0 overflow-y-auto overflow-x-hidden [scrollbar-gutter:stable]"
        >
          {messagesEmpty ? (
            <EmptyState
              chartId={chartId}
              chartName={chartName}
              onPick={(text) => {
                composerRef.current?.setValue(text)
                composerRef.current?.focus()
              }}
            />
          ) : (
            <>
              {validatorFailures ? (
                <ValidatorFailureView
                  failures={validatorFailures}
                  onRetry={() => {
                    const lastUser = displayMessages.filter(m => m.role === 'user').at(-1)
                    const text = lastUser?.parts
                      ?.filter((p): p is { type: 'text'; text: string } => p.type === 'text')
                      .map(p => p.text)
                      .join('') ?? ''
                    if (text) {
                      composerRef.current?.setValue(text)
                      composerRef.current?.focus()
                    }
                  }}
                />
              ) : (
                <>
                  {/* Gate III: top-of-turn surfaces */}
                  {outOfDomain && (
                    <div className="mx-auto w-full max-w-4xl px-4 pt-3">
                      <OutOfDomainBanner event={outOfDomain} />
                    </div>
                  )}
                  {correction && (
                    <div className="mx-auto w-full max-w-4xl px-4">
                      <CorrectionNotice correction={correction} />
                    </div>
                  )}
                  {contextUsage && session.isStreaming && (
                    <div className="mx-auto w-full max-w-4xl px-4 pt-2">
                      <ContextUsageCue usage={contextUsage} />
                    </div>
                  )}
                  {session.isStreaming && (
                    <LiveReasoningCard reasoningSteps={reasoningSteps} isStreaming />
                  )}
                  <StreamingAnswer
                    messages={displayMessages}
                    isStreaming={session.isStreaming && !branches.isViewingArchived}
                    onStop={session.stop}
                    onRegenerate={branches.isViewingArchived ? undefined : handleRegenerate}
                    ratings={ratings}
                    onRate={branches.isViewingArchived ? undefined : rate}
                    onMarkers={handleMarkers}
                  />
                  {showPendingAssistant && <PendingAssistantBubble />}
                  {/* Gate III: after-answer provenance pills */}
                  {!session.isStreaming && provenance && (
                    <div className="mx-auto w-full max-w-4xl px-4 pb-4">
                      <PostAnswerProvenance provenance={provenance} />
                    </div>
                  )}
                </>
              )}
            </>
          )}
          <div ref={bottomRef} className="h-1" />
        </div>

        <div className="pointer-events-none absolute inset-x-0 bottom-[var(--composer-h)] z-20 flex justify-center">
          <ScrollToBottomButton
            visible={!isAtBottom && !messagesEmpty}
            onClick={() => scrollToBottom('smooth')}
          />
        </div>

        {session.error && !validatorFailures && (() => {
          const err = classifyChatError(session.error)
          if (!err) return null
          return (
            <div className="mx-auto w-full max-w-4xl px-4">
              <div
                role="alert"
                className="flex items-start justify-between gap-3 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{err.title}</p>
                  <p className="mt-0.5 text-destructive/80">{err.hint}</p>
                  {err.detail && (
                    <p className="mt-1 font-mono text-[10px] break-all opacity-60 select-all">
                      {err.detail.slice(0, 400)}
                    </p>
                  )}
                </div>
                {err.kind !== 'auth' && (
                  <button
                    type="button"
                    onClick={handleRegenerate}
                    className="shrink-0 rounded-md border border-destructive/40 px-2 py-0.5 text-[11px] hover:bg-destructive/20"
                  >
                    Retry
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => {
                    const msgs = session.messages
                    const lastAssistant = [...msgs].reverse().findIndex(m => m.role === 'assistant')
                    if (lastAssistant >= 0) {
                      session.setMessages(msgs.slice(0, msgs.length - lastAssistant))
                    } else {
                      session.setMessages([])
                    }
                  }}
                  className="shrink-0 text-destructive/50 hover:text-destructive text-[11px] leading-none"
                  aria-label="Dismiss error"
                >
                  ✕
                </button>
              </div>
            </div>
          )
        })()}

        <div ref={composerEl} className="relative shrink-0 border-t border-border/60 bg-background/80 backdrop-blur supports-backdrop-filter:bg-background/60 pb-[env(safe-area-inset-bottom)]">
          {branches.isViewingArchived && (
            <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-3 px-4 pt-2">
              <p className="text-xs text-muted-foreground">
                Viewing an earlier version of this conversation. Composer is disabled.
              </p>
              <button
                type="button"
                onClick={branches.returnToLive}
                className="inline-flex h-7 items-center gap-1 rounded-md border border-border px-2 text-xs font-medium text-foreground transition-colors hover:bg-muted"
              >
                Return to latest
              </button>
            </div>
          )}
          <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-2 px-4 py-1.5">
            <div className="flex items-center gap-1">
              <ModelStylePicker
                stack={stack}
                style={style}
                onStackChange={setStack}
                onStyleChange={setStyle}
                disabled={session.isStreaming || branches.isViewingArchived}
              />
              {lastAssistantMeta && (
                <span className="text-[10px] text-brand-gold/40 font-mono ml-1 hidden sm:inline">
                  {lastAssistantMeta}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setLelContextEnabled(v => !v)}
                aria-pressed={lelContextEnabled}
                title={
                  lelContextEnabled
                    ? 'Life events included in this query. Click to exclude them.'
                    : 'Life events excluded from this query. Click to include them.'
                }
                className={[
                  'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
                  lelContextEnabled
                    ? 'bg-[var(--brand-gold)]/15 text-[var(--brand-gold)] ring-1 ring-[var(--brand-gold)]/40 hover:bg-[var(--brand-gold)]/20'
                    : 'bg-muted/40 text-muted-foreground ring-1 ring-border hover:bg-muted/60',
                ].join(' ')}
              >
                {lelContextEnabled ? (
                  <><BookOpenText className="h-3.5 w-3.5" /><span>Life Events: On</span></>
                ) : (
                  <><BookOpen className="h-3.5 w-3.5" /><span>Life Events: Off</span></>
                )}
              </button>
              {(panelModeEnabled || initialAudienceTier === 'super_admin') && (
                <>
                {/* TierPicker — visible to super_admin role regardless of currently-viewed tier */}
                {initialAudienceTier === 'super_admin' && (
                  <TierPicker tier={activeTier} onChange={handleTierChange} />
                )}

                {panelModeEnabled && (
                  <label
                    htmlFor="panel-opt-in"
                    className={[
                      'inline-flex cursor-pointer select-none items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors',
                      panelOptIn
                        ? 'border-[rgba(var(--brand-gold-rgb),0.6)] bg-[var(--brand-gold-faint)] text-[var(--brand-gold)]'
                        : 'border-border text-muted-foreground hover:border-[rgba(var(--brand-gold-rgb),0.4)] hover:bg-[var(--brand-gold-faint)] hover:text-[var(--brand-gold)]',
                    ].join(' ')}
                    aria-label="Panel mode — run 3 independent models and adjudicate"
                  >
                    <Columns3 className="h-3 w-3" />
                    Panel
                    <input
                      type="checkbox"
                      id="panel-opt-in"
                      checked={panelOptIn}
                      onChange={e => setPanelOptIn(e.target.checked)}
                      className="sr-only"
                    />
                  </label>
                )}

                {/* Trace — opens drawer instead of inline panel */}
                {activeTier === 'super_admin' && (
                  <button
                    type="button"
                    onClick={() => setTraceDrawerOpen(o => !o)}
                    className={[
                      'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors',
                      traceDrawerOpen
                        ? 'border-[rgba(var(--status-warn-rgb),0.6)] bg-[var(--status-warn-bg)] text-[var(--status-warn)] hover:bg-[var(--status-warn-bg)]'
                        : 'border-border text-muted-foreground hover:border-[rgba(var(--status-warn-rgb),0.4)] hover:bg-[var(--status-warn-bg)] hover:text-[var(--status-warn)]',
                    ].join(' ')}
                    aria-label="Toggle query trace drawer"
                  >
                    <Zap className="h-3 w-3" />
                    Trace
                  </button>
                )}
                </>
              )}
            </div>
          </div>
          {!lelContextEnabled && (
            <div className="mx-4 mb-2 flex items-center gap-2 rounded-md bg-[oklch(0.11_0.010_70)] px-3 py-2 text-xs text-[#fce29a]/85 ring-1 ring-[var(--brand-gold)]/15">
              <Info className="h-3.5 w-3.5 text-[var(--brand-gold)]/70" />
              <span>Life events excluded from this query.</span>
            </div>
          )}
          <Composer
            ref={composerRef}
            onSubmit={handleSend}
            onStop={session.stop}
            isStreaming={session.isStreaming}
            disabled={branches.isViewingArchived}
            placeholder={messagesEmpty ? 'Ask about career, finance, timing…' : 'Reply…'}
            attachments={attachmentsApi.attachments}
            onAddFiles={attachmentsApi.addFiles}
            onRemoveAttachment={attachmentsApi.remove}
            attachmentsReady={attachmentsApi.canSend}
          />
        </div>
      </ChatShell>
      <ShortcutsDialog open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} commands={paletteCommands} />

      {/* TraceDrawer replaces always-on TracePanel */}
      <TraceDrawer
        queryId={session.currentQueryId ?? null}
        open={traceDrawerOpen && activeTier === 'super_admin'}
        onOpenChange={setTraceDrawerOpen}
      />
      {/* Gate III: conversation history overlay drawer */}
      <ConversationHistoryDrawer
        chartId={chartId}
        open={historyDrawerOpen}
        onOpenChange={setHistoryDrawerOpen}
        initialConversations={conversations.map(c => ({
          id: c.id,
          title: c.title,
          created_at: c.created_at,
        }))}
        currentConversationId={currentConversationId}
      />
    </div>
  )
}
