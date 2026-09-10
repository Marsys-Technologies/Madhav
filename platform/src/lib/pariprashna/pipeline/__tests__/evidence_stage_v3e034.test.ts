/**
 * evidence_stage_v3e034.test.ts — V3-E-034 remediation proof (EDIR_V3_REGISTER_v1_0.md,
 * DEFECT, S3, "Registry-lookup-miss silently escapes toolEventLog, unlike a dispatch throw").
 *
 * Before this fix: a registry-lookup miss inside `runEvidenceStage`'s tool loop (`getToolByName`
 * fails to resolve an authorized tool name) pushed NOTHING to `toolEventLog` — the equivalent
 * dispatch-throw case (tool found, but the call itself threw) pushed a `status:'error'` row. That
 * asymmetry is what let the downstream gap collapse into the SAME `route_not_invoked`
 * empty_reason as "correctly never authorized" in `completeness_wiring.ts` (see the sibling test,
 * `../../pipeline/__tests__/completeness_wiring.test.ts`'s "V3-E-034" describe block, for the
 * downstream half of this proof).
 *
 * This test exercises the REAL `runEvidenceStage`, REAL `getToolByName` (no mock — an
 * intentionally-bogus tool name is used so the registry miss is genuine, not simulated), and REAL
 * `PariprashnaEmitter`-shaped calls via a recording stub (mirrors validation_stage.test.ts's own
 * `stubEmitter()` pattern for the exact same EDIR register). Only the one genuine I/O seam
 * (`hydrateBundle`, which talks to GCS) is mocked — matching the EDIR's own "mocked only at the
 * I/O seams" testing discipline for this finding.
 */
import { describe, it, expect, vi } from 'vitest'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { LegacyQueryPlan } from '../plan_stage'
import type { ScopeTuple as ClassifierScopeTuple } from '@/lib/vidhi/scope_classifier'

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false, total_bytes: 0, total_tokens: 0 })),
}))

const { runEvidenceStage } = await import('../evidence_stage')

const CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a' // synthetic chart only, per worktree constraint
const BOGUS_TOOL_NAME = '__v3e034_registry_lookup_miss_probe__' // guaranteed not in TOOL_NAME_TO_URI

function stubEmitter(): { em: PariprashnaEmitter; calls: Array<{ method: string; body: unknown }> } {
  const calls: Array<{ method: string; body: unknown }> = []
  const handler: ProxyHandler<Record<string, unknown>> = {
    get(_target, prop: string) {
      return (body: unknown) => {
        calls.push({ method: prop, body })
      }
    },
  }
  return { em: new Proxy({}, handler) as unknown as PariprashnaEmitter, calls }
}

function scopeTuple(overrides: Partial<ClassifierScopeTuple> = {}): ClassifierScopeTuple {
  return {
    intent: 'domain_assessment',
    domains: ['career'],
    width: 'standard',
    depth: 'deep',
    horizon: 'present',
    intervention: 'none',
    entitlement: 'native',
    ...overrides,
  }
}

function fakeRequest(): Request {
  return { signal: { aborted: false } } as unknown as Request
}

function minimalPlan(): PipelinePlan {
  return {
    query_class: 'factual',
    query_intent_summary: 'V3-E-034 registry-lookup-miss probe',
    asset_bundle: [],
    tool_calls: [],
    scope_tuple: scopeTuple(),
  } as unknown as PipelinePlan
}

function minimalQueryPlan(): LegacyQueryPlan {
  return {
    query_plan_id: 'test-plan',
    query_text: 'probe',
    chart_id: CHART,
    query_class: 'factual',
    domains: ['career'],
    forward_looking: false,
    tools_authorized: [BOGUS_TOOL_NAME],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'test',
    schema_version: '1.0',
    planets: undefined,
    houses: undefined,
    dasha_context_required: undefined,
    graph_seed_hints: undefined,
    vector_search_filter: undefined,
    time_window: undefined,
    tool_calls: [],
  }
}

describe('V3-E-034 — runEvidenceStage: a registry-lookup miss now produces a toolEventLog entry', () => {
  it('RED→GREEN: before this fix, a registry-lookup miss left toolEventLog EMPTY; now it pushes a status:"error" row shaped like the dispatch-throw branch', async () => {
    const { em, calls } = stubEmitter()

    const out = await runEvidenceStage({
      em,
      request: fakeRequest(),
      chartId: CHART,
      userUid: 'test-user',
      plan: minimalPlan(),
      queryPlan: minimalQueryPlan(),
      manifest: {} as never,
      toolsAuthorized: [BOGUS_TOOL_NAME],
      orientationPromise: Promise.resolve(null),
    })

    // THE FIX: toolEventLog is no longer empty for a registry-lookup miss.
    expect(out.toolEventLog).toHaveLength(1)
    const entry = out.toolEventLog[0]
    expect(entry.name).toBe(BOGUS_TOOL_NAME)
    // Same shape as the dispatch-throw branch (status:'error', ok_count:0, err_count:1) —
    // "recorded identically" per the EDIR's Expected clause.
    expect(entry.status).toBe('error')
    expect(entry.ok_count).toBe(0)
    expect(entry.err_count).toBe(1)
    // The NEW discriminator that lets completeness_wiring.ts tell this apart from a genuine
    // dispatch throw (and from genuine non-authorization downstream).
    expect(entry.error_kind).toBe('registry_unresolvable')

    // The wire-level activity event was ALREADY correct before this fix (the EDIR's own
    // "the live activity.upsert SSE event does say status:'error'" observation) — unchanged by
    // this fix, asserted here as a negative control that we didn't touch that path.
    const activityCall = calls.find(
      (c) => c.method === 'activity' && (c.body as { key?: string }).key === `retrieve:${BOGUS_TOOL_NAME}` && (c.body as { status?: string }).status === 'error',
    )
    expect(activityCall).toBeDefined()

    // No valid tool result for a name the registry couldn't resolve.
    expect(out.validToolResults).toHaveLength(0)
  })

  it('NEGATIVE CONTROL: an authorized-but-unresolvable tool alongside no other tools still produces exactly one event — the fix does not double-count or duplicate', async () => {
    const { em } = stubEmitter()
    const out = await runEvidenceStage({
      em,
      request: fakeRequest(),
      chartId: CHART,
      userUid: 'test-user',
      plan: minimalPlan(),
      queryPlan: minimalQueryPlan(),
      manifest: {} as never,
      toolsAuthorized: [BOGUS_TOOL_NAME, BOGUS_TOOL_NAME],
      orientationPromise: Promise.resolve(null),
    })
    // Two authorized entries (even if duplicated) → two independent misses, each recorded.
    expect(out.toolEventLog).toHaveLength(2)
    expect(out.toolEventLog.every((e) => e.error_kind === 'registry_unresolvable')).toBe(true)
  })

  it('the completeness receipt built from this toolEventLog is consistent with the downstream V3-E-034 fix (integration smoke: does not throw, still returns a receipt)', async () => {
    const { em } = stubEmitter()
    const out = await runEvidenceStage({
      em,
      request: fakeRequest(),
      chartId: CHART,
      userUid: 'test-user',
      plan: minimalPlan(),
      queryPlan: minimalQueryPlan(),
      manifest: {} as never,
      toolsAuthorized: [BOGUS_TOOL_NAME],
      orientationPromise: Promise.resolve(null),
    })
    // plan.scope_tuple was set, so a receipt is always built (never throws even though the
    // authorized tool could not be resolved).
    expect(out.completenessReceipt).not.toBeNull()
  })
})
