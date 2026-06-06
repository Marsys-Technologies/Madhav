'use client'

import { useState, useEffect } from 'react'

interface ChartContext {
  chartId: string
  chartName: string | null
  birthDate: string | null
  birthPlace: string | null
  ayanamshaSet: string[]
  lifeSpanYears: number
}

export function useChartContext(chartId: string): ChartContext {
  const [chartName, setChartName] = useState<string | null>(null)
  const [birthDate, setBirthDate] = useState<string | null>(null)
  const [birthPlace, setBirthPlace] = useState<string | null>(null)

  useEffect(() => {
    console.log('[CC] effect start, chartId=', chartId)
    const controller = new AbortController()
    let cancelled = false
    ;(async () => {
      try {
        console.log('[CC] fetching /api/charts/' + chartId)
        const r = await fetch(`/api/charts/${chartId}`, {
          credentials: 'include',
          signal: controller.signal,
        })
        console.log('[CC] fetch returned, ok=', r.ok, 'cancelled=', cancelled)
        if (cancelled) { console.log('[CC] cancelled after fetch'); return }
        if (!r.ok) return
        const body = await r.json()
        console.log('[CC] body parsed, subject_name=', body?.subject_name, 'cancelled=', cancelled)
        if (cancelled) { console.log('[CC] cancelled after parse'); return }
        setChartName(body.subject_name ?? null)
        console.log('[CC] setChartName called with:', body.subject_name ?? null)
        setBirthDate(body.birth_date ?? null)
        setBirthPlace(body.birth_place ?? null)
      } catch (e) {
        console.log('[CC] catch:', (e as Error)?.name, (e as Error)?.message)
        if ((e as Error)?.name === 'AbortError') return
        if (cancelled) return
      }
    })()
    return () => {
      console.log('[CC] cleanup, setting cancelled=true')
      cancelled = true
      controller.abort()
    }
  }, [chartId])

  return {
    chartId,
    chartName,
    birthDate,
    birthPlace,
    ayanamshaSet: ['Lahiri'],
    lifeSpanYears: 120,
  }
}
