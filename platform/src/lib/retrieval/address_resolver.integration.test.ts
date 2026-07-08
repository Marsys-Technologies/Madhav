/**
 * @integration-test
 *
 * address_resolver.integration.test.ts — live-DB verification against BOTH canonical charts.
 * ==============================================================================================
 * Per the W1 lane brief: "Verify resolver chains against chart_facts on BOTH canonical charts
 * (482012f1 native, and Abhinandan 1c826d5a)." Gated on DB_AVAILABLE (same pattern as
 * build.integration.test.ts) — runs against a real PostgreSQL DB when DB_URL/DATABASE_URL is
 * set, skips cleanly otherwise (this sandbox had no DB credentials available to vitest; the
 * SAME assertions were independently confirmed via direct SQL against the live DB during
 * development — see address_resolver.test.ts header + the W1 task report for the transcript).
 *
 * Run:
 *   DB_URL=postgresql://user:pass@host/db vitest run --testPathPattern=address_resolver.integration
 */

import { describe, it, expect } from 'vitest'
import { resolveAddress, type ResolvedGraha, type ResolvedKaraka, type ResolvedOccupants } from './address_resolver'

const DB_AVAILABLE = !!(process.env.DB_URL || process.env.DATABASE_URL)

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const AYANAMSHA = 'lahiri_chitrapaksha'

const maybeDescribe = DB_AVAILABLE ? describe : describe.skip

maybeDescribe('address_resolver — live DB, native chart (482012f1)', () => {
  it('lord_of(bhava:7) = Venus placed in the 9th (Sagittarius) — the design §27.2 worked example', async () => {
    const result = await resolveAddress(NATIVE_CHART_ID, { type: 'lord_of', house: 7 }, { ayanamsha_id: AYANAMSHA })
    const g = result.entities[0] as ResolvedGraha
    expect(g.graha).toBe('Venus')
    expect(g.house).toBe(9)
    expect(g.sign).toBe('Sagittarius')
  })

  it('lord_of(bhava:10) = Saturn placed in the 7th (Libra)', async () => {
    const result = await resolveAddress(NATIVE_CHART_ID, { type: 'lord_of', house: 10 }, { ayanamsha_id: AYANAMSHA })
    const g = result.entities[0] as ResolvedGraha
    expect(g.graha).toBe('Saturn')
    expect(g.house).toBe(7)
  })

  it("karaka('AK') = Moon, house 11", async () => {
    const result = await resolveAddress(NATIVE_CHART_ID, { type: 'karaka', code: 'AK' }, { ayanamsha_id: AYANAMSHA })
    const k = result.entities[0] as ResolvedKaraka
    expect(k.graha).toBe('Moon')
    expect(k.house).toBe(11)
  })

  it('occupants_of(bhava:10) = Sun, Mercury', async () => {
    const result = await resolveAddress(NATIVE_CHART_ID, { type: 'occupants_of', house: 10 }, { ayanamsha_id: AYANAMSHA })
    const o = result.entities[0] as ResolvedOccupants
    expect(new Set(o.grahas)).toEqual(new Set(['Sun', 'Mercury']))
  })

  it('graha(Venus, D9) = Libra, house 4', async () => {
    const result = await resolveAddress(NATIVE_CHART_ID, { type: 'graha', graha: 'Venus', varga: 'D9' }, { ayanamsha_id: AYANAMSHA })
    const g = result.entities[0] as ResolvedGraha
    expect(g.sign).toBe('Libra')
    expect(g.house).toBe(4)
  })
})

maybeDescribe('address_resolver — live DB, Abhinandan chart (1c826d5a)', () => {
  it('lord_of(bhava:10) = Saturn placed in the 8th (Scorpio)', async () => {
    const result = await resolveAddress(ABHINANDAN_CHART_ID, { type: 'lord_of', house: 10 }, { ayanamsha_id: AYANAMSHA })
    const g = result.entities[0] as ResolvedGraha
    expect(g.graha).toBe('Saturn')
    expect(g.house).toBe(8)
  })

  it('lord_of(bhava:1) = Mars placed in the 12th (Pisces)', async () => {
    const result = await resolveAddress(ABHINANDAN_CHART_ID, { type: 'lord_of', house: 1 }, { ayanamsha_id: AYANAMSHA })
    const g = result.entities[0] as ResolvedGraha
    expect(g.graha).toBe('Mars')
    expect(g.house).toBe(12)
  })

  it("karaka('AK') = Mercury, house 11", async () => {
    const result = await resolveAddress(ABHINANDAN_CHART_ID, { type: 'karaka', code: 'AK' }, { ayanamsha_id: AYANAMSHA })
    const k = result.entities[0] as ResolvedKaraka
    expect(k.graha).toBe('Mercury')
    expect(k.house).toBe(11)
  })

  it('occupants_of(bhava:11) = Sun, Mercury', async () => {
    const result = await resolveAddress(ABHINANDAN_CHART_ID, { type: 'occupants_of', house: 11 }, { ayanamsha_id: AYANAMSHA })
    const o = result.entities[0] as ResolvedOccupants
    expect(new Set(o.grahas)).toEqual(new Set(['Sun', 'Mercury']))
  })
})
