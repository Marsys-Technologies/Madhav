/**
 * KP frame doctrine (SS N-342 item 3 / N-339): Krishnamurti Paddhati cusps, sub-lords and
 * significators are read in the KRISHNAMURTI ayanamsha, never in the Lahiri primary, and every
 * surface that serves them says so.
 *
 * MIRROR of `platform/src/lib/retrieval/kp_frame.ts` (platform and platform-mcp are separate
 * packages: no cross-import, the constants are written twice). Parity is enforced by
 * `platform/src/lib/retrieval/registry/__tests__/kp_frame_parity.test.ts`.
 */
/** The stored ayanamsha id of the KP frame. */
export const KP_FRAME_AYANAMSHA = 'krishnamurti'

/** The label every KP-frame surface carries. */
export const KP_FRAME_LABEL = 'KP frame (Krishnamurti ayanamsha)'

/**
 * Label for a KP-frame payload read at `ayanamshaId`. Krishnamurti (or an unstated id, which the
 * KP handler defaults to Krishnamurti) -> the canonical label. Any other explicit id -> an honest
 * label naming the frame actually used, so a non-doctrinal KP read is never mistaken for the
 * canonical one.
 */
export function kpFrameLabelFor(ayanamshaId: string | null | undefined): string {
  if (ayanamshaId === undefined || ayanamshaId === null || ayanamshaId === '' || ayanamshaId === KP_FRAME_AYANAMSHA) {
    return KP_FRAME_LABEL
  }
  return `KP chain read at ${ayanamshaId} (explicit non-doctrinal frame; the ${KP_FRAME_LABEL} is the canonical one)`
}

/**
 * The KP-frame fact categories (SS N-358). MIRROR of `KP_FRAME_CATEGORIES` in
 * `platform/src/lib/retrieval/registry/kp_categories.ts` (separate packages; the list is written twice
 * and pinned by `platform-mcp/test/kp_reaching_wrappers.test.ts` against the platform source text).
 */
export const KP_FRAME_CATEGORIES: readonly string[] = [
  'cusp_kp_lords',
  'graha_kp_lords',
  'kp_cuspal_significators',
  'kp_house_significators',
  'kp_planet_significations',
  'kp_ruling_planets_natal',
]

/**
 * Does a `category` filter reach KP-frame rows? No filter (a default page, which the platform serves as a
 * mixed page that carries KP rows) or a comma list naming at least one KP-frame category: yes.
 */
export function categoryFilterReachesKpFrame(category: unknown): boolean {
  if (typeof category !== 'string' || category.trim() === '') return true
  return category.split(',').some((c) => KP_FRAME_CATEGORIES.includes(c.trim()))
}

/** Dasha systems that are NOT KP-frame rows. Anything else (vimshottari_kp, "all", an unrecognised value) is a KP-reaching page. */
const NON_KP_DASHA_SYSTEMS: ReadonlySet<string> = new Set([
  'vimshottari', 'yogini', 'ashtottari', 'chara', 'chara_karaka', 'narayana', 'shoola', 'kalachakra', 'mudda', 'naisargika',
])

/** Does a dasha `system` facet reach the KP-frame `vimshottari_kp` rows? Absent = the Vimshottari default: no. */
export function dashaSystemReachesKpFrame(system: unknown): boolean {
  if (typeof system !== 'string' || system.trim() === '') return false
  return !NON_KP_DASHA_SYSTEMS.has(system.trim().toLowerCase())
}

/**
 * The `ayanamsha_id` an MCP wrapper sends for a call that REACHES a KP-frame read (SS N-368): when the caller
 * OMITTED the id, none at all, so the platform handler applies its own default and does not mistake a
 * wrapper-pinned Lahiri for a request (a false "does not apply" note). An explicit id goes through `resolve`
 * (the wrapper's usual lenient normaliser). A call that cannot reach a KP-frame read keeps the wrapper's
 * Lahiri pin: `resolve(raw)`.
 */
export function ayanamshaArgForKpReach(
  raw: string | null | undefined,
  reachesKpFrame: boolean,
  resolve: (id?: string) => string,
): { ayanamsha_id?: string } {
  const omitted = raw === undefined || raw === null || String(raw).trim() === ''
  if (omitted && reachesKpFrame) return {}
  return { ayanamsha_id: resolve(omitted ? undefined : raw) }
}

/**
 * `ayanamsha_note` for an id the KP frame cannot even resolve (nonsense). The platform capability route
 * rejects an unknown id with a 400 BEFORE the KP handler runs, so the wrapper does not forward it: it is
 * ignored (never an error) and disclosed here, with PR-2's exact wording.
 */
export function kpFrameIgnoredNote(requested: string): string {
  return `KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope '${requested}' does not apply here`
}
