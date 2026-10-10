/**
 * ayanamsha_cross_check.ts — the labelled cross-check envelope (SS N-342 Q2/Q5/Q7, Lahiri-primary PR-3).
 * =====================================================================================================
 * LAHIRI (`lahiri_chitrapaksha`) is the PRIMARY reading everywhere. The other four stored ayanamshas
 * (true_chitra, krishnamurti, raman, surya_siddhanta_classical) appear ONLY as a LABELLED cross-check:
 * never merged into the primary answer, never reordered ahead of it, each one NAMED.
 *
 * TWO MODES of the SAME builder (SS N-361, "always-on means COMPACT"):
 *
 *   compact  every ALWAYS-ON identity cross-check (the `identity_cross_check` block and the identity-fact
 *            `ayanamsha_cross_check` on get_positions / get_dashas). SUMMARY ONLY: when all agree it is
 *            { heading, primary_id, scope, mode:'compact', agreement:'all_agree', summary:'Agrees across all
 *            five ayanamshas' } with NO per-ayanamsha entries and NO degrees; on dissent it adds ONLY the
 *            dissenting ayanamshas, each with the values it dissents on (`others` lists the dissenters only).
 *   full     the opt-in detail (`include_cross_check:true`, and the opt-in surfaces query_discoveries /
 *            query_pratijna): `primary`, all four others each NAMED, degrees shown, `density`.
 *
 * Response key: `ayanamsha_cross_check`. FULL shape (see `AyanamshaCrossCheck`):
 *
 *   { heading: 'Cross-check, not the reading', primary_id, scope, basis,
 *     agreement: 'all_agree' | 'agree_among_stored' | 'dissent' | 'incomplete',
 *     summary,                       // ONE line: "Agrees across all five ayanamshas", or the named dissent
 *     primary: { ayanamsha_id, label, values },
 *     others: [{ ayanamsha_id, label, status, values?, dissenting? }],   // serve order, primary removed
 *     density: { stored_ayanamshas, compared_facts, dissenting_ayanamshas } }
 *
 * or, when no honest comparison exists, `{ not_available: true, reason }` with reason
 * `single_ayanamsha_chart` (fewer than two ayanamshas stored: NEVER "1/1 agree") or
 * `primary_ayanamsha_not_stored` / `no_comparable_facts`, or `served_generation_unresolved` (SS N-361: the
 * served generation that fences the read could not be resolved; the read is NEVER made unfenced). When only
 * SOME compared facts are unresolved (e.g. the Mahadasha lord on the identity block) the others are still
 * compared and `facts_not_available: { <fact_key>: { not_available: true, reason } }` names the unresolved
 * ones; the agreement is then at best `incomplete` (a fact nobody read is never an agreement).
 *
 * Rules (CLAUDE.md §N.7 / §N.8, "an honest null beats an invented judgment"):
 *   - "Same answer" means CATEGORICAL equality only (a sign, a nakshatra, a dasha lord). Degrees are SHOWN
 *     (`degrees` beside a value) and are NEVER compared: two ayanamshas that place the Moon at different
 *     degrees of the same sign agree.
 *   - A missing value is never read as agreement: it makes the status `incomplete`, and the single line
 *     says so. "Agrees across all five ayanamshas" is produced only when all five ayanamshas are present
 *     and every compared fact is categorically equal, so the line has a detector that can read false.
 *   - The order is `AYANAMSHA_SERVE_ORDER` (Lahiri first), never alphabetical; the input row order is irrelevant.
 *   - Pure and deterministic: no I/O, no DB, no clock.
 *   - Derived POOLED values (phala_rectification_best, consensus tables) are NOT put through this envelope:
 *     they keep their own "consensus over five ayanamshas" label.
 *   - The KP frame stays Krishnamurti (labelled "KP frame (Krishnamurti ayanamsha)" where it is served); this
 *     envelope compares readings of the chart, it never relabels the KP frame as a disagreement with Lahiri.
 *
 * The platform-mcp response budget registers this key as TRIMMABLE (never hardFloor) so it is shed before
 * confirmed findings (platform-mcp/src/lib/response_budget.ts, `CROSS_CHECK_FIELDS`; parity pinned by
 * ayanamsha_cross_check.test.ts).
 */
import { AYANAMSHA_SERVE_ORDER, PRIMARY_AYANAMSHA } from './registry/constants'

/** The response key. Mirrored by platform-mcp `CROSS_CHECK_FIELDS` (parity test). */
export const CROSS_CHECK_KEY = 'ayanamsha_cross_check' as const

