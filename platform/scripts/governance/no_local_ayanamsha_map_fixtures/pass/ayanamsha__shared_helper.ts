// PASS fixture — uses resolveChartFactsAyanamsha from the shared helper.
// No local ayanamsha alias map defined here.

import { resolveChartFactsAyanamsha } from '../lib/chart_facts_helpers.js'

export async function buildQuery(ayanamsha_id?: string) {
  return { ayanamsha: resolveChartFactsAyanamsha(ayanamsha_id) }
}
