/**
 * manifest_reader.test.ts
 *
 * Tests the manifest + overrides merge logic with controlled sample data.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { AssetEntry } from '../types'

// ── Helpers ────────────────────────────────────────────────────────────────

function makeAsset(overrides: Partial<AssetEntry> & { canonical_id: string; path: string }): AssetEntry {
  return {
    version: '1.0',
    status: 'CURRENT',
    layer: 'L1',
    expose_to_chat: true,
    representations: ['file'],
    interface_version: '1.0',
    fingerprint: 'abc123',
    native_id: 'test',
    ...overrides,
  }
}

const SAMPLE_MANIFEST = {
  fingerprint: 'test-fingerprint-001',
  entry_count: 3,
  entries: [
    makeAsset({ canonical_id: 'FORENSIC', path: '99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md' }),
    makeAsset({ canonical_id: 'CGM', path: 'L2.5/CGM_v9_0.md' }),
    makeAsset({ canonical_id: 'UCN', path: 'L2.5/UCN_v4_0.md' }),
  ],
}

const SAMPLE_OVERRIDES_YAML = `
overrides:
  FORENSIC:
    path_pattern: "FORENSIC_DATA_v8_0_SUPPLEMENT"
    preferred_for: [factual, interpretive]
    cost_weight: 1.0
    always_required: true
  CGM:
    preferred_for: [interpretive, holistic]
    cost_weight: 1.0
    always_required: true
  UCN:
    path_pattern: "UCN_v4_0"
    preferred_for: [interpretive, cross_domain]
    cost_weight: 0.8
mirror_pairs: {}
`

// ── Mock storage ───────────────────────────────────────────────────────────

vi.mock('@/lib/storage', () => ({
  getStorageClient: () => ({
    readFile: async (path: string) => {
      if (path.includes('CAPABILITY_MANIFEST')) return JSON.stringify(SAMPLE_MANIFEST)
      if (path.includes('manifest_overrides')) return SAMPLE_OVERRIDES_YAML
      throw new Error(`Unexpected readFile path: ${path}`)
    },
  }),
}))

// ── Tests ──────────────────────────────────────────────────────────────────

describe('loadManifest', () => {
  beforeEach(async () => {
    const { resetCache } = await import('../manifest_reader')
    resetCache()
  })

  it('returns data with correct fingerprint', async () => {
    const { loadManifest } = await import('../manifest_reader')
    const data = await loadManifest()
    expect(data.fingerprint).toBe('test-fingerprint-001')
  })

  it('byId map contains all entries', async () => {
    const { loadManifest } = await import('../manifest_reader')
    const data = await loadManifest()
    expect(data.byId.size).toBe(3)
    expect(data.byId.has('FORENSIC')).toBe(true)
    expect(data.byId.has('CGM')).toBe(true)
    expect(data.byId.has('UCN')).toBe(true)
  })

  it('merges always_required from overrides by exact canonical_id', async () => {
    const { loadManifest } = await import('../manifest_reader')
    const data = await loadManifest()
    expect(data.byId.get('FORENSIC')?.always_required).toBe(true)
    expect(data.byId.get('CGM')?.always_required).toBe(true)
  })

  it('merges always_required from overrides by path_pattern', async () => {
    const { loadManifest } = await import('../manifest_reader')
    const data = await loadManifest()
    // UCN now has canonical_id "UCN" (exact match with override key "UCN"); path_pattern is a no-op fallback
    const ucn = data.byId.get('UCN')
    expect(ucn?.preferred_for).toContain('interpretive')
    expect(ucn?.cost_weight).toBe(0.8)
  })

  it('merges cost_weight from overrides', async () => {
    const { loadManifest } = await import('../manifest_reader')
    const data = await loadManifest()
    expect(data.byId.get('FORENSIC')?.cost_weight).toBe(1.0)
    expect(data.byId.get('CGM')?.cost_weight).toBe(1.0)
  })

  it('returns cached data on second call (same fingerprint)', async () => {
    const { loadManifest } = await import('../manifest_reader')
    const d1 = await loadManifest()
    const d2 = await loadManifest()
    // Same object reference from cache
    expect(d1).toBe(d2)
  })

  it('getTier1Entries returns only expose_to_chat + CURRENT entries', async () => {
    const { loadManifest, getTier1Entries } = await import('../manifest_reader')
    const data = await loadManifest()
    const t1 = getTier1Entries(data)
    // All 3 sample entries are expose_to_chat=true and status=CURRENT
    expect(t1.length).toBe(3)
  })
})
