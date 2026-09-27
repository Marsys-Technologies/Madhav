import { query as defaultQuery } from '@/lib/db/client'
import { compileChartCapabilityOverlay, type ChartCapabilityEvidence } from './overlay'
import { stableFingerprint } from './stable'
import { bindingProofKind, isNonAnswerBinding } from './proof_kind'
import type {
  AvailabilityRequirement,
  BindingAvailabilityContract,
  BindingAvailabilityDisposition,
  CapabilityKnowledgeSnapshot,
  ChartAssetCapabilityReceipt,
  ChartCapabilityOverlay,
  DerivedAvailabilityRequirement,
  ProducerOutputAvailabilityRequirement,
  ProducerOutputClaim,
  ServiceProbeAvailabilityRequirement,
  SnapshotResourceAvailabilityRequirement,
  SourceQueryAvailabilityRequirement,
  SemanticCapabilityBinding,
  SemanticCapabilityUnit,
} from './types'
import {
  getSourceQueryAvailabilityContract,
  sourceQueryAvailabilityContractMatches,
} from './source_query_availability'
import type { SourceQueryAvailabilityContract } from './source_query_availability'
import {
  chartServedGenerationFromRows,
  servedGenerationIdentity,
  servedReceiptColumnsSql,
  servedReceiptJoinsSql,
  type ChartServedGeneration,
} from '../generation/served_generation'

interface ReceiptRow {
  asset_id: string
  chart_id: string | null
  build_id: string | null
  receipt_version: string
  receipt_state: 'proven' | 'unknown'
  output_digest_spec_sha256: string | null
  observed_at: string
  freshness_state: 'fresh' | 'stale' | 'unknown' | null
  unknown_reasons: unknown
  freshness_reasons: unknown
}

export interface OverlayQueryRow extends ReceiptRow {
  // Served-generation classification columns (generation/served_generation.ts). Absent on
  // global receipts and on the anchor row that only carries service-probe evidence.
  partition_key?: string | null
  receipt_build_id?: string | null
  rows_build_id?: string | null
  spec_active?: boolean | null
  receipt_run_state?: string | null
  receipt_asset_present?: boolean | null
  receipt_disposition?: string | null
  service_probe_evidence?: unknown
}

export type OverlayQueryExecutor = (
  sql: string,
  params?: unknown[],
) => Promise<{ rows: OverlayQueryRow[] }>

