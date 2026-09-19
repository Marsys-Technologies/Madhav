import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import { accountableAnswersHash, answersFromCollection, createAccountableAnswersArtifact, main } from '../answers_from_collection'
import type { AcceptanceCaseInput } from '../acceptance_cases'
import { createCollectionArtifact, type CollectedCase } from '../collection_types'
import { BEYOND_ACARYA_ACCEPTANCE_CASES } from '../../../src/lib/vidhi/inquiry/beyond_acarya_acceptance.corpus'

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

function collection(inputOverride: AcceptanceCaseInput = input, rowOverride: CollectedCase = row) {
  return createCollectionArtifact({
    suite: inputOverride.kind === 'product' ? 'product' : 'beyond_acarya',
    environment: 'candidate', expectedRevision: 'candidate-a', authorizationApprovalId: 'approval-1',
    target: { chart_id: '11111111-1111-4111-8111-111111111111', portal_url: 'https://portal.example.test', mcp_url: 'https://mcp.example.test' },
    caseInputs: [inputOverride],
    rows: (['portal', 'managed_mcp', 'raw_mcp'] as const).map((door) => ({ ...rowOverride, door })),
  })
}

describe('Purna collection answer bridge', () => {
  it('derives evidence only from the selected real door and leaves unexposed semantic receipts failed', () => {
    const [answer] = answersFromCollection({ inputs: [input], door: 'managed_mcp', collection: collection() })
    expect(answer).toMatchObject({ case_id: 'case-1', answer: 'Answer', response_accountability: row.responseAccountability })
    expect(answer?.evidence).toEqual(expect.arrayContaining([
      expect.objectContaining({ gate_id: 'inquiry_closure_receipt', passed: true }),
      expect.objectContaining({ gate_id: 'response_accountability', passed: true }),
      expect.objectContaining({ gate_id: 'citation_resolution', passed: true }),
      expect.objectContaining({ gate_id: 'required_evidence_dimensions', passed: false }),
    ]))
  })

  it('rejects duplicate or fixture rows at the collection-artifact boundary', () => {
    expect(() => createCollectionArtifact({
      suite: 'product', environment: 'candidate', expectedRevision: 'candidate-a', authorizationApprovalId: 'approval-1',
      target: { chart_id: '11111111-1111-4111-8111-111111111111', portal_url: 'https://portal.example.test', mcp_url: 'https://mcp.example.test' },
      caseInputs: [input], rows: [row, row],
    })).toThrow('PURNA_COLLECTION_ARTIFACT_INVALID')
    expect(() => createCollectionArtifact({
      suite: 'product', environment: 'candidate', expectedRevision: 'candidate-a', authorizationApprovalId: 'approval-1',
      target: { chart_id: '11111111-1111-4111-8111-111111111111', portal_url: 'https://portal.example.test', mcp_url: 'https://mcp.example.test' },
      caseInputs: [input], rows: (['portal', 'managed_mcp', 'raw_mcp'] as const).map((door) => ({ ...row, door, source: 'fixture' as const })),
    })).toThrow('PURNA_COLLECTION_ARTIFACT_INVALID')
  })

  it('maps the immutable original-five gates only from the exact collected case manifest', () => {
    const original: AcceptanceCaseInput = {
      ...input,
      kind: 'beyond_acarya',
      deterministic_gates: ['immutable_case_input', 'source_acceptance_denominator'],
      required_dimensions: ['scu.one', 'scu.two'],
    }
    const source = collection(original)
    const [answer] = answersFromCollection({ inputs: [original], door: 'managed_mcp', collection: source })
    expect(answer?.evidence).toEqual([
      expect.objectContaining({ gate_id: 'immutable_case_input', passed: true, receipt_ref: expect.stringMatching(/^sha256:/) }),
      expect.objectContaining({ gate_id: 'source_acceptance_denominator', passed: true, receipt_ref: expect.stringMatching(/^sha256:/) }),
    ])
    expect(() => answersFromCollection({
      inputs: [{ ...original, required_dimensions: ['scu.changed'] }], door: 'managed_mcp', collection: source,
    })).toThrow('PURNA_COLLECTION_CASE_INPUT_MISMATCH')
  })

  it('emits a deterministic accountable-answer identity bound to door and collection', () => {
    const source = collection()
    const artifact = createAccountableAnswersArtifact({
      inputs: [input], door: 'managed_mcp', collection: source, collectionArtifact: '/restricted/collection.json',
    })
    expect(artifact.provenance).toMatchObject({
      door: 'managed_mcp', collection_hash: source.collection_hash,
      collection_manifest_hash: source.manifest_hash,
      accountable_answers_hash: accountableAnswersHash(artifact.answers, source.collection_hash, 'managed_mcp'),
    })
  })

  it('executes the collection-to-accountable-answer CLI against the immutable corpus', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'purna-accountable-answers-'))
    const sourceCase = BEYOND_ACARYA_ACCEPTANCE_CASES[0]!
    const immutableInput: AcceptanceCaseInput = {
      case_id: sourceCase.case_id,
      kind: 'beyond_acarya',
      question: sourceCase.question,
      scope_tuple: sourceCase.scope_tuple,
      deterministic_gates: ['immutable_case_input', 'source_acceptance_denominator'],
      required_dimensions: sourceCase.expected_required_scu_ids,
      expected: 'supported_complete',
    }
    const immutableRow = { ...row, caseId: sourceCase.case_id }
    const source = collection(immutableInput, immutableRow)
    const collectionPath = join(directory, 'collection.json')
    const writeSpy = vi.spyOn(process.stdout, 'write').mockImplementation(() => true)
    try {
      await writeFile(collectionPath, `${JSON.stringify(source)}\n`)
      await main([
        '--suite', 'beyond_acarya', '--door', 'managed_mcp',
        '--collection', collectionPath, '--artifact-dir', directory,
      ])
      const path = join(directory, `accountable-answers-managed_mcp-${source.collection_hash.replace(/^sha256:/, '').slice(0, 16)}.json`)
      const artifact = JSON.parse(await readFile(path, 'utf8')) as Record<string, unknown>
      expect(artifact).toMatchObject({
        schema_version: 'purna-accountable-answers/v1',
        provenance: { door: 'managed_mcp', collection_hash: source.collection_hash },
      })
    } finally {
      writeSpy.mockRestore()
      await rm(directory, { recursive: true, force: true })
    }
  })
})
