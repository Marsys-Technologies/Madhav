/**
 * MARSYS-JIS Retrieval tool — jaimini_chara_dasha_full (R2-S2)
 *
 * Canonical-name alias required by the MCP primitive dispatcher.
 * The MCP sidecar tool 'query_jaimini_chara_dasha' calls
 * callPlatformPrimitive('jaimini_chara_dasha_full', {include_sub_periods: true, date?})
 * for the full timeline. The portal dispatcher resolves
 * getTool('jaimini_chara_dasha_full'), which this file satisfies.
 *
 * Delegates to query_jaimini_chara_dasha with include_sub_periods=true,
 * returning the complete 12-rashi dasha timeline (120-year cycle).
 *
 * Input: { date?: string } — ISO date YYYY-MM-DD; defaults to today.
 * Output: ToolBundle with single result containing full_periods (12 rashi
 *   entries), total_years, active_rashi_dasha, active_antar_dasha.
 *
 * Data source: Python sidecar /jaimini_drishti/chara_dasha/full.
 * Algorithm: Jaimini Chara Dasha (sign lord longitude determines period length).
 *
 * GISMCP Remediation R2-S2.
 */

import { tool as baseTool } from './query_jaimini_chara_dasha'
import type { QueryPlan, ToolBundle, RetrievalTool } from './types'

const TOOL_NAME = 'jaimini_chara_dasha_full'
const TOOL_VERSION = '1.0.0'

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const bundle = await baseTool.retrieve(plan, { ...(params ?? {}), include_sub_periods: true })
  return { ...bundle, tool_name: TOOL_NAME }
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Jaimini Chara Dasha full timeline — returns all 12 rashi dasha periods (120-year cycle) ' +
    'plus the active maha dasha + antar dasha. Calls Python sidecar ' +
    '/jaimini_drishti/chara_dasha/full. ' +
    'For active period only use jaimini_chara_dasha. ' +
    'Prefer query_dasha_periods for Vimshottari Dasha.',
  retrieve,
}
