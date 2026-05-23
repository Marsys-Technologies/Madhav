/**
 * tier_catalog.test.ts — MCPT v3.2 Phase 6b: Snapshot tests for getCatalogForTier.
 *
 * Verifies the three tier behaviors:
 *   client      — ops tools hidden; synthesis tools present unchanged
 *   acharya     — full catalog; synthesis tools annotated with review note
 *   super_admin — full catalog; synthesis tools annotated with server-side note
 *
 * Handler behavior invariant: descriptions vary, but handler references are
 * NOT touched by getCatalogForTier (it only operates on ToolCatalogEntry arrays,
 * which have no handler field). The handler-unchanged guarantee is architectural —
 * registerHolisticBundle and registerMultiSchoolBundle only accept a description
 * override; they always use the same async handler closure.
 */

import { describe, it, expect } from 'vitest'
import { getCatalogForTier, OPS_TOOLS, SYNTHESIS_TOOLS } from '../src/tools/tier_catalog.js'
import { CATALOG } from '../src/tools/catalog.js'
import type { ToolCatalogEntry } from '../src/tools/catalog.js'

// ── Fixtures ─────────────────────────────────────────────────────────────────

/** Full 22-tool catalog as ALL_TOOLS. */
const ALL_TOOLS: ToolCatalogEntry[] = CATALOG

// ── Client tier ───────────────────────────────────────────────────────────────

describe('getCatalogForTier — client tier', () => {
  const catalog = getCatalogForTier('client', ALL_TOOLS)
  const names = catalog.map(t => t.name)

  it('hides data_coverage', () => {
    expect(names).not.toContain('data_coverage')
  })

  it('hides tool_health', () => {
    expect(names).not.toContain('tool_health')
  })

  it('hides log_prediction', () => {
    expect(names).not.toContain('log_prediction')
  })

  it('hides record_outcome', () => {
    expect(names).not.toContain('record_outcome')
  })

  it('hides flag_disagreement', () => {
    expect(names).not.toContain('flag_disagreement')
  })

  it('hides all OPS_TOOLS entries', () => {
    for (const opsTool of OPS_TOOLS) {
      expect(names, `client catalog must not contain ops tool "${opsTool}"`).not.toContain(opsTool)
    }
  })

  it('retains chart_summary', () => {
    expect(names).toContain('chart_summary')
  })

  it('retains holistic_bundle', () => {
    expect(names).toContain('holistic_bundle')
  })

  it('retains multi_school_bundle', () => {
    expect(names).toContain('multi_school_bundle')
  })

  it('retains all surgical primitives', () => {
    const surgicals = [
      'query_chart_facts', 'query_signals', 'query_dasha_periods', 'query_panchanga',
      'query_ephemeris', 'query_transit_event', 'lel_query', 'vector_search',
      'get_cgm_subgraph', 'cross_school_lookup', 'read_asset', 'read_classical_text',
    ]
    for (const s of surgicals) {
      expect(names, `client catalog must retain surgical tool "${s}"`).toContain(s)
    }
  })

  it('retains observability tools', () => {
    expect(names).toContain('get_trace')
    expect(names).toContain('list_recent_queries')
  })

  it('returns 17 tools (22 - 5 ops)', () => {
    expect(catalog).toHaveLength(ALL_TOOLS.length - OPS_TOOLS.size)
  })

  it('holistic_bundle description is unchanged (no tier annotation for client)', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    const base = ALL_TOOLS.find(t => t.name === 'holistic_bundle')
    expect(holistic?.description).toBe(base?.description)
  })

  it('chart_summary is first in the catalog', () => {
    expect(catalog[0].name).toBe('chart_summary')
  })
})

// ── Acharya tier ──────────────────────────────────────────────────────────────

