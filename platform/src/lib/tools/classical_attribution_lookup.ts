/**
 * Tool 26: classical_attribution_lookup
 *
 * classical_attributions, classical_chunks, classical_texts dropped in WS-0.
 * Stub returns empty results.
 * TODO(ws-2): repoint to brahmagyan.texts + bodha_signals citation scaffolds
 * once the L0 classical corpus is queryable via the platform retrieval layer.
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
