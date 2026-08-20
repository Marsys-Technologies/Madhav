import 'server-only'
/**
 * pariprashna/receipt/assemble.ts — `assembleAcharyaReadingReceipt` (lane
 * G3-A, PPR-01).
 *
 * PURE with respect to I/O: every argument is a value the pipeline already
 * computed from a real source elsewhere (`persistence_stage.ts` is the sole
 * caller and passes exactly what it already has in scope — no new DB read is
 * added by this module). That is what makes this function directly
 * unit-testable against realistic fixtures without a database, and what
 * makes the "field maps to real source" claim checkable per field: see the
 * per-field comment on `schema.ts` for the field ↔ source mapping, and
 * `__tests__/assemble.test.ts` for a fixture proving each one.
 */

import { createHash } from 'node:crypto'

import type { PipelinePlan } from '@/lib/pipeline/types'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'
import type { SafetyDecision } from '@/lib/pariprashna/safety'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'
import type { ResolvedTurnCitation } from '@/lib/pariprashna/citations/stream_wiring'
import type { CitationGrade } from '@/lib/pariprashna/citations/types'
import type { OpenBlock, DetectedCitationRow } from '@/lib/pariprashna/pipeline/reading_parts'
import { extractCitations } from '@/lib/citations/citation_data_part'
import type { ReceiptInterpretationSets } from '@/lib/pariprashna/interpretation/schema'

import {
  ACHARYA_READING_RECEIPT_SCHEMA_VERSION,
  type AcharyaReadingReceipt,
  type ReceiptCoverage,
  type ReceiptCrossDomain,
  type ReceiptEvidenceGrades,
  type ReceiptHonestGaps,
  type ReceiptSafetyDecision,
  type ReceiptCalibrationDisclosure,
  type ReceiptProseBinding,
  type ReceiptProvenance,
  type ReceiptConfidenceTyping,
  type ReceiptPrecisionFlag,
} from './schema'
import { computeReceiptHash } from './hash'
import {
  typeClaimConfidence,
  wasClassicalSourceConsulted,
  evaluateEmpiricalCalibrationGate,
  extractCalibrationSampleSize,
  extractCalibrationPrecisionCandidates,
  scanPrecision,
  countDecimalPlaces,
} from '@/lib/pariprashna/confidence'

/**
 * Every registered L5 Mīmāṃsā capability whose handler actually reads
 * `mimamsa_calibration` and returns calibration-shaped data — audited by
 * grepping `mimamsa_calibration` / `calibration_summary` across the FULL
 * `registry/layers/L5_mimamsa/` directory (2026-08-20, P2-I hardening), not
 * a guessed pattern match:
 *
 *   - `query_calibration.ts` (`tool_name: 'query_calibration'`, capability
 *     id `mi_pramana`, STUBBED per that layer's own index.ts comment) — the
 *     calibration scorecard/reliability-curve surface; `FROM
 *     mimamsa_calibration` directly.
 *   - `query_insights.ts` (`tool_name: 'query_insights'`, capability id
 *     `mi_darshana`) — the primary L5 insight-surface query. Alongside its
 *     `mimamsa_insight_units` rows it ALSO directly queries
 *     `mimamsa_calibration` (`calSql`) and returns the result as a
 *     `calibration_summary` object in its response — a second, real,
 *     already-registered calibration-bearing tool, missed by this list's
 *     prior single-entry form.
 *
 * Every other capability in this layer carrying `archetype: 'calibration'`
 * (query_predictions, query_signal_families, query_manifestation_grammar,
 * query_attribution, query_mimamsa_discoveries, query_insight_embeddings,
 * query_manifestation_sets, query_load_bearing, query_journal,
 * query_life_events, query_mechanism_retrodiction, lel_intake_checklist,
 * prediction_lifecycle_sweep) was checked and does NOT read
 * `mimamsa_calibration` — `archetype: 'calibration'` is a broader
 * tool-category tag on that field, not evidence of a calibration-table read;
 * do not add a name here on that tag alone. Re-run the grep across the
 * directory before trusting this list, the same way it was produced.
 */
