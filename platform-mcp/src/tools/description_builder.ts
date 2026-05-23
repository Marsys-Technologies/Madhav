/**
 * description_builder.ts — Helper for generating MCP tool descriptions
 * from underlying enum/registry values.
 *
 * F.3 fix (MCPT v3.1.0-S1): tool descriptions are generated at registration
 * time from the actual enum values in the platform layer, so the advertised
 * categories are always in sync with the underlying data model.
 *
 * MCPT v3.2 Phase 3: Extended to cover all 21 tools (not just query_chart_facts).
 * All descriptions must:
 *   - Start with a disambiguator: "What it does: …", "Returns …", or "FIRST CALL when …"
 *   - Include a "When to prefer:" section
 *   - Fit within 1200 characters
 */

export interface BuildToolDescriptionOptions {
  /** One-sentence summary of what the tool does. Must start with one of:
   *  "What it does:", "Returns", or "FIRST CALL when".
   */
  baseDescription: string
  /**
   * Exhaustive list of valid enum values for the primary filter param.
   * Mutually exclusive with freeformCategories — use enumSource when you have
   * a typed enum; use freeformCategories for plain-text lists.
   */
  enumSource?: readonly string[]
  /**
   * Optional free-text hint about current data coverage
   * (e.g. "2,717 rows across 27 categories").
   */
  coverageHint?: string
  /**
   * 1–2 sentences describing when to call this tool vs alternatives.
   * Required for the lint gate ("When to prefer:" must appear in every description).
   */
  whenToPrefer?: string
  /**
   * Optional tier restriction note
   * (e.g. "Available: super_admin + acharya only. client tier = 403.").
   */
  tierNote?: string
}

const MAX_DESCRIPTION_LENGTH = 1200

/**
 * Build a structured tool description that optionally advertises enum values
 * and always includes a "When to prefer:" section.
 *
 * Output format:
 *   "<baseDescription> [coverageHint.] [Valid categories: ...] [tierNote]"
 *   "When to prefer: <whenToPrefer>"
 *
 * The result is truncated at 1200 chars if necessary.
 */
export function buildToolDescription({
  baseDescription,
  enumSource,
  coverageHint,
  whenToPrefer,
  tierNote,
}: BuildToolDescriptionOptions): string {
  const parts: string[] = []

  // Base description (required)
  parts.push(baseDescription.trimEnd())

  // Coverage hint
  if (coverageHint) {
    parts.push(` ${coverageHint.trimEnd()}.`)
  }

  // Enum-derived category list
  if (enumSource && enumSource.length > 0) {
    parts.push(` Valid categories: ${enumSource.join(', ')}.`)
  }

  // When to prefer (required for lint gate)
  if (whenToPrefer) {
    parts.push(` When to prefer: ${whenToPrefer.trimEnd()}`)
    if (!whenToPrefer.trimEnd().endsWith('.')) {
      parts.push('.')
    }
  }

  // Tier note
  if (tierNote) {
    parts.push(` ${tierNote.trimEnd()}`)
    if (!tierNote.trimEnd().endsWith('.')) {
      parts.push('.')
    }
  }

  const full = parts.join('').trim()

  if (full.length <= MAX_DESCRIPTION_LENGTH) {
    return full
  }

  // Graceful truncation: cut at last space before the limit, append ellipsis
  const cutPoint = full.lastIndexOf(' ', MAX_DESCRIPTION_LENGTH - 3)
  return full.slice(0, cutPoint > 0 ? cutPoint : MAX_DESCRIPTION_LENGTH - 3) + '...'
}