/**
 * The key of the ONE shared identity block (SS N-360): the same envelope shape as `ayanamsha_cross_check`,
 * built by the same builder, restricted to the four identity facts (Lagna sign, Moon sign, Moon nakshatra,
 * current Mahadasha lord). Carried by chart_snapshot and dossier (always on), by graha_portrait (the Moon
 * always; any other graha only with `include_cross_check:true`), never by get_chart_header. Mirrored by
 * platform-mcp `CROSS_CHECK_FIELDS` (trimmable, never hardFloor; parity test).
 */
export const IDENTITY_CROSS_CHECK_KEY = 'identity_cross_check' as const

/** The heading every cross-check carries: it is not the reading. */
export const CROSS_CHECK_HEADING = 'Cross-check, not the reading' as const

/** Short, fixed basis string (kept short: the identity form is attached to dasha/header answers). */
export const CROSS_CHECK_BASIS =
  'categorical equality only; degrees shown, never compared' as const

export const CROSS_CHECK_AGREE_ALL_LINE = 'Agrees across all five ayanamshas' as const

/** The opt-in boolean input every cross-check-carrying tool declares. */
export const INCLUDE_CROSS_CHECK_INPUT = 'include_cross_check' as const

/** The four IDENTITY FACTS that are always cross-checked, compact (SS N-342). */
export type IdentityFactKey = 'lagna_sign' | 'moon_sign' | 'moon_nakshatra' | 'maha_lord'

export const IDENTITY_FACT_SPECS: Readonly<Record<IdentityFactKey, CrossCheckFactSpec>> = {
  lagna_sign: { key: 'lagna_sign', label: 'Lagna sign' },
  moon_sign: { key: 'moon_sign', label: 'Moon sign' },
  moon_nakshatra: { key: 'moon_nakshatra', label: 'Moon nakshatra' },
  maha_lord: { key: 'maha_lord', label: 'current Mahadasha lord' },
}

/** All four identity facts, in display order. */
export const ALL_IDENTITY_FACT_KEYS: readonly IdentityFactKey[] = ['lagna_sign', 'moon_sign', 'moon_nakshatra', 'maha_lord']

/** One fact to compare (categorical). `label` is the human name used in the single line. */
export interface CrossCheckFactSpec {
  readonly key: string
  readonly label: string
}

/** One per-ayanamsha reading of one fact. `degrees` is shown beside the value and never compared. */
export interface CrossCheckInputRow {
  readonly ayanamsha_id: string
  readonly fact_key: string
  /** The categorical value (sign / nakshatra / lord / 'present'), or null when unread. */
  readonly value: string | null
  readonly degrees?: number | null
}

export type CrossCheckScope = 'identity_facts' | 'requested_facts'

export type CrossCheckAgreement = 'all_agree' | 'agree_among_stored' | 'dissent' | 'incomplete'

export type CrossCheckOtherStatus = 'agrees' | 'dissents' | 'incomplete' | 'no_rows'

export interface CrossCheckValue {
  readonly value: string | null
  readonly degrees?: number
}

export interface CrossCheckDissent {
  readonly fact_key: string
  readonly fact_label: string
  readonly value: string | null
  readonly primary_value: string | null
}

export interface CrossCheckOther {
  readonly ayanamsha_id: string
  readonly label: string
  readonly status: CrossCheckOtherStatus
  readonly values?: Readonly<Record<string, CrossCheckValue>>
  readonly dissenting?: readonly CrossCheckDissent[]
}

/** Compact (always-on) or full (opt-in) detail of the SAME envelope. */
export type CrossCheckMode = 'compact' | 'full'

/** A compared fact that could not be read honestly (its fence is unresolved): an entry, never an invented value. */
export interface CrossCheckFactUnavailable {
  readonly not_available: true
  readonly reason: CrossCheckUnavailableReason
}

/** Declares a fact the caller could not read honestly; it is excluded from the comparison and named in the envelope. */
export interface CrossCheckUnavailableFactSpec extends CrossCheckFactSpec {
  readonly reason: CrossCheckUnavailableReason
}

interface AyanamshaCrossCheckBase {
  readonly heading: typeof CROSS_CHECK_HEADING
  readonly primary_id: string
  readonly scope: CrossCheckScope
  readonly agreement: CrossCheckAgreement
  /** The single line: "Agrees across all five ayanamshas", or the named dissent. */
  readonly summary: string
  /** Facts that were not compared because their fence could not be resolved (absent when every fact was read). */
  readonly facts_not_available?: Readonly<Record<string, CrossCheckFactUnavailable>>
}

