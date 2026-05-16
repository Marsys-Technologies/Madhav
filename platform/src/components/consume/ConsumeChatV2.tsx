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
import type { PanelMemberPart, PanelMetaPart, PredictionCandidatePart } from '@/lib/streams/data_parts'

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
  const rendered = useMemo(() => {
    const parts = renderWithCitations(text, onPin)
    const count = parts.filter(p => typeof p !== 'string').length
    onCitationCount?.(count)
    return parts
  }, [text, onPin, onCitationCount])
  return (
    <p className="whitespace-pre-wrap font-sans text-sm text-zinc-200 leading-relaxed" data-testid="v2-message-text">
      {rendered}
    </p>
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
      className="group flex w-full max-w-3xl mx-auto flex-col gap-1 px-4 py-3"
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

          {/* γ4: validator hard-fail band (above message body) */}
          {citationGate?.status === 'fail' && (
            <ValidatorFailureBand
              issues={citationGate.issues ?? []}
              isSuperAdmin={isSuperAdmin}
              onOpenDetails={() => setDetailsOpen(true)}
            />
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

          {/* Reload (regenerate) + Details + Copy actions for assistant messages */}
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1"
              data-testid="v2-assistant-action-bar"
            >
              <ActionBarPrimitive.Reload asChild>
                <button
                  type="button"
                  className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Regenerate response"
                  data-testid="v2-regenerate-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3 w-3">
                    <path d="M13.5 4A6 6 0 1 0 14 9" strokeLinecap="round" />
                    <path d="M11 1l2.5 3L11 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </ActionBarPrimitive.Reload>

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
      className="mx-auto max-w-3xl flex flex-wrap gap-2 pb-2"
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
        className="border-t border-zinc-800 bg-zinc-950 px-4 py-3"
        data-testid="v2-composer"
      >
        {interruptToast && (
          <div
            className="mb-2 text-center text-xs text-amber-400"
            data-testid="v2-interrupt-toast"
            aria-live="polite"
          >
            Cancelled — sending new query
          </div>
        )}

        {/* β5: attachment strip above the input */}
        <AttachmentStrip attachments={attachments} onRemove={removeAttachment} />

        <div className="mx-auto max-w-3xl flex items-end gap-3">
          {/* β5: hidden file input + attach button */}
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
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex h-11 w-11 md:h-10 md:w-10 shrink-0 items-center justify-center rounded-xl border border-zinc-700 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            title="Attach image or PDF"
            aria-label="Attach image or PDF file"
            data-testid="v2-attach-btn"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden="true">
              <path d="M13.5 9.5L7.5 15.5a4 4 0 0 1-5.66-5.66L9.18 2.5a2.5 2.5 0 0 1 3.54 3.54L6.5 11.9A1 1 0 0 1 5.09 10.5l5.5-5.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <ComposerPrimitive.Input
            className="flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-base md:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-colors"
            placeholder="Ask about the chart…"
            rows={3}
            data-testid="v2-composer-input"
            onPaste={handlePaste}
            aria-label="Message input"
            aria-multiline="true"
          />
          <div className="flex flex-col gap-2 pb-0.5">
            {isRunning ? (
              <>
                <ComposerPrimitive.Cancel asChild>
                  <button
                    type="button"
                    className="flex h-11 w-11 md:h-10 md:w-10 items-center justify-center rounded-xl bg-zinc-700 text-zinc-300 hover:bg-zinc-600 transition-colors"
                    title="Stop generation"
                    aria-label="Stop generating response"
                    data-testid="v2-abort-btn"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4" aria-hidden="true">
                      <rect x="4" y="4" width="8" height="8" rx="1" />
                    </svg>
                  </button>
                </ComposerPrimitive.Cancel>
                <button
                  type="button"
                  onClick={handleInterruptSend}
                  className="flex h-11 w-11 md:h-10 md:w-10 items-center justify-center rounded-xl bg-indigo-700 text-white hover:bg-indigo-600 transition-colors"
                  title="Cancel and send new query"
                  aria-label="Cancel current response and send new query"
                  data-testid="v2-interrupt-send-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4" aria-hidden="true">
                    <path d="M8 1L15 8L8 15M15 8H1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </>
            ) : (
              <ComposerPrimitive.Send asChild>
                <button
                  type="submit"
                  className="flex h-11 w-11 md:h-10 md:w-10 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 transition-colors"
                  aria-label="Send message"
                  data-testid="v2-send-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4" aria-hidden="true">
                    <path d="M8 1L15 8L8 15M15 8H1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </ComposerPrimitive.Send>
            )}
          </div>
        </div>
      </ComposerPrimitive.Root>
    </div>
  )
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

// ─── Thread ───────────────────────────────────────────────────────────────────

function V2Thread() {
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
          <div
            className="flex h-full flex-col items-center justify-center gap-3 text-center px-4 py-16"
            data-testid="v2-thread-empty"
          >
            <p className="text-sm font-medium text-zinc-200">Ready</p>
            <p className="text-xs text-zinc-500">Chat V2 — assistant-ui</p>
          </div>
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

      <V2Composer />
    </ThreadPrimitive.Root>
  )
}

// ─── ConsumeChatV2 ────────────────────────────────────────────────────────────

/**
 * β2: Thread with conversation list sidebar + write-through restore on mount.
 * Accepts the same props as ConsumeChatLegacy for API compatibility.
 */
export function ConsumeChatV2({ chartId, chartName, chartMeta, costVisibilityEnabled }: ConsumeChatProps) {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | undefined>(undefined)
  const [restoredKey, setRestoredKey] = useState(0)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

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

  return (
    <CostVisibilityCtx.Provider value={costVisibilityEnabled ?? false}>
    <div
      className="relative flex h-dvh bg-zinc-950 text-zinc-100"
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
          collapsed=true  → hidden on mobile (md: shows the w-10 strip)
          collapsed=false → fixed overlay on mobile (md: in-flow) */}
      <div
        className={
          sidebarCollapsed
            ? 'hidden md:flex'
            : 'fixed inset-y-0 left-0 z-40 flex md:relative md:inset-auto'
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
          {/* Mobile-only hamburger to open sidebar */}
          <button
            type="button"
            onClick={() => setSidebarCollapsed(false)}
            className="flex md:hidden h-8 w-8 min-h-[44px] min-w-[44px] items-center justify-center rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            aria-label="Open conversations"
            data-testid="v2-mobile-sidebar-open"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4" aria-hidden="true">
              <path d="M2 4h12M2 8h7M2 12h9" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
            </svg>
          </button>
          <span className="text-xs font-mono text-violet-400 bg-violet-400/10 px-2 py-0.5 rounded border border-violet-400/20">
            V2
          </span>
          <h1 className="text-sm font-semibold text-zinc-100 truncate" data-testid="v2-chart-name">
            {chartName}
          </h1>
          {chartMeta && (
            <span className="hidden sm:block text-xs text-zinc-500 truncate" data-testid="v2-chart-meta">
              {chartMeta}
            </span>
          )}
        </header>

        <main className="flex-1 overflow-hidden">
          <V2ChatRuntime
            key={restoredKey}
            chartId={chartId}
            conversationId={activeConversationId}
            initialMessages={initialMessages}
          />
        </main>
      </div>
    </div>
    </CostVisibilityCtx.Provider>
  )
}

// ─── Runtime mount (isolated so key reset remounts cleanly) ──────────────────

interface V2ChatRuntimeProps {
  chartId: string
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

function V2ChatRuntime({ chartId, conversationId, initialMessages }: V2ChatRuntimeProps) {
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
        }
      },
    }),
    messages: initialMessages,
  })


  return (
    <CitationCtx.Provider value={citationCtxValue}>
      <AttachmentCtx.Provider value={attachmentManager}>
        <AssistantRuntimeProvider runtime={runtime}>
          {/* γ7: track session-storage pending-stream entry for stream-resume */}
          <V2StreamResumeTracker chartId={chartId} conversationId={conversationId} />
          <div className="flex h-full overflow-hidden">
            <V2Thread />
            <CitationSidePanel
              citations={pinnedCitations}
              pinned={pinnedSet}
              onUnpin={handleUnpin}
            />
          </div>
        </AssistantRuntimeProvider>
      </AttachmentCtx.Provider>
    </CitationCtx.Provider>
  )
}
