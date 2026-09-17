import { describe, expect, it } from 'vitest'
import committedSnapshot from '../../../generated/capability_knowledge.snapshot.json'
import type {
  CapabilityKnowledgeSnapshot,
  ChartCapabilityOverlay,
  ExecutionChannel,
} from '../../retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import { BEYOND_ACARYA_ACCEPTANCE_CASES } from './beyond_acarya_acceptance.corpus'
import { compileInquiryContract } from './compiler'
import { buildInquiryDoorParityProjection } from './door_parity'

const snapshot = committedSnapshot as CapabilityKnowledgeSnapshot
const chartId = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const temporalAnchorDate = '2026-09-15'

/**
 * These are the only direct chart-evidence bindings C2 is permitted to light.
 * They deliberately name the generated registry declarations rather than an
 * MCP alias or a convenient same-SCU alternative.
 */
const requiredBindings = {
  'scu.catalog.get_dashas': 'registry:marsys://tool/L1/get_dashas',
  'scu.catalog.get_divisionals': 'registry:marsys://tool/L1/get_divisionals',
  'scu.catalog.query_planet_transit': 'registry:marsys://tool/L0/query_current_transit_snapshot',
  'scu.catalog.query_chart_gestalt': 'registry:marsys://tool/L2/query_chart_gestalt',
} as const

type RequiredScuId = keyof typeof requiredBindings
type Door = 'portal' | 'managed_mcp' | 'raw_mcp'

function bindingExists(scuId: RequiredScuId, bindingId: string): boolean {
  return Boolean(snapshot.scus.find((scu) => scu.scu_id === scuId)?.bindings.some((binding) =>
    binding.binding_id === bindingId
    && binding.kind === 'registry_capability'
    && binding.executable
    && binding.execution_channels?.includes('platform_internal')))
}

function overlayFor(excluded?: RequiredScuId): ChartCapabilityOverlay {
  const available = Object.entries(requiredBindings)
    .filter(([scuId]) => scuId !== excluded)
    .map(([scuId, bindingId]) => ({ scu_id: scuId as RequiredScuId, binding_id: bindingId }))
  return {
    chart_id: chartId,
    overlay_version: stableFingerprint({ kind: 'c2-runtime-channel-coverage', available }),
    capability_compatibility_version: snapshot.compatibility_version,
    catalog_content_hash: snapshot.content_hash,
    build_id: 'c2-runtime-channel-coverage-build',
    code_revision: 'c2-fixture',
    writer_inventory_hash: null,
    generated_at: '2026-09-17T00:00:00.000Z',
    availability: available.map(({ scu_id, binding_id }) => ({
      scu_id,
      state: 'available' as const,
      build_status: 'completed',
      build_id: 'c2-runtime-channel-coverage-build',
      freshness: 'fixture-current',
      available_binding_ids: [binding_id],
      gaps: [],
      asset_receipts: [],
    })),
  }
}

function compileDoor(
  door: Door,
  scenario: (typeof BEYOND_ACARYA_ACCEPTANCE_CASES)[number],
  overlay = overlayFor(),
) {
  const executionChannel: ExecutionChannel = door === 'raw_mcp' ? 'mcp_full' : 'platform_internal'
  return compileInquiryContract({
    snapshot,
    overlay,
    chart_id: chartId,
    question: scenario.question,
    scope_tuple: scenario.scope_tuple,
    ai_proposal: scenario.ai_proposal,
    planning_budget: scenario.planning_budget,
    execution_channel: executionChannel,
    presentation_transport: door,
    temporal_anchor_date: temporalAnchorDate,
  })
}

function selectedItems(
  contract: ReturnType<typeof compileDoor>,
  scuId: RequiredScuId,
) {
  return contract.plan_items.filter((item) => item.scu_id === scuId)
}

describe('C2 runtime channel coverage', () => {
  it('uses reviewed internal registry bindings from the generated snapshot', () => {
    for (const [scuId, bindingId] of Object.entries(requiredBindings) as Array<[RequiredScuId, string]>) {
      expect(bindingExists(scuId, bindingId), `${scuId} must retain its reviewed internal registry binding`).toBe(true)
    }
  })

  it('compiles every frozen scenario through Portal, managed MCP and raw MCP with the same allowed retrieval projection', () => {
    const observedScus = new Set<RequiredScuId>()
    for (const scenario of BEYOND_ACARYA_ACCEPTANCE_CASES) {
      const contracts = (['portal', 'managed_mcp', 'raw_mcp'] as const)
        .map((door) => [door, compileDoor(door, scenario)] as const)
      const projections = contracts.map(([, contract]) => buildInquiryDoorParityProjection(contract))

      // Transport affects the immutable execution envelope, but neither the
      // requested scope nor the selected evidence plan.
      expect(contracts[0]![1].semantic_contract_hash).toBe(contracts[1]![1].semantic_contract_hash)
      expect(contracts[0]![1].semantic_contract_hash).toBe(contracts[2]![1].semantic_contract_hash)
      expect(projections[1]).toEqual(projections[0])
      expect(projections[2]).toEqual(projections[0])

      for (const [scuId, expectedBinding] of Object.entries(requiredBindings) as Array<[RequiredScuId, string]>) {
        const items = selectedItems(contracts[2]![1], scuId)
        if (items.length === 0) continue
        observedScus.add(scuId)
        expect(items).toEqual(expect.arrayContaining([
          expect.objectContaining({ state: 'ready', binding_id: expectedBinding }),
        ]))
        expect(items.every((item) => item.state !== 'ready' || item.binding_id === expectedBinding)).toBe(true)
      }
    }
    expect([...observedScus].sort()).toEqual(Object.keys(requiredBindings).sort())
  })

  it('keeps a required evidence family dark on every door when its exact overlay contract is absent', () => {
    for (const [scuId] of Object.entries(requiredBindings) as Array<[RequiredScuId, string]>) {
      const scenario = BEYOND_ACARYA_ACCEPTANCE_CASES.find((candidate) =>
        candidate.expected_route_scu_ids.includes(scuId) || candidate.expected_required_scu_ids.includes(scuId))
      expect(scenario, `${scuId} must be exercised by a frozen scenario`).toBeDefined()
      for (const door of ['portal', 'managed_mcp', 'raw_mcp'] as const) {
        const items = selectedItems(compileDoor(door, scenario!, overlayFor(scuId)), scuId)
        expect(items.length, `${door}:${scuId} must be selected before availability is evaluated`).toBeGreaterThan(0)
        expect(items).toEqual(expect.arrayContaining([
          expect.objectContaining({ state: 'blocked', binding_id: null }),
        ]))
      }
    }
  })
})
