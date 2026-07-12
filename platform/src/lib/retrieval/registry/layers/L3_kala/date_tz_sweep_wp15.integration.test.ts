/**
 * date_tz_sweep_wp15.integration.test.ts — WP-1.5 F-DATE-TZ program-wide proof.
 *
 * Runs against the real DB (no mocks). Proves the to_char('YYYY-MM-DD') sweep on the
 * sibling L3/L4/L5 serving tools that WP-1.3(e) left unfixed: every served Postgres
 * `date` column comes back as a plain calendar-date string with NO node-postgres
 * IST-midnight → UTC off-by-one (the "1964-01-22" → "1964-01-21T18:30:00.000Z" bug).
 *
 * Also proves WP-1.5 receipt honesty on query_convergence_windows: total_matching is a
 * real COUNT and more_available/next_cursor never lie about a trim.
 *
 * Run with: INTEGRATION=true vitest run \
 *   src/lib/retrieval/registry/layers/L3_kala/date_tz_sweep_wp15.integration.test.ts
 */
import { describe, it, expect } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/
const HAS_TIME = /T\d\d:\d\d/

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>

/** Assert every named field on every row is a bare YYYY-MM-DD (or null) — never a TZ instant. */
function assertBareDates(rows: Array<Record<string, unknown>>, fields: string[]) {
  for (const r of rows) {
    for (const f of fields) {
      const v = r[f]
      if (v == null) continue
      expect(String(v), `${f}=${String(v)}`).toMatch(ISO_DATE)
      expect(String(v), `${f} must not carry a time component`).not.toMatch(HAS_TIME)
    }
  }
}

describeIf('WP-1.5 F-DATE-TZ — query_dasha_dossier (kala_avadhi period_start/end)', () => {
  it('period_start/period_end are bare calendar dates', async () => {
    const { queryDashaDossierCapability } = await import('./query_dasha_dossier')
    const h = queryDashaDossierCapability.handler as Handler
    const res = await h({ chart_id: NATIVE, limit: 50 })
    const rows = (res.content['rows'] as Array<Record<string, unknown>>) ?? []
    expect(rows.length).toBeGreaterThan(0)
    assertBareDates(rows, ['period_start', 'period_end'])
  })
})

describeIf('WP-1.5 F-DATE-TZ — query_temporal_view (kala_darshana windows)', () => {
  it('peak_date/window_start/window_end are bare calendar dates', async () => {
    const { queryTemporalViewCapability } = await import('./query_temporal_view')
    const h = queryTemporalViewCapability.handler as Handler
    const res = await h({ chart_id: NATIVE, limit: 50 })
    const rows = (res.content['rows'] as Array<Record<string, unknown>>) ?? []
    expect(rows.length).toBeGreaterThan(0)
    assertBareDates(rows, ['peak_date', 'window_start', 'window_end'])
  })
})

describeIf('WP-1.5 F-DATE-TZ + receipt honesty — query_convergence_windows', () => {
  it('window dates are bare + total_matching/more_available/cursor are honest', async () => {
    const { queryConvergenceWindowsCapability } = await import('./query_convergence_windows')
    const h = queryConvergenceWindowsCapability.handler as Handler
    const res = await h({ chart_id: NATIVE, top_k: 5 })
    const c = res.content
    const rows = (c['convergence_windows'] as Array<Record<string, unknown>>) ?? []
    if (rows.length > 0) assertBareDates(rows, ['window_start', 'window_end', 'peak_date'])

    // Receipt honesty: total_matching is a real COUNT; more_available agrees with it.
    const total = c['total_matching'] as number
    const served = c['window_count'] as number
    expect(typeof total).toBe('number')
    expect(total).toBeGreaterThanOrEqual(served)
    const more = c['more_available'] as boolean
    expect(more).toBe(total > served)
    // When trimmed, a working cursor is present; otherwise null.
    if (more) expect(c['next_cursor']).not.toBeNull()
    else expect(c['next_cursor']).toBeNull()
  })
})

describeIf('WP-1.5 F-DATE-TZ — query_projections (kala_bhavishya)', () => {
  it('peak_date/window_start/window_end are bare calendar dates', async () => {
    const { queryProjectionsCapability } = await import('./query_projections')
    const h = queryProjectionsCapability.handler as Handler
    const res = await h({ chart_id: NATIVE, horizon_years: 100, limit: 50 })
    const rows = (res.content['projections'] as Array<Record<string, unknown>>) ?? []
    if (rows.length > 0) assertBareDates(rows, ['peak_date', 'window_start', 'window_end'])
  })
})

describeIf('WP-1.5 — call_priority_ranking column fix (previously errored on absent columns)', () => {
  it('runs without a SQL error and returns bare activation dates', async () => {
    const mod = await import('./call_service_wrappers')
    const h = mod.callPriorityRankingCapability.handler as Handler
    // Widen window to capture Abhinandan's dated activation rows.
    const res = await h({ chart_id: ABHINANDAN, date_from: '1900-01-01', date_to: '2100-01-01', top_k: 20 })
    expect(res.is_error).toBeFalsy()
    const rows = (res.content['ranked_signals'] as Array<Record<string, unknown>>) ?? []
    if (rows.length > 0) assertBareDates(rows, ['window_start', 'window_end'])
  })
})
