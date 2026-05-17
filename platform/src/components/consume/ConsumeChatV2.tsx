'use client'

/**
 * ConsumeChatV2 — assistant-ui shell for MARSYS chat.
 *
 * β2: conversation list sidebar + write-through restore on mount.
 * β5: multi-modal file attachments (image + PDF) via upload → token flow.
 * Flag gate: only rendered when MARSYS_FLAG_CHAT_V2_ENABLED=true.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '@assistant-ui/react-ai-sdk'
import { DefaultChatTransport } from 'ai'
import type { UIMessage } from 'ai'
import { PanelLeft, Paperclip, Square, ArrowUp, PlusCircle, Keyboard } from 'lucide-react'
import { ShareButton } from '@/components/chat/ShareButton'
import { TraceDrawer } from '@/components/consume/TraceDrawer'
import { CommandPalette } from '@/components/chat/CommandPalette'
import type { Command } from '@/components/chat/CommandPalette'
import { ShortcutsDialog } from '@/components/chat/ShortcutsDialog'
import { ModelStylePicker } from '@/components/chat/ModelStylePicker'
import type { StyleId } from '@/components/chat/ModelStylePicker'
import { TierPicker } from '@/components/consume/TierPicker'
import { useChatPreferences } from '@/hooks/useChatPreferences'
import type { AudienceTier } from '@/lib/prompts/types'
import type { ModelStack } from '@/lib/models/registry'
import {
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  ActionBarPrimitive,
  BranchPickerPrimitive,
  useThreadRuntime,
  useMessage,
} from '@assistant-ui/react'
import type { ConsumeChatProps } from './ConsumeChatLegacy'
import { EmptyState } from './EmptyState'
import { MarkdownContent } from '../chat/MarkdownContent'
import { NumberedCitation } from '../chat/NumberedCitation'
import { CitationSidePanel } from '../chat/CitationSidePanel'
import type { CitationPart } from '@/lib/citations/citation_data_part'
import { PerMessageDetailsDrawer } from '../chat/PerMessageDetailsDrawer'
import { PanelConfidenceRibbon } from '../chat/PanelConfidenceRibbon'
import { PanelDissentTabs } from '../chat/PanelDissentTabs'
import { ReasoningProgress } from '../chat/ReasoningProgress'
import { PredictionLogModal } from '../chat/PredictionLogModal'
import { ValidatorFailureBand } from '../chat/ValidatorFailureBand'
import { ValidatorFooterChip } from '../chat/ValidatorFooterChip'
import type { PanelMemberPart, PanelMetaPart, PredictionCandidatePart, StagePart, ToolPart } from '@/lib/streams/data_parts'
import { StageStepper } from '../chat-v2/StageStepper'
import { ToolCallCard } from '../chat-v2/ToolCallCard'
import { PanelModeToggle, PanelOptInCtx } from '../chat-v2/PanelModeToggle'
import { ContextUsageCue } from './ContextUsageCue'
import { PostAnswerProvenance } from './PostAnswerProvenance'
import type { ContextUsageEvent, ProvenanceEvent } from '@/types/sse_events'

// ─── Upload / attachment types ────────────────────────────────────────────────

export interface AttachedFile {
  /** UUID token returned by /api/uploads/sign and stored by /api/uploads/store */
  token: string
  filename: string
  contentType: string
  size: number
  /** Object URL for local preview (revoked on unmount) */
  previewUrl: string | null
  status: 'uploading' | 'ready' | 'error'
  errorMsg?: string
}

const ACCEPT_TYPES = 'image/jpeg,image/png,image/gif,image/webp,application/pdf'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConversationSummary {
  id: string
  title: string | null
  created_at: string
  updated_at: string | null
  archived_at: string | null
}

// ─── Conversation sidebar ─────────────────────────────────────────────────────

interface ConversationSidebarProps {
  chartId: string
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  collapsed: boolean
  onToggle: () => void
}

function ConversationSidebar({
  chartId,
  activeId,
  onSelect,
  onNew,
  collapsed,
  onToggle,
}: ConversationSidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(false)

  const reload = useCallback(() => {
    setLoading(true)
    fetch(`/api/conversations?chartId=${encodeURIComponent(chartId)}&module=consume`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data?.conversations)) {
          setConversations(data.conversations as ConversationSummary[])
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [chartId])

  useEffect(() => {
    reload()
  }, [reload])

  if (collapsed) {
    return (
      <div className="flex flex-col items-center w-10 border-r border-zinc-800 bg-zinc-950 shrink-0">
        <button
          type="button"
          onClick={onToggle}
          title="Expand conversation list"
          className="mt-3 flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
          data-testid="v2-sidebar-expand"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
            <path d="M2 4h12M2 8h7M2 12h9" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    )
  }

  return (
    <aside
      className="flex flex-col w-56 shrink-0 border-r border-zinc-800 bg-zinc-950"
      data-testid="v2-conversation-sidebar"
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">Conversations</span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onNew}
            title="New conversation"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-new-conversation"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
              <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
            </svg>
          </button>
          <button
            type="button"
            onClick={onToggle}
            title="Collapse"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-sidebar-collapse"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
              <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-1">
        {loading && conversations.length === 0 && (
          <p className="px-3 py-2 text-xs text-zinc-500">Loading…</p>
        )}
        {conversations.map((conv) => (
          <button
            key={conv.id}
            type="button"
            onClick={() => onSelect(conv.id)}
            className={`w-full text-left px-3 py-2 text-xs rounded-md transition-colors truncate ${
              conv.id === activeId
                ? 'bg-indigo-600/20 text-indigo-300'
                : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
            }`}
            data-testid={`v2-conversation-item-${conv.id}`}
          >
            {conv.title ?? 'Untitled'}
          </button>
        ))}
        {!loading && conversations.length === 0 && (
          <p className="px-3 py-4 text-xs text-zinc-600 text-center">No conversations yet</p>
        )}
      </div>
    </aside>
  )
}

// ─── Branch picker (inline navigation between alternates) ────────────────────

function V2BranchPicker() {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className="flex items-center gap-1 text-xs text-zinc-500"
      data-testid="v2-branch-picker"
    >
      <BranchPickerPrimitive.Previous asChild>
        <button
          type="button"
          className="h-5 w-5 flex items-center justify-center rounded hover:bg-zinc-800 hover:text-zinc-300 transition-colors disabled:opacity-30"
          title="Previous branch"
          data-testid="v2-branch-prev"
        >
          ‹
        </button>
      </BranchPickerPrimitive.Previous>
      <span>
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <button
          type="button"
          className="h-5 w-5 flex items-center justify-center rounded hover:bg-zinc-800 hover:text-zinc-300 transition-colors disabled:opacity-30"
          title="Next branch"
          data-testid="v2-branch-next"
        >
          ›
        </button>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  )
}

