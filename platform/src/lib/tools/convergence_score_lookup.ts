/**
 * Tool 28: convergence_score_lookup
 *
 * convergence_scores dropped in WS-0. Stub returns empty results.
 * TODO(ws-2): rebuild once school_signal_coverage + convergence tables
 * are repopulated in the Brahma depth-build.
 */

import 'server-only'

export interface ConvergenceScoreLookupInput {
  domains: string[]
}

export interface ConvergenceScoreRow {
  domain: string
  schools_agreeing: number
  schools_total: number
  convergence_level: 'HIGH' | 'MEDIUM' | 'LOW'
  mean_domain_score: number
  std_domain_score: number
  direction: 'positive' | 'negative' | 'neutral' | 'mixed'
  per_school_scores: Record<string, number | null>
  convergence_narrative: string | null
  computed_at: string
}

export interface ConvergenceScoreLookupOutput {
  domains_requested: string[]
  convergence_scores: ConvergenceScoreRow[]
  summary: {
    high_convergence_domains: string[]
    medium_convergence_domains: string[]
    low_convergence_domains: string[]
    overall_agreement_signal: string
  }
}

export async function convergence_score_lookup(
  input: ConvergenceScoreLookupInput
): Promise<ConvergenceScoreLookupOutput> {
  return {
    domains_requested: input.domains,
    convergence_scores: [],
    summary: {
      high_convergence_domains: [],
      medium_convergence_domains: [],
      low_convergence_domains: [],
      overall_agreement_signal: 'convergence_scores table unavailable (WS-2 pending)',
    },
  }
}
