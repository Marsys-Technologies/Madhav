'use client'

import { useEffect, useState } from 'react'

interface DataReadiness {
  chart_id: string
  build_status: 'none' | 'partial' | 'complete' | 'failed'
  ready: string[]
  missing: string[]
  partial_count: number
  total_count: number
}

type Readiness =
  | { status: 'loading' | 'unavailable' }
  | { status: 'available'; data: DataReadiness }

function isDataReadiness(value: unknown, chartId: string): value is DataReadiness {
  if (typeof value !== 'object' || value === null) return false
  const { chart_id, build_status, ready, missing, partial_count, total_count } = value as Record<string, unknown>
  if (chart_id !== chartId || !Array.isArray(ready) || !Array.isArray(missing)
    || !ready.every(asset => typeof asset === 'string') || !missing.every(asset => typeof asset === 'string')
    || partial_count !== ready.length || total_count !== ready.length + missing.length) return false

  switch (build_status) {
    case 'complete': return missing.length === 0
    case 'partial': return ready.length > 0 && missing.length > 0
    case 'none':
    case 'failed': return ready.length === 0
    default: return false
  }
}

export function useChartDataReadiness(chartId: string): Readiness {
  const [snapshot, setSnapshot] = useState<{ request: { chartId: string }; readiness: Readiness }>(
    () => ({ request: { chartId }, readiness: { status: 'loading' } }),
  )
  const { request, readiness } = snapshot

  useEffect(() => {
    const controller = new AbortController()

    function publish(readiness: Readiness) {
      if (controller.signal.aborted) return
      setSnapshot(current => current.request === request ? { request, readiness } : current)
    }

    async function load() {
      try {
        const response = await fetch(`/api/build/data-readiness?chart_id=${encodeURIComponent(request.chartId)}`, {
          signal: controller.signal,
        })
        if (!response.ok) {
          publish({ status: 'unavailable' })
          return
        }
        const body: unknown = await response.json()
        publish(isDataReadiness(body, request.chartId)
          ? { status: 'available', data: body }
          : { status: 'unavailable' })
      } catch {
        publish({ status: 'unavailable' })
      }
    }

    void load()
    return () => controller.abort()
  }, [request])

  if (request.chartId !== chartId) {
    // Reset before children render, even when switching back to a chart whose request was still pending.
    const next: Readiness = { status: 'loading' }
    setSnapshot({ request: { chartId }, readiness: next })
    return next
  }
  return readiness
}

interface Props {
  chartId: string
  readiness: Readiness
  buildPreparationHref?: string
}

const bannerClass = 'mb-4 rounded-lg border border-brand-warn/30 bg-brand-warn/10 px-4 py-3 text-sm text-brand-warn'

export function PartialDataBanner({ chartId, readiness, buildPreparationHref }: Props) {
  if (readiness.status === 'unavailable') {
    return <div className={bannerClass} role="status">Chart preparation status is unavailable.</div>
  }
  if (readiness.status !== 'available' || readiness.data.missing.length === 0) return null

  const { missing, total_count, build_status } = readiness.data
  const preparationHref = `/clients/${encodeURIComponent(chartId)}/nirmana`

  return (
    <div className={bannerClass} role="status">
      <span className="font-medium">{build_status === 'partial' ? 'Chart partially built.' : 'Chart preparation is incomplete.'}</span>
      {' '}{missing.length} of {total_count} assets pending
      — some questions may not have complete answers.
      {buildPreparationHref === preparationHref && (
        <a href={preparationHref} className="ml-3 underline hover:text-brand-gold-1">
          Open Chart Preparation
        </a>
      )}
    </div>
  )
}