// ─── Cost visibility context (γ6) ────────────────────────────────────────────

const CostVisibilityCtx = createContext<boolean>(false)

// ─── Conversation ID context (B.3: threads conversationId into V2Message for regenerate) ──
const ConversationIdCtx = createContext<string | null>(null)

// ─── Latest query-id callback context (C.2: V2QueryIdTracker → ConsumeChatV2 header) ──
const V2QueryIdCb = createContext<((id: string) => void) | null>(null)

// ─── Preferences context (C.3: bottom-bar selectors share state with API body) ──
interface V2PrefsCtxValue {
  stack: ModelStack
  style: StyleId
  lelEnabled: boolean
  activeTier: AudienceTier
  audienceTier: AudienceTier
  setStack: (s: ModelStack) => void
  setStyle: (s: StyleId) => void
  setLelEnabled: (v: boolean) => void
  setActiveTier: (t: AudienceTier) => void
}
const V2PrefsCtx = createContext<V2PrefsCtxValue>({
  stack: 'gemini-2.5-flash' as ModelStack,
  style: 'acharya',
  lelEnabled: true,
  activeTier: 'client',
  audienceTier: 'client',
  setStack: () => {},
  setStyle: () => {},
  setLelEnabled: () => {},
  setActiveTier: () => {},
})

// ─── Citation context ─────────────────────────────────────────────────────────

interface CitationContextValue {
  onPin: (n: number, signalId: string) => void
}
const CitationCtx = createContext<CitationContextValue>({ onPin: () => {} })

function renderWithCitations(
  text: string,
  onPin: (n: number, signalId: string) => void,
): (string | React.ReactElement)[] {
  const pattern = /SIG\.MSR\.\d{3}(?!\d)/g
  const parts: (string | React.ReactElement)[] = []
  const seen: string[] = []
  function getN(id: string): number {
    const i = seen.indexOf(id)
    if (i >= 0) return i + 1
    seen.push(id)
    return seen.length
  }
  let lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index))
    const sigId = match[0]
    const n = getN(sigId)
    parts.push(<NumberedCitation key={`${sigId}-${match.index}`} n={n} signalId={sigId} onPin={onPin} />)
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex))
  return parts
}

interface V2AssistantTextProps { text: string; onCitationCount?: (n: number) => void }

function V2AssistantText({ text, onCitationCount }: V2AssistantTextProps) {
  const { onPin } = useContext(CitationCtx)
  const message = useMessage()
  const isStreaming = message.status?.type === 'running'

  // D.1: extract citation chips (NumberedCitation elements) for footer rendering.
  // MarkdownContent only accepts string children, so chips render below the text.
  const citationChips = useMemo(() => {
    const parts = renderWithCitations(text, onPin)
    return parts.filter((p): p is React.ReactElement => typeof p !== 'string')
  }, [text, onPin])

  useEffect(() => {
    onCitationCount?.(citationChips.length)
  }, [citationChips.length, onCitationCount])

  return (
    <div>
      <MarkdownContent
        streaming={isStreaming}
        className="text-sm text-zinc-200"
        data-testid="v2-message-text"
      >
        {text}
      </MarkdownContent>
      {citationChips.length > 0 && !isStreaming && (
        <div className="mt-2 flex flex-wrap gap-1.5" data-testid="v2-citation-chips">
          {citationChips}
        </div>
      )}
    </div>
  )
}

// ─── Panel data extraction helpers ───────────────────────────────────────────

function usePanelData(dataParts: ReadonlyArray<unknown>) {
  const panelMembers = useMemo(() => {
    const parts: PanelMemberPart[] = []
    for (const d of dataParts) {
      if (
        typeof d === 'object' && d !== null &&
        (d as Record<string, unknown>).type === 'data-panel-member'
      ) {
        const entry = d as { type: string; data: unknown }
        parts.push(entry.data as PanelMemberPart)
      }
    }
    // Sort by member_index for stable tab order
    parts.sort((a, b) => a.member_index - b.member_index)
    return parts
  }, [dataParts])

  const panelMeta = useMemo((): PanelMetaPart | null => {
    const entry = dataParts.find(
      (d): d is { type: string; data: PanelMetaPart } =>
        typeof d === 'object' && d !== null &&
        (d as Record<string, unknown>).type === 'data-panel-meta',
    )
    return entry ? (entry as { type: string; data: PanelMetaPart }).data : null
  }, [dataParts])

  return { panelMembers, panelMeta, isPanel: panelMeta !== null }
}

// ─── Regenerate button (B.3 fix) ─────────────────────────────────────────────
// Calls /api/chat/consume/regenerate to truncate conversation_messages before
// letting assistant-ui reload — prevents dead turns accumulating on regenerate.

function V2RegenerateButton() {
  const message = useMessage()
  const runtime = useThreadRuntime()
  const conversationId = useContext(ConversationIdCtx)

  // Fire truncation before assistant-ui's Reload handler executes.
  // Slot merges onClick handlers: child fires first, then Reload's handler.
  // Truncation is intentionally fire-and-forget: fast DB DELETE; synthesis
  // won't finish before truncation completes.
  const handleClick = useCallback(() => {
    if (!conversationId) return
    const messages = runtime.getState().messages
    const myIndex = messages.findIndex((m) => m.id === message.id)
    const parentId = myIndex > 0 ? messages[myIndex - 1].id : null
    if (!parentId) return
    void fetch('/api/chat/consume/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: conversationId, parent_message_id: parentId }),
    }).catch(() => {})
  }, [message.id, runtime, conversationId])

  return (
    <ActionBarPrimitive.Reload asChild>
      <button
        type="button"
        onClick={handleClick}
        className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
        title="Regenerate response"
        data-testid="v2-regenerate-btn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3 w-3" aria-hidden="true">
          <path d="M13.5 4A6 6 0 1 0 14 9" strokeLinecap="round" />
          <path d="M11 1l2.5 3L11 7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </ActionBarPrimitive.Reload>
  )
}

// ─── Message ─────────────────────────────────────────────────────────────────

