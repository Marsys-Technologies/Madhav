/**
 * registry.ts — Tool Contract Registry (Brahma delta build 2026-06-03)
 *
 * Rebuilding from clean-slate stub (legacy-teardown). Adding read_classical_text
 * as the first entry per brahmagyan.texts delta build brief.
 *
 * When adding further contracts per the Layer-0 → Layer-3 arc, append to
 * TOOL_CONTRACTS below and mirror the canonical_name in
 * platform-mcp/src/contract_bridge.ts MCP_CONTRACT_TOOL_NAMES array.
 */

import { z } from 'zod'
import type { ToolContract } from './types'

const readClassicalTextContract: ToolContract<{
  query: string
  schools?: string[]
  tier_max?: number
  limit?: number
}> = {
  canonical_name: 'read_classical_text',

  description: `Semantic search over the classical Jyotish corpus (BPHS, Jaimini Sutras, KP Reader,
Tajaka Neelakanthi, Saravali, etc.). Use for verse-addressable citation lookup (e.g. BPHS.1.7-1.12)
or free-text semantic queries ("what does Parashara say about exalted Sun in 10H").
Prefer this tool over vector_search when the question is explicitly anchored in a named classical text
or school tradition. Returns verse reference, chunk content, similarity score, and tradition metadata.
Not chart-bound — does not require chart_id.`,

  input_schema: z.object({
    query: z.string().min(3).describe(
      'Semantic search string or verse citation (e.g. "BPHS.1.7" or "Parashara on Moon in 4th house")'
    ),
    schools: z.array(z.string()).optional().describe(
      'Filter by school/tradition: parashari | jaimini | tajika | kp | nadi | bnn'
    ),
    tier_max: z.number().int().min(1).max(4).optional().describe(
      'Maximum text tier to include (1=mandatory only, 4=all including nadi/bnn). Default: 3'
    ),
    limit: z.number().int().min(1).max(20).optional().describe(
      'Maximum results to return. Default: 5'
    ),
  }),

  annotations: {
    readOnly: true,
    idempotent: true,
    surgical: true,
    layer: 'L1',
  },

  role: 'text',
  family: 'school',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  ayanamsha_id: null,
  per_chart: false,
}

export const TOOL_CONTRACTS: readonly ToolContract<unknown>[] = [
  readClassicalTextContract as ToolContract<unknown>,
]

export function getContract(canonical_name: string): ToolContract<unknown> | undefined {
  return TOOL_CONTRACTS.find(c => c.canonical_name === canonical_name)
}

export function getContractNames(): string[] {
  return TOOL_CONTRACTS.map(c => c.canonical_name)
}