export interface AyanamshaCrossCheckFull extends AyanamshaCrossCheckBase {
  readonly mode?: 'full'
  readonly basis: string
  readonly primary: {
    readonly ayanamsha_id: string
    readonly label: string
    readonly values: Readonly<Record<string, CrossCheckValue>>
  }
  /** The other ayanamshas in serve order (the primary removed); each one named, never merged. */
  readonly others: readonly CrossCheckOther[]
  readonly density: {
    readonly stored_ayanamshas: number
    readonly compared_facts: number
    readonly dissenting_ayanamshas: number
  }
}

/** One dissenting ayanamsha in the compact form: its name and the values it dissents on, no degrees. */
export interface CrossCheckCompactDissenter {
  readonly ayanamsha_id: string
  readonly label: string
  readonly status: 'dissents'
  readonly dissenting: readonly CrossCheckDissent[]
}

export interface AyanamshaCrossCheckCompact extends AyanamshaCrossCheckBase {
  readonly mode: 'compact'
  /** ONLY the dissenting ayanamshas (absent when none dissents); never the agreeing ones, never degrees. */
  readonly others?: readonly CrossCheckCompactDissenter[]
}

export type AyanamshaCrossCheckAvailable = AyanamshaCrossCheckFull | AyanamshaCrossCheckCompact

export type CrossCheckUnavailableReason =
  | 'single_ayanamsha_chart'
  | 'served_generation_unresolved'
  | 'primary_ayanamsha_not_stored'
  | 'no_comparable_facts'
  | 'cross_check_read_failed'

export interface AyanamshaCrossCheckUnavailable {
  readonly not_available: true
  readonly reason: CrossCheckUnavailableReason
  readonly heading: typeof CROSS_CHECK_HEADING
  readonly primary_id: string
}

export type AyanamshaCrossCheck = AyanamshaCrossCheckAvailable | AyanamshaCrossCheckUnavailable

export interface BuildCrossCheckOptions {
  /** Facts to compare, in display order. Rows for other keys are ignored. */
  readonly facts: readonly CrossCheckFactSpec[]
  readonly scope?: CrossCheckScope
  /**
   * The ayanamshas known to be stored for this chart. When omitted it is derived from the ayanamshas
   * that have at least one input row. Pass it when an ayanamsha can be stored yet have no row for the
   * compared fact (e.g. a discovery motif absent under that ayanamsha).
   */
  readonly storedAyanamshas?: readonly string[]
  /**
   * `compact` = summary only (the always-on identity cross-checks); `full` = the per-ayanamsha detail
   * (opt-in). The builder's own default is `full` (the opt-in surfaces); every always-on call site passes
   * `compact` explicitly through `fetchIdentityCrossCheck` / `fetchPositionsCrossCheck`, which REQUIRE a mode.
   */
  readonly mode?: CrossCheckMode
  /**
   * Facts the caller could not read honestly because their fence is unresolved (CLAUDE.md §N.7). They are not
   * compared; they are named under `facts_not_available`, and the agreement is at best `incomplete`.
   */
  readonly unavailableFacts?: readonly CrossCheckUnavailableFactSpec[]
}

/** Display labels (fixed, serve-order vocabulary). A switch, not a map: this is a label, not an alias table. */
export function crossCheckAyanamshaLabel(id: string): string {
  switch (id) {
    case 'lahiri_chitrapaksha': return 'Lahiri'
    case 'true_chitra': return 'True Chitrapaksha'
    case 'krishnamurti': return 'Krishnamurti'
    case 'raman': return 'Raman'
    case 'surya_siddhanta_classical': return 'Surya Siddhanta'
    default: return id
  }
}

const SERVE_ORDER: readonly string[] = AYANAMSHA_SERVE_ORDER

/** Categorical comparison key: trim, collapse whitespace, casefold. Never numeric. */
function norm(value: string | null): string | null {
  if (value === null) return null
  const v = value.replace(/\s+/g, ' ').trim().toLowerCase()
  return v === '' ? null : v
}

function unavailable(reason: CrossCheckUnavailableReason, primaryId: string): AyanamshaCrossCheckUnavailable {
  return { not_available: true, reason, heading: CROSS_CHECK_HEADING, primary_id: primaryId }
}

const FIVE_WORDS: Readonly<Record<number, string>> = { 2: 'two', 3: 'three', 4: 'four', 5: 'five' }

/**
 * Build the labelled cross-check envelope from per-ayanamsha reads of categorical facts.
 *
 * @param rows       one row per (ayanamsha, fact); order irrelevant. INVARIANT / unknown ids are ignored.
 * @param primaryId  the ayanamsha whose answer was served (Lahiri unless the caller asked for another)
 */
