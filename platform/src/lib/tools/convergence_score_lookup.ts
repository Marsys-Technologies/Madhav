/**
 * Tool 28: convergence_score_lookup
 * M9-A-S1 (2026-05-14) — STUB; full implementation in M9-D-S1
 *
 * Returns convergence_scores rows for requested domains.
 * Used by synthesis stage to append inter-school convergence context to domain answers.
 */

export interface ConvergenceScoreLookupInput {
  domains: string[]  // e.g. ['CAREER', 'HEALTH']
}

export interface ConvergenceScoreRow {
  domain: string
  schools_agreeing: number
  schools_total: number                    // 7 normally; 6 if Tajika [VARSHA_KUNDALI_PENDING]
  convergence_level: 'HIGH' | 'MEDIUM' | 'LOW'
  mean_domain_score: number
  std_domain_score: number
  direction: 'positive' | 'negative' | 'neutral' | 'mixed'
  per_school_scores: Record<string, number> // {"parashari": 3.2, "jaimini": 2.8, ...}
  convergence_narrative: string | null
  computed_at: string                      // ISO 8601
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

// TODO (M9-D-S1): Implement full query logic:
//   SELECT domain, schools_agreeing, schools_total, convergence_level,
//          mean_domain_score, std_domain_score, direction, per_school_scores,
//          convergence_narrative, computed_at
//   FROM convergence_scores
//   WHERE domain = ANY($1)
//   ORDER BY domain
//   -- Use most recent computed_at per domain

export async function convergence_score_lookup(
  input: ConvergenceScoreLookupInput
): Promise<ConvergenceScoreLookupOutput> {
  // STUB — M9-D-S1 replaces with full implementation
  throw new Error(
    `convergence_score_lookup not yet implemented (M9-D-S1). Domains: ${input.domains.join(', ')}`
  )
}