export const CALIBRATION_BEARING_TOOL_NAMES: readonly string[] = ['query_calibration', 'query_insights']

/**
 * CLAUDE.md §E's own words about L5's current calibration state — a fixed,
 * doctrinally-sourced disclosure, not a computed claim about this specific
 * reading's numbers (see schema.ts's `calibration_disclosure` comment for
 * why a fixed string is the honest choice here, not a fabrication).
 */
export const STRUCTURAL_MODE_CALIBRATION_NOTE =
  'No L5 Mīmāṃsā calibration capability was consulted this turn. L5 is sealed in ' +
  'STRUCTURAL mode (CLAUDE.md §E): empirical calibration values fill in as ' +
  'prediction→outcome data accrues. Predictive claims in this reading are not yet ' +
  'empirically calibrated.'

export const CALIBRATION_CONSULTED_NOTE =
  'A L5 Mīmāṃsā calibration capability was consulted this turn — see the cited tool ' +
  'results for the disclosed calibration state. This does not imply every predictive ' +
  'claim in the reading is empirically calibrated; see the citation grades above.'

export interface AssembleAcharyaReadingReceiptArgs {
  turnId: string
  conversationId: string
  chartId: string
  /** Injectable for deterministic tests; defaults to `new Date()`. */
  now?: Date
  plan: Pick<PipelinePlan, 'domains'>
  committedBlocks: readonly OpenBlock[]
  accumulatedText: string
  /** The turn's own citation detections — always computed, either path (persistence_stage.ts). */
  citationsFound: readonly DetectedCitationRow[]
  citationRewriteEnabled: boolean
  resolvedCitations: readonly ResolvedTurnCitation[]
  citationHallucinationCount: number
  completenessReceipt: WebCompletenessReceipt | null
  safetyDecision?: SafetyDecision
  validToolResults: readonly ToolBundle[]
  provenanceStamp: TurnProvenanceStamp
  /**
   * Lane G3-B (PPR-02) additive extension. Already-assembled
   * `interpretation/assemble.ts` output (or the caller's own
   * `unavailableInterpretationSets(reason)` when the G3-B flag was off this
   * turn). Omitted entirely (every pre-existing caller/fixture) -> this
   * function supplies its OWN honest "never attempted" default below, so
   * every pre-G3-B call site stays byte-for-byte unchanged in every OTHER
   * field while still getting a well-formed (not absent) receipt field.
   */
  interpretationSets?: ReceiptInterpretationSets
  /**
   * Lane G3-C (PPR-03). Own flag, layered on top of receipt emission itself
   * — defaults to `false` (unavailable) when omitted, so every pre-existing
   * caller/test of this function is unaffected. See `confidence/flag.ts`.
   */
  typedConfidenceEnabled?: boolean
}

const CITATION_GRADES: readonly CitationGrade[] = [
  'primary',
  'supporting',
  'contextual',
  'unverified',
  'prior_reading',
]

function parsePassId(blockId: string): number | null {
  const m = /^blk-(-?\d+)-\d+$/.exec(blockId)
  if (!m) return null
  const n = Number(m[1])
  return Number.isFinite(n) ? n : null
}

function buildCoverage(receipt: WebCompletenessReceipt | null): ReceiptCoverage {
  if (!receipt) {
    return {
      status: 'unavailable',
      served: null,
      empty: null,
      dark: null,
      floor_item_total: null,
      channel: null,
      channel_note: null,
      unavailable_reason: 'no WebCompletenessReceipt was built this turn (registry compile fault — see buildWebCompletenessReceipt)',
    }
  }
  return {
    status: 'measured',
    served: receipt.coverage.served,
    empty: receipt.coverage.empty,
    dark: receipt.coverage.dark,
    floor_item_total: receipt.coverage.floor_item_total,
    channel: receipt.channel,
    channel_note: receipt.channel_note,
    unavailable_reason: null,
  }
}

function buildCrossDomain(domains: readonly string[] | undefined): ReceiptCrossDomain {
  if (!domains) {
    return {
      status: 'unavailable',
      domains: null,
      unavailable_reason: 'plan.domains was not populated by the planner for this turn',
    }
  }
  return { status: 'measured', domains: [...domains], unavailable_reason: null }
}

