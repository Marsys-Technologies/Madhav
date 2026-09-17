import { query as defaultQuery } from '@/lib/db/client'
import { compileChartCapabilityOverlay, type ChartCapabilityEvidence } from './overlay'
import { stableFingerprint } from './stable'
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
  SemanticCapabilityBinding,
  SemanticCapabilityUnit,
} from './types'

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
  active_build_id: string | null
  active_build_status: string | null
  service_probe_evidence?: unknown
}

export type OverlayQueryExecutor = (
  sql: string,
  params?: unknown[],
) => Promise<{ rows: OverlayQueryRow[] }>

function reasons(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

function receiptForClaim(claim: ProducerOutputClaim, rows: readonly ReceiptRow[], activeBuildId: string | null): ChartAssetCapabilityReceipt {
  const matching = rows.filter((row) => row.asset_id === claim.asset_id)
  // A chart-scoped receipt is evidence only for the selected completed build.
  // Superseded rows must not poison a newer build, and must not be treated as
  // current merely because they share chart_id. Global evidence is a fallback
  // only when this asset has no receipt for the active chart build.
  const activeChartRows = activeBuildId === null
    ? []
    : matching.filter((row) => row.chart_id !== null && row.build_id === activeBuildId)
  const chosen = activeChartRows.length ? activeChartRows : matching.filter((row) => row.chart_id === null)
  if (!chosen.length) return {
    asset_id: claim.asset_id, build_id: null, writer_version: null,
    output_digest_spec_sha256: claim.output_digest_spec_sha256, state: 'missing', receipt_ref: null,
  }
  const specMismatch = chosen.some((row) => row.output_digest_spec_sha256 !== claim.output_digest_spec_sha256)
  const failed = chosen.some((row) => row.receipt_state !== 'proven' || row.freshness_state !== 'fresh')
  return {
    asset_id: claim.asset_id,
    build_id: chosen.map((row) => row.build_id).find(Boolean) ?? null,
    writer_version: null,
    output_digest_spec_sha256: claim.output_digest_spec_sha256,
    state: specMismatch ? 'failed' : failed ? 'partial' : 'passed',
    receipt_ref: stableFingerprint(chosen.map((row) => ({
      asset_id: row.asset_id,
      build_id: row.build_id,
      receipt_version: row.receipt_version,
      receipt_state: row.receipt_state,
      output_digest_spec_sha256: row.output_digest_spec_sha256,
      freshness_state: row.freshness_state,
      observed_at: row.observed_at,
    }))),
  }
}

function receiptForRequirement(
  requirement: ProducerOutputAvailabilityRequirement,
  rows: readonly ReceiptRow[],
  activeBuildId: string | null,
): ChartAssetCapabilityReceipt {
  const matching = rows.filter((row) => row.asset_id === requirement.asset_id)
  const chosen = requirement.scope === 'chart_build'
    ? activeBuildId === null ? [] : matching.filter((row) => row.chart_id !== null && row.build_id === activeBuildId)
    : matching.filter((row) => row.chart_id === null)
  if (!chosen.length) return {
    asset_id: requirement.asset_id, build_id: null, writer_version: null,
    output_digest_spec_sha256: requirement.spec_sha256, state: 'missing', receipt_ref: null,
  }
  const specMismatch = chosen.some((row) => row.output_digest_spec_sha256 !== requirement.spec_sha256)
  const failed = chosen.some((row) => row.receipt_state !== 'proven' || row.freshness_state !== 'fresh')
  return {
    asset_id: requirement.asset_id,
    build_id: chosen.map((row) => row.build_id).find(Boolean) ?? null,
    writer_version: null,
    output_digest_spec_sha256: requirement.spec_sha256,
    state: specMismatch ? 'failed' : failed ? 'partial' : 'passed',
    receipt_ref: stableFingerprint(chosen.map((row) => ({
      asset_id: row.asset_id,
      build_id: row.build_id,
      receipt_version: row.receipt_version,
      receipt_state: row.receipt_state,
      output_digest_spec_sha256: row.output_digest_spec_sha256,
      freshness_state: row.freshness_state,
      observed_at: row.observed_at,
    }))),
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
  if (!Array.isArray(contracts)
    || contracts.some((contract) => !isRecord(contract)
      || typeof contract.binding_id !== 'string'
      || !Array.isArray(contract.requirements))) return null
  const matches = contracts.filter((contract) => contract.binding_id === binding.binding_id)
  return matches.length === 1 ? matches[0] : matches.length > 1 ? null : undefined
}

function authoredContractIntegrityGap(scu: SemanticCapabilityUnit): string | null {
  const contracts = scu.availability_contracts
  if (contracts === undefined) return null
  if (!Array.isArray(contracts)
    || contracts.some((contract) => !isRecord(contract)
      || typeof contract.binding_id !== 'string'
      || !Array.isArray(contract.requirements))) {
    return 'Malformed binding availability contracts prevent a safe evidence selection.'
  }
  const contractBindingIds = new Set<string>()
  for (const contract of contracts) {
    if (contractBindingIds.has(contract.binding_id)) {
      return 'Duplicate binding availability contracts prevent a safe evidence selection.'
    }
    contractBindingIds.add(contract.binding_id)
    if (scu.bindings.filter((binding) => binding.binding_id === contract.binding_id && binding.executable).length !== 1) {
      return 'Binding availability contract names an unknown or non-executable local binding.'
    }
    if (contract.requirements.length === 0) {
      return 'Binding availability contract has no requirements.'
    }
    for (const requirement of contract.requirements) {
      if (producerOutputRequirement(requirement)) {
        const reviewedClaim = (scu.producer_output_claims ?? []).some((claim) => claim.disposition === 'reviewed_output'
          && claim.asset_id === requirement.asset_id
          && claim.output_digest_spec_sha256 === requirement.spec_sha256)
        if (!reviewedClaim) {
          return 'Producer-output availability requirement has no same-SCU reviewed output claim with the exact asset and SHA-256.'
        }
        continue
      }
      if (!serviceProbeRequirement(requirement) && !usableDerivedRequirement(requirement)) {
        return 'Binding availability contract contains a malformed or unsupported requirement.'
      }
    }
  }
  return null
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
    if (authoredContractIntegrityGap(scu)) return []
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
    if (authoredContractIntegrityGap(scu)) return []
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

function gapsForReceipts(receipts: readonly ChartAssetCapabilityReceipt[], rows: readonly ReceiptRow[]): string[] {
  return receipts.flatMap((receipt) => {
    if (receipt.state === 'passed') return []
    const sourceRows = rows.filter((row) => row.asset_id === receipt.asset_id)
    return [`${receipt.asset_id} availability is ${receipt.state}.`, ...sourceRows.flatMap((row) => [...reasons(row.unknown_reasons), ...reasons(row.freshness_reasons)])]
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
  activeBuildId: string | null,
  probeRows: readonly ServiceProbeEvidenceRow[],
  now: Date,
  bindingIndex: ReadonlyMap<string, BindingTarget | null>,
  visiting = new Set<string>(),
  requireExplicitContract = false,
): BindingEvidence {
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
  if ((hasAuthoredContracts(scu) || requireExplicitContract) && !contract) return {
    binding_id: binding.binding_id,
    passed: false,
    receipts: [],
    gaps: ['Binding has no authored availability contract.'],
  }
  if (contract) {
    const producerRequirements = contract.requirements.filter(producerOutputRequirement)
    const serviceRequirements = contract.requirements.filter(serviceProbeRequirement)
    const derivedRequirements = contract.requirements.filter(usableDerivedRequirement)
    const unsupported = contract.requirements.filter((requirement) => !producerOutputRequirement(requirement)
      && !serviceProbeRequirement(requirement) && !usableDerivedRequirement(requirement))
    const receipts = producerRequirements.map((requirement) => receiptForRequirement(requirement, rows, activeBuildId))
    const derivedEvidence = derivedRequirements.flatMap((requirement) => requirement.required_binding_ids.map((bindingId) => {
      const target = bindingIndex.get(bindingId)
      if (!target || target.scu.scope !== requirement.scope || scu.scope !== requirement.scope) return {
        binding_id: bindingId,
        passed: false,
        receipts: [],
        gaps: [`Derived availability leg ${bindingId} has no scope-compatible executable binding.`],
      } satisfies BindingEvidence
      return evidenceForBinding(
        target.scu, target.binding, rows, activeBuildId, probeRows, now, bindingIndex, nextVisiting, true,
      )
    }))
    const derivedGaps = derivedEvidence.flatMap((evidence) => evidence.gaps.map((gap) =>
      `Derived availability leg ${evidence.binding_id}: ${gap}`,
    ))
    const gaps = [
      ...(contract.requirements.length === 0 ? ['Binding availability contract has no requirements.'] : []),
      ...unsupported.map(() => 'Binding availability contract contains a malformed or unsupported requirement.'),
      ...gapsForReceipts(receipts, rows),
      ...serviceRequirements.flatMap((requirement) => serviceProbeGaps(requirement, probeRows, now)),
      ...derivedGaps,
    ]
    return {
      binding_id: binding.binding_id,
      passed: contract.requirements.length > 0 && !unsupported.length && receipts.every((receipt) => receipt.state === 'passed')
        && serviceRequirements.every((requirement) => serviceProbeGaps(requirement, probeRows, now).length === 0)
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
  const receipts = reviewed.map((claim) => receiptForClaim(claim, rows, activeBuildId))
  const unsupported = claims.filter((claim) => !reviewed.includes(claim))
  return {
    binding_id: binding.binding_id,
    passed: claims.length > 0 && !unsupported.length && receipts.every((receipt) => receipt.state === 'passed'),
    receipts,
    gaps: [
      ...unsupported.map((claim) => claim.gap_reason ?? `${claim.asset_id} has no reviewed output claim.`),
      ...gapsForReceipts(receipts, rows),
    ],
  }
}

function evidenceForSnapshot(
  snapshot: CapabilityKnowledgeSnapshot,
  rows: readonly ReceiptRow[],
  build: { build_id: string | null; status: string | null },
  probeRows: readonly ServiceProbeEvidenceRow[],
  now: Date,
): ChartCapabilityEvidence[] {
  const bindingIndex = executableBindingIndex(snapshot)
  return snapshot.scus.map((scu) => {
    const contractIntegrityGap = authoredContractIntegrityGap(scu)
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
    const bindingEvidence = executableBindings.map((binding) => evidenceForBinding(
      scu, binding, rows, build.build_id, probeRows, now, bindingIndex,
    ))
    const availableBindingIds = bindingEvidence.filter((evidence) => evidence.passed).map((evidence) => evidence.binding_id)
    const assetReceipts = bindingEvidence.flatMap((evidence) => evidence.receipts)
    const allPassed = executableBindings.length > 0 && availableBindingIds.length === executableBindings.length
    const gaps = bindingEvidence.flatMap((evidence) => evidence.gaps)
    const hasPartialReceipt = assetReceipts.some((receipt) => receipt.state === 'partial')
    const hasFailedReceipt = assetReceipts.some((receipt) => receipt.state === 'failed')
    const state = availableBindingIds.length > 0
      ? allPassed && gaps.length === 0 ? 'available' : 'partial'
      : hasFailedReceipt ? 'incompatible' : 'dark'
    return {
      scu_id: scu.scu_id,
      build_status: build.status,
      build_id: build.build_id,
      freshness: allPassed ? 'fresh' : hasPartialReceipt ? 'unknown' : null,
      available_binding_ids: availableBindingIds,
      state,
      gaps: gaps.length ? gaps : allPassed ? [] : ['No reviewed producer-output receipt is joined to this semantic capability.'],
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
  let build: { build_id: string | null; status: string | null } = { build_id: null, status: null }
  try {
    const assetIds = assetIdsForSnapshot(snapshot)
    const serviceProbeAssetIds = serviceProbeAssetIdsForSnapshot(snapshot)
    const { rows: queryRows } = await query(
        `WITH latest_build AS (
           SELECT id AS build_id, state AS status
             FROM build_runs
            WHERE chart_id=$2::uuid AND state='completed'
            ORDER BY ended_at DESC NULLS LAST, id DESC
            LIMIT 1
         ), service_probe_evidence AS (
           SELECT event.entity_id AS asset_id, event.source_kind, event.source_ref,
                  event.observed_at::text AS observed_at, event.evidence_payload
             FROM nirmana_evidence.nirmana_elevation_campaign_events event
            WHERE event.event_type = 'probe_accepted'
              AND event.entity_type = 'asset'
              AND event.entity_id = ANY($3::text[])
         )
         SELECT latest_build.build_id::text AS active_build_id,
                latest_build.status AS active_build_status,
                p.asset_id, p.chart_id::text, p.build_id::text, p.receipt_version,
                p.receipt_state, p.output_digest_spec_sha256, p.observed_at::text,
                f.freshness_state, p.unknown_reasons, f.reasons AS freshness_reasons,
                COALESCE((SELECT jsonb_agg(jsonb_build_object(
                  'asset_id', service.asset_id,
                  'source_kind', service.source_kind,
                  'source_ref', service.source_ref,
                  'observed_at', service.observed_at,
                  'evidence_payload', service.evidence_payload
                ) ORDER BY service.observed_at DESC)
                  FROM service_probe_evidence service), '[]'::jsonb) AS service_probe_evidence
           FROM (SELECT 1) anchor
           LEFT JOIN latest_build ON true
           LEFT JOIN asset_provenance_receipts p
             ON p.asset_id = ANY($1::text[])
            AND (
              (p.chart_id=$2::uuid AND p.build_id=latest_build.build_id)
              OR p.chart_id IS NULL
            )
           LEFT JOIN asset_freshness f
             ON f.asset_id=p.asset_id AND f.scope_key=p.scope_key AND f.partition_key=p.partition_key
          ORDER BY p.asset_id, (p.chart_id IS NOT NULL) DESC, p.observed_at DESC`,
        [assetIds, chartId, serviceProbeAssetIds],
      )
    build = { build_id: queryRows[0]?.active_build_id ?? null, status: queryRows[0]?.active_build_status ?? null }
    const rows = queryRows.filter((row): row is OverlayQueryRow & { asset_id: string } => typeof row.asset_id === 'string')
    return compileChartCapabilityOverlay({
      snapshot, chart_id: chartId, build_id: build.build_id,
      code_revision: process.env['K_REVISION'] ?? process.env['GIT_SHA'] ?? null,
      evidence: evidenceForSnapshot(snapshot, rows, build, serviceProbeRows(queryRows[0]?.service_probe_evidence), now),
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
