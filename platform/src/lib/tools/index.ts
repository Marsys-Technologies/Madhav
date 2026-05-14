/**
 * Classical tools registry — M8 additions (tools 25 + 26) + M9 additions (tools 27 + 28).
 * Tools 1-24 are the structured query tools registered in build-tools.ts
 * and the pipeline's tool_calls registry.
 *
 * Tool 25: classical_text_search
 * Tool 26: classical_attribution_lookup
 * Tool 27: multi_school_signal_lookup  (STUB at M9-A; full impl at M9-D)
 * Tool 28: convergence_score_lookup    (STUB at M9-A; full impl at M9-D)
 */

export {
  classical_text_search,
  type ClassicalTextSearchInput,
  type ClassicalTextSearchOutput,
  type ClassicalTextSearchResult,
} from './classical_text_search'

export {
  classical_attribution_lookup,
  type ClassicalAttributionLookupInput,
  type ClassicalAttributionLookupOutput,
  type ClassicalAttributionRecord,
} from './classical_attribution_lookup'

export {
  multi_school_signal_lookup,
  type MultiSchoolSignalLookupInput,
  type MultiSchoolSignalLookupOutput,
  type PerSchoolSignalResult,
} from './multi_school_signal_lookup'

export {
  convergence_score_lookup,
  type ConvergenceScoreLookupInput,
  type ConvergenceScoreLookupOutput,
  type ConvergenceScoreRow,
} from './convergence_score_lookup'

export const CLASSICAL_TOOL_REGISTRY = [
  {
    tool_number: 25,
    tool_name: 'classical_text_search',
    description: 'Semantic search over classical Jyotish text corpus using pgvector cosine similarity. Returns top-K chunks from Tier 1/2/3 texts with chapter, verse_range, and confidence baseline.',
    layer: 'L8',
    status: 'ACTIVE', // implemented M8-E-S1 2026-05-14
  },
  {
    tool_number: 26,
    tool_name: 'classical_attribution_lookup',
    description: 'Structured lookup of MSR signal attributions in classical_attributions JOIN classical_chunks JOIN classical_texts. Returns all attributions grouped by text for given signal IDs.',
    layer: 'L8',
    status: 'ACTIVE', // implemented M8-E-S1 2026-05-14
  },
  {
    tool_number: 27,
    tool_name: 'multi_school_signal_lookup',
    description: 'Queries school_signal_coverage to report what all 7 Jyotish schools (Parashari/Jaimini/Tajika/KP/Nadi/BNN/Yogini) say about a topic. Returns per-school coverage_type + confidence + matching signals.',
    layer: 'L9',
    status: 'STUB', // full implementation at M9-D-S1 2026-05-14
  },
  {
    tool_number: 28,
    tool_name: 'convergence_score_lookup',
    description: 'Returns inter-school convergence metrics from convergence_scores table for requested domains. Includes convergence_level (HIGH/MEDIUM/LOW), direction, mean/std scores, per-school breakdown.',
    layer: 'L9',
    status: 'STUB', // full implementation at M9-D-S1 2026-05-14
  },
] as const
