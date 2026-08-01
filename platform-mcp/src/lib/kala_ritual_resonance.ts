/**
 * kala_ritual_resonance.ts — ṢAḌ-DARŚANA W4 Lane R, registry items 37 (full) + 6.
 * ==========================================================================
 * Mode 1's four-factor opportunity scorer (KALA_W4_UPAYA_DESIGN_v1_0.md §3.3),
 * the configuration→rite mapping, and the item-6 activity-rule join.
 *
 * ONE-ENGINE RULE: this file calls `adjudicateCandidates` from the FROZEN
 * `kala_lattice_query.ts` for the election-quality factor. It defines no second
 * adjudicator, no second ledger builder, and no second Pareto `dominates`.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * THE FOUR FACTORS, AND THE RULE THAT KEEPS MODE 1 SHIPPABLE (Elevation §8)
 *
 * | Factor              | Source                                        | When unavailable |
 * |---------------------|-----------------------------------------------|------------------|
 * | structural_resonance| brahma_activity_ontology.significators ×      | honest_empty NAMING which of the three legs was missing |
 * |                     | brahma_remedy_corpus.deity/planet ×           | |
 * |                     | bodha_rm_resonances (THIS chart)              | |
 * | temporal_intensity  | the field's λ — kala_field_windows            | not_computed (field empty — ka_kshetra has written no rows; the N_e critical path) |
 * | election_quality    | the lattice + adjudicateCandidates' ledger    | honest_empty |
 * | rarity              | cohort-scored scarcity via bg_cohort          | not_computed if the cohort asset is dormant |
 *
 * **A factor that is not computed is DROPPED FROM THE PRODUCT and the product is
 * RENORMALISED over the factors actually present — never imputed, never silently
 * zero-filled** (Elevation §6.1 / the ADJUDICATION-10 precedent). The served
 * vector ALWAYS states which factors were present, so a caller can never mistake
 * a 3-factor score for a 4-factor one. Gate G5 asserts exactly this: "a 4-factor
 * vector with an imputed value" and "a score with no factor-state breakdown" are
 * both FAILs.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * REGISTRY ITEM 6 — the rite-specific resonance join, and its RAIL
 *
 * `bg_muhurta_activity_rules` (329 rows) keys on an INTEGER `factor_id` per
 * `factor_type ∈ {tithi, nakshatra, vara}`. Before W4 the lattice carried limb
 * NAMES only, so the item-36 engine excluded its `rite_specific_resonance`
 * Pareto axis with the disclosed reason that resolving names to ids "would
 * require a mapping table this lane refuses to invent (B.10)". ADJUDICATION-10
 * accepted that exclusion on condition it stay explicit.
 *
 * Migration 530 makes the map REAL rather than invented: the `vara`, `nakshatra`
 * and `tithi` lattice families carry `detail.factor_id` read DIRECTLY from
 * `panchang_engine`'s own numbered tables — the same source
 * `bg_muhurta_activity_rules.factor_id` was populated from
 * (`shastra_tables.EVENT_TABLES`). The join below therefore rests on ONE
 * deterministic source.
 *
 * **RAIL (design §3.3, binding):** this join is legitimate ONLY while the
 * emitter genuinely carries the id from panchang_engine. `joinActivityRules`
 * reads `detail.factor_id` and NOTHING ELSE — it contains no name→id table, and
 * an atom without a usable `factor_id` is reported as unjoinable rather than
 * matched by name. If a future edit removes `detail.factor_id`, this scorer
 * degrades to `not_computed` with a reason, which is the correct behaviour.
 *
 * **What did NOT close, disclosed here as well as in the census:** the item-36
 * engine's own `rite_specific_resonance` PARETO AXIS is still listed in
 * `kala_lattice_query.ts`'s `EXCLUDED_AXES`. That file is FROZEN for W4 and
 * `EXCLUDED_AXES` is a module-private `const` with no injection point, so Lane R
 * stopped and reported rather than editing a frozen file. The DATA-LAYER join is
 * live here; the ENGINE AXIS remains excluded pending a one-line unfreeze PR.
 * See census row `rite_specific/activity_rule_pareto_axis_in_frozen_engine`.
 */

