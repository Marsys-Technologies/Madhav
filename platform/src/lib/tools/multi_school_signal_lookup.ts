/**
 * Tool 27: multi_school_signal_lookup
 * M9-A-S1 (2026-05-14) — STUB; full implementation in M9-D-S1
 *
 * Queries school_signal_coverage to report what all 7 Jyotish schools say about a topic.
 * Used by synthesis stage when query involves multi-school comparison.
 */

export interface MultiSchoolSignalLookupInput {
  topic: string
  domains?: string[]  // filter to specific domains: CAREER|HEALTH|RELATIONSHIP|SPIRITUAL|PSYCHOLOGICAL
  schools?: string[]  // filter to specific schools; defaults to all 7
}

export interface PerSchoolSignalResult {
  school: 'parashari' | 'jaimini' | 'tajika' | 'kp' | 'nadi' | 'bnn' | 'yogini'
  coverage_type: 'primary' | 'secondary' | 'silent'
  confidence: number | null
  matching_signals: Array<{
    signal_id: string
    signal_name: string
    domain: string
    attribution_ref?: string
  }>
}

export interface MultiSchoolSignalLookupOutput {
  topic: string
  results_by_school: PerSchoolSignalResult[]
  total_signals_found: number
  schools_with_primary_coverage: string[]
  schools_silent: string[]
}

// TODO (M9-D-S1): Implement full query logic:
//   SELECT ssc.school, ssc.coverage_type, ssc.confidence, cc.content, ct.text_key
//   FROM school_signal_coverage ssc
//   JOIN l25_msr_signals msr ON msr.signal_id = ssc.signal_id
//   LEFT JOIN classical_chunks cc ON cc.id = ssc.attribution_chunk_id
//   LEFT JOIN classical_texts ct ON ct.id = cc.text_id
//   WHERE (msr.signal_name ILIKE $topic OR msr.domains_affected @> $domains)
//   AND ($schools IS NULL OR ssc.school = ANY($schools))
//   ORDER BY ssc.school, ssc.coverage_type, ssc.confidence DESC NULLS LAST

export async function multi_school_signal_lookup(
  input: MultiSchoolSignalLookupInput
): Promise<MultiSchoolSignalLookupOutput> {
  // STUB — M9-D-S1 replaces with full implementation
  throw new Error(
    `multi_school_signal_lookup not yet implemented (M9-D-S1). Input: ${JSON.stringify(input)}`
  )
}
