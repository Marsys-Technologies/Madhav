/**
 * temporal_activation_wp13e.integration.test.ts — WP-1.3(e) live-DB proof.
 *
 * Runs against the real kala_activation table (no mocks). Proves, on Abhinandan
 * (the only chart with dated activation rows at lahiri — 84 dated):
 *   - returned date fields are plain 'YYYY-MM-DD' strings with NO timezone shift
 *     (the raw-JS-Date serialization bug rendered 1964-01-22 as "1964-01-21T18:30:00.000Z");
 *   - ROUND-TRIP: the returned activation_start string, fed back as as_of, returns
 *     that window (start <= as_of <= end) — proving point-in-time genuinely works;
 *   - the native chart stays honest-empty with the PENDING-W3 / awaiting_activation_dates
 *     disclosure (R-45 — dates land at WP-2.1).
 *
 * Run with: INTEGRATION=true vitest run \
 *   src/lib/retrieval/registry/layers/L3_kala/temporal_activation_wp13e.integration.test.ts
 */
import { describe, it, expect } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const LAHIRI = 'lahiri_chitrapaksha'
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>

async function handler(): Promise<Handler> {
  const { queryTemporalActivationCapability } = await import('./query_temporal_activation')
  return queryTemporalActivationCapability.handler as Handler
}

describeIf('WP-1.3(e) live-DB — returned dates are YYYY-MM-DD (no TZ shift)', () => {
  it('every returned activation_start/end/peak is a plain calendar-date string', async () => {
    const h = await handler()
    // Widen the window to capture Abhinandan's dated rows (they span 1964..2027).
    const res = await h({ chart_id: ABHINANDAN, ayanamsha_id: LAHIRI, date_from: '1900-01-01', date_to: '2100-01-01', top_k: 50 })
    const acts = res.content['activations'] as Array<Record<string, unknown>>
    expect(acts.length).toBeGreaterThan(0)
    for (const a of acts) {
      if (a['activation_start'] != null) expect(String(a['activation_start'])).toMatch(ISO_DATE)
      if (a['activation_end'] != null) expect(String(a['activation_end'])).toMatch(ISO_DATE)
      if (a['activation_peak_date'] != null) expect(String(a['activation_peak_date'])).toMatch(ISO_DATE)
      // explicitly assert the old TZ-shifted timestamp form is gone
      expect(String(a['activation_start'])).not.toMatch(/T\d\d:\d\d/)
    }
  })
})

describeIf('WP-1.3(e) live-DB — as_of round-trip on a real returned date', () => {
  it('a returned start date, fed back as as_of, returns a window that brackets it', async () => {
    const h = await handler()
    const seed = await h({ chart_id: ABHINANDAN, ayanamsha_id: LAHIRI, date_from: '1900-01-01', date_to: '2100-01-01', top_k: 50 })
    const acts = seed.content['activations'] as Array<Record<string, unknown>>
    const withStart = acts.find(a => a['activation_start'] != null)!
    const startStr = String(withStart['activation_start'])
    expect(startStr).toMatch(ISO_DATE)

    // Round-trip: point-in-time query AT the returned start date.
    const res = await h({ chart_id: ABHINANDAN, ayanamsha_id: LAHIRI, as_of: startStr })
    const df = res.content['date_filter'] as Record<string, unknown>
    expect(df['mode']).toBe('point_in_time')
    expect(df['as_of']).toBe(startStr)

    const hits = res.content['activations'] as Array<Record<string, unknown>>
    expect(hits.length).toBeGreaterThan(0)
    // every returned window must actually bracket the instant
    for (const w of hits) {
      expect(String(w['activation_start']) <= startStr).toBe(true)
      expect(String(w['activation_end']) >= startStr).toBe(true)
    }
  })
})

describeIf('WP-1.3(e) live-DB — native honest-empty + PENDING-W3 disclosure (R-45)', () => {
  it('native at lahiri returns 0 activations with awaiting_activation_dates + PENDING-W3 reason', async () => {
    const h = await handler()
    const res = await h({ chart_id: NATIVE, ayanamsha_id: LAHIRI, date_from: '2020-01-01', date_to: '2030-01-01' })
    expect(res.content['activation_count']).toBe(0)
    expect(res.content['awaiting_activation_dates']).toBe(true)
    expect(String(res.content['empty_reason'])).toMatch(/PENDING-W3/)
    expect(String(res.content['empty_reason'])).toMatch(/WP-2\.1/)
  })
})