function buildEvidenceGrades(args: {
  citationRewriteEnabled: boolean
  resolvedCitations: readonly ResolvedTurnCitation[]
  hallucinationCount: number
}): ReceiptEvidenceGrades {
  if (!args.citationRewriteEnabled) {
    return {
      status: 'unavailable',
      grade_counts: null,
      hallucination_count: null,
      unavailable_reason:
        'PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED was off this turn; citation detection ran ' +
        'via regex only and carries no per-citation grade tier',
    }
  }
  const grade_counts = { primary: 0, supporting: 0, contextual: 0, unverified: 0, prior_reading: 0 }
  for (const c of args.resolvedCitations) {
    if (CITATION_GRADES.includes(c.grade)) grade_counts[c.grade] += 1
  }
  return {
    status: 'measured',
    grade_counts,
    hallucination_count: args.hallucinationCount,
    unavailable_reason: null,
  }
}

function buildHonestGaps(receipt: WebCompletenessReceipt | null): ReceiptHonestGaps {
  if (!receipt) {
    return {
      status: 'unavailable',
      gaps: null,
      unavailable_reason: 'no WebCompletenessReceipt was built this turn (registry compile fault)',
    }
  }
  const gaps = [
    ...receipt.empty.map((e) => ({ floor_item_id: e.floor_item_id, kind: 'empty' as const, reason: e.empty_reason })),
    ...receipt.dark.map((d) => ({
      floor_item_id: d.floor_item_id,
      kind: 'dark' as const,
      reason: d.note ? `${d.cr_row}: ${d.note}` : d.cr_row,
    })),
  ]
  return { status: 'measured', gaps, unavailable_reason: null }
}

function buildSafetyDecision(decision: SafetyDecision | undefined): ReceiptSafetyDecision {
  if (!decision) {
    return {
      status: 'unavailable',
      decision_id: null,
      enforced: null,
      severity: null,
      action: null,
      classes_detected: null,
      review_id: null,
      audit_written: null,
      unavailable_reason: 'no SafetyDecision was supplied to persistence for this turn',
    }
  }
  return {
    status: 'measured',
    decision_id: decision.decision_id,
    enforced: decision.enforced,
    severity: decision.severity,
    action: decision.action,
    classes_detected: [...decision.classes_detected],
    review_id: decision.review_id,
    audit_written: decision.audit_written,
    unavailable_reason: null,
  }
}

function buildCalibrationDisclosure(validToolResults: readonly ToolBundle[]): ReceiptCalibrationDisclosure {
  const consultedNames = [
    ...new Set(
      validToolResults
        .map((tb) => tb.tool_name)
        .filter((name) => CALIBRATION_BEARING_TOOL_NAMES.includes(name)),
    ),
  ]
  return {
    consulted: consultedNames.length > 0,
    consulted_tool_names: consultedNames,
    disclosure_note: consultedNames.length > 0 ? CALIBRATION_CONSULTED_NOTE : STRUCTURAL_MODE_CALIBRATION_NOTE,
  }
}

function buildProseBinding(args: {
  committedBlocks: readonly OpenBlock[]
  accumulatedText: string
}): ReceiptProseBinding {
  const blocks = args.committedBlocks.map((b) => ({
    block_id: b.id,
    role: b.role,
    char_count: b.text.length,
    semantic_kind: b.semantic?.kind ?? null,
    semantic_role: b.semantic?.role ?? null,
  }))
  return {
    blocks,
    accumulated_text_sha256: createHash('sha256').update(args.accumulatedText, 'utf8').digest('hex'),
    accumulated_char_count: args.accumulatedText.length,
  }
}

/**
 * Lane G3-B (PPR-02). The honest default when the caller supplies nothing —
 * every pre-existing caller of this function (every fixture/test written
 * before this lane) hits this branch and gets a well-formed `unavailable`
 * field rather than an absent/undefined one, which is what lets
 * `receipt/validate.ts`'s coherence check run uniformly over every FRESHLY
 * ASSEMBLED receipt regardless of whether the caller knows about G3-B yet.
 */
