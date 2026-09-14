import { CAPABILITY_COMPATIBILITY_VERSION, type CapabilityKnowledgeSnapshot, type ChartAssetCapabilityReceipt, type ChartCapabilityAvailability, type ChartCapabilityOverlay } from './types'
import { deepFreeze, stableFingerprint } from './stable'

export interface ChartCapabilityEvidence {
  readonly scu_id: string
  readonly build_status: string | null
  readonly build_id: string | null
  readonly freshness: string | null
  readonly available_binding_ids: readonly string[]
  readonly state?: ChartCapabilityAvailability['state']
  readonly gaps?: readonly string[]
  readonly asset_receipts?: readonly ChartAssetCapabilityReceipt[]
}

export function compileChartCapabilityOverlay(args: {
  snapshot: CapabilityKnowledgeSnapshot
  chart_id: string
  build_id: string | null
  code_revision?: string | null
  writer_inventory_hash?: string | null
  evidence: readonly ChartCapabilityEvidence[]
  generated_at?: string
}): ChartCapabilityOverlay {
  const evidenceByScu = new Map(args.evidence.map((item) => [item.scu_id, item]))
  const availability: ChartCapabilityAvailability[] = args.snapshot.scus.map((scu) => {
    const evidence = evidenceByScu.get(scu.scu_id)
    if (!evidence) return {
      scu_id: scu.scu_id,
      state: 'dark',
      build_status: null,
      build_id: args.build_id,
      freshness: null,
      available_binding_ids: [],
      gaps: ['No chart/build availability evidence was supplied.'],
      asset_receipts: [],
    }
    const expected = new Set(scu.bindings.filter((binding) => binding.executable).map((binding) => binding.binding_id))
    const available = evidence.available_binding_ids.filter((id) => expected.has(id)).sort()
    return {
      scu_id: scu.scu_id,
      state: evidence.state ?? (available.length === 0 ? 'empty' : available.length === expected.size ? 'available' : 'partial'),
      build_status: evidence.build_status,
      build_id: evidence.build_id,
      freshness: evidence.freshness,
      available_binding_ids: available,
      gaps: [...(evidence.gaps ?? [])],
      asset_receipts: [...(evidence.asset_receipts ?? [])].sort((a, b) => a.asset_id.localeCompare(b.asset_id)),
    }
  })
  const overlayVersion = stableFingerprint({
    compatibility_version: CAPABILITY_COMPATIBILITY_VERSION,
    catalog_content_hash: args.snapshot.content_hash,
    chart_id: args.chart_id,
    build_id: args.build_id,
    code_revision: args.code_revision ?? null,
    writer_inventory_hash: args.writer_inventory_hash ?? null,
    availability,
  })
  return deepFreeze({
    chart_id: args.chart_id,
    overlay_version: overlayVersion,
    capability_compatibility_version: CAPABILITY_COMPATIBILITY_VERSION,
    catalog_content_hash: args.snapshot.content_hash,
    build_id: args.build_id,
    code_revision: args.code_revision ?? null,
    writer_inventory_hash: args.writer_inventory_hash ?? null,
    generated_at: args.generated_at ?? new Date().toISOString(),
    availability,
  })
}

export function assertOverlayCompatibility(snapshot: CapabilityKnowledgeSnapshot, overlay: ChartCapabilityOverlay, chartId?: string): void {
  if (overlay.capability_compatibility_version !== snapshot.compatibility_version || overlay.catalog_content_hash !== snapshot.content_hash) {
    throw new Error('CAPABILITY_OVERLAY_INCOMPATIBLE')
  }
  if (chartId && overlay.chart_id !== chartId) throw new Error('CAPABILITY_OVERLAY_CHART_MISMATCH')
}
