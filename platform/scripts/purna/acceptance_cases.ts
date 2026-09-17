import { BEYOND_ACARYA_ACCEPTANCE_CASES, BEYOND_ACARYA_CORPUS_VERSION, type BeyondAcaryaAcceptanceCase } from '../../src/lib/vidhi/inquiry/beyond_acarya_acceptance.corpus'
import type { InquiryResponseAccountability } from '../../src/lib/vidhi/inquiry/types'
import { createHash } from 'node:crypto'

export const PRODUCT_ACCEPTANCE_PROTOCOL_VERSION = 'purna-product-acceptance-v2' as const
export const PRODUCT_ACCEPTANCE_PROTOCOL_SCHEMA_VERSION = 'madhav-purna-anvesana/product-acceptance-protocol/v2' as const
export const PRODUCT_ACCEPTANCE_RUN_VERSION = 'madhav-purna-anvesana/product-acceptance-run/v1' as const

export type AcceptanceSuite = 'beyond_acarya' | 'product'
export type AcceptanceEnvironment = 'candidate' | 'live'

const EXPECTED_PRODUCT_SCENARIOS = [
  {
    scenario_id: 'three_door_semantic_equivalence',
    description: 'Portal, managed MCP, and raw MCP answers have matching normalized inquiry closure and accountability receipts.',
    deterministic_gates: ['inquiry_closure_receipt', 'response_accountability', 'door_parity_projection'],
  },
  {
    scenario_id: 'pagination_truthfulness',
    description: 'First, middle, final, and empty pages retain a truthful exhaustion proof and continuation receipt.',
    deterministic_gates: ['pagination_receipt', 'no_false_total', 'continuation_exhaustion'],
  },
  {
    scenario_id: 'managed_recovery_safety',
    description: 'A recovered managed inquiry returns stored accepted evidence or an explicit blocked state without protected-action replay.',
    deterministic_gates: ['reservation_receipt', 'recovery_state', 'no_replay'],
  },
  {
    scenario_id: 'availability_fail_closed',
    description: 'Dark or changed availability cannot be represented as a complete answer.',
    deterministic_gates: ['capability_overlay', 'availability_contract', 'incomplete_or_blocked'],
  },
] as const satisfies readonly ProductAcceptanceScenario[]

const EXPECTED_HARD_GATES = [
  'explicit_suite_and_environment',
  'approved_non_secret_environment_configuration',
  'https_url_and_revision_for_each_arm',
  'case_input_and_evidence_receipt_retention',
  'deterministic_evidence_failure_overrides_qualitative_score',
  'fixtures_are_never_live_evidence',
] as const

const EXPECTED_RUN_RECORD_FIELDS = [
  'protocol_version', 'suite', 'environment', 'revision', 'case_inputs', 'evidence', 'answers',
  'case_verdicts', 'failures', 'verdict',
] as const

export interface ProductAcceptanceScenario {
  readonly scenario_id: string
  readonly description: string
  readonly deterministic_gates: readonly string[]
}

export interface ProductAcceptanceProtocol {
  readonly schema_version: string
  readonly protocol_version: string
  readonly immutable_beyond_acarya: {
    readonly corpus_version: string
    readonly case_ids: readonly string[]
    readonly case_content_fingerprint: {
      readonly algorithm: 'sha256'
      readonly value: string
    }
  }
  readonly product_scenarios: readonly ProductAcceptanceScenario[]
  readonly hard_gates: readonly string[]
  readonly run_record: { readonly schema_version: string; readonly required_fields: readonly string[] }
}

export interface AcceptanceCaseInput {
  readonly case_id: string
  readonly kind: 'beyond_acarya' | 'product'
  readonly question: string | null
  readonly scope_tuple: BeyondAcaryaAcceptanceCase['scope_tuple'] | null
  readonly deterministic_gates: readonly string[]
}

export interface DeterministicEvidence {
  readonly gate_id: string
  readonly passed: boolean
  readonly receipt_ref: string | null
  readonly detail?: string
}

export interface AcceptanceAnswer {
  readonly case_id: string
  readonly answer: string | null
  readonly evidence: readonly DeterministicEvidence[]
  /** Optional qualitative input; it cannot override deterministic gate failure. */
  readonly qualitative_score?: number | null
  /** Reuses the governed response-accountability shape when supplied by a real run. */
  readonly response_accountability?: InquiryResponseAccountability | null
}

