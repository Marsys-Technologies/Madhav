'use client'

/**
 * ReasoningProgress — γ2
 *
 * Collapsible reasoning drawer with live token count + elapsed-time-in-thought.
 * - Elapsed timer starts on first reasoning character; stops when streaming ends.
 * - Auto-collapses when reasoning text exceeds COLLAPSE_THRESHOLD tokens at end of stream.
 * - < COLLAPSE_THRESHOLD: defaults to expanded.
 * - ≥ COLLAPSE_THRESHOLD: defaults to collapsed with a "Show N tokens of reasoning" affordance.
 *
 * The component is mounted as the `Reasoning` renderer inside MessagePrimitive.Parts.
 * It calls useMessagePartReasoning() for live status; the caller passes `text` as a prop.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { useMessagePartReasoning } from '@assistant-ui/react'

/** Approx tokens: Claude tokenizer averages ~4 chars/token. */
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

const COLLAPSE_THRESHOLD = 2000 // tokens

interface ReasoningProgressProps {
  /** The full accumulated reasoning text (from MessagePrimitive.Parts Reasoning renderer). */
  text: string
  'data-testid'?: string
}

export function ReasoningProgress({ text, 'data-testid': testId }: ReasoningProgressProps) {
  const { status } = useMessagePartReasoning()
  const isStreaming = status.type === 'running'

  const tokenCount = useMemo(() => estimateTokens(text), [text])
  const isLong = tokenCount >= COLLAPSE_THRESHOLD

  // Collapsed state: starts expanded if short, starts collapsed if long.
  // Once the stream ends and the text is long, collapse if still at default.
  const [collapsed, setCollapsed] = useState(false)
  const hasAutoCollapsed = useRef(false)
  const wasStreaming = useRef(isStreaming)

  // Auto-collapse at end of stream if text is long (only fires once)
  useEffect(() => {
    if (wasStreaming.current && !isStreaming && isLong && !hasAutoCollapsed.current) {
      hasAutoCollapsed.current = true
      setCollapsed(true)
    }
    wasStreaming.current = isStreaming
  }, [isStreaming, isLong])

  // Elapsed timer — counts seconds while streaming, freezes on stop.
  const startRef = useRef<number | null>(null)
  const [elapsedMs, setElapsedMs] = useState(0)

  useEffect(() => {
    if (text.length > 0 && startRef.current === null) {
      startRef.current = Date.now()
    }
  }, [text])

  useEffect(() => {
    if (!isStreaming || startRef.current === null) return
    const id = setInterval(() => {
      setElapsedMs(Date.now() - (startRef.current ?? Date.now()))
    }, 200)
    return () => clearInterval(id)
  }, [isStreaming])

  // Freeze elapsed at stream end
  useEffect(() => {
    if (!isStreaming && startRef.current !== null) {
      setElapsedMs(Date.now() - startRef.current)
    }
  }, [isStreaming])

  const elapsedSec = (elapsedMs / 1000).toFixed(1)
  const collapseLabel = `Show ${tokenCount.toLocaleString()} tokens of reasoning`

  return (
    <div
      className="rounded-lg border border-zinc-700 bg-zinc-900/60 overflow-hidden"
      data-testid={testId ?? 'reasoning-progress'}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="flex w-full items-center justify-between px-4 py-2 text-xs text-zinc-400 hover:bg-zinc-800/40 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-500"
        aria-expanded={!collapsed}
        aria-controls="reasoning-content"
        data-testid="reasoning-toggle"
      >
        <span className="flex items-center gap-2">
          {/* Pulsing dot while streaming */}
          {isStreaming && (
            <span
              className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse"
              aria-label="streaming"
              data-testid="reasoning-streaming-dot"
            />
          )}
          <span className="font-semibold text-violet-300" data-testid="reasoning-header-label">
            {isStreaming ? 'Thinking…' : 'Reasoning'}
          </span>
          <span className="text-zinc-600" data-testid="reasoning-token-count">
            {tokenCount.toLocaleString()} tokens
          </span>
          {(isStreaming || elapsedMs > 0) && (
            <span className="text-zinc-600" data-testid="reasoning-elapsed">
              {elapsedSec}s
            </span>
          )}
        </span>

        {/* Chevron */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className={`h-3 w-3 transition-transform ${collapsed ? '' : 'rotate-180'}`}
          aria-hidden="true"
        >
          <path d="M2 4l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* Collapsed affordance label */}
      {collapsed && isLong && (
        <div
          className="px-4 py-1 text-[10px] text-zinc-600 italic cursor-pointer hover:text-zinc-500"
          onClick={() => setCollapsed(false)}
          aria-hidden="true"
          data-testid="reasoning-collapse-label"
        >
          {collapseLabel} ⌄
        </div>
      )}

      {/* Content */}
      {!collapsed && (
        <div
          id="reasoning-content"
          className="px-4 pb-3 pt-0 text-xs font-mono text-zinc-400 whitespace-pre-wrap leading-relaxed border-t border-zinc-800"
          data-testid="reasoning-content"
          aria-live={isStreaming ? 'polite' : undefined}
        >
          {text}
        </div>
      )}
    </div>
  )
}
