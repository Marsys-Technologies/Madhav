'use client'

/**
 * LiveReasoningCard — Gate III.
 *
 * The ambient, collapsible reasoning surface that sits above the streaming
 * answer for each in-flight assistant turn.
 *
 * Behavior:
 *  - No steps + streaming → pulsing dot + "Thinking…"
 *  - 1+ step + streaming → most-recent step text with pulsing dot
 *  - 1+ step + finished → most-recent step text (no pulse)
 *  - Click → expand full chronological list of steps
 *
 * Vocabulary: classical Jyotish only. Steps are produced upstream by
 * `parseMarkers` (synthesis phase) and / or `narratePipelineStep` (pipeline
 * phase). This component does no translation itself.
 */

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ReasoningStepEvent } from '@/types/sse_events'

export interface LiveReasoningCardProps {
  reasoningSteps: ReasoningStepEvent[]
  isStreaming: boolean
  defaultExpanded?: boolean
  className?: string
}

export function LiveReasoningCard({
  reasoningSteps,
  isStreaming,
  defaultExpanded = false,
  className,
}: LiveReasoningCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  const latest = reasoningSteps[reasoningSteps.length - 1] ?? null
  const showThinking = isStreaming && reasoningSteps.length === 0

  if (!isStreaming && reasoningSteps.length === 0) {
    // After streaming finished with no reasoning emitted — render nothing.
    return null
  }

  const displayText = showThinking ? 'Thinking…' : (latest?.text ?? '')

  return (
    <div
      className={cn(
        'mx-auto w-full max-w-4xl px-4 py-2',
        className,
      )}
    >
      <div
        className={cn(
          'rounded-md border border-border/60 bg-muted/30 px-3 py-2',
          'transition-colors',
        )}
      >
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="flex w-full items-center gap-2 text-left"
          aria-expanded={expanded}
          aria-controls="live-reasoning-list"
          disabled={reasoningSteps.length === 0}
        >
          <span
            className={cn(
              'inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--brand-gold)]/70',
              isStreaming && 'animate-pulse',
            )}
            aria-hidden="true"
          />
          <span className="flex-1 truncate text-xs text-muted-foreground">
            {displayText}
          </span>
          {reasoningSteps.length > 0 && (
            <span className="shrink-0 text-muted-foreground/70">
              {expanded ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </span>
          )}
        </button>
        {expanded && reasoningSteps.length > 0 && (
          <ul
            id="live-reasoning-list"
            aria-labelledby="live-reasoning-list"
            className="mt-2 space-y-1 border-t border-border/40 pt-2"
          >
            {reasoningSteps.map((step, i) => (
              <li
                key={`${step.timestamp}-${i}`}
                className={cn(
                  'flex items-baseline gap-2 text-[11px] text-muted-foreground/90',
                  step.phase === 'synthesis' && 'pl-2',
                )}
              >
                <span className="font-mono text-[9px] text-muted-foreground/50 shrink-0">
                  {step.phase === 'pipeline' ? '◇' : '◆'}
                </span>
                <span className="leading-tight">{step.text}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
