/**
 * Typed deterministic-gate receipts derived from a door's own response-accountability envelope
 * (Pūrṇa R2C.6 / review RC-6.6). The collection bridge previously hard-coded these gates as
 * unavailable, so no product case could pass them even with perfect collection.
 *
 * Every receipt is computed only from what the door returned — the fact register and coverage
 * receipt — never from prose heuristics. A gate that cannot be proven from those fields fails
 * with a typed reason naming what is missing.
 */
import type {
  InquiryRegisteredFact,
  InquiryResponseAccountability,
} from '../../src/lib/vidhi/inquiry/types'
import { stableFingerprint } from '../../src/lib/retrieval/registry/knowledge/stable'

export interface TypedGateResult {
  readonly passed: boolean
  readonly receipt_ref: string | null
  readonly detail?: string
}

const DELIVERABLE_DISPOSITIONS = new Set(['served', 'empty'])
const MISSING_DISPOSITIONS = new Set(['pending', 'dark', 'failed', 'open', 'capped'])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** The envelope, when it carries the register and coverage receipt these gates read. */
export function accountabilityEnvelope(value: unknown): InquiryResponseAccountability | null {
  if (!isRecord(value) || value.accountability_version !== 'inquiry-response-accountability-v1') return null
  const register = value.fact_register
  const coverage = value.response_coverage_receipt
  if (!isRecord(register) || !Array.isArray(register.facts)) return null
  if (!isRecord(coverage) || !Array.isArray(coverage.delivered_fact_ids) || typeof coverage.status !== 'string') return null
  return value as unknown as InquiryResponseAccountability
}

function fail(detail: string): TypedGateResult {
  return { passed: false, receipt_ref: null, detail }
}

/**
 * Every required dimension must be evidenced by a delivered register fact. Dimensions that are
 * SCU ids (the immutable Beyond-Ācārya corpus) are matched against the facts' SCU ids. A
 * semantic product label (e.g. `wealth_mechanisms`) has no ratified label → evidence map, so it
 * fails with a typed reason rather than being matched heuristically.
 */
export function requiredEvidenceDimensionsReceipt(
  requiredDimensions: readonly string[],
  envelopeValue: unknown,
): TypedGateResult {
  const envelope = accountabilityEnvelope(envelopeValue)
  if (!envelope) return fail('RESPONSE_ACCOUNTABILITY_ENVELOPE_MISSING')
  if (!requiredDimensions.length) return fail('REQUIRED_DIMENSIONS_EMPTY')
  const delivered = new Set(envelope.response_coverage_receipt.delivered_fact_ids)
  const evidence: Record<string, string[]> = {}
  const unratified: string[] = []
  const unevidenced: string[] = []
  for (const dimension of requiredDimensions) {
    if (!dimension.startsWith('scu.')) {
      unratified.push(dimension)
      continue
    }
    const facts = envelope.fact_register.facts.filter((fact) => fact.meaning.scu_ids.includes(dimension)
      && DELIVERABLE_DISPOSITIONS.has(fact.meaning.disposition)
      && delivered.has(fact.fact_id))
    if (facts.length) evidence[dimension] = facts.map((fact) => fact.fact_id).sort()
    else unevidenced.push(dimension)
  }
  if (unratified.length) return fail(`DIMENSION_EVIDENCE_MAP_UNRATIFIED:${unratified.join(',')}`)
  if (unevidenced.length) return fail(`REQUIRED_DIMENSION_NOT_DELIVERED:${unevidenced.join(',')}`)
  return { passed: true, receipt_ref: stableFingerprint({ gate_id: 'required_evidence_dimensions', evidence }) }
}

function missingRequiredFacts(envelope: InquiryResponseAccountability): InquiryRegisteredFact[] {
  const missingIds = new Set(envelope.response_coverage_receipt.missing_required_fact_ids ?? [])
  return envelope.fact_register.facts.filter((fact) => fact.materiality === 'required'
    && (MISSING_DISPOSITIONS.has(fact.meaning.disposition) || missingIds.has(fact.fact_id)))
}

/**
 * The response names the evidence it could not obtain: at least one required register fact is
 * missing, and every named item carries a label and a rationale (a reason, not a bare id).
 */
export function namedMissingEvidenceReceipt(envelopeValue: unknown): TypedGateResult {
  const envelope = accountabilityEnvelope(envelopeValue)
  if (!envelope) return fail('RESPONSE_ACCOUNTABILITY_ENVELOPE_MISSING')
  const missing = missingRequiredFacts(envelope)
  if (!missing.length) return fail('NO_REQUIRED_EVIDENCE_NAMED_MISSING')
  const unnamed = missing.filter((fact) => !fact.meaning.label.trim() || !fact.meaning.rationale.trim())
  if (unnamed.length) return fail(`MISSING_EVIDENCE_WITHOUT_REASON:${unnamed.map((fact) => fact.fact_id).join(',')}`)
  return {
    passed: true,
    receipt_ref: stableFingerprint({
      gate_id: 'named_missing_evidence',
      missing: missing.map((fact) => ({ fact_id: fact.fact_id, label: fact.meaning.label, disposition: fact.meaning.disposition })),
    }),
  }
}

/**
 * The door delivered a bounded answer instead of a complete-looking one: the inquiry did not
 * close complete, the coverage receipt does not claim completeness, the missing evidence is
 * named, and an answer was still delivered. Whether the prose bounds its claims well is the
 * independent judge's assessment, not this gate's.
 */
export function boundedInsufficiencyReceipt(args: {
  readonly terminal: string
  readonly answer: string
  readonly envelope: unknown
}): TypedGateResult {
  const envelope = accountabilityEnvelope(args.envelope)
  if (!envelope) return fail('RESPONSE_ACCOUNTABILITY_ENVELOPE_MISSING')
  if (args.terminal === 'complete') return fail('INQUIRY_CLOSED_COMPLETE_DESPITE_INSUFFICIENCY')
  if (envelope.response_coverage_receipt.status === 'COMPLETE') return fail('COVERAGE_CLAIMS_COMPLETE_DESPITE_INSUFFICIENCY')
  const named = namedMissingEvidenceReceipt(args.envelope)
  if (!named.passed) return fail(named.detail ?? 'NO_REQUIRED_EVIDENCE_NAMED_MISSING')
  if (!args.answer.trim()) return fail('BOUNDED_ANSWER_NOT_DELIVERED')
  return {
    passed: true,
    receipt_ref: stableFingerprint({
      gate_id: 'bounded_insufficiency',
      terminal: args.terminal,
      coverage_status: envelope.response_coverage_receipt.status,
      named_missing: named.receipt_ref,
    }),
  }
}
