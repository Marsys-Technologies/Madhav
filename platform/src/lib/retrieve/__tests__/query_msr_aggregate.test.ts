import { describe, it, expect } from 'vitest'

import { tool } from '../query_msr_aggregate'
import type { QueryPlan } from '../types'

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000007',
  query_text: 'Compare across natives',
  query_class: 'cross_native',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_msr_aggregate'],
  history_mode: 'research',
  panel_mode: false,
  expected_output_shape: 'structured_data',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

describe('query_msr_aggregate tool', () => {
  it('returns ToolBundle without throwing', async () => {
    await expect(tool.retrieve(basePlan)).resolves.toBeDefined()
  })

  it('result has status multi_native_not_deployed in content', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(1)
    const parsed = JSON.parse(bundle.results[0].content)
    expect(parsed.status).toBe('multi_native_not_deployed')
  })

  it('result content includes the query_class from the plan', async () => {
    const bundle = await tool.retrieve(basePlan)

    const parsed = JSON.parse(bundle.results[0].content)
    expect(parsed.query_class).toBe('cross_native')
  })

  it('result includes a human-readable message', async () => {
    const bundle = await tool.retrieve(basePlan)

    const parsed = JSON.parse(bundle.results[0].content)
    expect(typeof parsed.message).toBe('string')
    expect(parsed.message.length).toBeGreaterThan(0)
  })

  it('latency_ms is a non-negative number', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.latency_ms).toBeGreaterThanOrEqual(0)
  })

  it('schema_version is 1.0', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.schema_version).toBe('1.0')
  })

  it('served_from_cache is false', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.served_from_cache).toBe(false)
  })

  it('tool_name is query_msr_aggregate', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('query_msr_aggregate')
  })

  it('result signal_id is multi_native_not_deployed', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results[0].signal_id).toBe('multi_native_not_deployed')
  })

  it('result source_canonical_id is SYSTEM', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results[0].source_canonical_id).toBe('SYSTEM')
  })

  it('does not have cache_key property', async () => {
    const bundle = await tool.retrieve(basePlan)

    expect(bundle).not.toHaveProperty('cache_key')
  })
})