export interface ApprovedEnvironmentConfig {
  readonly schema_version: 'purna-product-acceptance-environment/v1'
  readonly environment: AcceptanceEnvironment
  readonly base_url: string
  readonly revision: string
  readonly authorization: {
    readonly mode: 'approved_non_secret'
    readonly approval_id: string
  }
  /** A fixture may support deterministic tests but is never live/candidate evidence. */
  readonly evidence_mode: 'candidate_or_live' | 'fixture'
}

function immutableCaseContentFingerprint(): string {
  return createHash('sha256').update(JSON.stringify(BEYOND_ACARYA_ACCEPTANCE_CASES)).digest('hex')
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function validateProtocol(value: unknown): ProductAcceptanceProtocol {
  if (!isObject(value)) throw new Error('PRODUCT_ACCEPTANCE_PROTOCOL_INVALID')
  const protocol = value as unknown as ProductAcceptanceProtocol
  if (protocol.schema_version !== PRODUCT_ACCEPTANCE_PROTOCOL_SCHEMA_VERSION
    || protocol.protocol_version !== PRODUCT_ACCEPTANCE_PROTOCOL_VERSION
    || !Array.isArray(protocol.immutable_beyond_acarya?.case_ids)
    || !Array.isArray(protocol.product_scenarios)
    || !Array.isArray(protocol.hard_gates)
    || protocol.run_record?.schema_version !== PRODUCT_ACCEPTANCE_RUN_VERSION
    || !Array.isArray(protocol.run_record?.required_fields)) {
    throw new Error('PRODUCT_ACCEPTANCE_PROTOCOL_INVALID')
  }
  const actualCaseIds = BEYOND_ACARYA_ACCEPTANCE_CASES.map((item) => item.case_id)
  if (protocol.immutable_beyond_acarya.corpus_version !== BEYOND_ACARYA_CORPUS_VERSION
    || JSON.stringify(protocol.immutable_beyond_acarya.case_ids) !== JSON.stringify(actualCaseIds)
    || !isObject(protocol.immutable_beyond_acarya.case_content_fingerprint)
    || protocol.immutable_beyond_acarya.case_content_fingerprint.algorithm !== 'sha256'
    || protocol.immutable_beyond_acarya.case_content_fingerprint.value !== immutableCaseContentFingerprint()) {
    throw new Error('PRODUCT_ACCEPTANCE_IMMUTABLE_CORPUS_MISMATCH')
  }
  if (JSON.stringify(protocol.product_scenarios) !== JSON.stringify(EXPECTED_PRODUCT_SCENARIOS)
    || JSON.stringify(protocol.hard_gates) !== JSON.stringify(EXPECTED_HARD_GATES)
    || JSON.stringify(protocol.run_record.required_fields) !== JSON.stringify(EXPECTED_RUN_RECORD_FIELDS)) {
    throw new Error('PRODUCT_ACCEPTANCE_PROTOCOL_CONTENT_MISMATCH')
  }
  return protocol
}

export function casesForSuite(protocol: ProductAcceptanceProtocol, suite: AcceptanceSuite): readonly AcceptanceCaseInput[] {
  if (suite === 'beyond_acarya') {
    return BEYOND_ACARYA_ACCEPTANCE_CASES.map((item) => ({
      case_id: item.case_id,
      kind: 'beyond_acarya' as const,
      question: item.question,
      scope_tuple: item.scope_tuple,
      deterministic_gates: ['immutable_case_input', 'source_acceptance_denominator'],
    }))
  }
  return protocol.product_scenarios.map((scenario) => ({
    case_id: scenario.scenario_id,
    kind: 'product' as const,
    question: null,
    scope_tuple: null,
    deterministic_gates: scenario.deterministic_gates,
  }))
}

export function validateEnvironmentConfig(value: unknown, environment: AcceptanceEnvironment): ApprovedEnvironmentConfig {
  if (!isObject(value)) throw new Error('PRODUCT_ACCEPTANCE_ENV_CONFIG_INVALID')
  const config = value as unknown as ApprovedEnvironmentConfig
  if (config.schema_version !== 'purna-product-acceptance-environment/v1'
    || config.environment !== environment
    || typeof config.revision !== 'string' || config.revision.trim().length < 7
    || !isObject(config.authorization)
    || config.authorization.mode !== 'approved_non_secret'
    || typeof config.authorization.approval_id !== 'string' || config.authorization.approval_id.trim().length === 0
    || (config.evidence_mode !== 'candidate_or_live' && config.evidence_mode !== 'fixture')) {
    throw new Error('PRODUCT_ACCEPTANCE_ENV_CONFIG_INVALID')
  }
  let url: URL
  try { url = new URL(config.base_url) } catch { throw new Error('PRODUCT_ACCEPTANCE_ENV_URL_INVALID') }
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('PRODUCT_ACCEPTANCE_ENV_URL_INVALID')
  }
  if (environment === 'live' && config.evidence_mode === 'fixture') throw new Error('PRODUCT_ACCEPTANCE_FIXTURE_NOT_LIVE_EVIDENCE')
  return config
}

