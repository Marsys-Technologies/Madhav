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
 * Capabilities whose DEFAULT request reaches fact categories stored under
 * `ayanamsha_id = 'INVARIANT'` and whose handler still filters with a bare `ayanamsha_id = $n`
 * (which would silently DROP those rows), so the bridge must NOT inject Lahiri for them.
 *
 * EMPTY since Lahiri-primary PR-2: get_panchanga, get_nakshatra, get_strength (and query_planet,
 * whose shadbala leg is get_strength) now read `ayanamsha_id IN ($n, 'INVARIANT')`
 * (registry/handler_ayanamsha.ts `pushAyanamshaFilter(..., { includeInvariant: true })`), as do
 * get_positions and get_divisionals, so the bridge injects Lahiri for all of them. The set and
 * its mechanism are kept for a future handler that cannot take the INVARIANT-inclusive read.
 */
export const INVARIANT_BEARING_CAPABILITY_URIS: ReadonlySet<string> = new Set<string>([])

/**
 * Fact categories stored under `ayanamsha_id = 'INVARIANT'` (ga_* writers). A call that explicitly
 * asks for one of these via `categories`/`category` is never narrowed to a single ayanamsha by the
 * bridge (that would return zero rows). `panchanga_*` categories are matched by prefix.
 *
 * PROVISIONAL: replace with the live-read result after the post-round restore (see
 * ONE_AYANAMSHA/LAHIRI_PRIMARY_PR_SPECS.md). This list was built from WRITER CODE (ga_panchanga_writer,
 * ga_strength_writer, ga_nakshatra, ga_positions_writer), NOT from the database, and is NOT verified.
 * The authoritative read-only query is:
 *
 *   SELECT DISTINCT fact_category FROM chart_facts WHERE ayanamsha_id = 'INVARIANT' ORDER BY 1;
 *
 * `registry/__tests__/invariant_categories_pin.test.ts` pins the exact list, so changing it later is
 * a deliberate, visible edit. (Handlers do not depend on this list: their INVARIANT-inclusive
 * filter is category-agnostic; the list only decides when the BRIDGE declines to narrow an
 * explicit `categories` request.)
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