function buildInterpretationSetsDefault(): ReceiptInterpretationSets {
  return {
    status: 'unavailable',
    interpretation_sets_schema_version: null,
    detected_count: null,
    covered_count: null,
    truncated_count: null,
    waived_count: null,
    sets: null,
    unavailable_reason: 'interpretation-set generation did not run this turn (PARIPRASHNA_INTERPRETATION_SETS_ENABLED was off, or no value was supplied to the assembler)',
  }
}

function buildProvenance(stamp: TurnProvenanceStamp): ReceiptProvenance {
  return {
    build_id: stamp.build_id,
    priors_version: stamp.priors_version,
    formula_versions: { salience_formula_ver: stamp.formula_versions.salience_formula_ver },
    ranking_config: { mode: stamp.ranking_config.mode },
    now_context_date: stamp.now_context_date,
    computed_at: stamp.computed_at,
  }
}

/**
 * Lane G3-C (PPR-03) — `confidence_typing`.
 *
 * Types every citation this turn detected (`citationsFound` — the SAME
 * source `facts_consumed` already reads, never re-scanned a second way) via
 * `typeClaimConfidence`, computes the real `empirically_calibrated`
 * activation gate from this turn's own calibration-bearing tool results, and
 * runs the T-8 precision scan over the precision-bearing numeric fields
 * those same tool results served (see `extractCalibrationPrecisionCandidates`
 * — G3BC hardening defect 2 fix: this used to read `ToolBundleResult.
 * confidence`, a top-level field neither `query_calibration.ts` nor
 * `query_insights.ts` ever populates, making the scan dead code against real
 * production tool output; §N.8).
 *
 * The sample-size extraction is BEST-EFFORT and DEFENSIVE, grounded in a
 * verified real serialization path: `registry/tool_name_bridge.ts`'s
 * `toToolBundleResults` JSON.stringifies a capability handler's plain
 * `content` object (no `results`/`content` sub-key) into a SINGLE
 * `ToolBundleResult.content` string — exactly the shape
 * `query_calibration.ts`/`query_insights.ts` return (`{ ...,
 * verdict_distribution, calibration_summary, ... }`, no `results` key of
 * their own). `JSON.parse` here can only fail on a genuine shape drift or a
 * differently-wired tool; on failure this returns null/skips rather than
 * guessing — the gate then honestly stays closed (see `activation_gate.ts`).
 *
 * G3BC hardening defect 3 fix: the sample size backing the
 * `empirically_calibrated` activation gate is the MINIMUM sample size across
 * this turn's contributing calibration-bearing tool RESULTS, never a SUM.
 * Summing let two independent, unrelated calibration calls (e.g. two
 * `query_insights` calls over different domains/strata, each n=15, neither
 * individually meeting the activation threshold) combine into a
 * turn-wide n=30 that incorrectly opened the gate for a claim really backed
 * by only 15 relevant samples. This codebase does not thread a per-claim
 * "which specific tool result backs THIS citation's typing" attribution
 * through to receipt-assembly scope (the same turn-scoped-not-claim-scoped
 * honesty boundary `type_claim.ts`'s `calibrationConsulted`/
 * `classicalConsulted` already disclose for the OTHER two consultation-based
 * types) — threading real per-claim tool-result attribution through the
 * pipeline is a genuine, larger refactor out of scope for this hardening
 * round, so MIN is the conservative fallback: it can never let a small,
 * possibly-irrelevant sample borrow credibility from an unrelated larger
 * one, at the cost of being more conservative than a true per-claim
 * attribution would be (a real per-claim-backed sample size might legally
 * exceed the minimum). Each bundle's OWN multiple results (rare — a single
 * tool call ordinarily returns one result) still sum within that bundle,
 * since they represent the SAME underlying call's own data; only the
 * cross-bundle combination changed from sum to min.
 */
function extractCalibrationSummaryFromToolBundle(tb: ToolBundle): unknown[] {
  const parsed: unknown[] = []
  for (const r of tb.results) {
    try {
      parsed.push(JSON.parse(r.content))
    } catch {
      // Non-JSON content (e.g. a plain-text snippet from a non-calibration
      // tool that happens to share the name) — honestly skip, never guess.
    }
  }
  return parsed
}