function reasons(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

function receiptFingerprint(rows: readonly ReceiptRow[]): string {
  return stableFingerprint(rows.map((row) => ({
    asset_id: row.asset_id,
    build_id: row.build_id,
    receipt_version: row.receipt_version,
    receipt_state: row.receipt_state,
    output_digest_spec_sha256: row.output_digest_spec_sha256,
    freshness_state: row.freshness_state,
    observed_at: row.observed_at,
  })))
}

/**
 * A chart-scoped receipt is evidence only when the asset's served generation resolves
 * (generation/served_generation.ts): proven, fresh, active-spec, issued by a completed run,
 * with a provable writing run. The chart's latest completed run is irrelevant — asset runs
 * are frequently single-asset, so it rarely wrote the rows being served.
 */
function chartReceipt(
  assetId: string,
  specSha256: string | null,
  rows: readonly ReceiptRow[],
  generation: ChartServedGeneration,
): ChartAssetCapabilityReceipt | null {
  const chartRows = rows.filter((row) => row.asset_id === assetId && row.chart_id !== null)
  if (!chartRows.length) return null
  const binding = generation.assets[assetId]
  const specMismatch = chartRows.some((row) => row.output_digest_spec_sha256 !== specSha256)
  return {
    asset_id: assetId,
    build_id: binding?.state === 'resolved' ? binding.rows_build_id : chartRows.map((row) => row.build_id).find(Boolean) ?? null,
    writer_version: null,
    output_digest_spec_sha256: specSha256,
    state: specMismatch ? 'failed' : binding?.state === 'resolved' ? 'passed' : 'partial',
    receipt_ref: receiptFingerprint(chartRows),
  }
}

function globalReceipt(assetId: string, specSha256: string | null, rows: readonly ReceiptRow[]): ChartAssetCapabilityReceipt {
  const chosen = rows.filter((row) => row.asset_id === assetId && row.chart_id === null)
  if (!chosen.length) return {
    asset_id: assetId, build_id: null, writer_version: null,
    output_digest_spec_sha256: specSha256, state: 'missing', receipt_ref: null,
  }
  const specMismatch = chosen.some((row) => row.output_digest_spec_sha256 !== specSha256)
  const failed = chosen.some((row) => row.receipt_state !== 'proven' || row.freshness_state !== 'fresh')
  return {
    asset_id: assetId,
    build_id: chosen.map((row) => row.build_id).find(Boolean) ?? null,
    writer_version: null,
    output_digest_spec_sha256: specSha256,
    state: specMismatch ? 'failed' : failed ? 'partial' : 'passed',
    receipt_ref: receiptFingerprint(chosen),
  }
}

function receiptForClaim(
  claim: ProducerOutputClaim,
  rows: readonly ReceiptRow[],
  generation: ChartServedGeneration,
): ChartAssetCapabilityReceipt {
  // Global evidence is a fallback only when this asset has no chart receipt at all.
  return chartReceipt(claim.asset_id, claim.output_digest_spec_sha256, rows, generation)
    ?? globalReceipt(claim.asset_id, claim.output_digest_spec_sha256, rows)
}

function receiptForRequirement(
  requirement: ProducerOutputAvailabilityRequirement,
  rows: readonly ReceiptRow[],
  generation: ChartServedGeneration,
): ChartAssetCapabilityReceipt {
  if (requirement.scope === 'global') return globalReceipt(requirement.asset_id, requirement.spec_sha256, rows)
  return chartReceipt(requirement.asset_id, requirement.spec_sha256, rows, generation) ?? {
    asset_id: requirement.asset_id, build_id: null, writer_version: null,
    output_digest_spec_sha256: requirement.spec_sha256, state: 'missing', receipt_ref: null,
  }
}

function producerOutputRequirement(requirement: unknown): requirement is ProducerOutputAvailabilityRequirement {
  return isRecord(requirement)
    && requirement.kind === 'producer_output'
    && typeof requirement.asset_id === 'string' && requirement.asset_id.length > 0
    && typeof requirement.spec_sha256 === 'string' && /^[a-f0-9]{64}$/.test(requirement.spec_sha256)
    && (requirement.scope === 'chart_build' || requirement.scope === 'global')
    && typeof requirement.source_ref === 'string' && requirement.source_ref.length > 0
}

function serviceProbeRequirement(requirement: unknown): requirement is ServiceProbeAvailabilityRequirement {
  return isRecord(requirement)
    && requirement.kind === 'service_probe'
    && typeof requirement.asset_id === 'string' && requirement.asset_id.length > 0
    && typeof requirement.probe_id === 'string' && /^[a-z][a-z0-9_]{1,127}$/.test(requirement.probe_id)
    && typeof requirement.endpoint_identity === 'string' && /^nirmana-elevation:health-probe:[a-z][a-z0-9_]{1,255}$/.test(requirement.endpoint_identity)
    && typeof requirement.probe_contract_sha256 === 'string' && /^[a-f0-9]{64}$/.test(requirement.probe_contract_sha256)
    && typeof requirement.max_age_seconds === 'number' && Number.isSafeInteger(requirement.max_age_seconds)
    && requirement.max_age_seconds > 0 && requirement.max_age_seconds <= 86_400
    && typeof requirement.source_ref === 'string' && requirement.source_ref.length > 0
}

function sourceQueryRequirement(requirement: unknown): requirement is SourceQueryAvailabilityRequirement {
  return isRecord(requirement)
    && requirement.kind === 'source_query'
    && typeof requirement.contract_id === 'string' && requirement.contract_id.length > 0
    && typeof requirement.capability_uri === 'string' && requirement.capability_uri.length > 0
    && typeof requirement.contract_sha256 === 'string' && /^sha256:[a-f0-9]{64}$/.test(requirement.contract_sha256)
    && (requirement.scope === 'chart' || requirement.scope === 'global')
    && typeof requirement.source_ref === 'string' && requirement.source_ref.length > 0
}

function snapshotResourceRequirement(requirement: unknown): requirement is SnapshotResourceAvailabilityRequirement {
  return isRecord(requirement)
    && requirement.kind === 'snapshot_resource'
    && (requirement.proof === 'registered_in_pinned_snapshot' || requirement.proof === 'index_compiled_from_pinned_catalog')
    && requirement.scope === 'global'
    && typeof requirement.source_ref === 'string' && requirement.source_ref.length > 0
}


function derivedRequirement(requirement: unknown): requirement is DerivedAvailabilityRequirement {
  return isRecord(requirement) && requirement.kind === 'derived'
}

function usableDerivedRequirement(requirement: unknown): requirement is DerivedAvailabilityRequirement {
  return derivedRequirement(requirement)
    && (requirement.scope === 'chart' || requirement.scope === 'global')
    && Array.isArray(requirement.required_binding_ids)
    && requirement.required_binding_ids.length > 0
    && requirement.required_binding_ids.every((bindingId) => typeof bindingId === 'string' && bindingId.length > 0)
    && new Set(requirement.required_binding_ids).size === requirement.required_binding_ids.length
    && typeof requirement.source_ref === 'string' && requirement.source_ref.length > 0
}

function contractForBinding(
  scu: SemanticCapabilityUnit,
  binding: SemanticCapabilityBinding,
): BindingAvailabilityContract | null | undefined {
  const contracts = scu.availability_contracts
  if (contracts === undefined) return undefined
  if (!Array.isArray(contracts)) return null
  const matches = contracts.filter((contract) => isRecord(contract) && contract.binding_id === binding.binding_id)
  if (matches.length !== 1) return matches.length > 1 ? null : undefined
  return Array.isArray(matches[0]?.requirements) ? matches[0] as BindingAvailabilityContract : null
}

type ContractValidationMemo = Map<string, string | null>

interface ContractIntegrityContext {
  readonly bindingMemo: ContractValidationMemo
  readonly scuMemo: Map<string, string | null>
  readonly visitingScuIds: Set<string>
}

function contractIntegrityContext(): ContractIntegrityContext {
  return { bindingMemo: new Map(), scuMemo: new Map(), visitingScuIds: new Set() }
}

function contractValidationKey(scu: SemanticCapabilityUnit, binding: SemanticCapabilityBinding): string {
  return `${scu.scu_id}\u0000${binding.binding_id}`
}

function bindingContractIntegrityGap(
  scu: SemanticCapabilityUnit,
  binding: SemanticCapabilityBinding,
  bindingIndex: ReadonlyMap<string, BindingTarget | null>,
  context: ContractIntegrityContext,
  visiting: Set<string>,
): string | null {
  const key = contractValidationKey(scu, binding)
  if (visiting.has(key)) return 'Derived availability contracts contain a cycle.'
  if (context.bindingMemo.has(key)) return context.bindingMemo.get(key)!
  const contract = contractForBinding(scu, binding)
  if (!contract) return null
  visiting.add(key)
  let gap: string | null = null
  for (const requirement of contract.requirements) {
    if (producerOutputRequirement(requirement)) {
      const reviewedClaim = (scu.producer_output_claims ?? []).some((claim) => claim.disposition === 'reviewed_output'
        && claim.asset_id === requirement.asset_id
        && claim.output_digest_spec_sha256 === requirement.spec_sha256)
      if (!reviewedClaim) {
        gap = 'Producer-output availability requirement has no same-SCU reviewed output claim with the exact asset and SHA-256.'
        break
      }
      continue
    }
    if (sourceQueryRequirement(requirement)) {
      if (scu.scope !== requirement.scope || binding.capability_uri !== requirement.capability_uri
        || !sourceQueryAvailabilityContractMatches(requirement)) {
        gap = 'Source-query availability requirement does not match its registry-owned reviewed query contract.'
        break
      }
      continue
    }
    if (snapshotResourceRequirement(requirement)) {
      if (!isNonAnswerBinding(scu, binding) || contract.requirements.length !== 1) {
        gap = 'A snapshot-resource proof is valid only as the sole proof of a plan, resource or discovery binding.'
        break
      }
      continue
    }
    if (usableDerivedRequirement(requirement)) {
      for (const childBindingId of requirement.required_binding_ids) {
        const childTarget = bindingIndex.get(childBindingId)
        if (!childTarget || childTarget.scu.scope !== requirement.scope || scu.scope !== requirement.scope) {
          gap = `Derived availability leg ${childBindingId} has no scope-compatible executable binding.`
          break
        }
        if (isNonAnswerBinding(childTarget.scu, childTarget.binding)) {
          gap = `Derived availability leg ${childBindingId} is a ${bindingProofKind(childTarget.scu, childTarget.binding)} binding and cannot evidence a composite answer.`
          break
        }
        if (!contractForBinding(childTarget.scu, childTarget.binding)) {
          gap = `Derived availability leg ${childBindingId} has no exact authored availability contract.`
          break
        }
        const childScuGap = childTarget.scu === scu ? null : authoredContractIntegrityGap(childTarget.scu, bindingIndex, context)
        if (childScuGap) {
          gap = `Derived availability leg ${childBindingId}: ${childScuGap}`
          break
        }
        const childGap = bindingContractIntegrityGap(childTarget.scu, childTarget.binding, bindingIndex, context, visiting)
        if (childGap) {
          gap = `Derived availability leg ${childBindingId}: ${childGap}`
          break
        }
      }
      if (gap) break
      continue
    }
    if (!serviceProbeRequirement(requirement)) {
      gap = 'Binding availability contract contains a malformed or unsupported requirement.'
      break
    }
  }
  visiting.delete(key)
  context.bindingMemo.set(key, gap)
  return gap
}

function authoredContractIntegrityGap(
  scu: SemanticCapabilityUnit,
  bindingIndex: ReadonlyMap<string, BindingTarget | null>,
  context: ContractIntegrityContext = contractIntegrityContext(),
): string | null {
  if (context.scuMemo.has(scu.scu_id)) return context.scuMemo.get(scu.scu_id)!
  // A binding-level DFS is responsible for identifying the precise derived cycle.
  // This SCU-level guard only prevents re-entering an in-flight aggregate validation.
  if (context.visitingScuIds.has(scu.scu_id)) return null
  context.visitingScuIds.add(scu.scu_id)
  let gap: string | null = null
  const contracts = scu.availability_contracts
  if (contracts === undefined) {
    context.visitingScuIds.delete(scu.scu_id)
    context.scuMemo.set(scu.scu_id, null)
    return null
  }
  if (!Array.isArray(contracts)
    || contracts.some((contract) => !isRecord(contract)
      || typeof contract.binding_id !== 'string'
      || !Array.isArray(contract.requirements))) {
    gap = 'Malformed binding availability contracts prevent a safe evidence selection.'
  }
  const contractBindingIds = new Set<string>()
  if (!gap) for (const contract of contracts) {
    if (contractBindingIds.has(contract.binding_id)) {
      gap = 'Duplicate binding availability contracts prevent a safe evidence selection.'
      break
    }
    contractBindingIds.add(contract.binding_id)
    if (scu.bindings.filter((binding) => binding.binding_id === contract.binding_id && binding.executable).length !== 1) {
      gap = 'Binding availability contract names an unknown or non-executable local binding.'
      break
    }
    if (contract.requirements.length === 0) {
      gap = 'Binding availability contract has no requirements.'
      break
    }
  }
  if (!gap) for (const contract of contracts) {
    const binding = scu.bindings.find((candidate) => candidate.binding_id === contract.binding_id && candidate.executable)!
    gap = bindingContractIntegrityGap(scu, binding, bindingIndex, context, new Set())
    if (gap) break
  }
  context.visitingScuIds.delete(scu.scu_id)
  context.scuMemo.set(scu.scu_id, gap)
  return gap
}

function hasAuthoredContracts(scu: SemanticCapabilityUnit): boolean {
  return (scu.availability_contracts?.length ?? 0) > 0
}

function deliberateDarkDisposition(
  scu: SemanticCapabilityUnit,
  binding: SemanticCapabilityBinding,
): BindingAvailabilityDisposition | null {
  const matches = scu.availability_dispositions?.filter((disposition) => disposition.binding_id === binding.binding_id) ?? []
  return matches.length === 1 ? matches[0]! : null
}

interface BindingTarget {
  readonly scu: SemanticCapabilityUnit
  readonly binding: SemanticCapabilityBinding
}

function executableBindingIndex(snapshot: CapabilityKnowledgeSnapshot): ReadonlyMap<string, BindingTarget | null> {
  const index = new Map<string, BindingTarget | null>()
  for (const scu of snapshot.scus) for (const binding of scu.bindings) {
    if (!binding.executable) continue
    if (index.has(binding.binding_id)) index.set(binding.binding_id, null)
    else index.set(binding.binding_id, { scu, binding })
  }
  return index
}

function explicitRequirementsForBinding(
  bindingId: string,
  index: ReadonlyMap<string, BindingTarget | null>,
): readonly AvailabilityRequirement[] {
  const target = index.get(bindingId)
  if (!target) return []
  return contractForBinding(target.scu, target.binding)?.requirements ?? []
}

function requirementsForBindingTree(
  bindingId: string,
  index: ReadonlyMap<string, BindingTarget | null>,
  visiting = new Set<string>(),
): readonly AvailabilityRequirement[] {
  if (visiting.has(bindingId)) return []
  visiting.add(bindingId)
  const requirements = explicitRequirementsForBinding(bindingId, index)
  const flattened = requirements.flatMap((requirement) => usableDerivedRequirement(requirement)
    ? requirement.required_binding_ids.flatMap((childBindingId) => requirementsForBindingTree(childBindingId, index, visiting))
    : [requirement])
  visiting.delete(bindingId)
  return flattened
}

function assetIdsForSnapshot(snapshot: CapabilityKnowledgeSnapshot): string[] {
  const index = executableBindingIndex(snapshot)
  return [...new Set(snapshot.scus.flatMap((scu) => scu.bindings.flatMap((binding) => {
    if (authoredContractIntegrityGap(scu, index)) return []
    if (!binding.executable) return []
    const contract = contractForBinding(scu, binding)
    if (contract === null) return []
    if (contract) return requirementsForBindingTree(binding.binding_id, index).filter(producerOutputRequirement).map((requirement) => requirement.asset_id)
    if (hasAuthoredContracts(scu)) return []
    return (scu.producer_output_claims ?? []).filter((claim) => claim.disposition === 'reviewed_output').map((claim) => claim.asset_id)
  })))].sort()
}

function serviceProbeAssetIdsForSnapshot(snapshot: CapabilityKnowledgeSnapshot): string[] {
  const index = executableBindingIndex(snapshot)
  return [...new Set(snapshot.scus.flatMap((scu) => scu.bindings.flatMap((binding) => {
    if (authoredContractIntegrityGap(scu, index)) return []
    if (!binding.executable) return []
    const contract = contractForBinding(scu, binding)
    if (!contract) return []
    return requirementsForBindingTree(binding.binding_id, index).filter(serviceProbeRequirement).map((requirement) => requirement.asset_id)
  })))].sort()
}

interface BindingEvidence {
  readonly binding_id: string
  readonly passed: boolean
  readonly receipts: readonly ChartAssetCapabilityReceipt[]
  readonly gaps: readonly string[]
}

type SourceQueryEvidence = ReadonlyMap<string, readonly string[]>

function sourceQueryEvidenceKey(requirement: SourceQueryAvailabilityRequirement): string {
  return `${requirement.contract_id}\u0000${requirement.contract_sha256}`
}

export async function probeSourceQueryAvailabilityContract(
  contract: SourceQueryAvailabilityContract,
  chartId: string,
  servedBuildIds: readonly string[] | null,
  query: OverlayQueryExecutor,
): Promise<readonly string[]> {
  const served = servedBuildIds?.length ? [...servedBuildIds] : null
  if (contract.parameter_binding === 'chart_and_served_builds' && !served) {
    return [`${contract.contract_id} cannot bind the selected chart to a served chart generation.`]
  }
  if (contract.parameter_binding === 'chart_with_active_build_context' && !served) {
    return [`${contract.contract_id} requires a served chart generation for the selected chart.`]
  }
  const params = contract.parameter_binding === 'global'
    ? []
    : contract.parameter_binding === 'chart_and_served_builds'
      ? [chartId, served]
      // Global addresses such as concept_locate can still make an explicitly
      // documented chart-backed fallback query.  The public capability remains
      // global; the probe deliberately exercises that fallback with the selected
      // chart instead of silently certifying only its in-memory path.
      : [chartId]
  try {
    const result = await query(contract.sql, params)
    // Most reviewed handlers have honest-empty semantics: query success proves
    // source reachability even when no domain rows match. A required-row probe is
    // deliberately different: it encodes mandatory handler prerequisites and must
    // return at least one readiness row before the binding is admitted.
    if (contract.empty_semantics === 'required_rows_must_exist' && result.rows.length === 0) {
      return [`${contract.contract_id} returned no required readiness rows.`]
    }
    return []
  } catch {
    return [`${contract.contract_id} could not execute its authenticated source query.`]
  }
}

async function sourceQueryEvidenceForSnapshot(
  snapshot: CapabilityKnowledgeSnapshot,
  chartId: string,
  servedBuildIds: readonly string[] | null,
  query: OverlayQueryExecutor,
): Promise<SourceQueryEvidence> {
  const requirements = new Map<string, SourceQueryAvailabilityRequirement>()
  for (const scu of snapshot.scus) for (const contract of scu.availability_contracts ?? []) {
    for (const requirement of contract.requirements) if (sourceQueryRequirement(requirement)) {
      requirements.set(sourceQueryEvidenceKey(requirement), requirement)
    }
  }
  const evidence = new Map<string, readonly string[]>()
  await Promise.all([...requirements.entries()].map(async ([key, requirement]) => {
    const contract = getSourceQueryAvailabilityContract(requirement.contract_id)
    if (!contract || !sourceQueryAvailabilityContractMatches(requirement)) {
      evidence.set(key, ['Source-query availability requirement does not match its registry-owned reviewed query contract.'])
      return
    }
    evidence.set(key, await probeSourceQueryAvailabilityContract(contract, chartId, servedBuildIds, query))
  }))
  return evidence
}

function gapsForReceipts(
  receipts: readonly ChartAssetCapabilityReceipt[],
  rows: readonly ReceiptRow[],
  generation: ChartServedGeneration,
): string[] {
  return receipts.flatMap((receipt) => {
    if (receipt.state === 'passed') return []
    const sourceRows = rows.filter((row) => row.asset_id === receipt.asset_id)
    const binding = generation.assets[receipt.asset_id]
    return [
      `${receipt.asset_id} availability is ${receipt.state}.`,
      ...(binding?.state === 'unresolved' ? [`${receipt.asset_id} served generation is unresolved: ${binding.reason}.`] : []),
      ...sourceRows.flatMap((row) => [...reasons(row.unknown_reasons), ...reasons(row.freshness_reasons)]),
    ]
  })
}

interface ServiceProbeEvidenceRow {
  readonly asset_id: string
  readonly source_kind: string
  readonly source_ref: string
  readonly observed_at: string
  readonly evidence_payload: unknown
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function serviceProbeRows(value: unknown): ServiceProbeEvidenceRow[] {
  if (!Array.isArray(value)) return []
  return value.filter((row): row is ServiceProbeEvidenceRow => isRecord(row)
    && typeof row.asset_id === 'string'
    && typeof row.source_kind === 'string'
    && typeof row.source_ref === 'string'
    && typeof row.observed_at === 'string')
}

function serviceProbeGaps(
  requirement: ServiceProbeAvailabilityRequirement,
  rows: readonly ServiceProbeEvidenceRow[],
  now: Date,
): string[] {
  const candidates = rows.filter((row) => row.asset_id === requirement.asset_id)
  if (!candidates.length) return [`${requirement.asset_id} has no authenticated service-probe evidence.`]
  const endpointRows = candidates.filter((row) => row.source_kind === 'server_reconstructed'
    && row.source_ref === requirement.endpoint_identity)
  if (!endpointRows.length) return [`${requirement.asset_id} has no evidence from authenticated probe endpoint ${requirement.endpoint_identity}.`]
  const configuredRows = endpointRows.filter((row) => {
    const payload = isRecord(row.evidence_payload) ? row.evidence_payload : null
    return payload?.probe_contract_sha256 === requirement.probe_contract_sha256
  })
  if (!configuredRows.length) return [`${requirement.asset_id} has no probe evidence for the pinned configuration version.`]
  const successfulRows = configuredRows.filter((row) => {
    const payload = isRecord(row.evidence_payload) ? row.evidence_payload : null
    const observation = payload && isRecord(payload.detector_observation) ? payload.detector_observation : null
    const result = observation && isRecord(observation.result) ? observation.result : null
    const checks = result?.checks
    const requestStarted = observation?.request_started_at
    const requestEnded = observation?.request_ended_at
    const observedAt = Date.parse(row.observed_at)
    const startedAt = typeof requestStarted === 'string' ? Date.parse(requestStarted) : Number.NaN
    const endedAt = typeof requestEnded === 'string' ? Date.parse(requestEnded) : Number.NaN
    return typeof payload?.registry_fingerprint_sha256 === 'string' && /^[a-f0-9]{64}$/.test(payload.registry_fingerprint_sha256)
      && typeof payload?.analysis_digest === 'string' && /^[a-f0-9]{64}$/.test(payload.analysis_digest)
      && typeof payload?.response_digest === 'string' && /^[a-f0-9]{64}$/.test(payload.response_digest)
      && observation?.probe_type === requirement.probe_id
      && typeof observation?.runner_revision === 'string' && observation.runner_revision.length > 0
      && result?.status === 'GREEN'
      && Array.isArray(checks) && checks.length > 0
      && checks.every((check) => isRecord(check) && check.passed === true)
      && Number.isFinite(observedAt) && Number.isFinite(startedAt) && Number.isFinite(endedAt)
      && startedAt <= observedAt && observedAt <= endedAt
  })
  if (!successfulRows.length) return [`${requirement.asset_id} probe evidence is malformed or did not record a successful authenticated probe.`]
  const freshRows = successfulRows.filter((row) => {
    const observedAt = Date.parse(row.observed_at)
    const ageMs = now.getTime() - observedAt
    return ageMs >= 0 && ageMs <= requirement.max_age_seconds * 1_000
  })
  return freshRows.length ? [] : [`${requirement.asset_id} authenticated probe evidence is stale or has an invalid observation time.`]
}

function evidenceForBinding(
  scu: SemanticCapabilityUnit,
  binding: SemanticCapabilityBinding,
  rows: readonly ReceiptRow[],
  generation: ChartServedGeneration,
  probeRows: readonly ServiceProbeEvidenceRow[],
  sourceQueryEvidence: SourceQueryEvidence,
  now: Date,
  bindingIndex: ReadonlyMap<string, BindingTarget | null>,
  visiting = new Set<string>(),
  requireExplicitContract = false,
): BindingEvidence {
  const contractIntegrityGap = bindingContractIntegrityGap(scu, binding, bindingIndex, contractIntegrityContext(), new Set())
  if (contractIntegrityGap) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: [contractIntegrityGap],
  }
  if (bindingIndex.has(binding.binding_id) && bindingIndex.get(binding.binding_id) === null) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: ['Duplicate executable binding ID prevents a safe availability selection.'],
  }
  if (visiting.has(binding.binding_id)) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: ['Derived availability contracts contain a cycle.'],
  }
  const nextVisiting = new Set(visiting)
  nextVisiting.add(binding.binding_id)
  const contract = contractForBinding(scu, binding)
  if (contract === null) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: ['Duplicate binding availability contracts prevent a safe evidence selection.'],
  }
  // R3 boundary ("genuine per-mode proof typing"): a binding's own deliberately-dark
  // disposition must be recognized BEFORE the "SCU has authored contracts elsewhere, so every
  // binding must have one too" gate below — otherwise a sibling binding's contract (e.g.
  // sav_bav_gating's) makes THIS binding's honest disposition (e.g. kakshya_windows') look
  // like an unreviewed omission instead of the disclosed, reviewed gap it actually is.
  const deliberatelyDarkEarly = !contract ? deliberateDarkDisposition(scu, binding) : null
  if (deliberatelyDarkEarly) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: [`Binding is deliberately dark: ${deliberatelyDarkEarly.reason}`],
  }
  if ((hasAuthoredContracts(scu) || requireExplicitContract) && !contract) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: ['Binding has no authored availability contract.'],
  }
  if (contract) {
    const producerRequirements = contract.requirements.filter(producerOutputRequirement)
    const serviceRequirements = contract.requirements.filter(serviceProbeRequirement)
    const sourceQueryRequirements = contract.requirements.filter(sourceQueryRequirement)
    const derivedRequirements = contract.requirements.filter(usableDerivedRequirement)
    const snapshotResourceRequirements = contract.requirements.filter(snapshotResourceRequirement)
    // The snapshot proof is valid only as the sole proof of a non-answer BINDING, and never as
    // a derived leg of an answer composite (the snapshot compiler rejects both). Scoped to
    // this binding, not the whole SCU, so a plan/resource/discovery mode can live on an
    // otherwise chart-scoped SCU (e.g. synergy_pipeline's dry_run leg).
    const snapshotResourceGaps = snapshotResourceRequirements.length === 0 ? [] : [
      ...(!isNonAnswerBinding(scu, binding) || contract.requirements.length !== 1 || requireExplicitContract
        ? ['A snapshot-resource proof is valid only as the sole proof of a plan, resource or discovery binding.'] : []),
      ...(bindingIndex.get(binding.binding_id)?.binding !== binding
        ? ['Binding is not uniquely registered and executable in the pinned snapshot.'] : []),
    ]
    const unsupported = contract.requirements.filter((requirement) => !producerOutputRequirement(requirement)
      && !serviceProbeRequirement(requirement) && !sourceQueryRequirement(requirement) && !usableDerivedRequirement(requirement)
      && !snapshotResourceRequirement(requirement))
    const receipts = producerRequirements.map((requirement) => receiptForRequirement(requirement, rows, generation))
    const derivedEvidence = derivedRequirements.flatMap((requirement) => requirement.required_binding_ids.map((bindingId) => {
      const target = bindingIndex.get(bindingId)
      if (!target || target.scu.scope !== requirement.scope || scu.scope !== requirement.scope) return {
        binding_id: bindingId,
        passed: false,
        receipts: [],
        gaps: [`Derived availability leg ${bindingId} has no scope-compatible executable binding.`],
      } satisfies BindingEvidence
      return evidenceForBinding(
        target.scu, target.binding, rows, generation, probeRows, sourceQueryEvidence, now, bindingIndex, nextVisiting, true,
      )
    }))
    const derivedGaps = derivedEvidence.flatMap((evidence) => evidence.gaps.map((gap) =>
      `Derived availability leg ${evidence.binding_id}: ${gap}`,
    ))
    const gaps = [
      ...(contract.requirements.length === 0 ? ['Binding availability contract has no requirements.'] : []),
      ...unsupported.map(() => 'Binding availability contract contains a malformed or unsupported requirement.'),
      ...gapsForReceipts(receipts, rows, generation),
      ...serviceRequirements.flatMap((requirement) => serviceProbeGaps(requirement, probeRows, now)),
      ...sourceQueryRequirements.flatMap((requirement) => sourceQueryEvidence.get(sourceQueryEvidenceKey(requirement))
        ?? ['Source-query availability evidence was not evaluated.']),
      ...derivedGaps,
      ...snapshotResourceGaps,
    ]
    return {
      binding_id: binding.binding_id,
      passed: contract.requirements.length > 0 && !unsupported.length && snapshotResourceGaps.length === 0
        && receipts.every((receipt) => receipt.state === 'passed')
        && serviceRequirements.every((requirement) => serviceProbeGaps(requirement, probeRows, now).length === 0)
        && sourceQueryRequirements.every((requirement) => sourceQueryEvidence.get(sourceQueryEvidenceKey(requirement))?.length === 0)
        && derivedEvidence.every((evidence) => evidence.passed),
      receipts: [...receipts, ...derivedEvidence.flatMap((evidence) => evidence.receipts)],
      gaps,
    }
  }

  const deliberatelyDark = deliberateDarkDisposition(scu, binding)
  if (deliberatelyDark) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: [`Binding is deliberately dark: ${deliberatelyDark.reason}`],
  }

  const claims = scu.producer_output_claims ?? []
  if (binding.relation !== 'primary') return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: ['Legacy availability fallback is limited to the primary executable binding.'],
  }
  const reviewed = claims.filter((claim) => claim.disposition === 'reviewed_output' && /^[a-f0-9]{64}$/.test(claim.output_digest_spec_sha256 ?? ''))
  const receipts = reviewed.map((claim) => receiptForClaim(claim, rows, generation))
  const unsupported = claims.filter((claim) => !reviewed.includes(claim))
  return {
    binding_id: binding.binding_id,
    passed: claims.length > 0 && !unsupported.length && receipts.every((receipt) => receipt.state === 'passed'),
    receipts,
    gaps: [
      ...unsupported.map((claim) => claim.gap_reason ?? `${claim.asset_id} has no reviewed output claim.`),
      ...gapsForReceipts(receipts, rows, generation),
    ],
  }
}

