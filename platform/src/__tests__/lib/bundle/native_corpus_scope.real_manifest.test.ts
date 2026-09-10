/**
 * native_corpus_scope.real_manifest.test.ts — the V3-E-016 leak detector, run
 * against the REAL production data path with NOTHING mocked.
 *
 * `bundle_hydrator.test.ts` covers the scoping logic against synthetic
 * fixtures. This file covers the thing that actually shipped: the real
 * `CAPABILITY_MANIFEST.json`, the real corpus files on disk, read by the real
 * storage client — the identical read the deployed Cloud Run image performs
 * (`readFile` resolves to the filesystem adapter in both environments; the
 * image carries the repo).
 *
 * Why a real-file test and not another fixture test: V3-E-016 shipped to
 * production precisely because every existing test around this path mocked the
 * storage layer, so no test ever observed that the bytes being joined into the
 * synthesis system prompt were one specific living person's chart. A fixture
 * cannot catch "the real manifest marks six assets `native_id: abhisek` and the
 * hydrator force-injects one of them into every chart's prompt." This can.
 *
 * If a future edit removes the scoping, these assertions fail — that is the
 * detector §N.8 requires, not a flag with nothing behind it.
 */

import { describe, it, expect, beforeAll } from 'vitest'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { PipelinePlan } from '@/lib/pipeline/types'

const HERE = path.dirname(fileURLToPath(import.meta.url))
// platform/src/__tests__/lib/bundle → repo root
const REPO_ROOT = path.resolve(HERE, '../../../../..')

/** The synthetic operator-E2E chart (Abhinandan Mohanty) — the probing input. */
const SYNTHETIC_TEST_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
/** The native's canonical chart (CLAUDE.md §B) — the no-over-restriction control. */
const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/**
 * Markers taken from the native's own FORENSIC birth anchors (CLAUDE.md §B)
 * plus the exact natal degree string the live production capture reproduced
 * verbatim. Any of these reaching a non-canonical chart's synthesis bundle is
 * the leak, in the same bytes the reader saw.
 */
const NATIVE_PRIVATE_FACT_MARKERS = [
  'Purva Bhadrapada',
  '27°02′48″',
  'Bhubaneswar',
  '1984-02-05',
] as const

type Hydrate = typeof import('@/lib/bundle/bundle_hydrator')['hydrateBundle']
type LoadManifest = typeof import('@/lib/bundle/manifest_reader')['loadManifest']

let hydrateBundle: Hydrate
let manifest: Awaited<ReturnType<LoadManifest>>

function planDeclaring(assetIds: string[]): PipelinePlan {
  return {
    query_class: 'factual',
    query_intent_summary: 'V3-E-016 real-manifest scope check',
    asset_bundle: assetIds.map((asset_id) => ({ asset_id, priority: 1 as const, reason: 'test' })),
    tool_calls: [],
  } as unknown as PipelinePlan
}

async function bundleContentFor(chartId: string, declared: string[] = []) {
  const bundle = await hydrateBundle(planDeclaring(declared), manifest, { chartId })
  return { bundle, joined: bundle.assets.map((a) => a.content).join('\n\n') }
}

beforeAll(async () => {
  // The filesystem storage adapter reads REPO_ROOT at module load, so this must
  // be set before the dynamic imports below.
  process.env.MARSYS_REPO_ROOT = REPO_ROOT
  hydrateBundle = (await import('@/lib/bundle/bundle_hydrator')).hydrateBundle
  manifest = await (await import('@/lib/bundle/manifest_reader')).loadManifest()
})

describe('V3-E-016 — real manifest, real corpus files, nothing mocked', () => {
  it('the real manifest still marks native-bound assets (guards the premise this fix rests on)', () => {
    const nativeScoped = manifest.entries.filter((e) => typeof e.native_id === 'string' && e.native_id.length > 0)
    expect(nativeScoped.length).toBeGreaterThan(0)
    // CGM specifically: the asset `bundle_hydrator` force-injects as a floor asset.
    expect(manifest.byId.get('CGM')?.native_id).toBe('abhisek')
  })

  it('NO native-private fact reaches a non-canonical chart (floor-injection path — the live-reproduced one)', async () => {
    const { bundle, joined } = await bundleContentFor(SYNTHETIC_TEST_CHART_ID)

    for (const marker of NATIVE_PRIVATE_FACT_MARKERS) {
      expect(joined, `native-private marker leaked to a chart it does not belong to: ${marker}`).not.toContain(marker)
    }
    // The withholding is recorded, not silent.
    expect(bundle.excluded_native_scoped.map((e) => e.asset_id)).toContain('CGM')
    expect(bundle.floor_enforced).toBe(false)
  })

  it('NO native-private fact reaches a non-canonical chart even when the planner names the registers outright', async () => {
    const { joined } = await bundleContentFor(SYNTHETIC_TEST_CHART_ID, ['CGM', 'MSR', 'CDLM', 'LEL', 'RM', 'UCN'])

    for (const marker of NATIVE_PRIVATE_FACT_MARKERS) {
      expect(joined, `native-private marker leaked to a chart it does not belong to: ${marker}`).not.toContain(marker)
    }
  })

  it('the native\'s OWN chart still receives his own corpus (this fix must not narrow his reading)', async () => {
    const { bundle, joined } = await bundleContentFor(CANONICAL_CHART_ID)

    expect(bundle.assets.map((a) => a.asset_id)).toContain('CGM')
    expect(bundle.excluded_native_scoped).toEqual([])
    // If this ever goes false, the corpus moved or the binding is wrong — either
    // way the two negative tests above would be passing vacuously, so assert it.
    expect(joined).toContain('Purva Bhadrapada')
  })
})
