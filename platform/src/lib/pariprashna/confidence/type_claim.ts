/**
 * pariprashna/confidence/type_claim.ts — `typeClaimConfidence` (lane G3-C,
 * PPR-03).
 *
 * Assigns ONE of the five PPR-03 confidence types to a single cited claim,
 * from REAL, priority-ordered signals — never a guess based on how a type
 * "reads" (§N.7). Every branch below cites the exact real field it reads:
 *
 *   1. `layer === 'L1'`                              → deterministic_fact
 *      Source: `citation_data_part.ts`'s own
 *      `layer: z.enum(['L1', 'L2.5'])` — an `'L1'`-tagged citation is a
 *      direct L1 Gaṇita `chart_facts` reference (a computed-once chart fact,
 *      not a derived signal).
 *
 *   2. calibration consulted AND the activation gate is open  → empirically_calibrated
 *      Source: `receipt/assemble.ts#CALIBRATION_BEARING_TOOL_NAMES` (reused,
 *      never re-derived — the SAME audited tool-name list G3-A already
 *      built for `calibration_disclosure`) for "was a real L5 calibration
 *      capability consulted this turn", AND
 *      `activation_gate.ts#evaluateEmpiricalCalibrationGate` for "does this
 *      turn's real sample size clear the gate" — both must be real and true.
 *      Turn-scoped (not per-citation), the SAME honesty boundary
 *      `calibration_disclosure` already uses: this codebase does not thread
 *      a per-signal "was THIS specific signal calibration-derived" flag
 *      through to receipt-assembly scope, so this branch fires per-turn, not
 *      per-fact-ref — disclosed here rather than fabricating a per-ref
 *      distinction that does not exist yet.
 *
 *   3. classical sources consulted this turn                  → classical_prior
 *      Source: `CLASSICAL_PRIOR_BEARING_TOOL_NAMES` below — a real, audited
 *      list of registered classical-text capabilities
 *      (`classical_attribution_lookup`, `read_sutravali_rule`, etc. — see
 *      that constant's own doc comment for the audit). Same turn-scoped
 *      honesty boundary as branch 2.
 *
 *   4. `layer === 'L2.5'`                             → structural_prior
 *      Source: the same `citation_data_part.ts` layer enum — an
 *      `'L2.5'`-tagged citation is an MSR/Bodha structural signal (a
 *      yoga/dignity/structural computation derived from the chart, not a
 *      raw L1 fact and not a classical-text citation).
 *
 *   5. none of the above                               → unresolved
 *      The honest fallback (§N.7 item 6): a citation whose layer is neither
 *      recognized value and which triggered no other real detector is typed
 *      `unresolved`, never defaulted to a plausible-sounding type.
 *
 * `capConfidenceTypeForEngineGeneration` (engine_tier.ts) is applied AFTER
 * this priority chain when generation metadata is available to the caller —
 * see that module's own header for why it is not wired into this function
 * directly in this lane.
 */

import type { ConfidenceType, TypedConfidenceEntry } from './types'
import { evaluateEmpiricalCalibrationGate, type CalibrationGateResult } from './activation_gate'

/**
 * Real, registered classical-text capabilities — audited the SAME way G3-A
 * audited `CALIBRATION_BEARING_TOOL_NAMES`: grepped `name: '...'` across
 * `registry/layers/register_d7_channel.ts` (the D7 classical/remedy channel
 * registrations) for handlers that return classical-text-sourced content
 * (verse/rule/attribution text), not a computed chart structure.
 *
 *   - `classical_attribution_lookup` — links an MSR signal_id to a classical
 *     text passage (text_key/title/author/chapter/verse_range/content) with
 *     an attribution_type (confirms/contradicts/partial/extends/silent).
 *     THE clearest real classical-source-for-a-claim signal in the registry.
 *   - `read_sutravali_rule`, `query_sutravali_rules`,
 *     `query_sutravali_rules_for_planet`, `list_sutravali_rules_by_text` —
 *     the classical rule-corpus (sutravali) reader/search surfaces.
 *   - `read_chapter`, `list_classical_texts`, `find_verses_about` — the
 *     general classical-text reading/search surfaces (`search_classical_texts`
 *     is the MCP-side name for the same family; not separately registered
 *     here as of this audit).
 *
 * Re-run the grep before trusting this list, the same discipline
 * `CALIBRATION_BEARING_TOOL_NAMES` documents for itself.
 */
