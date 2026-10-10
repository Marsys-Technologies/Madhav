/**
 * get_dashas — SS N-368: (1) no false note for system=vimshottari_kp, (2) the vimshottari_kp rows of a
 * MULTI-SYSTEM page (system="all", or an unrecognised system value that serves every system) are read
 * in the KP frame too.
 *
 * Rule (same as the KP-category mixed pages of get_karakas / get_nakshatra): the vimshottari_kp rows come
 * from `krishnamurti` and carry `frame_label`; every other system's rows come from the requested/default
 * ayanamsha (Lahiri when omitted, the pooled "all" opt-out kept); one statement, so LIMIT / OFFSET /
 * ORDER BY / the served-generation fence and the continuation cursor are the page's own.
 *
 * No database: `dashas_fake_db` holds vimshottari / vimshottari_kp / yogini at ALL FIVE ayanamshas.
 * Fails on the pre-N-368 handler (KP rows come back at Lahiri, unlabelled; injected Lahiri is "noted").
 */
import { createHash } from 'node:crypto'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { buildDashaFixture, createDashasFakeDb, installSigningKey, DASHA_ROWS_PER_GROUP } from '../../../__tests__/helpers/dashas_fake_db'

const fake = createDashasFakeDb(buildDashaFixture())
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => fake.query(args[0], args[1]) }))

import { getDashasCapability } from '../get_dashas'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const KP = 'krishnamurti'

type Content = Record<string, unknown> & { rows: Array<Record<string, unknown>> }
let restoreKey: () => void
beforeEach(() => { fake.reset(); restoreKey = installSigningKey() })
afterEach(() => restoreKey())

const base = { chart_id: CHART_ID, fields: 'all', window_start: '2000-01-01', window_end: '2100-01-01' }
const call = (a: Record<string, unknown>) => getDashasCapability.handler({ ...base, ...a }, undefined) as Promise<{ content: Content; is_error: boolean }>
const sqlOf = (i = 0) => fake.pages()[i]!.sql.replace(/\s+/g, ' ')
/** The page_rows WHERE clause only (the fence text above it legitimately uses IS DISTINCT FROM). */
const whereOf = (i = 0) => /WHERE (d\.chart_id[\s\S]*?) ORDER BY/.exec(sqlOf(i))![1]!

