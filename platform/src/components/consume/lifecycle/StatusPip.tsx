'use client'

import { cn } from '@/lib/utils'
import type { ChatLifecycleState } from '@/lib/hooks/useChatLifecycle'

interface Props {
  state: ChatLifecycleState
  className?: string
}

const STATUS_LABELS: Partial<Record<ChatLifecycleState, string>> = {
  queued: 'Queuing request…',
  planning: 'Planning the response…',
  retrieving: 'Retrieving context…',
  reasoning: 'Reasoning…',
  tool_calling: 'Consulting sources…',
  composing: 'Composing answer…',
}

/**
 * StatusPip — inline processing indicator driven by ChatLifecycleState.
 *
 * Renders for processing states (queued → composing). Dissolves at complete,
 * error, cancelled, or idle. Uses aria-live="polite" so screen readers
 * announce stage changes without interrupting ongoing reading.
 */
export function StatusPip({ state, className }: Props) {
  const label = STATUS_LABELS[state]

  if (!label) return null

  return (
    <div
      className={cn('mx-auto w-full max-w-4xl px-4 py-2', className)}
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span
          className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--brand-gold)]/70 animate-pulse"
          aria-hidden="true"
        />
        <span>{label}</span>
      </div>
    </div>
  )
}
