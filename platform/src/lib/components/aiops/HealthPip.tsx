'use client'

import { useEffect, useState } from 'react'

import type { AiopsModelHealthStatus } from '@/lib/db/schema/aiops'
type HealthStatus = AiopsModelHealthStatus

interface HealthData {
  status:        HealthStatus
  latency_ms:    number | null
  last_probe_at: string | null
  last_error:    string | null
}

interface HealthPipProps {
  modelId: string
}

function formatTimeAgo(isoString: string | null): string {
  if (!isoString) return 'never'
  const diff = Date.now() - new Date(isoString).getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return 'just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function pipColor(health: HealthData | null): string {
  if (!health || !health.last_probe_at) return '#6b7280' // gray — never probed
  const hoursSince = (Date.now() - new Date(health.last_probe_at).getTime()) / (1000 * 60 * 60)
  if (health.status === 'fail' || health.status === 'timeout') return '#ef4444' // red
  if (hoursSince > 7 * 24) return '#6b7280' // gray — stale
  if (hoursSince > 24) return '#eab308' // yellow — aging
  return '#22c55e' // green — fresh pass
}

function pipLabel(health: HealthData | null): string {
  if (!health || !health.last_probe_at) return 'Never probed'
  const timeAgo = formatTimeAgo(health.last_probe_at)
  const latency = health.latency_ms != null ? ` · ${health.latency_ms}ms` : ''
  const status = health.status
  return `${status} · ${timeAgo}${latency}`
}

export function HealthPip({ modelId }: HealthPipProps) {
  const [health, setHealth] = useState<HealthData | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch(`/api/admin/aiops/health?model_id=${encodeURIComponent(modelId)}`)
      .then(r => r.json())
      .then((d: { rows: HealthData[] }) => {
        if (!cancelled && d.rows?.[0]) setHealth(d.rows[0])
      })
      .catch(() => null)
    return () => { cancelled = true }
  }, [modelId])

  const color = pipColor(health)
  const label = pipLabel(health)

  return (
    <span
      role="img"
      aria-label={`Model health: ${label}`}
      title={label}
      className="inline-block h-2 w-2 rounded-full shrink-0"
      style={{ backgroundColor: color, boxShadow: `0 0 4px ${color}60` }}
    />
  )
}
