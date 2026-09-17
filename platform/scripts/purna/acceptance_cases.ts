import { BEYOND_ACARYA_ACCEPTANCE_CASES, BEYOND_ACARYA_CORPUS_VERSION, type BeyondAcaryaAcceptanceCase } from '../../src/lib/vidhi/inquiry/beyond_acarya_acceptance.corpus'
import type { InquiryResponseAccountability } from '../../src/lib/vidhi/inquiry/types'
import { stableFingerprint } from '../../src/lib/retrieval/registry/knowledge/stable'
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

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
}

function isStringArray(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every(isString)
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0
}

function hasOnlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  return Object.keys(value).every((key) => keys.includes(key))
}

const obligationDispositions = new Set(['pending', 'served', 'empty', 'dark', 'failed', 'not_applicable'])
const factDispositions = new Set([...obligationDispositions, 'open', 'absorbed', 'capped'])
const deliveryKinds = new Set([
  'prose', 'structured_findings', 'finding_interpretation', 'conjoint_interpretation', 'permitted_exclusion',
])
const SHA256_FINGERPRINT = /^sha256:[a-f0-9]{64}$/

function uniqueSorted(values: readonly string[]): string[] {
  return [...new Set(values)].sort()
}

function isCanonicalStringSet(value: readonly string[]): boolean {
  return JSON.stringify(value) === JSON.stringify(uniqueSorted(value))
}

function sameStrings(actual: readonly string[], expected: readonly string[]): boolean {
  return JSON.stringify(actual) === JSON.stringify(expected)
}

function evidenceHashFromRef(ref: string): string | null {
  const match = ref.match(/sha256:[a-f0-9]{64}$/)
  return match?.[0] ?? null
}

function deliveryContentHash(
  factsById: ReadonlyMap<string, Record<string, unknown>>,
  part: Record<string, unknown>,
): string {
  const factIds = part.fact_ids as readonly string[]
  return stableFingerprint({
    kind: part.kind,
    facts: uniqueSorted(factIds).map((factId) => factsById.get(factId) ?? { fact_id: factId, unresolved: true }),
    evidence_payload_hashes: uniqueSorted(part.evidence_payload_hashes as readonly string[]),
    content: part.content,
    exclusion_reason: part.exclusion_reason,
  })
}

function isRegisteredFact(value: unknown): boolean {
  if (!isObject(value) || !isString(value.fact_id)
    || !hasOnlyKeys(value, ['fact_id', 'kind', 'obligation_ids', 'obligation_id', 'frontier_id', 'materiality', 'meaning', 'evidence_refs', 'normalized_content'])
    || !['obligation', 'frontier', 'finding'].includes(value.kind as string)
    || !isStringArray(value.obligation_ids)
    || (value.obligation_id !== null && !isString(value.obligation_id))
    || (value.frontier_id !== null && !isString(value.frontier_id))
    || !['required', 'supporting'].includes(value.materiality as string)
    || !isObject(value.meaning)
    || !hasOnlyKeys(value.meaning, ['label', 'rationale', 'scu_ids', 'disposition'])
    || !isString(value.meaning.label)
    || !isString(value.meaning.rationale)
    || !isStringArray(value.meaning.scu_ids)
    || !factDispositions.has(value.meaning.disposition as string)
    || !isStringArray(value.evidence_refs)
    || (value.normalized_content !== null && typeof value.normalized_content !== 'string')) return false
  return true
}

function isDeliveryPart(value: unknown): boolean {
  return isObject(value)
    && hasOnlyKeys(value, ['part_id', 'kind', 'content_hash', 'content', 'fact_ids', 'evidence_payload_hashes', 'exclusion_reason'])
    && isString(value.part_id)
    && deliveryKinds.has(value.kind as string)
    && isString(value.content_hash)
    && (value.content === null || typeof value.content === 'string')
    && isStringArray(value.fact_ids)
    && isStringArray(value.evidence_payload_hashes)
    && (value.exclusion_reason === null || typeof value.exclusion_reason === 'string')
}