function V2Message() {
  // β6: details drawer state lives per-message (mounted inside MessagePrimitive.Root
  // so useMessage() is valid for the PerMessageDetailsDrawer).
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [citationCount, setCitationCount] = useState(0)
  const [showDissent, setShowDissent] = useState(false)
  // γ3: prediction log modal state
  const [predModalOpen, setPredModalOpen] = useState(false)
  const [activePredCandidate, setActivePredCandidate] = useState<PredictionCandidatePart | null>(null)

  // γ1: panel data from message metadata
  const message = useMessage()
  const dataParts = (message.metadata?.unstable_data ?? []) as ReadonlyArray<unknown>
  const { panelMembers, panelMeta, isPanel } = usePanelData(dataParts)
  const meta = (message.metadata?.custom ?? {}) as Record<string, unknown>
  const isSuperAdmin = meta.disclosure_tier === 'super_admin'

  // C.8: extract context_usage (from messageMetadata.start) and provenance (from finish or custom)
  const rawMeta = message.metadata as Record<string, unknown> | undefined
  const contextUsage = (rawMeta?.context_usage ?? meta.context_usage) as ContextUsageEvent | undefined ?? null
  const provenance = (meta.provenance ?? rawMeta?.provenance) as ProvenanceEvent | null ?? null

  // γ6: cost visibility from context (super_admin always sees cost regardless)
  const costVisible = useContext(CostVisibilityCtx)

  // γ4: extract citation gate status from data parts
  const citationGate = useMemo(() => {
    const entry = dataParts.find(
      (d): d is { type: string; data: { status?: string; issues?: string[] } } =>
        typeof d === 'object' && d !== null &&
        (d as Record<string, unknown>).type === 'data-citation-gate',
    )
    return entry ? (entry as { type: string; data: { status?: string; issues?: string[] } }).data : null
  }, [dataParts])

  // O3: compute isStreaming for stage/tool gating
  const isStreaming = message.status?.type === 'running'

  // O3: extract stage parts (latest per stage name — stage can transition running→done)
  const stageHistory = useMemo(() => {
    const map = new Map<string, StagePart>()
    for (const d of dataParts) {
      if (
        typeof d === 'object' && d !== null &&
        (d as Record<string, unknown>).type === 'data-stage'
      ) {
        const entry = d as { type: string; data: StagePart }
        map.set(entry.data.stage, entry.data)
      }
    }
    return Array.from(map.values())
  }, [dataParts])

  // O3: extract tool parts (latest per tool name)
  const toolHistory = useMemo(() => {
    const map = new Map<string, ToolPart>()
    for (const d of dataParts) {
      if (
        typeof d === 'object' && d !== null &&
        (d as Record<string, unknown>).type === 'data-tool'
      ) {
        const entry = d as { type: string; data: ToolPart }
        map.set(entry.data.name, entry.data)
      }
    }
    return Array.from(map.values())
  }, [dataParts])

  // γ3: extract prediction candidates from data parts
  const predictionCandidates = useMemo(() => {
    return dataParts
      .filter(
        (d): d is { type: string; data: PredictionCandidatePart } =>
          typeof d === 'object' && d !== null &&
          (d as Record<string, unknown>).type === 'data-prediction-candidate',
      )
      .map(d => d.data)
      .sort((a, b) => b.score - a.score)
  }, [dataParts])

  const handleCitationCount = useCallback((n: number) => {
    setCitationCount(n)
  }, [])

  return (
    <MessagePrimitive.Root
      className="group flex w-full max-w-4xl mx-auto flex-col gap-1 px-4 py-3"
      data-testid="v2-message"
    >
      <MessagePrimitive.If user>
        <div className="flex flex-col items-end gap-1">
          <div
            className="rounded-2xl bg-indigo-600 px-4 py-2.5 text-sm text-white max-w-[70%]"
            data-testid="v2-user-message"
          >
            {/* F.2: flat props — renderer receives {text,...} directly, not a nested part object */}
            <MessagePrimitive.Parts components={{ Text: (props) => <span>{props.text}</span> }} />
          </div>

          {/* Edit action + branch picker for user messages */}
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1"
              data-testid="v2-user-action-bar"
            >
              <ActionBarPrimitive.Edit asChild>
                <button
                  type="button"
                  className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Edit message"
                  data-testid="v2-edit-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3">
                    <path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13H2v-3L11.5 2.5z" />
                  </svg>
                </button>
              </ActionBarPrimitive.Edit>
            </ActionBarPrimitive.Root>
          </div>
        </div>
      </MessagePrimitive.If>

      <MessagePrimitive.If assistant>
        <div className="flex flex-col gap-2 w-full" data-testid="v2-assistant-message">
          {/* γ1: panel confidence ribbon (only for panel-mode messages) */}
          {isPanel && panelMeta && (
            <PanelConfidenceRibbon
              memberCount={panelMeta.member_count}
              hasDivergence={panelMeta.has_divergence}
              showDissent={showDissent}
              onToggleDissent={() => setShowDissent((s) => !s)}
              isSuperAdmin={isSuperAdmin}
            />
          )}

          {/* C.8: context usage cue — compact chip showing how many prior turns were used */}
          {contextUsage && <ContextUsageCue usage={contextUsage} />}

          {/* γ4: validator hard-fail band (above message body) */}
          {citationGate?.status === 'fail' && (
            <ValidatorFailureBand
              issues={citationGate.issues ?? []}
              isSuperAdmin={isSuperAdmin}
              onOpenDetails={() => setDetailsOpen(true)}
            />
          )}

          {/* O3: stage stepper — linear pipeline progress above streaming text */}
          {isStreaming && stageHistory.length > 0 && (
            <StageStepper stages={stageHistory} />
          )}

          {/* O3: tool call cards — per-tool fetch status */}
          {isStreaming && toolHistory.length > 0 && (
            <div className="flex flex-col gap-1 py-1" data-testid="v2-tool-cards">
              {toolHistory.map((tool) => (
                <ToolCallCard key={tool.name} tool={tool} />
              ))}
            </div>
          )}

          <MessagePrimitive.Parts
            components={{
              // γ2: ReasoningProgress with live token count + elapsed timer + auto-collapse >2k tokens
              // F.2: props.text is the accumulated reasoning text (flat prop, not props.reasoning)
              Reasoning: (props) => <ReasoningProgress text={props.text} />,
              Text: (props) => <V2AssistantText text={props.text} onCitationCount={handleCitationCount} />,
            }}
          />

          {/* γ4: validator soft-fail chip (below message body) */}
          {citationGate?.status === 'warn' && (
            <ValidatorFooterChip
              issues={citationGate.issues ?? []}
              isSuperAdmin={isSuperAdmin}
              onOpenDetails={() => setDetailsOpen(true)}
            />
          )}

          {/* γ1: panel dissent tabs (collapsible, gated on toggle) */}
          {isPanel && showDissent && panelMembers.length > 0 && (
            <PanelDissentTabs
              members={panelMembers}
              isSuperAdmin={isSuperAdmin}
            />
          )}

          {/* γ3: prediction candidate affordances (end-of-message, super_admin only) */}
          {isSuperAdmin && predictionCandidates.length > 0 && (
            <div
              className="flex flex-wrap gap-2 pt-1"
              data-testid="v2-prediction-candidates"
            >
              {predictionCandidates.slice(0, 3).map((candidate, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => {
                    setActivePredCandidate(candidate)
                    setPredModalOpen(true)
                  }}
                  className="flex items-center gap-1 rounded-full border border-violet-500/30 bg-violet-900/20 px-2.5 py-0.5 text-[10px] text-violet-300 hover:bg-violet-900/40 transition-colors"
                  title={candidate.text}
                  data-testid={`v2-log-prediction-${i}`}
                >
                  📋 Log as prediction
                  {candidate.horizon && (
                    <span className="opacity-70">{candidate.horizon}</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* C.8: post-answer provenance — model/source/signal counts with drawer */}
          {provenance && <PostAnswerProvenance provenance={provenance} />}

          {/* Reload (regenerate) + Details + Copy actions for assistant messages */}
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1"
              data-testid="v2-assistant-action-bar"
            >
              <V2RegenerateButton />

              {/* β6: Show details drawer */}
              <button
                type="button"
                onClick={() => setDetailsOpen(true)}
                className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                title="Show message details"
                data-testid="v2-details-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3 w-3">
                  <circle cx="8" cy="8" r="6" />
                  <path d="M8 7v4M8 5h.01" strokeLinecap="round" />
                </svg>
              </button>

              <ActionBarPrimitive.Copy asChild>
                <button
                  type="button"
                  className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Copy response"
                  data-testid="v2-copy-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3">
                    <rect x="5" y="5" width="8" height="9" rx="1" />
                    <path d="M3 2h7a1 1 0 0 1 1 1v1H3V2z" />
                  </svg>
                </button>
              </ActionBarPrimitive.Copy>
            </ActionBarPrimitive.Root>
          </div>
        </div>

        {/* β6: Details drawer — rendered inside MessagePrimitive.Root so useMessage() works */}
        <PerMessageDetailsDrawer
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          citationCount={citationCount}
          costVisible={costVisible}
        />

        {/* γ3: prediction log modal */}
        {activePredCandidate && (
          <PredictionLogModal
            open={predModalOpen}
            onClose={() => {
              setPredModalOpen(false)
              setActivePredCandidate(null)
            }}
            queryId={(meta.queryId as string) ?? ''}
            conversationId={null}
            predictionText={activePredCandidate.text}
            horizon={activePredCandidate.horizon}
          />
        )}
      </MessagePrimitive.If>
    </MessagePrimitive.Root>
  )
}

// ─── Attachment context (shared between Composer + V2ChatRuntime) ────────────

interface AttachmentContextValue {
  attachments: AttachedFile[]
  addAttachment: (file: File) => void
  removeAttachment: (token: string) => void
  clearAttachments: () => void
}
const AttachmentCtx = createContext<AttachmentContextValue>({
  attachments: [],
  addAttachment: () => {},
  removeAttachment: () => {},
  clearAttachments: () => {},
})

function useAttachmentManager() {
  const [attachments, setAttachments] = useState<AttachedFile[]>([])
  const previewUrls = useRef<string[]>([])

  // Revoke object URLs on unmount
  useEffect(() => {
    return () => {
      for (const url of previewUrls.current) URL.revokeObjectURL(url)
    }
  }, [])

  const addAttachment = useCallback(async (file: File) => {
    const tempToken = `pending-${crypto.randomUUID()}`
    const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    if (previewUrl) previewUrls.current.push(previewUrl)

    const pending: AttachedFile = {
      token: tempToken,
      filename: file.name,
      contentType: file.type,
      size: file.size,
      previewUrl,
      status: 'uploading',
    }
    setAttachments(prev => [...prev, pending])

    try {
      // Step 1: get upload token + URL
      const signRes = await fetch('/api/uploads/sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, contentType: file.type, size: file.size }),
      })
      if (!signRes.ok) {
        const err = await signRes.json().catch(() => ({})) as { error?: string }
        throw new Error(err.error ?? `Sign failed: ${signRes.status}`)
      }
      const { token, uploadUrl } = await signRes.json() as { token: string; uploadUrl: string }

      // Step 2: upload bytes
      const putRes = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': file.type,
          'x-filename': encodeURIComponent(file.name),
        },
        body: file,
      })
      if (!putRes.ok) {
        const err = await putRes.json().catch(() => ({})) as { error?: string }
        throw new Error(err.error ?? `Upload failed: ${putRes.status}`)
      }

      // Replace pending entry with real token
      setAttachments(prev =>
        prev.map(a =>
          a.token === tempToken
            ? { ...a, token, status: 'ready' }
            : a,
        ),
      )
    } catch (e) {
      setAttachments(prev =>
        prev.map(a =>
          a.token === tempToken
            ? { ...a, status: 'error', errorMsg: e instanceof Error ? e.message : 'Upload failed' }
            : a,
        ),
      )
    }
  }, [])

  const removeAttachment = useCallback((token: string) => {
    setAttachments(prev => {
      const entry = prev.find(a => a.token === token)
      if (entry?.previewUrl) URL.revokeObjectURL(entry.previewUrl)
      return prev.filter(a => a.token !== token)
    })
  }, [])

  const clearAttachments = useCallback(() => {
    setAttachments(prev => {
      for (const a of prev) if (a.previewUrl) URL.revokeObjectURL(a.previewUrl)
      return []
    })
  }, [])

  return { attachments, addAttachment, removeAttachment, clearAttachments }
}

// ─── Attachment strip (above composer) ───────────────────────────────────────

function AttachmentStrip({
  attachments,
  onRemove,
}: {
  attachments: AttachedFile[]
  onRemove: (token: string) => void
}) {
  if (attachments.length === 0) return null
  return (
    <div
      className="mx-auto max-w-4xl flex flex-wrap gap-2 pb-2"
      data-testid="v2-attachment-strip"
    >
      {attachments.map((a) => (
        <div
          key={a.token}
          className={`relative flex items-center gap-2 rounded-lg border px-2 py-1.5 text-xs ${
            a.status === 'error'
              ? 'border-red-500/40 bg-red-900/20 text-red-400'
              : a.status === 'uploading'
                ? 'border-zinc-700 bg-zinc-800/60 text-zinc-400 animate-pulse'
                : 'border-zinc-700 bg-zinc-800 text-zinc-300'
          }`}
          data-testid={`v2-attachment-${a.token}`}
        >
          {a.previewUrl ? (
            // Image thumbnail
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={a.previewUrl}
              alt={a.filename}
              className="h-8 w-8 rounded object-cover shrink-0"
              data-testid="v2-attachment-preview-img"
            />
          ) : (
            // PDF icon
            <div
              className="flex h-8 w-8 items-center justify-center rounded bg-zinc-700 shrink-0 text-[9px] font-bold text-zinc-400"
              data-testid="v2-attachment-pdf-icon"
            >
              PDF
            </div>
          )}
          <div className="flex flex-col min-w-0">
            <span className="truncate max-w-[120px]" title={a.filename}>
              {a.filename}
            </span>
            {a.status === 'error' && (
              <span className="text-[10px] text-red-400 truncate max-w-[120px]">
                {a.errorMsg}
              </span>
            )}
            {a.status === 'uploading' && (
              <span className="text-[10px] text-zinc-500">Uploading…</span>
            )}
          </div>
          <button
            type="button"
            onClick={() => onRemove(a.token)}
            className="ml-1 flex h-4 w-4 items-center justify-center rounded-full text-zinc-500 hover:bg-zinc-700 hover:text-zinc-300 transition-colors shrink-0"
            title="Remove attachment"
            data-testid={`v2-attachment-remove-${a.token}`}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}

// ─── Composer ─────────────────────────────────────────────────────────────────

function V2Composer() {
  // F.3: useThreadRuntime().subscribe() for run-state (deprecated primitive avoided)
  const runtime = useThreadRuntime()
  const [isRunning, setIsRunning] = useState(false)
  const [interruptToast, setInterruptToast] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const isRunningRef = useRef(false)
  const pendingResubmit = useRef(false)

  const { attachments, addAttachment, removeAttachment } = useContext(AttachmentCtx)

  useEffect(() => {
    const unsub = runtime.subscribe(() => {
      const running = runtime.getState().isRunning
      const wasRunning = isRunningRef.current
      isRunningRef.current = running
      setIsRunning(running)

      // β3: When run ends with a pending interrupt-send, resubmit after 300ms.
      if (wasRunning && !running && pendingResubmit.current) {
        pendingResubmit.current = false
        setTimeout(() => {
          setInterruptToast(false)
          const form = containerRef.current?.querySelector('form')
          form?.requestSubmit()
        }, 300)
      }
    })
    return unsub
  }, [runtime])

  function handleInterruptSend() {
    pendingResubmit.current = true
    setInterruptToast(true)
    runtime.cancelRun()
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    for (const f of files) addAttachment(f)
    // Reset input so the same file can be re-selected after removal
    e.target.value = ''
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    for (const f of files) addAttachment(f)
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
  }

  // Handle paste (images only — paste event carries DataTransfer items)
  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const items = Array.from(e.clipboardData.items)
    const imageItems = items.filter(i => i.kind === 'file' && i.type.startsWith('image/'))
    for (const item of imageItems) {
      const file = item.getAsFile()
      if (file) addAttachment(file)
    }
  }

  return (
    <div
      ref={containerRef}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      <ComposerPrimitive.Root
        className="px-4 pb-3 pt-1"
        data-testid="v2-composer"
      >
        {interruptToast && (
          <div
            className="mx-auto max-w-4xl mb-2 text-center text-xs text-amber-400"
            data-testid="v2-interrupt-toast"
            aria-live="polite"
          >
            Cancelled — sending new query
          </div>
        )}

        {/* β5: hidden file input (inside form, outside pill) */}
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT_TYPES}
          multiple
          className="sr-only"
          aria-label="Attach file"
          onChange={handleFileChange}
          data-testid="v2-file-input"
        />

        {/* C.4: brand pill wrapper — paperclip + textarea + hints + send inside the pill */}
        <div className="mx-auto max-w-4xl">
          <div className="relative flex flex-col rounded-3xl border border-[rgba(var(--brand-gold-rgb),0.35)] bg-background shadow-sm transition-all duration-200">
            {/* β5: attachment strip inside pill top */}
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 px-4 pt-3">
                <AttachmentStrip attachments={attachments} onRemove={removeAttachment} />
              </div>
            )}

            <ComposerPrimitive.Input
              className="w-full resize-none overflow-y-auto rounded-3xl bg-transparent px-5 py-4 text-[15px] leading-[1.55] text-zinc-100 placeholder-zinc-500 focus:outline-none"
              placeholder="Ask about the chart…"
              rows={3}
              data-testid="v2-composer-input"
              onPaste={handlePaste}
              aria-label="Message input"
              aria-multiline="true"
            />

            {/* Bottom row inside pill: paperclip + hints | send/stop */}
            <div className="flex items-center justify-between gap-2 px-3 pb-3 pt-0.5">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full text-zinc-500 transition-all hover:bg-zinc-800 hover:text-zinc-300"
                  title="Attach image or PDF"
                  aria-label="Attach image or PDF file"
                  data-testid="v2-attach-btn"
                >
                  <Paperclip className="h-4 w-4" aria-hidden="true" />
                </button>
                <span className="hidden md:inline pl-1 text-[10px] uppercase tracking-[0.18em] text-zinc-600">
                  ↵ Send · ⇧↵ New line
                </span>
              </div>

              <div className="flex items-center gap-1">
                {isRunning ? (
                  <>
                    <ComposerPrimitive.Cancel asChild>
                      <button
                        type="button"
                        className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-zinc-100 text-zinc-900 transition-all hover:opacity-80"
                        title="Stop generation"
                        aria-label="Stop generating response"
                        data-testid="v2-abort-btn"
                      >
                        <Square className="h-3.5 w-3.5 fill-current" aria-hidden="true" />
                      </button>
                    </ComposerPrimitive.Cancel>
                    <button
                      type="button"
                      onClick={handleInterruptSend}
                      className="brand-cta inline-flex h-9 w-9 items-center justify-center rounded-full transition-all active:scale-95"
                      title="Cancel and send new query"
                      aria-label="Cancel current response and send new query"
                      data-testid="v2-interrupt-send-btn"
                    >
                      <ArrowUp className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </>
                ) : (
                  <ComposerPrimitive.Send asChild>
                    <button
                      type="submit"
                      className="brand-cta inline-flex h-9 w-9 items-center justify-center rounded-full transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40 active:scale-95"
                      aria-label="Send message"
                      data-testid="v2-send-btn"
                    >
                      <ArrowUp className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </ComposerPrimitive.Send>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* O2: panel mode toggle — below pill */}
        <div className="mx-auto max-w-4xl flex items-center pt-1.5" data-testid="v2-composer-options">
          <PanelModeToggle />
        </div>
      </ComposerPrimitive.Root>
    </div>
  )
}

// ─── C.2: Query-id tracker ────────────────────────────────────────────────────
// Mounted inside AssistantRuntimeProvider; subscribes to messages and surfaces
// the most recent query_id into V2QueryIdCtx for the TraceDrawer.

function V2QueryIdTracker() {
  const runtime = useThreadRuntime()
  const onQueryId = useContext(V2QueryIdCb)

  useEffect(() => {
    if (!onQueryId) return
    const unsub = runtime.subscribe(() => {
      const state = runtime.getState()
      const messages = state.messages
      for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i]
        if (msg.role !== 'assistant') continue
        const custom = (msg.metadata as { custom?: { queryId?: string } } | undefined)?.custom
        if (custom?.queryId) { onQueryId(custom.queryId); return }
        const data = (msg.metadata as unknown as { unstable_data?: ReadonlyArray<unknown> } | undefined)?.unstable_data ?? []
        for (const part of data) {
          const p = part as { query_id?: string }
          if (p.query_id) { onQueryId(p.query_id); return }
        }
      }
    })
    return unsub
  }, [runtime, onQueryId])

  return null
}

