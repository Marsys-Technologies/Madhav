'use client'

interface EmptyObservatoryStateProps {
  /** The date range currently selected — shown in the message so users
   *  know the filter is active and data might exist outside the range. */
  dateRangeLabel?: string
}

export function EmptyObservatoryState({ dateRangeLabel }: EmptyObservatoryStateProps) {
  return (
    <div
      data-testid="observatory-empty-state"
      className="flex flex-col items-center justify-center gap-4 rounded-lg border border-[rgba(212,175,55,0.18)] bg-[rgba(212,175,55,0.04)] px-8 py-14 text-center"
    >
      <div className="text-3xl opacity-40">◎</div>
      <div>
        <p className="text-sm font-medium text-[rgba(212,175,55,0.85)]">
          No LLM calls recorded{dateRangeLabel ? ` in the last ${dateRangeLabel}` : ''}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Every query you send through the portal is tracked here automatically.
        </p>
      </div>
      <div className="mt-2 rounded border border-[rgba(212,175,55,0.12)] bg-background/60 px-5 py-3 text-left text-xs text-muted-foreground">
        <p className="mb-1 font-semibold text-[rgba(212,175,55,0.6)]">If you&apos;ve sent queries and still see this:</p>
        <ol className="list-decimal space-y-0.5 pl-4">
          <li>Check that the pricing seed has been applied to the database</li>
          <li>Verify <code className="rounded bg-muted px-1 py-0.5">MARSYS_FLAG_OBSERVATORY_ENABLED=true</code></li>
          <li>Open the Events tab — partial rows may appear there</li>
          <li>Try a wider date range — data may fall outside the current window</li>
        </ol>
      </div>
    </div>
  )
}
