'use client'

export function HeaderSkeleton() {
  return (
    <div aria-hidden="true" data-testid="v2-header-skeleton" className="min-w-0 flex-1 px-1.5">
      <div className="h-3.5 rounded bg-zinc-700/60 animate-pulse w-32" />
      <div className="mt-1 h-2 rounded bg-zinc-700/60 animate-pulse w-24" />
    </div>
  )
}