// ─── γ7: Stream-resume tracker ────────────────────────────────────────────────
// Mounted inside AssistantRuntimeProvider so it can use useThreadRuntime().
// Saves queryId + received char count to sessionStorage while a stream is live;
// clears the entry when the stream ends normally.

function V2StreamResumeTracker({ chartId, conversationId }: { chartId: string; conversationId: string | null }) {
  const runtime = useThreadRuntime()
  const conversationIdRef = useRef(conversationId)
  conversationIdRef.current = conversationId

  useEffect(() => {
    const key = pendingStreamKey(chartId)
    const unsub = runtime.subscribe(() => {
      const state = runtime.getState()
      const isRunning = state.isRunning
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const lastMsg = (state as any).messages?.at?.(-1) as UIMessage | undefined

      if (isRunning && lastMsg?.role === 'assistant') {
        const meta = lastMsg.metadata as Record<string, unknown> | undefined
        const custom = meta?.custom as Record<string, unknown> | undefined
        const queryId = custom?.queryId as string | undefined
        if (queryId) {
          const text = lastMsg.parts
            .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
            .map(p => p.text)
            .join('')
          const entry: PendingStreamEntry = {
            queryId,
            conversationId: conversationIdRef.current,
            receivedChars: text.length,
          }
          try { sessionStorage.setItem(key, JSON.stringify(entry)) } catch { /* SSR/private */ }
        }
      }

      if (!isRunning) {
        try { sessionStorage.removeItem(key) } catch { /* SSR/private */ }
      }
    })
    return unsub
  }, [runtime, chartId])

  return null
}