describe('getCatalogForTier — acharya tier', () => {
  const catalog = getCatalogForTier('acharya', ALL_TOOLS)
  const names = catalog.map(t => t.name)

  it('returns full catalog (22 tools)', () => {
    expect(catalog).toHaveLength(ALL_TOOLS.length)
  })

  it('retains all ops tools', () => {
    for (const opsTool of OPS_TOOLS) {
      expect(names, `acharya catalog must retain ops tool "${opsTool}"`).toContain(opsTool)
    }
  })

  it('annotates holistic_bundle with Acharya-review-grade note', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    expect(holistic?.description).toContain('Acharya-review-grade')
  })

  it('annotates multi_school_bundle with Acharya-review-grade note', () => {
    const multi = catalog.find(t => t.name === 'multi_school_bundle')
    expect(multi?.description).toContain('Acharya-review-grade')
  })

  it('annotates holistic_bundle with "Use to verify the fact layer"', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    expect(holistic?.description).toContain('Use to verify the fact layer.')
  })

  it('does NOT annotate chart_summary', () => {
    const cs = catalog.find(t => t.name === 'chart_summary')
    expect(cs?.description).not.toContain('Acharya-review-grade')
  })

  it('does NOT annotate surgical primitives', () => {
    const qcf = catalog.find(t => t.name === 'query_chart_facts')
    expect(qcf?.description).not.toContain('Acharya-review-grade')
  })

  it('annotation does not break the base description', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    const base = ALL_TOOLS.find(t => t.name === 'holistic_bundle')
    // Base description is a prefix of the annotated one
    expect(holistic?.description).toMatch(new RegExp(`^${escapeRegex(base?.description ?? '')}`))
  })

  it('chart_summary is first in the catalog', () => {
    expect(catalog[0].name).toBe('chart_summary')
  })

  it('synthesis tools appear before ops tools', () => {
    const holisticIdx = names.indexOf('holistic_bundle')
    const dataCovIdx = names.indexOf('data_coverage')
    expect(holisticIdx).toBeLessThan(dataCovIdx)
  })
})

// ── Super-admin tier ──────────────────────────────────────────────────────────

describe('getCatalogForTier — super_admin tier', () => {
  const catalog = getCatalogForTier('super_admin', ALL_TOOLS)
  const names = catalog.map(t => t.name)

  it('returns full catalog (22 tools)', () => {
    expect(catalog).toHaveLength(ALL_TOOLS.length)
  })

  it('retains all ops tools', () => {
    for (const opsTool of OPS_TOOLS) {
      expect(names, `super_admin catalog must retain ops tool "${opsTool}"`).toContain(opsTool)
    }
  })

  it('annotates holistic_bundle with Server-side synthesized note', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    expect(holistic?.description).toContain('Server-side synthesized')
  })

  it('annotates multi_school_bundle with Server-side synthesized note', () => {
    const multi = catalog.find(t => t.name === 'multi_school_bundle')
    expect(multi?.description).toContain('Server-side synthesized')
  })

  it('annotates holistic_bundle with prefer chart_summary hint', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    expect(holistic?.description).toContain('prefer chart_summary')
  })

  it('does NOT annotate chart_summary', () => {
    const cs = catalog.find(t => t.name === 'chart_summary')
    expect(cs?.description).not.toContain('Server-side synthesized')
  })

  it('does NOT use Acharya-review-grade for super_admin', () => {
    for (const entry of catalog) {
      expect(entry.description).not.toContain('Acharya-review-grade')
    }
  })

  it('annotation does not break the base description', () => {
    const holistic = catalog.find(t => t.name === 'holistic_bundle')
    const base = ALL_TOOLS.find(t => t.name === 'holistic_bundle')
    expect(holistic?.description).toMatch(new RegExp(`^${escapeRegex(base?.description ?? '')}`))
  })

  it('chart_summary is first in the catalog', () => {
    expect(catalog[0].name).toBe('chart_summary')
  })
})

// ── Handler behavior invariant ────────────────────────────────────────────────

