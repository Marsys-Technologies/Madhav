'use client'

import { useEffect, useState } from 'react'

interface DataReadiness {
  build_status: string
  ready: string[]
  missing: string[]
  total_count: number
}

interface Props {
  chartId: string
  /** Optional callback — receives the ready asset list once fetched. */
  onReadyAssets?: (readyAssets: string[]) => void
}

export function PartialDataBanner({ chartId, onReadyAssets }: Props) {
  const [readiness, setReadiness] = useState<DataReadiness | null>(null)

  useEffect(() => {
    fetch(`/api/build/data-readiness?chart_id=${chartId}`)
      .then(r => r.json())
      .then((data: DataReadiness) => {
        setReadiness(data)
        onReadyAssets?.(data.ready)
      })
      .catch(() => null)
  }, [chartId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!readiness || readiness.missing.length === 0) return null

  function handleBuildNow() {
    fetch('/api/build/continue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chart_id: chartId }),
    }).catch(() => null)
  }

  return (
    <div className="mb-4 rounded-lg border border-brand-warn/30 bg-brand-warn/10 px-4 py-3 text-sm text-brand-warn">
      <span className="font-medium">Chart partially built.</span>
      {' '}{readiness.missing.length} of {readiness.total_count} assets pending
      — some questions may not have complete answers.
      <button
        type="button"
        className="ml-3 underline hover:text-brand-gold-1"
        onClick={handleBuildNow}
      >
        Build now
      </button>
    </div>
  )
}