function evidenceForSnapshot(
  snapshot: CapabilityKnowledgeSnapshot,
  rows: readonly ReceiptRow[],
  generation: ChartServedGeneration,
  build: { build_id: string | null; status: string | null },
  probeRows: readonly ServiceProbeEvidenceRow[],
  sourceQueryEvidence: SourceQueryEvidence,
  now: Date,
): ChartCapabilityEvidence[] {
  const bindingIndex = executableBindingIndex(snapshot)
  return snapshot.scus.map((scu) => {
    const contractIntegrityGap = authoredContractIntegrityGap(scu, bindingIndex)
    if (contractIntegrityGap) return {
      scu_id: scu.scu_id,
      build_status: build.status,
      build_id: build.build_id,
      freshness: null,
      available_binding_ids: [],
      state: 'dark' as const,
      gaps: [contractIntegrityGap],
      asset_receipts: [],
    }
    const executableBindings = scu.bindings.filter((binding) => binding.executable)
    const bindingEvidence = executableBindings.map((binding) => ({
      binding,
      evidence: evidenceForBinding(scu, binding, rows, generation, probeRows, sourceQueryEvidence, now, bindingIndex),
    }))
    // R3 boundary ("genuine per-mode proof typing"): TWO independent partitions, not one.
    //
    // 1. Mandatory (no `mode_selector`) vs optional mode (`mode_selector` present) — an
    //    optional mode is an ALTERNATE way to use this capability (e.g. get_av_transit_gating's
    //    kakshya_windows, selected only by `mode: 'kakshya_windows'`); its own unavailability
    //    must never affect whether the SCU's mandatory/default binding(s) read as 'available'.
    //    A non-modal SCU (100% of the pre-existing estate) has zero optional-mode bindings, so
    //    its state is computed exactly as before this type existed.
    // 2. Answer vs non-answer (RC-7) — a plan/resource/discovery binding is never admitted as
    //    answer evidence, whether it is mandatory or an optional mode.
    const mandatory = bindingEvidence.filter(({ binding }) => (binding.mode_selector?.length ?? 0) === 0)
    const optionalModes = bindingEvidence.filter(({ binding }) => (binding.mode_selector?.length ?? 0) > 0)
    const mandatoryAnswer = mandatory.filter(({ binding }) => !isNonAnswerBinding(scu, binding))
    const mandatoryNonAnswer = mandatory.filter(({ binding }) => isNonAnswerBinding(scu, binding))
    const optionalAnswer = optionalModes.filter(({ binding }) => !isNonAnswerBinding(scu, binding))
    const optionalNonAnswer = optionalModes.filter(({ binding }) => isNonAnswerBinding(scu, binding))

    // available_binding_ids lists every PASSED answer binding — mandatory or optional mode —
    // since a caller that specifically requested an available optional mode must still be able
    // to find it here; a non-answer binding is never added, whether it passed or not.
    const availableBindingIds = [...mandatoryAnswer, ...optionalAnswer]
      .filter(({ evidence }) => evidence.passed)
      .map(({ evidence }) => evidence.binding_id)
    const assetReceipts = mandatoryAnswer.flatMap(({ evidence }) => evidence.receipts)
    const mandatoryAnswerGaps = mandatoryAnswer.flatMap(({ evidence }) => evidence.gaps)
    // Diagnostic-only: an optional mode's or a non-answer binding's own gaps are reported for
    // visibility, but — critically — never folded into mandatoryAnswerGaps, so they can never
    // move `state` away from 'available'.
    const diagnosticGaps = [
      ...mandatoryNonAnswer.filter(({ evidence }) => !evidence.passed)
        .flatMap(({ evidence }) => evidence.gaps.map((gap) => `${evidence.binding_id} (non-answer): ${gap}`)),
      ...optionalAnswer.filter(({ evidence }) => !evidence.passed)
        .flatMap(({ evidence }) => evidence.gaps.map((gap) => `${evidence.binding_id} (optional mode): ${gap}`)),
      ...optionalNonAnswer.filter(({ evidence }) => !evidence.passed)
        .flatMap(({ evidence }) => evidence.gaps.map((gap) => `${evidence.binding_id} (optional, non-answer mode): ${gap}`)),
    ]
    const gaps = [...mandatoryAnswerGaps, ...diagnosticGaps]
    const hasSourceQueryRequirement = mandatoryAnswer.some(({ binding }) =>
      requirementsForBindingTree(binding.binding_id, bindingIndex).some(sourceQueryRequirement),
    )

    if (mandatoryAnswer.length === 0) {
      // No mandatory answer binding at all — either every mandatory binding is non-answer (the
      // whole-SCU RC-7 case), or this SCU has only optional-mode bindings (no plain default).
      // Either way there is no chart-evidence-bearing default to report as 'available'/'partial'.
      const allMandatoryNonAnswerPassed = mandatoryNonAnswer.length > 0
        && mandatoryNonAnswer.every(({ evidence }) => evidence.passed)
      return {
        scu_id: scu.scu_id,
        build_status: build.status,
        build_id: build.build_id,
        freshness: null,
        // Never listed as available: a plan/resource/discovery capability carries no chart
        // evidence, so no door may admit it for an answer. An optional mode that DID pass as
        // answer evidence is still listed (availableBindingIds already includes it) even
        // though the SCU as a whole has no mandatory answer default.
        available_binding_ids: availableBindingIds,
        state: allMandatoryNonAnswerPassed && mandatoryNonAnswer.every(({ evidence }) => evidence.gaps.length === 0)
          ? 'resource_ok' as const
          : availableBindingIds.length > 0 ? 'partial' as const : 'dark' as const,
        gaps,
        asset_receipts: [],
      }
    }

    const allMandatoryAnswerPassed = mandatoryAnswer.every(({ evidence }) => evidence.passed)
    const hasPartialReceipt = assetReceipts.some((receipt) => receipt.state === 'partial')
    const hasFailedReceipt = assetReceipts.some((receipt) => receipt.state === 'failed')
    // A missing/unavailable MANDATORY answer binding still prevents 'available' — the state
    // computation below reads only mandatoryAnswerGaps/allMandatoryAnswerPassed, never
    // diagnosticGaps, so an optional mode's own unavailability (whether non-answer or a failed
    // answer probe) can only ever add a diagnostic gap line, never move state away from
    // 'available'.
    const state = allMandatoryAnswerPassed && mandatoryAnswerGaps.length === 0 ? 'available'
      : mandatoryAnswer.some(({ evidence }) => evidence.passed) ? 'partial'
      : hasFailedReceipt ? 'incompatible' : 'dark'
    return {
      scu_id: scu.scu_id,
      build_status: build.status,
      build_id: build.build_id,
      // A successful LIMIT 0 source query proves only schema/query
      // reachability. It carries no row timestamp or content-freshness proof.
      freshness: allMandatoryAnswerPassed ? hasSourceQueryRequirement ? 'unknown' : 'fresh' : hasPartialReceipt ? 'unknown' : null,
      available_binding_ids: availableBindingIds,
      state,
      gaps: gaps.length ? gaps : allMandatoryAnswerPassed ? [] : ['No reviewed producer-output receipt is joined to this semantic capability.'],
      asset_receipts: assetReceipts,
    }
  })
}

