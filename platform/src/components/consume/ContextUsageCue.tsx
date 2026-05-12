'use client'

import { cn } from '@/lib/utils'
import type { ContextUsageEvent } from '@/types/sse_events'

interface Props {
  usage: ContextUsageEvent
  className?: string
}

function modeLabel(usage: ContextUsageEvent): string {
  if (usage.mode === 'independent' || usage.prior_turns_used === 0) return 'Independent query'
  if (usage.mode === 'continuation') return `${usage.prior_turns_used} prior turn (continuation)`
  return `${usage.prior_turns_used} prior turn${usage.prior_turns_used > 1 ? 's' : ''} (comprehension only)`
}

/**
 * ContextUsageCue — Gate III §8.
 *
 * Tiny muted chip in the answer header that tells the native how the
 * planner sliced prior turns for this query.
 */
export function ContextUsageCue({ usage, className }: Props) {
  return (
    <span
      title={usage.reason}
      className={cn(
        'inline-flex items-center rounded border border-border/60 bg-muted/30 px-1.5 py-0.5',
        'text-[10px] font-medium text-muted-foreground/80',
        className,
      )}
    >
      {modeLabel(usage)}
    </span>
  )
}
