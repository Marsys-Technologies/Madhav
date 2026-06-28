/**
 * classical_disclosure_filter.ts — Tier-gated disclosure filter for classical attributions
 *
 * D7 Step 4 (2026-06-28): moved from lib/retrieve/ to lib/retrieval/tools/ on lib/retrieve retirement.
 *
 * Note: audience_tier gating is a serve-time concern per DG1 ruling. This filter
 * is retained as a utility for API boundary use — it does NOT live in the retrieval
 * capability registry (which is tier-free). Capability descriptors carry no tier field.
 */

export interface ClassicalDisclosureBlock {
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

export type AudienceTier =
  | 'super_admin'
  | 'acharya_reviewer'
  | 'client'
  | 'public_redacted'

const REDACTED_CONTENT_MSG =
  '[Content restricted — full verse text available to acharya_reviewer+ audience tier]'

/**
 * Applies disclosure filtering to an array of attribution records.
 * Returns ClassicalDisclosureBlock[] suitable for serialization.
 */
export function applyClassicalDisclosureFilter(
  records: ClassicalDisclosureBlock[],
  audienceTier: AudienceTier
): ClassicalDisclosureBlock[] {
  return records.map(r => {
    const citationHeader = [
      r.title,
      r.chapter ? `Ch. ${r.chapter}` : null,
      r.verse_range ? `v. ${r.verse_range}` : null,
    ].filter(Boolean).join(', ')

    if (audienceTier === 'public_redacted') {
      return {
        ...r,
        content: `${citationHeader} — ${REDACTED_CONTENT_MSG}`,
      }
    }

    return {
      ...r,
      content: `${citationHeader}: ${r.content}`,
    }
  })
}
