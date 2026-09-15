import { query as defaultQuery } from '@/lib/db/client'
import { compileChartCapabilityOverlay, type ChartCapabilityEvidence } from './overlay'
import { stableFingerprint } from './stable'
import type { CapabilityKnowledgeSnapshot, ChartAssetCapabilityReceipt, ChartCapabilityOverlay, ProducerOutputClaim } from './types'

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

function evidenceForSnapshot(
  snapshot: CapabilityKnowledgeSnapshot,
  rows: readonly ReceiptRow[],
  build: { build_id: string | null; status: string | null },
): ChartCapabilityEvidence[] {
  return snapshot.scus.map((scu) => {
    const claims = scu.producer_output_claims ?? []
    const reviewed = claims.filter((claim) => claim.disposition === 'reviewed_output')
    const assetReceipts = reviewed.map((claim) => receiptForClaim(claim, rows, build.build_id))
    const unsupported = claims.filter((claim) => claim.disposition !== 'reviewed_output')
    const allPassed = assetReceipts.length > 0 && assetReceipts.every((receipt) => receipt.state === 'passed')
    const gaps = [
      ...unsupported.map((claim) => claim.gap_reason ?? `${claim.asset_id} has no reviewed output claim.`),
      ...assetReceipts.flatMap((receipt) => {
        if (receipt.state === 'passed') return []
        const sourceRows = rows.filter((row) => row.asset_id === receipt.asset_id)
        return [`${receipt.asset_id} availability is ${receipt.state}.`, ...sourceRows.flatMap((row) => [...reasons(row.unknown_reasons), ...reasons(row.freshness_reasons)])]
      }),
    ]
    return {
      scu_id: scu.scu_id,
      build_status: build.status,
      build_id: build.build_id,
      freshness: allPassed ? 'fresh' : assetReceipts.some((receipt) => receipt.state === 'partial') ? 'unknown' : null,
      available_binding_ids: allPassed ? scu.bindings.filter((binding) => binding.executable).map((binding) => binding.binding_id) : [],
      state: allPassed ? (gaps.length ? 'partial' : 'available') : assetReceipts.some((receipt) => receipt.state === 'failed') ? 'incompatible' : 'dark',
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
    const assetIds = [...new Set(snapshot.scus.flatMap((scu) => (scu.producer_output_claims ?? []).map((claim) => claim.asset_id)))]
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
