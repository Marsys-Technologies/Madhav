'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ChatLifecycleState } from '@/lib/hooks/useChatLifecycle'

interface Props {
  state: ChatLifecycleState
  reasoningText: string
  /** Present only when the model has reasoning_via !== 'none'. CO.3 gates this. */
  modelHasReasoning?: boolean
  className?: string
}

/**
 * ReasoningSlot — stable DOM slot anchored from query submission.
 *
 * CO.1: structural stub. Renders the accumulated reasoningText when present.
 * CO.3 wires full reasoning_delta stream and auto-collapse on composing.
 *
 * The slot is present in the DOM tree regardless of content (stable DOM
 * position — no layout shift). When no reasoning has arrived yet, renders
 * a "Reasoning…" placeholder during the reasoning state.
 */
export function ReasoningSlot({ state, reasoningText, modelHasReasoning = true, className }: Props) {
  const [expanded, setExpanded] = useState(true)

  const isReasoning = state === 'reasoning'
  const isPostReasoning = state === 'composing' || state === 'complete' || state === 'cancelled'

  if (!modelHasReasoning) return null
  if (state === 'idle' || state === 'queued' || state === 'planning' || state === 'retrieving') {
    return null
  }
  if (!isReasoning && !isPostReasoning && reasoningText === '') return null

  const showPlaceholder = isReasoning && reasoningText === ''
  const displayText = showPlaceholder ? 'Reasoning…' : reasoningText.split('\n').at(-1) ?? reasoningText

  return (
    <div className={cn('mx-auto w-full max-w-4xl px-4 py-2', className)}>
      <div className="rounded-md border border-border/60 bg-muted/30 px-3 py-2 transition-colors">
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="flex w-full items-center gap-2 text-left"
          aria-expanded={expanded}
          aria-controls="reasoning-slot-content"
          disabled={reasoningText === ''}
        >
          <span
            className={cn(
              'inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--brand-gold)]/70',
              isReasoning && 'animate-pulse',
            )}
            aria-hidden="true"
          />
          <span className="flex-1 truncate text-xs text-muted-foreground">
            {displayText}
          </span>
          {reasoningText !== '' && (
            <span className="shrink-0 text-muted-foreground/70">
              {expanded ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </span>
          )}
        </button>
        {expanded && reasoningText !== '' && (
          <div
            id="reasoning-slot-content"
            className="mt-2 border-t border-border/40 pt-2 text-[11px] text-muted-foreground/80 leading-relaxed whitespace-pre-wrap"
          >
            {reasoningText}
          </div>
        )}
      </div>
    </div>
  )
}
