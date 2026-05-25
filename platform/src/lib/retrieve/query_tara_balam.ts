/**
 * MARSYS-JIS Retrieval tool — query_tara_balam (R2-S1)
 *
 * Canonical-name alias for tara_balam_for_native, required by the MCP primitive
 * dispatcher. The MCP sidecar tool 'tara_balam_for_native' calls
 * callPlatformPrimitive('query_tara_balam', {date}) — the portal dispatcher
 * resolves getTool('query_tara_balam'), which this file satisfies.
 *
 * Single-date Tara Bala (Star Strength) for the native (Abhisek Mohanty,
 * birth nakshatra: Purva Bhadrapada, id=25). Computes the Nava Tara Chakra
 * position of the Moon's daily nakshatra relative to the birth nakshatra.
 *
 * Input: { date: string } — ISO date YYYY-MM-DD.
 * Output: ToolBundle with single result containing tara_count, tara_name,
 *   score (0–1), interpretation, moon_nakshatra, and native context.
 *
 * Data source: panchanga_daily (primary), ephemeris_daily (fallback).
 * Classical source: MC §Tara Bala; BPHS §Tara; Jataka Parijata §Tara Bala.
 *
 * GISMCP Remediation R2-S1.
 */

import { tool as baseTool } from './tara_balam_for_native'
import type { QueryPlan, ToolBundle, RetrievalTool } from './types'

const TOOL_NAME = 'query_tara_balam'
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
