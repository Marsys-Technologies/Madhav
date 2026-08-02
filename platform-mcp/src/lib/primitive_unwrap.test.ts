/**
 * primitive_unwrap.test.ts — pins the WIRE SHAPE of /api/mcp/primitives/<tool>.
 *
 * This is the test that was missing when the lattice/parihāra substrate shipped:
 * every prior mock used the flat (already-unwrapped) shape, so code reading
 * `envelope.result.<key>` passed unit tests while always reading `undefined` in
 * production (same failure mode PR #823 documented for fetchReadingSupplements).
 *
 * The fixtures here are byte-faithful to what `tool_name_bridge.ts`'s
 * `capabilityResultToToolBundle` → `toToolBundleResults` branch 3 ("Single
 * ToolResult") actually produces: `results: [{ content: JSON.stringify(payload) }]`.
 */

import { describe, it, expect } from 'vitest'
import { unwrapPrimitiveResult, unwrapFailureReason } from './primitive_unwrap.js'

/** Byte-faithful production wrapper: toToolBundleResults branch 3. */
export function toolBundleResult(payload: Record<string, unknown>): Record<string, unknown> {
  return {
    tool_bundle_id: 'tb-test-1',
    tool_name: 'test_tool',
    results: [{ content: JSON.stringify(payload) }],
    result_hash: 'sha256:test',
    duration_ms: 1,
  }
}

describe('unwrapPrimitiveResult — production ToolBundle shape', () => {
  it('recovers the capability payload from results[0].content as a JSON string', () => {
    const payload = { rows: [{ factor_family: 'vara', factor_key: 'ravivara' }], count: 1 }
    const { payload: out, failure } = unwrapPrimitiveResult(toolBundleResult(payload))
    expect(failure).toBeNull()
    expect(out).toEqual(payload)
  })

  it('NEVER finds the payload at envelope.result.<key> (the misread this fix removes)', () => {
    // Sanity pin: the wrapper itself does not carry the payload keys.
    const bundle = toolBundleResult({ rows: [1, 2, 3] })
    expect((bundle as { rows?: unknown }).rows).toBeUndefined()
    expect((bundle as { parihara_rules?: unknown }).parihara_rules).toBeUndefined()
  })

  it('tolerates bridge drift where content arrives already parsed as an object', () => {
    const { payload, failure } = unwrapPrimitiveResult({
      tool_bundle_id: 'tb',
      results: [{ content: { rows: [] } }],
    })
    expect(failure).toBeNull()
    expect(payload).toEqual({ rows: [] })
  })

  it('passes a direct-object result through unchanged (non-bundle shape)', () => {
    const direct = { rows: [{ a: 1 }] }
    const { payload, failure } = unwrapPrimitiveResult(direct)
    expect(failure).toBeNull()
    expect(payload).toBe(direct)
  })
})

describe('unwrapPrimitiveResult — wrapper-shape drift is HONEST failure, never silent empty', () => {
  it('null / non-object result → result_not_object', () => {
    expect(unwrapPrimitiveResult(null).failure).toBe('result_not_object')
    expect(unwrapPrimitiveResult(undefined).failure).toBe('result_not_object')
    expect(unwrapPrimitiveResult('str').failure).toBe('result_not_object')
    expect(unwrapPrimitiveResult([1]).failure).toBe('result_not_object')
  })

  it('ToolBundle-marked wrapper with no results array → results_missing (not a direct payload)', () => {
    const { payload, failure } = unwrapPrimitiveResult({ tool_bundle_id: 'tb', tool_name: 'x' })
    expect(failure).toBe('results_missing')
    expect(payload).toBeNull()
  })

  it('empty results array → results_empty', () => {
    const { payload, failure } = unwrapPrimitiveResult({ results: [] })
    expect(failure).toBe('results_empty')
    expect(payload).toBeNull()
  })

  it('results[0] without a content field → content_missing', () => {
    expect(unwrapPrimitiveResult({ results: [{}] }).failure).toBe('content_missing')
    expect(unwrapPrimitiveResult({ results: [null] }).failure).toBe('content_missing')
  })

  it('non-JSON string content → content_not_json', () => {
    const { payload, failure } = unwrapPrimitiveResult({ results: [{ content: 'not json {{' }] })
    expect(failure).toBe('content_not_json')
    expect(payload).toBeNull()
  })

  it('JSON but non-object content → payload_not_object', () => {
    expect(unwrapPrimitiveResult({ results: [{ content: '"just a string"' }] }).failure).toBe('payload_not_object')
    expect(unwrapPrimitiveResult({ results: [{ content: '[1,2]' }] }).failure).toBe('payload_not_object')
    expect(unwrapPrimitiveResult({ results: [{ content: 42 }] }).failure).toBe('payload_not_object')
  })
})

describe('unwrapFailureReason', () => {
  it('names the tool, the cause, and states this is NOT empty data', () => {
    const reason = unwrapFailureReason('query_parihara_graph', 'content_not_json')
    expect(reason).toContain('query_parihara_graph')
    expect(reason).toContain('content_not_json')
    expect(reason).toMatch(/not as empty data/i)
  })
})