/** Verifies a supplied envelope's complete typed structure and internal receipt projections. */
export function validateResponseAccountability(value: unknown, answer: string | null): InquiryResponseAccountability {
  if (!isObject(value)
    || !hasOnlyKeys(value, ['accountability_version', 'fact_register', 'delivery_parts', 'response_coverage_receipt'])
    || value.accountability_version !== 'inquiry-response-accountability-v1'
    || !isObject(value.fact_register)
    || !Array.isArray(value.delivery_parts)
    || !isObject(value.response_coverage_receipt)) {
    throw new Error('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
  }
  const register = value.fact_register
  const coverage = value.response_coverage_receipt
  if (!hasOnlyKeys(register, ['register_version', 'contract_id', 'semantic_contract_hash', 'facts', 'required_fact_ids', 'validation_errors', 'register_hash'])
    || register.register_version !== 'inquiry-fact-register-v1'
    || !isString(register.contract_id)
    || !isString(register.semantic_contract_hash)
    || !Array.isArray(register.facts) || !register.facts.every(isRegisteredFact)
    || !isStringArray(register.required_fact_ids)
    || !isStringArray(register.validation_errors)
    || !isString(register.register_hash)
    || value.delivery_parts.length === 0
    || !value.delivery_parts.every(isDeliveryPart)
    || coverage.receipt_version !== 'inquiry-response-coverage-v1'
    || coverage.contract_id !== register.contract_id
    || coverage.semantic_contract_hash !== register.semantic_contract_hash
    || coverage.fact_register_hash !== register.register_hash
    || !hasOnlyKeys(coverage, [
      'receipt_version', 'contract_id', 'semantic_contract_hash', 'fact_register_hash', 'status', 'coverage',
      'delivered_fact_ids', 'permitted_exclusion_fact_ids', 'missing_fact_ids', 'missing_required_fact_ids',
      'interpretation_unmapped_fact_ids', 'delivery_part_ids', 'invalid_delivery_claims', 'continuation',
      'resume_required', 'receipt_hash',
    ])
    || !['COMPLETE', 'INCOMPLETE_RESUMABLE', 'BLOCKED'].includes(coverage.status as string)
    || !isObject(coverage.coverage)
    || !hasOnlyKeys(coverage.coverage, [
      'synthesis_present', 'all_total', 'all_delivered', 'all_permitted_exclusions', 'required_total',
      'required_delivered', 'interpretation_mapped',
    ])
    || typeof coverage.coverage.synthesis_present !== 'boolean'
    || !['all_total', 'all_delivered', 'all_permitted_exclusions', 'required_total', 'required_delivered', 'interpretation_mapped']
      .every((key) => isNonNegativeInteger(coverage.coverage[key]))
    || !isStringArray(coverage.delivered_fact_ids)
    || !isStringArray(coverage.permitted_exclusion_fact_ids)
    || !isStringArray(coverage.missing_fact_ids)
    || !isStringArray(coverage.missing_required_fact_ids)
    || !isStringArray(coverage.interpretation_unmapped_fact_ids)
    || !isStringArray(coverage.delivery_part_ids)
    || !isStringArray(coverage.invalid_delivery_claims)
    || !isObject(coverage.continuation)
    || !hasOnlyKeys(coverage.continuation, [
      'iteration', 'max_iterations', 'exhausted', 'next_action_ids', 'blocked_item_ids',
      'unresolved_obligation_ids', 'frontier_ids',
    ])
    || !isNonNegativeInteger(coverage.continuation.iteration)
    || !isNonNegativeInteger(coverage.continuation.max_iterations)
    || typeof coverage.continuation.exhausted !== 'boolean'
    || !isStringArray(coverage.continuation.next_action_ids)
    || !isStringArray(coverage.continuation.blocked_item_ids)
    || !isStringArray(coverage.continuation.unresolved_obligation_ids)
    || !isStringArray(coverage.continuation.frontier_ids)
    || typeof coverage.resume_required !== 'boolean'
    || !isString(coverage.receipt_hash)) {
    throw new Error('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
  }
  const facts = register.facts as Record<string, unknown>[]
  const parts = value.delivery_parts as Record<string, unknown>[]
  const factIds = new Set(facts.map((fact) => fact.fact_id as string))
  const factsById = new Map(facts.map((fact) => [fact.fact_id as string, fact]))
  const partIds = new Set(parts.map((part) => part.part_id as string))
  const { register_hash: registerHash, ...registerProjection } = register
  const { receipt_hash: receiptHash, ...coverageProjection } = coverage
  const delivered = new Set<string>()
  const excluded = new Set<string>()
  const interpretationMapped = new Set<string>()
  let synthesisPresent = false
  let invalidDelivery = coverage.invalid_delivery_claims.length > 0
  for (const part of parts) {
    const partFactIds = part.fact_ids as readonly string[]
    const evidenceHashes = part.evidence_payload_hashes as readonly string[]
    if (!isCanonicalStringSet(partFactIds) || !isCanonicalStringSet(evidenceHashes)
      || !SHA256_FINGERPRINT.test(part.content_hash as string)
      || evidenceHashes.some((hash) => !SHA256_FINGERPRINT.test(hash))) {
      invalidDelivery = true
      continue
    }
    const kind = part.kind as string
    if (kind === 'prose') {
      if (!answer?.trim()
        || part.content !== null
        || partFactIds.length > 0
        || evidenceHashes.length > 0
        || part.exclusion_reason !== null
        || part.content_hash !== stableFingerprint(answer)) invalidDelivery = true
      else synthesisPresent = true
      continue
    }
    if (part.content_hash !== deliveryContentHash(factsById, part)) {
      invalidDelivery = true
      continue
    }
    for (const factId of partFactIds) {
      const fact = factsById.get(factId)
      if (!fact) {
        invalidDelivery = true
        continue
      }
      if (kind === 'permitted_exclusion') {
        if (fact.materiality !== 'supporting' || !isString(part.exclusion_reason) || delivered.has(factId)) invalidDelivery = true
        else excluded.add(factId)
        continue
      }
      if (kind === 'finding_interpretation' || kind === 'conjoint_interpretation') {
        if (fact.kind !== 'finding'
          || !isString(fact.normalized_content)
          || !isString(part.content)
          || !answer?.includes(part.content)
          || !part.content.includes(fact.normalized_content)
          || (kind === 'finding_interpretation' && partFactIds.length !== 1)
          || (kind === 'conjoint_interpretation' && partFactIds.length < 2)) invalidDelivery = true
        else interpretationMapped.add(factId)
        continue
      }
      const expectedEvidenceHashes = (fact.evidence_refs as readonly string[])
        .map(evidenceHashFromRef)
        .filter((hash): hash is string => hash !== null)
      const disposition = (fact.meaning as Record<string, unknown>).disposition as string
      if (delivered.has(factId)
        || excluded.has(factId)
        || (fact.kind === 'obligation'
          && ['served', 'empty'].includes(disposition)
          && ((fact.evidence_refs as readonly string[]).length !== expectedEvidenceHashes.length
            || expectedEvidenceHashes.some((hash) => !evidenceHashes.includes(hash))))) {
        invalidDelivery = true
      } else delivered.add(factId)
    }
  }
  const allFactIds = facts.map((fact) => fact.fact_id as string)
  const requiredFactIds = facts.filter((fact) => fact.materiality === 'required').map((fact) => fact.fact_id as string)
  const missingFactIds = allFactIds.filter((factId) => !delivered.has(factId) && !excluded.has(factId))
  const missingRequiredFactIds = requiredFactIds.filter((factId) => !delivered.has(factId))
  const interpretationUnmappedFactIds = facts
    .filter((fact) => fact.kind === 'finding' && delivered.has(fact.fact_id as string) && !interpretationMapped.has(fact.fact_id as string))
    .map((fact) => fact.fact_id as string)
  const canComplete = synthesisPresent
    && !invalidDelivery
    && missingFactIds.length === 0
    && missingRequiredFactIds.length === 0
    && interpretationUnmappedFactIds.length === 0
    && coverage.continuation.exhausted === false
    && coverage.continuation.next_action_ids.length === 0
    && coverage.continuation.blocked_item_ids.length === 0
    && coverage.continuation.unresolved_obligation_ids.length === 0
    && coverage.continuation.frontier_ids.length === 0
  const expectedStatus = canComplete ? 'COMPLETE'
    : coverage.continuation.exhausted ? 'BLOCKED'
      : 'INCOMPLETE_RESUMABLE'
  if (factIds.size !== register.facts.length
    || partIds.size !== value.delivery_parts.length
    || !sameStrings(register.required_fact_ids, requiredFactIds)
    || !isCanonicalStringSet(register.required_fact_ids)
    || !sameStrings(coverage.delivered_fact_ids, uniqueSorted([...delivered]))
    || !sameStrings(coverage.permitted_exclusion_fact_ids, uniqueSorted([...excluded]))
    || !sameStrings(coverage.missing_fact_ids, missingFactIds)
    || !sameStrings(coverage.missing_required_fact_ids, missingRequiredFactIds)
    || !sameStrings(coverage.interpretation_unmapped_fact_ids, uniqueSorted(interpretationUnmappedFactIds))
    || !sameStrings(coverage.delivery_part_ids, uniqueSorted([...partIds]))
    || coverage.coverage.synthesis_present !== synthesisPresent
    || coverage.coverage.all_total !== allFactIds.length
    || coverage.coverage.all_delivered !== delivered.size
    || coverage.coverage.all_permitted_exclusions !== excluded.size
    || coverage.coverage.required_total !== requiredFactIds.length
    || coverage.coverage.required_delivered !== requiredFactIds.filter((factId) => delivered.has(factId)).length
    || coverage.coverage.interpretation_mapped !== interpretationMapped.size
    || coverage.status !== expectedStatus
    || coverage.resume_required !== !canComplete
    || coverage.continuation.iteration > coverage.continuation.max_iterations
    || ![
      coverage.continuation.next_action_ids,
      coverage.continuation.blocked_item_ids,
      coverage.continuation.unresolved_obligation_ids,
      coverage.continuation.frontier_ids,
    ].every(isCanonicalStringSet)
    || invalidDelivery
    || !SHA256_FINGERPRINT.test(register.semantic_contract_hash as string)
    || !SHA256_FINGERPRINT.test(registerHash as string)
    || !SHA256_FINGERPRINT.test(receiptHash as string)
    || registerHash !== stableFingerprint(registerProjection)
    || receiptHash !== stableFingerprint(coverageProjection)) {
    throw new Error('PRODUCT_ACCEPTANCE_RESPONSE_ACCOUNTABILITY_INVALID')
  }
  return value as unknown as InquiryResponseAccountability
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
    const responseAccountability = candidate.response_accountability === undefined || candidate.response_accountability === null
      ? candidate.response_accountability
      : validateResponseAccountability(candidate.response_accountability)
    return {
      case_id: candidate.case_id,
      answer: candidate.answer as string | null,
      evidence,
      ...(candidate.qualitative_score === undefined ? {} : { qualitative_score: candidate.qualitative_score as number | null }),
      ...(responseAccountability === undefined
        ? {}
        : { response_accountability: responseAccountability }),
    }
  })
}
