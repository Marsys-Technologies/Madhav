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
    const fetch_ = async () => {
      try {
        const r = await fetch('/api/cockpit/status', { credentials: 'include', cache: 'no-store' })
        if (!r.ok) return
        const body = await r.json()
        setStatus(body.data)
      } catch {
        // keep last known
      }
    }
    fetch_()
    const t = setInterval(fetch_, 30_000)
    return () => clearInterval(t)
  }, [])

  return status
}
