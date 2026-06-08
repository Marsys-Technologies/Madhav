'use client'

import { useState, useEffect } from 'react'

interface ChartContext {
  chartId: string
  chartName: string | null
  birthDate: string | null
  birthTime: string | null
  birthPlace: string | null
  ayanamshaSet: string[]
  lifeSpanYears: number
}

interface InitialChartMeta {
  subject_name: string | null
  birth_date: string | null
  birth_time?: string | null
  birth_place: string | null
}

export function useChartContext(chartId: string, initialMeta?: InitialChartMeta | null): ChartContext {
  const [chartName, setChartName] = useState<string | null>(initialMeta?.subject_name ?? null)
  const [birthDate, setBirthDate] = useState<string | null>(initialMeta?.birth_date ?? null)
  const [birthTime, setBirthTime] = useState<string | null>(initialMeta?.birth_time ?? null)
  const [birthPlace, setBirthPlace] = useState<string | null>(initialMeta?.birth_place ?? null)

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
        setBirthTime(body.birth_time ?? null)
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
    birthTime,
    birthPlace,
    ayanamshaSet: ['Lahiri'],
    lifeSpanYears: 120,
  }
}
