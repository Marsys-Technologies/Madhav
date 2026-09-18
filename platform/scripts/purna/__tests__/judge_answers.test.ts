import { describe, expect, it } from 'vitest'
import { buildJudgePrompt, judgeAnswers, judgedAnswersArtifact, parseJudgeOutput } from '../judge_answers'
import type { AcceptanceAnswer, AcceptanceCaseInput } from '../acceptance_cases'
import { PURNA_ACCOUNTABLE_ANSWERS_VERSION } from '../collection_types'

const input: AcceptanceCaseInput = {
  case_id: 'case-1', kind: 'product', question: 'What should I do?', scope_tuple: null,
  deterministic_gates: ['receipt'], required_dimensions: ['timing'], expected: 'supported_complete',
}

const accountability = { accountability_version: 'inquiry-response-accountability-v1' } as never
const answer: AcceptanceAnswer = {
  case_id: 'case-1', answer: 'A calibrated answer with evidence.',
  evidence: [{ gate_id: 'receipt', passed: true, receipt_ref: 'receipt-1' }],
  response_accountability: accountability,
}

describe('independent Purna answer judge', () => {
  it('preserves collection and door provenance when attaching the assessment', () => {
    const provenance = {
      collection_artifact: '/restricted/collection.json',
      collection_hash: `sha256:${'a'.repeat(64)}`,
      collection_manifest_hash: `sha256:${'b'.repeat(64)}`,
      suite: 'product' as const,
      door: 'portal' as const,
      environment: 'candidate' as const,
      expected_revision: 'candidate-a',
      authorization_approval_id: 'collection-approval',
      accountable_answers_hash: `sha256:${'c'.repeat(64)}`,
    }
    expect(judgedAnswersArtifact({
      input: { schema_version: PURNA_ACCOUNTABLE_ANSWERS_VERSION, provenance, answers: [] },
      answers: [], approvalId: 'judge-approval', modelId: 'judge-model',
    })).toMatchObject({
      provenance,
      assessment: { approval_id: 'judge-approval', assessor: 'independent_eval_judge', model_id: 'judge-model' },
    })
  })

  it('requires all four integer rubric scores', () => {
    expect(parseJudgeOutput({ relevance: 5, evidence_based_explanation: 4, contradiction_handling: 3, usefulness: 4, rationale: 'grounded' }))
      .toMatchObject({ usefulness: 4 })
    expect(() => parseJudgeOutput({ relevance: 5, evidence_based_explanation: 4, contradiction_handling: 3, usefulness: 4.5, rationale: 'grounded' }))
      .toThrow('PURNA_ANSWER_JUDGE_OUTPUT_INVALID')
  })

  it('adds an independent assessment only after an accountable answer is judged', async () => {
    const judged = await judgeAnswers({
      inputs: [input], answers: [answer], modelId: 'judge-model',
      invoke: async () => ({ relevance: 4, evidence_based_explanation: 5, contradiction_handling: 4, usefulness: 4, rationale: 'clear evidence and calibrated limits' }),
    })
    expect(judged[0]?.qualitative_assessment).toMatchObject({ assessor: 'independent_eval_judge', model_id: 'judge-model', relevance: 4 })
    expect(buildJudgePrompt(input, answer)).toContain('contradiction_handling')
  })

  it('fails closed when a response accountability envelope is absent', async () => {
    await expect(judgeAnswers({
      inputs: [input], answers: [{ ...answer, response_accountability: null }], modelId: 'judge-model', invoke: async () => ({}),
    })).rejects.toThrow('PURNA_ANSWER_JUDGE_ACCOUNTABILITY_REQUIRED')
  })
})
