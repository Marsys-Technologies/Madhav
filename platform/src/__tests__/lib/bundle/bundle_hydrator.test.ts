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

/**
 * Every fixture above declares `native_id: 'abhisek'` (mirroring the real
 * manifest), so the pre-existing behavioural assertions below are made against
 * the chart that native's corpus is actually bound to. That is the point: the
 * V3-E-016 scoping is additive, and the bound chart's own bundle is unchanged.
 */
const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const OTHER_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

beforeEach(() => {
  mockReadFile.mockReset()
})

// ── Tests ──────────────────────────────────────────────────────────────────

describe('hydrateBundle', () => {
  it('enforces CGM floor when asset_bundle is empty', async () => {
    const manifest = makeManifest([CGM])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)

    const plan = makePlan([])
    const bundle = await hydrateBundle(plan, manifest, { chartId: CANONICAL_CHART_ID })

    expect(bundle.floor_enforced).toBe(true)
    expect(bundle.assets.map(a => a.asset_id)).toEqual(['CGM'])
    expect(mockReadFile).toHaveBeenCalledTimes(1)
    expect(mockReadFile).toHaveBeenCalledWith('L2_5/CGM.md')
  })

  it('does not throw when FORENSIC is absent from the manifest (post-teardown reality; regression guard for the 2026-07-19/20 production HTTP 500)', async () => {
    // FORENSIC was deleted from CAPABILITY_MANIFEST.json in PR #187; this manifest
    // reflects that real state — no FORENSIC entry at all. Prior to the fix,
    // FLOOR_ASSET_IDS still listed 'FORENSIC', so this exact shape threw
    // `bundle_hydrator: floor asset 'FORENSIC' not found in manifest` on every
    // hydrateBundle() call, which is what PG-2 Lane X-2 found live.
    const manifest = makeManifest([CGM, UCN])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)

    const plan = makePlan([])
    const bundle = await hydrateBundle(plan, manifest, { chartId: CANONICAL_CHART_ID })

    expect(bundle.floor_enforced).toBe(true)
    expect(bundle.assets.map(a => a.asset_id)).toEqual(['CGM'])
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
    const bundle = await hydrateBundle(plan, manifest, { chartId: CANONICAL_CHART_ID })

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
    const bundle = await hydrateBundle(plan, manifest, { chartId: CANONICAL_CHART_ID })

    expect(bundle.mandatory_context).toBeInstanceOf(Array)
    expect(bundle.mandatory_context).toHaveLength(3)
    expect(bundle.mandatory_context.every(e => typeof e.canonical_id === 'string')).toBe(true)
    expect(bundle.assets).toHaveLength(3)
    expect(bundle.floor_enforced).toBe(false)
  })
})

// ── V3-E-016 — native-corpus chart scoping ─────────────────────────────────
//
// The defect: `bundle_hydrator` read every asset the plan named (plus the CGM
// floor asset, unconditionally) and joined the file text straight into the
// synthesis system prompt, without ever consulting which chart the turn was
// about. CGM/MSR/CDLM/RM/UCN/LEL are one specific native's chart, so EVERY
// other chart's turn — the synthetic operator-E2E chart and four other real
// people's charts in production — received his private chart facts.
//
// These tests are the detector §N.8 asks for: they FAIL if the scoping is
// removed, and they distinguish the two directions (leak vs over-restriction).
describe('hydrateBundle — native-corpus chart scoping (V3-E-016)', () => {
  it('WITHHOLDS a native-bound floor asset from a chart it is not bound to, without throwing', async () => {
    const manifest = makeManifest([CGM])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const bundle = await hydrateBundle(makePlan([]), manifest, { chartId: OTHER_CHART_ID })

    expect(bundle.assets).toHaveLength(0)
    // The read must never happen — the withheld file is not even loaded.
    expect(mockReadFile).not.toHaveBeenCalled()
    expect(bundle.excluded_native_scoped).toEqual([
      { asset_id: 'CGM', reason: 'native_binding_mismatch', was_floor: true },
    ])
    // `floor_enforced` must not claim an injection that did not happen.
    expect(bundle.floor_enforced).toBe(false)
    warnSpy.mockRestore()
  })

  it('WITHHOLDS native-bound assets the planner explicitly declared', async () => {
    const manifest = makeManifest([FORENSIC, CGM, UCN])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const plan = makePlan([
      { asset_id: 'FORENSIC', priority: 1, reason: 'r' },
      { asset_id: 'UCN', priority: 2, reason: 'r' },
    ])
    const bundle = await hydrateBundle(plan, manifest, { chartId: OTHER_CHART_ID })

    expect(bundle.assets).toHaveLength(0)
    expect(bundle.excluded_native_scoped.map(e => e.asset_id).sort()).toEqual(['CGM', 'FORENSIC', 'UCN'])
    warnSpy.mockRestore()
  })

  it('ADMITS a chart-agnostic asset (no native_id) to any chart', async () => {
    const REFERENCE = makeEntry('BPHS', 'corpus/BPHS.md', { native_id: undefined })
    const manifest = makeManifest([CGM, REFERENCE])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const plan = makePlan([{ asset_id: 'BPHS', priority: 1, reason: 'r' }])
    const bundle = await hydrateBundle(plan, manifest, { chartId: OTHER_CHART_ID })

    // The chart-agnostic asset survives; only the native-bound CGM floor is withheld.
    expect(bundle.assets.map(a => a.asset_id)).toEqual(['BPHS'])
    expect(bundle.excluded_native_scoped.map(e => e.asset_id)).toEqual(['CGM'])
    warnSpy.mockRestore()
  })

  it('FAILS CLOSED for a native_id with no chart binding at all', async () => {
    const UNBOUND = makeEntry('SOMEONE_ELSE_CGM', 'L2_5/other.md', { native_id: 'not-bound-to-anything' })
    const manifest = makeManifest([CGM, UNBOUND])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const plan = makePlan([{ asset_id: 'SOMEONE_ELSE_CGM', priority: 1, reason: 'r' }])
    const bundle = await hydrateBundle(plan, manifest, { chartId: CANONICAL_CHART_ID })

    // An unbound native's corpus is withheld even on the canonical chart — a
    // manifest entry naming a native this module has no binding for is not
    // "probably fine", it is unknown, and unknown fails closed.
    expect(bundle.assets.map(a => a.asset_id)).toEqual(['CGM'])
    expect(bundle.excluded_native_scoped).toEqual([
      { asset_id: 'SOMEONE_ELSE_CGM', reason: 'native_binding_unknown', was_floor: false },
    ])
    warnSpy.mockRestore()
  })

  it('does NOT narrow the bound chart: the native still receives his own corpus', async () => {
    const manifest = makeManifest([CGM, UCN])
    mockReadFile.mockImplementation(async (p: string) => `content-of:${p}`)

    const plan = makePlan([{ asset_id: 'UCN', priority: 2, reason: 'r' }])
    const bundle = await hydrateBundle(plan, manifest, { chartId: CANONICAL_CHART_ID })

    expect(bundle.assets.map(a => a.asset_id).sort()).toEqual(['CGM', 'UCN'])
    expect(bundle.excluded_native_scoped).toEqual([])
    expect(bundle.floor_enforced).toBe(true)
  })
})
