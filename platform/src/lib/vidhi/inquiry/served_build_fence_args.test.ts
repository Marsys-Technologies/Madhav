import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { compileChartCapabilityOverlay } from '../../retrieval/registry/knowledge/overlay'
import { compileInquiryContract } from './compiler'
import type { ScopeTuple } from '../types'

const SERVED = ['22222222-2222-4222-8222-222222222222', '11111111-1111-4111-8111-111111111111']
const scope: ScopeTuple = {
  intent: 'wealth_deepdive', domains: ['wealth'], width: 'panoramic', depth: 'deepdive',
  horizon: 'multi_year', intervention: false, entitlement: 'native',
}

describe('served-generation fence reaches dispatched plan args (review: fenced probe, unfenced read)', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-13T00:00:00.000Z')
  const fenceAcceptingBindings = new Set(snapshot.scus.flatMap((scu) =>
    scu.bindings.filter((binding) => binding.input_contract['build_id']).map((binding) => binding.binding_id)))

  // Every executable binding proven available, so the plan is not empty of fence-accepting items.
  function overlayFor(servedBuildIds?: readonly string[]) {
    return compileChartCapabilityOverlay({
      snapshot, chart_id: 'chart-fixture', build_id: 'build-1', generated_at: '2026-09-13T00:00:00.000Z',
      evidence: snapshot.scus.map((scu) => ({
        scu_id: scu.scu_id, build_status: 'completed', build_id: 'build-1', freshness: 'fresh', state: 'available' as const,
        available_binding_ids: scu.bindings.filter((binding) => binding.executable).map((binding) => binding.binding_id),
        gaps: [], asset_receipts: [],
      })),
      ...(servedBuildIds ? { served_build_ids: servedBuildIds } : {}),
    })
  }

  it('declares build_id on every leaf that accepts a build fence', () => {
    for (const name of ['get_strength', 'get_av_transit_gating', 'get_kp_cusps', 'get_yoga_firings', 'get_divisionals',
      'query_signals', 'query_domain_reading', 'yoga_activation_by_dasha']) {
      expect(fenceAcceptingBindings.has(`registry:marsys://tool/${
        snapshot.scus.flatMap((scu) => scu.bindings).find((binding) => binding.binding_id.endsWith(`/${name}`))
          ?.binding_id.replace('registry:marsys://tool/', '')}`), name).toBe(true)
    }
  })

  it('injects the overlay\'s served build set (sorted, deduplicated) into every fence-accepting plan item', () => {
    const overlay = overlayFor([...SERVED, SERVED[0]!])
    expect(overlay.served_build_ids).toEqual([...SERVED].sort())
    const contract = compileInquiryContract({ snapshot, overlay, chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: scope })
    const fenced = contract.plan_items.filter((item) => item.binding_id && fenceAcceptingBindings.has(item.binding_id))
    expect(fenced.length).toBeGreaterThan(0)
    for (const item of fenced) expect(item.args['build_id'], item.binding_id!).toEqual([...SERVED].sort())
    // Items whose tool declares no fence never receive one.
    for (const item of contract.plan_items.filter((candidate) => candidate.binding_id && !fenceAcceptingBindings.has(candidate.binding_id))) {
      expect(item.args['build_id']).toBeUndefined()
    }
  })

  it('injects nothing when the overlay resolved no served build set', () => {
    const contract = compileInquiryContract({ snapshot, overlay: overlayFor(), chart_id: 'chart-fixture', question: 'Complete wealth outlook', scope_tuple: scope })
    for (const item of contract.plan_items) expect(item.args['build_id']).toBeUndefined()
  })

  it('moves the overlay version when the served build set changes, so drift is detected', () => {
    expect(overlayFor(SERVED).overlay_version).not.toBe(overlayFor([SERVED[0]!]).overlay_version)
    expect(overlayFor().overlay_version).toBe(overlayFor().overlay_version)
  })
})
