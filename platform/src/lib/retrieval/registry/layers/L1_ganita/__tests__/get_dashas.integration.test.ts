/**
 * get_dashas.integration.test.ts — live-DB regression pin for marsys://tool/L1/get_dashas'
 * "current-dasha" gate (R5 W1 dasha_query lane, Ring-1 verifier finding + JL-010).
 *
 * The verifier found the tool's own description omitted that `ayanamsha_id` must be
 * explicitly supplied for the ≤1KB current-dasha gate — chart_dashas carries 5 ayanamshas
 * and get_dashas.ts applies NO server-side default for this one facet (unlike system/level/
 * window), so a caller who omits it silently gets one row PER AYANAMSHA (5 rows, ~3.2KB,
 * 3x over budget). This test pins the ≤1KB number using the COMPLETE correct facet set
 * (system=vimshottari, level=1, as_of_date=<today>, ayanamsha_id=lahiri_chitrapaksha) on
 * both canonical charts, and pins the documented failure mode (omitting ayanamsha_id busts
 * the gate) so a future regression in either the handler or its own tool description is
 * caught here rather than rediscovered live.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_dashas.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getDashasCapability } from '../get_dashas'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

const today = new Date().toISOString().slice(0, 10)

describeIf('get_dashas (marsys://tool/L1/get_dashas) — current-dasha gate, live DB', () => {
  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] COMPLETE facet set (system=vimshottari, level=1, as_of_date=${today}, ayanamsha_id=lahiri_chitrapaksha) is ONE row, <=1KB`, async () => {
      const result = await getDashasCapability.handler({
        chart_id: chartId,
        system: 'vimshottari',
        level: 1,
        as_of_date: today,
        ayanamsha_id: 'lahiri_chitrapaksha',
      }, undefined)

      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const rows = content['rows'] as Array<Record<string, unknown>>

      // Exactly one currently-active Mahadasha for one ayanamsha.
      expect(rows.length).toBe(1)
      expect(rows[0]['ayanamsha_id']).toBe('lahiri_chitrapaksha')
      expect(rows[0]['level_n']).toBe(1)

      const bytes = Buffer.byteLength(JSON.stringify(content), 'utf8')
      expect(bytes, `current-dasha payload was ${bytes} bytes`).toBeLessThanOrEqual(1024)
    })

    it(`[${chartId}] omitting ayanamsha_id now defaults to lahiri_chitrapaksha (server-side default closes the documented failure mode)`, async () => {
      const result = await getDashasCapability.handler({
        chart_id: chartId,
        system: 'vimshottari',
        level: 1,
        as_of_date: today,
        // ayanamsha_id intentionally omitted — must now default to lahiri_chitrapaksha
      }, undefined)

      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const rows = content['rows'] as Array<Record<string, unknown>>

      // F-93: server-side default now applies — exactly one row, correct ayanamsha.
      expect(rows.length).toBe(1)
      expect(rows[0]['ayanamsha_id']).toBe('lahiri_chitrapaksha')

      const bytes = Buffer.byteLength(JSON.stringify(content), 'utf8')
      expect(bytes, `defaulted payload was ${bytes} bytes`).toBeLessThanOrEqual(1024)
    })
  }

  it(`[${NATIVE_CHART_ID}] omitting ayanamsha_id returns exact Lahiri MD dates (two_pass_verified live repro)`, async () => {
    const result = await getDashasCapability.handler({
      chart_id: NATIVE_CHART_ID,
      system: 'vimshottari',
      level: 1,
      as_of_date: today,
      // ayanamsha_id intentionally omitted — must default to lahiri_chitrapaksha
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>

    expect(rows.length).toBe(1)
    expect(rows[0]['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    // Exact Lahiri MD dates pinned from DIAGNOSIS live repro — NOT '2010-07-07'/'2027-07-07' (Krishnamurti).
    expect(rows[0]['start_date']).toBe('2010-08-18')
    expect(rows[0]['end_date']).toBe('2027-08-18')
  })
})

// ── F-93: levels_available consistency — omit vs. explicit ayanamsha_id must agree ──────────
// Guards the two SQL-building sites (:210 row-fetch and :545 sub-query) from drifting
// out of sync in a future edit.
describeIf('get_dashas — levels_available consistency (F-93 sub-query drift guard), live DB', () => {
  it(`[${NATIVE_CHART_ID}] levels_available is identical whether ayanamsha_id is omitted or explicit`, async () => {
    const [omitted, explicit] = await Promise.all([
      getDashasCapability.handler({ chart_id: NATIVE_CHART_ID, system: 'vimshottari' }, undefined),
      getDashasCapability.handler({ chart_id: NATIVE_CHART_ID, system: 'vimshottari', ayanamsha_id: 'lahiri_chitrapaksha' }, undefined),
    ])

    expect(omitted.is_error).toBe(false)
    expect(explicit.is_error).toBe(false)
    const omittedContent = omitted.content as Record<string, unknown>
    const explicitContent = explicit.content as Record<string, unknown>

    expect(omittedContent['levels_available']).toEqual(explicitContent['levels_available'])
  })
})

// ── WP-1.3 (b): query_dasha_periods honors system_id (F-0354) ──────────────────
// ~437k non-vimshottari rows/chart were dark because the handler ignored the raw
// `system_id` column name a caller most naturally passes, silently defaulting to
// vimshottari. These pin that each requested system actually returns THAT system's rows,
// addressed by both the `system` facet and the new `system_id` alias.
describeIf('get_dashas — system_id honored (WP-1.3b / F-0354), live DB', () => {
  const NON_VIMSHOTTARI = ['yogini', 'ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika'] as const

  for (const system of NON_VIMSHOTTARI) {
    it(`[native] system_id="${system}" returns ONLY ${system} rows (not silently vimshottari)`, async () => {
      const result = await getDashasCapability.handler({
        chart_id: NATIVE_CHART_ID,
        system_id: system,           // raw column-name alias — the F-0354 path
        ayanamsha_id: 'lahiri_chitrapaksha',
        all_levels: true,
        window_start: '1984-02-05',
        window_end: '2084-02-05',
        limit: 50,
      }, undefined)

      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const facets = content['facets_applied'] as Record<string, unknown>
      // Applied system is echoed back and equals what was requested.
      expect(facets['system']).toBe(system)

      const rows = content['rows'] as Array<Record<string, unknown>>
      expect(rows.length).toBeGreaterThan(0)
      // Every served row belongs to the requested system — proves it is NOT defaulting to vimshottari.
      for (const r of rows) {
        expect(r['system_id']).toBe(system)
      }
    })
  }

  it('[native] precedence: explicit `system` wins over `system_id`', async () => {
    const result = await getDashasCapability.handler({
      chart_id: NATIVE_CHART_ID,
      system: 'yogini',
      system_id: 'ashtottari',
      ayanamsha_id: 'lahiri_chitrapaksha',
      all_levels: true,
      limit: 50,
    }, undefined)
    const content = result.content as Record<string, unknown>
    expect((content['facets_applied'] as Record<string, unknown>)['system']).toBe('yogini')
  })
})

// ── WP-1.3 (c): dasha tools honor requested WINDOWS + echo them (F-0471/0485) ──
// A fixed today-centered decade made past/future timing questions unanswerable. A
// historical window and a future window must both resolve, and the applied temporal
// filter must be echoed (never silently dropped).
describeIf('get_dashas — requested windows resolve + are echoed (WP-1.3c / F-0471/0485), live DB', () => {
  it('[native] historical window (2000-2010) resolves and is echoed, no default applied', async () => {
    const result = await getDashasCapability.handler({
      chart_id: NATIVE_CHART_ID,
      system: 'vimshottari',
      level: 1,
      ayanamsha_id: 'lahiri_chitrapaksha',
      window_start: '2000-01-01',
      window_end: '2010-12-31',
      limit: 50,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const facets = content['facets_applied'] as Record<string, unknown>
    // Echoed window is exactly what was requested — NOT the today±5y default.
    expect(facets['window']).toEqual({ start: '2000-01-01', end: '2010-12-31' })
    const dateFilter = facets['date_filter'] as Record<string, unknown>
    expect(dateFilter['default_window_applied']).toBeUndefined()

    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    // Every Maha period overlaps the requested historical window.
    for (const r of rows) {
      expect(String(r['start_date']) <= '2010-12-31').toBe(true)
      expect(String(r['end_date']) >= '2000-01-01').toBe(true)
    }
  })

  it('[native] future window (2030-2045) resolves and is echoed', async () => {
    const result = await getDashasCapability.handler({
      chart_id: NATIVE_CHART_ID,
      system: 'vimshottari',
      level: 1,
      ayanamsha_id: 'lahiri_chitrapaksha',
      window_start: '2030-01-01',
      window_end: '2045-12-31',
      limit: 50,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const facets = content['facets_applied'] as Record<string, unknown>
    expect(facets['window']).toEqual({ start: '2030-01-01', end: '2045-12-31' })
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    for (const r of rows) {
      expect(String(r['start_date']) <= '2045-12-31').toBe(true)
      expect(String(r['end_date']) >= '2030-01-01').toBe(true)
    }
  })

  it('[native] as_of_date filter is echoed in facets_applied.date_filter (no longer silent)', async () => {
    const result = await getDashasCapability.handler({
      chart_id: NATIVE_CHART_ID,
      system: 'vimshottari',
      level: 1,
      ayanamsha_id: 'lahiri_chitrapaksha',
      as_of_date: '2005-06-15',
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const facets = content['facets_applied'] as Record<string, unknown>
    const dateFilter = facets['date_filter'] as Record<string, unknown>
    expect(dateFilter['as_of_date']).toBe('2005-06-15')

    const rows = content['rows'] as Array<Record<string, unknown>>
    // The Maha period running on 2005-06-15 contains that date.
    expect(rows.length).toBe(1)
    expect(String(rows[0]['start_date']) <= '2005-06-15').toBe(true)
    expect(String(rows[0]['end_date']) >= '2005-06-15').toBe(true)
  })
})
