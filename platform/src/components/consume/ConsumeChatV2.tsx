'use client'

/**
 * ConsumeChatV2 — assistant-ui shell for MARSYS chat.
 *
 * β2: conversation list sidebar + write-through restore on mount.
 * β5: multi-modal file attachments (image + PDF) via upload → token flow.
 * Post-§M.16 (2026-05-18): sole chat shell — flag + legacy path removed.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '@assistant-ui/react-ai-sdk'
import { DefaultChatTransport } from 'ai'
import type { UIMessage } from 'ai'
import { PanelLeft, Paperclip, Square, ArrowUp, PlusCircle, Keyboard, Pencil, RotateCcw, Info, Copy, Loader2, ArrowLeft, Camera } from 'lucide-react'
import Link from 'next/link'
import { ShareButton } from '@/components/chat/ShareButton'
import { StillWorkingIndicator } from '@/components/chat/StillWorkingIndicator'
import { HeaderSkeleton } from '@/components/chat/HeaderSkeleton'
import { ScrollToBottomButton } from '@/components/chat/ScrollToBottomButton'
import { useScrollDiscipline } from '@/hooks/useScrollDiscipline'
import { TraceDrawer } from '@/components/consume/TraceDrawer'
import { ConsumeReportLibraryV2 } from '@/components/consume/ConsumeReportLibraryV2'
import { ConversationSidebarV2 } from '@/components/consume/ConversationSidebarV2'
import { CommandPalette } from '@/components/chat/CommandPalette'
import type { Command } from '@/lib/chat-commands'
import { COMMANDS } from '@/lib/chat-commands'
import { SlashCommandMenu } from '@/components/chat/SlashCommandMenu'
import { ShortcutsDialog } from '@/components/chat/ShortcutsDialog'
import { ModelStylePicker } from '@/components/chat/ModelStylePicker'
import type { StyleId } from '@/components/chat/ModelStylePicker'
import { useChatPreferences, useLastPrompt, useTextScale, TEXT_SCALES } from '@/hooks/useChatPreferences'
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
  useMessageRuntime,
} from '@assistant-ui/react'
interface ConversationRow {
  id: string
  title: string | null
  created_at: string
  chart_id: string
  user_id: string
  module: ConversationModule
}

/**
 * WS-1-S3-B: Capability gate state passed from the server component.
 *
 * 'no-build'     — no pyramid layers exist; chart has never been built.
 *                  Render a full-screen block with a link back to the cockpit.
 * 'l1-building'  — L1 (Gaṇita / Chart Facts) is in progress.
 *                  Render a dismissible amber banner; chat is still usable but
 *                  hints that grounded tools are not yet available.
 * 'ready'        — L1 (or better) is built; chat is fully grounded.
 *                  No banner; capabilities list is passed for informational use.
 */
export type CapabilityGateState =
  | { state: 'no-build'; cockpitHref: string }
  | { state: 'l1-building'; cockpitHref: string }
  | { state: 'ready'; capabilities: string[] }

export interface ConsumeChatProps {
  chartId: string
  chartName: string
  chartMeta?: string
  reports: Report[]
  conversations: ConversationRow[]
  currentConversationId?: string
  initialMessages?: UIMessage[]
  panelModeEnabled?: boolean
  audienceTier?: AudienceTier
  /** γ6: show per-message cost to non-admin users. Super-admin always sees cost. */
  costVisibilityEnabled?: boolean
  /** R8-S6: enable inline slash command menu in composer */
  slashEnabled?: boolean
  /** R8-S7: enable conversation export dropdown in header */
  exportEnabled?: boolean
  /** R8-S5: enable token count display in composer */
  tokensEnabled?: boolean
  /**
   * WS-1-S3-B: Capability gate state from the server component.
   * When omitted, no gate is applied (backwards-compatible default).
   */
  capabilityGateState?: CapabilityGateState
}
import { EmptyState } from './EmptyState'
import { MarkdownContent } from '../chat/MarkdownContent'
import { NumberedCitation } from '../chat/NumberedCitation'
import { CodeBlock } from '../chat/CodeBlock'
// B-S7: side panel deleted — inline citation parity; NumberedCitation is the sole citation surface.
import { PerMessageDetailsDrawer } from '../chat/PerMessageDetailsDrawer'
import { PanelConfidenceRibbon } from '../chat/PanelConfidenceRibbon'
import { PanelDissentTabs } from '../chat/PanelDissentTabs'
import { ReasoningProgress } from '../chat/ReasoningProgress'
import { PredictionLogModal } from '../chat/PredictionLogModal'
import { ValidatorFailureBand } from '../chat/ValidatorFailureBand'
import { ValidatorFooterChip } from '../chat/ValidatorFooterChip'
import type { PanelMemberPart, PanelMetaPart, PredictionCandidatePart, StagePart, ToolPart } from '@/lib/streams/data_parts'
import { useDataParts } from '@/lib/chat-v2/useDataParts'
import { InlineToolFlow } from '../chat/InlineToolFlow'
import { ExportDropdown } from '../chat/ExportDropdown'
import { useTokenCount } from '@/hooks/useTokenCount'
import type { NormalizedDataPart } from '@/lib/chat-v2/useDataParts'
import { StageStepper } from '../chat-v2/StageStepper'
import { ToolCallCard } from '../chat-v2/ToolCallCard'
import { PanelModeToggle, PanelOptInCtx } from '../chat-v2/PanelModeToggle'
import { ContextUsageCue } from './ContextUsageCue'
import { PostAnswerProvenance } from './PostAnswerProvenance'
import { CorrectionNotice } from './CorrectionNotice'
import { OutOfDomainBanner } from './OutOfDomainBanner'
import type { ContextUsageEvent, ProvenanceEvent } from '@/types/sse_events'
import { AnimatePresence, motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { SettingsDropdown } from './SettingsDropdown'
import { useMultiProviderParity } from '@/lib/chat-v2/useMultiProviderParity'

// R11.B — Look-and-Feel umbrella flag (NEXT_PUBLIC, build-time)
const R11B_LOOK_AND_FEEL_ENV =
  typeof process !== 'undefined' &&
  process.env.NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL === 'true'
import type { Report, ConversationModule } from '@/lib/db/types'

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

// ─── Y-S5: Truncated-message context (stop-and-edit while streaming) ─────────
const TruncatedMsgCtx = createContext<string | null>(null)
const SetTruncatedMsgCtx = createContext<((id: string | null) => void) | null>(null)

// ─── Conversation ID context (B.3: threads conversationId into V2Message for regenerate) ──
const ConversationIdCtx = createContext<string | null>(null)

// ─── Latest query-id callback context (C.2: V2QueryIdTracker → ConsumeChatV2 header) ──
const V2QueryIdCb = createContext<((id: string) => void) | null>(null)

// ─── Conversation-id callback context (W5 fix: V2ConversationIdTracker → ConsumeChatV2) ──
// Reads data-persistence parts to propagate conversation_id after the first turn so that
// the regenerate button and subsequent request bodies carry the correct conversation ID.
const V2ConversationIdCb = createContext<((id: string) => void) | null>(null)

// ─── Title callback context (E.1: V2TitleTracker → ConsumeChatV2 sidebar reload) ──
// Fires once on the first turn when a data-title part lands, triggering sidebar refresh.
const V2TitleCb = createContext<(() => void) | null>(null)

// ─── Preferences context (C.3: bottom-bar selectors share state with API body) ──
interface V2PrefsCtxValue {
  stack: ModelStack
  style: StyleId
  lelEnabled: boolean
  activeTier: AudienceTier
  /** READ-ONLY: server-provided audience tier from chart_meta. The in-chat override is `activeTier` + `setActiveTierOverride`. */
  audienceTier: AudienceTier
  /** R9-S3: Active persona ID; null means no persona selected. */
  activePersonaId: string | null
  setStack: (s: ModelStack) => void
  setStyle: (s: StyleId) => void
  setLelEnabled: (v: boolean) => void
  setActiveTierOverride: (t: AudienceTier) => void
  setActivePersonaId: (id: string | null) => void
}
const V2PrefsCtx = createContext<V2PrefsCtxValue>({
  stack: 'gemini-2.5-flash' as ModelStack,
  style: 'acharya',
  lelEnabled: true,
  activeTier: 'client',
  audienceTier: 'client',
  activePersonaId: null,
  setStack: () => {},
  setStyle: () => {},
  setLelEnabled: () => {},
  setActiveTierOverride: () => {},
  setActivePersonaId: () => {},
})

// ─── B-S7: Citation side panel retired ───────────────────────────────────────
// Citations are now inline-only via NumberedCitation. No side panel, no ctx.
// onPin back-compat in NumberedCitation maps to onActivate.

/** Pre-process LLM response text before markdown rendering.
 *
 *  Primary path (new prompt format):
 *    bare SIG.MSR.NNN → inline CITE badge marker
 *
 *  Defence-in-depth for legacy / prompt-drift:
 *    custom sanskrit markup tags → bare inner term
 *    (→ id1, id2, ...) wrappers  → badges for MSR ids, rest dropped
 *
 *  Returns processed text and unique MSR citation count. */
function preprocessCitations(text: string): { processedText: string; count: number } {
  const seen: string[] = []
  function badge(sigId: string): string {
    let i = seen.indexOf(sigId)
    if (i < 0) { seen.push(sigId); i = seen.length - 1 }
    return `\`CITE:${i + 1}:${sigId}\``
  }

  // Defence-in-depth: strip custom markup tags (prompt-drift safety net).
  let result = text.replace(/‹sanskrit[^›]*›([\s\S]*?)‹\/sanskrit›/g, '$1')

  // Defence-in-depth: collapse (→ ...) wrappers — extract MSR signals, drop others.
  result = result.replace(/\(→\s*([^)]*)\)/g, (_match, contents: string) => {
    const signals = [...contents.matchAll(/SIG\.MSR\.(\d{3})(?!\d)/g)].map(m => `SIG.MSR.${m[1]}`)
    return signals.length > 0 ? signals.map(badge).join(' ') : ''
  })

  // Primary: replace bare SIG.MSR.NNN with inline CITE badge markers.
  // Negative lookbehind skips IDs already wrapped by step 2 (CITE:N: prefix).
  result = result.replace(/(?<!CITE:\d+:)SIG\.MSR\.\d{3}(?!\d)/g, badge)

  return { processedText: result, count: seen.length }
}

