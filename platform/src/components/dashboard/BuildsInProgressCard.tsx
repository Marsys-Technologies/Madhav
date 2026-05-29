'use client'

import { useEffect, useState, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ProgressBar } from '@/components/build/ProgressBar'

export interface ActiveBuild {
  build_id: string
  chart_id: string
  chart_name: string | null
  ayanamshas: string[]
  status: 'queued' | 'running' | 'cancelling'
  queued_at: string
  started_at: string | null
  steps_complete: number
  steps_total: number
  progress_pct: number
}

const AYANAMSHA_SHORT: Record<string, string> = {
  lahiri: 'L',
  true_chitra: 'TC',
  kp: 'KP',
  raman: 'R',
  surya_siddhanta: 'SS',
}

function relativeTime(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  if (diffSecs < 60) return `${diffSecs}s ago`
  const diffMins = Math.floor(diffSecs / 60)
  if (diffMins < 60) return `${diffMins} min ago`
  const diffHours = Math.floor(diffMins / 60)
  return `${diffHours}h ago`
}

function statusVariant(
  status: ActiveBuild['status']
): 'default' | 'secondary' | 'outline' {
  if (status === 'running') return 'default'
  if (status === 'cancelling') return 'outline'
  return 'secondary'
}

export default function BuildsInProgressCard() {
  const [builds, setBuilds] = useState<ActiveBuild[]>([])
  const [loading, setLoading] = useState(true)
  const [cancellingIds, setCancellingIds] = useState<Set<string>>(new Set())

  const fetchBuilds = useCallback(async () => {
    try {
      const res = await fetch('/api/build/active')
      if (res.ok) {
        const data: ActiveBuild[] = await res.json()
        setBuilds(data)
      }
    } catch {
      // silent fail — polling will retry
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchBuilds()
    const interval = setInterval(() => void fetchBuilds(), 5000)
    return () => clearInterval(interval)
  }, [fetchBuilds])

  const handleCancel = async (buildId: string) => {
    if (!confirm('Cancel this build?')) return
    setCancellingIds((prev) => new Set([...prev, buildId]))
    try {
      await fetch(`/api/build/cancel/${buildId}`, { method: 'POST' })
      await fetchBuilds()
    } finally {
      setCancellingIds((prev) => {
        const s = new Set(prev)
        s.delete(buildId)
        return s
      })
    }
  }

  if (loading) {
    return (
      <Card data-testid="builds-in-progress-card">
        <CardHeader>
          <CardTitle>Builds In Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground" data-testid="builds-loading">
            Loading builds…
          </p>
        </CardContent>
      </Card>
    )
  }

  if (builds.length === 0) {
    return (
      <Card data-testid="builds-in-progress-card">
        <CardHeader>
          <CardTitle>Builds In Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground" data-testid="builds-empty">
            No builds running
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card data-testid="builds-in-progress-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Builds In Progress
          <Badge variant="secondary" data-testid="builds-count">
            {builds.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {builds.map((build) => {
          const isCancelling =
            cancellingIds.has(build.build_id) || build.status === 'cancelling'
          const startTime = build.started_at ?? build.queued_at

          return (
            <div
              key={build.build_id}
              className="border rounded-lg p-3 space-y-2"
              data-testid={`build-row-${build.build_id}`}
            >
              {/* Header row: chart name + status + cancel */}
              <div className="flex justify-between items-start gap-2">
                <div className="min-w-0 flex-1">
                  <p
                    className="font-medium text-sm truncate"
                    data-testid={`build-chart-name-${build.build_id}`}
                  >
                    {build.chart_name ?? 'Unknown chart'}
                  </p>

                  {/* Ayanamsha badges */}
                  {build.ayanamshas.length > 0 && (
                    <div
                      className="flex flex-wrap gap-1 mt-1"
                      data-testid={`build-ayanamshas-${build.build_id}`}
                    >
                      {build.ayanamshas.map((a) => (
                        <Badge key={a} variant="outline" className="text-xs px-1 py-0">
                          {AYANAMSHA_SHORT[a] ?? a}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Badge
                    variant={statusVariant(build.status)}
                    data-testid={`build-status-${build.build_id}`}
                  >
                    {build.status}
                  </Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={isCancelling}
                    onClick={() => void handleCancel(build.build_id)}
                    data-testid={`build-cancel-${build.build_id}`}
                  >
                    {isCancelling ? 'Cancelling…' : 'Cancel'}
                  </Button>
                </div>
              </div>

              {/* Progress bar */}
              <ProgressBar
                percent={build.progress_pct}
                tone={build.status === 'running' ? 'active' : 'default'}
              />

              {/* Footer: steps + start time */}
              <div className="flex justify-between text-xs text-muted-foreground">
                <span data-testid={`build-steps-${build.build_id}`}>
                  {build.steps_complete}/{build.steps_total} assets
                </span>
                <span data-testid={`build-time-${build.build_id}`}>
                  {relativeTime(startTime)}
                </span>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
