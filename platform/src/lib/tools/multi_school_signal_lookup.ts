/**
 * Tool 27: multi_school_signal_lookup
 *
 * school_signal_coverage, l25_msr_signals, classical_chunks dropped in WS-0.
 * Stub retained to satisfy exports in tools/index.ts. Returns empty results.
 *
 * TODO(ws-2): rebuild via bodha_signals JOIN school_signal_coverage once
 * school_signal_coverage is repopulated in the Brahma depth-build. SQL
 * prototype lives in git history (WS-0C Sub-C commit 01c32903).
 */

import 'server-only'

export interface MultiSchoolSignalLookupInput {
  topic: string
  domains?: string[]
  schools?: string[]
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

export async function multi_school_signal_lookup(
  input: MultiSchoolSignalLookupInput
): Promise<MultiSchoolSignalLookupOutput> {
  return {
    topic: input.topic,
    results_by_school: [],
    total_signals_found: 0,
    schools_with_primary_coverage: [],
    schools_silent: ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini'],
  }
}
