/**
 * MARSYS-JIS Retrieval tool — jaimini_chara_dasha (R2-S2)
 *
 * Canonical-name alias required by the MCP primitive dispatcher.
 * The MCP sidecar tool 'query_jaimini_chara_dasha' calls
 * callPlatformPrimitive('jaimini_chara_dasha', {date?}) for the active dasha.
 * The portal dispatcher resolves getTool('jaimini_chara_dasha'), which this
 * file satisfies.
 *
 * Delegates to query_jaimini_chara_dasha with include_sub_periods=false,
 * returning only the active rashi maha dasha + antar dasha for a given date.
 *
 * Input: { date?: string } — ISO date YYYY-MM-DD; defaults to today.
 * Output: ToolBundle with single result containing active_rashi_dasha,
 *   active_antar_dasha, query_date, algorithm.
 *
 * Data source: Python sidecar /jaimini_drishti/chara_dasha.
 * Algorithm: Jaimini Chara Dasha (sign lord longitude determines period length).
 *
 * GISMCP Remediation R2-S2.
 */

import { tool as baseTool } from './query_jaimini_chara_dasha'
import type { QueryPlan, ToolBundle, RetrievalTool } from './types'

const TOOL_NAME = 'jaimini_chara_dasha'
const TOOL_VERSION = '1.0.0'

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const bundle = await baseTool.retrieve(plan, { ...(params ?? {}), include_sub_periods: false })
  return { ...bundle, tool_name: TOOL_NAME }
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Jaimini Chara Dasha active period lookup — returns the active rashi maha dasha + antar ' +
    'dasha for a given date. Calls Python sidecar /jaimini_drishti/chara_dasha. ' +
    'For the full 12-rashi timeline use jaimini_chara_dasha_full. ' +
    'Prefer query_dasha_periods for Vimshottari Dasha.',
  retrieve,
}
