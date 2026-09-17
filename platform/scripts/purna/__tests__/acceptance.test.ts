import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { beforeAll, describe, expect, it } from 'vitest'
import { stableFingerprint } from '../../../src/lib/retrieval/registry/knowledge/stable'
import {
  PRODUCT_ACCEPTANCE_PROTOCOL_VERSION,
  PRODUCT_ACCEPTANCE_RUN_VERSION,
  casesForSuite,
  type AcceptanceCaseInput,
  type ProductAcceptanceProtocol,
  validateResponseAccountability,
  validateProtocol,
} from '../acceptance_cases'
import { parseCliArgs, writeAcceptanceRun } from '../acceptance'
import { scoreAnswers } from '../score_answers'

let protocol: ProductAcceptanceProtocol

const scoreInput: AcceptanceCaseInput = {
  case_id: 'deterministic_product_case', kind: 'product', question: null, scope_tuple: null,
  deterministic_gates: ['receipt_gate'],
}

const candidateConfig = {
  schema_version: 'purna-product-acceptance-environment/v1' as const,
  environment: 'candidate' as const,
  base_url: 'https://candidate.example.invalid',
  revision: 'candidate-revision-123',
  authorization: { mode: 'approved_non_secret' as const, approval_id: 'approval-123' },
  evidence_mode: 'candidate_or_live' as const,
}

const validFactRegister = {
  register_version: 'inquiry-fact-register-v1',
  contract_id: 'contract-1',
  semantic_contract_hash: `sha256:${'a'.repeat(64)}`,
  facts: [],
  required_fact_ids: [],
  validation_errors: [],
}

const validFactRegisterHash = stableFingerprint(validFactRegister)
const validCoverage = {
  receipt_version: 'inquiry-response-coverage-v1',
  contract_id: 'contract-1',
  semantic_contract_hash: validFactRegister.semantic_contract_hash,
  fact_register_hash: validFactRegisterHash,
  status: 'INCOMPLETE_RESUMABLE',
  coverage: {
    synthesis_present: false,
    all_total: 0,
    all_delivered: 0,
    all_permitted_exclusions: 0,
    required_total: 0,
    required_delivered: 0,
    interpretation_mapped: 0,
  },
  delivered_fact_ids: [],
  permitted_exclusion_fact_ids: [],
  missing_fact_ids: [],
  missing_required_fact_ids: [],
  interpretation_unmapped_fact_ids: [],
  delivery_part_ids: ['structured-findings:1'],
  invalid_delivery_claims: [],
  continuation: {
    iteration: 0,
    max_iterations: 4,
    exhausted: false,
    next_action_ids: [],
    blocked_item_ids: [],
    unresolved_obligation_ids: [],
    frontier_ids: [],
  },
  resume_required: true,
}

const validResponseAccountability = {
  accountability_version: 'inquiry-response-accountability-v1',
  fact_register: {
    ...validFactRegister,
    register_hash: validFactRegisterHash,
  },
  delivery_parts: [{
    part_id: 'structured-findings:1',
    kind: 'structured_findings',
    content_hash: stableFingerprint({
      kind: 'structured_findings', facts: [], evidence_payload_hashes: [], content: null, exclusion_reason: null,
    }),
    content: null,
    fact_ids: [],
    evidence_payload_hashes: [],
    exclusion_reason: null,
  }],
  response_coverage_receipt: { ...validCoverage, receipt_hash: stableFingerprint(validCoverage) },
}

function withCoverageReceipt<T extends Record<string, unknown>>(coverage: T): T & { receipt_hash: string } {
  const projection: Record<string, unknown> = { ...coverage }
  delete projection.receipt_hash
  return { ...projection, receipt_hash: stableFingerprint(projection) } as T & { receipt_hash: string }
}

