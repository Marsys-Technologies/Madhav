/**
 * get_dashas system=vimshottari_kp (SS N-362 a): the Moon's KP sub-period chain is a dasha SYSTEM, not
 * one of the six KP categories, but it is KP content and is served in the KP frame like every other
 * KP read: read at `krishnamurti` WHATEVER ayanamsha_id / ayanamsha_scope the caller passed (omitted,
 * an explicit Lahiri id, an alias, "all", scope "all", another stored id, nonsense),
 * labelled "KP frame (Krishnamurti ayanamsha)", with an `ayanamsha_note` when the caller EXPLICITLY asked for
 * something else (SS N-368: never for an omitted id or the bridge-injected default; see get_dashas_kp_system_all.test.ts). Every OTHER dasha system keeps the Lahiri-primary path byte for byte.
 *
 * Also pins how vimshottari_kp interacts with the get_dashas served-generation fence: it has NO
 * handling of its own (KP rows are ga_dashas rows of the same chart_dashas table and the same
 * build), so the same receipt/replacement fence statement guards the KP page.
 *
 * No database: `@/lib/db/client` is a mock that records the page statement.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { getDashasCapability } from '../get_dashas'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const KP = 'krishnamurti'
const OTHERS = ['lahiri_chitrapaksha', 'true_chitra', 'raman', 'surya_siddhanta_classical']

interface Page { sql: string; params: unknown[] }

function mockPages(opts: { replacement?: boolean; rows?: Array<Record<string, unknown>> } = {}) {
  const pages: Page[] = []
  const levelQueries: Page[] = []
  queryMock.mockImplementation((sql: string, params: unknown[] = []) => {
    if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
    if (sql.includes('replacement_fence AS')) {
      pages.push({ sql, params })
      return Promise.resolve({ rows: [{ replacement_in_progress: opts.replacement === true, eligible_build_id: 'build-a', rows: opts.rows ?? [] }] })
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
    if (sql.startsWith('SELECT MAX(level_n)')) {
      levelQueries.push({ sql, params })
      return Promise.resolve({ rows: [{ max_level: 3 }] })
    }
    return Promise.resolve({ rows: [] })
  })
  return { pages, levelQueries }
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

/** [label, extra args, requested value the note must name (null = no note)] */
const requests: Array<[string, Record<string, unknown>, string | null]> = [
  ['no id', {}, null],
  ['an explicit Lahiri id (no injection marker)', { ayanamsha_id: LAHIRI }, LAHIRI],
  ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }, 'LAHIRI'],
  ['raman', { ayanamsha_id: 'raman' }, 'raman'],
  ['"all"', { ayanamsha_id: 'all' }, 'all'],
  ['ayanamsha_scope "all"', { ayanamsha_scope: 'all' }, 'all'],
  ['a nonsense id', { ayanamsha_id: 'not_an_ayanamsha_xyz' }, 'not_an_ayanamsha_xyz'],
  ['krishnamurti itself', { ayanamsha_id: KP }, null],
  ['the alias kp', { ayanamsha_id: 'kp' }, null],
]

const systems: Array<[string, Record<string, unknown>]> = [
  ['system=vimshottari_kp', { system: 'vimshottari_kp' }],
  ['system=KP (alias)', { system: 'KP' }],
  ['dasha_system=kp_sub (alias)', { dasha_system: 'kp_sub' }],
  ['system_id=vimshottari_kp', { system_id: 'vimshottari_kp' }],
]

