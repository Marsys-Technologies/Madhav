/**
 * bundle_hydrator.test.ts — covers floor enforcement, unknown-asset skip,
 * and HydratedBundle.mandatory_context shape.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { AssetEntry, ManifestData } from '@/lib/bundle/types'
import type { PipelinePlan } from '@/lib/pipeline/types'

// ── Mocks ──────────────────────────────────────────────────────────────────

const mockReadFile = vi.fn<(p: string) => Promise<string>>()

vi.mock('@/lib/storage', () => ({
  getStorageClient: () => ({
    readFile: (p: string) => mockReadFile(p),
  }),
}))

import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'

// ── Fixtures ───────────────────────────────────────────────────────────────

function makeEntry(canonical_id: string, path: string, extras: Partial<AssetEntry> = {}): AssetEntry {
  return {
    canonical_id,
    path,
    version: '1.0',
    status: 'CURRENT',
    layer: 'L1',
    expose_to_chat: true,
    representations: ['file'],
    interface_version: '1.0',
    fingerprint: 'fp-' + canonical_id,
    native_id: 'abhisek',
    ...extras,
  }
}

function makeManifest(entries: AssetEntry[]): ManifestData {
  const byId = new Map(entries.map(e => [e.canonical_id, e]))
  return { fingerprint: 'mfp-test', entries, byId }
}

function makePlan(asset_bundle: PipelinePlan['asset_bundle']): PipelinePlan {
  return {
    query_class: 'interpretive',
    query_intent_summary: 'test',
    asset_bundle,
    tool_calls: [],
    query_plan_id: '00000000-0000-0000-0000-000000000001',
  }
}

const FORENSIC = makeEntry('FORENSIC', 'L1/facts/FORENSIC.md', { token_count: 12000 })
const CGM = makeEntry('CGM', 'L2_5/CGM.md', { token_count: 60000 })
const UCN = makeEntry('UCN', 'L2_5/UCN.md', { token_count: 40000 })

beforeEach(() => {
  mockReadFile.mockReset()
})

// ── Tests ──────────────────────────────────────────────────────────────────

describe('hydrateBundle', () => {
  it('enforces FORENSIC + CGM floor when asset_bundle is empty', async () => {
    const manifest = makeManifest([FORENSIC, CGM])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)

    const plan = makePlan([])
    const bundle = await hydrateBundle(plan, manifest)

    expect(bundle.floor_enforced).toBe(true)
    expect(bundle.assets.map(a => a.asset_id).sort()).toEqual(['CGM', 'FORENSIC'])
    expect(mockReadFile).toHaveBeenCalledTimes(2)
    expect(mockReadFile).toHaveBeenCalledWith('L1/facts/FORENSIC.md')
    expect(mockReadFile).toHaveBeenCalledWith('L2_5/CGM.md')
  })

  it('skips unknown asset_id with a warning, no throw', async () => {
    const manifest = makeManifest([FORENSIC, CGM])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const plan = makePlan([
      { asset_id: 'FORENSIC', priority: 1, reason: 'chart' },
      { asset_id: 'CGM', priority: 1, reason: 'topology' },
      { asset_id: 'NONEXISTENT_ASSET', priority: 2, reason: 'whoops' },
    ])
    const bundle = await hydrateBundle(plan, manifest)

    expect(bundle.assets.map(a => a.asset_id)).toEqual(['FORENSIC', 'CGM'])
    expect(warnSpy).toHaveBeenCalled()
    warnSpy.mockRestore()
  })

  it('mandatory_context length matches successfully loaded asset count', async () => {
    const manifest = makeManifest([FORENSIC, CGM, UCN])
    mockReadFile.mockImplementation(async (p: string) => `body:${p}`)

    const plan = makePlan([
      { asset_id: 'FORENSIC', priority: 1, reason: 'r' },
      { asset_id: 'CGM', priority: 1, reason: 'r' },
      { asset_id: 'UCN', priority: 2, reason: 'r' },
    ])
    const bundle = await hydrateBundle(plan, manifest)

    expect(bundle.mandatory_context).toBeInstanceOf(Array)
    expect(bundle.mandatory_context).toHaveLength(3)
    expect(bundle.mandatory_context.every(e => typeof e.canonical_id === 'string')).toBe(true)
    expect(bundle.assets).toHaveLength(3)
    expect(bundle.floor_enforced).toBe(false)
  })
})
