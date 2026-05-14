'use client'

import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getModelMeta } from '@/lib/models/registry'
import type { ChatLifecycleState } from '@/lib/hooks/useChatLifecycle'

interface Props {
  state: ChatLifecycleState
  reasoningText: string
  /** Legacy fallback — used when modelId is not provided. Default true. */
  modelHasReasoning?: boolean
  /** CO.3: look up reasoning_via from model registry. Preferred over modelHasReasoning. */
  modelId?: string
  /** CO.3: override the default collapse-after-complete behaviour. */
  collapsedByDefault?: boolean
  className?: string
}

/**
 * ReasoningSlot — stable DOM slot anchored from query submission.
 *
 * CO.1: structural stub anchoring the slot at submission time.
 * CO.3: model-aware gate (Bug 3.4) + "Thought for Xs" label (Bug 3.3):
 *   - reasoning_via 'none' → slot collapses to nothing immediately
 *   - 'native' / 'markers' → expandable card; "Thinking…" during stream,
 *     "Thought for Xs" collapsed header after composing
 *
 * Stable DOM position from submission → no layout shift (Bug 3.3).
 * Model-aware gate → no false-positive reasoning panels (Bug 3.4).
 */
export function ReasoningSlot({
  state,
  reasoningText,
  modelHasReasoning = true,
  modelId,
  collapsedByDefault,
  className,
}: Props) {
  const isReasoning = state === 'reasoning'
  const isDone = state === 'composing' || state === 'complete'

  // CO.3: model-aware capability check via registry.
  const meta = modelId ? getModelMeta(modelId) : null
  const reasoningCapable = meta
    ? meta.quirks.reasoning_via !== 'none'
    : modelHasReasoning

  // Track duration for "Thought for Xs" label.
  const startRef = useRef<number | null>(null)
  const [durationSec, setDurationSec] = useState<number | null>(null)

  useEffect(() => {
    if (isReasoning) {
      startRef.current = Date.now()
      setDurationSec(null)
    } else if (isDone && startRef.current !== null) {
      const elapsed = (Date.now() - startRef.current) / 1000
      setDurationSec(Math.round(elapsed * 10) / 10)
      startRef.current = null
    }
  }, [isReasoning, isDone])

  // Sync expansion: open while streaming, collapsed after completion.
  const defaultExpanded = collapsedByDefault !== undefined ? !collapsedByDefault : !isDone
  const [expanded, setExpanded] = useState(defaultExpanded)

  useEffect(() => {
    if (isDone) setExpanded(false)
    else if (isReasoning) setExpanded(true)
  }, [isDone, isReasoning])

  if (!reasoningCapable) return null
  if (state === 'idle' || state === 'queued' || state === 'planning' || state === 'retrieving') {
    return null
  }
  if (!isReasoning && !isDone && reasoningText === '') return null

  const headerLabel = isReasoning
    ? 'Thinking…'
    : durationSec !== null
      ? `Thought for ${durationSec}s`
      : reasoningText
        ? 'Reasoned'
        : null

  if (!isReasoning && !reasoningText && !headerLabel) return null

  return (
    <div className={cn('mx-auto w-full max-w-4xl px-4 py-1', className)}>
      <div className="rounded-md border border-border/40 bg-muted/20">
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="flex w-full items-center gap-2 px-3 py-2 text-left"
          aria-expanded={expanded}
          aria-label="Reasoning — click to expand"
        >
          <span
            className={cn(
              'inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--brand-gold)]/70',
              isReasoning && 'animate-pulse',
            )}
            aria-hidden="true"
          />
          <span className="flex-1 text-[11px] text-muted-foreground">
            {headerLabel ?? 'Reasoning…'}
          </span>
          {expanded
            ? <ChevronUp className="h-3 w-3 shrink-0 text-muted-foreground/60" />
            : <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground/60" />
          }
        </button>

        {expanded && (
          <div className="max-h-48 overflow-y-auto border-t border-border/30 px-3 py-2">
            {reasoningText ? (
              <pre className="whitespace-pre-wrap text-[11px] text-muted-foreground/80 leading-relaxed">
                {reasoningText}
              </pre>
            ) : (
              <p className="text-[11px] text-muted-foreground/60 italic">Reasoning…</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
