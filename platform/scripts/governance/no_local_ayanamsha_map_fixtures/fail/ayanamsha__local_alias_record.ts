// FAIL fixture — local AYANAMSHA_ALIAS Record<string, string> (register_p1_aliases.ts pattern)
// Defect: file-local ayanamsha alias map that silently rewrites ayanamsha_id values.
// Fix: import and use resolveChartFactsAyanamsha from the shared helper.

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha',
  LAHIRI: 'lahiri_chitrapaksha',
  Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha',
  true_chitra: 'lahiri_chitrapaksha',
}

function na(id?: string): string {
  return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha'
}

export function buildQuery(ayanamsha_id?: string) {
  return { ayanamsha: na(ayanamsha_id) }
}
