/**
 * Classical literature disclosure filter — M8-G-S1.
 *
 * Applies per NAP.M8.2: classical-claim-failure findings are published with
 * attribution + translation source; no suppression. For public_redacted
 * audience_tier, verse content is summarised; confidence tier and translation
 * cross-check status are always included.
 */

import type { ClassicalAttributionRecord } from '@/lib/tools/classical_attribution_lookup'

export interface ClassicalCitationBlock {
  msr_signal_id: string
  source_text: string
  chapter: string | null
  verse_range: string | null
  attribution_type: string
  confidence_tier: string
  translation_cross_checked: boolean
  /** Verse content — redacted to summary for public_redacted audience */
  content: string
}

export type AudienceTier = 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'

/**
 * Apply the classical disclosure filter to attribution records.
 * For public_redacted, verse content is replaced with a summary disclosure line.
 */
export function applyClassicalDisclosureFilter(
  records: ClassicalAttributionRecord[],
  audienceTier: AudienceTier,
): ClassicalCitationBlock[] {
  return records.map(r => ({
    msr_signal_id: r.msr_signal_id,
    source_text: r.title,
    chapter: r.chapter,
    verse_range: r.verse_range,
    attribution_type: r.attribution_type,
    confidence_tier: r.confidence_tier,
    translation_cross_checked: r.translation_cross_checked,
    content:
      audienceTier === 'public_redacted'
        ? buildRedactedDisclosure(r)
        : buildFullDisclosure(r),
  }))
}

function buildFullDisclosure(r: ClassicalAttributionRecord): string {
  const verseRef = [r.chapter, r.verse_range].filter(Boolean).join(' v.')
  const xcheck = r.translation_cross_checked
    ? 'Translation accuracy cross-checked: yes'
    : 'Translation accuracy cross-checked: no'
  return (
    `Source: ${r.title}${verseRef ? `, ${verseRef}` : ''}. ` +
    `Attribution: ${r.attribution_type}. Confidence: ${r.confidence_tier}. ${xcheck}. ` +
    `"${r.content.slice(0, 300)}${r.content.length > 300 ? '…' : ''}"`
  )
}

function buildRedactedDisclosure(r: ClassicalAttributionRecord): string {
  const xcheck = r.translation_cross_checked ? 'yes' : 'no'
  return (
    `Classical attribution drawn from ${r.title}; ` +
    `confidence tier: ${r.confidence_tier}. ` +
    `Translation accuracy cross-checked: ${xcheck}. ` +
    `[Verse content available at acharya_reviewer+ tier.]`
  )
}

/**
 * Format a classical citation block for inclusion in the synthesis prompt.
 */
export function formatClassicalCitationForSynthesis(blocks: ClassicalCitationBlock[]): string {
  if (blocks.length === 0) return ''
  const lines = blocks.map(b => `- ${b.content}`)
  return `\n\n## Classical Attribution\n${lines.join('\n')}`
}
