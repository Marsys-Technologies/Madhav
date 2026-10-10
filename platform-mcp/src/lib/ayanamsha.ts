/**
 * Shared ayanāṃśa resolver for MCP serving paths (SS N-339 / N-342).
 *
 * LAHIRI (`lahiri_chitrapaksha`) is the PRIMARY reading for every chart. `chart_facts` contains
 * distinct rows for each stored school; `true_chitra` must remain reachable and is not a
 * spelling of Lahiri.
 *
 * MIRROR of `platform/src/lib/retrieval/chart_facts_helpers.ts` (platform and platform-mcp are
 * separate packages: no cross-import, the logic is written twice). The alias table and the
 * resolver below MUST stay identical to the platform helper; parity is enforced by
 * `platform/src/lib/retrieval/registry/__tests__/ayanamsha_parity.test.ts` (imports both files,
 * one shared input table); `platform-mcp/test/ayanamsha_tools.test.ts` pins this side's table.
 *
 * Two entry points:
 *   - `resolveChartFactsAyanamsha(id)` : LENIENT (historical contract used by every wrapper):
 *     falsy -> Lahiri, alias -> stored id, "all" -> "all", unknown ids pass through unchanged so
 *     the platform bridge (which validates) returns the authoritative error listing stored ids.
 *   - `resolveAyanamshaArg(raw)` / `normalizeAyanamshaId(raw)` : STRICT (identical to the
 *     platform helper): unknown ids are an error that lists the stored ids.
 */

/** The primary reading at serve time. */
export const PRIMARY_AYANAMSHA = 'lahiri_chitrapaksha'

/** Stored (real) ayanamshas in SERVE ORDER: primary first, then the project's canonical order. */
export const AYANAMSHA_SERVE_ORDER = [
  'lahiri_chitrapaksha',
  'true_chitra',
  'krishnamurti',
  'raman',
  'surya_siddhanta_classical',
] as const

/** Sentinel stored on facts that do not depend on the ayanamsha. Not a real ayanamsha. */
export const INVARIANT_AYANAMSHA = 'INVARIANT'

/** Explicit opt-out: raw multi-row access, no ayanamsha filter. Never a stored id. */
export const AYANAMSHA_ALL = 'all'

/** Stored ids a caller may name, in serve order. Excludes the sentinel and "all". */
export const STORED_AYANAMSHA_IDS: readonly string[] = AYANAMSHA_SERVE_ORDER

/**
 * Alias -> stored id. Keys are canonical (lower case, whitespace/hyphen runs -> `_`). Superset
 * of every vocabulary in the repo. `chitra`/`chitrapaksha` keep the pre-existing meaning
 * (True Chitrapaksha).
 */
const CHART_FACTS_AYANAMSHA_ALIASES: Readonly<Record<string, string>> = {
  lahiri: 'lahiri_chitrapaksha',
  lahiri_chitra: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha',
  true_chitra: 'true_chitra',
  true_citra: 'true_chitra',
  true_chitra_paksha: 'true_chitra',
  true_chitrapaksha: 'true_chitra',
  chitra: 'true_chitra',
  chitrapaksha: 'true_chitra',
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

/** The alias keys, exported so the parity test can enumerate the vocabulary. */
export const AYANAMSHA_ALIAS_KEYS: readonly string[] = Object.keys(CHART_FACTS_AYANAMSHA_ALIASES)

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
 * throws. Identical to the platform helper.
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
  const stored = CHART_FACTS_AYANAMSHA_ALIASES[key]
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
 * Omitted/blank -> Lahiri. Unknown -> throws `InvalidAyanamshaError`.
 */
export function normalizeAyanamshaId(raw: unknown): string | null {
  const r = resolveAyanamshaArg(raw)
  if (!r.ok) throw new InvalidAyanamshaError(r.received)
  return r.ayanamsha_id
}

/**
 * Lenient resolver used by every MCP wrapper that forwards an id to the platform. Falsy ->
 * Lahiri; known alias (any case) -> stored id; "all" -> "all" (the platform bridge turns it into
 * the unfiltered opt-out); an unknown id passes through unchanged so the platform bridge returns
 * the authoritative error listing the stored ids (never a silent zero-row result).
 */
export function resolveChartFactsAyanamsha(id?: string): string {
  const r = resolveAyanamshaArg(id)
  if (r.ok) return r.ayanamsha_id ?? AYANAMSHA_ALL
  return typeof id === 'string' ? id : r.received
}