// ─── C.3: Bottom-bar selectors ───────────────────────────────────────────────

function V2BottomBar() {
  const { stack, style, lelEnabled, activeTier, audienceTier, setStack, setStyle, setLelEnabled, setActiveTier } =
    useContext(V2PrefsCtx)

  return (
    <div
      className="mx-auto max-w-4xl w-full px-4 py-1 flex flex-wrap items-center gap-2 border-b border-zinc-800"
      data-testid="v2-bottom-bar"
    >
      <ModelStylePicker
        stack={stack}
        style={style}
        onStackChange={setStack}
        onStyleChange={setStyle}
      />
      <button
        type="button"
        aria-pressed={lelEnabled}
        onClick={() => setLelEnabled(!lelEnabled)}
        className={`flex items-center gap-1 px-2.5 py-1 text-[11px] rounded-md border transition-colors ${
          lelEnabled
            ? 'border-[rgba(var(--brand-gold-rgb),0.35)] text-[rgba(var(--brand-gold-rgb),0.80)] bg-[rgba(var(--brand-gold-rgb),0.06)]'
            : 'border-zinc-700 text-zinc-500 bg-transparent'
        }`}
        data-testid="v2-lel-toggle"
        title={lelEnabled ? 'Life Events context enabled' : 'Life Events context disabled'}
      >
        Life Events: {lelEnabled ? 'On' : 'Off'}
      </button>
      {audienceTier === 'super_admin' && (
        <TierPicker tier={activeTier} onChange={setActiveTier} />
      )}
    </div>
  )
}

