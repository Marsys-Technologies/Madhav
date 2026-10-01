/**
 * Registry-level Āyurdāya disclosure safety net (SS N-62 Q10).
 *
 * Generic readers (get_structural_signals, get_sensitive_points, get_strength, get_positions, …) take a
 * caller-supplied `categories` list into `fact_category = ANY(...)`, so `categories:['ayurdaya']` would
 * serve bare totals through them. registerCapability wraps every tool handler with a post-processor so
 * the disclosure travels on EVERY dispatch path, without editing each reader.
 */
import { describe, it, expect } from 'vitest'
import { registerCapability, getCapability } from '../index'
import type { CapabilityDescriptor } from '../types'

const BASE = 'base_only_haranas_deferred_to_w3'
const ayuRows = () => [
  { fact_id: 'a', fact_category: 'ayurdaya', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 98.7521, fact_value_jsonb: { method: 'pindayu', harana_status: BASE } },
  { fact_id: 'b', fact_category: 'ayurdaya', fact_subject: 'SAT', fact_key: 'pindayu_contribution_years', fact_value_num: 19.8649, fact_value_jsonb: { method: 'pindayu' } },
]

function fakeTool(uri: string, name: string, rowsFor: (args: Record<string, unknown>) => unknown[], overrides: Record<string, unknown> = {}): CapabilityDescriptor {
  return {
    uri, type: 'tool', layer: 'L1', name, description: 'fake generic category reader',
    input_schema: {}, required_inputs: [], scope: 'global', archetype: 'flat_fact', traversal_level: 'L-SIGNAL',
    tool_role: 'leaf', emits_references: false, lel_capable: false, grounds_to: {},
    handler: async (args: Record<string, unknown>) => ({ content: { chart_id: 'c', categories: args['categories'], rows: rowsFor(args), total: 2 }, is_error: false }),
    ...overrides,
  } as unknown as CapabilityDescriptor
}