export { preprocessCitations }


interface V2AssistantTextProps { text: string; onCitationCount?: (n: number) => void }

function V2AssistantText({ text, onCitationCount }: V2AssistantTextProps) {
  const message = useMessage()
  const isStreaming = message.status?.type === 'running'
  const dataParts = useDataParts(message)
  // C.3: build signal_id → {snippet, layer, confidence} map from data-citation parts.
  const citationRichMap = useMemo(() => {
    const result = new Map<string, { snippet: string; layer: 'L1' | 'L2.5'; confidence: number | undefined }>()
    for (const d of dataParts) {
      if (d.type === 'data-citation') {
        const data = d.data as Record<string, unknown>
        if (typeof data.signal_id === 'string') {
          result.set(data.signal_id, {
            snippet: typeof data.snippet === 'string' ? data.snippet : '',
            layer: (data.layer === 'L1' ? 'L1' : 'L2.5'),
            confidence: typeof data.confidence === 'number' ? data.confidence : undefined,
          })
        }
      }
    }
    return result
  }, [dataParts])

  // Pre-process text: replace SIG.MSR.NNN → `CITE:N:SIG.MSR.NNN` inline markers.
  const { processedText, count } = useMemo(
    () => preprocessCitations(text),
    [text],
  )

  useEffect(() => {
    onCitationCount?.(count)
  }, [count, onCitationCount])

  // Custom code component: intercepts CITE:N:SIG patterns to render inline badges;
  // all other code (inline or fenced) falls through to standard rendering.
  const citeCodeComponent = useMemo(() => {
    function CiteCode({ className: codeClass, children, ...rest }: React.ComponentPropsWithoutRef<'code'>) {
      const raw = String(children ?? '')
      const m = raw.match(/^CITE:(\d+):(SIG\.MSR\.\d{3})$/)
      if (m) {
        return (
          <NumberedCitation
            n={parseInt(m[1], 10)}
            signalId={m[2]}
            snippet={citationRichMap.get(m[2])?.snippet}
            confidence={citationRichMap.get(m[2])?.confidence}
          />
        )
      }
      const lang = codeClass?.match(/language-(\w+)/)?.[1]
      if (!lang) {
        return <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.88em]" {...rest}>{children}</code>
      }
      if (lang === 'marsys_methodology_block') return null
      return <CodeBlock code={raw.replace(/\n$/, '')} lang={lang} isStreaming={isStreaming} />
    }
    return CiteCode
  }, [citationRichMap, isStreaming])

  // C.3 + B.4: citation-enriched render helper — data-testid enables E2E targeting.
  return (
    <div data-testid="v2-message-text">
      <MarkdownContent
        streaming={isStreaming}
        className="text-sm text-zinc-200"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        customComponents={{ code: citeCodeComponent as any }}
      >
        {processedText}
      </MarkdownContent>
    </div>
  )
}

// ─── Panel data extraction helpers ───────────────────────────────────────────

function usePanelData(dataParts: ReadonlyArray<NormalizedDataPart>) {
  const panelMembers = useMemo(() => {
    const parts: PanelMemberPart[] = []
    for (const d of dataParts) {
      if (d.type === 'data-panel-member') {
        parts.push(d.data as PanelMemberPart)
      }
    }
    // Sort by member_index for stable tab order
    parts.sort((a, b) => a.member_index - b.member_index)
    return parts
  }, [dataParts])

  const panelMeta = useMemo((): PanelMetaPart | null => {
    const entry = dataParts.find(d => d.type === 'data-panel-meta')
    return entry ? (entry.data as PanelMetaPart) : null
  }, [dataParts])

  return { panelMembers, panelMeta, isPanel: panelMeta !== null }
}

// ─── Regenerate button (B.3 fix) ─────────────────────────────────────────────
// Calls /api/chat/consume/regenerate to truncate conversation_messages before
// letting assistant-ui reload — prevents dead turns accumulating on regenerate.

