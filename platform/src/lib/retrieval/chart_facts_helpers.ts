/**
 * chart_facts_helpers.ts — the ONE platform-side ayanamsha normaliser (SS N-339 / N-342).
 * ========================================================================================
 * Canonical path named by `platform/scripts/governance/check_no_local_ayanamsha_map.py`
 * (D-01c): a file-local ayanamsha alias map anywhere else in `platform/src` is a CI failure.
 *
 * Owner decision N-339: all five ayanamshas stay computed and stored; LAHIRI
 * (`lahiri_chitrapaksha`) is the PRIMARY reading at serve time for EVERY chart (global, not
 * per chart). SS decision N-342 fixes the boundary contract implemented here:
 *
 *   - omitted / null / "" / whitespace  -> Lahiri (`PRIMARY_AYANAMSHA`)
 *   - short ids and any case/whitespace -> the STORED long id (`lahiri` -> `lahiri_chitrapaksha`)
 *   - `"all"` (any case)                -> explicit opt-out: raw multi-row access, no filter
 *   - the `INVARIANT` sentinel          -> accepted verbatim (stored data carries it)
 *   - anything else                     -> an ERROR that lists the stored ids, NEVER a silent
 *                                          zero-row query
 *
 * MIRROR: `platform-mcp/src/lib/ayanamsha.ts` carries the same alias table and the same
 * resolver (the two packages are separate, no cross-import). Parity is enforced by
 * `registry/__tests__/ayanamsha_parity.test.ts` (imports both files; shared input table,
 * identical results). Any
 * change here MUST be made in both files.
 *
 * Pure: no I/O, no DB.
 */
import {
  AYANAMSHA_ALL,
  AYANAMSHA_SERVE_ORDER,
  INVARIANT_AYANAMSHA,
  INVARIANT_BEARING_CAPABILITY_URIS,
  INVARIANT_STORED_FACT_CATEGORIES,
  INVARIANT_STORED_FACT_CATEGORY_PREFIXES,
  KP_FRAME_CAPABILITY_URIS,
  PRIMARY_AYANAMSHA,
} from './registry/constants'

export { AYANAMSHA_ALL, AYANAMSHA_SERVE_ORDER, INVARIANT_AYANAMSHA, PRIMARY_AYANAMSHA }

/** Stored ids a caller may name, in serve order (Lahiri first). Excludes the sentinel and "all". */
export const STORED_AYANAMSHA_IDS: readonly string[] = AYANAMSHA_SERVE_ORDER

/**
 * Alias -> stored id. Keys are in canonical form (lower case, whitespace/hyphen runs -> `_`).
 * Superset of every vocabulary already in the repo: MCP resolver, `lib/ayanamsha.ts`
 * (chart create/edit), sidecar `panchang_engine` (`true_chitra_paksha`), PyJHora adapter,
 * generated chat schema text (`LAHIRI`), and the aliases ratified in N-342.
 * `chitrapaksha` = LAHIRI (the standard name of Lahiri's ayanamsha; SS N-348); `chitra` keeps its pre-existing MCP meaning (True Chitrapaksha).
 */
const AYANAMSHA_ALIAS_TABLE: Readonly<Record<string, string>> = {
  lahiri: 'lahiri_chitrapaksha',
  lahiri_chitra: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha',
  true_chitra: 'true_chitra',
  true_citra: 'true_chitra',
  true_chitra_paksha: 'true_chitra',
  true_chitrapaksha: 'true_chitra',
  chitra: 'true_chitra',
  chitrapaksha: 'lahiri_chitrapaksha', // Chitrapaksha is the standard name of Lahiri's ayanamsha (SS N-348); `chitra` keeps its older MCP meaning below
  kp: 'krishnamurti',
  krishnamurti: 'krishnamurti',
  krishnamurti_paddhati: 'krishnamurti',
  raman: 'raman',
  surya_siddhanta: 'surya_siddhanta_classical',
  surya_siddhanta_classical: 'surya_siddhanta_classical',
  suryasiddhanta: 'surya_siddhanta_classical',
  ss: 'surya_siddhanta_classical',
  invariant: INVARIANT_AYANAMSHA,
}

