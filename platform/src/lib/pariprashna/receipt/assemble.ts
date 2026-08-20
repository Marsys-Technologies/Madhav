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
} from './schema'
import { computeReceiptHash } from './hash'

/**
 * The one registered L5 Mīmāṃsā calibration-bearing retrieval capability's
 * `tool_name` as of this lane (`registry/layers/L5_mimamsa/query_calibration.ts`
 * — capability id `mi_pramana`, STUBBED per that layer's own index.ts
 * comment). A real, named, single-source-of-truth-in-this-file list rather
 * than a guessed pattern match — extend it here if a second L5 calibration
 * capability is registered later.
 */
export const CALIBRATION_BEARING_TOOL_NAMES: readonly string[] = ['query_calibration']

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

function buildDerivationChains(committedBlocks: readonly OpenBlock[]) {
  return committedBlocks.map((b) => ({
    block_id: b.id,
    pass_id: parsePassId(b.id),
    role: b.role,
    fact_refs: extractCitations(b.text).map((c) => c.signal_id),
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
    derivation_chains: buildDerivationChains(args.committedBlocks),
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
  }

  return {
    ...contentWithoutHash,
    receipt_hash: computeReceiptHash(contentWithoutHash),
  }
}
