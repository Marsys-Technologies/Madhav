/**
 * Panchang loading skeleton — shown while the server-side page fetches from the sidecar.
 * Matches the Primary Strip layout (6 anga rows) per §4.2 mockup.
 */
export default function PanchangLoading() {
  return (
    <div className="relative min-h-full overflow-hidden" aria-busy="true" aria-label="Loading Panchang">
      {/* Header skeleton */}
      <div className="border-b border-[rgba(212,175,55,0.12)] bg-[rgba(28,28,26,0.60)] px-6 py-4">
        <div className="mx-auto max-w-4xl flex items-center gap-4 flex-wrap">
          <div className="h-9 w-48 rounded-md bg-[rgba(212,175,55,0.08)] animate-pulse" />
          <div className="h-9 w-44 rounded-md bg-[rgba(212,175,55,0.08)] animate-pulse" />
          <div className="h-9 w-36 rounded-md bg-[rgba(212,175,55,0.08)] animate-pulse opacity-50" />
        </div>
      </div>

      {/* Primary Strip skeleton — 6 rows */}
      <div className="mx-auto max-w-4xl px-4 py-6">
        <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center justify-between px-5 py-4 border-b border-[rgba(212,175,55,0.08)] last:border-0"
            >
              <div className="flex items-center gap-3">
                <div className="h-4 w-20 rounded bg-[rgba(212,175,55,0.10)] animate-pulse" />
                <div className="h-5 w-32 rounded bg-[rgba(212,175,55,0.14)] animate-pulse" />
              </div>
              <div className="h-4 w-16 rounded bg-[rgba(212,175,55,0.08)] animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