describe('(1) system=vimshottari_kp: no false note', () => {
  it.each([
    ['id omitted (direct call)', {}],
    ['bridge-injected Lahiri', { ayanamsha_id: LAHIRI, ayanamsha_injected: true }],
    ['the marker alone, no id', { ayanamsha_injected: true }],
    ['explicit krishnamurti', { ayanamsha_id: KP }],
  ] as Array<[string, Record<string, unknown>]>)('%s: krishnamurti + label, NO note', async (_l, extra) => {
    const res = await call({ system: 'vimshottari_kp', ...extra })
    expect(res.is_error).toBe(false)
    expect(res.content['ayanamsha_id']).toBe(KP)
    expect(res.content['frame_label']).toBe(KP_FRAME_LABEL)
    expect(res.content['ayanamsha_note']).toBeUndefined()
    expect(JSON.stringify(res.content)).not.toContain('ayanamsha_injected')
    expect(fake.pages()[0]!.params).not.toContain(true)
    for (const r of res.content.rows) expect(r['ayanamsha_id']).toBe(KP)
  })

  it.each([
    ['explicit Lahiri (no marker)', { ayanamsha_id: LAHIRI }, LAHIRI],
    ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }, 'LAHIRI'],
    ['raman', { ayanamsha_id: 'raman' }, 'raman'],
    ['"all"', { ayanamsha_id: 'all' }, 'all'],
    ['scope "all"', { ayanamsha_scope: 'all' }, 'all'],
    ['a marker cannot mask an explicit non-primary id', { ayanamsha_id: 'raman', ayanamsha_injected: true }, 'raman'],
  ] as Array<[string, Record<string, unknown>, string]>)('%s: the note names the request', async (_l, extra, requested) => {
    const res = await call({ system: 'vimshottari_kp', ...extra })
    expect(res.content['ayanamsha_id']).toBe(KP)
    expect(String(res.content['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
    expect(String(res.content['ayanamsha_note'])).toContain(`'${requested}'`)
  })

  it('the KP rows of a KP-only page each carry the frame', async () => {
    const res = await call({ system: 'vimshottari_kp' })
    expect(res.content.rows.length).toBe(DASHA_ROWS_PER_GROUP)
    for (const r of res.content.rows) expect(r['frame_label']).toBe(KP_FRAME_LABEL)
  })
})

describe('(2) system="all": the vimshottari_kp rows are read at krishnamurti, labelled; the rest at Lahiri', () => {
  it('default id: KP rows from krishnamurti with the label, every other system from Lahiri', async () => {
    const res = await call({ system: 'all', limit: 1000 })
    expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
    const kp = res.content.rows.filter((r) => r['system_id'] === 'vimshottari_kp')
    const other = res.content.rows.filter((r) => r['system_id'] !== 'vimshottari_kp')
    expect(kp.length).toBe(DASHA_ROWS_PER_GROUP)
    expect(new Set(kp.map((r) => r['ayanamsha_id']))).toEqual(new Set([KP]))
    for (const r of kp) expect(r['frame_label']).toBe(KP_FRAME_LABEL)
    expect(other.length).toBe(2 * DASHA_ROWS_PER_GROUP) // vimshottari + yogini, one ayanamsha each
    expect(new Set(other.map((r) => r['ayanamsha_id']))).toEqual(new Set([LAHIRI]))
    for (const r of other) expect(r['frame_label']).toBeUndefined()
    expect(res.content['ayanamsha_id']).toBe(LAHIRI) // describes the non-KP rows
    expect(res.content['kp_frame']).toEqual({ ayanamsha_id: KP, frame_label: KP_FRAME_LABEL, systems: ['vimshottari_kp'] })
    expect(res.content['ayanamsha_note']).toBeUndefined() // nothing was asked for
    expect(res.content['frame_label']).toBeUndefined() // not a KP-only page
    expect(res.content['total']).toBe(3 * DASHA_ROWS_PER_GROUP)
    expect(res.content['more_available']).toBe(false)
  })

  it('the injected Lahiri default (bridge marker): same page, still NO note', async () => {
    const res = await call({ system: 'all', limit: 1000, ayanamsha_id: LAHIRI, ayanamsha_injected: true })
    expect(res.content['ayanamsha_note']).toBeUndefined()
    expect(res.content['kp_frame']).toBeDefined()
    expect(new Set(res.content.rows.filter((r) => r['system_id'] === 'vimshottari_kp').map((r) => r['ayanamsha_id']))).toEqual(new Set([KP]))
    expect(JSON.stringify(res.content)).not.toContain('ayanamsha_injected')
  })

  it('an unrecognised system value serves every system, so it is the same two-leg page', async () => {
    const res = await call({ system: 'no_such_system', limit: 1000 })
    expect(res.is_error).toBe(false)
    const kp = res.content.rows.filter((r) => r['system_id'] === 'vimshottari_kp')
    expect(kp.length).toBe(DASHA_ROWS_PER_GROUP)
    expect(new Set(kp.map((r) => r['ayanamsha_id']))).toEqual(new Set([KP]))
    for (const r of kp) expect(r['frame_label']).toBe(KP_FRAME_LABEL)
  })

  it.each([
    ['explicit Lahiri', { ayanamsha_id: LAHIRI }, LAHIRI, true],
    ['raman', { ayanamsha_id: 'raman' }, 'raman', true],
    ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }, LAHIRI, true],
  ] as Array<[string, Record<string, unknown>, string, boolean]>)('%s: other systems at that id, KP rows at krishnamurti, note says the id applies to the other rows only', async (_l, extra, otherId) => {
    const res = await call({ system: 'all', limit: 1000, ...extra })
    const kp = res.content.rows.filter((r) => r['system_id'] === 'vimshottari_kp')
    const other = res.content.rows.filter((r) => r['system_id'] !== 'vimshottari_kp')
    expect(new Set(kp.map((r) => r['ayanamsha_id']))).toEqual(new Set([KP]))
    expect(new Set(other.map((r) => r['ayanamsha_id']))).toEqual(new Set([otherId]))
    expect(String(res.content['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
    expect(String(res.content['ayanamsha_note'])).toContain('applies to the other rows only')
  })

  it('"all" pools the non-KP systems across the five ayanamshas, the KP rows stay at krishnamurti alone', async () => {
    const res = await call({ system: 'all', limit: 1000, ayanamsha_id: 'all' })
    const kp = res.content.rows.filter((r) => r['system_id'] === 'vimshottari_kp')
    const other = res.content.rows.filter((r) => r['system_id'] !== 'vimshottari_kp')
    expect(kp.length).toBe(DASHA_ROWS_PER_GROUP)
    expect(new Set(kp.map((r) => r['ayanamsha_id']))).toEqual(new Set([KP]))
    expect(other.length).toBe(2 * 5 * DASHA_ROWS_PER_GROUP)
    expect(new Set(other.map((r) => r['ayanamsha_id'])).size).toBe(5)
    expect(res.content['ayanamsha_scope']).toBe('all')
    expect(res.content['ayanamsha_id']).toBeUndefined()
    expect(String(res.content['ayanamsha_note'])).toContain("'all'")
    // pooled non-KP rows still lead with Lahiri within their system (serve order), never alphabetical
    const yogini = res.content.rows.filter((r) => r['system_id'] === 'yogini')
    expect(yogini[0]!['ayanamsha_id']).toBe(LAHIRI)
  })

  it('a nonsense id is still invalid_ayanamsha_id for a multi-system page (the non-KP legs need it), with no SQL', async () => {
    const res = await call({ system: 'all', ayanamsha_id: 'bogus' })
    expect(res.is_error).toBe(true)
    expect((res.content as Record<string, unknown>)['code']).toBe('invalid_ayanamsha_id')
    expect(fake.statements).toEqual([])
  })

  it('the SQL: one statement, the KP id and system are code constants (nothing extra bound), fenced like a single-system page', async () => {
    await call({ system: 'all', limit: 1000 })
    const sql = sqlOf()
    expect(fake.pages().length).toBe(1)
    expect(sql).toContain("((d.system_id = 'vimshottari_kp' AND d.ayanamsha_id = 'krishnamurti') OR (d.system_id IS DISTINCT FROM 'vimshottari_kp' AND d.ayanamsha_id = $4))")
    expect(fake.pages()[0]!.params).toEqual([CHART_ID, 1001, 0, LAHIRI, '2000-01-01', '2100-01-01', 'ga_dashas', expect.stringMatching(/^[a-f0-9]{64}$/)])
    // the same receipt + replacement-fence + page statement skeleton as any single-system page
    expect(sql).toContain('eligible_receipt AS')
    expect(sql).toContain('replacement_fence AS')
    expect(sql).toContain('JOIN eligible_receipt eligible ON d.build_id = eligible.build_id::uuid')
    expect(sql).toContain('LIMIT $2 OFFSET $3')
    expect(sql).toContain('ORDER BY d.system_id ASC, array_position(ARRAY[')
    // the served-depth probe reads the same two legs
    const lv = fake.levelQueries()[0]!.sql.replace(/\s+/g, ' ')
    expect(lv).toContain("((system_id = 'vimshottari_kp' AND ayanamsha_id = 'krishnamurti') OR (system_id IS DISTINCT FROM 'vimshottari_kp' AND ayanamsha_id = $2))")
  })

  it('an active ga_dashas replacement refuses a system="all" page exactly like any other (one receipt, one fence)', async () => {
    fake.setReplacement(true)
    const res = await call({ system: 'all' })
    expect(res.is_error).toBe(true)
    expect((res.content as Record<string, unknown>)['code']).toBe('ga_dashas_replacement_in_progress')
  })

  it('pagination: pages through next_page_cursor are disjoint, complete, ordered, and each KP row is krishnamurti + labelled', async () => {
    const seen: Array<Record<string, unknown>> = []
    let cursor: string | null = null
    let pages = 0
    do {
      const res: { content: Content; is_error: boolean } = await call({ system: 'all', limit: 5, ...(cursor ? { page_cursor: cursor } : {}) })
      expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
      seen.push(...res.content.rows)
      cursor = (res.content['next_page_cursor'] as string | null) ?? null
      pages += 1
      expect(res.content.rows.length).toBeLessThanOrEqual(5)
    } while (cursor && pages < 10)
    expect(pages).toBe(3) // 12 rows at 5 per page
    expect(seen.length).toBe(3 * DASHA_ROWS_PER_GROUP)
    expect(new Set(seen.map((r) => r['dasha_row_id'])).size).toBe(seen.length) // no duplicate, none skipped
    for (const r of seen) {
      if (r['system_id'] === 'vimshottari_kp') {
        expect(r['ayanamsha_id']).toBe(KP)
        expect(r['frame_label']).toBe(KP_FRAME_LABEL)
      } else {
        expect(r['ayanamsha_id']).toBe(LAHIRI)
        expect(r['frame_label']).toBeUndefined()
      }
    }
    // page order is the single-statement ORDER BY: system_id ascending
    const systems = seen.map((r) => String(r['system_id']))
    expect([...systems].sort()).toEqual(systems)
  })

  it('the continuation cursor is refused by a page for a different query (single system) and accepted by the same one', async () => {
    const first = await call({ system: 'all', limit: 5 })
    const cursor = first.content['next_page_cursor'] as string
    expect(typeof cursor).toBe('string')
    const again = await call({ system: 'all', limit: 5, page_cursor: cursor })
    expect(again.is_error).toBe(false)
    const other = await call({ system: 'vimshottari', limit: 5, page_cursor: cursor })
    expect(other.is_error).toBe(true)
    expect((other.content as Record<string, unknown>)['code']).toBe('page_cursor_filter_mismatch')
  })

  const ORDER = 'system_id:asc,ayanamsha_serve_order:asc,start_date:asc,level_n:asc,start_iso:asc,dasha_row_id:asc'
  const fingerprintOf = (cursor: string): string =>
    (JSON.parse(Buffer.from(cursor.split('.')[1]!, 'base64url').toString('utf8')) as { filter_fingerprint: string }).filter_fingerprint
  const sha = (o: unknown): string => createHash('sha256').update(JSON.stringify(o)).digest('hex')

  it('the cursor fingerprint COVERS the KP frame of a mixed page (golden recomputation, KP leg present)', async () => {
    const page = await call({ system: 'all', limit: 5 })
    const withFrame = sha({
      chart_id: CHART_ID, ayanamsha_id: LAHIRI, system_id: null, kp_frame: 'vimshottari_kp@krishnamurti', level: 'cap<=3',
      lord_graha: null, date_contains: null, date_from: null, window_start: '2000-01-01', window_end: '2100-01-01', order: ORDER,
    })
    const withoutFrame = sha({
      chart_id: CHART_ID, ayanamsha_id: LAHIRI, system_id: null, level: 'cap<=3',
      lord_graha: null, date_contains: null, date_from: null, window_start: '2000-01-01', window_end: '2100-01-01', order: ORDER,
    })
    expect(fingerprintOf(page.content['next_page_cursor'] as string)).toBe(withFrame)
    expect(fingerprintOf(page.content['next_page_cursor'] as string)).not.toBe(withoutFrame)
  })

  it('a non-mixed page keeps its fingerprint byte for byte (no KP key)', async () => {
    const page = await call({ system: 'vimshottari', limit: 2 })
    const old = sha({
      chart_id: CHART_ID, ayanamsha_id: LAHIRI, system_id: 'vimshottari', level: 'cap<=3',
      lord_graha: null, date_contains: null, date_from: null, window_start: '2000-01-01', window_end: '2100-01-01', order: ORDER,
    })
    expect(fingerprintOf(page.content['next_page_cursor'] as string)).toBe(old)
  })

  it('the same request spelled with an alias mints the same fingerprint; another non-KP ayanamsha mints another', async () => {
    const a = await call({ system: 'all', limit: 5, ayanamsha_id: 'raman' })
    const b = await call({ system: 'all', limit: 5, ayanamsha_id: 'RAMAN' })
    const c = await call({ system: 'all', limit: 5 })
    expect(fingerprintOf(a.content['next_page_cursor'] as string)).toBe(fingerprintOf(b.content['next_page_cursor'] as string))
    expect(fingerprintOf(a.content['next_page_cursor'] as string)).not.toBe(fingerprintOf(c.content['next_page_cursor'] as string))
  })
})

describe('no KP involvement: the SQL and the response shape are unchanged', () => {
  it.each(['vimshottari', 'yogini'])('system=%s has no two-leg predicate and no KP fields', async (system) => {
    const res = await call({ system })
    const where = whereOf()
    expect(where).not.toContain('IS DISTINCT FROM')
    expect(where).not.toContain('krishnamurti')
    expect(where).toMatch(/d\.ayanamsha_id = \$4/)
    expect(res.content['kp_frame']).toBeUndefined()
    expect(res.content['frame_label']).toBeUndefined()
    for (const r of res.content.rows) expect(r['frame_label']).toBeUndefined()
    expect(new Set(res.content.rows.map((r) => r['ayanamsha_id']))).toEqual(new Set([LAHIRI]))
  })

  it('the default system (none given) is vimshottari at Lahiri', async () => {
    const res = await call({})
    expect(whereOf()).not.toContain('IS DISTINCT FROM')
    expect(res.content['kp_frame']).toBeUndefined()
    expect(new Set(res.content.rows.map((r) => r['system_id']))).toEqual(new Set(['vimshottari']))
  })
})