function buildConfidenceTyping(args: {
  enabled: boolean
  citationsFound: readonly DetectedCitationRow[]
  validToolResults: readonly ToolBundle[]
}): ReceiptConfidenceTyping {
  if (!args.enabled) {
    return {
      status: 'unavailable',
      entries: null,
      activation_gate: null,
      precision_flags: null,
      unavailable_reason: 'PARIPRASHNA_TYPED_CONFIDENCE_ENABLED was off this turn',
    }
  }

  const calibrationBundles = args.validToolResults.filter((tb) =>
    CALIBRATION_BEARING_TOOL_NAMES.includes(tb.tool_name),
  )
  const calibrationConsulted = calibrationBundles.length > 0
  const toolNames = args.validToolResults.map((tb) => tb.tool_name)
  const classicalConsulted = wasClassicalSourceConsulted(toolNames)

  // sampleSize: MIN across contributing calibration-bearing tool RESULTS this
  // turn (defect 3 fix — see doc comment above). null when no bundle yielded
  // a real sample size.
  let sampleSize: number | null = null
  const precisionFlags: ReceiptPrecisionFlag[] = []
  for (const tb of calibrationBundles) {
    const payloads = extractCalibrationSummaryFromToolBundle(tb)
    let tbSampleSize: number | null = null
    for (const payload of payloads) {
      // Sample size — same extraction as before, still summed WITHIN one
      // bundle's own payloads (see doc comment: multiple results on the
      // SAME bundle represent the same underlying call).
      const extracted = extractCalibrationSampleSize(payload)
      if (extracted !== null) {
        tbSampleSize = (tbSampleSize ?? 0) + extracted
      }
      // T-8 precision scan (defect 2 fix) — read the precision-bearing
      // value(s) from the PARSED content, never from the nonexistent
      // top-level `ToolBundleResult.confidence`.
      for (const candidate of extractCalibrationPrecisionCandidates(payload)) {
        const scan = scanPrecision({
          value: candidate.value,
          servedDecimalPlaces: countDecimalPlaces(candidate.value),
          // Prefer the candidate's OWN row-level sample size (e.g. a single
          // verdict group's own `n`) over the bundle's aggregate — a more
          // precise, more conservative pairing than falling back to
          // `tbSampleSize` would be. Falls back to the bundle's own
          // aggregate only when the candidate carries no row-level size of
          // its own (e.g. the `calibration_summary` shape, which already
          // pairs its value with its own `total_matches`).
          sampleSize: candidate.sampleSize,
        })
        if (scan.overstated) {
          precisionFlags.push({
            tool_name: tb.tool_name,
            overstated: scan.overstated,
            max_supported_decimal_places: scan.max_supported_decimal_places,
            served_decimal_places: scan.served_decimal_places,
            sample_size: scan.sample_size,
            band_label: scan.band_label,
            demoted_value: scan.demoted_value,
          })
        }
      }
    }
    if (tbSampleSize !== null) {
      sampleSize = sampleSize === null ? tbSampleSize : Math.min(sampleSize, tbSampleSize)
    }
  }

  const gate = evaluateEmpiricalCalibrationGate({ sampleSize })

  const entries = args.citationsFound.map((c) =>
    typeClaimConfidence({
      ref: c.signal_id,
      layer: c.layer,
      calibrationConsulted,
      calibrationGate: gate,
      classicalConsulted,
    }),
  )

  return {
    status: 'measured',
    entries,
    activation_gate: gate,
    precision_flags: precisionFlags,
    unavailable_reason: null,
  }
}