export function buildAyanamshaCrossCheck(
  rows: readonly CrossCheckInputRow[],
  primaryId: string,
  options: BuildCrossCheckOptions & { readonly mode?: 'full' },
): AyanamshaCrossCheckFull | AyanamshaCrossCheckUnavailable
export function buildAyanamshaCrossCheck(
  rows: readonly CrossCheckInputRow[],
  primaryId: string,
  options: BuildCrossCheckOptions & { readonly mode: 'compact' },
): AyanamshaCrossCheckCompact | AyanamshaCrossCheckUnavailable
export function buildAyanamshaCrossCheck(
  rows: readonly CrossCheckInputRow[],
  primaryId: string,
  options: BuildCrossCheckOptions,
): AyanamshaCrossCheck
export function buildAyanamshaCrossCheck(
  rows: readonly CrossCheckInputRow[],
  primaryId: string,
  options: BuildCrossCheckOptions,
): AyanamshaCrossCheck {
  const facts = options.facts
  const scope: CrossCheckScope = options.scope ?? 'identity_facts'
  const mode: CrossCheckMode = options.mode ?? 'full'
  const unavailableFacts = options.unavailableFacts ?? []
  if (facts.length === 0) {
    return unavailableFacts.length > 0
      ? unavailable(unavailableFacts[0]!.reason, primaryId)
      : unavailable('no_comparable_facts', primaryId)
  }

  const factKeys = new Set(facts.map((f) => f.key))
  const relevant = rows.filter((r) => SERVE_ORDER.includes(r.ayanamsha_id) && factKeys.has(r.fact_key))

  // Which ayanamshas does this chart store? (explicit list, else those that have a relevant row)
  const storedSet = new Set<string>(
    (options.storedAyanamshas ?? relevant.map((r) => r.ayanamsha_id)).filter((id) => SERVE_ORDER.includes(id)),
  )
  const stored = SERVE_ORDER.filter((id) => storedSet.has(id))
  if (stored.length < 2) return unavailable('single_ayanamsha_chart', primaryId)
  if (!stored.includes(primaryId)) return unavailable('primary_ayanamsha_not_stored', primaryId)

  // (ayanamsha, fact) -> value; two rows that disagree for the same (ayanamsha, fact) are unread, not guessed.
  const cell = new Map<string, { value: string | null; degrees?: number }>()
  const cellKey = (a: string, k: string) => `${a}\u0000${k}`
  const conflict = new Set<string>()
  for (const r of relevant) {
    const key = cellKey(r.ayanamsha_id, r.fact_key)
    const incoming = { value: r.value, ...(typeof r.degrees === 'number' && Number.isFinite(r.degrees) ? { degrees: r.degrees } : {}) }
    const prev = cell.get(key)
    if (!prev) { cell.set(key, incoming); continue }
    if (norm(prev.value) !== norm(incoming.value)) conflict.add(key)
  }
  const read = (a: string, k: string): { value: string | null; degrees?: number } => {
    const key = cellKey(a, k)
    if (conflict.has(key)) return { value: null }
    return cell.get(key) ?? { value: null }
  }
  const valuesOf = (a: string): Record<string, CrossCheckValue> => {
    const out: Record<string, CrossCheckValue> = {}
    for (const f of facts) {
      const c = read(a, f.key)
      out[f.key] = { value: c.value, ...(c.degrees !== undefined ? { degrees: c.degrees } : {}) }
    }
    return out
  }

  const primaryValues = valuesOf(primaryId)
  const primaryUnread = facts.filter((f) => norm(primaryValues[f.key]!.value) === null)

  const others: CrossCheckOther[] = []
  const missingRows: string[] = []
  for (const id of SERVE_ORDER) {
    if (id === primaryId) continue
    const label = crossCheckAyanamshaLabel(id)
    if (!storedSet.has(id)) {
      others.push({ ayanamsha_id: id, label, status: 'no_rows' })
      missingRows.push(label)
      continue
    }
    const values = valuesOf(id)
    const dissenting: CrossCheckDissent[] = []
    let unread = 0
    for (const f of facts) {
      const mine = norm(values[f.key]!.value)
      const theirs = norm(primaryValues[f.key]!.value)
      if (mine === null || theirs === null) { unread += 1; continue }
      if (mine !== theirs) {
        dissenting.push({
          fact_key: f.key, fact_label: f.label,
          value: values[f.key]!.value, primary_value: primaryValues[f.key]!.value,
        })
      }
    }
    const status: CrossCheckOtherStatus = dissenting.length > 0 ? 'dissents' : unread > 0 ? 'incomplete' : 'agrees'
    const showValues = status !== 'agrees' || facts.some((f) => values[f.key]!.degrees !== undefined)
    others.push({
      ayanamsha_id: id, label, status,
      ...(showValues ? { values } : {}),
      ...(dissenting.length > 0 ? { dissenting } : {}),
    })
  }

  const dissenters = others.filter((o) => o.status === 'dissents')
  const incompletes = others.filter((o) => o.status === 'incomplete')
  const agreement: CrossCheckAgreement =
    dissenters.length > 0 ? 'dissent'
      : incompletes.length > 0 || primaryUnread.length > 0 ? 'incomplete'
        : missingRows.length > 0 ? 'agree_among_stored'
          : 'all_agree'

  let summary: string
  if (agreement === 'all_agree') {
    summary = CROSS_CHECK_AGREE_ALL_LINE
  } else if (agreement === 'agree_among_stored') {
    summary = `Agrees across the ${FIVE_WORDS[stored.length] ?? String(stored.length)} stored ayanamshas (no rows for: ${missingRows.join(', ')})`
  } else if (agreement === 'dissent') {
    const parts = dissenters.map((o) =>
      `${o.label}: ${o.dissenting!.map((d) => `${d.fact_label} ${d.value} (primary ${d.primary_value})`).join(', ')}`)
    summary = `Dissent: ${parts.join('; ')}`
    if (incompletes.length > 0) summary += `; not read: ${incompletes.map((o) => o.label).join(', ')}`
  } else {
    const who = primaryUnread.length > 0
      ? `the primary reading (${primaryUnread.map((f) => f.label).join(', ')})`
      : incompletes.map((o) => o.label).join(', ')
    summary = `Cannot confirm agreement: a compared value is unread for ${who}`
  }

  // Facts whose fence could not be resolved were NOT compared: the agreement is never read as complete, and the
  // line says so (a fact nobody read is never an agreement, §N.7 / §N.8).
  let finalAgreement: CrossCheckAgreement = agreement
  let factsNotAvailable: Record<string, CrossCheckFactUnavailable> | undefined
  if (unavailableFacts.length > 0) {
    factsNotAvailable = {}
    for (const f of unavailableFacts) factsNotAvailable[f.key] = { not_available: true, reason: f.reason }
    const note = `not cross-checked: ${unavailableFacts.map((f) => `${f.label} (${f.reason})`).join(', ')}`
    if (agreement === 'all_agree') {
      summary = `${CROSS_CHECK_AGREE_ALL_LINE} on ${facts.map((f) => f.label).join(', ')}; ${note}`
    } else {
      summary = `${summary}; ${note}`
    }
    if (agreement !== 'dissent') finalAgreement = 'incomplete'
  }

  if (mode === 'compact') {
    return {
      heading: CROSS_CHECK_HEADING,
      primary_id: primaryId,
      scope,
      mode: 'compact',
      agreement: finalAgreement,
      summary,
      ...(dissenters.length > 0
        ? {
            others: dissenters.map((o) => ({
              ayanamsha_id: o.ayanamsha_id, label: o.label, status: 'dissents' as const, dissenting: o.dissenting!,
            })),
          }
        : {}),
      ...(factsNotAvailable ? { facts_not_available: factsNotAvailable } : {}),
    }
  }

  return {
    heading: CROSS_CHECK_HEADING,
    primary_id: primaryId,
    scope,
    basis: CROSS_CHECK_BASIS,
    agreement: finalAgreement,
    summary,
    primary: { ayanamsha_id: primaryId, label: crossCheckAyanamshaLabel(primaryId), values: primaryValues },
    others,
    density: {
      stored_ayanamshas: stored.length,
      compared_facts: facts.length,
      dissenting_ayanamshas: dissenters.length,
    },
    ...(factsNotAvailable ? { facts_not_available: factsNotAvailable } : {}),
  }
}

/** True for the `{ not_available: true }` form. */
export function isCrossCheckUnavailable(c: AyanamshaCrossCheck): c is AyanamshaCrossCheckUnavailable {
  return (c as AyanamshaCrossCheckUnavailable).not_available === true
}

/** Convenience: the identity facts' specs in the canonical display order, filtered to `keys`. */
export function identityFactSpecs(keys: readonly IdentityFactKey[]): CrossCheckFactSpec[] {
  const order: IdentityFactKey[] = ['lagna_sign', 'moon_sign', 'moon_nakshatra', 'maha_lord']
  return order.filter((k) => keys.includes(k)).map((k) => IDENTITY_FACT_SPECS[k])
}

export { PRIMARY_AYANAMSHA }