function V2RegenerateButton() {
  const message = useMessage()
  const messageRuntime = useMessageRuntime()
  const runtime = useThreadRuntime()
  const conversationId = useContext(ConversationIdCtx)

  // Await DB truncation BEFORE triggering assistant-ui reload.
  // Prior implementation was fire-and-forget which caused a race: synthesis
  // would start against the un-truncated conversation.
  // If conversationId is not yet available (first turn before data-persistence lands),
  // skip truncation and reload directly — the DB doesn't have a persisted turn to truncate.
  const handleClick = useCallback(async () => {
    const messages = runtime.getState().messages
    const myIndex = messages.findIndex((m) => m.id === message.id)
    const parentId = myIndex > 0 ? messages[myIndex - 1].id : null
    if (!parentId) return
    if (conversationId) {
      try {
        await fetch('/api/chat/consume/regenerate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_id: conversationId, parent_message_id: parentId }),
        })
      } catch {
        // Truncation failed — still reload so the UI reflects the new attempt
      }
    }
    messageRuntime.reload()
  }, [message.id, messageRuntime, runtime, conversationId])

  return (
    <button
      type="button"
      onClick={handleClick}
      className="flex h-8 w-8 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
      title="Regenerate response"
      data-testid="v2-regenerate-btn"
    >
      <RotateCcw className="h-4 w-4" aria-hidden="true" />
    </button>
  )
}

// ─── Truncation banner (R7-S5) ────────────────────────────────────────────────

