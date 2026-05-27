/**
 * registry.ts — the SINGLE registry of tool contracts.
 *
 * Both channels (portal + MCP) read from this. catalog.ts is generated from it.
 */

import type { ToolContract } from './types'
import { queryChartFactsContract } from './tools/query_chart_facts'
import { queryPanchangaContract } from './tools/query_panchanga'
import { queryDashaPeriodsContract } from './tools/query_dasha_periods'
import { queryDivisionalChartContract } from './tools/query_divisional_chart'
import { queryKpRulingPlanetsContract } from './tools/query_kp_ruling_planets'
import { kpQueryContract } from './tools/kp_query'
import { queryEphemerisContract } from './tools/query_ephemeris'
import { readClassicalTextContract } from './tools/read_classical_text'

export const TOOL_CONTRACTS: readonly ToolContract<unknown>[] = [
  queryChartFactsContract,
  queryPanchangaContract,
  queryDashaPeriodsContract,
  queryDivisionalChartContract,
  queryKpRulingPlanetsContract,
  kpQueryContract,
  queryEphemerisContract,
  readClassicalTextContract,
] as ToolContract<unknown>[]

export function getContract(canonical_name: string): ToolContract<unknown> | undefined {
  return TOOL_CONTRACTS.find(c => c.canonical_name === canonical_name)
}

export function getContractNames(): string[] {
  return TOOL_CONTRACTS.map(c => c.canonical_name)
}