/** Reject untrusted JSON before the scorer can collapse it into Maps. */
export function validateAcceptanceAnswers(
  value: unknown,
  inputs: readonly AcceptanceCaseInput[],
): readonly AcceptanceAnswer[] {
  if (!Array.isArray(value)) throw new Error('PRODUCT_ACCEPTANCE_INPUT_INVALID')
  const gatesByCase = new Map(inputs.map((input) => [input.case_id, new Set(input.deterministic_gates)]))
  const seenCases = new Set<string>()
  return value.map((candidate): AcceptanceAnswer => {
    if (!isObject(candidate)
      || typeof candidate.case_id !== 'string'
      || (candidate.answer !== null && typeof candidate.answer !== 'string')
      || !Array.isArray(candidate.evidence)
      || (candidate.qualitative_score !== undefined
        && candidate.qualitative_score !== null
        && (typeof candidate.qualitative_score !== 'number'
          || !Number.isFinite(candidate.qualitative_score)
          || candidate.qualitative_score < 0
          || candidate.qualitative_score > 1))
      || (candidate.response_accountability !== undefined
        && candidate.response_accountability !== null
        && !isObject(candidate.response_accountability))) {
      throw new Error('PRODUCT_ACCEPTANCE_INPUT_INVALID')
    }
    if (!gatesByCase.has(candidate.case_id)) throw new Error('PRODUCT_ACCEPTANCE_UNKNOWN_ANSWER_ID')
    if (seenCases.has(candidate.case_id)) throw new Error('PRODUCT_ACCEPTANCE_DUPLICATE_ANSWER_ID')
    seenCases.add(candidate.case_id)
    const allowedGates = gatesByCase.get(candidate.case_id)!
    const seenGates = new Set<string>()
    const evidence = candidate.evidence.map((item): DeterministicEvidence => {
      if (!isObject(item)
        || typeof item.gate_id !== 'string'
        || typeof item.passed !== 'boolean'
        || (item.receipt_ref !== null && typeof item.receipt_ref !== 'string')
        || (item.detail !== undefined && typeof item.detail !== 'string')) {
        throw new Error('PRODUCT_ACCEPTANCE_INPUT_INVALID')
      }
      if (!allowedGates.has(item.gate_id)) throw new Error('PRODUCT_ACCEPTANCE_UNKNOWN_GATE_ID')
      if (seenGates.has(item.gate_id)) throw new Error('PRODUCT_ACCEPTANCE_DUPLICATE_GATE_ID')
      seenGates.add(item.gate_id)
      return {
        gate_id: item.gate_id,
        passed: item.passed,
        receipt_ref: item.receipt_ref,
        ...(item.detail === undefined ? {} : { detail: item.detail }),
      }
    })
    return {
      case_id: candidate.case_id,
      answer: candidate.answer as string | null,
      evidence,
      ...(candidate.qualitative_score === undefined ? {} : { qualitative_score: candidate.qualitative_score as number | null }),
      ...(candidate.response_accountability === undefined
        ? {}
        : { response_accountability: candidate.response_accountability as InquiryResponseAccountability | null }),
    }
  })
}