function TruncationContinueBanner() {
  const message = useMessage()
  const dataParts = useDataParts(message)
  const conversationId = useContext(ConversationIdCtx)
  const isStreaming = message.status?.type === 'running'

  const [status, setStatus] = useState<'idle' | 'loading' | 'done'>('idle')
  const [error, setError] = useState(false)

  const isTruncated = useMemo(() => {
    if (isStreaming) return false
    // AC-1 primary signal: data-truncated part
    if (dataParts.some(d => d.type === 'data-truncated')) return true
    // AC-1 heuristic fallback: no truncated part, but last char is not sentence-ending
    // and context_usage indicates >= 90% utilization
    const textContent = message.content
      ?.filter((p): p is { type: 'text'; text: string } => p.type === 'text')
      .map(p => p.text).join('') ?? ''
    const lastChar = textContent.trimEnd().slice(-1)
    if (/[.!?…]/.test(lastChar)) return false
    const usagePart = dataParts.find(d => d.type === 'data-context-usage')
    if (usagePart) {
      const u = usagePart.data as { tokens_used?: number; tokens_limit?: number }
      if (typeof u.tokens_used === 'number' && typeof u.tokens_limit === 'number' && u.tokens_limit > 0) {
        return u.tokens_used / u.tokens_limit >= 0.90
      }
    }
    return false
  }, [isStreaming, dataParts, message.content])

  if (!isTruncated || status === 'done') return null

  const handleContinue = async () => {
    if (status !== 'idle' || !conversationId) return
    setStatus('loading')
    setError(false)
    try {
      const r = await fetch('/api/chat/consume/continue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, last_message_id: message.id }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      // Drain the stream so the server completes; the thread will update via its own subscription.
      await r.body?.cancel()
      setStatus('done')
    } catch (err) {
      console.error('Continue failed', err)
      setError(true)
      setStatus('idle')
    }
  }

  return (
    <div
      className="flex items-center gap-2 mt-1"
      data-testid="v2-truncation-continue-banner"
      aria-label="Response was truncated"
    >
      <span className="text-[10px] text-zinc-500 italic">Response truncated</span>
      <button
        type="button"
        onClick={handleContinue}
        disabled={status === 'loading'}
        className="border border-zinc-600 text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 rounded px-2.5 py-1 text-xs font-medium transition-colors"
        data-testid="v2-truncation-continue-btn"
      >
        {status === 'loading'
          ? <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading" />
          : 'Continue'
        }
      </button>
      {error && <span className="text-[10px] text-red-400">Failed — try again</span>}
    </div>
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

  // γ1: panel data from message — merged from both stream sources via hook
  const message = useMessage()
  const dataParts = useDataParts(message)
  const { panelMembers, panelMeta, isPanel } = usePanelData(dataParts)
  const meta = (message.metadata?.custom ?? {}) as Record<string, unknown>
  // C.8: disclosure_tier, queryId, context_usage, provenance all live in metadata.custom (route wraps in custom: {})
  const isSuperAdmin = meta.disclosure_tier === 'super_admin'
  const contextUsage = meta.context_usage as ContextUsageEvent | undefined ?? null
  const provenance = meta.provenance as ProvenanceEvent | null ?? null

  // γ6: cost visibility from context (super_admin always sees cost regardless)
  const costVisible = useContext(CostVisibilityCtx)

  // Y-S5: truncated-by-edit marker — set by handleStopAndEdit in V2Composer
  const truncatedId = useContext(TruncatedMsgCtx)
  const isTruncatedByEdit = truncatedId !== null && message.id === truncatedId

  // γ4: extract citation gate status from data parts
  const citationGate = useMemo(() => {
    const entry = dataParts.find(d => d.type === 'data-citation-gate')
    return entry ? (entry.data as { status?: string; issues?: string[]; gates?: Array<{ name: string; verdict: 'PASS' | 'FAIL' | 'WARN'; reason: string }> }) : null
  }, [dataParts])

  // O3: compute isStreaming for stage/tool gating
  const isStreaming = message.status?.type === 'running'

  // O3: extract stage parts (latest per stage name — stage can transition running→done)
  const stageHistory = useMemo(() => {
    const map = new Map<string, StagePart>()
    for (const d of dataParts) {
      if (d.type === 'data-stage') {
        const stage = d.data as StagePart
        map.set(stage.stage, stage)
      }
    }
    return Array.from(map.values())
  }, [dataParts])

  // O3: extract tool parts (latest per tool name)
  const toolHistory = useMemo(() => {
    const map = new Map<string, ToolPart>()
    for (const d of dataParts) {
      if (d.type === 'data-tool') {
        const tool = d.data as ToolPart
        map.set(tool.name, tool)
      }
    }
    return Array.from(map.values())
  }, [dataParts])

  // γ3: extract prediction candidates from data parts
  const predictionCandidates = useMemo(() => {
    return dataParts
      .filter(d => d.type === 'data-prediction-candidate')
      .map(d => d.data as PredictionCandidatePart)
      .sort((a, b) => b.score - a.score)
  }, [dataParts])

  // D.3: extract correction and out-of-domain via hook (merges both live-stream + post-stream sources).
  const correction = useMemo(() => {
    const d = dataParts.find(d => d.type === 'data-correction')
    return d ? (d.data as { original_claim: string; corrected_claim: string; classical_source?: string }) : null
  }, [dataParts])

  const outOfDomain = useMemo(() => {
    const d = dataParts.find(d => d.type === 'data-out-of-domain')
    return d ? (d.data as { reason: string }) : null
  }, [dataParts])

  const handleCitationCount = useCallback((n: number) => {
    setCitationCount(n)
  }, [])

  // R11.B B-S3: .v2-message-row class enables CSS targeting.
  // Under .consume-shell.r11b-active, this column is pinned to max-width 48rem (768px)
  // via globals.css .consume-shell.r11b-active .v2-message-row rule.
  return (
    <MessagePrimitive.Root
      className="group flex w-full max-w-4xl mx-auto flex-col gap-1 px-4 py-3 v2-message-row"
      data-testid="v2-message"
    >
      <MessagePrimitive.If user>
        <div className="flex flex-col items-end gap-1">
          <div
            className="v2-user-bubble v2-user-bubble--r11b-shape rounded-2xl px-4 py-2.5 text-sm text-foreground max-w-[70%]"
            data-testid="v2-user-message"
          >
            {/* F.2: flat props — renderer receives {text,...} directly, not a nested part object */}
            <MessagePrimitive.Parts components={{ Text: (props) => <span>{props.text}</span> }} />
          </div>

          {/* Edit action + branch picker for user messages */}
          <div className="flex min-h-[2rem] items-center gap-2 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1.5"
              data-testid="v2-user-action-bar"
            >
              <ActionBarPrimitive.Copy asChild>
                <button
                  type="button"
                  className="flex h-8 w-8 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Copy message"
                  data-testid="v2-user-copy-btn"
                >
                  <Copy className="h-4 w-4" aria-hidden="true" />
                </button>
              </ActionBarPrimitive.Copy>
              <ActionBarPrimitive.Edit asChild>
                <button
                  type="button"
                  className="flex h-8 w-8 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Edit message"
                  data-testid="v2-edit-btn"
                >
                  <Pencil className="h-4 w-4" aria-hidden="true" />
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
              gates={citationGate.gates}
            />
          )}

          {/* D.3: out-of-domain banner (above answer) */}
          {outOfDomain && (
            <OutOfDomainBanner event={{ type: 'out_of_domain', reason: outOfDomain.reason }} data-testid="v2-out-of-domain-banner" />
          )}

          {/* D.3: correction notice (above answer) */}
          {correction && (
            <CorrectionNotice
              correction={{ type: 'correction', original_claim: correction.original_claim, corrected_claim: correction.corrected_claim, classical_source: correction.classical_source }}
              data-testid="v2-correction-notice"
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

          {/* X-S4: still-working indicator after 25s of streaming — reassures user on long queries */}
          <StillWorkingIndicator isStreaming={isStreaming} />

          <MessagePrimitive.Parts
            components={{
              // γ2: ReasoningProgress with live token count + elapsed timer + auto-collapse >2k tokens
              // F.2: props.text is the accumulated reasoning text (flat prop, not props.reasoning)
              Reasoning: (props) => <ReasoningProgress text={props.text} />,
              Text: (props) => <V2AssistantText text={props.text} onCitationCount={handleCitationCount} />,
            }}
          />

          {/* R7-S5: truncation continue banner — shown after stream ends if message was cut off */}
          <TruncationContinueBanner />

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

          {/* Y-S5: truncated-by-edit chip — shown when user stopped stream for editing */}
          {isTruncatedByEdit && (
            <div
              className="flex items-center gap-1 self-start rounded-full border border-amber-500/30 bg-amber-900/20 px-2.5 py-0.5 text-[11px] text-amber-400"
              data-testid="v2-truncated-by-edit-chip"
              aria-label="Response stopped for editing"
            >
              <Square className="h-2.5 w-2.5 fill-current shrink-0" aria-hidden="true" />
              Stopped for editing
            </div>
          )}

          {/* C.8: post-answer provenance — model/source/signal counts with drawer */}
          {provenance && <PostAnswerProvenance provenance={provenance} />}

          {/* Reload (regenerate) + Details + Copy actions for assistant messages */}
          <div className="flex min-h-[2rem] items-center gap-2 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1.5"
              data-testid="v2-assistant-action-bar"
            >
              <V2RegenerateButton />

              {/* β6: Show details drawer */}
              <button
                type="button"
                onClick={() => setDetailsOpen(true)}
                className="flex h-8 w-8 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                title="Show message details"
                data-testid="v2-details-btn"
              >
                <Info className="h-4 w-4" aria-hidden="true" />
              </button>

              <ActionBarPrimitive.Copy asChild>
                <button
                  type="button"
                  className="flex h-8 w-8 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Copy response"
                  data-testid="v2-copy-btn"
                >
                  <Copy className="h-4 w-4" aria-hidden="true" />
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
        {/* R9: inline tool-flow timeline — admin-only; NEXT_PUBLIC_MARSYS_FLAG_R9_TOOL_FLOW gates internally */}
        <InlineToolFlow queryId={(meta.queryId as string | null) ?? null} isAdmin={isSuperAdmin} />
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
export const AttachmentCtx = createContext<AttachmentContextValue>({
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

function V2Composer({ slashEnabled = false, tokensEnabled = false }: { slashEnabled?: boolean; tokensEnabled?: boolean }) {
  // F.3: useThreadRuntime().subscribe() for run-state (deprecated primitive avoided)
  const runtime = useThreadRuntime()
  const [isRunning, setIsRunning] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const isRunningRef = useRef(false)
  const [composerValue, setComposerValue] = useState('')
  const [slashActiveIdx, setSlashActiveIdx] = useState(0)
  const { tokenCount, pctUsed } = useTokenCount(tokensEnabled ? composerValue : '')

  const { attachments, addAttachment, removeAttachment } = useContext(AttachmentCtx)
  const conversationId = useContext(ConversationIdCtx)
  const [lastPrompt, saveLastPrompt] = useLastPrompt(conversationId)
  const setTruncatedId = useContext(SetTruncatedMsgCtx)

  useEffect(() => {
    const unsub = runtime.subscribe(() => {
      const running = runtime.getState().isRunning
      isRunningRef.current = running
      setIsRunning(running)
    })
    return unsub
  }, [runtime])

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

  // Slash command detection
  const slashQuery = slashEnabled ? (() => {
    const m = composerValue.match(/(?:^| )\/(\w*)$/)
    return m ? m[1] : null
  })() : null
  const slashFiltered = slashQuery !== null
    ? COMMANDS.filter(c =>
        c.name.toLowerCase().startsWith(slashQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(slashQuery.toLowerCase())
      ).slice(0, 6)
    : []
  const slashOpen = slashEnabled && slashQuery !== null

  function handleSlashSelect(cmd: typeof COMMANDS[0]) {
    const textarea = containerRef.current?.querySelector('textarea')
    if (!textarea) return
    const newValue = composerValue.replace(
      /(?:^|( ))\/\w*$/,
      (_, space) => (space ?? '') + (cmd.template ?? '')
    )
    // Use native setter so React's synthetic event fires
    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    )?.set
    nativeSetter?.call(textarea, newValue)
    textarea.dispatchEvent(new Event('input', { bubbles: true }))
    setComposerValue(newValue)
    setSlashActiveIdx(0)
    textarea.focus()
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

  // X-S2: ArrowUp recall + save last prompt on Enter/send
  function handleComposerKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'ArrowUp' && composerValue === '') {
      // Restore last sent message for this conversation
      const key = `marsys_chat_v2_last_prompt_${conversationId ?? '__new__'}`
      let last = ''
      try { last = localStorage.getItem(key) ?? '' } catch {}
      if (!last) return
      e.preventDefault()
      const textarea = e.currentTarget
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set
      nativeSetter?.call(textarea, last)
      textarea.dispatchEvent(new Event('input', { bubbles: true }))
      setComposerValue(last)
    } else if (e.key === 'Enter' && !e.shiftKey) {
      // Save current value as last prompt before send clears the textarea
      if (composerValue.trim()) saveLastPrompt(composerValue)
    }
  }

  // Y-S5: Abort stream + restore last prompt for editing.
  // Reads the last assistant message ID from the runtime snapshot so the
  // truncated chip can pin to that specific message even after re-sends.
  function handleStopAndEdit() {
    const messages = runtime.getState().messages
    const lastAssistantId = [...messages].reverse().find(m => m.role === 'assistant')?.id ?? '__truncated__'
    runtime.cancelRun()
    setTruncatedId?.(lastAssistantId)
    if (!lastPrompt) return
    const textarea = containerRef.current?.querySelector('textarea')
    if (!textarea) return
    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    )?.set
    nativeSetter?.call(textarea, lastPrompt)
    textarea.dispatchEvent(new Event('input', { bubbles: true }))
    setComposerValue(lastPrompt)
    textarea.focus()
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
        {/* X-S1: camera-only input for mobile — capture="environment" opens back camera directly */}
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="sr-only"
          aria-label="Take photo"
          onChange={handleFileChange}
          data-testid="v2-camera-input"
        />

        {/* C.4: brand pill wrapper — paperclip + textarea + hints + send inside the pill */}
        <div className="mx-auto max-w-4xl relative">
          {slashOpen && (
            <SlashCommandMenu
              commands={slashFiltered}
              activeIndex={slashActiveIdx}
              onSelect={handleSlashSelect}
            />
          )}
          <div className="relative flex flex-col rounded-3xl border border-[rgba(var(--brand-gold-rgb),0.35)] bg-background shadow-sm transition-all duration-200">
            {/* β5: attachment strip inside pill top */}
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 px-4 pt-3">
                <AttachmentStrip attachments={attachments} onRemove={removeAttachment} />
              </div>
            )}

            <ComposerPrimitive.Input
              className="w-full resize-none overflow-y-auto rounded-3xl bg-transparent px-5 py-4 text-[15px] leading-[1.55] text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
              placeholder="Ask about the chart…"
              rows={3}
              data-testid="v2-composer-input"
              onPaste={handlePaste}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                setComposerValue(e.target.value)
              }}
              onKeyDown={handleComposerKeyDown}
              aria-label="Message input"
              aria-multiline="true"
            />

            {tokensEnabled && (
              <p className={cn('px-5 pb-0.5 text-[10px] transition-colors', pctUsed === null || pctUsed < 75 ? 'text-zinc-500' : pctUsed < 95 ? 'text-amber-400' : 'text-red-400')}>
                {tokenCount === null ? '— tokens' : `${tokenCount} tokens · ${pctUsed}%`}
              </p>
            )}
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
                {/* X-S1: camera shortcut — mobile only (md:hidden); desktop uses paperclip */}
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="md:hidden inline-flex h-8 w-8 items-center justify-center rounded-full text-zinc-500 transition-all hover:bg-zinc-800 hover:text-zinc-300"
                  title="Take photo"
                  aria-label="Take photo with camera"
                  data-testid="v2-camera-btn"
                >
                  <Camera className="h-4 w-4" aria-hidden="true" />
                </button>
                <span className="hidden md:inline pl-1 text-[10px] uppercase tracking-[0.18em] text-zinc-600">
                  ↵ Send · ⇧↵ New line
                </span>
              </div>

              <div className="flex items-center gap-1">
                {isRunning ? (
                  EDIT_WHILE_STREAMING_ENABLED ? (
                    <button
                      type="button"
                      className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 h-9 text-xs font-medium text-zinc-900 transition-all hover:opacity-80"
                      title="Stop generation and restore prompt for editing"
                      aria-label="Stop and edit"
                      data-testid="v2-stop-and-edit-btn"
                      onClick={handleStopAndEdit}
                    >
                      <Square className="h-3 w-3 fill-current shrink-0" aria-hidden="true" />
                      Edit
                    </button>
                  ) : (
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
                  )
                ) : (
                  <ComposerPrimitive.Send asChild>
                    <button
                      type="submit"
                      className="brand-cta inline-flex h-9 w-9 items-center justify-center rounded-full transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40 active:scale-95"
                      aria-label="Send message"
                      data-testid="v2-send-btn"
                      onClick={() => { if (composerValue.trim()) saveLastPrompt(composerValue) }}
                    >
                      <ArrowUp className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </ComposerPrimitive.Send>
                )}
              </div>
            </div>
          </div>
        </div>

      </ComposerPrimitive.Root>
    </div>
  )
}

