import type { AcceptanceAnswer, AcceptanceCaseInput, DeterministicEvidence } from './acceptance_cases'
import type { AcceptanceDoor, CollectedCase } from './collection_types'
import { stableFingerprint } from '../../src/lib/retrieval/registry/knowledge/stable'

function evidence(gate_id: string, passed: boolean, receipt_ref: string | null, detail?: string): DeterministicEvidence {
  return { gate_id, passed, receipt_ref, ...(detail ? { detail } : {}) }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function accountabilityEvidence(row: CollectedCase): DeterministicEvidence {
  if (!isObject(row.responseAccountability)) {
    return evidence('response_accountability', false, null, 'RESPONSE_ACCOUNTABILITY_ENVELOPE_MISSING')
  }
  return evidence('response_accountability', true, `response_accountability:${stableFingerprint(row.responseAccountability)}`)
}

function gateEvidence(input: AcceptanceCaseInput, row: CollectedCase): readonly DeterministicEvidence[] {
  const delivered = new Set(row.deliveredFactIds)
  const allMaterialDelivered = row.materialFactIds.every((factId) => delivered.has(factId))
  return input.deterministic_gates.map((gate): DeterministicEvidence => {
    if (gate === 'inquiry_closure_receipt') {
      const receipt = row.receiptRefs[0] ?? null
      return evidence(gate, row.terminal === 'complete' && row.observedRevision === row.expectedRevision && receipt !== null, receipt,
        row.terminal === 'complete' && row.observedRevision === row.expectedRevision && receipt !== null ? undefined : 'COMPLETE_REVISION_BOUND_CLOSURE_RECEIPT_REQUIRED')
    }
    if (gate === 'response_accountability') return accountabilityEvidence(row)
    if (gate === 'citation_resolution') {
      return evidence(gate, row.materialFactIds.length > 0 && allMaterialDelivered, row.receiptRefs[0] ?? null,
        row.materialFactIds.length > 0 && allMaterialDelivered ? undefined : 'MATERIAL_FACT_DELIVERY_RECEIPT_INCOMPLETE')
    }
    // Collection intentionally has no heuristic substitute for these semantic
    // receipts. A door must expose typed proof before this bridge can pass it.
    return evidence(gate, false, null, `CHANNEL_${gate.toUpperCase()}_RECEIPT_UNAVAILABLE`)
  })
}

/**
 * Convert exactly one actual channel arm into the answer-input shape consumed
 * by the independent judge and acceptance runner. Duplicate/missing rows are
 * rejected; unsupported evidence remains an explicit failed deterministic gate.
 */
export function answersFromCollection(args: {
  readonly inputs: readonly AcceptanceCaseInput[]
  readonly door: AcceptanceDoor
  readonly rows: readonly CollectedCase[]
}): readonly AcceptanceAnswer[] {
  const byCase = new Map<string, CollectedCase>()
  for (const row of args.rows.filter((candidate) => candidate.door === args.door)) {
    if (byCase.has(row.caseId)) throw new Error('PURNA_COLLECTION_DUPLICATE_DOOR_CASE')
    byCase.set(row.caseId, row)
  }
  return args.inputs.map((input): AcceptanceAnswer => {
    const row = byCase.get(input.case_id)
    if (!row) throw new Error('PURNA_COLLECTION_DOOR_CASE_MISSING')
    if (row.source === 'fixture') throw new Error('PURNA_COLLECTION_FIXTURE_NOT_ACCEPTANCE_EVIDENCE')
    return {
      case_id: input.case_id,
      answer: row.answer || null,
      evidence: gateEvidence(input, row),
      response_accountability: row.responseAccountability as AcceptanceAnswer['response_accountability'],
    }
  })
}
