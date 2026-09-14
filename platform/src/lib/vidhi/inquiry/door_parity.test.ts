import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { compileChartCapabilityOverlay } from '../../retrieval/registry/knowledge/overlay'
import type { ChartCapabilityEvidence } from '../../retrieval/registry/knowledge/overlay'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import { bindingForInquiryItem } from './managed_bridge'
import {
  compileInquiryContract,
  failInquiryForOverlayDrift,
  finalizeInquiryContract,
  recordInquiryExecution,
} from './compiler'
import { buildInquiryDoorParityProjection } from './door_parity'
import type { InquiryContract } from './types'

const chartId = '482012f1-710e-4a25-994a-93821f5871aa'
const scope = {
  intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
  horizon: 'multi_year', intervention: false, entitlement: 'native',
} as const

const compiledSnapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-14T00:00:00.000Z')
const sharedScus = compiledSnapshot.scus.map((scu) => ({
  ...scu,
  bindings: scu.bindings.map((binding) => binding.executable && binding.kind === 'registry_capability'
    ? { ...binding, execution_channels: ['platform_internal', 'mcp_full'] as const }
    : binding),
}))
const snapshot = {
  ...compiledSnapshot,
  scus: sharedScus,
  content_hash: stableFingerprint({ fixture: 'wave5-three-door-shared', scus: sharedScus }),
}
const evidence: ChartCapabilityEvidence[] = snapshot.scus.flatMap((scu) => {
  const sharedBindings = scu.bindings.filter((binding) => binding.executable
    && binding.execution_channels?.includes('platform_internal')
    && binding.execution_channels.includes('mcp_full'))
  return sharedBindings.length ? [{
    scu_id: scu.scu_id,
    build_status: 'completed',
    build_id: 'build-parity',
    freshness: 'fixture-current',
    available_binding_ids: sharedBindings.map((binding) => binding.binding_id),
  }] : []
})
const overlay = compileChartCapabilityOverlay({
  snapshot,
  chart_id: chartId,
  build_id: 'build-parity',
  code_revision: 'wave5-local-fixture',
  evidence,
  generated_at: '2026-09-14T00:00:00.000Z',
})

function compileDoors(): Record<'portal' | 'managed_mcp' | 'raw_mcp', InquiryContract> {
  const common = {
    snapshot,
    overlay,
    chart_id: chartId,
    question: 'Give me a deep wealth outlook with mechanisms, yoga and timing.',
    scope_tuple: scope,
  }
  return {
    portal: compileInquiryContract({ ...common, execution_channel: 'platform_internal' }),
    managed_mcp: compileInquiryContract({ ...common, execution_channel: 'platform_internal' }),
    raw_mcp: compileInquiryContract({ ...common, execution_channel: 'mcp_full' }),
  }
}

function semanticPlan(contract: InquiryContract) {
  return contract.plan_items.map((item) => ({
    item_id: item.item_id,
    obligation_ids: item.obligation_ids,
    scu_id: item.scu_id,
    state: item.state,
  }))
}

function semanticObligations(contract: InquiryContract) {
  return contract.obligations.map((obligation) => ({
    obligation_id: obligation.obligation_id,
    source: obligation.source,
    materiality: obligation.materiality,
    scu_ids: obligation.scu_ids,
    disposition: obligation.disposition,
  }))
}

