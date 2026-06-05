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
    const controller = new AbortController()
    ;(async () => {
      try {
        const r = await fetch(`/api/charts/${chartId}`, {
          credentials: 'include',
          signal: controller.signal,
        })
        if (!r.ok || controller.signal.aborted) return
        const body = await r.json()
        setChartName(body.subject_name ?? null)
        setBirthDate(body.birth_date ?? null)
        setBirthPlace(body.birth_place ?? null)
      } catch {
        // Non-fatal: header just shows the chartId fallback
      }
    })()
    return () => controller.abort()
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
