import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createToolCache } from '../tool_cache'
import { executeWithCache } from '../with_cache'
import type { QueryPlan, ToolBundle, RetrievalTool } from '../../retrieval/shared_types'

function makeQueryPlan(overrides: Partial<QueryPlan> = {}): QueryPlan {
  return {
    query_plan_id: 'plan-with-cache-test',
    query_text: 'Test query',
    query_class: 'interpretive',
    domains: ['psychology'],
    forward_looking: false,
    tools_authorized: ['mock_tool'],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'three_interpretation',
    manifest_fingerprint: 'sha256:test',
    schema_version: '1.0',
    ...overrides,
  }
}

function makeBundle(overrides: Partial<ToolBundle> = {}): ToolBundle {
  return {
    tool_bundle_id: 'bundle-wc-1',
    tool_name: 'mock_tool',
    tool_version: '1.0',
    invocation_params: {},
    results: [{ content: 'mock content' }],
    served_from_cache: false,
    cache_key: undefined,
    latency_ms: 8,
    result_hash: 'sha256:mockhash',
    schema_version: '1.0',
    ...overrides,
  }
}

function makeMockTool(): RetrievalTool {
  const bundle = makeBundle()
  return {
    name: 'mock_tool',
    version: '1.0',
    retrieve: vi.fn(() => Promise.resolve(bundle)),
  }
}

describe('executeWithCache', () => {
  describe('without cache', () => {
    it('calls tool.retrieve directly and returns the result', async () => {
      const tool = makeMockTool()
      const plan = makeQueryPlan()

      const result = await executeWithCache(tool, plan)

      expect(tool.retrieve).toHaveBeenCalledOnce()
      expect(tool.retrieve).toHaveBeenCalledWith(plan, undefined)
      expect(result.tool_bundle_id).toBe('bundle-wc-1')
    })

    it('does not set served_from_cache=true on direct call', async () => {
      const tool = makeMockTool()
      const result = await executeWithCache(tool, makeQueryPlan())
      // The raw bundle has served_from_cache: false; no cache to flip it
      expect(result.served_from_cache).toBe(false)
    })
  })

  describe('with cache — first call', () => {
    it('calls tool.retrieve and stores the promise', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()
      const plan = makeQueryPlan()

      await executeWithCache(tool, plan, cache)

      expect(tool.retrieve).toHaveBeenCalledOnce()
      expect(cache.size()).toBe(1)
    })

    it('served_from_cache is false on the first call', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()

      const result = await executeWithCache(tool, makeQueryPlan(), cache)
      expect(result.served_from_cache).toBe(false)
    })
  })

  describe('with cache — second identical call', () => {
    it('does not call tool.retrieve again', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()
      const plan = makeQueryPlan()

      await executeWithCache(tool, plan, cache)
      await executeWithCache(tool, plan, cache)

      expect(tool.retrieve).toHaveBeenCalledOnce()
    })

    it('served_from_cache is true on the second call', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()
      const plan = makeQueryPlan()

      await executeWithCache(tool, plan, cache)
      const result2 = await executeWithCache(tool, plan, cache)

      expect(result2.served_from_cache).toBe(true)
    })

    it('cache size stays at 1 for two identical calls', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()
      const plan = makeQueryPlan()

      await executeWithCache(tool, plan, cache)
      await executeWithCache(tool, plan, cache)

      expect(cache.size()).toBe(1)
    })
  })

  describe('cache key normalisation', () => {
    it('treats domain lists in different order as the same cache entry', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()

      const plan1 = makeQueryPlan({ domains: ['career', 'finance'] })
      const plan2 = makeQueryPlan({ domains: ['finance', 'career'] })

      await executeWithCache(tool, plan1, cache)
      await executeWithCache(tool, plan2, cache)

      // Only one retrieve call: the two plans are cache-equivalent
      expect(tool.retrieve).toHaveBeenCalledOnce()
      expect(cache.size()).toBe(1)
    })

    it('treats different query_class as different cache entries', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()

      const plan1 = makeQueryPlan({ query_class: 'factual' })
      const plan2 = makeQueryPlan({ query_class: 'predictive' })

      await executeWithCache(tool, plan1, cache)
      await executeWithCache(tool, plan2, cache)

      expect(tool.retrieve).toHaveBeenCalledTimes(2)
      expect(cache.size()).toBe(2)
    })

    it('treats different forward_looking as different cache entries', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()

      await executeWithCache(tool, makeQueryPlan({ forward_looking: false }), cache)
      await executeWithCache(tool, makeQueryPlan({ forward_looking: true }), cache)

      expect(tool.retrieve).toHaveBeenCalledTimes(2)
    })

    it('unique query_plan_id does not bust the cache', async () => {
      const tool = makeMockTool()
      const cache = createToolCache()

      await executeWithCache(tool, makeQueryPlan({ query_plan_id: 'id-aaa' }), cache)
      const result = await executeWithCache(
        tool,
        makeQueryPlan({ query_plan_id: 'id-bbb' }),
        cache,
      )

      // query_plan_id is excluded from cache key, so second call is a cache hit
      expect(tool.retrieve).toHaveBeenCalledOnce()
      expect(result.served_from_cache).toBe(true)
    })
  })
})
