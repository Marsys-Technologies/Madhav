'use client'

interface ChartContext {
  chartId: string
  ayanamshaSet: string[]
  lifeSpanYears: number
}

export function useChartContext(chartId: string): ChartContext {
  // ayanamshaSet and lifeSpanYears stubbed for this phase
  return {
    chartId,
    ayanamshaSet: ['Lahiri'],
    lifeSpanYears: 120,
  }
}
