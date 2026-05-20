'use client'

export function SidebarSkeleton() {
  return (
    <div aria-hidden="true" data-testid="v2-sidebar-skeleton" className="px-2 py-1">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-2 px-1 py-2">
          <div className="h-7 w-7 rounded-full bg-zinc-700/60 animate-pulse shrink-0" />
          <div className="flex-1 min-w-0 space-y-1.5">
            <div className="h-2 rounded bg-zinc-700/60 animate-pulse w-4/5" />
            <div className="h-2 rounded bg-zinc-700/60 animate-pulse w-3/5" />
          </div>
        </div>
      ))}
    </div>
  )
}
