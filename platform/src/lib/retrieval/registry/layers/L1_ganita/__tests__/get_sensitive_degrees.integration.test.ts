/**
 * get_sensitive_degrees.integration.test.ts — F-B14 (L1_W1_ANALYSIS_BATCH_B.md, MUST, §N.6
 * item 1), live-DB regression pin.
 *
 * The tool's SELECT list omitted `verification_pass_status`, so 225 `single` + 50
 * `pending_w3_verification` + 60 `two_pass_verified` `chart_facts` rows were served as one
 * undifferentiated flat array — a caller had no way to tell a two-pass-confirmed sensitive
 * degree from a single-pass one. Pins the fix: every served row now carries
 * `verification_pass_status`, and the response discloses `tier_breakdown` +
 * `unverified_rows_in_page` for the page — without dropping or hiding any row (B.10).
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_sensitive_degrees.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getSensitiveDegreesCapability } from '../get_sensitive_degrees'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_sensitive_degrees (marsys://tool/L1/get_sensitive_degrees) — F-B14 tier disclosure, live DB', () => {
  it(`[${NATIVE_CHART_ID}] every served row carries verification_pass_status`, async () => {
    const result = await getSensitiveDegreesCapability.handler({
      chart_id: NATIVE_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      limit: 200,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    for (const r of rows) {
      expect(r['verification_pass_status']).toBeDefined()
      expect(r['verification_pass_status']).not.toBeNull()
    }
  })

  it(`[${NATIVE_CHART_ID}] tier_breakdown sums to the page's row count, and unverified_rows_in_page excludes only two_pass_verified`, async () => {
    const result = await getSensitiveDegreesCapability.handler({
      chart_id: NATIVE_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      limit: 200,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    const tierBreakdown = content['tier_breakdown'] as Record<string, number>
    const unverified = content['unverified_rows_in_page'] as number

    const tierSum = Object.values(tierBreakdown).reduce((a, b) => a + b, 0)
    expect(tierSum).toBe(rows.length)

    const expectedUnverified = rows.filter(r => r['verification_pass_status'] !== 'two_pass_verified').length
    expect(unverified).toBe(expectedUnverified)
    expect(unverified).toBeGreaterThan(0) // known live mix: single + pending_w3_verification present
  })

  it(`[${NATIVE_CHART_ID}] sensitive_point_yogi rows are two_pass_verified, sensitive_degree_check rows are not — none dropped`, async () => {
    const result = await getSensitiveDegreesCapability.handler({
      chart_id: NATIVE_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      limit: 200,
    }, undefined)

    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>

    const byCategory = new Map<string, Set<string>>()
    for (const r of rows) {
      const cat = String(r['fact_category'])
      const tier = String(r['verification_pass_status'])
      if (!byCategory.has(cat)) byCategory.set(cat, new Set())
      byCategory.get(cat)!.add(tier)
    }

    // Every row is still present (B.10) — no tier silently filtered out.
    expect(byCategory.get('sensitive_point_yogi')).toEqual(new Set(['two_pass_verified']))
    expect([...(byCategory.get('sensitive_degree_check') ?? [])].sort()).toEqual(
      ['pending_w3_verification', 'single'].sort(),
    )
  })

  it(`[${NATIVE_CHART_ID}] response with zero unverified rows omits unverified_note (honest-empty discipline)`, async () => {
    // sensitive_point_yogi alone is fully two_pass_verified — filtering to it should
    // surface unverified_rows_in_page: 0 and no unverified_note field at all.
    const result = await getSensitiveDegreesCapability.handler({
      chart_id: NATIVE_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      subject: 'YOGI',
      limit: 200,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['unverified_rows_in_page']).toBe(0)
    expect(content['unverified_note']).toBeUndefined()
  })
})