// ─── E.1: V2TitleTracker — sidebar refresh on auto-title data part ───────────
// Subscribes to runtime messages; fires V2TitleCb when a data part with
// name === 'title' is first observed. Extracted from V2RuntimeTracker for
// named-component test discoverability.

function V2TitleTracker() {
  const runtime = useThreadRuntime()
  const onTitle = useContext(V2TitleCb)

  useEffect(() => {
    if (!onTitle) return
    let fired = false
    return runtime.subscribe(() => {
      if (fired) return
      const messages = runtime.getState().messages
      for (const msg of messages) {
        if (msg.role !== 'assistant') continue
        for (const part of (msg.content ?? []) as ReadonlyArray<unknown>) {
          if (
            typeof part === 'object' && part !== null &&
            (part as Record<string, unknown>).type === 'data' &&
            (part as Record<string, unknown>).name === 'title'
          ) {
            fired = true
            onTitle()
            return
          }
        }
      }
    })
  }, [runtime, onTitle])

  return null
}

// ─── C.2 + W5 + E.1: Unified runtime tracker ─────────────────────────────────
// Single subscriber replacing V2QueryIdTracker and V2ConversationIdTracker.
// V2TitleTracker is extracted above as a named component for test discoverability.

function V2RuntimeTracker() {
  const runtime = useThreadRuntime()
  const onQueryId = useContext(V2QueryIdCb)
  const onConversationId = useContext(V2ConversationIdCb)
  const onTitle = useContext(V2TitleCb)

  useEffect(() => {
    if (!onQueryId && !onConversationId && !onTitle) return

    let lastQueryId: string | null = null
    let lastConversationId: string | null = null
    let lastTitleEmit = false

    const unsub = runtime.subscribe(() => {
      const state = runtime.getState()
      const messages = state.messages

      let queryIdHit: string | null = null
      let conversationIdHit: string | null = null
      let titleHit = false

      // Backward walk: query_id + conversation_id from latest assistant message.
      for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i]
        if (msg.role !== 'assistant') continue
        if (!queryIdHit) {
          const custom = (msg.metadata as { custom?: { queryId?: string } } | undefined)?.custom
          if (custom?.queryId) {
            queryIdHit = custom.queryId
          } else {
            const data = (msg.metadata as unknown as { unstable_data?: ReadonlyArray<unknown> } | undefined)?.unstable_data ?? []
            for (const part of data) {
              const p = part as { query_id?: string }
              if (p.query_id) { queryIdHit = p.query_id; break }
            }
          }
        }
        if (!conversationIdHit) {
          const content = (msg.content ?? []) as ReadonlyArray<unknown>
          for (const part of content) {
            if (
              typeof part === 'object' && part !== null &&
              (part as Record<string, unknown>).type === 'data' &&
              (part as Record<string, unknown>).name === 'persistence'
            ) {
              const data = (part as Record<string, unknown>).data as Record<string, unknown>
              if (typeof data?.conversation_id === 'string') {
                conversationIdHit = data.conversation_id
                break
              }
            }
          }
        }
        if (queryIdHit && conversationIdHit) break
      }

      // Forward walk: title part (first occurrence; fires once per mount).
      for (const msg of messages) {
        if (msg.role !== 'assistant') continue
        const content = (msg.content ?? []) as ReadonlyArray<unknown>
        for (const part of content) {
          if (
            typeof part === 'object' && part !== null &&
            (part as Record<string, unknown>).type === 'data' &&
            (part as Record<string, unknown>).name === 'title'
          ) {
            titleHit = true
            break
          }
        }
        if (titleHit) break
      }

      // Emit only on transitions — avoid callback spam on every streaming token.
      if (queryIdHit && queryIdHit !== lastQueryId) {
        lastQueryId = queryIdHit
        if (onQueryId) onQueryId(queryIdHit)
      }
      if (conversationIdHit && conversationIdHit !== lastConversationId) {
        lastConversationId = conversationIdHit
        if (onConversationId) onConversationId(conversationIdHit)
      }
      if (titleHit && !lastTitleEmit) {
        lastTitleEmit = true
        if (onTitle) onTitle()
      }
    })

    return unsub
  }, [runtime, onQueryId, onConversationId, onTitle])

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
          // runtime.getState().messages returns ThreadMessage objects whose text
          // lives in .content, not .parts. Guard with ?? [] to avoid crashes.
          const text = (lastMsg.parts ?? (lastMsg as any).content ?? [])
            .filter((p: { type: string }): p is { type: 'text'; text: string } => p.type === 'text')
            .map((p: { text: string }) => p.text)
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
  const { stack, style, lelEnabled, activeTier, audienceTier, activePersonaId, setStack, setStyle, setLelEnabled, setActiveTierOverride, setActivePersonaId } =
    useContext(V2PrefsCtx)

  return (
    <div
      className="mx-auto max-w-4xl w-full px-4 py-1 flex items-center justify-between border-b border-zinc-800"
      data-testid="v2-bottom-bar"
    >
      <ModelStylePicker
        stack={stack}
        style={style}
        onStackChange={setStack}
        onStyleChange={setStyle}
        activePersonaId={activePersonaId}
        onPersonaChange={setActivePersonaId}
      />
      <div className="flex items-center gap-2" data-testid="v2-composer-options">
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
        {/* TierPicker removed (Stream A 3.tier_excision 2026-05-28). Depth is now planner-auto-selected by query class. */}
        <PanelModeToggle />
        {/* R11.G: Settings dropdown — replaces inline parity toggle */}
        <SettingsDropdown />
      </div>
    </div>
  )
}

