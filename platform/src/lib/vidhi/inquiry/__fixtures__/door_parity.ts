import snapshotJson from '@/generated/capability_knowledge.snapshot.json'
import type {
  CapabilityKnowledgeSnapshot,
  ChartCapabilityOverlay,
} from '@/lib/retrieval/registry/knowledge/types'
import { stableFingerprint } from '@/lib/retrieval/registry/knowledge/stable'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { compileInquiryContract } from '../compiler'
import { finalizeInquiryContract, recordInquiryExecution } from '../compiler'
import { bindingForInquiryItem, managedPlanToAiInquiryProposal } from '../managed_bridge'
import { classifyInquiryResult, deriveInquiryPaginationReceipt } from '../pagination'
import { buildInquiryDoorParityProjection } from '../door_parity'

export const W5_DOOR_PARITY_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
export const W5_DOOR_PARITY_QUESTION = 'Assess wealth through the reviewed cross-door evidence surface.'
export const W5_DOOR_PARITY_SCOPE = {
  intent: 'domain_assessment',
  domains: ['wealth'],
  width: 'standard',
  depth: 'standard',
  horizon: 'present',
  intervention: 'none',
  entitlement: 'native',
} as const

const generated = snapshotJson as CapabilityKnowledgeSnapshot
const sharedScus = generated.scus.filter((scu) => scu.bindings.some((binding) =>
  binding.executable
  && binding.execution_channels?.includes('platform_internal')
  && binding.execution_channels.includes('mcp_full')))
const sharedIds = new Set(sharedScus.map((scu) => scu.scu_id))

export const W5_DOOR_PARITY_CHANNEL_COUNTS = {
  platform: generated.scus.flatMap((scu) => scu.bindings).filter((binding) =>
    binding.executable && binding.execution_channels?.includes('platform_internal')).length,
  shared: sharedScus.flatMap((scu) => scu.bindings).filter((binding) =>
    binding.executable
    && binding.execution_channels?.includes('platform_internal')
    && binding.execution_channels.includes('mcp_full')).length,
} as const

/** Real generated declarations only: this fixture never fabricates channel authority. */
export const W5_DOOR_PARITY_SNAPSHOT: CapabilityKnowledgeSnapshot = {
  ...generated,
  content_hash: stableFingerprint({ fixture: 'wave5-reviewed-cross-door', scus: sharedScus }),
  scus: sharedScus,
  edges: generated.edges.filter((edge) => sharedIds.has(edge.from_scu_id) && sharedIds.has(edge.to_scu_id)),
}

export const W5_DOOR_PARITY_OVERLAY: ChartCapabilityOverlay = {
  chart_id: W5_DOOR_PARITY_CHART_ID,
  overlay_version: stableFingerprint({ fixture: 'wave5-reviewed-cross-door-overlay' }),
  capability_compatibility_version: W5_DOOR_PARITY_SNAPSHOT.compatibility_version,
  catalog_content_hash: W5_DOOR_PARITY_SNAPSHOT.content_hash,
  build_id: 'build-wave5-reviewed-cross-door',
  code_revision: 'wave5-local-fixture',
  writer_inventory_hash: null,
  generated_at: '2026-09-15T00:00:00.000Z',
  availability: sharedScus.map((scu) => ({
    scu_id: scu.scu_id,
    state: 'available' as const,
    build_status: 'completed',
    build_id: 'build-wave5-reviewed-cross-door',
    freshness: 'fixture-current',
    available_binding_ids: scu.bindings.filter((binding) => binding.executable
      && binding.execution_channels?.includes('platform_internal')
      && binding.execution_channels.includes('mcp_full')).map((binding) => binding.binding_id),
    gaps: [],
    asset_receipts: [],
  })),
}

