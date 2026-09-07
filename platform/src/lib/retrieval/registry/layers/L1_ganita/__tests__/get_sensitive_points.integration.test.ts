/**
 * get_sensitive_points.integration.test.ts — live-DB pin for the 2 categories added by
 * F-B32 slice 9 (cycle 182): esoteric_point_sphuta_fertility / esoteric_point_yogi_system.
 *
 * These were genuine ga_sensitive_writer.py-owned categories with zero serving path anywhere
 * (cycle-156 F-B32 sweep), mischaracterized by cycle 181's own comment as "ambiguous
 * multi-writer ownership" -- corrected cycle 182 and added directly to this tool's existing
 * esoteric_point_* family. Pins that both are actually reachable live, both via the explicit
 * categories filter and via the `esoteric` tradition facet.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_sensitive_points.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getSensitivePointsCapability } from '../get_sensitive_points'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_sensitive_points (marsys://tool/L1/get_sensitive_points) — live DB', () => {
  it('esoteric_point_sphuta_fertility (70 live rows) and esoteric_point_yogi_system (25 live rows) are reachable via an explicit categories filter', async () => {
    const result = await getSensitivePointsCapability.handler(
      { chart_id: NATIVE_CHART_ID, categories: ['esoteric_point_sphuta_fertility', 'esoteric_point_yogi_system'], limit: 200 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    const categoriesSeen = new Set(rows.map(r => r['fact_category']))
    expect(categoriesSeen.has('esoteric_point_sphuta_fertility')).toBe(true)
    expect(categoriesSeen.has('esoteric_point_yogi_system')).toBe(true)
  })

  it('the esoteric tradition facet includes both new categories among the full esoteric_point_* family', async () => {
    const result = await getSensitivePointsCapability.handler(
      { chart_id: NATIVE_CHART_ID, tradition: 'esoteric', limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    const categoriesSeen = new Set(rows.map(r => r['fact_category']))
    expect(categoriesSeen.has('esoteric_point_sphuta_fertility')).toBe(true)
    expect(categoriesSeen.has('esoteric_point_yogi_system')).toBe(true)
    for (const r of rows) {
      expect(String(r['fact_category'])).toMatch(/^esoteric_point/)
    }
  })
})
