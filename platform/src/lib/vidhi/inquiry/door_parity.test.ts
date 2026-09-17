import { describe, expect, it } from 'vitest'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import { bindingForInquiryItem } from './managed_bridge'
import {
  failInquiryForOverlayDrift,
  finalizeInquiryContract,
  recordInquiryExecution,
} from './compiler'
import { buildInquiryDoorParityProjection } from './door_parity'
import type { InquiryContract } from './types'
import {
  compileW5DoorParityContract,
  W5_DOOR_PARITY_CHANNEL_COUNTS,
  W5_DOOR_PARITY_SNAPSHOT as snapshot,
} from './__fixtures__/door_parity'

function compileDoors(): Record<'portal' | 'managed_mcp' | 'raw_mcp', InquiryContract> {
  return {
    portal: compileW5DoorParityContract('platform_internal'),
    managed_mcp: compileW5DoorParityContract('platform_internal'),
    raw_mcp: compileW5DoorParityContract('mcp_full'),
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
  it('detects the representative current-catalog channel gap instead of relabeling it parity', () => {
    expect(W5_DOOR_PARITY_CHANNEL_COUNTS.shared).toBeGreaterThan(0)
    expect(W5_DOOR_PARITY_CHANNEL_COUNTS.shared).toBeLessThan(W5_DOOR_PARITY_CHANNEL_COUNTS.platform)
  })

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

  it('keeps distinct unresolved binding argument sets non-equivalent', () => {
    const initial = compileDoors().portal
    const failed = (gap_reason: string): InquiryContract => finalizeInquiryContract(recordInquiryExecution(initial, {
      item_id: initial.plan_items.find((item) => item.state === 'ready')!.item_id,
      disposition: 'failed', evidence_refs: [], gap_reason,
      pagination: { semantics: 'none', exhausted: true, next: null },
    }))
    const questionMissing = buildInquiryDoorParityProjection(failed(
      'Required binding arguments are unresolved: question.',
    ))
    const queryMissing = buildInquiryDoorParityProjection(failed(
      'Required binding arguments are unresolved: query.',
    ))
    expect(questionMissing.parity_hash).not.toBe(queryMissing.parity_hash)
  })

  it('does not hide scope, date, omission, or completion differences behind a transport projection', () => {
    const initial = compileDoors().portal
    const baseline = buildInquiryDoorParityProjection(initial)
    const firstItem = initial.plan_items[0]!
    const changedScope: InquiryContract = {
      ...initial,
      scope_tuple: { ...initial.scope_tuple, horizon: 'multi_year' },
    }
    const changedDate: InquiryContract = {
      ...initial,
      plan_items: initial.plan_items.map((item, index) => index === 0 ? {
        ...item,
        authorization_args: { ...(item.authorization_args ?? item.args), as_of_date: '2030-01-01' },
      } : item),
    }
    const changedOmission: InquiryContract = {
      ...initial,
      omission_findings: [{
        rule_id: 'PARITY-OMISSION', severity: 'material', missing_scu_id: firstItem.scu_id,
        rationale: 'Synthetic parity regression.', source: 'rule', relation: null, source_ref: 'test:parity',
      }],
    }
    const changedCompletion: InquiryContract = {
      ...initial,
      iteration: initial.iteration + 1,
      status_reasons: ['different completion state'],
    }

    expect(buildInquiryDoorParityProjection(changedScope).parity_hash).not.toBe(baseline.parity_hash)
    expect(buildInquiryDoorParityProjection(changedDate).parity_hash).not.toBe(baseline.parity_hash)
    expect(buildInquiryDoorParityProjection(changedOmission).parity_hash).not.toBe(baseline.parity_hash)
    expect(buildInquiryDoorParityProjection(changedCompletion).parity_hash).not.toBe(baseline.parity_hash)
  })
})