/** The alias keys, exported so the parity test and docs can enumerate the vocabulary. */
export const AYANAMSHA_ALIAS_KEYS: readonly string[] = Object.keys(AYANAMSHA_ALIAS_TABLE)

function canonicalKey(raw: string): string {
  return raw.trim().toLowerCase().replace(/[\s-]+/g, '_')
}

export type AyanamshaResolution =
  | { ok: true; ayanamsha_id: string; source: 'omitted' | 'explicit' }
  | { ok: true; ayanamsha_id: null; source: 'all' }
  | { ok: false; received: string; message: string; stored_ids: readonly string[] }

/** Error text shared by every rejection (lists the stored ids so the caller can self-correct). */
export function invalidAyanamshaMessage(received: string): string {
  return (
    `Unknown ayanamsha_id ${JSON.stringify(received)}. Stored ayanamsha ids: ` +
    `${STORED_AYANAMSHA_IDS.join(', ')} (plus the ${INVARIANT_AYANAMSHA} sentinel). ` +
    `Short aliases (lahiri, kp, ...) and any letter case are accepted; omit ayanamsha_id for ` +
    `${PRIMARY_AYANAMSHA} (the primary reading); pass "${AYANAMSHA_ALL}" for raw multi-ayanamsha rows.`
  )
}

/**
 * Resolve a caller-supplied `ayanamsha_id` to its serve-time meaning. Total and pure: never
 * throws, never returns a stored id the caller did not (directly or by omission) ask for.
 */
export function resolveAyanamshaArg(raw: unknown): AyanamshaResolution {
  if (raw === undefined || raw === null) {
    return { ok: true, ayanamsha_id: PRIMARY_AYANAMSHA, source: 'omitted' }
  }
  if (typeof raw !== 'string') {
    let received: string
    try {
      received = typeof raw === 'object' ? JSON.stringify(raw) : String(raw)
    } catch {
      received = String(raw)
    }
    return { ok: false, received, message: invalidAyanamshaMessage(received), stored_ids: STORED_AYANAMSHA_IDS }
  }
  if (raw.trim() === '') {
    return { ok: true, ayanamsha_id: PRIMARY_AYANAMSHA, source: 'omitted' }
  }
  const key = canonicalKey(raw)
  if (key === AYANAMSHA_ALL) return { ok: true, ayanamsha_id: null, source: 'all' }
  const stored = AYANAMSHA_ALIAS_TABLE[key]
  if (stored !== undefined) return { ok: true, ayanamsha_id: stored, source: 'explicit' }
  return { ok: false, received: raw, message: invalidAyanamshaMessage(raw), stored_ids: STORED_AYANAMSHA_IDS }
}

/** Thrown by the throwing entry points; carries the stored ids for structured error surfaces. */
export class InvalidAyanamshaError extends Error {
  readonly code = 'invalid_ayanamsha_id'
  readonly received: string
  readonly stored_ids: readonly string[]
  constructor(received: string) {
    super(invalidAyanamshaMessage(received))
    this.name = 'InvalidAyanamshaError'
    this.received = received
    this.stored_ids = STORED_AYANAMSHA_IDS
  }
}

/**
 * Normalise an `ayanamsha_id` to a stored id, or `null` for the explicit `"all"` opt-out.
 * Omitted/blank -> Lahiri. Unknown -> throws `InvalidAyanamshaError` (never a silent zero-row id).
 */
export function normalizeAyanamshaId(raw: unknown): string | null {
  const r = resolveAyanamshaArg(raw)
  if (!r.ok) throw new InvalidAyanamshaError(r.received)
  return r.ayanamsha_id
}

