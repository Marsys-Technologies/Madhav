/**
 * Tool 26: classical_attribution_lookup
 *
 * The classical_attributions / classical_chunks / classical_texts relations this
 * tool originally joined were dropped in WS-0, and no queryable L0/Bodha
 * signal-to-verse attribution source has replaced them. The lookup therefore
 * FAILS CLOSED: it throws ClassicalAttributionSourceUnavailableError (code
 * CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE) instead of returning an empty result.
 * An empty result would read as "every requested signal is classically silent",
 * which is a claim nothing measured (CLAUDE.md §N.7 item 6 / §N.8).
 *
 * TODO(ws-2): repoint to brahmagyan.texts + bodha_signals citation scaffolds
 * once a grounded signal-to-verse attribution source exists; only then may this
 * return a (possibly empty) successful result.
 */

import 'server-only'

export interface ClassicalAttributionLookupInput {
  signal_ids: string[]
  attribution_type?: 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
  confidence_tier?: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface ClassicalAttributionRecord {
  attribution_id: string
  msr_signal_id: string
  text_key: string
  title: string
  author: string | null
  chapter: string | null
  verse_range: string | null
  content: string
  attribution_type: 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
  confidence: number
  confidence_tier: 'HIGH' | 'MEDIUM' | 'LOW'
  derivation_notes: string | null
  translation_cross_checked: boolean
}

export interface ClassicalAttributionLookupOutput {
  attributions: ClassicalAttributionRecord[]
  signal_ids_queried: string[]
  signal_ids_with_attributions: string[]
  signal_ids_silent: string[]
}

export const CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE = 'CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE'

/**
 * The retired attribution relations cannot truthfully answer an ordinary empty
 * result. Callers must disclose the missing source rather than treating every
 * requested signal as classically silent.
 */
export class ClassicalAttributionSourceUnavailableError extends Error {
  readonly code = CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE

  constructor() {
    super(
      'Classical attribution lookup is unavailable: the retired classical_attributions store has not yet been replaced by a queryable L0/Bodha attribution source.',
    )
    this.name = 'ClassicalAttributionSourceUnavailableError'
  }
}

export async function classical_attribution_lookup(
  input: ClassicalAttributionLookupInput
): Promise<ClassicalAttributionLookupOutput> {
  void input
  throw new ClassicalAttributionSourceUnavailableError()
}
