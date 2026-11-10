export default function TimelineLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <p role="status" className="mb-6 text-sm text-muted-foreground">Loading life events…</p>
      <div aria-hidden="true" className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4 rounded-lg border border-border p-4">
            <div className="mt-1 h-4 w-16 shrink-0 rounded bg-muted motion-safe:animate-pulse" />
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <div className="h-4 w-48 max-w-full rounded bg-muted motion-safe:animate-pulse" />
              <div className="h-3 w-full rounded bg-muted motion-safe:animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