function executeFixture(contract: InquiryContract, door: string): InquiryContract {
  let current = contract
  const paginationItem = current.plan_items.find((item) => {
    const binding = bindingForInquiryItem(snapshot, current, item.item_id)
    return item.state === 'ready' && binding?.pagination_contract?.request_position_path
  })
  expect(paginationItem, `${door} must expose one source-reviewed continuation fixture`).toBeDefined()
  const binding = bindingForInquiryItem(snapshot, current, paginationItem!.item_id)!
  const positionPath = binding.pagination_contract!.request_position_path!
  const positionKey = positionPath.split('.').at(-1)!
  current = recordInquiryExecution(current, {
    item_id: paginationItem!.item_id,
    disposition: 'served',
    evidence_refs: [`${door}:${stableFingerprint({ page: 1, item_id: paginationItem!.item_id })}`],
    pagination: { semantics: binding.pagination, exhausted: false, next: 50 },
    request_position_path: positionPath,
  })
  expect(current.plan_items.find((item) => item.item_id === paginationItem!.item_id)?.args[positionKey])
    .toBe(50)
  current = recordInquiryExecution(current, {
    item_id: paginationItem!.item_id,
    disposition: 'served',
    evidence_refs: [`${door}:${stableFingerprint({ page: 2, item_id: paginationItem!.item_id })}`],
    pagination: { semantics: binding.pagination, exhausted: true, next: null },
    request_position_path: positionPath,
  })

  for (const item of current.plan_items.filter((candidate) => candidate.state === 'ready')) {
    const itemBinding = bindingForInquiryItem(snapshot, current, item.item_id)
    current = recordInquiryExecution(current, {
      item_id: item.item_id,
      disposition: 'served',
      evidence_refs: [`${door}:${stableFingerprint({ item_id: item.item_id })}`],
      pagination: { semantics: itemBinding?.pagination ?? 'none', exhausted: true, next: null },
      request_position_path: itemBinding?.pagination_contract?.request_position_path,
    })
  }
  return finalizeInquiryContract(current)
}

describe('Wave 5 three-door semantic parity', () => {
  it('proves three_door_equivalence for one pinned snapshot and shared availability overlay', () => {
    const doors = compileDoors()
    expect(doors.portal.semantic_contract_hash).toBe(doors.managed_mcp.semantic_contract_hash)
    expect(doors.portal.semantic_contract_hash).toBe(doors.raw_mcp.semantic_contract_hash)
    expect(semanticObligations(doors.portal)).toEqual(semanticObligations(doors.raw_mcp))
    expect(semanticPlan(doors.portal)).toEqual(semanticPlan(doors.raw_mcp))
    expect(doors.portal.execution_plan_hash).not.toBe(doors.raw_mcp.execution_plan_hash)
  })

  it('proves pagination_continuation without equating door-specific evidence references', () => {
    const completed = Object.entries(compileDoors()).map(([door, contract]) =>
      buildInquiryDoorParityProjection(executeFixture(contract, door)))
    expect(completed[1]).toEqual(completed[0])
    expect(completed[2]).toEqual(completed[0])
  })

  it('proves failure_state_parity when the pinned overlay changes', () => {
    const blocked = Object.values(compileDoors()).map((contract) =>
      buildInquiryDoorParityProjection(failInquiryForOverlayDrift(contract)))
    expect(blocked[0].status).toBe('BLOCKED')
    expect(blocked[1]).toEqual(blocked[0])
    expect(blocked[2]).toEqual(blocked[0])
  })

  it('fails parity when canonical evidence payload identities differ', () => {
    const complete = executeFixture(compileDoors().portal, 'portal')
    const changed: InquiryContract = {
      ...complete,
      obligations: complete.obligations.map((obligation, index) => index === 0
        ? { ...obligation, evidence_refs: [`raw:${stableFingerprint({ changed: true })}`] }
        : obligation),
    }
    expect(buildInquiryDoorParityProjection(changed).parity_hash)
      .not.toBe(buildInquiryDoorParityProjection(complete).parity_hash)
  })

  it('normalizes equivalent dispatch spellings without merging distinct failure classes', () => {
    const initial = compileDoors().portal
    const failed = (gap_reason: string): InquiryContract => finalizeInquiryContract(recordInquiryExecution(initial, {
      item_id: initial.plan_items.find((item) => item.state === 'ready')!.item_id,
      disposition: 'failed', evidence_refs: [], gap_reason,
      pagination: { semantics: 'none', exhausted: true, next: null },
    }))
    const dispatchA = buildInquiryDoorParityProjection(failed('dispatch_error'))
    const dispatchB = buildInquiryDoorParityProjection(failed('TOOL_DISPATCH_FAILED'))
    const resultLimit = buildInquiryDoorParityProjection(failed('RESULT_LIMIT_EXCEEDED'))
    const registry = buildInquiryDoorParityProjection(failed('registry_unresolvable'))
    const toolEnvelope = buildInquiryDoorParityProjection(failed('tool_failure_envelope'))

    expect(dispatchA).toEqual(dispatchB)
    expect(resultLimit.parity_hash).not.toBe(dispatchA.parity_hash)
    expect(registry.parity_hash).not.toBe(dispatchA.parity_hash)
    expect(toolEnvelope.parity_hash).not.toBe(dispatchA.parity_hash)
  })
})
