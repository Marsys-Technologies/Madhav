/**
 * RIR-S6/S7: tool_registration tests
 * [BUILD-ORCH-RIR-S6, RIR-S7]
 */

import { describe, it, expect } from 'vitest'
import {
  generateToolDescription,
  specToManifestEntry,
  toolDescription,
  type ToolRegistrationSpec,
} from '../tool_registration'

const EXAMPLE_SPEC: ToolRegistrationSpec = {
  tool_name: 'query_chart_facts',
  asset_id: 'A3',
  brief_description: 'Retrieve chart facts by category from chart_facts table.',
  llm_description: `USE WHEN: User asks about planet positions, house cusps, yogas, dasha periods, or any quantitative chart datum.
DO NOT use for: panchanga (use query_panchanga), remedies (use query_remedial_mantras).
Always pass ayanamsha_id matching the active ayanamsha.`,
  params: [
    { name: 'chart_id', type: 'string', required: true, description: 'UUID of the chart', example: 'aaaaaaaa-0000-...' },
    { name: 'category', type: 'string', required: true, description: 'Fact category', enum: ['planet', 'house', 'yoga', 'shadbala'] },
    { name: 'limit', type: 'number', required: false, description: 'Max rows', default: 20 },
  ],
  channels: ['portal', 'mcp', 'consume_hybrid'],
  min_tier: 'client',
  requires_chart_id: true,
  ayanamsha_sensitive: true,
  few_shot_example: {
    query: 'Where is the Sun in my chart?',
    call: { chart_id: 'xxx', category: 'planet', limit: 10 },
    expected_output_summary: 'List of planet placements including Sun sign, house, nakshatra.',
  },
}

describe('generateToolDescription', () => {
  it('includes tool name and brief description', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('query_chart_facts')
    expect(desc).toContain('Retrieve chart facts by category')
  })

  it('includes LLM description', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('USE WHEN')
    expect(desc).toContain('panchanga')
  })

  it('lists required parameters', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('chart_id')
    expect(desc).toContain('required')
    expect(desc).toContain('category')
  })

  it('shows parameter enum values', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('planet')
    expect(desc).toContain('yoga')
  })

  it('shows default value for optional params', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('20') // default limit
  })

  it('includes routing notes when chart_id required', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('Requires chart_id')
  })

  it('includes ayanamsha note for sensitive tools', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('ayanamsha')
  })

  it('includes few-shot example', () => {
    const desc = generateToolDescription(EXAMPLE_SPEC)
    expect(desc).toContain('Where is the Sun')
    expect(desc).toContain('Expected:' === '' ? '' : 'Returns:')
  })

  it('toolDescription is an alias for generateToolDescription', () => {
    expect(toolDescription(EXAMPLE_SPEC)).toBe(generateToolDescription(EXAMPLE_SPEC))
  })
})

describe('specToManifestEntry', () => {
  it('returns correct tool_name and asset_id', () => {
    const entry = specToManifestEntry(EXAMPLE_SPEC)
    expect(entry.tool_name).toBe('query_chart_facts')
    expect(entry.asset_id).toBe('A3')
  })

  it('includes channels', () => {
    const entry = specToManifestEntry(EXAMPLE_SPEC)
    expect(entry.channels).toContain('mcp')
    expect(entry.channels).toContain('portal')
  })

  it('sets requires_chart_id correctly', () => {
    const entry = specToManifestEntry(EXAMPLE_SPEC)
    expect(entry.requires_chart_id).toBe(true)
  })

  it('sets ayanamsha_sensitive correctly', () => {
    const entry = specToManifestEntry(EXAMPLE_SPEC)
    expect(entry.ayanamsha_sensitive).toBe(true)
  })

  it('includes a description_hash string', () => {
    const entry = specToManifestEntry(EXAMPLE_SPEC)
    expect(typeof entry.description_hash).toBe('string')
    expect(entry.description_hash.length).toBeGreaterThan(0)
  })

  it('produces stable hash for same spec', () => {
    const e1 = specToManifestEntry(EXAMPLE_SPEC)
    const e2 = specToManifestEntry(EXAMPLE_SPEC)
    expect(e1.description_hash).toBe(e2.description_hash)
  })

  it('produces different hash when description changes', () => {
    const modified = { ...EXAMPLE_SPEC, brief_description: 'Different description here.' }
    const e1 = specToManifestEntry(EXAMPLE_SPEC)
    const e2 = specToManifestEntry(modified)
    expect(e1.description_hash).not.toBe(e2.description_hash)
  })
})
