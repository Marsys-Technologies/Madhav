/**
 * ucn_cdlm_rm_parametric_smoke — COV-S5 gate test
 *
 * Integration smoke tests for the three L2.5 file-based retrieval tools:
 *   - query_ucn_walk: extracts structural slices from UCN_v4_0.md
 *   - query_cdlm_lookup: looks up domain-pair cells in CDLM_v1_1.md
 *   - query_rm_walk: retrieves resonance entries from RM_v2_0.md
 *
 * These tests read the REAL Markdown files (no mocking).
 * Gate criteria: all 3 tools return non-empty results for known seeded entries.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { RETRIEVAL_TOOLS } from '@/lib/retrieve/index'
import type { QueryPlan } from '@/lib/retrieve/types'

const NEW_TOOLS = ['query_ucn_walk', 'query_cdlm_lookup', 'query_rm_walk']
const EXPECTED_MIN_TOTAL = 36

/** Minimal QueryPlan for testing — only required fields per types.ts */
function makeTestPlan(toolName: string, extra?: Record<string, unknown>): QueryPlan {
  return {
    query_plan_id: 'test-cov-s5-123',
    query_text: 'test query',
    query_class: 'factual',
    domains: [],
    forward_looking: false,
    audience_tier: 'super_admin',
    tools_authorized: [toolName],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'test-fingerprint',
    schema_version: '1.0',
    ...extra,
  }
}

describe('ucn_cdlm_rm_parametric_smoke — COV-S5 L2.5 structural retrieval tools', () => {

  // ── Registry checks ──────────────────────────────────────────────────────

  it(`RETRIEVAL_TOOLS contains at least ${EXPECTED_MIN_TOTAL} tools (33 existing + 3 new)`, () => {
    expect(RETRIEVAL_TOOLS.length).toBeGreaterThanOrEqual(EXPECTED_MIN_TOTAL)
  })

  it.each(NEW_TOOLS)('RETRIEVAL_TOOLS contains %s', (toolName) => {
    const found = RETRIEVAL_TOOLS.find(t => t.name === toolName)
    expect(found, `${toolName} not found in RETRIEVAL_TOOLS`).toBeDefined()
  })

  it.each(NEW_TOOLS)('%s has name, version, description, and retrieve function', (toolName) => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === toolName)!
    expect(typeof t.name).toBe('string')
    expect(typeof t.version).toBe('string')
    expect(typeof t.retrieve).toBe('function')
    expect(typeof t.description).toBe('string')
    expect((t.description ?? '').length).toBeGreaterThan(20)
  })

  // ── Manifest checks ──────────────────────────────────────────────────────

  it('manifest_overrides.yaml has entries for all 3 new tools', () => {
    const overridesPath = resolve(__dirname, '../../../00_ARCHITECTURE/manifest_overrides.yaml')
    const content = readFileSync(overridesPath, 'utf-8')
    for (const toolName of NEW_TOOLS) {
      expect(content).toContain(`tool_name: "${toolName}"`)
    }
  })

  it.each(NEW_TOOLS)('%s is marked expose_to_planner: true in manifest_overrides', (toolName) => {
    const overridesPath = resolve(__dirname, '../../../00_ARCHITECTURE/manifest_overrides.yaml')
    const content = readFileSync(overridesPath, 'utf-8')
    const idx = content.indexOf(`tool_name: "${toolName}"`)
    expect(idx).toBeGreaterThan(-1)
    const slice = content.slice(idx, idx + 2000)
    expect(slice).toContain('expose_to_planner: true')
  })

  it.each(NEW_TOOLS)('%s is marked layer: L2.5 in manifest_overrides', (toolName) => {
    const overridesPath = resolve(__dirname, '../../../00_ARCHITECTURE/manifest_overrides.yaml')
    const content = readFileSync(overridesPath, 'utf-8')
    const idx = content.indexOf(`tool_name: "${toolName}"`)
    expect(idx).toBeGreaterThan(-1)
    const slice = content.slice(idx, idx + 2000)
    expect(slice).toContain('layer: "L2.5"')
  })

  // ── Live retrieval smoke tests ─────────────────────────────────────────────

  it('query_ucn_walk with seed "Mercury" returns non-empty results (reads real UCN file)', async () => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === 'query_ucn_walk')!
    expect(t).toBeDefined()

    const plan = makeTestPlan('query_ucn_walk')
    const bundle = await t.retrieve(plan, { seed: 'Mercury', max_chars: 2000, part: 'all' })

    expect(bundle.tool_name).toBe('query_ucn_walk')
    expect(bundle.results.length).toBeGreaterThan(0)
    expect(bundle.results[0].content.length).toBeGreaterThan(0)
    expect(bundle.results[0].content.toLowerCase()).toContain('mercury')

    // Log first 200 chars for CI visibility
    console.log('[query_ucn_walk] First 200 chars:', bundle.results[0].content.slice(0, 200))
  })

  it('query_cdlm_lookup with domain_from="D1", domain_to="D2" returns non-empty results (reads real CDLM file)', async () => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === 'query_cdlm_lookup')!
    expect(t).toBeDefined()

    const plan = makeTestPlan('query_cdlm_lookup')
    const bundle = await t.retrieve(plan, { domain_from: 'D1', domain_to: 'D2' })

    expect(bundle.tool_name).toBe('query_cdlm_lookup')
    expect(bundle.results.length).toBeGreaterThan(0)
    expect(bundle.results[0].content.length).toBeGreaterThan(0)
    // Should contain the cell label or related content
    expect(bundle.results[0].content).toContain('CDLM.D1.D2')

    console.log('[query_cdlm_lookup] First 200 chars:', bundle.results[0].content.slice(0, 200))
  })

  it('query_rm_walk with rm_seed="RM.1" returns non-empty results (reads real RM file)', async () => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === 'query_rm_walk')!
    expect(t).toBeDefined()

    const plan = makeTestPlan('query_rm_walk')
    const bundle = await t.retrieve(plan, { rm_seed: 'RM.1', max_chars: 2000 })

    expect(bundle.tool_name).toBe('query_rm_walk')
    expect(bundle.results.length).toBeGreaterThan(0)
    expect(bundle.results[0].content.length).toBeGreaterThan(0)
    expect(bundle.results[0].signal_id).toBe('RM.01')

    console.log('[query_rm_walk] First 200 chars:', bundle.results[0].content.slice(0, 200))
  })

  // ── Additional integration coverage ──────────────────────────────────────

  it('query_ucn_walk with part="I" restricts search to Part I', async () => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === 'query_ucn_walk')!
    const plan = makeTestPlan('query_ucn_walk')
    const bundle = await t.retrieve(plan, { seed: 'Mercury', part: 'I' })
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('query_cdlm_lookup resolves domain names to IDs (career → D1)', async () => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === 'query_cdlm_lookup')!
    const plan = makeTestPlan('query_cdlm_lookup')
    const bundle = await t.retrieve(plan, { domain_from: 'career', domain_to: 'wealth' })
    // Should produce same result as D1→D2
    expect(bundle.results.length).toBeGreaterThan(0)
    expect(bundle.results[0].content).toContain('CDLM.D1.D2')
  })

  it('query_rm_walk with keyword seed returns matching RM sections', async () => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === 'query_rm_walk')!
    const plan = makeTestPlan('query_rm_walk')
    const bundle = await t.retrieve(plan, { rm_seed: 'Saturn', max_chars: 3000 })
    expect(bundle.results.length).toBeGreaterThan(0)
    for (const r of bundle.results) {
      expect(r.content.toLowerCase()).toContain('saturn')
    }
  })
})
