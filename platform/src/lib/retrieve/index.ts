/**
 * MARSYS-JIS Retrieval tool registry
 *
 * Stream G (BRAHMA-G-1): PyHora capabilities registered here.
 * compute_natal_positions, query_dasha_periods, query_special_lagnas
 *
 * Types and CONTRACT_CATALOG re-exports preserved so the serve shell
 * (route.ts, tool_catalogue.ts, agentic loop) compiles and boots.
 */

export * from './types'
import type { RetrievalTool } from './types'

// Stream G — PyHora L1 Gaṇita capabilities (BRAHMA-G-1)
import { tool as computeNatalPositions } from './pyhora_natal_positions'
import { tool as queryDashaPeriods } from './pyhora_dasha_periods'
import { tool as querySpecialLagnas } from './pyhora_special_lagnas'

// Stream C — Classical text search
import { tool as classicalTextSearch } from './classical_text_search_tool'

export const RETRIEVAL_TOOLS: RetrievalTool[] = [
  // L1 Gaṇita — PyJHora natal computation (Stream G)
  computeNatalPositions,
  queryDashaPeriods,
  querySpecialLagnas,
  // Classical text retrieval (Stream C)
  classicalTextSearch,
]

export function getTool(name: string): RetrievalTool | undefined {
  return RETRIEVAL_TOOLS.find(t => t.name === name)
}

// CONTRACT_CATALOG re-exports — registry is also empty after teardown.
export {
  CONTRACT_CATALOG,
  CONTRACT_CATALOG_BY_NAME,
  CONTRACT_TOOL_NAMES,
} from '../contract'