import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import {
  adjudicateCandidates,
  type CandidateInterval,
  type JudgmentLedger,
  type LatticeFactorRow,
  type LatticeSubstrate,
} from './kala_lattice_query.js'

// ══════════════════════════════════════════════════════════════════════════════
// Factor vector
// ══════════════════════════════════════════════════════════════════════════════

export type FactorState = 'computed' | 'honest_empty' | 'not_computed'

export interface ScoredFactor {
  /** `null` whenever `state !== 'computed'` — an honest null, NEVER a zero
   *  standing in for "I don't know" (§N.7 item 6). */
  value: number | null
  state: FactorState
  /** Required in substance whenever `state !== 'computed'`. */
  reason: string | null
  /** Names the substrate this factor read, so a caller can audit the claim. */
  source: string
}

export interface RitualScoreVector {
  structural_resonance: ScoredFactor
  temporal_intensity: ScoredFactor
  election_quality: ScoredFactor
  rarity: ScoredFactor
  /** Item 6's factor. Reported alongside the four so it can never be mistaken
   *  for one of Elevation §8's named four, and so its own honest state is
   *  visible independently. */
  rite_specific_resonance: ScoredFactor
  /** The renormalised product over the factors that were actually `computed`.
   *  `null` when NO factor computed — an honest empty score, not a zero. */
  composite: number | null
  /** Exactly which factors entered `composite`. A caller reading a 3-name list
   *  cannot mistake the score for a 4-factor one (gate G5). */
  factors_present: string[]
  factors_absent: string[]
  composite_method: string
}

const RENORMALISATION_NOTE =
  'composite = the geometric mean of the factors whose state is `computed`, i.e. the product ' +
  'renormalised over PRESENT factors only. An absent factor is DROPPED, never imputed and never ' +
  'zero-filled — zero-filling would silently rank every candidate equal on that axis while ' +
  'reading as a computed comparison (Elevation §6.1; the ADJUDICATION-10 precedent). ' +
  'factors_present / factors_absent name the split on every vector.'

