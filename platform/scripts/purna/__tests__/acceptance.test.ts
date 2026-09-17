import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { BEYOND_ACARYA_ACCEPTANCE_CASES, BEYOND_ACARYA_CORPUS_VERSION } from '../../../src/lib/vidhi/inquiry/beyond_acarya_acceptance.corpus'
import {
  PRODUCT_ACCEPTANCE_PROTOCOL_VERSION,
  PRODUCT_ACCEPTANCE_RUN_VERSION,
  casesForSuite,
  type ProductAcceptanceProtocol,
  validateProtocol,
} from '../acceptance_cases'
import { parseCliArgs, writeAcceptanceRun } from '../acceptance'
import { scoreAnswers } from '../score_answers'

const protocol: ProductAcceptanceProtocol = {
  schema_version: 'madhav-purna-anvesana/product-acceptance-protocol/v2',
  protocol_version: PRODUCT_ACCEPTANCE_PROTOCOL_VERSION,
  immutable_beyond_acarya: {
    corpus_version: BEYOND_ACARYA_CORPUS_VERSION,
    case_ids: BEYOND_ACARYA_ACCEPTANCE_CASES.map((item) => item.case_id),
  },
  product_scenarios: [{
    scenario_id: 'deterministic_product_case', description: 'test-only scenario', deterministic_gates: ['receipt_gate'],
  }],
  hard_gates: ['explicit_suite_and_environment'],
  run_record: { schema_version: PRODUCT_ACCEPTANCE_RUN_VERSION, required_fields: ['answers'] },
}

const candidateConfig = {
  schema_version: 'purna-product-acceptance-environment/v1' as const,
  environment: 'candidate' as const,
  base_url: 'https://candidate.example.invalid',
  revision: 'candidate-revision-123',
  authorization: { mode: 'approved_non_secret' as const, approval_id: 'approval-123' },
  evidence_mode: 'candidate_or_live' as const,
}

describe('Purna product acceptance harness', () => {
  it('pins the versioned protocol manifest to the immutable Beyond-Acarya denominator', async () => {
    const manifest = JSON.parse(await readFile(new URL(
      '../../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PRODUCT_ACCEPTANCE_PROTOCOL_v2.json',
      import.meta.url,
    ), 'utf8'))
    expect(validateProtocol(manifest)).toMatchObject({ protocol_version: PRODUCT_ACCEPTANCE_PROTOCOL_VERSION })
  })

  it('requires explicit suite, environment, and non-secret configuration paths', () => {
    expect(() => parseCliArgs(['--suite', 'product'])).toThrow('PRODUCT_ACCEPTANCE_CLI_REQUIRED_ARGUMENT_MISSING')
    expect(() => parseCliArgs([
      '--suite', 'product', '--environment', 'live', '--config', 'config.json', '--input', 'input.json',
      '--artifact-dir', 'records', '--extra', 'no',
    ])).toThrow('PRODUCT_ACCEPTANCE_CLI_INVALID')
  })

  it('makes failed deterministic evidence override a perfect qualitative score', () => {
    const inputs = casesForSuite(protocol, 'product')
    const score = scoreAnswers(inputs, [{
      case_id: 'deterministic_product_case', answer: 'unsupported', qualitative_score: 1,
      evidence: [{ gate_id: 'receipt_gate', passed: false, receipt_ref: null }],
    }])
    expect(score.verdict).toBe('FAIL_DETERMINISTIC_EVIDENCE')
    expect(score.cases[0]).toMatchObject({ qualitative_score: 1, verdict: 'FAIL_DETERMINISTIC_EVIDENCE' })
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

  it('persists a versioned run record with inputs, answers, evidence, and deterministic failures without network activity', async () => {
    const artifactDir = await mkdtemp(join(tmpdir(), 'purna-acceptance-'))
    try {
      const written = await writeAcceptanceRun({
        protocol, suite: 'product', environment: 'candidate', environmentConfig: candidateConfig,
        input: { answers: [{
          case_id: 'deterministic_product_case', answer: 'answer retained despite failed evidence', qualitative_score: 1,
          evidence: [{ gate_id: 'receipt_gate', passed: false, receipt_ref: null, detail: 'receipt unavailable' }],
        }] },
        artifactDir, now: new Date('2026-09-17T00:00:00.000Z'), runId: 'run-test',
      })
      const persisted = JSON.parse(await readFile(written.path, 'utf8')) as Record<string, unknown>
      expect(persisted).toMatchObject({
        schema_version: PRODUCT_ACCEPTANCE_RUN_VERSION, run_id: 'run-test', environment: 'candidate',
        revision: 'candidate-revision-123', verdict: 'FAIL_DETERMINISTIC_EVIDENCE', network_calls_made: 0,
      })
      expect(persisted.case_inputs).toHaveLength(1)
      expect(persisted.answers).toHaveLength(1)
      expect(persisted.evidence).toHaveLength(1)
      expect(persisted.failures).toHaveLength(1)
    } finally {
      await rm(artifactDir, { recursive: true, force: true })
    }
  })
})