function accountabilityWithDeliveredFact() {
  const fact = {
    fact_id: 'fact:one',
    kind: 'frontier',
    obligation_ids: [],
    obligation_id: null,
    frontier_id: 'frontier:one',
    materiality: 'required',
    meaning: { label: 'fact', rationale: 'test', scu_ids: ['scu.test'], disposition: 'absorbed' },
    evidence_refs: [],
    normalized_content: null,
  }
  const registerProjection = {
    register_version: 'inquiry-fact-register-v1',
    contract_id: 'contract-2',
    semantic_contract_hash: `sha256:${'b'.repeat(64)}`,
    facts: [fact],
    required_fact_ids: ['fact:one'],
    validation_errors: [],
  }
  const registerHash = stableFingerprint(registerProjection)
  const part = {
    part_id: 'structured-findings:fact-one',
    kind: 'structured_findings',
    content_hash: stableFingerprint({
      kind: 'structured_findings', facts: [fact], evidence_payload_hashes: [], content: null, exclusion_reason: null,
    }),
    content: null,
    fact_ids: ['fact:one'],
    evidence_payload_hashes: [],
    exclusion_reason: null,
  }
  const coverage = {
    receipt_version: 'inquiry-response-coverage-v1',
    contract_id: 'contract-2',
    semantic_contract_hash: registerProjection.semantic_contract_hash,
    fact_register_hash: registerHash,
    status: 'INCOMPLETE_RESUMABLE',
    coverage: {
      synthesis_present: false,
      all_total: 1,
      all_delivered: 1,
      all_permitted_exclusions: 0,
      required_total: 1,
      required_delivered: 1,
      interpretation_mapped: 0,
    },
    delivered_fact_ids: ['fact:one'],
    permitted_exclusion_fact_ids: [],
    missing_fact_ids: [],
    missing_required_fact_ids: [],
    interpretation_unmapped_fact_ids: [],
    delivery_part_ids: [part.part_id],
    invalid_delivery_claims: [],
    continuation: {
      iteration: 0,
      max_iterations: 4,
      exhausted: false,
      next_action_ids: [],
      blocked_item_ids: [],
      unresolved_obligation_ids: [],
      frontier_ids: [],
    },
    resume_required: true,
  }
  return {
    accountability_version: 'inquiry-response-accountability-v1',
    fact_register: { ...registerProjection, register_hash: registerHash },
    delivery_parts: [part],
    response_coverage_receipt: withCoverageReceipt(coverage),
  }
}

function accountabilityWithCompleteProse(answer: string) {
  const base = accountabilityWithDeliveredFact()
  const prosePart = {
    part_id: 'prose:complete',
    kind: 'prose',
    content_hash: stableFingerprint(answer),
    content: null,
    fact_ids: [],
    evidence_payload_hashes: [],
    exclusion_reason: null,
  }
  const coverage = withCoverageReceipt({
    ...base.response_coverage_receipt,
    status: 'COMPLETE',
    coverage: { ...base.response_coverage_receipt.coverage, synthesis_present: true },
    delivery_part_ids: [base.delivery_parts[0]!.part_id, prosePart.part_id].sort(),
    resume_required: false,
  })
  return { ...base, delivery_parts: [...base.delivery_parts, prosePart], response_coverage_receipt: coverage }
}

