import { describe, expect, it } from 'vitest'
import type {
  CapabilityKnowledgeSnapshot,
  ChartCapabilityOverlay,
  SemanticCapabilityBinding,
} from '../../retrieval/registry/knowledge/types'
import committedSnapshot from '../../../generated/capability_knowledge.snapshot.json'
import { BEYOND_ACARYA_ACCEPTANCE_CASES } from './beyond_acarya_acceptance.corpus'
import { compileInquiryContract } from './compiler'

const snapshot = committedSnapshot as CapabilityKnowledgeSnapshot
const chartId = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const temporalAnchorDate = '2026-09-15'
const rawTransport = { execution_channel: 'mcp_full' as const, presentation_transport: 'raw_mcp' as const }
const requiredRouteScuIds = new Set([
  'scu.catalog.get_dashas',
  'scu.catalog.get_divisionals',
  'scu.catalog.query_planet_transit',
  'scu.catalog.query_chart_gestalt',
])

function registryBinding(
  source: CapabilityKnowledgeSnapshot,
  scuId: string,
): SemanticCapabilityBinding {
  const binding = source.scus.find((scu) => scu.scu_id === scuId)?.bindings.find((candidate) =>
    candidate.kind === 'registry_capability'
    && candidate.executable
    && candidate.execution_channels?.includes('platform_internal'))
  if (!binding) throw new Error(`MISSING_INTERNAL_REGISTRY_BINDING:${scuId}`)
  return binding
}

function overlayFor(
  source: CapabilityKnowledgeSnapshot,
  available: readonly { scu_id: string; binding_id: string }[],
): ChartCapabilityOverlay {
  return {
    chart_id: chartId,
    overlay_version: 'sha256:raw-inquiry-binding-specific-overlay',
    capability_compatibility_version: source.compatibility_version,
    catalog_content_hash: source.content_hash,
    build_id: 'raw-inquiry-binding-specific-build',
    code_revision: 'raw-inquiry-policy-test',
    writer_inventory_hash: null,
    generated_at: '2026-09-17T00:00:00.000Z',
    availability: available.map(({ scu_id, binding_id }) => ({
      scu_id,
      state: 'available' as const,
      build_status: 'completed',
      build_id: 'raw-inquiry-binding-specific-build',
      freshness: 'fixture-current',
      available_binding_ids: [binding_id],
      gaps: [],
      asset_receipts: [],
    })),
  }
}

function compileRaw(
  source: CapabilityKnowledgeSnapshot,
  overlay: ChartCapabilityOverlay,
  question: string,
  scope_tuple: (typeof BEYOND_ACARYA_ACCEPTANCE_CASES)[number]['scope_tuple'],
) {
  return compileInquiryContract({
    snapshot: source,
    overlay,
    chart_id: chartId,
    question,
    scope_tuple,
    temporal_anchor_date: temporalAnchorDate,
    ...rawTransport,
  })
}

describe('raw inquiry registry execution policy', () => {
  const allowedBindings = [...requiredRouteScuIds].map((scu_id) => ({
    scu_id,
    binding_id: registryBinding(snapshot, scu_id).binding_id,
  }))
  const overlay = overlayFor(snapshot, allowedBindings)

  it('uses only exact overlay-granted internal registry bindings for the frozen raw corpus', () => {
    expect(overlay.availability).toHaveLength(requiredRouteScuIds.size)
    expect(overlay.availability.every((availability) => availability.available_binding_ids.length === 1)).toBe(true)

    const contracts = BEYOND_ACARYA_ACCEPTANCE_CASES.map((item) =>
      compileRaw(snapshot, overlay, item.question, item.scope_tuple))

    for (const scuId of requiredRouteScuIds) {
      const expectedBinding = registryBinding(snapshot, scuId)
      const matchingItems = contracts.flatMap((contract) => contract.plan_items.filter((item) => item.scu_id === scuId))
      expect(matchingItems.length, `${scuId} must be selected by the frozen corpus`).toBeGreaterThan(0)
      expect(matchingItems).toEqual(expect.arrayContaining([
        expect.objectContaining({ state: 'ready', binding_id: expectedBinding.binding_id }),
      ]))
    }

    // This is deliberately not a globally lit overlay: unrelated obligations
    // remain dark even though the raw transport can use the safe bindings above.
    expect(contracts.flatMap((contract) => contract.plan_items).some((item) =>
      !requiredRouteScuIds.has(item.scu_id) && item.state === 'blocked')).toBe(true)
  })

  it('keeps a missing handler, an MCP-native alias, and an ungranted binding blocked', () => {
    const divisionalScuId = 'scu.catalog.get_divisionals'
    const internal = registryBinding(snapshot, divisionalScuId)
    const alias = snapshot.scus.find((scu) => scu.scu_id === divisionalScuId)!.bindings.find((binding) =>
      binding.kind === 'mcp_native')!

    const noHandler: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id !== divisionalScuId ? scu : {
        ...scu,
        bindings: scu.bindings.map((binding) => binding.binding_id === internal.binding_id
          ? { ...binding, executable: false }
          : binding),
      }),
    }
    const aliasOnly: CapabilityKnowledgeSnapshot = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id !== divisionalScuId ? scu : {
        ...scu,
        bindings: scu.bindings.filter((binding) => binding.binding_id === alias.binding_id),
      }),
    }
    const scenario = BEYOND_ACARYA_ACCEPTANCE_CASES[0]!
    const noHandlerItem = compileRaw(
      noHandler,
      overlayFor(noHandler, [{ scu_id: divisionalScuId, binding_id: internal.binding_id }]),
      scenario.question,
      scenario.scope_tuple,
    ).plan_items.find((item) => item.scu_id === divisionalScuId)
    const aliasItem = compileRaw(
      aliasOnly,
      overlayFor(aliasOnly, [{ scu_id: divisionalScuId, binding_id: alias.binding_id }]),
      scenario.question,
      scenario.scope_tuple,
    ).plan_items.find((item) => item.scu_id === divisionalScuId)
    const ungrantedItem = compileRaw(
      snapshot,
      overlayFor(snapshot, [{ scu_id: divisionalScuId, binding_id: 'registry:marsys://tool/L1/not-granted' }]),
      scenario.question,
      scenario.scope_tuple,
    ).plan_items.find((item) => item.scu_id === divisionalScuId)

    expect(noHandlerItem).toMatchObject({ state: 'blocked', binding_id: null })
    expect(aliasItem).toMatchObject({ state: 'blocked', binding_id: null })
    expect(ungrantedItem).toMatchObject({ state: 'blocked', binding_id: null })
    expect(ungrantedItem?.blocked_reason).toContain('overlay')
  })
})