describe('Handler behavior unchanged across tiers', () => {
  it('getCatalogForTier only touches descriptions — no handler field on ToolCatalogEntry', () => {
    // ToolCatalogEntry has only { name, description }. There is no handler field.
    // This confirms getCatalogForTier cannot alter handler behavior structurally.
    const adminCatalog = getCatalogForTier('super_admin', ALL_TOOLS)
    const clientCatalog = getCatalogForTier('client', ALL_TOOLS)
    const acharyaCatalog = getCatalogForTier('acharya', ALL_TOOLS)

    for (const entry of [...adminCatalog, ...clientCatalog, ...acharyaCatalog]) {
      expect(Object.keys(entry).sort()).toEqual(['description', 'name'])
    }
  })

  it('holistic_bundle description varies between acharya and super_admin (annotations differ)', () => {
    const acharyaDesc = getCatalogForTier('acharya', ALL_TOOLS).find(t => t.name === 'holistic_bundle')?.description
    const adminDesc = getCatalogForTier('super_admin', ALL_TOOLS).find(t => t.name === 'holistic_bundle')?.description
    expect(acharyaDesc).not.toBe(adminDesc)
  })

  it('holistic_bundle base description is identical across tiers (description is append-only)', () => {
    const base = ALL_TOOLS.find(t => t.name === 'holistic_bundle')!.description
    const tiers = ['client', 'acharya', 'super_admin']
    for (const tier of tiers) {
      const cat = getCatalogForTier(tier, ALL_TOOLS)
      const entry = cat.find(t => t.name === 'holistic_bundle')
      if (entry) {
        expect(entry.description.startsWith(base)).toBe(true)
      }
    }
  })
})

// ── Ordering invariant ────────────────────────────────────────────────────────

describe('Catalog ordering', () => {
  it('chart_summary is always first for non-client tiers', () => {
    for (const tier of ['acharya', 'super_admin']) {
      const catalog = getCatalogForTier(tier, ALL_TOOLS)
      expect(catalog[0].name, `${tier}: chart_summary must be first`).toBe('chart_summary')
    }
  })

  it('chart_summary is first for client tier', () => {
    const catalog = getCatalogForTier('client', ALL_TOOLS)
    expect(catalog[0].name).toBe('chart_summary')
  })

  it('synthesis tools come after surgical primitives', () => {
    for (const tier of ['client', 'acharya', 'super_admin']) {
      const catalog = getCatalogForTier(tier, ALL_TOOLS)
      const names = catalog.map(t => t.name)
      const qcfIdx = names.indexOf('query_chart_facts')
      const holisticIdx = names.indexOf('holistic_bundle')
      expect(holisticIdx, `${tier}: holistic_bundle must come after query_chart_facts`).toBeGreaterThan(qcfIdx)
    }
  })

  it('SYNTHESIS_TOOLS set contains holistic_bundle and multi_school_bundle', () => {
    expect(SYNTHESIS_TOOLS.has('holistic_bundle')).toBe(true)
    expect(SYNTHESIS_TOOLS.has('multi_school_bundle')).toBe(true)
  })
})

// ── Edge cases ────────────────────────────────────────────────────────────────

describe('Edge cases', () => {
  it('unknown tier falls back to full catalog with no annotations', () => {
    const catalog = getCatalogForTier('unknown_tier', ALL_TOOLS)
    // No ops tools hidden, no annotations
    expect(catalog).toHaveLength(ALL_TOOLS.length)
    for (const entry of catalog) {
      expect(entry.description).not.toContain('Acharya-review-grade')
      expect(entry.description).not.toContain('Server-side synthesized')
    }
  })

  it('empty allTools returns empty array for any tier', () => {
    expect(getCatalogForTier('client', [])).toHaveLength(0)
    expect(getCatalogForTier('super_admin', [])).toHaveLength(0)
  })

  it('tools not in CANONICAL_ORDER are appended at the end', () => {
    const extraTool: ToolCatalogEntry = { name: 'future_tool', description: 'What it does: future. When to prefer: always.' }
    const withExtra = [...ALL_TOOLS, extraTool]
    const catalog = getCatalogForTier('super_admin', withExtra)
    expect(catalog[catalog.length - 1].name).toBe('future_tool')
  })

  it('does not mutate the input allTools array', () => {
    const copy = ALL_TOOLS.map(t => ({ ...t }))
    getCatalogForTier('acharya', copy)
    for (let i = 0; i < copy.length; i++) {
      expect(copy[i].description).toBe(ALL_TOOLS[i].description)
    }
  })
})

// ── Utility ───────────────────────────────────────────────────────────────────

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