// ─── Thread ───────────────────────────────────────────────────────────────────

function V2Thread({ chartId, chartName }: { chartId: string; chartName: string }) {
  return (
    <ThreadPrimitive.Root
      className="flex h-full flex-col"
      data-testid="v2-thread-root"
    >
      {/* γ8: live region announces new assistant messages to screen readers */}
      <ThreadPrimitive.Viewport
        className="flex-1 overflow-y-auto scroll-smooth py-4"
        data-testid="v2-thread-viewport"
        // γ8: role=log is the semantic landmark for a chat message log.
        // aria-live=polite ensures new messages are announced without interrupting.
        role="log"
        aria-live="polite"
        aria-atomic="false"
        aria-label="Conversation messages"
      >
        <ThreadPrimitive.Empty>
          <EmptyState
            chartId={chartId}
            chartName={chartName}
            className="h-full"
            data-testid="v2-thread-empty"
          />
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages components={{ Message: V2Message }} />

        <ThreadPrimitive.ScrollToBottom asChild>
          <button
            type="button"
            className="fixed bottom-24 right-6 flex h-8 w-8 items-center justify-center rounded-full bg-zinc-700 text-zinc-300 shadow-lg hover:bg-zinc-600 transition-all opacity-80 hover:opacity-100"
            data-testid="v2-scroll-to-bottom"
            aria-label="Scroll to bottom"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4" aria-hidden="true">
              <path d="M8 12L2 6h12l-6 6z" />
            </svg>
          </button>
        </ThreadPrimitive.ScrollToBottom>
      </ThreadPrimitive.Viewport>

      <V2BottomBar />
      <V2Composer />
    </ThreadPrimitive.Root>
  )
}

// ─── ConsumeChatV2 ────────────────────────────────────────────────────────────

/**
 * β2: Thread with conversation list sidebar + write-through restore on mount.
 * Accepts the same props as ConsumeChatLegacy for API compatibility.
 */
