/**
 * get_dashas (Lahiri primary, PR-2): omitted = Lahiri (F-93, unchanged), aliases normalise,
 * ayanamsha_id:"all" / ayanamsha_scope:"all" is the explicit pooled opt-out served in AYANAMSHA_SERVE_ORDER
 * (Lahiri first, not alphabetical), unknown ids stay `invalid_ayanamsha_id`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { getDashasCapability } from '../get_dashas'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const ids = ['krishnamurti', 'lahiri_chitrapaksha', 'raman', 'surya_siddhanta_classical', 'true_chitra']

function mockPages() {
  const pages: Array<{ sql: string; params: unknown[] }> = []
  queryMock.mockImplementation((sql: string, params: unknown[] = []) => {
    if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
    if (sql.includes('replacement_fence AS')) {
      pages.push({ sql, params })
      return Promise.resolve({ rows: [{ replacement_in_progress: false, eligible_build_id: 'build-a', rows: [] }] })
    }
    if (sql.includes('FROM asset_provenance_receipts receipt') && sql.includes('AS rows_build_id')) {
      return Promise.resolve({ rows: [{
        asset_id: 'ga_vargas', partition_key: '__whole_asset__', receipt_version: 'v1',
        receipt_build_id: 'build-vargas', rows_build_id: 'build-vargas', receipt_state: 'proven',
        freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
        receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build',
        observed_at: '2026-09-07T00:00:00Z',
      }] })
    }
    if (sql.startsWith('SELECT MAX(level_n)')) return Promise.resolve({ rows: [{ max_level: 3 }] })
    return Promise.resolve({ rows: [] })
  })
  return pages
}

const env = { kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID, key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT }
beforeEach(() => {
  queryMock.mockReset()
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
})
afterEach(() => {
  if (env.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = env.kid
  if (env.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = env.key
})

const base = { chart_id: CHART_ID, limit: 2, fields: 'all', window_start: '2000-01-01', window_end: '2100-01-01' }

describe('get_dashas ayanamsha scope', () => {
  it('omitted -> the page query binds lahiri_chitrapaksha', async () => {
    const pages = mockPages()
    const res = await getDashasCapability.handler({ ...base }, undefined)
    expect(res.is_error).toBe(false)
    expect(pages[0]!.params).toContain(LAHIRI)
    expect((res.content as Record<string, unknown>)['ayanamsha_id']).toBe(LAHIRI)
  })

  it.each([['LAHIRI', LAHIRI], ['kp', 'krishnamurti'], ['True_Citra', 'true_chitra']])('alias %j -> %j', async (input, stored) => {
    const pages = mockPages()
    await getDashasCapability.handler({ ...base, ayanamsha_id: input }, undefined)
    expect(pages[0]!.params).toContain(stored)
  })

  it.each([[{ ayanamsha_id: 'all' }], [{ ayanamsha_scope: 'all' }]])('%j -> pooled: no ayanamsha param, serve-order sort, scope marker', async (extra) => {
    const pages = mockPages()
    const res = await getDashasCapability.handler({ ...base, ...extra }, undefined)
    expect(res.is_error).toBe(false)
    for (const id of ids) expect(pages[0]!.params).not.toContain(id)
    const sql = pages[0]!.sql.replace(/\s+/g, ' ')
    expect(sql).not.toMatch(/d\.ayanamsha_id\s*=\s*\$/)
    expect(sql).toMatch(/array_position\(ARRAY\['lahiri_chitrapaksha'/)
    expect(sql).not.toMatch(/ORDER BY d\.system_id ASC, d\.ayanamsha_id ASC/)
    const content = res.content as Record<string, unknown>
    expect(content['ayanamsha_scope']).toBe('all')
    expect((content['facets_applied'] as Record<string, unknown>)['ayanamsha']).toBe('all')
  })

  it('an explicit id beats ayanamsha_scope:"all"', async () => {
    const pages = mockPages()
    await getDashasCapability.handler({ ...base, ayanamsha_id: 'raman', ayanamsha_scope: 'all' }, undefined)
    expect(pages[0]!.params).toContain('raman')
  })

  it('unknown id is still invalid_ayanamsha_id, with no SQL', async () => {
    mockPages()
    const res = await getDashasCapability.handler({ ...base, ayanamsha_id: 'bogus' }, undefined)
    expect(res.is_error).toBe(true)
    expect((res.content as Record<string, unknown>)['code']).toBe('invalid_ayanamsha_id')
    expect(queryMock).not.toHaveBeenCalled()
  })
})
