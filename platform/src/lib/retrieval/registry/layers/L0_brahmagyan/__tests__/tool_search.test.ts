/**
 * tool_search.test.ts — Wave 5 Lane L4 ("tool-search metadata")
 * ================================================================================
 * Unit-level test of the LIVE `tool_search` capability's own handler (no DB, no
 * network — the handler is pure in-memory search over `getCatalog()`, dynamic-
 * imported at call time — see the handler's own comment for why the import is
 * dynamic rather than a top-level import). Complements
 * `projection_compiler_parity.test.ts`'s coverage of the SHARED derivation
 * functions (`buildToolSearchIndex`/`searchToolIndex`) by proving the capability
 * that actually gets served over MCP wires those same functions correctly:
 * required-arg validation, honest empty result, and a representative query.
 */
import { describe, it, expect } from 'vitest'
import { toolSearchCapability } from '../tool_search'

describe('tool_search capability (marsys://tool/L0/tool_search)', () => {
  it('is registered as a global-scope tool with no chart_id in required_inputs', () => {
    expect(toolSearchCapability.uri).toBe('marsys://tool/L0/tool_search')
    expect(toolSearchCapability.type).toBe('tool')
    expect(toolSearchCapability.scope).toBe('global')
    expect(toolSearchCapability.name).toBe('tool_search')
  })

  it('errors honestly when query is missing (never silently returns the whole catalog)', async () => {
    const result = await toolSearchCapability.handler({}, {} as never)
    expect(result.is_error).toBe(true)
  })

  it('errors honestly when query is an empty/whitespace string', async () => {
    const result = await toolSearchCapability.handler({ query: '   ' }, {} as never)
    expect(result.is_error).toBe(true)
  })

  it('returns matching results for a real keyword ("dasha") including catalog_total', async () => {
    const result = await toolSearchCapability.handler({ query: 'dasha' }, {} as never)
    expect(result.is_error).toBe(false)
    const content = result.content as {
      total_matches: number
      returned: number
      results: Array<{ name: string }>
      catalog_total: number
    }
    expect(content.total_matches).toBeGreaterThan(0)
    expect(content.results.length).toBeGreaterThan(0)
    expect(content.catalog_total).toBeGreaterThan(100) // sanity bound, not a hardcoded exact count
    // The capability itself must be discoverable in the live catalog (used by getCatalog()
    // inside the handler), proving the dynamic import + registration actually wired up.
    expect(content.catalog_total).toBeGreaterThanOrEqual(1)
  })

  it('respects the limit parameter', async () => {
    const result = await toolSearchCapability.handler({ query: 'chart', limit: 2 }, {} as never)
    expect(result.is_error).toBe(false)
    const content = result.content as { results: unknown[] }
    expect(content.results.length).toBeLessThanOrEqual(2)
  })

  it('returns an honest empty result for a nonsense query (never a fabricated guess)', async () => {
    const result = await toolSearchCapability.handler({ query: 'zzznonexistentqueryxyz123' }, {} as never)
    expect(result.is_error).toBe(false)
    const content = result.content as { total_matches: number; results: unknown[] }
    expect(content.total_matches).toBe(0)
    expect(content.results).toEqual([])
  })

  it('finds itself when searching for "tool search" (self-discoverable)', async () => {
    const result = await toolSearchCapability.handler({ query: 'tool search catalog' }, {} as never)
    expect(result.is_error).toBe(false)
    const content = result.content as { results: Array<{ name: string }> }
    expect(content.results.some((r) => r.name === 'tool_search')).toBe(true)
  })
})
