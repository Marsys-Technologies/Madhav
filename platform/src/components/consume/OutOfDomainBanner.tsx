'use client'

import { cn } from '@/lib/utils'
import type { OutOfDomainEvent } from '@/types/sse_events'

interface Props {
  event: OutOfDomainEvent
  className?: string
}

export function OutOfDomainBanner({ event, className }: Props) {
  return (
    <div
      role="status"
      className={cn(
        'mb-3 rounded-md border border-border/60 bg-muted/40 px-3 py-2 text-xs text-muted-foreground',
        className,
      )}
    >
      This question is outside the Jyotish scope of this instrument — answering briefly.
      {event.reason ? <span className="ml-1 opacity-70">({event.reason})</span> : null}
    </div>
  )
}