/**
 * Per-block `fact_refs` for `derivation_chains`.
 *
 * Flag-off: the pre-existing regex scan over the block's OWN committed text
 * (`extractCitations`) — unchanged.
 *
 * Flag-on (G2-B live rewriter, PPR-08): `b.text` on this path already
 * contains the rewriter's resolved `[n]` inline markers, not raw
 * `SIG.MSR.NNN` tokens (`reading_parts.ts`'s own `preResolvedCitations` doc:
 * the register-leak lint has already scrubbed/rewritten every such token
 * before it reached committed block text) — `extractCitations(b.text)`
 * structurally finds nothing on this path, the exact silent-empty defect
 * `buildFactsConsumed` already avoids by reading `citationsFound` (itself
 * sourced from `resolvedCitations` on this path — see persistence_stage.ts)
 * instead of re-scanning text.
 *
 * `ResolvedTurnCitation` (citations/stream_wiring.ts) carries no block
 * association of its own to filter/group by. What DOES exist, and is real
 * rather than guessed: the rewriter always renders the DEFAULT `[n]` inline
 * marker into the committing block's own text (`citations/rewriter.ts`'s
 * `renderMarker` option, never overridden — `synthesis_stage.ts` constructs
 * `TurnCitationStream` with no `renderMarker` in production). A block
 * genuinely "contains" a resolved citation iff its own committed text
 * contains that citation's own `[n]` marker — the same reader-visible
 * association the reader's own eyes make. Bracket-delimited exact-substring
 * match (`[${index}]`) cannot false-positive across different indices
 * (`[1]` is not a substring of `[10]` or vice versa).
 */
function factRefsForBlock(
  blockText: string,
  args: { citationRewriteEnabled: boolean; resolvedCitations: readonly ResolvedTurnCitation[] },
): string[] {
  if (!args.citationRewriteEnabled) {
    return extractCitations(blockText).map((c) => c.signal_id)
  }
  return args.resolvedCitations
    .filter((c) => blockText.includes(`[${c.index}]`))
    .map((c) => c.signal_id)
}

function buildDerivationChains(
  committedBlocks: readonly OpenBlock[],
  args: { citationRewriteEnabled: boolean; resolvedCitations: readonly ResolvedTurnCitation[] },
) {
  return committedBlocks.map((b) => ({
    block_id: b.id,
    pass_id: parsePassId(b.id),
    role: b.role,
    fact_refs: factRefsForBlock(b.text, args),
  }))
}

function buildFactsConsumed(citationsFound: readonly DetectedCitationRow[]) {
  return citationsFound.map((c) => ({ ref: c.signal_id, layer: c.layer, index: c.index }))
}

export function assembleAcharyaReadingReceipt(
  args: AssembleAcharyaReadingReceiptArgs,
): AcharyaReadingReceipt {
  const now = args.now ?? new Date()

  const contentWithoutHash = {
    receipt_schema_version: ACHARYA_READING_RECEIPT_SCHEMA_VERSION,
    turn_id: args.turnId,
    conversation_id: args.conversationId,
    chart_id: args.chartId,
    generated_at: now.toISOString(),
    coverage: buildCoverage(args.completenessReceipt),
    facts_consumed: buildFactsConsumed(args.citationsFound),
    derivation_chains: buildDerivationChains(args.committedBlocks, {
      citationRewriteEnabled: args.citationRewriteEnabled,
      resolvedCitations: args.resolvedCitations,
    }),
    cross_domain: buildCrossDomain(args.plan.domains),
    evidence_grades: buildEvidenceGrades({
      citationRewriteEnabled: args.citationRewriteEnabled,
      resolvedCitations: args.resolvedCitations,
      hallucinationCount: args.citationHallucinationCount,
    }),
    honest_gaps: buildHonestGaps(args.completenessReceipt),
    safety_decision: buildSafetyDecision(args.safetyDecision),
    calibration_disclosure: buildCalibrationDisclosure(args.validToolResults),
    prose_binding: buildProseBinding({
      committedBlocks: args.committedBlocks,
      accumulatedText: args.accumulatedText,
    }),
    provenance: buildProvenance(args.provenanceStamp),
    interpretation_sets: args.interpretationSets ?? buildInterpretationSetsDefault(),
    confidence_typing: buildConfidenceTyping({
      enabled: args.typedConfidenceEnabled ?? false,
      citationsFound: args.citationsFound,
      validToolResults: args.validToolResults,
    }),
  }

  return {
    ...contentWithoutHash,
    receipt_hash: computeReceiptHash(contentWithoutHash),
  }
}