export function ConsumeChatV2({ chartId, chartName, chartMeta, costVisibilityEnabled, audienceTier = 'client' }: ConsumeChatProps) {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | undefined>(undefined)
  const [restoredKey, setRestoredKey] = useState(0)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [traceOpen, setTraceOpen] = useState(false)
  const [latestQueryId, setLatestQueryId] = useState<string | null>(null)
  const { stack, style, lelEnabled, setStack, setStyle, setLelEnabled } = useChatPreferences(chartId)
  const [activeTier, setActiveTier] = useState<AudienceTier>(audienceTier)

  const prefsCtxValue = useMemo<V2PrefsCtxValue>(() => ({
    stack, style, lelEnabled, activeTier, audienceTier,
    setStack, setStyle, setLelEnabled, setActiveTier,
  }), [stack, style, lelEnabled, activeTier, audienceTier, setStack, setStyle, setLelEnabled])

  const [paletteOpen, setPaletteOpen] = useState(false)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setPaletteOpen(o => !o)
        return
      }
      if (!isInput && (e.key === '?' || ((e.metaKey || e.ctrlKey) && e.key === '/'))) {
        e.preventDefault()
        setShortcutsOpen(o => !o)
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  const chartIdRef = useRef(chartId)
  chartIdRef.current = chartId

  // γ7: On mount, check sessionStorage for an in-progress stream from a prior page load.
  // If found, call the resume endpoint and restore the partial message.
  useEffect(() => {
    const key = pendingStreamKey(chartId)
    let entry: PendingStreamEntry | null = null
    try {
      const raw = sessionStorage.getItem(key)
      if (raw) entry = JSON.parse(raw) as PendingStreamEntry
    } catch { /* SSR/private-mode */ }

    if (!entry?.queryId) return

    const { queryId, receivedChars } = entry
    const params = new URLSearchParams({ query_id: queryId })
    if (receivedChars > 0) params.set('since_chars', String(receivedChars))

    fetch(`/api/chat/consume/resume?${params}`)
      .then(async (r) => {
        if (r.status === 404 || r.status === 204) {
          // Stream completed + β2 persisted, or nothing to resume. Fall through
          // to normal conversation restore. Clear the stale sessionStorage entry.
          try { sessionStorage.removeItem(key) } catch { /* ok */ }
          return
        }
        if (!r.ok) return
        const data = await r.json() as { text: string; query_id: string }
        if (!data.text) return
        // Reconstruct the partial response as a UIMessage so the runtime renders it.
        const recoveredMsg: UIMessage = {
          id: `resumed-${data.query_id.slice(0, 8)}`,
          role: 'assistant',
          parts: [{ type: 'text', text: `${data.text}\n\n_(Stream interrupted — showing recovered partial response.)_` }],
          metadata: { custom: { queryId: data.query_id, recovered: true } },
        }
        setInitialMessages([recoveredMsg])
        setRestoredKey((k) => k + 1)
        try { sessionStorage.removeItem(key) } catch { /* ok */ }
      })
      .catch(() => {
        try { sessionStorage.removeItem(key) } catch { /* ok */ }
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartId]) // Mount only — chartId is stable within a page load

  // Restore conversation messages on conversation switch.
  const handleSelectConversation = useCallback(async (id: string) => {
    setActiveConversationId(id)
    try {
      const r = await fetch(`/api/conversations/${id}/messages`)
      if (r.ok) {
        const data = await r.json() as { messages: UIMessage[] }
        setInitialMessages(data.messages ?? [])
      } else {
        setInitialMessages([])
      }
    } catch {
      setInitialMessages([])
    }
    // Increment key to remount the runtime with restored messages.
    setRestoredKey((k) => k + 1)
  }, [])

  const handleNewConversation = useCallback(() => {
    setActiveConversationId(null)
    setInitialMessages(undefined)
    setRestoredKey((k) => k + 1)
  }, [])

  const v2Commands = useMemo<Command[]>(() => [
    {
      id: 'new-chat',
      label: 'New conversation',
      hint: '⌘ ⇧ O',
      icon: PlusCircle,
      keywords: 'new chat conversation',
      run: () => { handleNewConversation(); setPaletteOpen(false) },
    },
    {
      id: 'toggle-sidebar',
      label: 'Toggle sidebar',
      hint: '⌘ B',
      icon: PanelLeft,
      keywords: 'sidebar conversations toggle',
      run: () => { setSidebarCollapsed(c => !c); setPaletteOpen(false) },
    },
    {
      id: 'shortcuts',
      label: 'Show keyboard shortcuts',
      hint: '⌘ /',
      icon: Keyboard,
      keywords: 'shortcuts keyboard help',
      run: () => { setPaletteOpen(false); setShortcutsOpen(true) },
    },
  ], [handleNewConversation])

  return (
    <CostVisibilityCtx.Provider value={costVisibilityEnabled ?? false}>
    <V2PrefsCtx.Provider value={prefsCtxValue}>
    <div
      className="relative flex h-dvh text-zinc-100"
      data-testid="consume-chat-v2-root"
    >
      {/* Mobile sidebar backdrop — visible only when sidebar is open on small screens */}
      {!sidebarCollapsed && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setSidebarCollapsed(true)}
          aria-hidden="true"
          data-testid="v2-mobile-sidebar-backdrop"
        />
      )}

      {/* Sidebar wrapper:
          Always fixed/overlay so it never steals width from the chat column.
          collapsed=true  → hidden on mobile; fixed thin strip on md+
          collapsed=false → fixed slide-over on all viewports */}
      <div
        className={
          sidebarCollapsed
            ? 'hidden md:fixed md:inset-y-0 md:left-0 md:z-40 md:flex'
            : 'fixed inset-y-0 left-0 z-40 flex'
        }
      >
        <ConversationSidebar
          chartId={chartId}
          activeId={activeConversationId}
          onSelect={handleSelectConversation}
          onNew={handleNewConversation}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed((c) => !c)}
        />
      </div>

      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <header
          className="flex items-center gap-3 border-b border-zinc-800 px-4 md:px-6 py-3 shrink-0"
          data-testid="v2-header"
        >
              {/* Mobile: open sidebar */}
          <button
            type="button"
            onClick={() => setSidebarCollapsed(false)}
            className="flex md:hidden h-8 w-8 min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors"
            aria-label="Open conversations"
            data-testid="v2-mobile-sidebar-open"
          >
            <PanelLeft className="h-4 w-4" aria-hidden="true" />
          </button>
          {/* Desktop: toggle sidebar */}
          <button
            type="button"
            onClick={() => setSidebarCollapsed(c => !c)}
            className="hidden md:flex h-8 w-8 items-center justify-center rounded-md text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors"
            aria-label="Toggle conversations"
            data-testid="v2-desktop-sidebar-toggle"
          >
            <PanelLeft className="h-4 w-4" aria-hidden="true" />
          </button>

          {/* Brand title + meta */}
          <div className="min-w-0 flex-1 px-1.5">
            <span
              role="heading"
              aria-level={1}
              className="truncate font-serif text-[15px] font-medium text-foreground leading-tight block"
              data-testid="v2-chart-name"
            >
              {chartName}
            </span>
            {chartMeta && (
              <span
                className="truncate text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)] leading-none block mt-0.5"
                data-testid="v2-chart-meta"
              >
                {chartMeta}
              </span>
            )}
          </div>

          {/* Right-side actions: Share + Trace (super_admin only) */}
          <div className="flex shrink-0 items-center gap-1" data-testid="v2-header-actions">
            <ShareButton conversationId={activeConversationId ?? undefined} />
            {audienceTier === 'super_admin' && (
              <button
                type="button"
                onClick={() => setTraceOpen(true)}
                className="flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium text-[color-mix(in_oklch,var(--brand-gold-cream)_60%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors"
                aria-label="View query trace"
                data-testid="v2-trace-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3.5 w-3.5" aria-hidden="true">
                  <circle cx="8" cy="8" r="5" /><path d="M8 5v3l2 2" strokeLinecap="round" />
                </svg>
                Trace
              </button>
            )}
          </div>
        </header>

        {/* TraceDrawer — outside header but inside main column */}
        <TraceDrawer queryId={latestQueryId} open={traceOpen} onOpenChange={setTraceOpen} />

        <main className="flex-1 overflow-hidden">
          <V2ChatRuntime
            key={restoredKey}
            chartId={chartId}
            chartName={chartName}
            conversationId={activeConversationId}
            initialMessages={initialMessages}
            onQueryId={setLatestQueryId}
          />
        </main>
      </div>
    </div>

    {/* C.7: command palette + shortcuts dialog — mounted at tree top, portalled to body */}
    <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} commands={v2Commands} />
    <ShortcutsDialog open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
    </V2PrefsCtx.Provider>
    </CostVisibilityCtx.Provider>
  )
}

