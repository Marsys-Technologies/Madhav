import { describe, expect, it } from 'vitest'
import { answersFromCollection } from '../answers_from_collection'
import type { AcceptanceCaseInput } from '../acceptance_cases'
import type { CollectedCase } from '../collection_types'

const input: AcceptanceCaseInput = {
  case_id: 'case-1', kind: 'product', question: 'Question', scope_tuple: null,
  deterministic_gates: ['inquiry_closure_receipt', 'response_accountability', 'citation_resolution', 'required_evidence_dimensions'],
  required_dimensions: ['wealth'], expected: 'supported_complete',
}
const row: CollectedCase = {
  caseId: 'case-1', door: 'managed_mcp', inquiryId: 'i-1', expectedRevision: 'candidate-a', observedRevision: 'candidate-a',
  snapshotHash: 'snapshot', chartBuildId: 'build', answer: 'Answer', responseAccountability: { accountability_version: 'inquiry-response-accountability-v1' },
  receiptRefs: ['receipt-1'], materialFactIds: ['fact-1'], deliveredFactIds: ['fact-1'], unresolvedObligationIds: [],
  networkCallCount: 2, source: 'candidate', terminal: 'complete', diagnostic: null,
}

describe('Purna collection answer bridge', () => {
  it('derives evidence only from the selected real door and leaves unexposed semantic receipts failed', () => {
    const [answer] = answersFromCollection({ inputs: [input], door: 'managed_mcp', rows: [row] })
    expect(answer).toMatchObject({ case_id: 'case-1', answer: 'Answer', response_accountability: row.responseAccountability })
    expect(answer?.evidence).toEqual(expect.arrayContaining([
      expect.objectContaining({ gate_id: 'inquiry_closure_receipt', passed: true }),
      expect.objectContaining({ gate_id: 'response_accountability', passed: true }),
      expect.objectContaining({ gate_id: 'citation_resolution', passed: true }),
      expect.objectContaining({ gate_id: 'required_evidence_dimensions', passed: false }),
    ]))
  })

  it('rejects a duplicate or fixture arm rather than selecting an arbitrary answer', () => {
    expect(() => answersFromCollection({ inputs: [input], door: 'managed_mcp', rows: [row, row] })).toThrow('PURNA_COLLECTION_DUPLICATE_DOOR_CASE')
    expect(() => answersFromCollection({ inputs: [input], door: 'managed_mcp', rows: [{ ...row, source: 'fixture' }] })).toThrow('PURNA_COLLECTION_FIXTURE_NOT_ACCEPTANCE_EVIDENCE')
  })
})