describe('get_dashas system=vimshottari_kp is read in the KP frame', () => {
  describe.each(systems)('%s', (_s, sys) => {
    it.each(requests)('%s: the page binds krishnamurti only, labelled', async (_label, extra, requested) => {
      const { pages, levelQueries } = mockPages()
      const res = await getDashasCapability.handler({ ...base, ...sys, ...extra }, undefined)
      expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
      expect(pages.length).toBe(1)
      expect(pages[0]!.params).toContain(KP)
      for (const other of OTHERS) expect(pages[0]!.params, `page leaked ${other}`).not.toContain(other)
      expect(pages[0]!.sql.replace(/\s+/g, ' ')).toMatch(/d\.ayanamsha_id = \$\d+/)
      // the dasha system is still the KP system
      expect(pages[0]!.params).toContain('vimshottari_kp')
      // the served-depth probe is read in the same frame
      expect(levelQueries[0]!.params).toContain(KP)
      for (const other of OTHERS) expect(levelQueries[0]!.params).not.toContain(other)
      const c = res.content as Record<string, unknown>
      expect(c['ayanamsha_id']).toBe(KP)
      expect(c['ayanamsha_scope']).toBeUndefined()
      expect(c['frame_label']).toBe(KP_FRAME_LABEL)
      expect((c['facets_applied'] as Record<string, unknown>)['ayanamsha']).toBe(KP)
      expect((c['facets_applied'] as Record<string, unknown>)['system']).toBe('vimshottari_kp')
      if (requested === null) {
        expect(c['ayanamsha_note']).toBeUndefined()
      } else {
        expect(String(c['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
        expect(String(c['ayanamsha_note'])).toContain(`'${requested}'`)
      }
    })
  })

  it('a nonsense id is NOT an invalid_ayanamsha_id error for the KP system (the id is ignored, never validated)', async () => {
    mockPages()
    const res = await getDashasCapability.handler({ ...base, system: 'vimshottari_kp', ayanamsha_id: 'bogus' }, undefined)
    expect(res.is_error).toBe(false)
    expect((res.content as Record<string, unknown>)['code']).toBeUndefined()
  })
})

describe('every other dasha system keeps the Lahiri-primary path', () => {
  it.each(['vimshottari', 'yogini', 'chara_karaka'])('system=%s: omitted -> Lahiri, unlabelled, no note', async (system) => {
    const { pages } = mockPages()
    const res = await getDashasCapability.handler({ ...base, system }, undefined)
    expect(pages[0]!.params).toContain(LAHIRI)
    expect(pages[0]!.params).not.toContain(KP)
    const c = res.content as Record<string, unknown>
    expect(c['ayanamsha_id']).toBe(LAHIRI)
    expect(c['frame_label']).toBeUndefined()
    expect(c['ayanamsha_note']).toBeUndefined()
  })

  it('the default system (none given) is vimshottari at Lahiri', async () => {
    const { pages } = mockPages()
    const res = await getDashasCapability.handler({ ...base }, undefined)
    expect(pages[0]!.params).toContain(LAHIRI)
    expect(pages[0]!.params).toContain('vimshottari')
    expect((res.content as Record<string, unknown>)['frame_label']).toBeUndefined()
  })

  it('an explicit non-KP id on vimshottari is honoured (raman), nonsense stays invalid_ayanamsha_id with no SQL', async () => {
    const { pages } = mockPages()
    await getDashasCapability.handler({ ...base, system: 'vimshottari', ayanamsha_id: 'raman' }, undefined)
    expect(pages[0]!.params).toContain('raman')
    queryMock.mockReset()
    const bad = await getDashasCapability.handler({ ...base, system: 'vimshottari', ayanamsha_id: 'bogus' }, undefined)
    expect(bad.is_error).toBe(true)
    expect((bad.content as Record<string, unknown>)['code']).toBe('invalid_ayanamsha_id')
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('system="all" pooled keeps its pooled shape for the other systems; since SS N-368 its vimshottari_kp rows ARE re-framed (see get_dashas_kp_system_all.test.ts)', async () => {
    const { pages } = mockPages()
    const res = await getDashasCapability.handler({ ...base, system: 'all', ayanamsha_id: 'all' }, undefined)
    // no id is bound (the KP leg's krishnamurti is an inlined code constant, the pooled leg has no predicate)
    for (const id of [KP, ...OTHERS]) expect(pages[0]!.params).not.toContain(id)
    expect((res.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
    // not a KP-only page: no top-level frame_label, but the KP system's frame is reported beside it
    expect((res.content as Record<string, unknown>)['frame_label']).toBeUndefined()
    expect((res.content as Record<string, unknown>)['kp_frame']).toEqual({ ayanamsha_id: KP, frame_label: KP_FRAME_LABEL, systems: ['vimshottari_kp'] })
  })
})

describe('vimshottari_kp and the served-generation fence (no handling of its own)', () => {
  it('the KP page is the same receipt + replacement-fence statement as any other system', async () => {
    const kp = mockPages()
    await getDashasCapability.handler({ ...base, system: 'vimshottari_kp' }, undefined)
    const kpSql = kp.pages[0]!.sql.replace(/\s+/g, ' ')
    queryMock.mockReset()
    const classical = mockPages()
    await getDashasCapability.handler({ ...base, system: 'vimshottari' }, undefined)
    const classicalSql = classical.pages[0]!.sql.replace(/\s+/g, ' ')
    expect(kpSql).toContain('eligible_receipt AS')
    expect(kpSql).toContain('replacement_fence AS')
    expect(kpSql).toContain('JOIN eligible_receipt eligible ON d.build_id = eligible.build_id::uuid')
    expect(kpSql).toBe(classicalSql)
  })

  it('an active ga_dashas replacement refuses the KP page exactly like any other system', async () => {
    mockPages({ replacement: true })
    const res = await getDashasCapability.handler({ ...base, system: 'vimshottari_kp', ayanamsha_id: LAHIRI }, undefined)
    expect(res.is_error).toBe(true)
    expect((res.content as Record<string, unknown>)['code']).toBe('ga_dashas_replacement_in_progress')
  })

  it('a continuation cursor minted for the KP page is the same for any passed id (the frame, not the request, is fingerprinted)', async () => {
    const row = (n: number) => ({ dasha_row_id: `r${n}`, system_id: 'vimshottari_kp', ayanamsha_id: KP, level_n: 2, lord_graha: 'Moon', start_date: '2020-01-0' + n, end_date: '2020-02-0' + n })
    mockPages({ rows: [row(1), row(2), row(3)] })
    const a = await getDashasCapability.handler({ ...base, system: 'vimshottari_kp', ayanamsha_id: LAHIRI }, undefined)
    queryMock.mockReset()
    mockPages({ rows: [row(1), row(2), row(3)] })
    const b = await getDashasCapability.handler({ ...base, system: 'vimshottari_kp', ayanamsha_id: 'raman' }, undefined)
    const ca = (a.content as Record<string, unknown>)['next_page_cursor']
    const cb = (b.content as Record<string, unknown>)['next_page_cursor']
    expect(typeof ca).toBe('string')
    expect(ca).toBe(cb)
  })
})