/**
 * Apply the serve-time ayanamsha contract to a capability's handler args (returns a new object).
 *
 * - `inject: true`  (default): omitted -> `ayanamsha_id = lahiri_chitrapaksha`.
 * - `inject: false`: omitted stays omitted (the handler's own doctrinal default applies, e.g.
 *   the KP cusp tools stay on Krishnamurti). An explicit value is still validated/normalised.
 * - `"all"`: `ayanamsha_id` is REMOVED (the handler's unfiltered path) and
 *   `ayanamsha_scope: "all"` is set so handlers that default an omitted id to Lahiri can tell
 *   an explicit opt-out from an omission.
 * - Unknown id: throws `InvalidAyanamshaError` listing the stored ids.
 */
export function applyAyanamshaContract(
  args: Record<string, unknown>,
  opts: { inject?: boolean } = {},
): Record<string, unknown> {
  const inject = opts.inject !== false
  const r = resolveAyanamshaArg(args['ayanamsha_id'])
  if (!r.ok) throw new InvalidAyanamshaError(r.received)
  const out: Record<string, unknown> = { ...args }
  if (r.source === 'all') {
    delete out['ayanamsha_id']
    out['ayanamsha_scope'] = AYANAMSHA_ALL
    return out
  }
  if (r.source === 'omitted') {
    if (inject) out['ayanamsha_id'] = r.ayanamsha_id
    else delete out['ayanamsha_id']
    return out
  }
  out['ayanamsha_id'] = r.ayanamsha_id
  return out
}

function isInvariantStoredCategory(c: unknown): boolean {
  return (
    typeof c === 'string' &&
    (INVARIANT_STORED_FACT_CATEGORIES.has(c) ||
      INVARIANT_STORED_FACT_CATEGORY_PREFIXES.some((p) => c.startsWith(p)))
  )
}

/**
 * Whether an OMITTED `ayanamsha_id` may be defaulted to Lahiri for this capability + call.
 * False (omission stays omitted) for:
 *   - KP-frame capabilities (`KP_FRAME_CAPABILITY_URIS`): their doctrinal default is Krishnamurti;
 *   - INVARIANT-bearing capabilities (`INVARIANT_BEARING_CAPABILITY_URIS`) and any call whose
 *     explicit `categories`/`category` names an INVARIANT-stored category: a single-ayanamsha
 *     filter would silently drop those ayanamsha-independent rows (see constants.ts).
 */
export function shouldInjectPrimaryAyanamsha(
  cap: { uri: string },
  args: Record<string, unknown>,
): boolean {
  if (KP_FRAME_CAPABILITY_URIS.has(cap.uri)) return false
  if (INVARIANT_BEARING_CAPABILITY_URIS.has(cap.uri)) return false
  const cats = args['categories']
  if (Array.isArray(cats) && cats.some(isInvariantStoredCategory)) return false
  if (isInvariantStoredCategory(args['category'])) return false
  return true
}

/**
 * Capability-level entry point shared by the platform dispatchers: applies
 * `applyAyanamshaContract` ONLY when the capability's input schema declares `ayanamsha_id`.
 * Omission is defaulted to Lahiri only where `shouldInjectPrimaryAyanamsha` allows and
 * `opts.inject !== false` (the MCP capability route passes `inject: false`: it validates and
 * normalises but leaves omission to the caller/handler). A capability with no `ayanamsha_id`
 * input gets its args back untouched (same object).
 */
export function applyAyanamshaContractForCapability(
  cap: { uri: string; input_schema?: Record<string, unknown> | undefined },
  args: Record<string, unknown>,
  opts: { inject?: boolean } = {},
): Record<string, unknown> {
  if (!cap.input_schema || !Object.prototype.hasOwnProperty.call(cap.input_schema, 'ayanamsha_id')) {
    return args
  }
  return applyAyanamshaContract(args, {
    inject: opts.inject !== false && shouldInjectPrimaryAyanamsha(cap, args),
  })
}