// ─── X-S6: Scroll discipline — sentinel + unread count button ────────────────

const SCROLL_DISCIPLINE_ENABLED = process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE === 'true'

// ─── Y-S5: Stop-and-edit while streaming ─────────────────────────────────────
const EDIT_WHILE_STREAMING_ENABLED = process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING === 'true'

function V2ScrollDiscipline() {
  const { isAtBottom, unreadCount, sentinelRef, incrementUnread, scrollToBottom } = useScrollDiscipline()
  const runtime = useThreadRuntime()

  useEffect(() => {
    return runtime.subscribe(() => {
      if (runtime.getState().isRunning && !isAtBottom) {
        incrementUnread()
      }
    })
  }, [runtime, isAtBottom, incrementUnread])

  return (
    <>
      <div
        ref={sentinelRef}
        aria-hidden="true"
        style={{ height: 1, flexShrink: 0 }}
        data-testid="v2-scroll-sentinel"
      />
      <ScrollToBottomButton
        visible={!isAtBottom}
        unreadCount={unreadCount}
        onClick={scrollToBottom}
      />
    </>
  )
}

// ─── Thread ───────────────────────────────────────────────────────────────────

function V2Thread({ chartId, chartName, slashEnabled = false, tokensEnabled = false }: { chartId: string; chartName: string; slashEnabled?: boolean; tokensEnabled?: boolean }) {
  const [truncatedMsgId, setTruncatedMsgId] = useState<string | null>(null)
  return (
    <TruncatedMsgCtx.Provider value={truncatedMsgId}>
    <SetTruncatedMsgCtx.Provider value={setTruncatedMsgId}>
    <ThreadPrimitive.Root
      className="flex h-full flex-col flex-1 min-w-0"
      data-testid="v2-thread-root"
    >
      {/* γ8: live region announces new assistant messages to screen readers */}
      <ThreadPrimitive.Viewport
        className="flex flex-col items-center flex-1 overflow-y-auto scroll-smooth py-4"
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
            className="max-w-4xl px-4"
            data-testid="v2-thread-empty"
          />
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages components={{ Message: V2Message }} />

        {SCROLL_DISCIPLINE_ENABLED ? (
          <V2ScrollDiscipline />
        ) : (
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
        )}
      </ThreadPrimitive.Viewport>

      <V2BottomBar />
      <V2Composer slashEnabled={slashEnabled} tokensEnabled={tokensEnabled} />
    </ThreadPrimitive.Root>
    </SetTruncatedMsgCtx.Provider>
    </TruncatedMsgCtx.Provider>
  )
}

// ─── WS-1-S3-B: Capability gate UI components ────────────────────────────────

/**
 * Full-screen block shown when no pyramid layers exist (chart never built).
 * Caps the user at the cockpit — they cannot proceed to chat until L1 is built.
 */
function NoBuildGate({ cockpitHref }: { cockpitHref: string }) {
  return (
    <div
      className="flex flex-col items-center justify-center h-full gap-6 p-8 text-center"
      data-testid="capability-gate-no-build"
      role="alert"
      aria-live="polite"
    >
      <div className="rounded-full bg-gray-100 p-5">
        <svg className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
      </div>
      <div className="max-w-md">
        <h2 className="text-lg font-semibold text-gray-900">Build required before consulting</h2>
        <p className="mt-2 text-sm text-gray-600">
          This chart has not been built yet. The Gaṇita layer (L1 — Chart Facts) must complete
          before Madhav can provide grounded astrological analysis.
        </p>
      </div>
      <a
        href={cockpitHref}
        className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
        data-testid="capability-gate-cockpit-link"
      >
        Go to build cockpit
      </a>
    </div>
  )
}

/**
 * Dismissible amber banner shown when L1 is still building.
 * Chat renders underneath — the user can type, but grounded tools are limited.
 */