describe('registerCapability — ayurdaya post-processor', () => {
  it("categories:['ayurdaya'] through a generic reader carries the disclosure; numbers unchanged", async () => {
    const cap = fakeTool('marsys://tool/L1/fake_generic_reader_a', 'fake_generic_reader_a', () => ayuRows())
    registerCapability(cap)
    const res = await getCapability(cap.uri)!.handler({ categories: ['ayurdaya'] }) as { content: Record<string, unknown>; judgment_flags: Array<Record<string, unknown>> }
    expect(Object.keys(res.content)[0]).toBe('ayurdaya_figure_disclosure')
    expect(res.content['ayurdaya_figure_disclosure']).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false })
    const rows = res.content['rows'] as Array<Record<string, unknown>>
    expect(rows[0]).toMatchObject({ fact_value_num: 98.7521, figure_kind: 'unreduced_base', reductions_applied: false })
    expect(rows[1]).toMatchObject({ fact_value_num: 19.8649, figure_kind: 'unreduced_base' })
    expect(res.judgment_flags.map(f => f['code'])).toEqual(['ayurdaya_unreduced_base_figures'])
    // the descriptor object handed to registerCapability is the one served (identity preserved)
    expect(getCapability(cap.uri)).toBe(cap)
  })

  it('leaves non-ayurdaya results untouched (same reference)', async () => {
    const payload = { content: { rows: [{ fact_category: 'graha_position', fact_key: 'sign' }] }, is_error: false }
    const cap = fakeTool('marsys://tool/L1/fake_generic_reader_b', 'fake_generic_reader_b', () => [], { handler: async () => payload })
    registerCapability(cap)
    expect(await getCapability(cap.uri)!.handler({})).toBe(payload)
  })

  it('re-registering the same descriptor does not double-wrap (one flag, one disclosure)', async () => {
    const cap = fakeTool('marsys://tool/L1/fake_generic_reader_c', 'fake_generic_reader_c', () => ayuRows())
    registerCapability(cap)
    registerCapability(cap)
    const res = await getCapability(cap.uri)!.handler({}) as unknown as { judgment_flags: unknown[] }
    expect(res.judgment_flags).toHaveLength(1)
  })

  it('re-registering leaves the registered handler identity unchanged (no second wrap)', () => {
    const cap = fakeTool('marsys://tool/L1/fake_generic_reader_e', 'fake_generic_reader_e', () => ayuRows())
    registerCapability(cap)
    const h1 = cap.handler
    expect(getCapability(cap.uri)!.handler).toBe(h1)
    registerCapability(cap)
    expect(cap.handler).toBe(h1)
    expect(getCapability(cap.uri)!.handler).toBe(h1)
  })

  it('does not mutate the handler-owned (possibly cached/shared) rows; flag present at content level too', async () => {
    const shared = { content: { rows: ayuRows() }, is_error: false }
    const cap = fakeTool('marsys://tool/L1/fake_generic_reader_f', 'fake_generic_reader_f', () => [], { handler: async () => shared })
    registerCapability(cap)
    const res = await getCapability(cap.uri)!.handler({}) as unknown as { content: Record<string, unknown> }
    expect(shared.content.rows.every(r => !('figure_kind' in r))).toBe(true)
    expect(Object.keys(shared.content)).toEqual(['rows'])
    expect((res.content['judgment_flags'] as Array<Record<string, unknown>>).map(f => f['code'])).toEqual(['ayurdaya_unreduced_base_figures'])
    // second call on the same shared object yields the same result (no accumulating state)
    const again = await getCapability(cap.uri)!.handler({}) as unknown as { content: Record<string, unknown> }
    expect(again.content['judgment_flags']).toHaveLength(1)
  })

  it('composed tools: an outer tool returning a subset of an inner tool\'s rows keeps the inner tags', async () => {
    const innerCap = fakeTool('marsys://tool/L1/fake_inner_reader', 'fake_inner_reader', () => ayuRows())
    registerCapability(innerCap)
    const outerCap = fakeTool('marsys://tool/L1/fake_outer_reader', 'fake_outer_reader', () => [], {
      handler: async () => {
        const inner = await getCapability(innerCap.uri)!.handler({}) as { content: { rows: Array<Record<string, unknown>> } }
        // outer keeps ONLY the contribution row (no total on its own page) and drops the inner disclosure
        return { content: { composed: { rows: [inner.content.rows[1]] } }, is_error: false }
      },
    })
    registerCapability(outerCap)
    const res = await getCapability(outerCap.uri)!.handler({}) as unknown as { content: Record<string, unknown> }
    const row = ((res.content['composed'] as Record<string, unknown>)['rows'] as Array<Record<string, unknown>>)[0]!
    expect(row['figure_kind']).toBe('unreduced_base') // inner confirmed it against its total; not recomputed to "unverified"
    expect(row['reductions_applied']).toBe(false)
    expect(res.content['ayurdaya_figure_disclosure']).toMatchObject({ figure_kind: 'unreduced_base', figure_counts: { unreduced_base: 1, reduction_status_unverified: 0 } })
  })

  it('calls the original handler with the descriptor as `this` and forwards args/ctx', async () => {
    let seen: { self: unknown; args: unknown; ctx: unknown } | null = null
    const cap = fakeTool('marsys://tool/L1/fake_generic_reader_d', 'fake_generic_reader_d', () => [], {
      handler: async function (this: unknown, args: Record<string, unknown>, ctx?: unknown) { seen = { self: this, args, ctx }; return { content: {}, is_error: false } },
    })
    registerCapability(cap)
    const ctx = { x: 1 }
    await getCapability(cap.uri)!.handler({ q: 1 }, ctx as never)
    expect(seen).toEqual({ self: cap, args: { q: 1 }, ctx })
  })

  it('does not wrap non-tool capabilities', async () => {
    const handler = async () => ({ content: { rows: ayuRows() }, is_error: false })
    const res = fakeTool('marsys://resource/L1/fake_res', 'fake_res', () => [], { type: 'resource', handler })
    registerCapability(res)
    expect(getCapability(res.uri)!.handler).toBe(handler)
  })
})
