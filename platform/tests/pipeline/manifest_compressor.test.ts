import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  PRIMARY_TOOL_NAMES,
  compressManifest,
  compressedManifestToString,
  estimateTokens,
  type CapabilityManifest,
  type CompressedEntry,
} from '@/lib/pipeline/manifest_compressor'

function loadLiveManifest(): CapabilityManifest {
  const path = resolve(__dirname, '../../../00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
  return JSON.parse(readFileSync(path, 'utf-8')) as CapabilityManifest
}

describe('manifest_compressor — primary-tool projection', () => {
  it('only returns entries for primary tools that exist in the manifest', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    const names = entries.map(e => e.t)
    for (const name of names) {
      expect(PRIMARY_TOOL_NAMES).toContain(name)
    }
  })

  it('every returned entry has all 5 fields populated', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    for (const entry of entries) {
      expect(typeof entry.t).toBe('string')
      expect(entry.t.length).toBeGreaterThan(0)
      expect(typeof entry.d).toBe('string')
      expect(entry.d.length).toBeGreaterThan(0)
      expect(Array.isArray(entry.p)).toBe(true)
      expect(['low', 'med', 'hi']).toContain(entry.c)
      expect(typeof entry.a).toBe('string')
      expect(entry.a.length).toBeGreaterThan(0)
    }
  })

  it('description is ≤15 words for every entry', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    for (const entry of entries) {
      const wordCount = entry.d.split(/\s+/).filter(Boolean).length
      expect(wordCount).toBeLessThanOrEqual(15)
    }
  })

  it('serialised output ≤3000 tokens for the live 8-tool manifest', () => {
    const manifest = loadLiveManifest()
    const entries = compressManifest(manifest)
    const out = compressedManifestToString(entries)
    expect(estimateTokens(out)).toBeLessThanOrEqual(3000)
  })

  it('compressedManifestToString is deterministic', () => {
    const manifest = loadLiveManifest()
    const a = compressedManifestToString(compressManifest(manifest))
    const b = compressedManifestToString(compressManifest(manifest))
    expect(a).toBe(b)

    // Order of input entries should not affect output.
    const entries: CompressedEntry[] = compressManifest(manifest)
    const reversed = [...entries].reverse()
    expect(compressedManifestToString(reversed)).toBe(compressedManifestToString(entries))
  })

  it('skips entries without tool_name and entries not in the primary list', () => {
    const synthetic: CapabilityManifest = {
      entries: [
        {
          canonical_id: 'X',
          tool_name: 'msr_sql',
          tool_description: 'short msr description',
          query_schema: { type: 'object', properties: { domains: {}, planets: {} } },
          token_cost_hint: 'hi',
          linked_data_asset_id: 'MSR_v3_0',
        },
        {
          canonical_id: 'Y',
          tool_name: 'not_a_primary_tool',
          query_schema: { type: 'object', properties: { foo: {} } },
          token_cost_hint: 'low',
          linked_data_asset_id: 'NONE',
        },
        {
          canonical_id: 'Z',
          // no tool_name → ignored
        },
      ],
    }
    const entries = compressManifest(synthetic)
    expect(entries).toHaveLength(1)
    expect(entries[0].t).toBe('msr_sql')
    expect(entries[0].p).toEqual(['domains', 'planets'])
  })
})
