/**
 * description_builder.ts — Helper for generating MCP tool descriptions
 * from underlying enum/registry values.
 *
 * F.3 fix (MCPT v3.1.0-S1): tool descriptions are generated at registration
 * time from the actual enum values in the platform layer, so the advertised
 * categories are always in sync with the underlying data model.
 */

export interface BuildToolDescriptionOptions {
  /** One-sentence summary of what the tool does. */
  baseDescription: string
  /** Exhaustive list of valid enum values for the primary filter param. */
  enumSource: readonly string[]
  /**
   * Optional free-text hint about current data coverage
   * (e.g. "2,717 rows across 27 categories").
   */
  coverageHint?: string
}

/**
 * Build a structured tool description that advertises the real enum values
 * from the underlying platform layer.
 *
 * Example output:
 *   "What it does: Queries the chart_facts table (2,717 rows). ...
 *    Valid categories: house, shadbala, dasha_vimshottari, ..."
 */
export function buildToolDescription({
  baseDescription,
  enumSource,
  coverageHint,
}: BuildToolDescriptionOptions): string {
  const categoryList = enumSource.join(', ')
  const coverageLine = coverageHint ? ` ${coverageHint}.` : ''
  return (
    `${baseDescription}${coverageLine} ` +
    `Valid categories: ${categoryList}.`
  )
}
