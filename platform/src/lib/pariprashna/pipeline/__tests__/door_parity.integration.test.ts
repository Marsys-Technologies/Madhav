import { describe, expect, it, vi } from 'vitest'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import type { TurnParams } from '../stage_context'
import {
  expectedW5DoorParityProjection,
  W5_DOOR_PARITY_CHART_ID,
  W5_DOOR_PARITY_OVERLAY,
  W5_DOOR_PARITY_QUESTION,
  W5_DOOR_PARITY_SNAPSHOT,
  w5DoorParityPlan,
  w5DoorParityToolResult,
} from '@/lib/vidhi/inquiry/__fixtures__/door_parity'

vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  callPipelinePlanner: vi.fn(async () => ({ outcome: 'plan', plan: w5DoorParityPlan() })),
}))
vi.mock('@/lib/pipeline/budget_arbiter', () => ({
  arbitrateBudgets: (calls: unknown[]) => calls,
}))
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: () => ({ toolCalls: [], mappedPrimitives: [], unmappedPrimitives: [], compilerIntent: 'general_synthesis', compileFailed: false, llm_extension_note: '' }),
  ensureB11WholeChartReadFloor: () => false,
  ensureDashaContextFloor: () => false,
}))
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({
  filterLeakedCapabilities: (names: string[]) => names,
}))
vi.mock('@/lib/retrieval/orientation', () => ({ buildChartOrientation: async () => null }))
vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: async () => ({ fingerprint: 'wave5-door-parity-fixture' }),
}))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: async () => ({ assets: [], floor_enforced: false, total_bytes: 0, total_tokens: 0 }),
}))
vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: async () => 'wave5-fixture-model',
}))
vi.mock('@/lib/pariprashna/injection/flag', () => ({ isInjectionContainmentEnabled: () => false }))
vi.mock('@/lib/pariprashna/honest_controls/flag', () => ({ isHonestControlsEnabled: () => false }))
vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: () => W5_DOOR_PARITY_SNAPSHOT,
  getPinnedCapabilityKnowledgeSnapshot: () => W5_DOOR_PARITY_SNAPSHOT,
  loadChartCapabilityOverlay: async () => W5_DOOR_PARITY_OVERLAY,
}))
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: () => ({ display: { reader_label_key: 'examining_chart' } }),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  TOOL_NAME_TO_URI: {},
  resolveToolUri: (name: string) => name,
  getToolByName: (name: string) => ({
    name,
    version: 'wave5-fixture-v1',
    retrieve: async (_query: unknown, args: Record<string, unknown>) => w5DoorParityToolResult(name, args),
  }),
}))

const { runPlanStage } = await import('../plan_stage')
const { runEvidenceStage } = await import('../evidence_stage')
const { emitCompletenessReceipt } = await import('../receipt_stage')

function emitter(): { em: PariprashnaEmitter; grades: Array<Record<string, unknown>> } {
  const grades: Array<Record<string, unknown>> = []
  return {
    grades,
    em: new Proxy({}, {
      get: (_target, property: string) => (body: Record<string, unknown>) => {
        if (property === 'grade') grades.push(body)
      },
    }) as unknown as PariprashnaEmitter,
  }
}

describe('Wave 5 actual Portal door parity integration', () => {
  it('drives plan, paginated evidence and receipt stages to the shared exact projection', async () => {
    const { em, grades } = emitter()
    const request = new Request('http://localhost/api/pariprashna', { method: 'POST' })
    const planned = await runPlanStage({
      em,
      request,
      messages: [{ id: 'fixture-user', role: 'user', parts: [{ type: 'text', text: W5_DOOR_PARITY_QUESTION }] }],
      identity: {
        turnId: 'fixture-turn', queryId: 'fixture-query', conversationId: 'fixture-conversation',
        chartId: W5_DOOR_PARITY_CHART_ID, isFirstTurn: false,
      },
      params: {
        selectedStack: 'anthropic', modelId: 'wave5-fixture-model', modelMeta: { maxInputTokens: 128_000 },
        readingDepth: 'standard', deepDive: false, lengthTier: 'standard', lelContextEnabled: false, style: 'default',
      } as unknown as TurnParams,
      safetyDecision: { enforced: false } as never,
    })
    expect(planned.halted).toBe(false)
    if (planned.halted) return

    const evidence = await runEvidenceStage({
      em,
      request,
      chartId: W5_DOOR_PARITY_CHART_ID,
      userUid: 'fixture-principal',
      plan: planned.value.plan,
      queryPlan: planned.value.queryPlan,
      manifest: planned.value.manifest,
      toolsAuthorized: planned.value.toolsAuthorized,
      orientationPromise: planned.value.orientationPromise,
      inquiryContract: planned.value.inquiryContract,
    })
    const projection = emitCompletenessReceipt({
      em,
      completenessReceipt: evidence.completenessReceipt,
      inquiryContract: evidence.inquiryContract,
    })

    expect(projection).toEqual(expectedW5DoorParityProjection('platform_internal'))
    const emitted = grades.find((grade) => grade.subject === 'inquiry_door_parity')
    expect(JSON.parse(String(emitted?.detail))).toEqual(projection)
  })
})
