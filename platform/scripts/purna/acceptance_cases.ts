import { BEYOND_ACARYA_ACCEPTANCE_CASES, BEYOND_ACARYA_CORPUS_VERSION, type BeyondAcaryaAcceptanceCase } from '../../src/lib/vidhi/inquiry/beyond_acarya_acceptance.corpus'
import type { InquiryResponseAccountability } from '../../src/lib/vidhi/inquiry/types'

export const PRODUCT_ACCEPTANCE_PROTOCOL_VERSION = 'purna-product-acceptance-v2' as const
export const PRODUCT_ACCEPTANCE_RUN_VERSION = 'madhav-purna-anvesana/product-acceptance-run/v1' as const

export type AcceptanceSuite = 'beyond_acarya' | 'product'
export type AcceptanceEnvironment = 'candidate' | 'live'

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

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function validateProtocol(value: unknown): ProductAcceptanceProtocol {
  if (!isObject(value)) throw new Error('PRODUCT_ACCEPTANCE_PROTOCOL_INVALID')
  const protocol = value as unknown as ProductAcceptanceProtocol
  if (protocol.protocol_version !== PRODUCT_ACCEPTANCE_PROTOCOL_VERSION
    || !Array.isArray(protocol.immutable_beyond_acarya?.case_ids)
    || !Array.isArray(protocol.product_scenarios)
    || !Array.isArray(protocol.hard_gates)
    || protocol.run_record?.schema_version !== PRODUCT_ACCEPTANCE_RUN_VERSION) {
    throw new Error('PRODUCT_ACCEPTANCE_PROTOCOL_INVALID')
  }
  const actualCaseIds = BEYOND_ACARYA_ACCEPTANCE_CASES.map((item) => item.case_id)
  if (protocol.immutable_beyond_acarya.corpus_version !== BEYOND_ACARYA_CORPUS_VERSION
    || JSON.stringify(protocol.immutable_beyond_acarya.case_ids) !== JSON.stringify(actualCaseIds)) {
    throw new Error('PRODUCT_ACCEPTANCE_IMMUTABLE_CORPUS_MISMATCH')
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
