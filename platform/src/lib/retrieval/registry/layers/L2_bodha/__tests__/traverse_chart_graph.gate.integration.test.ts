/**
 * @integration-test
 *
 * traverse_chart_graph.gate.integration.test.ts — R5 W2 GATE MEASUREMENT (live DB).
 * ====================================================================================
 * The W2 gate: "a '10th-lord→Moon' graph path resolves in ONE call" on BOTH canonical
 * charts (native 482012f1, Abhinandan 1c826d5a). This calls the REAL capability handler
 * exactly once per chart with about_from/about_to address expressions — no separate
 * resolve-then-traverse round trip — and asserts a real path was found.
 *
 * Gated on DB_AVAILABLE (same pattern as address_resolver.integration.test.ts). Run:
 *   DATABASE_URL=postgresql://user:pass@host:port/db vitest run --testPathPattern=traverse_chart_graph.gate
 */

import { describe, it, expect } from 'vitest'
import { traverseChartGraphCapability } from '../traverse_chart_graph'

const DB_AVAILABLE = !!(process.env.DB_URL || process.env.DATABASE_URL)
const maybeDescribe = DB_AVAILABLE ? describe : describe.skip

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

maybeDescribe('traverse_chart_graph — W2 gate: 10th-lord -> Moon path, ONE call, live DB', () => {

  it('native chart (482012f1): resolves in exactly one handler call, path found', async () => {
    const t0 = performance.now()
    const result = await traverseChartGraphCapability.handler(
      {
        chart_id: NATIVE_CHART_ID,
        mode: 'paths',
        about_from: 'lord_of(bhava 10)',
        about_to: { type: 'graha', graha: 'Moon' },
        direction: 'directed',
      },
      undefined
    )
    const elapsedMs = performance.now() - t0
    console.log(`[GATE] native chart — latency ${elapsedMs.toFixed(1)}ms`)
    console.log(`[GATE] native chart — result:`, JSON.stringify(result.content, null, 2))

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['path_found']).toBe(true)
    expect((content['paths'] as unknown[]).length).toBeGreaterThan(0)
    expect(content['about_resolution']).toBeTruthy()
  }, 30_000)

  it('Abhinandan chart (1c826d5a): resolves in exactly one handler call, path found', async () => {
    const t0 = performance.now()
    const result = await traverseChartGraphCapability.handler(
      {
        chart_id: ABHINANDAN_CHART_ID,
        mode: 'paths',
        about_from: 'lord_of(bhava 10)',
        about_to: { type: 'graha', graha: 'Moon' },
        direction: 'directed',
      },
      undefined
    )
    const elapsedMs = performance.now() - t0
    console.log(`[GATE] Abhinandan chart — latency ${elapsedMs.toFixed(1)}ms`)
    console.log(`[GATE] Abhinandan chart — result:`, JSON.stringify(result.content, null, 2))

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['path_found']).toBe(true)
    expect((content['paths'] as unknown[]).length).toBeGreaterThan(0)
    expect(content['about_resolution']).toBeTruthy()
  }, 30_000)

  it('neighbors mode: about seed ("graha(Moon)") resolves and returns neighbors, native chart', async () => {
    const result = await traverseChartGraphCapability.handler(
      {
        chart_id: NATIVE_CHART_ID,
        mode: 'neighbors',
        about: ['graha(Moon)'],
        min_strength: 0.5,
      },
      undefined
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['about_resolution']).toBeTruthy()
    expect((content['nodes'] as unknown[]).length).toBeGreaterThan(0)
  }, 30_000)

})
