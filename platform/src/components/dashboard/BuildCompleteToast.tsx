'use client'

// /api/build/recent was decommissioned (410 Gone).
// TODO(axis-A): restore once replaced with /api/cockpit/runs?state=completed&since=<window>

export interface RecentBuild {
  build_id: string
  chart_id: string
  chart_name: string | null
  status: 'complete' | 'failed'
  finished_at: string
  ayanamshas: string[]
  error_summary: string | null
}

// Component is a no-op stub until the backing endpoint is replaced.
export default function BuildCompleteToast() {
  return null
}
