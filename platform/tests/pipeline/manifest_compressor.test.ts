import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  PRIMARY_TOOL_NAMES,
  DESCRIPTION_MAX_WORDS,
  MANIFEST_TOKEN_BUDGET,
  compressManifest,
  compressedManifestToString,
  estimateTokens,
  type CapabilityManifest,
  type CapabilityManifestEntry,
  type CompressedEntry,
} from '@/lib/pipeline/manifest_compressor'

function loadLiveManifest(): CapabilityManifest {
  const path = resolve(__dirname, '../../../00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  return JSON.parse(readFileSync(path, 'utf-8')) as CapabilityManifest
}

describe('manifest_compressor — expose_to_planner projection (COV-S3)', () => {
  it('only returns entries where expose_to_planner === true', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    // All returned entries must come from manifest entries with expose_to_planner=true
    const exposedNames = new Set(
      manifest.entries.filter((e) => e.expose_to_planner && e.tool_name).map((e) => e.tool_name!),
    )
    for (const entry of entries) {
      expect(exposedNames.has(entry.t)).toBe(true)
    }
  })

  it('live manifest returns at least 5 entries (the 5 tools updated with expose_to_planner=true)', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    expect(entries.length).toBeGreaterThanOrEqual(5)
  })

  it('every returned entry has all 5 fields populated', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    for (const entry of entries) {
      expect(typeof entry.t).toBe('string')
      expect(entry.t.length).toBeGreaterThan(0)
      expect(typeof entry.d).toBe('string')
      expect(Array.isArray(entry.p)).toBe(true)
      expect(['low', 'med', 'hi']).toContain(entry.c)
      expect(typeof entry.a).toBe('string')
    }
  })

  it(`description is ≤${DESCRIPTION_MAX_WORDS} words for every entry`, () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    for (const entry of entries) {
      const wordCount = entry.d.split(/\s+/).filter(Boolean).length
      expect(wordCount).toBeLessThanOrEqual(DESCRIPTION_MAX_WORDS)
    }
  })

  it(`serialised output stays within MANIFEST_TOKEN_BUDGET (${MANIFEST_TOKEN_BUDGET} tokens)`, () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    const out = compressedManifestToString(entries)
    expect(estimateTokens(out)).toBeLessThanOrEqual(MANIFEST_TOKEN_BUDGET)
  })

  it('compressedManifestToString is deterministic', () => {
    const manifest = loadLiveManifest()
    const a = compressedManifestToString(compressManifest(manifest))
    const b = compressedManifestToString(compressManifest(manifest))
    expect(a).toBe(b)

    const entries: CompressedEntry[] = compressManifest(manifest)
    const reversed = [...entries].reverse()
    expect(compressedManifestToString(reversed)).toBe(compressedManifestToString(entries))
  })

  it('CapabilityManifestEntry accepts COV-S1 extension fields (type-check)', () => {
    const entry: CapabilityManifestEntry = {
      canonical_id: 'TEST',
      expose_to_planner: true,
      output_schema: { type: 'object' },
      linked_data_asset_ids: ['MSR_v3_0', 'UCN_v4_0'],
      examples: [{ query: 'What is the lagna?', expected_plan_fragment: 'msr_sql(domains=["lagna"])' }],
      gating_constraints: [{ condition: 'date_required', action: 'require_date_param' }],
    }
    expect(entry.expose_to_planner).toBe(true)
    expect(entry.linked_data_asset_ids).toHaveLength(2)
    expect(entry.examples).toHaveLength(1)
    expect(entry.gating_constraints).toHaveLength(1)
  })

  it('skips entries without tool_name and entries where expose_to_planner is false/missing', () => {
    const synthetic: CapabilityManifest = {
      entries: [
        {
          canonical_id: 'X',
          tool_name: 'msr_sql',
          expose_to_planner: true,
          tool_description: 'MSR signal retrieval from Cloud SQL for domain and entity queries.',
          query_schema: { type: 'object', properties: { domains: {}, planets: {} } },
          token_cost_hint: 'hi',
          linked_data_asset_id: 'MSR_v3_0',
        },
        {
          canonical_id: 'Y',
          tool_name: 'hidden_tool',
          expose_to_planner: false,
          query_schema: { type: 'object', properties: { foo: {} } },
          token_cost_hint: 'low',
          linked_data_asset_id: 'NONE',
        },
        {
          canonical_id: 'Z',
          tool_name: 'no_flag_tool',
          // expose_to_planner missing → treated as false
          query_schema: { type: 'object', properties: { bar: {} } },
          token_cost_hint: 'low',
        },
        {
          canonical_id: 'W',
          // no tool_name → ignored
          expose_to_planner: true,
        },
      ],
    }
    const entries = compressManifest(synthetic)
    expect(entries).toHaveLength(1)
    expect(entries[0].t).toBe('msr_sql')
    expect(entries[0].p).toEqual(['domains', 'planets'])
  })

  it('PRIMARY_TOOL_NAMES is still exported (backward compat for golden regression baselines)', () => {
    expect(Array.isArray(PRIMARY_TOOL_NAMES)).toBe(true)
    expect(PRIMARY_TOOL_NAMES.length).toBeGreaterThan(0)
  })
})
