import type { CallType, Capability, ModelRole } from '@/lib/models/registry'
import type { CatalogEntry } from '@/lib/aiops/catalog/types'

export type PreferredSortKey = 'params_desc' | 'cost_asc' | 'latency_asc' | 'context_desc'

export interface CallTypeSpec {
  mandatory: {
    minInputTokens?: number
    capabilities?:  Capability[]
    roleIn?:        ModelRole[]
  }
  preferred: {
    sortBy:          PreferredSortKey
    secondarySortBy?: PreferredSortKey
  }
  notes?: string
}

export const CALL_TYPE_SPECS: Record<CallType, CallTypeSpec> = {
  synthesis: {
    mandatory: { minInputTokens: 1_000_000, roleIn: ['synthesis', 'both'] },
    preferred: { sortBy: 'params_desc' },
    notes: 'Mandatory ≥1M context (Whole-Chart-Read); preferred highest parameter count.',
  },
  context_assembly: {
    mandatory: { minInputTokens: 1_000_000 },
    preferred: { sortBy: 'cost_asc' },
    notes: 'Mandatory ≥1M context; preferred low cost (called once per query).',
  },
  planner_deep: {
    mandatory: { capabilities: ['tool-use'] },
    preferred: { sortBy: 'params_desc', secondarySortBy: 'latency_asc' },
    notes: 'Mandatory tool-use; preferred deep reasoning at acceptable latency.',
  },
  planner_fast: {
    mandatory: { capabilities: ['tool-use'] },
    preferred: { sortBy: 'latency_asc', secondarySortBy: 'cost_asc' },
    notes: 'Mandatory tool-use; preferred lowest latency.',
  },
  worker: {
    mandatory: {},
    preferred: { sortBy: 'cost_asc' },
    notes: 'Cheapest model that responds; latency secondary.',
  },
  eval_judge: {
    mandatory: { minInputTokens: 200_000 },
    preferred: { sortBy: 'params_desc' },
    notes: '≥200K context to ingest synthesis output + ground truth; highest reasoning capacity.',
  },
  eval_generator: {
    mandatory: {},
    preferred: { sortBy: 'params_desc' },
    notes: 'Used to generate eval prompts; reasoning quality matters more than cost.',
  },
  smoke_synth: {
    mandatory: { minInputTokens: 1_000_000 },
    preferred: { sortBy: 'cost_asc' },
    notes: 'Same context floor as synthesis; should be cheap (run frequently).',
  },
  checkpoint_4_5: {
    mandatory: {},
    preferred: { sortBy: 'cost_asc' },
    notes: 'Mid-flight planner verification; speed and cost matter.',
  },
  checkpoint_5_5: {
    mandatory: { minInputTokens: 200_000 },
    preferred: { sortBy: 'cost_asc' },
    notes: '≥200K context to inspect assembled bundle; cheap.',
  },
  checkpoint_8_5: {
    mandatory: { minInputTokens: 200_000 },
    preferred: { sortBy: 'params_desc' },
    notes: 'Post-hoc synthesis verification; deeper reasoning useful.',
  },
}

/** Compare function for a preferred sort key. Lower value = sorted first. */
function sortScore(entry: CatalogEntry, key: PreferredSortKey): number {
  switch (key) {
    case 'params_desc':  return -(entry.param_count ?? 0)
    case 'cost_asc':     return (entry.cost_input_per_1m ?? Infinity)
    case 'latency_asc':  return 0                          // latency not in catalog yet; tie-break by cost
    case 'context_desc': return -(entry.context_window ?? 0)
  }
}

/**
 * Filter a catalog entry list to those matching the call type's mandatory spec,
 * then sort by the preferred key (+ optional secondary key).
 */
export function filterCatalogForCallType(entries: CatalogEntry[], callType: CallType): CatalogEntry[] {
  const spec = CALL_TYPE_SPECS[callType]

  const filtered = entries.filter(e => {
    const { minInputTokens, capabilities, roleIn } = spec.mandatory
    if (minInputTokens && (e.context_window ?? 0) < minInputTokens) return false
    if (capabilities?.length) {
      for (const cap of capabilities) {
        if (!e.capabilities.includes(cap)) return false
      }
    }
    if (roleIn?.length && e.role !== null && !roleIn.includes(e.role)) return false
    return true
  })

  return filtered.sort((a, b) => {
    const primary = sortScore(a, spec.preferred.sortBy) - sortScore(b, spec.preferred.sortBy)
    if (primary !== 0) return primary
    if (spec.preferred.secondarySortBy) {
      return sortScore(a, spec.preferred.secondarySortBy) - sortScore(b, spec.preferred.secondarySortBy)
    }
    return 0
  })
}
