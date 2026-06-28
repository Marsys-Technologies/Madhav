'use client'

import { useEffect, useState } from 'react'

interface CockpitStatus {
  writers: string | null
  queue: string | null
  build: 'running' | 'idle' | null
}

export function useCockpitStatus(): CockpitStatus {
  const [status, setStatus] = useState<CockpitStatus>({ writers: null, queue: null, build: null })

  useEffect(() => {
    const controller = new AbortController()

    const fetch_ = async () => {
      try {
        const r = await fetch('/api/cockpit/status', { credentials: 'include', signal: controller.signal })
        if (!r.ok || controller.signal.aborted) return
        const body = await r.json()
        if (controller.signal.aborted) return
        setStatus(body.data)
      } catch (e) {
        if ((e as Error)?.name === 'AbortError') return
        // keep last known
      }
    }

    fetch_()
    const t = setInterval(fetch_, 30_000)
    return () => {
      controller.abort()
      clearInterval(t)
    }
  }, [])

  return status
}