// ─── Runtime mount (isolated so key reset remounts cleanly) ──────────────────

interface V2ChatRuntimeProps {
  chartId: string
  chartName: string
  conversationId: string | null
  initialMessages: UIMessage[] | undefined
}

// ─── γ7: Session-storage key for stream-resume ───────────────────────────────

function pendingStreamKey(chartId: string) {
  return `v2_pending_${chartId}`
}

interface PendingStreamEntry {
  queryId: string
  conversationId: string | null
  receivedChars: number
}

function V2ChatRuntime({ chartId, chartName, conversationId, initialMessages, onQueryId }: V2ChatRuntimeProps & { onQueryId?: (id: string) => void }) {
  const chartIdRef = useRef(chartId)
  chartIdRef.current = chartId
  const conversationIdRef = useRef(conversationId)
  conversationIdRef.current = conversationId

  // β4: Pinned citations state
  const [pinnedCitations, setPinnedCitations] = useState<CitationPart[]>([])
  const pinnedSet = useMemo(() => new Set(pinnedCitations.map(c => c.index)), [pinnedCitations])

  const handlePin = useCallback((n: number, signalId: string) => {
    setPinnedCitations(prev => {
      if (prev.some(c => c.index === n)) return prev
      return [...prev, { type: 'citation' as const, index: n, signal_id: signalId, layer: 'L2.5' as const, snippet: '' }]
    })
  }, [])

  const handleUnpin = useCallback((n: number) => {
    setPinnedCitations(prev => prev.filter(c => c.index !== n))
  }, [])

  const citationCtxValue = useMemo(() => ({ onPin: handlePin }), [handlePin])

  // β5: attachment manager — tokens injected into each request body
  const attachmentManager = useAttachmentManager()
  const attachmentsRef = useRef(attachmentManager.attachments)
  attachmentsRef.current = attachmentManager.attachments

  // O2: panel mode opt-in — persists in sessionStorage per conversation
  const panelStorageKey = conversationId ? `v2_panel_opt_in_${conversationId}` : 'v2_panel_opt_in_new'
  const [panelOptIn, setPanelOptInRaw] = useState(() => {
    try { return sessionStorage.getItem(panelStorageKey) === 'true' } catch { return false }
  })
  const panelOptInRef = useRef(panelOptIn)
  panelOptInRef.current = panelOptIn

  const setPanelOptIn = useCallback((v: boolean) => {
    setPanelOptInRaw(v)
    try { sessionStorage.setItem(panelStorageKey, String(v)) } catch { /* SSR/private */ }
  }, [panelStorageKey])

  const panelOptInCtxValue = useMemo(() => ({ panelOptIn, setPanelOptIn }), [panelOptIn, setPanelOptIn])

  const { stack, style, lelEnabled } = useContext(V2PrefsCtx)
  const stackRef = useRef(stack)
  stackRef.current = stack
  const styleRef = useRef(style)
  styleRef.current = style
  const lelEnabledRef = useRef(lelEnabled)
  lelEnabledRef.current = lelEnabled

  const runtime = useChatRuntime({
    transport: new DefaultChatTransport({
      api: '/api/chat/consume',
      body: () => {
        // β5: include ready attachment tokens in the request body, then clear
        const readyAttachments = attachmentsRef.current
          .filter(a => a.status === 'ready')
          .map(a => ({ token: a.token, filename: a.filename, contentType: a.contentType }))

        if (readyAttachments.length > 0) {
          // Clear after capturing so the next message starts fresh
          attachmentManager.clearAttachments()
        }

        return {
          chartId: chartIdRef.current,
          ...(conversationIdRef.current ? { conversationId: conversationIdRef.current } : {}),
          ...(readyAttachments.length > 0 ? { attachments: readyAttachments } : {}),
          ...(panelOptInRef.current ? { panel_opt_in: true } : {}),
          stack: stackRef.current,
          style: styleRef.current,
          lel_context_enabled: lelEnabledRef.current,
        }
      },
    }),
    messages: initialMessages,
  })


  return (
    <V2QueryIdCb.Provider value={onQueryId ?? null}>
    <PanelOptInCtx.Provider value={panelOptInCtxValue}>
    <ConversationIdCtx.Provider value={conversationId}>
    <CitationCtx.Provider value={citationCtxValue}>
      <AttachmentCtx.Provider value={attachmentManager}>
        <AssistantRuntimeProvider runtime={runtime}>
          {/* γ7: track session-storage pending-stream entry for stream-resume */}
          <V2StreamResumeTracker chartId={chartId} conversationId={conversationId} />
          {/* C.2: surface latest query_id to parent via callback */}
          <V2QueryIdTracker />
          <div className="flex h-full overflow-hidden">
            <V2Thread chartId={chartId} chartName={chartName} />
            <CitationSidePanel
              citations={pinnedCitations}
              pinned={pinnedSet}
              onUnpin={handleUnpin}
            />
          </div>
        </AssistantRuntimeProvider>
      </AttachmentCtx.Provider>
    </CitationCtx.Provider>
    </ConversationIdCtx.Provider>
    </PanelOptInCtx.Provider>
    </V2QueryIdCb.Provider>
  )
}
