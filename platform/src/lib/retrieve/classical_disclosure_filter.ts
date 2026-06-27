/**
 * classical_disclosure_filter.ts — Tier-gated disclosure filter for classical attributions
 *
 * RETIRED / DEPRECATED — lib/retrieve layer (legacy chat-route pipeline)
 * -----------------------------------------------------------------------
 * This file is part of the legacy lib/retrieve layer. It is RETIRED in
 * favour of the retrieval registry layer and MCP tool surface.
 *
 * Replacement registry capabilities (Gate C citation):
 *   marsys://tool/L0/query_classical_texts — registered in
 *     platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_classical_texts.ts
 *   MCP surface: platform-mcp/src/tools/read_classical_text.ts
 *   Disclosure/tier filtering at serve-time is now handled by the MCP auth
 *   layer (platform-mcp/src/auth.ts) and the chat-route principal context —
 *   no audience_tier gating is stored in capability descriptors per the
 *   no-audience-tier build principle (§N.4 feedback-no-audience-tier).
 *
 * This file is retained for compatibility with any chat-route code that
 * still calls applyDisclosureFilter(). Do NOT add new tier logic here —
 * serve-time filtering belongs at the API/MCP boundary.
 * -----------------------------------------------------------------------
 *
 * Applies audience-tier filtering to ClassicalAttributionRecord objects before
 * they are serialized in a response. Only content fields are redacted; metadata
 * (confidence_tier, translation_cross_checked, attribution_type) is always emitted.
 *
 * Tier semantics:
 *   - super_admin / acharya_reviewer / client: full content emitted
 *   - public_redacted: verse content replaced with redaction notice; only
 *     metadata + citation header emitted
 *
 * M8/Brahmagyan delta build 2026-06-03
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
 *
 * For all tiers, prepends a citation header (title + chapter + verse) to the
 * content so downstream consumers can identify the source without inspecting
 * separate fields. For public_redacted, the verse body is replaced with a
 * redaction notice; only the citation header is visible.
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
      // Redact verse body; emit citation header + redaction notice
      return {
        ...r,
        content: `${citationHeader} — ${REDACTED_CONTENT_MSG}`,
      }
    }

    // super_admin, acharya_reviewer, client: prepend citation header then full verse content
    return {
      ...r,
      content: `${citationHeader}: ${r.content}`,
    }
  })
}
