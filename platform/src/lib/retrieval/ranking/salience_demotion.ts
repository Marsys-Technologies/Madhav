/**
 * salience_demotion.ts — WP-1.2(d) (LCA-9b-2 serving cap) serving-side salience demotion.
 * ========================================================================================
 * At SERVE time, descriptive almanac fact_keys (akshara, symbol, yoni, pakshi,
 * presiding_deity, and similar) and per-varga granular divisional data are BARRED from
 * the `major` / `chart_defining` signature tiers — this stops nakshatra trivia and the
 * thousands-strong per-varga dignity flood from drowning genuinely chart-defining signals
 * at the top of every orient/signals surface.
 *
 * This is a SERVING transform only:
 *   - It never mutates a stored value — the ingestion-side source fix is WP-2.4.
 *   - It never drops a row — the signal is still fully served and composite-ranked; only
 *     its served `signature_tier` label is capped (down to `supporting`), with the
 *     original tier preserved on `signature_tier_demoted_from` for auditability (B.10:
 *     nothing hidden, the demotion is disclosed on the row itself).
 *
 * Tier order (high→low): chart_defining > major > supporting > background.
 */

/**
 * Descriptive/almanac fact_keys that carry no bhava-bearing weight — nakshatra
 * curiosities and classification labels. Barred from major/chart_defining candidacy.
 */
export const DESCRIPTIVE_FACT_KEYS: ReadonlySet<string> = new Set([
  'akshara',
  'symbol',
  'yoni',
  'yoni_animal',
  'pakshi',
  'presiding_deity',
  'deity',
  'gana',
  'nadi',
  'varna',
  'vashya',
  'tara',
])

/** Tiers that a descriptive/per-varga signal may NOT occupy at serve time. */
const DEMOTABLE_TIERS: ReadonlySet<string> = new Set(['major', 'chart_defining'])

/** The tier a barred signal is capped down to. */
export const DEMOTED_TIER = 'supporting'

interface DemotableRow {
  signal_type_id?: string | null
  signature_tier?: string | null
  configuration_jsonb?: Record<string, unknown> | null
  [k: string]: unknown
}

/**
 * True iff the row is a descriptive almanac descriptor OR per-varga granular data
 * (a divisional beyond the D1 rasi chart). D1 itself is NOT per-varga granular and
 * is left untouched.
 */
export function isDescriptiveOrPerVarga(row: DemotableRow): boolean {
  const cfg = row.configuration_jsonb
  if (cfg && typeof cfg === 'object') {
    const factKey = typeof cfg['fact_key'] === 'string' ? (cfg['fact_key'] as string).toLowerCase() : ''
    if (factKey && DESCRIPTIVE_FACT_KEYS.has(factKey)) return true
    const varga = typeof cfg['varga'] === 'string' ? (cfg['varga'] as string).toUpperCase() : ''
    if (varga && varga !== 'D1') return true
  }
  const stid = typeof row.signal_type_id === 'string' ? row.signal_type_id.toLowerCase() : ''
  if (stid.includes('per_varga')) return true
  for (const k of DESCRIPTIVE_FACT_KEYS) {
    if (stid.endsWith(':' + k) || stid.endsWith('_' + k)) return true
  }
  return false
}

/**
 * Return a serve-time copy of the row with its signature_tier capped when it is a
 * descriptive/per-varga signal occupying major/chart_defining. Non-matching rows are
 * returned unchanged (same object reference). The demotion is disclosed on the row.
 */
export function demoteSignatureTier<T extends DemotableRow>(
  row: T,
): T & { signature_tier_demoted_from?: string; signature_tier_demotion_reason?: string } {
  const tier = typeof row.signature_tier === 'string' ? row.signature_tier : null
  if (tier && DEMOTABLE_TIERS.has(tier) && isDescriptiveOrPerVarga(row)) {
    return {
      ...row,
      signature_tier: DEMOTED_TIER,
      signature_tier_demoted_from: tier,
      // Served reason is human-readable prose; keep the WP-1.2d ticket reference only in
      // code comments (see file header) — never ship raw work-package ids in served fields.
      signature_tier_demotion_reason:
        'Demoted: descriptive/per-varga signals are not served at major/chart_defining tier',
    }
  }
  return row
}

/** Apply demoteSignatureTier across a row array. */
export function demoteSignatureTiers<T extends DemotableRow>(rows: T[]): T[] {
  return rows.map(demoteSignatureTier)
}
