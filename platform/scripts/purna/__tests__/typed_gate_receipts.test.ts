import { describe, expect, it } from 'vitest'
import {
  boundedInsufficiencyReceipt,
  namedMissingEvidenceReceipt,
  requiredEvidenceDimensionsReceipt,
} from '../typed_gate_receipts'

function fact(fact_id: string, scu: string, disposition: string, materiality: 'required' | 'supporting' = 'required', rationale = 'Why it matters.') {
  return {
    fact_id, kind: 'obligation', obligation_ids: [fact_id], obligation_id: fact_id, frontier_id: null, materiality,
    meaning: { label: `Evidence for ${scu}`, rationale, scu_ids: [scu], disposition }, evidence_refs: [], normalized_content: null,
  }
}

function envelope(facts: unknown[], delivered: string[], status = 'COMPLETE', missingRequired: string[] = []) {
  return {
    accountability_version: 'inquiry-response-accountability-v1',
    fact_register: { register_version: 'inquiry-fact-register-v1', facts },
    delivery_parts: [],
    response_coverage_receipt: { status, delivered_fact_ids: delivered, missing_required_fact_ids: missingRequired },
  }
}

describe('typed deterministic-gate receipts (RC-6.6)', () => {
  it('proves SCU-id dimensions only from delivered, served register facts', () => {
    const env = envelope([fact('f1', 'scu.a', 'served'), fact('f2', 'scu.b', 'empty'), fact('f3', 'scu.c', 'served')], ['f1', 'f2'])
    expect(requiredEvidenceDimensionsReceipt(['scu.a', 'scu.b'], env)).toMatchObject({ passed: true, receipt_ref: expect.stringMatching(/^sha256:/) })
    expect(requiredEvidenceDimensionsReceipt(['scu.a', 'scu.c'], env)).toMatchObject({ passed: false, detail: 'REQUIRED_DIMENSION_NOT_DELIVERED:scu.c' })
  })

  it('refuses a dark obligation as dimension evidence even when listed as delivered', () => {
    const env = envelope([fact('f1', 'scu.a', 'dark')], ['f1'])
    expect(requiredEvidenceDimensionsReceipt(['scu.a'], env)).toMatchObject({ passed: false })
  })

  it('never matches a semantic product label heuristically', () => {
    const env = envelope([fact('f1', 'scu.finance.prosperity_assessment', 'served')], ['f1'])
    expect(requiredEvidenceDimensionsReceipt(['wealth_mechanisms'], env))
      .toMatchObject({ passed: false, detail: 'DIMENSION_EVIDENCE_MAP_UNRATIFIED:wealth_mechanisms' })
  })

  it('names missing required evidence with its reason, or fails', () => {
    const named = envelope([fact('f1', 'scu.timing', 'dark'), fact('f2', 'scu.a', 'served')], ['f2'], 'INCOMPLETE_RESUMABLE')
    expect(namedMissingEvidenceReceipt(named)).toMatchObject({ passed: true })
    const nothingMissing = envelope([fact('f2', 'scu.a', 'served')], ['f2'])
    expect(namedMissingEvidenceReceipt(nothingMissing)).toMatchObject({ passed: false, detail: 'NO_REQUIRED_EVIDENCE_NAMED_MISSING' })
    const unexplained = envelope([fact('f1', 'scu.timing', 'failed', 'required', ' ')], [])
    expect(namedMissingEvidenceReceipt(unexplained)).toMatchObject({ passed: false, detail: 'MISSING_EVIDENCE_WITHOUT_REASON:f1' })
  })

  it('accepts bounded insufficiency only when nothing claims completeness and an answer is delivered', () => {
    const env = envelope([fact('f1', 'scu.timing', 'dark')], [], 'INCOMPLETE_RESUMABLE')
    expect(boundedInsufficiencyReceipt({ terminal: 'incomplete', answer: 'Structural promise only; timing cannot be established.', envelope: env }))
      .toMatchObject({ passed: true })
    expect(boundedInsufficiencyReceipt({ terminal: 'complete', answer: 'x', envelope: env }))
      .toMatchObject({ passed: false, detail: 'INQUIRY_CLOSED_COMPLETE_DESPITE_INSUFFICIENCY' })
    expect(boundedInsufficiencyReceipt({ terminal: 'incomplete', answer: 'x', envelope: envelope([fact('f1', 'scu.timing', 'dark')], [], 'COMPLETE') }))
      .toMatchObject({ passed: false, detail: 'COVERAGE_CLAIMS_COMPLETE_DESPITE_INSUFFICIENCY' })
    expect(boundedInsufficiencyReceipt({ terminal: 'incomplete', answer: '  ', envelope: env }))
      .toMatchObject({ passed: false, detail: 'BOUNDED_ANSWER_NOT_DELIVERED' })
  })

  it('fails every typed gate closed without a structurally valid envelope', () => {
    for (const bad of [null, {}, { accountability_version: 'inquiry-response-accountability-v1' }]) {
      expect(requiredEvidenceDimensionsReceipt(['scu.a'], bad)).toMatchObject({ passed: false, detail: 'RESPONSE_ACCOUNTABILITY_ENVELOPE_MISSING' })
      expect(namedMissingEvidenceReceipt(bad)).toMatchObject({ passed: false })
      expect(boundedInsufficiencyReceipt({ terminal: 'incomplete', answer: 'a', envelope: bad })).toMatchObject({ passed: false })
    }
  })
})