export const CLASSICAL_PRIOR_BEARING_TOOL_NAMES: readonly string[] = [
  'classical_attribution_lookup',
  'read_sutravali_rule',
  'query_sutravali_rules',
  'query_sutravali_rules_for_planet',
  'list_sutravali_rules_by_text',
  'read_chapter',
  'list_classical_texts',
  'find_verses_about',
]

export const TYPING_BASIS = {
  L1_FACT_LAYER: 'l1_fact_layer',
  CALIBRATION_GATE_OPEN: 'calibration_gate_open',
  // G3BC hardening defect 4: renamed from 'classical_source_consulted' to
  // disclose the turn-scoping this module's OWN header comment already
  // documents (branch 3 above) directly in the value a receipt reader
  // actually sees. Before this rename, the receipt's emitted `basis` string
  // gave a downstream reader no way to tell "a classical tool was consulted
  // SOMEWHERE this turn" apart from "specifically for this citation" — the
  // exact ambiguity G3-A's `calibration_disclosure` field already avoids by
  // disclosing turn-scoping in its OWN emitted `disclosure_note`. This is a
  // naming/disclosure fix ONLY — `assignType` below still fires on the
  // IDENTICAL condition (`classicalConsulted`, a turn-wide detector); no
  // detection logic changed.
  CLASSICAL_SOURCE_CONSULTED: 'classical_source_consulted_this_turn',
  L2_5_STRUCTURAL_SIGNAL: 'l2_5_structural_signal',
  UNRESOLVED_NO_DETECTOR: 'unresolved_no_detector',
} as const

export interface TypeClaimConfidenceArgs {
  ref: string
  layer: string
  calibrationConsulted: boolean
  calibrationGate: CalibrationGateResult
  classicalConsulted: boolean
}

function assignType(args: Pick<TypeClaimConfidenceArgs, 'layer' | 'calibrationConsulted' | 'calibrationGate' | 'classicalConsulted'>): {
  confidence_type: ConfidenceType
  basis: string
} {
  if (args.layer === 'L1') {
    return { confidence_type: 'deterministic_fact', basis: TYPING_BASIS.L1_FACT_LAYER }
  }
  if (args.calibrationConsulted && args.calibrationGate.gate_open) {
    return { confidence_type: 'empirically_calibrated', basis: TYPING_BASIS.CALIBRATION_GATE_OPEN }
  }
  if (args.classicalConsulted) {
    return { confidence_type: 'classical_prior', basis: TYPING_BASIS.CLASSICAL_SOURCE_CONSULTED }
  }
  if (args.layer === 'L2.5') {
    return { confidence_type: 'structural_prior', basis: TYPING_BASIS.L2_5_STRUCTURAL_SIGNAL }
  }
  return { confidence_type: 'unresolved', basis: TYPING_BASIS.UNRESOLVED_NO_DETECTOR }
}

/** Type a single cited claim per the priority chain documented above. */
export function typeClaimConfidence(args: TypeClaimConfidenceArgs): TypedConfidenceEntry {
  const { confidence_type, basis } = assignType(args)
  return { ref: args.ref, layer: args.layer, confidence_type, basis }
}

/**
 * Turn-level "was a classical-text capability consulted" detector — the
 * SAME shape as `receipt/assemble.ts#buildCalibrationDisclosure`, reused
 * (never re-derived a second way): scans `validToolResults[].tool_name`
 * membership in `CLASSICAL_PRIOR_BEARING_TOOL_NAMES`.
 */
export function wasClassicalSourceConsulted(toolNames: readonly string[]): boolean {
  return toolNames.some((name) => CLASSICAL_PRIOR_BEARING_TOOL_NAMES.includes(name))
}

/** Re-exported for callers that only need the gate's own evaluator without importing activation_gate.ts directly. */
export { evaluateEmpiricalCalibrationGate }
