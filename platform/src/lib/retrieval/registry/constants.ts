/** The canonical ayanamsha key as stored in all bodha_* / kala_* / phala_* tables. */
export const DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'

/**
 * SS N-339 / N-342: LAHIRI is the PRIMARY reading at serve time for EVERY chart (global, not
 * per chart). Alias of DEFAULT_AYANAMSHA so call sites that mean "the reading we serve when the
 * caller did not choose" say so. An omitted `ayanamsha_id` means this value.
 */
export const PRIMARY_AYANAMSHA = DEFAULT_AYANAMSHA

/**
 * The five stored (real) ayanamshas in SERVE ORDER: the primary first, then the other four in
 * the project's canonical order. This is the ONE exported constant every serving surface that
 * lists or iterates the ayanamshas must use (labelled cross-check, planner axis, error text).
 * The `INVARIANT` sentinel is deliberately NOT here (see `INVARIANT_AYANAMSHA`).
 */
export const AYANAMSHA_SERVE_ORDER = [
  'lahiri_chitrapaksha',
  'true_chitra',
  'krishnamurti',
  'raman',
  'surya_siddhanta_classical',
] as const

export type ServedAyanamshaId = (typeof AYANAMSHA_SERVE_ORDER)[number]

/**
 * Capabilities whose CONTRACT is the Krishnamurti Paddhati frame (SS N-342: KP stays on
 * Krishnamurti BY DOCTRINE). The bridge does NOT inject Lahiri into these when `ayanamsha_id`
 * is omitted; their own handler default (`krishnamurti`) applies. An explicit value is still
 * validated and normalised. A capability whose uri or name mentions KP/Krishnamurti and has an
 * `ayanamsha_id` input MUST be listed here or the lahiri_primary_contract test fails.
 */
export const KP_FRAME_CAPABILITY_URIS: ReadonlySet<string> = new Set([
  'marsys://tool/L1/get_kp_cusps',
])

/**
 * Capabilities whose DEFAULT request reaches fact categories that are stored under
 * `ayanamsha_id = 'INVARIANT'` (ayanamsha-independent facts: birth tithi/vara/yoga/karana and the
 * other panchanga limbs, naisargika bala and the classical required_rupa, the cross-ayanamsha
 * nakshatra rows). These handlers filter with a bare `ayanamsha_id = $n`, so injecting Lahiri would
 * silently DROP those INVARIANT rows (e.g. `get_panchanga` would lose the birth tithi/vara anchors
 * and the MCP `kala_now_get` janma-resonance join with it). Until PR-2 changes those handlers to
 * read `ayanamsha_id IN ($n, 'INVARIANT')`, the bridge does NOT inject Lahiri on omission for
 * them (their pre-N-342 behaviour is preserved); an explicit value is still validated and
 * normalised. Remove an entry when its handler gains the INVARIANT-inclusive read.
 */
export const INVARIANT_BEARING_CAPABILITY_URIS: ReadonlySet<string> = new Set([
  'marsys://tool/L1/get_panchanga', // 31 of its 39 panchanga categories are INVARIANT
  'marsys://tool/L1/get_nakshatra', // nakshatra_cross_ayanamsha is INVARIANT
  'marsys://tool/L1/get_strength', // graha_shadbala_naisargika + graha_shadbala_total.required_rupa are INVARIANT
  'marsys://tool/L1/query_planet', // its shadbala leg is get_strength
])

/**
 * Fact categories stored under `ayanamsha_id = 'INVARIANT'` (ga_* writers). A call that explicitly
 * asks for one of these via `categories`/`category` is never narrowed to a single ayanamsha by the
 * bridge (that would return zero rows). `panchanga_*` categories are matched by prefix.
 */
export const INVARIANT_STORED_FACT_CATEGORIES: ReadonlySet<string> = new Set([
  'nakshatra_cross_ayanamsha',
  'graha_retrogression_state',
  'graha_combustion_state',
  'graha_speed_state',
  'graha_shadbala_naisargika',
  'graha_shadbala_total',
])
export const INVARIANT_STORED_FACT_CATEGORY_PREFIXES: readonly string[] = ['panchanga_']

/** Sentinel stored on facts that do not depend on the ayanamsha. Not a real ayanamsha. */
export const INVARIANT_AYANAMSHA = 'INVARIANT'

/**
 * Explicit opt-out: `ayanamsha_id: "all"` asks for raw multi-row access (no ayanamsha filter,
 * the pre-N-342 "omitted" behaviour). It is never a stored id and never a default.
 */
export const AYANAMSHA_ALL = 'all'
