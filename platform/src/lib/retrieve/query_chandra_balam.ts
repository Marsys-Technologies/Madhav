/**
 * MARSYS-JIS Retrieval tool — query_chandra_balam (R2-S1)
 *
 * Canonical-name alias for chandra_balam_for_native, required by the MCP primitive
 * dispatcher. The MCP sidecar tool 'chandra_balam_for_native' calls
 * callPlatformPrimitive('query_chandra_balam', {date}) — the portal dispatcher
 * resolves getTool('query_chandra_balam'), which this file satisfies.
 *
 * Single-date Chandra Bala (Moon Strength) for the native (Abhisek Mohanty,
 * birth Moon sign: Pisces/Meena, id=12). Scores the Moon's sign position
 * relative to the native's birth Moon sign (1–12).
 *
 * Input: { date: string } — ISO date YYYY-MM-DD.
 * Output: ToolBundle with single result containing chandra_bala_score,
 *   position_from_birth_moon, moon_sign, moon_nakshatra, interpretation.
 *
 * Data source: ephemeris_daily (primary), panchanga_daily (fallback).
 * Classical source: MC §Chandra Bala; DP "Chandra Bala" reference.
 *
 * GISMCP Remediation R2-S1.
 */

import { tool as baseTool } from './chandra_balam_for_native'
import type { QueryPlan, ToolBundle, RetrievalTool } from './types'

const TOOL_NAME = 'query_chandra_balam'
const TOOL_VERSION = '1.0.0'

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const bundle = await baseTool.retrieve(plan, params)
  return { ...bundle, tool_name: TOOL_NAME }
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description: baseTool.description,
  retrieve,
}