export function composeScoreVector(parts: {
  structural_resonance: ScoredFactor
  temporal_intensity: ScoredFactor
  election_quality: ScoredFactor
  rarity: ScoredFactor
  rite_specific_resonance: ScoredFactor
}): RitualScoreVector {
  const named: [string, ScoredFactor][] = [
    ['structural_resonance', parts.structural_resonance],
    ['temporal_intensity', parts.temporal_intensity],
    ['election_quality', parts.election_quality],
    ['rarity', parts.rarity],
    ['rite_specific_resonance', parts.rite_specific_resonance],
  ]
  const present = named.filter(([, f]) => f.state === 'computed' && typeof f.value === 'number')
  const absent = named.filter(([, f]) => !(f.state === 'computed' && typeof f.value === 'number'))
  const composite =
    present.length === 0
      ? null
      : Math.pow(
          present.reduce((acc, [, f]) => acc * Math.max(0, Math.min(1, f.value as number)), 1),
          1 / present.length,
        )
  return {
    ...parts,
    composite: composite === null ? null : Number(composite.toFixed(4)),
    factors_present: present.map(([k]) => k),
    factors_absent: absent.map(([k]) => k),
    composite_method: RENORMALISATION_NOTE,
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// Item 6 — the activity-rule join
// ══════════════════════════════════════════════════════════════════════════════

export interface ActivityRuleRow {
  activity_class: string
  factor_type: 'tithi' | 'nakshatra' | 'vara'
  factor_id: number
  quality_score: number
  source_citation: string
}

/** The eight activity classes `bg_muhurta_activity_rules`'s CHECK admits. */
export const ACTIVITY_CLASSES = [
  'vivah',
  'griha_pravesh',
  'vyapara',
  'yatra',
  'property_purchase',
  'mantra_initiation',
  'upaya_ritual',
  'sadhana_initiation',
] as const

export type ActivityClass = (typeof ACTIVITY_CLASSES)[number]

export interface ActivityRuleFetch {
  rows: ActivityRuleRow[]
  available: boolean
  unavailable_reason: string | null
}

export async function fetchActivityRules(
  activityClass: ActivityClass | null,
  principal: Principal,
): Promise<ActivityRuleFetch> {
  try {
    const { status, envelope } = await callPlatformPrimitive(
      'query_parihara_graph',
      {
        sections: ['activity_rules'],
        ...(activityClass ? { activity_class: activityClass } : {}),
      },
      principal,
    )
    if (status !== 200 || !envelope.ok) {
      return { rows: [], available: false, unavailable_reason: `query_parihara_graph returned status ${status}` }
    }
    const result = envelope.result as Record<string, unknown> | null
    const section = result?.['activity_rules'] as { rows?: unknown } | undefined
    if (section === undefined) {
      return {
        rows: [],
        available: false,
        unavailable_reason: 'query_parihara_graph returned no activity_rules section',
      }
    }
    const rows = Array.isArray(section.rows) ? (section.rows as ActivityRuleRow[]) : []
    return { rows, available: true, unavailable_reason: null }
  } catch (err) {
    return { rows: [], available: false, unavailable_reason: `query_parihara_graph threw: ${String(err)}` }
  }
}

export interface ActivityJoinResult {
  /** Mean `quality_score` across every (factor_type, factor_id) that BOTH the
   *  lattice atoms and the rule table carry. `null` when nothing joined. */
  score: number | null
  /** Every rule row that matched, with the lattice atom it matched through —
   *  the audit trail for the join. */
  matched: { factor_type: string; factor_id: number; quality_score: number; source_citation: string }[]
  /** Lattice atoms in the window whose family is joinable but which carry no
   *  usable `detail.factor_id`. A NON-ZERO value here means the emitter has
   *  stopped carrying the canonical id and the RAIL is broken — reported, never
   *  papered over by falling back to a name match. */
  unjoinable_atoms: number
  reason: string | null
}

/**
 * Item 6's join. Deterministic, id-only, no name→id table anywhere.
 *
 * Reads `detail.factor_id` off `vara` / `nakshatra` / `tithi` lattice atoms and
 * looks it up in `bg_muhurta_activity_rules` by `(factor_type, factor_id)`.
 * An atom whose `detail.factor_id` is missing or non-numeric is counted in
 * `unjoinable_atoms` and CONTRIBUTES NOTHING — it is never rescued by matching
 * on `factor_key`, because a name match is exactly the hand-mapped
 * correspondence ADJUDICATION-10 refused (B.10).
 */
export function joinActivityRules(
  atoms: LatticeFactorRow[],
  rules: ActivityRuleRow[],
  activityClass: ActivityClass,
): ActivityJoinResult {
  const JOINABLE = new Set(['vara', 'nakshatra', 'tithi'])
  const byKey = new Map<string, ActivityRuleRow>()
  for (const r of rules) {
    if (r.activity_class !== activityClass) continue
    byKey.set(`${r.factor_type}:${r.factor_id}`, r)
  }

  const matched: ActivityJoinResult['matched'] = []
  let unjoinable = 0
  const seen = new Set<string>()

  for (const atom of atoms) {
    if (!JOINABLE.has(atom.factor_family)) continue
    const raw = (atom.detail as { factor_id?: unknown } | null)?.factor_id
    const fid = typeof raw === 'number' ? raw : Number(raw)
    if (!Number.isFinite(fid)) {
      unjoinable += 1
      continue
    }
    const key = `${atom.factor_family}:${fid}`
    if (seen.has(key)) continue
    seen.add(key)
    const rule = byKey.get(key)
    if (rule) {
      matched.push({
        factor_type: rule.factor_type,
        factor_id: rule.factor_id,
        quality_score: Number(rule.quality_score),
        source_citation: rule.source_citation,
      })
    }
  }

  if (matched.length === 0) {
    return {
      score: null,
      matched: [],
      unjoinable_atoms: unjoinable,
      reason:
        unjoinable > 0
          ? `no lattice atom in this window carried a usable detail.factor_id (${unjoinable} atom(s) ` +
            'were unjoinable). The item-6 RAIL requires the id to come from panchang_engine\'s own ' +
            'numbered tables via bg_muhurta_lattice.py; a name-based fallback is deliberately NOT ' +
            'implemented, because that is the hand-mapped correspondence ADJUDICATION-10 refused (B.10).'
          : `no bg_muhurta_activity_rules row exists for activity_class='${activityClass}' at any ` +
            'tithi/nakshatra/vara id present in this window. An honest empty join, not a defect: the ' +
            'rule table is sparse by construction (EVENT_TABLES lists only the limbs a source grades).',
    }
  }

  const score = matched.reduce((a, m) => a + m.quality_score, 0) / matched.length
  return { score: Number(score.toFixed(4)), matched, unjoinable_atoms: unjoinable, reason: null }
}

// ══════════════════════════════════════════════════════════════════════════════
// Structural resonance — the three-leg join, with per-leg honesty
// ══════════════════════════════════════════════════════════════════════════════

export interface RemedyCorpusRow {
  remedy_id?: string
  planet?: string | null
  deity?: string | null
  remedy_type?: string | null
  citation?: string | null
  source_citation?: string | null
}

export interface RmResonanceRow {
  graha?: string | null
  resonance_score?: number | null
  weakness_score?: number | null
  remedy_priority_class?: string | null
}

export interface StructuralSubstrate {
  remedy_rows: RemedyCorpusRow[]
  resonance_rows: RmResonanceRow[]
  remedy_available: boolean
  resonance_available: boolean
  /** `brahma_activity_ontology` has NO retrieval capability in this estate
   *  (verified: no descriptor under
   *  platform/src/lib/retrieval/registry/layers/L0_brahmagyan/). Adding one is
   *  outside Lane R's declared file ownership (design §0.1), so this leg is
   *  reported unavailable BY NAME rather than silently substituted. */
  activity_ontology_available: false
  missing_legs: string[]
}

export async function fetchStructuralSubstrate(
  chartId: string,
  principal: Principal,
): Promise<StructuralSubstrate> {
  const missing: string[] = []

  let remedy_rows: RemedyCorpusRow[] = []
  let remedy_available = false
  try {
    const { status, envelope } = await callPlatformPrimitive('query_remedy_corpus', { limit: 200 }, principal)
    if (status === 200 && envelope.ok) {
      const r = envelope.result as { rows?: unknown } | null
      remedy_rows = Array.isArray(r?.rows) ? (r.rows as RemedyCorpusRow[]) : []
      remedy_available = true
    } else {
      missing.push(`brahma_remedy_corpus (query_remedy_corpus status ${status})`)
    }
  } catch (err) {
    missing.push(`brahma_remedy_corpus (${String(err)})`)
  }

  let resonance_rows: RmResonanceRow[] = []
  let resonance_available = false
  try {
    const { status, envelope } = await callPlatformPrimitive(
      'query_rm_resonances',
      { chart_id: chartId, limit: 100 },
      principal,
    )
    if (status === 200 && envelope.ok) {
      const r = envelope.result as { rows?: unknown } | null
      resonance_rows = Array.isArray(r?.rows) ? (r.rows as RmResonanceRow[]) : []
      resonance_available = true
    } else {
      missing.push(`bodha_rm_resonances (query_rm_resonances status ${status})`)
    }
  } catch (err) {
    missing.push(`bodha_rm_resonances (${String(err)})`)
  }

  missing.push(
    'brahma_activity_ontology (no retrieval capability exists for this table in the estate; ' +
      'adding one is outside Lane R\'s declared file ownership — reported by name, never substituted)',
  )

  return {
    remedy_rows,
    resonance_rows,
    remedy_available,
    resonance_available,
    activity_ontology_available: false,
    missing_legs: missing,
  }
}

/**
 * Structural resonance for one rite.
 *
 * Honest by construction: the design says this factor is the product of THREE
 * legs, and one of them (`brahma_activity_ontology`) has no retrieval capability
 * in this estate. So the factor NEVER claims `computed` on the full three-leg
 * definition — it computes what the two available legs support and states which
 * leg is missing, exactly as design §3.3's "when unavailable" column requires
 * ("honest_empty naming which of the three was missing").
 */
export function scoreStructuralResonance(
  rite: RemedyCorpusRow,
  substrate: StructuralSubstrate,
): ScoredFactor {
  const source =
    'brahma_remedy_corpus.planet/deity × bodha_rm_resonances.resonance_score (this chart) ' +
    '× brahma_activity_ontology.significators [leg unavailable]'

  if (!substrate.remedy_available || !substrate.resonance_available) {
    return {
      value: null,
      state: 'honest_empty',
      reason:
        'structural resonance needs three legs and at least one could not be read: ' +
        substrate.missing_legs.join('; '),
      source,
    }
  }

  const planet = (rite.planet ?? '').trim().toLowerCase()
  if (!planet) {
    return {
      value: null,
      state: 'honest_empty',
      reason: 'the selected rite carries no `planet` in brahma_remedy_corpus, so it cannot be joined ' +
        'to this chart\'s per-graha resonance. Not scored rather than scored at a default.',
      source,
    }
  }
  const match = substrate.resonance_rows.find((r) => (r.graha ?? '').trim().toLowerCase() === planet)
  if (!match || typeof match.resonance_score !== 'number') {
    return {
      value: null,
      state: 'honest_empty',
      reason:
        `no bodha_rm_resonances row for graha '${rite.planet}' on this chart — the rite is real and ` +
        'cited, but its load-bearing role in THIS chart is not on record, so no structural score is ' +
        'asserted.',
      source,
    }
  }

  // Two legs of three. Reported as `computed` for the two-leg quantity it
  // genuinely is, with the third named in `reason` so the claim is never read as
  // the full three-leg definition.
  const raw = Math.max(0, Math.min(1, match.resonance_score))
  return {
    value: Number(raw.toFixed(4)),
    state: 'computed',
    reason:
      'TWO of three legs: brahma_remedy_corpus (graha→deity→rite) × bodha_rm_resonances ' +
      '(this chart\'s per-graha resonance_score, referenced not recomputed — §N.5). The third leg, ' +
      'brahma_activity_ontology.significators, has no retrieval capability in this estate and is ' +
      'NOT imputed. Read this as a two-leg structural score, not a three-leg one.',
    source,
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// The remaining three factors
// ══════════════════════════════════════════════════════════════════════════════

/** The N_e blocker, stated once. */
export const TEMPORAL_INTENSITY_UNAVAILABLE_REASON =
  'not_computed (field empty — ka_kshetra has written no rows; see the N_e critical path). The ' +
  "field's λ for the rite's domain is this factor's only honest source; a substitute would be an " +
  'invented intensity. The factor is DROPPED from the product and the product renormalised over ' +
  'the factors actually present — never zero-filled.'

export function scoreTemporalIntensity(): ScoredFactor {
  return {
    value: null,
    state: 'not_computed',
    reason: TEMPORAL_INTENSITY_UNAVAILABLE_REASON,
    source: "kala_field_windows (the field's λ for the rite's domain)",
  }
}

/**
 * Election quality — the FROZEN engine's own verdict on the window, mapped to
 * [0,1]. Calls `adjudicateCandidates`; defines no second grader.
 */
export function scoreElectionQuality(
  candidate: CandidateInterval,
  substrate: LatticeSubstrate,
  subjectLabel: string,
): { factor: ScoredFactor; ledger: JudgmentLedger | null } {
  const source = 'kala_lattice_query.adjudicateCandidates (the FROZEN shared engine) — judgment_ledger'
  const adjudication = adjudicateCandidates([candidate], substrate, { subject_label: subjectLabel })
  const ledger = adjudication.ledgers[0] ?? null
  if (adjudication.coverage_state !== 'computed' || ledger === null) {
    return {
      factor: {
        value: null,
        state: 'honest_empty',
        reason:
          adjudication.coverage_reason ??
          'the lattice engine returned no cited annotation for this window, so no election quality is asserted',
        source,
      },
      ledger,
    }
  }
  // A deterministic mapping of the engine's OWN ledger fields — no second
  // grading convention is introduced: residual doṣas subtract, cited auspicious
  // support adds, both clamped. The engine remains the authority on WHAT is a
  // doṣa and WHAT cancels it; this only reads its counts.
  const residual = ledger.residual_dosas.length
  const support = ledger.supporting_factors.length
  const raw = (1 + support) / (1 + support + 2 * residual)
  return {
    factor: {
      value: Number(Math.max(0, Math.min(1, raw)).toFixed(4)),
      state: 'computed',
      reason:
        `derived from the engine's own ledger counts for this window: ${support} cited auspicious ` +
        `support factor(s), ${residual} residual doṣa(s), net_standing='${ledger.net_standing}'. ` +
        'No second grading convention is introduced — the engine stays the authority on what is a ' +
        'doṣa and what cancels it.',
      source,
    },
    ledger,
  }
}

/** Rarity. `bg_cohort` has no retrieval capability wired into this surface, so
 *  this factor is honestly `not_computed` and drops out of the product. */
export function scoreRarity(): ScoredFactor {
  return {
    value: null,
    state: 'not_computed',
    reason:
      'cohort-scored scarcity needs bg_cohort, which is a dormant L0 asset with no retrieval ' +
      'capability wired into this surface. Reported not_computed and dropped from the product — ' +
      'a rarity score invented from the candidate count alone would be a fabricated comparison.',
    source: 'bg_cohort (cohort-scored scarcity)',
  }
}

export function scoreRiteSpecificResonance(
  join: ActivityJoinResult,
  activityClass: ActivityClass,
): ScoredFactor {
  const source =
    `bg_muhurta_activity_rules (activity_class='${activityClass}') joined on ` +
    'bg_muhurta_lattice.detail.factor_id — both ids from panchang_engine\'s own numbered tables ' +
    '(registry item 6; the join rests on ONE deterministic source, never a hand-written map)'
  if (join.score === null) {
    return { value: null, state: 'honest_empty', reason: join.reason, source }
  }
  return { value: join.score, state: 'computed', reason: null, source }
}

// ══════════════════════════════════════════════════════════════════════════════
// Mode 1 — the ranked (window, rite) pairs
// ══════════════════════════════════════════════════════════════════════════════

export interface RitualOpportunity {
  window: { start_utc: string; end_utc: string }
  rite: {
    rite_id: string | null
    rite_class: string | null
    planet: string | null
    deity: string | null
    /** B.10: every rite this wave serves is a ROW THAT ALREADY EXISTS in
     *  brahma_remedy_corpus, selected and cited — never composed at serve time
     *  by concatenating a graha, a deity and an action. */
    citation: string | null
  }
  score_vector: RitualScoreVector
  judgment_ledger: JudgmentLedger | null
  /** item 44 — the atom keys this window inherited. */
  authority_basis: string[]
  precision_regime: 'intra_day' | 'day_grade'
  precision_basis: string
}

export interface Mode1Params {
  chartId: string
  activityClass: ActivityClass
  windows: { start_utc: string; end_utc: string; authority_basis: string[]; binding_families: string[] }[]
  substrate: LatticeSubstrate
  subjectLabel: string
  limit?: number
}

export interface Mode1Result {
  opportunities: RitualOpportunity[]
  activity_rules: ActivityRuleFetch
  structural: StructuralSubstrate
  /** Separated per §N.6: rites carrying a resolvable citation vs. corpus rows
   *  that are placeholder-shaped. NEVER flattened into one array — a caller must
   *  not be able to read a raw row count as "N attested remedies". */
  cited_rite_count: number
  uncited_rite_count: number
  uncited_rite_note: string | null
}

const UNCITED_RITE_NOTE =
  'brahma_remedy_corpus contains placeholder-shaped rows alongside citation-bearing ones. Rows ' +
  'without a resolvable citation are COUNTED HERE SEPARATELY and are never offered as a ' +
  'prescription (§N.6 serving density; B.10 forbids dropping the data AND forbids presenting it ' +
  'as attested).'

function riteCitation(r: RemedyCorpusRow): string | null {
  const c = (r.citation ?? r.source_citation ?? '').trim()
  return c.length > 0 ? c : null
}

export async function scoreMode1Opportunities(
  params: Mode1Params,
  principal: Principal,
): Promise<Mode1Result> {
  const [activityRules, structural] = await Promise.all([
    fetchActivityRules(params.activityClass, principal),
    fetchStructuralSubstrate(params.chartId, principal),
  ])

  const cited = structural.remedy_rows.filter((r) => riteCitation(r) !== null)
  const uncited = structural.remedy_rows.length - cited.length

  const atomsByWindow = (w: { start_utc: string; end_utc: string }): LatticeFactorRow[] => {
    const s = Date.parse(w.start_utc)
    const e = Date.parse(w.end_utc)
    return params.substrate.lattice_rows.filter((r) => {
      const rs = Date.parse(r.start_utc)
      const re = Date.parse(r.end_utc)
      return !Number.isNaN(rs) && !Number.isNaN(re) && rs < e && re > s
    })
  }

  const opportunities: RitualOpportunity[] = []
  for (const [i, w] of params.windows.entries()) {
    const atoms = atomsByWindow(w)
    const join = joinActivityRules(atoms, activityRules.rows, params.activityClass)

    // Rite selection: the highest-resonance CITED corpus row whose graha this
    // chart actually carries a resonance for. Selection, never composition.
    const rite = pickRite(cited, structural)

    const { factor: electionQuality, ledger } = scoreElectionQuality(
      { id: `m1_${i}`, start: w.start_utc, end: w.end_utc, score: 0, disqualified: false },
      params.substrate,
      params.subjectLabel,
    )

    const vector = composeScoreVector({
      structural_resonance: rite
        ? scoreStructuralResonance(rite, structural)
        : {
            value: null,
            state: 'honest_empty',
            reason:
              'no citation-bearing brahma_remedy_corpus row could be selected for this chart ' +
              '(either the corpus is unavailable or no cited row\'s graha has a resonance row here). ' +
              'No rite is composed at serve time — B.10.',
            source: 'brahma_remedy_corpus (cited rows only)',
          },
      temporal_intensity: scoreTemporalIntensity(),
      election_quality: electionQuality,
      rarity: scoreRarity(),
      rite_specific_resonance: scoreRiteSpecificResonance(join, params.activityClass),
    })

    const degrading = false // Mode 1 binds only pāñcāṅgika/day-part families here.
    opportunities.push({
      window: { start_utc: w.start_utc, end_utc: w.end_utc },
      rite: {
        rite_id: rite?.remedy_id ?? null,
        rite_class: rite?.remedy_type ?? null,
        planet: rite?.planet ?? null,
        deity: rite?.deity ?? null,
        citation: rite ? riteCitation(rite) : null,
      },
      score_vector: vector,
      judgment_ledger: ledger,
      authority_basis: w.authority_basis,
      precision_regime: degrading ? 'day_grade' : 'intra_day',
      precision_basis:
        w.binding_families.length > 0
          ? `every binding constraint is pāñcāṅgika or day-part (${w.binding_families.join(', ')})`
          : 'no lattice family bound this window; no precision claim is made from a binding factor',
    })
  }

  // Rank by composite, nulls last — an unscored opportunity is still SERVED
  // (B.10 forbids dropping it) but never outranks a scored one.
  opportunities.sort((a, b) => (b.score_vector.composite ?? -1) - (a.score_vector.composite ?? -1))

  return {
    opportunities: params.limit ? opportunities.slice(0, params.limit) : opportunities,
    activity_rules: activityRules,
    structural,
    cited_rite_count: cited.length,
    uncited_rite_count: uncited,
    uncited_rite_note: uncited > 0 ? UNCITED_RITE_NOTE : null,
  }
}

/** Selects — never composes — a rite from the CITED corpus rows, preferring the
 *  graha this chart's remedial matrix ranks highest. Returns `null` honestly
 *  when nothing selectable exists. */
export function pickRite(
  citedRites: RemedyCorpusRow[],
  structural: StructuralSubstrate,
): RemedyCorpusRow | null {
  if (citedRites.length === 0) return null
  const byGraha = new Map<string, number>()
  for (const r of structural.resonance_rows) {
    const g = (r.graha ?? '').trim().toLowerCase()
    if (g && typeof r.resonance_score === 'number') {
      byGraha.set(g, Math.max(byGraha.get(g) ?? 0, r.resonance_score))
    }
  }
  const scored = citedRites
    .map((r) => ({ rite: r, score: byGraha.get((r.planet ?? '').trim().toLowerCase()) ?? -1 }))
    // Total order: score desc, then a stable tiebreak on the rite's own id, so
    // repeated calls return the same rite (§N.7 item 2 discipline).
    .sort((a, b) => b.score - a.score || String(a.rite.remedy_id ?? '').localeCompare(String(b.rite.remedy_id ?? '')))
  const best = scored[0]
  return best && best.score >= 0 ? best.rite : null
}
