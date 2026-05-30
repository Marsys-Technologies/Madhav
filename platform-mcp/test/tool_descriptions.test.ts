/**
 * tool_descriptions.test.ts — F.3 acceptance: enum-derived tool descriptions.
 *
 * Asserts that every advertised category in query_chart_facts is present in
 * CHART_FACTS_CATEGORIES (which mirrors ChartFactsCategory from the platform).
 *
 * MCPT v3.1.0-S1 AC.S1.3
 *
 * MCPT v3.2 Phase 3: Added lint gate for all tool descriptions.
 * Every tool description must:
 *   - Start with a disambiguator sentence (What it does / Returns / FIRST CALL when)
 *   - Contain "When to prefer:"
 *   - Be ≤ 1200 characters
 */

import { describe, it, expect } from 'vitest'
import { CHART_FACTS_CATEGORIES } from '../src/tools/query_chart_facts.js'
import { buildToolDescription } from '../src/tools/description_builder.js'
import { CATALOG } from '../src/tools/catalog.js'

// Canonical ChartFactsCategory values from platform/src/lib/retrieve/chart_facts_query.ts:21–30
// Kept here as ground-truth for the assertion; update both when the platform enum changes.
const PLATFORM_ENUM_CATEGORIES = [
  'house', 'dasha_chara', 'planet', 'dasha_vimshottari', 'saham',
  'sensitive_point', 'birth_metadata', 'strength_extra', 'yoga',
  'dasha_yogini', 'deity_assignment', 'shadbala', 'ashtakavarga_sav',
  'kp_cusp', 'navatara', 'panchang', 'cusp', 'arudha_occupancy',
  'bhava_bala', 'chandra_placement', 'mrityu_bhaga', 'longevity_indicator',
  'arudha', 'aspect', 'chalit_shift', 'kp_planet', 'special_lagna',
  'strength', 'upagraha', 'ashtakavarga_bav', 'kakshya_zone',
  'mercury_convergence', 'ashtakavarga_pinda', 'ishta_kashta',
  'kp_significator', 'varshphal', 'avastha',
] as const

describe('F.3 — Enum-derived tool descriptions', () => {
  it('CHART_FACTS_CATEGORIES matches the platform ChartFactsCategory enum exactly', () => {
    const mcpSet = new Set(CHART_FACTS_CATEGORIES)
    const platformSet = new Set(PLATFORM_ENUM_CATEGORIES)

    // Every MCP-advertised category must exist in the platform enum
    for (const cat of mcpSet) {
      expect(
        platformSet.has(cat as string),
        `MCP advertises category "${cat}" that is NOT in the platform enum`
      ).toBe(true)
    }

    // Every platform enum value must be advertised by the MCP tool
    for (const cat of platformSet) {
      expect(
        mcpSet.has(cat as string),
        `Platform enum has category "${cat}" that is NOT advertised by the MCP tool`
      ).toBe(true)
    }
  })

  it('CHART_FACTS_CATEGORIES has no duplicates', () => {
    const seen = new Set<string>()
    for (const cat of CHART_FACTS_CATEGORIES) {
      expect(seen.has(cat), `Duplicate category: "${cat}"`).toBe(false)
      seen.add(cat)
    }
  })

  it('buildToolDescription includes all categories in the output string', () => {
    const desc = buildToolDescription({
      baseDescription: 'Test tool.',
      enumSource: ['alpha', 'beta', 'gamma'],
      coverageHint: '3 items',
    })
    expect(desc).toContain('alpha')
    expect(desc).toContain('beta')
    expect(desc).toContain('gamma')
    expect(desc).toContain('3 items')
  })

  it('buildToolDescription works without coverageHint', () => {
    const desc = buildToolDescription({
      baseDescription: 'Test tool.',
      enumSource: ['x', 'y'],
    })
    expect(desc).toContain('x')
    expect(desc).toContain('y')
    expect(typeof desc).toBe('string')
    expect(desc.length).toBeGreaterThan(10)
  })
})

describe('MCPT v3.2 Phase 3 — Tool description lint gate', () => {
  it('CATALOG covers all tools', () => {
    const actualCount = CATALOG.length
    expect(actualCount).toBeGreaterThanOrEqual(22)
    const names = CATALOG.map(t => t.name)
    // Spot-check a representative from each tier
    expect(names).toContain('chart_summary')
    expect(names).toContain('holistic_bundle')
    expect(names).toContain('query_chart_facts')
    expect(names).toContain('read_asset')
    expect(names).toContain('get_trace')
    expect(names).toContain('log_prediction')
    expect(names).toContain('flag_disagreement')
  })

  it('every description starts with a disambiguator sentence', () => {
    for (const tool of CATALOG) {
      const first = tool.description.split('. ')[0]
      expect(
        first,
        `${tool.name}: first sentence must start with "What it does:", "Returns", or "FIRST CALL when"`
      ).toMatch(/^(What it does|FIRST CALL when|Returns)/)
    }
  })

  it('every description is ≤ 1200 characters', () => {
    for (const tool of CATALOG) {
      expect(
        tool.description.length,
        `${tool.name}: description is ${tool.description.length} chars (limit: 1200)`
      ).toBeLessThanOrEqual(1200)
    }
  })

  it('every description contains "When to prefer"', () => {
    for (const tool of CATALOG) {
      expect(
        tool.description,
        `${tool.name}: description must contain "When to prefer"`
      ).toMatch(/When to prefer/)
    }
  })

  it('no description is empty', () => {
    for (const tool of CATALOG) {
      expect(tool.description.length, `${tool.name}: description is empty`).toBeGreaterThan(50)
    }
  })
})