export function w5DoorParityPlan(): PipelinePlan {
  return {
    query_class: 'holistic',
    query_intent_summary: '',
    asset_bundle: [],
    domains: ['wealth'],
    forward_looking: false,
    tool_calls: [],
    scope_tuple: W5_DOOR_PARITY_SCOPE,
    history_mode: 'synthesized',
    expected_output_shape: 'structured_data',
  } as unknown as PipelinePlan
}

export function compileW5DoorParityContract(executionChannel: 'platform_internal' | 'mcp_full') {
  const plan = w5DoorParityPlan()
  return compileInquiryContract({
    snapshot: W5_DOOR_PARITY_SNAPSHOT,
    overlay: W5_DOOR_PARITY_OVERLAY,
    chart_id: W5_DOOR_PARITY_CHART_ID,
    question: W5_DOOR_PARITY_QUESTION,
    scope_tuple: W5_DOOR_PARITY_SCOPE,
    ai_proposal: managedPlanToAiInquiryProposal(plan),
    execution_channel: executionChannel,
  })
}

export function w5DoorParityToolResult(toolName: string, args: Readonly<Record<string, unknown>>) {
  const offset = typeof args.offset === 'number' ? args.offset : 0
  const moreAvailable = offset === 0
  return {
    tool_bundle_id: `fixture:${toolName}`,
    tool_name: toolName,
    tool_version: 'wave5-fixture-v1',
    invocation_params: args,
    results: [{ content: JSON.stringify({
      rows: [{ id: moreAvailable ? 'page-1' : 'page-2', value: 'shared-evidence' }],
      total_matching: moreAvailable ? 2 : 2,
      more_available: moreAvailable,
    }) }],
    served_from_cache: false,
    latency_ms: 0,
    result_hash: stableFingerprint({ toolName, args, moreAvailable }),
    schema_version: '1.0',
  }
}

export function expectedW5DoorParityProjection(executionChannel: 'platform_internal' | 'mcp_full') {
  let contract = compileW5DoorParityContract(executionChannel)
  // The evidence stage dispatches every initially authorized item in pass one,
  // then follows only observed continuation items. Mirror that ordering here so
  // the shared fixture projects the real managed route rather than a serial
  // one-item-at-a-time approximation.
  for (const item of [...contract.plan_items]) {
    if (item.state !== 'ready' || !item.binding_id) continue
    const binding = bindingForInquiryItem(W5_DOOR_PARITY_SNAPSHOT, contract, item.item_id)
    if (!binding) continue
    const toolName = item.binding_id.replace(/^registry:/, '')
    const raw = w5DoorParityToolResult(toolName, item.args)
    contract = recordInquiryExecution(contract, {
      item_id: item.item_id,
      disposition: classifyInquiryResult(binding, raw),
      evidence_refs: [`retrieval:${toolName}:pass-1:${stableFingerprint(raw)}`],
      pagination: deriveInquiryPaginationReceipt(binding, raw, item.args),
      request_position_path: binding.pagination_contract?.request_position_path,
    })
  }
  let pass = 2
  while (contract.iteration < contract.max_iterations) {
    const item = contract.plan_items.find((candidate) => candidate.state === 'ready' && candidate.observation !== null)
    if (!item?.binding_id) break
    const binding = bindingForInquiryItem(W5_DOOR_PARITY_SNAPSHOT, contract, item.item_id)
    if (!binding) break
    const toolName = item.binding_id.replace(/^registry:/, '')
    const raw = w5DoorParityToolResult(toolName, item.args)
    contract = recordInquiryExecution(contract, {
      item_id: item.item_id,
      disposition: classifyInquiryResult(binding, raw),
      evidence_refs: [`retrieval:${toolName}:pass-${pass}:${stableFingerprint(raw)}`],
      pagination: deriveInquiryPaginationReceipt(binding, raw, item.args),
      request_position_path: binding.pagination_contract?.request_position_path,
    })
    pass += 1
  }
  return buildInquiryDoorParityProjection(finalizeInquiryContract(contract))
}
