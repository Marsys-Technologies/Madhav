import { query as defaultQuery } from '@/lib/db/client'
import { compileChartCapabilityOverlay, type ChartCapabilityEvidence } from './overlay'
import { stableFingerprint } from './stable'
import type {
  AvailabilityRequirement,
  BindingAvailabilityContract,
  CapabilityKnowledgeSnapshot,
  ChartAssetCapabilityReceipt,
  ChartCapabilityOverlay,
  ProducerOutputAvailabilityRequirement,
  ProducerOutputClaim,
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

function producerOutputRequirement(requirement: AvailabilityRequirement): requirement is ProducerOutputAvailabilityRequirement {
  return requirement.kind === 'producer_output'
}

function contractForBinding(
  scu: SemanticCapabilityUnit,
  binding: SemanticCapabilityBinding,
): BindingAvailabilityContract | undefined {
  return scu.availability_contracts?.find((contract) => contract.binding_id === binding.binding_id)
}

function assetIdsForSnapshot(snapshot: CapabilityKnowledgeSnapshot): string[] {
  return [...new Set(snapshot.scus.flatMap((scu) => scu.bindings.flatMap((binding) => {
    if (!binding.executable) return []
    const contract = contractForBinding(scu, binding)
    if (contract) return contract.requirements.filter(producerOutputRequirement).map((requirement) => requirement.asset_id)
    return (scu.producer_output_claims ?? []).filter((claim) => claim.disposition === 'reviewed_output').map((claim) => claim.asset_id)
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

function evidenceForBinding(
  scu: SemanticCapabilityUnit,
  binding: SemanticCapabilityBinding,
  rows: readonly ReceiptRow[],
  activeBuildId: string | null,
): BindingEvidence {
  const contract = contractForBinding(scu, binding)
  if (contract) {
    const producerRequirements = contract.requirements.filter(producerOutputRequirement)
    const unsupported = contract.requirements.filter((requirement) => !producerOutputRequirement(requirement))
    const receipts = producerRequirements.map((requirement) => receiptForRequirement(requirement, rows, activeBuildId))
    const gaps = [
      ...(contract.requirements.length === 0 ? ['Binding availability contract has no requirements.'] : []),
      ...unsupported.map((requirement) => `${requirement.kind} availability requirements are not implemented.`),
      ...gapsForReceipts(receipts, rows),
    ]
    return { binding_id: binding.binding_id, passed: receipts.length > 0 && !unsupported.length && receipts.every((receipt) => receipt.state === 'passed'), receipts, gaps }
  }

  const claims = scu.producer_output_claims ?? []
  const reviewed = claims.filter((claim) => claim.disposition === 'reviewed_output')
  const receipts = reviewed.map((claim) => receiptForClaim(claim, rows, activeBuildId))
  const unsupported = claims.filter((claim) => claim.disposition !== 'reviewed_output')
  return {
    binding_id: binding.binding_id,
    passed: receipts.length > 0 && receipts.every((receipt) => receipt.state === 'passed'),
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
): ChartCapabilityEvidence[] {
  return snapshot.scus.map((scu) => {
    const executableBindings = scu.bindings.filter((binding) => binding.executable)
    const bindingEvidence = executableBindings.map((binding) => evidenceForBinding(scu, binding, rows, build.build_id))
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
): Promise<ChartCapabilityOverlay> {
  let build: { build_id: string | null; status: string | null } = { build_id: null, status: null }
  try {
    const assetIds = assetIdsForSnapshot(snapshot)
    const { rows: queryRows } = await query(
        `WITH latest_build AS (
           SELECT id AS build_id, state AS status
             FROM build_runs
            WHERE chart_id=$2::uuid AND state='completed'
            ORDER BY ended_at DESC NULLS LAST, id DESC
            LIMIT 1
         )
         SELECT latest_build.build_id::text AS active_build_id,
                latest_build.status AS active_build_status,
                p.asset_id, p.chart_id::text, p.build_id::text, p.receipt_version,
                p.receipt_state, p.output_digest_spec_sha256, p.observed_at::text,
                f.freshness_state, p.unknown_reasons, f.reasons AS freshness_reasons
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
        [assetIds, chartId],
      )
    build = { build_id: queryRows[0]?.active_build_id ?? null, status: queryRows[0]?.active_build_status ?? null }
    const rows = queryRows.filter((row): row is OverlayQueryRow & { asset_id: string } => typeof row.asset_id === 'string')
    return compileChartCapabilityOverlay({
      snapshot, chart_id: chartId, build_id: build.build_id,
      code_revision: process.env['K_REVISION'] ?? process.env['GIT_SHA'] ?? null,
      evidence: evidenceForSnapshot(snapshot, rows, build),
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
