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

export async function classical_attribution_lookup(
  input: ClassicalAttributionLookupInput
): Promise<ClassicalAttributionLookupOutput> {
  return {
    attributions: [],
    signal_ids_queried: input.signal_ids,
    signal_ids_with_attributions: [],
    signal_ids_silent: input.signal_ids,
  }
}
