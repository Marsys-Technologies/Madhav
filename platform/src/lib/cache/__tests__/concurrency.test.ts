/**
 * Concurrency / promise-coalescing test for RequestScopedToolCache.
 *
 * The critical invariant: two concurrent calls with identical params must
 * share ONE promise so the underlying tool executes EXACTLY ONCE.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createToolCache } from '../tool_cache'
import { executeWithCache } from '../with_cache'
import type { QueryPlan, ToolBundle, RetrievalTool } from '../../retrieval/shared_types'

function makeQueryPlan(overrides: Partial<QueryPlan> = {}): QueryPlan {
  return {
    query_plan_id: 'plan-concurrent-test',
    query_text: 'Test query',
    query_class: 'factual',
    domains: ['career'],
    forward_looking: false,
    tools_authorized: ['mock_tool'],
    history_mode: 'synthesized',
    panel_mode: true,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'sha256:test',
    schema_version: '1.0',
    ...overrides,
  }
}

function makeBundle(callIndex: number): ToolBundle {
  return {
    tool_bundle_id: `bundle-${callIndex}`,
    tool_name: 'mock_tool',
    tool_version: '1.0',
    invocation_params: {},
    results: [{ content: `result from call ${callIndex}` }],
    served_from_cache: false,
    cache_key: undefined,
    latency_ms: 10,
    result_hash: `sha256:call${callIndex}`,
    schema_version: '1.0',
  }
}

describe('Promise coalescing under concurrency', () => {
  let callCount: number

  beforeEach(() => {
    callCount = 0
  })

  function makeMockTool(delayMs = 10): RetrievalTool {
    return {
      name: 'mock_tool',
      version: '1.0',
      retrieve: vi.fn((_plan: QueryPlan): Promise<ToolBundle> => {
        const index = ++callCount
        return new Promise((resolve) =>
          setTimeout(() => resolve(makeBundle(index)), delayMs),
        )
      }),
    }
  }

  it('calls retrieve exactly once when two concurrent calls share the same params', async () => {
    const cache = createToolCache()
    const tool = makeMockTool(10)
    const plan = makeQueryPlan()

    const [result1, result2] = await Promise.all([
      executeWithCache(tool, plan, cache),
      executeWithCache(tool, plan, cache),
    ])

    // Tool must have been called exactly once
    expect(callCount).toBe(1)
    expect(tool.retrieve).toHaveBeenCalledTimes(1)

    // Both callers get the same bundle content
    expect(result1.tool_bundle_id).toBe(result2.tool_bundle_id)
    expect(result1.results[0].content).toBe(result2.results[0].content)
  })

  it('calls retrieve twice when two concurrent calls have different params', async () => {
    const cache = createToolCache()
    const tool = makeMockTool(10)

    const plan1 = makeQueryPlan({ query_class: 'factual', domains: ['career'] })
    const plan2 = makeQueryPlan({ query_class: 'predictive', domains: ['finance'] })

    const [result1, result2] = await Promise.all([
      executeWithCache(tool, plan1, cache),
      executeWithCache(tool, plan2, cache),
    ])

    expect(callCount).toBe(2)
    expect(tool.retrieve).toHaveBeenCalledTimes(2)
    expect(result1.tool_bundle_id).not.toBe(result2.tool_bundle_id)
  })

  it('subsequent sequential call after coalescing is served from cache (one more retrieve call)', async () => {
    const cache = createToolCache()
    const tool = makeMockTool(10)
    const plan = makeQueryPlan()

    // Two concurrent calls — coalesced to one retrieve
    await Promise.all([
      executeWithCache(tool, plan, cache),
      executeWithCache(tool, plan, cache),
    ])
    expect(callCount).toBe(1)

    // Third call after the promise has settled — still served from the cached promise
    const result3 = await executeWithCache(tool, plan, cache)
    expect(callCount).toBe(1) // still only one retrieve call total
    expect(result3.served_from_cache).toBe(true)
  })
})
