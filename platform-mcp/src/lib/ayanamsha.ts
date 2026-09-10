/**
 * Shared ayanāṃśa resolver for MCP serving paths.
 *
 * `chart_facts` contains distinct rows for each stored school. In particular,
 * `true_chitra` must remain reachable; it is not a spelling of Lahiri.
 */
const CHART_FACTS_AYANAMSHA_ALIASES: Readonly<Record<string, string>> = {
  lahiri: 'lahiri_chitrapaksha',
  lahiri_chitra: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha',
  kp: 'krishnamurti',
  krishnamurti: 'krishnamurti',
  raman: 'raman',
  surya_siddhanta: 'surya_siddhanta_classical',
  surya_siddhanta_classical: 'surya_siddhanta_classical',
  true_chitra: 'true_chitra',
  true_citra: 'true_chitra',
  chitra: 'true_chitra',
  invariant: 'INVARIANT',
}

/**
 * Resolves convenience spellings without collapsing distinct schools. Unknown
 * ids pass through so the underlying capability returns an honest empty result.
 */
export function resolveChartFactsAyanamsha(id?: string): string {
  if (!id) return 'lahiri_chitrapaksha'
  return CHART_FACTS_AYANAMSHA_ALIASES[id] ?? CHART_FACTS_AYANAMSHA_ALIASES[id.toLowerCase()] ?? id
}