/** Load a chart/build overlay without treating unavailable provenance as availability. */
export async function loadChartCapabilityOverlay(
  snapshot: CapabilityKnowledgeSnapshot,
  chartId: string,
  query: OverlayQueryExecutor = defaultQuery as OverlayQueryExecutor,
  now: Date = new Date(),
): Promise<ChartCapabilityOverlay> {
  // `build_id` on the overlay is the served-generation identity: a stable token that changes
  // whenever any asset's served binding changes. It is never a single build_runs id.
  let build: { build_id: string | null; status: string | null } = { build_id: null, status: null }
  try {
    const assetIds = assetIdsForSnapshot(snapshot)
    const serviceProbeAssetIds = serviceProbeAssetIdsForSnapshot(snapshot)
    const aliases = { receipt: 'p', receiptRun: 'receipt_run', receiptAsset: 'receipt_asset' }
    const { rows: queryRows } = await query(
        `WITH service_probe_evidence AS (
           SELECT event.entity_id AS asset_id, event.source_kind, event.source_ref,
                  event.observed_at::text AS observed_at, event.evidence_payload
             FROM nirmana_evidence.nirmana_elevation_campaign_events event
            WHERE event.event_type = 'probe_accepted'
              AND event.entity_type = 'asset'
              AND event.entity_id = ANY($3::text[])
         )
         SELECT p.asset_id, p.chart_id::text, p.build_id::text, p.receipt_version,
                p.receipt_state, p.output_digest_spec_sha256, p.observed_at::text,
                f.freshness_state, p.unknown_reasons, f.reasons AS freshness_reasons,
                ${servedReceiptColumnsSql(aliases)},
                COALESCE((SELECT jsonb_agg(jsonb_build_object(
                  'asset_id', service.asset_id,
                  'source_kind', service.source_kind,
                  'source_ref', service.source_ref,
                  'observed_at', service.observed_at,
                  'evidence_payload', service.evidence_payload
                ) ORDER BY service.observed_at DESC)
                  FROM service_probe_evidence service), '[]'::jsonb) AS service_probe_evidence
           FROM (SELECT 1) anchor
           -- Every chart receipt (the served generation spans all of them), plus global
           -- receipts for the snapshot's producer assets.
           LEFT JOIN asset_provenance_receipts p
             ON p.chart_id=$2::uuid
             OR (p.chart_id IS NULL AND p.asset_id = ANY($1::text[]))
           LEFT JOIN asset_freshness f
             ON f.asset_id=p.asset_id AND f.scope_key=p.scope_key AND f.partition_key=p.partition_key
           ${servedReceiptJoinsSql(aliases)}
          ORDER BY p.asset_id, (p.chart_id IS NOT NULL) DESC, p.observed_at DESC`,
        [assetIds, chartId, serviceProbeAssetIds],
      )
    const rows = queryRows.filter((row): row is OverlayQueryRow & { asset_id: string } => typeof row.asset_id === 'string')
    // The resolver keeps only this chart's receipts (case-insensitively); global rows drop out.
    const generation = chartServedGenerationFromRows(chartId, null, rows as unknown as Record<string, unknown>[])
    const identity = servedGenerationIdentity(generation)
    build = { build_id: identity, status: identity ? 'served_generation' : null }
    const sourceQueryEvidence = await sourceQueryEvidenceForSnapshot(snapshot, chartId, generation.served_build_ids, query)
    return compileChartCapabilityOverlay({
      snapshot, chart_id: chartId, build_id: build.build_id,
      code_revision: process.env['K_REVISION'] ?? process.env['GIT_SHA'] ?? null,
      evidence: evidenceForSnapshot(snapshot, rows, generation, build, serviceProbeRows(queryRows[0]?.service_probe_evidence), sourceQueryEvidence, now),
    })
  } catch (error) {
    console.error('[capability-overlay] availability evidence unavailable', error)
    return compileChartCapabilityOverlay({
      snapshot, chart_id: chartId, build_id: build.build_id,
      code_revision: process.env['K_REVISION'] ?? process.env['GIT_SHA'] ?? null,
      evidence: snapshot.scus.map((scu) => ({
        scu_id: scu.scu_id, build_status: build.status, build_id: build.build_id,
        freshness: null, available_binding_ids: [], state: 'dark' as const,
        gaps: ['Capability provenance could not be loaded.'], asset_receipts: [],
      })),
    })
  }
}