function L1BuildingBanner({ cockpitHref, onDismiss }: { cockpitHref: string; onDismiss: () => void }) {
  return (
    <div
      className="flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
      data-testid="capability-gate-l1-building"
      role="alert"
      aria-live="polite"
    >
      <svg className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
        <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
      </svg>
      <div className="flex-1">
        <span className="font-semibold">Gaṇita layer building</span>
        {' — '}consult is available but grounded chart-fact tools will complete after L1 finishes.{' '}
        <a href={cockpitHref} className="underline hover:text-amber-700 font-medium">
          Monitor progress
        </a>
      </div>
      <button
        type="button"
        onClick={onDismiss}
        className="shrink-0 rounded p-0.5 hover:bg-amber-200 focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors"
        aria-label="Dismiss building banner"
        data-testid="capability-gate-l1-dismiss"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}

// ─── ConsumeChatV2 ────────────────────────────────────────────────────────────

/**
 * β2: Thread with conversation list sidebar + write-through restore on mount.
 */
export function ConsumeChatV2({ chartId, chartName, chartMeta, costVisibilityEnabled, audienceTier = 'client', reports = [], slashEnabled = false, exportEnabled = false, tokensEnabled = false, initialMessages: initialMessagesProp, capabilityGateState }: ConsumeChatProps) {
  // WS-1-S3-B: L1-building banner dismiss state
  const [l1BannerDismissed, setL1BannerDismissed] = useState(false)

  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | undefined>(initialMessagesProp)
  const [restoredKey, setRestoredKey] = useState(0)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)
  // pinnedOpen: true when the user explicitly clicked the toggle to open — hover-out won't auto-close.
  // Resets to false when the user clicks toggle again (to close) or when sidebar auto-opens via hover.
  const [sidebarPinned, setSidebarPinned] = useState(false)
  const collapseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const expandTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [sidebarReloadTick, setSidebarReloadTick] = useState(0)
  const [sidebarLoading, setSidebarLoading] = useState(false)
  const [textScale, increaseTextScale, decreaseTextScale] = useTextScale()
  const handleTitleGenerated = useCallback(() => setSidebarReloadTick((n) => n + 1), [])

  // Hover-based auto-expand / auto-collapse (desktop only).
  // Strip mouseenter → expand after 150ms. Sidebar mouseleave → collapse after 400ms if not pinned.
  const handleStripEnter = useCallback(() => {
    if (expandTimerRef.current) clearTimeout(expandTimerRef.current)
    if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current)
    expandTimerRef.current = setTimeout(() => {
      setSidebarCollapsed(false)
      setSidebarPinned(false) // hover-open is not pinned
    }, 150)
  }, [])

  const handleSidebarEnter = useCallback(() => {
    if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current)
    if (expandTimerRef.current) clearTimeout(expandTimerRef.current)
  }, [])

  const handleSidebarLeave = useCallback(() => {
    if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current)
    collapseTimerRef.current = setTimeout(() => {
      setSidebarPinned(prev => {
        if (!prev) setSidebarCollapsed(true)
        return prev
      })
    }, 400)
  }, [])
  const [traceOpen, setTraceOpen] = useState(false)
  const [latestQueryId, setLatestQueryId] = useState<string | null>(null)
  const { stack, style, lelEnabled, setStack, setStyle, setLelEnabled } = useChatPreferences(chartId)
  const [activeTier, setActiveTierOverride] = useState<AudienceTier>(audienceTier)
  // R9-S3: Persona selection state — persists for the session; null = no persona active.
  const [activePersonaId, setActivePersonaId] = useState<string | null>(null)
  // R11.B — multi-provider parity hook (A-S11). Combined with build-time flag to gate r11b-active.
  const isParityActive = useMultiProviderParity()
  // r11b-active class activates the Look-and-Feel layer (typography, shapes, chrome).
  // Both conditions must be true: build-time kill-switch AND user runtime toggle.
  const r11bActive = R11B_LOOK_AND_FEEL_ENV && isParityActive

  const prefsCtxValue = useMemo<V2PrefsCtxValue>(() => ({
    stack, style, lelEnabled, activeTier, audienceTier, activePersonaId,
    setStack, setStyle, setLelEnabled, setActiveTierOverride, setActivePersonaId,
  }), [stack, style, lelEnabled, activeTier, audienceTier, activePersonaId, setStack, setStyle, setLelEnabled])

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
        return
      }
      if (!isInput && e.key === 'j') {
        document.querySelector('[role="log"]')?.scrollBy({ top: 150, behavior: 'smooth' })
        return
      }
      if (!isInput && e.key === 'k') {
        document.querySelector('[role="log"]')?.scrollBy({ top: -150, behavior: 'smooth' })
        return
      }
      if (!isInput && e.key === 'c') {
        e.preventDefault()
        const textarea = document.querySelector('textarea[data-testid="v2-composer-input"]') as HTMLTextAreaElement | null
        textarea?.focus()
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
    setSidebarCollapsed(true)
    setSidebarPinned(false)
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

  const handleRenameConversation = useCallback(async (id: string, currentTitle: string) => {
    const newTitle = window.prompt('Rename conversation', currentTitle)
    if (!newTitle || newTitle.trim() === currentTitle.trim()) return
    try {
      const r = await fetch(`/api/conversations/${id}`, {
        method: 'PATCH',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ title: newTitle.trim() }),
      })
      if (!r.ok) throw new Error(`PATCH failed ${r.status}`)
      setSidebarReloadTick(t => t + 1)
    } catch (err) {
      console.error('Rename failed', err)
    }
  }, [])

  const handleDeleteConversation = useCallback(async (id: string) => {
    if (!window.confirm('Archive this conversation? It will be hidden from the list.')) return
    try {
      const r = await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
      if (!r.ok) throw new Error(`DELETE failed ${r.status}`)
      if (activeConversationId === id) setActiveConversationId(null)
      setSidebarReloadTick(t => t + 1)
    } catch (err) {
      console.error('Delete failed', err)
    }
  }, [activeConversationId])

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
      run: () => { setSidebarCollapsed(c => { setSidebarPinned(!c); return !c }); setPaletteOpen(false) },
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

  // WS-1-S3-B: Capability gate — full-screen block when no build exists
  if (capabilityGateState?.state === 'no-build') {
    return (
      <CostVisibilityCtx.Provider value={costVisibilityEnabled ?? false}>
      <V2PrefsCtx.Provider value={prefsCtxValue}>
      <div className="relative flex h-dvh text-zinc-100 consume-shell bg-gray-950" data-testid="v2-chat-shell">
        <NoBuildGate cockpitHref={capabilityGateState.cockpitHref} />
      </div>
      </V2PrefsCtx.Provider>
      </CostVisibilityCtx.Provider>
    )
  }

  return (
    <CostVisibilityCtx.Provider value={costVisibilityEnabled ?? false}>
    <V2PrefsCtx.Provider value={prefsCtxValue}>
    <div
      className={cn(
        'relative flex h-dvh text-zinc-100 consume-shell',
        r11bActive && 'r11b-active',
      )}
      data-testid="v2-chat-shell"
      data-r11b-active={r11bActive ? 'true' : 'false'}
      style={{ ['--text-scale' as string]: textScale }}
    >
      {/* Mobile sidebar backdrop — fades in/out when sidebar opens/closes on small screens */}
      <AnimatePresence>
        {!sidebarCollapsed && (
          <motion.div
            key="mobile-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="fixed inset-0 z-30 bg-black/60 md:hidden"
            onClick={() => setSidebarCollapsed(true)}
            aria-hidden="true"
            data-testid="v2-mobile-sidebar-backdrop"
          />
        )}
      </AnimatePresence>

      {/* Condensed glass rail — fades out when sidebar opens, fades in when it closes. */}
      <AnimatePresence>
        {sidebarCollapsed && (
          <motion.div
            key="glass-rail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="fixed left-0 inset-y-0 w-3 z-40 hidden md:block backdrop-blur-[8px] border-r"
            style={{
              background: 'rgba(13,10,5,0.38)',
              borderRightColor: 'rgba(255,255,255,0.10)',
            }}
            onMouseEnter={handleStripEnter}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      {/* Sidebar wrapper — slides in from the left with spring physics. */}
      <AnimatePresence>
        {!sidebarCollapsed && (
          <motion.div
            key="sidebar"
            initial={{ x: '-100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '-100%', opacity: 0 }}
            transition={{
              x: { type: 'spring', stiffness: 320, damping: 32 },
              opacity: { duration: 0.18, ease: 'easeOut' },
            }}
            className="fixed inset-y-0 left-0 z-40 flex"
            onMouseEnter={handleSidebarEnter}
            onMouseLeave={handleSidebarLeave}
          >
            <ConversationSidebarV2
              chartId={chartId}
              activeId={activeConversationId}
              onSelect={handleSelectConversation}
              onNew={handleNewConversation}
              collapsed={sidebarCollapsed}
              onToggle={() => {
                const next = sidebarCollapsed
                setSidebarCollapsed(!next)
                setSidebarPinned(next) // opening via click = pin; closing via click = unpin
              }}
              reloadTrigger={sidebarReloadTick}
              onRename={handleRenameConversation}
              onDelete={handleDeleteConversation}
              showProjects={process.env.NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS === 'true'}
              onLoadingChange={setSidebarLoading}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <div
        data-testid="v2-chat-column"
        className={cn(
          "flex flex-col flex-1 overflow-hidden min-w-0"
        )}
      >
        <header
          className="flex items-center gap-3 px-4 md:px-6 py-3 shrink-0"
          data-testid="v2-header"
        >
          {/* Back to dashboard */}
          <Link
            href="/dashboard"
            title="Back to dashboard"
            className="flex h-8 w-8 items-center justify-center rounded-md text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors"
            aria-label="Back to dashboard"
            data-testid="v2-back-to-dashboard"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          </Link>

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
          {/* Desktop: toggle sidebar (click = pin open / unpin+close) */}
          <button
            type="button"
            onClick={() => {
              const next = sidebarCollapsed
              setSidebarCollapsed(!next)
              setSidebarPinned(next) // opening = pin, closing = unpin
            }}
            className="hidden md:flex h-8 w-8 items-center justify-center rounded-md text-[color-mix(in_oklch,var(--brand-gold-cream)_40%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors"
            aria-label="Toggle conversations"
            data-testid="v2-desktop-sidebar-toggle"
          >
            <PanelLeft className="h-4 w-4" aria-hidden="true" />
          </button>

          {/* Brand title + meta — skeleton during initial sidebar load */}
          {sidebarLoading ? (
            <HeaderSkeleton />
          ) : (
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
          )}

          {/* Right-side actions: Reports + Export + Aa+/Aa− + Share + Trace (super_admin only) */}
          <div className="flex shrink-0 items-center gap-1" data-testid="v2-header-actions">
            <ConsumeReportLibraryV2 reports={reports} />
            {exportEnabled && activeConversationId && (
              <ExportDropdown conversationId={activeConversationId} />
            )}
            {/* X-S7: font-size controls */}
            <button
              type="button"
              onClick={decreaseTextScale}
              aria-label="Decrease text size"
              aria-disabled={textScale === TEXT_SCALES[0]}
              data-testid="v2-font-decrease"
              className="flex h-7 items-center justify-center rounded px-1.5 text-[11px] font-semibold text-[color-mix(in_oklch,var(--brand-gold-cream)_50%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors disabled:opacity-40"
            >
              Aa−
            </button>
            <button
              type="button"
              onClick={increaseTextScale}
              aria-label="Increase text size"
              aria-disabled={textScale === TEXT_SCALES[TEXT_SCALES.length - 1]}
              data-testid="v2-font-increase"
              className="flex h-7 items-center justify-center rounded px-1.5 text-[11px] font-semibold text-[color-mix(in_oklch,var(--brand-gold-cream)_50%,transparent)] hover:bg-[rgba(var(--brand-gold-rgb),0.06)] transition-colors disabled:opacity-40"
            >
              Aa+
            </button>
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

        {/* WS-1-S3-B: L1-building capability gate banner */}
        {capabilityGateState?.state === 'l1-building' && !l1BannerDismissed && (
          <div className="px-4 md:px-6 pt-2 shrink-0">
            <L1BuildingBanner
              cockpitHref={capabilityGateState.cockpitHref}
              onDismiss={() => setL1BannerDismissed(true)}
            />
          </div>
        )}

        <main className="flex-1 overflow-hidden">
          <V2ChatRuntime
            key={restoredKey}
            chartId={chartId}
            chartName={chartName}
            conversationId={activeConversationId}
            initialMessages={initialMessages}
            onQueryId={setLatestQueryId}
            onConversationId={setActiveConversationId}
            onTitle={handleTitleGenerated}
            slashEnabled={slashEnabled}
            tokensEnabled={tokensEnabled}
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
  onConversationId?: (id: string) => void
  onTitle?: () => void
  slashEnabled?: boolean
  tokensEnabled?: boolean
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

function V2ChatRuntime({ chartId, chartName, conversationId, initialMessages, onQueryId, onConversationId, onTitle, slashEnabled = false, tokensEnabled = false }: V2ChatRuntimeProps & { onQueryId?: (id: string) => void }) {
  const chartIdRef = useRef(chartId)
  chartIdRef.current = chartId
  const conversationIdRef = useRef(conversationId)
  conversationIdRef.current = conversationId

  // B-S7: Citation side panel retired. Citations are inline-only via NumberedCitation.
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

  const { stack, style, lelEnabled, activePersonaId: activePersonaIdCtx } = useContext(V2PrefsCtx)
  const stackRef = useRef(stack)
  stackRef.current = stack
  const styleRef = useRef(style)
  styleRef.current = style
  const lelEnabledRef = useRef(lelEnabled)
  lelEnabledRef.current = lelEnabled
  // R9-S3: Track active persona via ref so the body() closure reads the latest value.
  const activePersonaIdRef = useRef(activePersonaIdCtx)
  activePersonaIdRef.current = activePersonaIdCtx

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
          // R9-S3: Include active persona so synthesis can prepend its system_prompt.
          ...(activePersonaIdRef.current ? { persona_id: activePersonaIdRef.current } : {}),
        }
      },
    }),
    messages: initialMessages,
  })


  return (
    <V2QueryIdCb.Provider value={onQueryId ?? null}>
    <V2ConversationIdCb.Provider value={onConversationId ?? null}>
    <V2TitleCb.Provider value={onTitle ?? null}>
    <PanelOptInCtx.Provider value={panelOptInCtxValue}>
    <ConversationIdCtx.Provider value={conversationId}>
      <AttachmentCtx.Provider value={attachmentManager}>
        <AssistantRuntimeProvider runtime={runtime}>
          {/* γ7: track session-storage pending-stream entry for stream-resume */}
          <V2StreamResumeTracker chartId={chartId} conversationId={conversationId} />
          {/* E.1: V2TitleTracker — sidebar refresh on auto-title */}
          <V2TitleTracker />
          {/* C.2 + W5: unified runtime tracker — emits query_id, conversation_id */}
          <V2RuntimeTracker />
          <div className="flex h-full overflow-hidden">
            {/* B-S7: side panel retired — citations are inline-only via NumberedCitation */}
            <V2Thread chartId={chartId} chartName={chartName} slashEnabled={slashEnabled ?? false} tokensEnabled={tokensEnabled ?? false} />
          </div>
        </AssistantRuntimeProvider>
      </AttachmentCtx.Provider>
    </ConversationIdCtx.Provider>
    </PanelOptInCtx.Provider>
    </V2TitleCb.Provider>
    </V2ConversationIdCb.Provider>
    </V2QueryIdCb.Provider>
  )
}
