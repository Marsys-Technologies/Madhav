'use client'

import { useEffect } from 'react'
import { toast } from 'sonner'

export interface RecentBuild {
  build_id: string
  chart_id: string
  chart_name: string | null
  status: 'complete' | 'failed'
  finished_at: string
  ayanamshas: string[]
  error_summary: string | null
}

const SEEN_KEY = 'marsys_seen_builds'
const MAX_SEEN = 100

function getSeenIds(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) ?? '[]') as string[])
  } catch {
    return new Set()
  }
}

function markSeen(ids: string[]): void {
  try {
    const seen = getSeenIds()
    for (const id of ids) seen.add(id)
    const trimmed = [...seen].slice(-MAX_SEEN)
    localStorage.setItem(SEEN_KEY, JSON.stringify(trimmed))
  } catch {
    // localStorage unavailable — silent
  }
}

/**
 * BuildCompleteToast
 *
 * Mounts once per page load, fetches /api/build/recent, and fires a sonner
 * toast for every completed/failed build the user has not yet seen.
 * "Seen" state is tracked in localStorage by build_id (up to 100 entries).
 *
 * No polling — it is a single check on mount plus a 2-second deferred retry
 * to capture builds that complete during the initial page hydration window.
 */
export default function BuildCompleteToast() {
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/api/build/recent')
        if (!res.ok) return

        const builds: RecentBuild[] = await res.json()
        const seen = getSeenIds()
        const unseen = builds.filter((b) => !seen.has(b.build_id))

        if (unseen.length === 0) return

        // Mark all unseen as seen before showing (avoids double-fire on re-render)
        markSeen(unseen.map((b) => b.build_id))

        for (const build of unseen) {
          const label = build.chart_name ?? 'Chart'
          const ayas =
            build.ayanamshas.length > 0 ? ` — ${build.ayanamshas.join(', ')}` : ''
          const message =
            build.status === 'complete'
              ? `${label} build complete${ayas}`
              : `${label} build failed${ayas}`

          const viewUrl = `/clients/${build.chart_id}/build`

          if (build.status === 'complete') {
            toast.success(message, {
              id: build.build_id,
              duration: 8000,
              action: {
                label: 'View',
                onClick: () => {
                  window.location.href = viewUrl
                },
              },
            })
          } else {
            toast.error(message, {
              id: build.build_id,
              duration: 10000,
              description: build.error_summary ?? undefined,
              action: {
                label: 'View',
                onClick: () => {
                  window.location.href = viewUrl
                },
              },
            })
          }
        }
      } catch {
        // silent — non-critical notification
      }
    }

    void check()
    const timer = setTimeout(() => void check(), 2000)
    return () => clearTimeout(timer)
  }, [])

  // Renders nothing — all output goes through Sonner's <Toaster />
  return null
}
