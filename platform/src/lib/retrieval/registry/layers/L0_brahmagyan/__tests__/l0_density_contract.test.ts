/**
 * l0_density_contract — W-L0-4 served-surface contract detector
 * =============================================================================
 * MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md §4.2 W-L0-4 exit condition:
 * "every exported CapabilityDescriptor in the L0 registry declares one (the proof
 * counts descriptors, not files)".
 *
 * What this gates:
 *   1. The descriptor COUNT. `L0_CAPABILITIES` (the registry's own export list) is
 *      the counted set — descriptors, not files. Measured 2026-09-25: 46. A new L0
 *      capability added without updating this measured count fails here first, so the
 *      count can never silently drift past the contract requirement below.
 *   2. Explicit declaration. Every descriptor must carry its own `density_contract`
 *      on the exported literal — NOT the catalog-time backfill. This test imports the
 *      layer index directly and never calls `getCatalog()`, so
 *      `applyDescriptorDefaults()` never runs: a descriptor relying on the default
 *      reads `undefined` here and fails.
 *   3. Well-formedness (same shape `descriptor_defaults.test.ts` asserts estate-wide):
 *      paginated boolean, facets string[], empty_reason boolean, byte ceilings > 0
 *      when present.
 */

import { describe, it, expect, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/embeddings/embedText', () => ({ embedText: vi.fn() }))
vi.mock('@/lib/vidhi/inquiry/lifecycle_token', () => ({
  loadInquiryLifecycleSigningKeyRing: vi.fn(),
}))

import { L0_CAPABILITIES } from '../index'

/** Measured 2026-09-25 (W-L0-4 inventory): 46 pre-existing capability files, exactly
 *  one exported CapabilityDescriptor each, + `ref_graha_reference_get` added by this
 *  packet = 47 entries in L0_CAPABILITIES. The strategy text says "49" — stale by 3
 *  against the measured registry even before this packet's addition; the detector
 *  counts the measured set, not the prose. Update this number only by re-measuring
 *  the registry. */
const MEASURED_L0_DESCRIPTOR_COUNT = 47

describe('W-L0-4 density_contract — L0 served surface', () => {
  it('the L0 registry carries exactly the measured descriptor count (descriptors, not files)', () => {
    expect(L0_CAPABILITIES.length).toBe(MEASURED_L0_DESCRIPTOR_COUNT)
    const uris = L0_CAPABILITIES.map((c) => c.uri)
    expect(new Set(uris).size).toBe(MEASURED_L0_DESCRIPTOR_COUNT)
  })

  it('every exported L0 descriptor declares an explicit density_contract (no backfill reliance)', () => {
    const missing = L0_CAPABILITIES.filter(
      (c) => (c as { density_contract?: unknown }).density_contract === undefined,
    ).map((c) => c.uri)
    expect(missing).toEqual([])
  })

  it('every declared density_contract is well-formed', () => {
    for (const cap of L0_CAPABILITIES) {
      const dc = (cap as { density_contract?: {
        max_verdict_bytes?: number
        max_digest_bytes?: number
        paginated: boolean
        facets: string[]
        empty_reason: boolean
      } }).density_contract
      expect(dc, `${cap.uri} missing density_contract`).toBeDefined()
      if (!dc) continue
      expect(typeof dc.paginated, `${cap.uri}.density_contract.paginated`).toBe('boolean')
      expect(Array.isArray(dc.facets), `${cap.uri}.density_contract.facets`).toBe(true)
      for (const f of dc.facets) {
        expect(typeof f, `${cap.uri}.density_contract.facets entry`).toBe('string')
      }
      expect(typeof dc.empty_reason, `${cap.uri}.density_contract.empty_reason`).toBe('boolean')
      if (dc.max_verdict_bytes !== undefined) {
        expect(dc.max_verdict_bytes, `${cap.uri}.density_contract.max_verdict_bytes`).toBeGreaterThan(0)
      }
      if (dc.max_digest_bytes !== undefined) {
        expect(dc.max_digest_bytes, `${cap.uri}.density_contract.max_digest_bytes`).toBeGreaterThan(0)
      }
    }
  })

  it('declared facets are real input parameters, not JSON-schema keywords (the Stream B defect class)', () => {
    const SCHEMA_KEYWORDS = new Set(['type', 'properties', 'required', 'additionalProperties', 'enum', 'items', 'default'])
    for (const cap of L0_CAPABILITIES) {
      const dc = (cap as { density_contract?: { facets: string[] } }).density_contract
      if (!dc) continue
      const bogus = dc.facets.filter((f) => SCHEMA_KEYWORDS.has(f))
      expect(bogus, `${cap.uri} declares JSON-schema keywords as facets`).toEqual([])
    }
  })
})
