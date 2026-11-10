export default function DashboardLoading() {
  return (
    <div className="container mx-auto py-8 px-4" role="status" aria-label="Loading charts">
      <div className="flex items-center justify-between mb-6">
        <div className="h-8 w-24 bg-muted rounded motion-safe:animate-pulse" />
        <div className="h-9 w-32 bg-muted rounded motion-safe:animate-pulse" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="border rounded-lg p-4 space-y-3">
            <div className="h-5 w-32 bg-muted rounded motion-safe:animate-pulse" />
            <div className="h-3 w-48 bg-muted rounded motion-safe:animate-pulse" />
            <div className="flex gap-2 pt-1">
              <div className="h-8 flex-1 bg-muted rounded motion-safe:animate-pulse" />
              <div className="h-8 flex-1 bg-muted rounded motion-safe:animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
