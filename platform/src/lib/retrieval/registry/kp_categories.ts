/**
 * kp_categories.ts — the KP category set (SS N-358): "a KP category is served in the KP frame".
 * =====================================================================================
 * Krishnamurti Paddhati has ONE frame by doctrine, the Krishnamurti ayanamsha (SS N-342 item 3).
 * SS N-357 pinned the KP BRANCH of get_karakas (system=kp) and get_nakshatra (domain=kp). SS N-358
 * closes the residual: a KP category named on a DEFAULT page, or in an explicit `categories` list,
 * is read at `krishnamurti` too, whatever ayanamsha the page is otherwise served at.
 *
 * `KP_FRAME_CATEGORIES` is THE one set. It lists every chart_facts `fact_category` the L1 writers
 * emit for Krishnamurti Paddhati (sub-lord / star-lord / cuspal-chain / KP significator ladders):
 *
 *   cusp_kp_lords            ga_nakshatra  (ga_nakshatra_emitters.emit_kp_lords): per-cusp KP chain
 *   graha_kp_lords           ga_nakshatra  (same emitter): per-graha KP chain
 *   kp_cuspal_significators  ga_sensitive  (ga_sensitive_writer, category 23): cusp sign/star/sub lords
 *   kp_house_significators   ga_nakshatra  (ga_kp_significators): 4-limbed significator ladder per house
 *   kp_planet_significations ga_nakshatra  (ga_kp_significators): the same ladder inverted per planet
 *   kp_ruling_planets_natal  ga_sensitive  (ga_sensitive_writer, category 22): the 5 natal ruling planets
 *
 * Deliberately NOT in the set: `bhava_cusps` (cusp longitudes, a general house-frame fact read by
 * every system, not a KP-purposed category), `significator_path` and `bhava_significance_link`
 * (sign-graph / structural, not KP).
 *
 * Disjoint from the INVARIANT categories by construction (a KP chain depends on the ayanamsha, so
 * it is stored per ayanamsha, never under the `INVARIANT` sentinel); pinned by
 * `__tests__/kp_categories_pin.test.ts`.
 *
 * Pure: no I/O, no DB. The KP frame id/label constants stay in `../kp_frame.ts`.
 */

export const KP_FRAME_CATEGORIES: readonly string[] = [
  'cusp_kp_lords',
  'graha_kp_lords',
  'kp_cuspal_significators',
  'kp_house_significators',
  'kp_planet_significations',
  'kp_ruling_planets_natal',
]

const KP_FRAME_CATEGORY_SET: ReadonlySet<string> = new Set(KP_FRAME_CATEGORIES)

/** True when `cat` is a Krishnamurti Paddhati category (served only in the KP frame). */
export function isKpFrameCategory(cat: unknown): boolean {
  return typeof cat === 'string' && KP_FRAME_CATEGORY_SET.has(cat)
}

/** Split a requested category list into its KP-frame part and the rest (order preserved). */
export function partitionKpCategories(categories: readonly string[]): { kp: string[]; other: string[] } {
  const kp: string[] = []
  const other: string[] = []
  for (const c of categories) (isKpFrameCategory(c) ? kp : other).push(c)
  return { kp, other }
}
