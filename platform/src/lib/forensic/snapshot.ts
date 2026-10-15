// ForensicChart is the shape the chart-rendering components and the chart
// workspace/journey1 builders consume. It is a TYPE-ONLY module: it holds no
// chart data and no query. Callers build a ForensicChart from the chart they
// were given (see lib/charts/journey1.ts and lib/charts/workspaceSummary.ts).
//
// History: this file used to export getForensicSnapshot(), which returned a
// hard-coded copy of one native's chart (lagna, houses, yogas, dasha) for every
// chart_id. It had no caller, and "no birth data in code" is the rule, so the
// function and the embedded chart were removed (SS N-342 item 10). The honest
// behaviour when no chart is supplied is that there is nothing to return.

export interface PlanetPlacement {
  planet: string
  sign: string
  house: number
  degreeDms: string
}

export interface ForensicChart {
  chartId: string
  lagnaSign: string
  lagnaDegreeDms: string
  houses: Array<{ house: number; sign: string; planets: string[] }>
  topYogas: string[]
  currentDasha: { md: string; ad: string; adEnd: string } | null
  isEmpty: boolean
}