describe('Purna product acceptance harness', () => {
  beforeAll(async () => {
    protocol = JSON.parse(await readFile(new URL(
      '../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PRODUCT_ACCEPTANCE_PROTOCOL_v2.json',
      import.meta.url,
    ), 'utf8')) as ProductAcceptanceProtocol
  })

  it('pins the versioned protocol manifest to the immutable Beyond-Acarya denominator and case content', () => {
    expect(validateProtocol(protocol)).toMatchObject({ protocol_version: PRODUCT_ACCEPTANCE_PROTOCOL_VERSION })
  })

  it('rejects empty or malformed product scenario/gate declarations and a stale corpus fingerprint', () => {
    const emptyScenarios = structuredClone(protocol) as { product_scenarios: unknown[] }
    emptyScenarios.product_scenarios = []
    expect(() => validateProtocol(emptyScenarios)).toThrow('PRODUCT_ACCEPTANCE_PROTOCOL_CONTENT_MISMATCH')

    const malformedGates = structuredClone(protocol) as { product_scenarios: Array<{ deterministic_gates: unknown }> }
    malformedGates.product_scenarios[0].deterministic_gates = []
    expect(() => validateProtocol(malformedGates)).toThrow('PRODUCT_ACCEPTANCE_PROTOCOL_CONTENT_MISMATCH')

    const staleFingerprint = structuredClone(protocol) as { immutable_beyond_acarya: { case_content_fingerprint: { value: string } } }
    staleFingerprint.immutable_beyond_acarya.case_content_fingerprint.value = '0'.repeat(64)
    expect(() => validateProtocol(staleFingerprint)).toThrow('PRODUCT_ACCEPTANCE_IMMUTABLE_CORPUS_MISMATCH')
  })

  it('requires explicit suite, environment, and non-secret configuration paths', () => {
    expect(() => parseCliArgs(['--suite', 'product'])).toThrow('PRODUCT_ACCEPTANCE_CLI_REQUIRED_ARGUMENT_MISSING')
    expect(() => parseCliArgs([
      '--suite', 'product', '--environment', 'live', '--config', 'config.json', '--input', 'input.json',
      '--artifact-dir', 'records', '--extra', 'no',
    ])).toThrow('PRODUCT_ACCEPTANCE_CLI_INVALID')
  })

  it('makes failed deterministic evidence override a perfect qualitative score', () => {
    const score = scoreAnswers([scoreInput], [{
      case_id: 'deterministic_product_case', answer: 'unsupported', qualitative_score: 1,
      evidence: [{ gate_id: 'receipt_gate', passed: false, receipt_ref: null }],
    }])
    expect(score.verdict).toBe('FAIL_DETERMINISTIC_EVIDENCE')
    expect(score.cases[0]).toMatchObject({ qualitative_score: 1, verdict: 'FAIL_DETERMINISTIC_EVIDENCE' })
  })

  it('records qualitative and incomplete per-case failures structurally', () => {
    const inputs: AcceptanceCaseInput[] = [
      { ...scoreInput, case_id: 'qualitative_case' },
      { ...scoreInput, case_id: 'incomplete_case' },
    ]
    const score = scoreAnswers(inputs, [
      { case_id: 'qualitative_case', answer: 'low quality', qualitative_score: 0.2, evidence: [{ gate_id: 'receipt_gate', passed: true, receipt_ref: 'r1' }] },
      { case_id: 'incomplete_case', answer: 'unscored', evidence: [{ gate_id: 'receipt_gate', passed: true, receipt_ref: 'r2' }] },
    ])
    expect(score.failures).toEqual([
      expect.objectContaining({ case_id: 'qualitative_case', kind: 'qualitative', gate_id: null, qualitative_score: 0.2 }),
      expect.objectContaining({ case_id: 'incomplete_case', kind: 'incomplete', gate_id: null, qualitative_score: null }),
    ])
  })

  it('rejects coercive JSON and duplicate or unknown answer and gate IDs before persistence', async () => {
    const artifactDir = await mkdtemp(join(tmpdir(), 'purna-acceptance-'))
    const firstCase = casesForSuite(protocol, 'product')[0]
    const answer = {
      case_id: firstCase.case_id, answer: 'answer', qualitative_score: 1,
      evidence: [{ gate_id: firstCase.deterministic_gates[0], passed: true, receipt_ref: 'r1' }],
    }
    try {
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{ ...answer, qualitative_score: '1' }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_INPUT_INVALID')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [answer, answer] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_DUPLICATE_ANSWER_ID')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{ ...answer, case_id: 'unknown_case' }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_UNKNOWN_ANSWER_ID')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{ ...answer, evidence: [...answer.evidence, { gate_id: 'unknown_gate', passed: true, receipt_ref: 'r2' }] }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_UNKNOWN_GATE_ID')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{ ...answer, evidence: [...answer.evidence, answer.evidence[0]] }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_DUPLICATE_GATE_ID')
    } finally {
      await rm(artifactDir, { recursive: true, force: true })
    }
  })

  it('rejects malformed response accountability before persistence and retains a complete typed envelope', async () => {
    const artifactDir = await mkdtemp(join(tmpdir(), 'purna-acceptance-'))
    const firstCase = casesForSuite(protocol, 'product')[0]
    const answer = {
      case_id: firstCase.case_id,
      answer: 'answer',
      qualitative_score: 1,
      evidence: [{ gate_id: firstCase.deterministic_gates[0], passed: true, receipt_ref: 'r1' }],
    }
    try {
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{ ...answer, response_accountability: {} }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{
          ...answer,
          response_accountability: {
            ...validResponseAccountability,
            response_coverage_receipt: {
              ...validResponseAccountability.response_coverage_receipt,
              continuation: { ...validResponseAccountability.response_coverage_receipt.continuation, exhausted: 'false' },
            },
          },
        }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{
          ...answer,
          response_accountability: { ...validResponseAccountability, untyped_forgery: true },
        }] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
      const written = await writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{ ...answer, response_accountability: validResponseAccountability }] }, artifactDir,
      })
      expect(written.record.answers[0]?.response_accountability).toMatchObject({
        accountability_version: 'inquiry-response-accountability-v1',
        response_coverage_receipt: { fact_register_hash: validFactRegisterHash, receipt_hash: stableFingerprint(validCoverage) },
      })
    } finally {
      await rm(artifactDir, { recursive: true, force: true })
    }
  })

  it('persists a valid COMPLETE prose accountability envelope through writeAcceptanceRun', async () => {
    const artifactDir = await mkdtemp(join(tmpdir(), 'purna-acceptance-'))
    const firstCase = casesForSuite(protocol, 'product')[0]
    const answer = 'Complete accountable response'
    try {
      const written = await writeAcceptanceRun({
        protocol,
        suite: 'product',
        environment: 'candidate',
        environmentConfig: candidateConfig,
        input: { answers: [{
          case_id: firstCase.case_id,
          answer,
          qualitative_score: 1,
          evidence: [{ gate_id: firstCase.deterministic_gates[0], passed: true, receipt_ref: 'receipt-1' }],
          response_accountability: accountabilityWithCompleteProse(answer),
        }] },
        artifactDir,
      })
      expect(written.record.answers[0]?.response_accountability?.response_coverage_receipt.status).toBe('COMPLETE')
    } finally {
      await rm(artifactDir, { recursive: true, force: true })
    }
  })

  it('rejects forged-but-rehashed accountability coverage and delivery projections', () => {
    const base = accountabilityWithDeliveredFact()
    expect(validateResponseAccountability(base, 'answer')).toMatchObject({
      response_coverage_receipt: { status: 'INCOMPLETE_RESUMABLE' },
    })

    const arbitraryComplete = {
      ...base,
      response_coverage_receipt: withCoverageReceipt({
        ...base.response_coverage_receipt,
        status: 'COMPLETE',
        coverage: { ...base.response_coverage_receipt.coverage, all_total: 99, synthesis_present: true },
        resume_required: false,
      }),
    }
    expect(() => validateResponseAccountability(arbitraryComplete, 'answer')).toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')

    const overlap = {
      ...base,
      response_coverage_receipt: withCoverageReceipt({
        ...base.response_coverage_receipt,
        permitted_exclusion_fact_ids: ['fact:one'],
        coverage: { ...base.response_coverage_receipt.coverage, all_permitted_exclusions: 1 },
      }),
    }
    expect(() => validateResponseAccountability(overlap, 'answer')).toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')

    const omittedRequiredProjection = {
      ...base,
      fact_register: {
        ...base.fact_register,
        required_fact_ids: [],
      },
    }
    const requiredProjection: Record<string, unknown> = { ...omittedRequiredProjection.fact_register }
    delete requiredProjection.register_hash
    const rehashedRegister = { ...requiredProjection, register_hash: stableFingerprint(requiredProjection) }
    const requiredCoverageProjection: Record<string, unknown> = { ...base.response_coverage_receipt }
    delete requiredCoverageProjection.receipt_hash
    const rehashedCoverage = withCoverageReceipt({
      ...requiredCoverageProjection,
      fact_register_hash: rehashedRegister.register_hash,
    })
    expect(() => validateResponseAccountability({
      ...omittedRequiredProjection,
      fact_register: rehashedRegister,
      response_coverage_receipt: rehashedCoverage,
    }, 'answer')).toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')

    const arbitraryPartHash = {
      ...base,
      delivery_parts: [{ ...base.delivery_parts[0], content_hash: `sha256:${'c'.repeat(64)}` }],
    }
    expect(() => validateResponseAccountability({
      ...arbitraryPartHash,
      response_coverage_receipt: withCoverageReceipt(base.response_coverage_receipt),
    }, 'answer')).toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')

    const capBypass = {
      ...base,
      response_coverage_receipt: withCoverageReceipt({
        ...base.response_coverage_receipt,
        continuation: {
          ...base.response_coverage_receipt.continuation,
          iteration: 4,
          max_iterations: 4,
          next_action_ids: ['action:remaining'],
        },
      }),
    }
    expect(() => validateResponseAccountability(capBypass, 'answer')).toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')

    const denominatorErrorProjection: Record<string, unknown> = {
      ...base.fact_register,
      validation_errors: ['required denominator mismatch'],
    }
    delete denominatorErrorProjection.register_hash
    const denominatorErrorRegister = {
      ...denominatorErrorProjection,
      register_hash: stableFingerprint(denominatorErrorProjection),
    }
    const denominatorErrorCoverage = withCoverageReceipt({
      ...base.response_coverage_receipt,
      fact_register_hash: denominatorErrorRegister.register_hash,
    })
    expect(() => validateResponseAccountability({
      ...base,
      fact_register: denominatorErrorRegister,
      response_coverage_receipt: denominatorErrorCoverage,
    }, 'answer')).toThrow('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
  })

  it('rejects fixture evidence as live evidence and rejects secret-bearing configuration', async () => {
    const artifactDir = await mkdtemp(join(tmpdir(), 'purna-acceptance-'))
    try {
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'live',
        environmentConfig: { ...candidateConfig, environment: 'live', evidence_mode: 'fixture' },
        input: { answers: [] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_FIXTURE_NOT_LIVE_EVIDENCE')
      await expect(writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate',
        environmentConfig: { ...candidateConfig, api_token: 'not-allowed' },
        input: { answers: [] }, artifactDir,
      })).rejects.toThrow('PRODUCT_ACCEPTANCE_SECRET_CONFIG_FORBIDDEN')
    } finally {
      await rm(artifactDir, { recursive: true, force: true })
    }
  })

  it('persists per-case verdicts and structured deterministic failures without network activity', async () => {
    const artifactDir = await mkdtemp(join(tmpdir(), 'purna-acceptance-'))
    const firstCase = casesForSuite(protocol, 'product')[0]
    try {
      const written = await writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{
          case_id: firstCase.case_id, answer: 'answer retained despite failed evidence', qualitative_score: 1,
          evidence: firstCase.deterministic_gates.map((gate_id, index) => ({
            gate_id, passed: index !== 0, receipt_ref: index === 0 ? null : `receipt-${gate_id}`,
            ...(index === 0 ? { detail: 'receipt unavailable' } : {}),
          })),
        }] },
        artifactDir, now: new Date('2026-09-17T00:00:00.000Z'), runId: 'run-test',
      })
      const persisted = JSON.parse(await readFile(written.path, 'utf8')) as Record<string, unknown>
      expect(persisted).toMatchObject({
        schema_version: PRODUCT_ACCEPTANCE_RUN_VERSION, run_id: 'run-test', environment: 'candidate',
        revision: 'candidate-revision-123', verdict: 'FAIL_DETERMINISTIC_EVIDENCE', network_calls_made: 0,
      })
      expect(persisted.case_inputs).toHaveLength(4)
      expect(persisted.answers).toHaveLength(1)
      expect(persisted.evidence).toHaveLength(3)
      expect(persisted.case_verdicts).toHaveLength(4)
      expect(persisted.failures).toEqual(expect.arrayContaining([
        expect.objectContaining({ case_id: firstCase.case_id, kind: 'deterministic' }),
        expect.objectContaining({ kind: 'deterministic', detail: 'answer_missing' }),
      ]))
    } finally {
      await rm(artifactDir, { recursive: true, force: true })
    }
  })
})
