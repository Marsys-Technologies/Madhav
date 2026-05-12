'use client'

import { cn } from '@/lib/utils'
import type { CorrectionEvent } from '@/types/sse_events'

interface Props {
  correction: CorrectionEvent
  className?: string
}

/**
 * CorrectionNotice — Gate III §8.
 *
 * Compact, polite-but-firm callout above the answer when synthesis emitted
 * a ‹correction› marker (the user's query contained a factual or
 * methodological error).
 */
export function CorrectionNotice({ correction, className }: Props) {
  return (
    <div
      role="note"
      aria-label="Factual correction"
      className={cn(
        'mb-3 border-l-2 border-amber-500/60 bg-amber-500/5 px-3 py-2 text-sm',
        className,
      )}
    >
      <p>
        <span className="font-medium text-amber-200">Note:</span>{' '}
        <span className="text-foreground/90">{correction.corrected_claim}</span>
      </p>
      {correction.original_claim && (
        <p className="mt-1 text-xs text-muted-foreground">
          You wrote: <em>&ldquo;{correction.original_claim}&rdquo;</em>
        </p>
      )}
      {correction.classical_source && (
        <p className="mt-0.5 text-[11px] text-muted-foreground/70">
          Source: {correction.classical_source}
        </p>
      )}
    </div>
  )
}
