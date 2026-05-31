'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'

interface ActiveBuild { build_id: string; chart_id: string; status: string }

export function BuildButton({ chartId }: { chartId: string }) {
  const [active, setActive] = useState<ActiveBuild | null>(null)
  const [starting, setStarting] = useState(false)

  async function poll() {
    const res = await fetch('/api/build/active').catch(() => null)
    if (!res?.ok) return
    const data = (await res.json()) as ActiveBuild[]
    setActive(data.find((b) => b.chart_id === chartId) ?? null)
  }

  useEffect(() => {
    void poll()
    const id = setInterval(() => void poll(), 10_000)
    return () => clearInterval(id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartId])

  async function start() {
    setStarting(true)
    try {
      const res = await fetch('/api/build/start', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId }),
      })
      const body = (await res.json()) as { build_id?: string; status?: string; error?: string }
      if ((res.ok || res.status === 409) && body.build_id) {
        setActive({ build_id: body.build_id, chart_id: chartId, status: body.status ?? 'queued' })
      }
    } finally {
      setStarting(false)
    }
  }

  if (active) {
    return (
      <span className="text-sm text-muted-foreground" data-testid="build-button-active">
        Build {active.status} —{' '}
        <button className="underline" onClick={() => void poll()}>refresh</button>
      </span>
    )
  }

  return (
    <Button size="sm" disabled={starting} onClick={() => void start()} data-testid="build-button">
      {starting ? 'Starting…' : 'Build'}
    </Button>
  )
}
