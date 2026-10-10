/* eslint-disable @typescript-eslint/no-explicit-any -- fixture-shaped JSON in a test */
/**
 * Lahiri primary PR-3 — the labelled cross-check on the surfaces that carry it (SS N-342 Q2/Q5/Q7).
 *
 *   get_positions    identity facts always (Lagna sign, Moon sign, Moon nakshatra); full per-graha form opt-in
 *   get_dashas       current Mahadasha lord always (when the page serves it); opt-in otherwise
 *   query_discoveries / query_pratijna   opt-in; replace the "1/1 ayanamshas agree" chip under a filter
 *
 * No database: `query` is a router over a five-ayanamsha fixture. Every surface: the primary answer is
 * equal with and without the cross-check; "all" stays the raw option and carries no envelope.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('@/lib/retrieval/tail/build_tail_watch', () => ({
  buildTailWatch: async () => ({ tail_watch: [], tail_watch_empty_reason: 'fixture', tail_watch_components: [] }),
}))

import { getPositionsCapability } from '../layers/L1_ganita/get_positions'
import { getDashasCapability } from '../layers/L1_ganita/get_dashas'
import { queryDiscoveriesCapability } from '../layers/L2_bodha/query_discoveries'
import { queryPratijnaCapability } from '../layers/L2_bodha/query_pratijna'
import { AYANAMSHA_SERVE_ORDER } from '../constants'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const KEY = 'ayanamsha_cross_check'
const OTHERS_IN_ORDER = ['true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical']
// fixture rows are emitted in ALPHABETICAL order on purpose: the builder must re-order to serve order
const ALPHA: string[] = [...AYANAMSHA_SERVE_ORDER].sort()

type Cc = Record<string, any>
const cc = (x: unknown): Cc => (x as Record<string, any>)[KEY]

// ── get_positions ─────────────────────────────────────────────────────────────────────────────────
type PosOverride = Record<string, Record<string, string>> // ayanamsha -> "SUBJECT.key" -> value
function positionsDb(opts: { stored?: readonly string[]; override?: PosOverride; subjectsOnPage?: string[] } = {}) {
  const stored = opts.stored ?? AYANAMSHA_SERVE_ORDER
  const page = opts.subjectsOnPage ?? ['LAGNA', 'MOON', 'SUN']
  const base: Record<string, string> = {
    'LAGNA.sign': 'Aries', 'MOON.sign': 'Aquarius', 'MOON.nakshatra': 'Purva Bhadrapada',
    'SUN.sign': 'Capricorn', 'SUN.nakshatra': 'Uttara Ashadha',
  }
  const value = (aya: string, subject: string, key: string): string | undefined =>
    opts.override?.[aya]?.[`${subject}.${key}`] ?? base[`${subject}.${key}`]
  const lon = (aya: string, subject: string): number => 10 + ALPHA.indexOf(aya) + (subject === 'MOON' ? 0.5 : 0)
  const calls: Array<{ sql: string; params: unknown[] }> = []
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    calls.push({ sql, params })
    if (sql.includes('fact_category = ANY($2::text[])')) {
      // the page: LAHIRI only (the default scope), 'all' returns every stored ayanamsha
      const wantAll = !sql.includes('ayanamsha_id = $') && !sql.includes('ayanamsha_id IN ($')
      const ayas = wantAll ? stored : [LAHIRI]
      const rows = ayas.flatMap((aya) => page.flatMap((subject) => ['sign', 'nakshatra'].filter((k) => !(subject === 'LAGNA' && k === 'nakshatra')).map((key) => ({
        fact_id: `${aya}-${subject}-${key}`, fact_category: 'graha_position', fact_subject: subject, ayanamsha_id: aya,
        fact_key: key, fact_value_text: value(aya, subject, key) ?? null, fact_value_num: null, citation_ref: 'r', citation_human: null,
      }))))
      return { rows }
    }
    if (sql.includes('fact_subject = ANY($3::text[])')) {
      const subjects = params[2] as string[]
      const rows = [...stored].sort().flatMap((aya) => subjects.flatMap((subject) => [
        { ayanamsha_id: aya, fact_subject: subject, fact_key: 'sign', fact_value_text: value(aya, subject, 'sign') ?? null, fact_value_num: null },
        ...(subject === 'LAGNA' ? [] : [{ ayanamsha_id: aya, fact_subject: subject, fact_key: 'nakshatra', fact_value_text: value(aya, subject, 'nakshatra') ?? null, fact_value_num: null }]),
        { ayanamsha_id: aya, fact_subject: subject, fact_key: 'longitude_sidereal', fact_value_text: null, fact_value_num: String(lon(aya, subject)) },
      ]))
      return { rows }
    }
    return { rows: [] }
  })
  return calls
}

describe('get_positions: identity facts are always cross-checked, compact', () => {
  beforeEach(() => { queryMock.mockReset() })

  it('default (omitted) = Lahiri page + the compact identity cross-check; degrees differ across ayanamshas but signs agree -> "Agrees across all five ayanamshas"', async () => {
    positionsDb()
    const res = await getPositionsCapability.handler({ chart_id: CHART }, undefined)
    expect(res.is_error).toBe(false)
    const content = res.content as Record<string, unknown>
    expect(content['ayanamsha_id']).toBe(LAHIRI)
    const x = cc(content)
    expect(x.scope).toBe('identity_facts')
    expect(x.heading).toBe('Cross-check, not the reading')
    expect(x.primary_id).toBe(LAHIRI)
    expect(x.agreement).toBe('all_agree')
    expect(x.summary).toBe('Agrees across all five ayanamshas')
    expect(x.others.map((o: Cc) => o.ayanamsha_id)).toEqual(OTHERS_IN_ORDER)
    // only the identity facts, never the Sun
    expect(Object.keys(x.primary.values)).toEqual(['lagna_sign', 'moon_sign', 'moon_nakshatra'])
    // degrees shown, different per ayanamsha, never compared
    const degs = new Set([x.primary.values.moon_sign.degrees, ...x.others.map((o: Cc) => o.values.moon_sign.degrees)])
    expect(degs.size).toBe(5)
  })

  it('the primary answer (rows) is identical with and without the cross-check; page 1 is Lahiri only', async () => {
    positionsDb()
    const plain = (await getPositionsCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, any>
    const withX = (await getPositionsCapability.handler({ chart_id: CHART, include_cross_check: true }, undefined)).content as Record<string, any>
    expect(withX.rows).toEqual(plain.rows)
    expect(plain.rows.every((r: Cc) => r.ayanamsha_id === LAHIRI)).toBe(true)
    expect(plain.rows.map((r: Cc) => r.ayanamsha_id)).not.toContain('krishnamurti')
  })

  it('a dissenting ayanamsha is named with its value under the heading', async () => {
    positionsDb({ override: { raman: { 'MOON.nakshatra': 'Uttara Bhadrapada', 'MOON.sign': 'Pisces' } } })
    const x = cc((await getPositionsCapability.handler({ chart_id: CHART }, undefined)).content)
    expect(x.agreement).toBe('dissent')
    expect(x.summary).toBe('Dissent: Raman: Moon sign Pisces (primary Aquarius), Moon nakshatra Uttara Bhadrapada (primary Purva Bhadrapada)')
    expect(x.others.filter((o: Cc) => o.status === 'dissents').map((o: Cc) => o.ayanamsha_id)).toEqual(['raman'])
  })

  it('single-ayanamsha chart -> not_available/single_ayanamsha_chart, never "1/1"', async () => {
    positionsDb({ stored: [LAHIRI] })
    const x = cc((await getPositionsCapability.handler({ chart_id: CHART }, undefined)).content)
    expect(x).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(JSON.stringify(x)).not.toMatch(/1\/1|agree/i)
  })

  it('"all" stays the raw multi-row option: no envelope, no cross-check read', async () => {
    const calls = positionsDb()
    const res = await getPositionsCapability.handler({ chart_id: CHART, ayanamsha_id: 'all' }, undefined)
    const content = res.content as Record<string, any>
    expect(content['ayanamsha_scope']).toBe('all')
    expect(KEY in content).toBe(false)
    expect(new Set(content['rows'].map((r: Cc) => r.ayanamsha_id)).size).toBe(5)
    expect(calls.some((c) => c.sql.includes('fact_subject = ANY($3::text[])'))).toBe(false)
  })

  it('a page that serves neither Lagna nor Moon carries no envelope unless include_cross_check is set', async () => {
    positionsDb({ subjectsOnPage: ['SUN'] })
    const plain = (await getPositionsCapability.handler({ chart_id: CHART, planet: 'Sun' }, undefined)).content as Record<string, unknown>
    expect(KEY in plain).toBe(false)
    const opt = cc((await getPositionsCapability.handler({ chart_id: CHART, planet: 'Sun', include_cross_check: true }, undefined)).content)
    expect(opt.scope).toBe('requested_facts')
    expect(Object.keys(opt.primary.values)).toEqual(['sun_sign', 'sun_nakshatra'])
  })

  it('include_cross_check adds every served graha (Lagna, Moon first); absent -> identity facts only', async () => {
    positionsDb()
    const opt = cc((await getPositionsCapability.handler({ chart_id: CHART, include_cross_check: true }, undefined)).content)
    expect(opt.scope).toBe('requested_facts')
    expect(Object.keys(opt.primary.values)).toEqual(['lagna_sign', 'moon_sign', 'moon_nakshatra', 'sun_sign', 'sun_nakshatra'])
    expect(opt.summary).toBe('Agrees across all five ayanamshas')
  })

  it('an explicit non-Lahiri request anchors the cross-check on the requested ayanamsha and lists Lahiri among the others in serve order', async () => {
    positionsDb()
    const x = cc((await getPositionsCapability.handler({ chart_id: CHART, ayanamsha_id: 'raman' }, undefined)).content)
    expect(x.primary_id).toBe('raman')
    expect(x.others.map((o: Cc) => o.ayanamsha_id)).toEqual([LAHIRI, 'true_chitra', 'krishnamurti', 'surya_siddhanta_classical'])
  })

  it('a failed cross-check read never fails the primary answer', async () => {
    positionsDb()
    const original = queryMock.getMockImplementation()!
    queryMock.mockImplementation(async (sql: string, params: unknown[]) => {
      if (sql.includes('fact_subject = ANY($3::text[])')) throw new Error('db down')
      return original(sql, params)
    })
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const res = await getPositionsCapability.handler({ chart_id: CHART }, undefined)
    spy.mockRestore()
    expect(res.is_error).toBe(false)
    expect(cc(res.content)).toMatchObject({ not_available: true, reason: 'cross_check_read_failed' })
    expect((res.content as Record<string, any>).rows.length).toBeGreaterThan(0)
  })
})

// ── get_dashas ────────────────────────────────────────────────────────────────────────────────────
function dashasDb(opts: { stored?: readonly string[]; lords?: Record<string, string> } = {}) {
  const stored = opts.stored ?? AYANAMSHA_SERVE_ORDER
  const lords = opts.lords ?? {}
  const page = {
    replacement_in_progress: false, eligible_build_id: 'build-a',
    rows: [{ ayanamsha_id: LAHIRI, system_id: 'vimshottari', level_n: 1, lord_graha: 'Venus', start_date: '2000-01-01', end_date: '2100-01-01', citation_ref: 'c' }],
  }
  const calls: Array<{ sql: string; params: unknown[] }> = []
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    calls.push({ sql, params })
    if (typeof sql !== 'string') return { rows: [] }
    if (sql.includes('replacement_fence AS')) return { rows: [page] }
    if (sql.includes('FROM asset_provenance_receipts receipt') && sql.includes('AS rows_build_id')) {
      return { rows: [{
        asset_id: 'ga_vargas', partition_key: '__whole_asset__', receipt_version: 'v1', receipt_build_id: 'b', rows_build_id: 'b',
        receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
        receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
      }] }
    }
    if (sql.startsWith('SELECT MAX(level_n)')) return { rows: [{ max_level: 3 }] }
    if (sql.includes('FROM chart_dashas') && sql.includes('level_n = 1 AND start_date <= $3::date')) {
      return { rows: [...stored].sort().map((aya) => ({ ayanamsha_id: aya, lord_graha: lords[aya] ?? 'Venus' })) }
    }
    return { rows: [] }
  })
  return calls
}
const dashaEnv = { kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID, key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT }
const dashaArgs = { chart_id: CHART, limit: 2, window_start: '2000-01-01', window_end: '2100-01-01' }

describe('get_dashas: the current Mahadasha lord is always cross-checked, compact', () => {
  beforeEach(() => {
    queryMock.mockReset()
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
  })
  afterEach(() => {
    if (dashaEnv.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = dashaEnv.kid
    if (dashaEnv.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = dashaEnv.key
  })

  it('default: Lahiri rows + compact "Agrees across all five ayanamshas"; the cross-check reads the SAME proven build', async () => {
    const calls = dashasDb()
    const res = await getDashasCapability.handler({ ...dashaArgs }, undefined)
    expect(res.is_error).toBe(false)
    const content = res.content as Record<string, any>
    expect(content.ayanamsha_id).toBe(LAHIRI)
    expect(content.rows.every((r: Cc) => r.ayanamsha_id === LAHIRI)).toBe(true)
    const x = cc(content)
    expect(x).toMatchObject({ scope: 'identity_facts', agreement: 'all_agree', summary: 'Agrees across all five ayanamshas', primary_id: LAHIRI })
    expect(x.others.map((o: Cc) => o.ayanamsha_id)).toEqual(OTHERS_IN_ORDER)
    expect(Object.keys(x.primary.values)).toEqual(['maha_lord'])
    const xc = calls.find((c) => c.sql.includes('level_n = 1 AND start_date <= $3::date'))!
    expect(xc.params).toContain('build-a')
  })

  it('the compact agree form stays small (it rides on the <=1KB current-dasha answer)', async () => {
    dashasDb()
    const x = cc((await getDashasCapability.handler({ ...dashaArgs }, undefined)).content)
    expect(Buffer.byteLength(JSON.stringify(x), 'utf8')).toBeLessThan(800)
  })

  it('a dissenting ayanamsha is named with its lord', async () => {
    dashasDb({ lords: { krishnamurti: 'Saturn' } })
    const x = cc((await getDashasCapability.handler({ ...dashaArgs }, undefined)).content)
    expect(x.agreement).toBe('dissent')
    expect(x.summary).toBe('Dissent: Krishnamurti: current Mahadasha lord Saturn (primary Venus)')
  })

  it('single-ayanamsha chart -> not_available/single_ayanamsha_chart', async () => {
    dashasDb({ stored: [LAHIRI] })
    const x = cc((await getDashasCapability.handler({ ...dashaArgs }, undefined)).content)
    expect(x).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
  })

  it('"all" and a non-Vimshottari system carry no envelope and issue no cross-check read', async () => {
    const calls = dashasDb()
    const all = (await getDashasCapability.handler({ ...dashaArgs, ayanamsha_id: 'all' }, undefined)).content as Record<string, unknown>
    expect(KEY in all).toBe(false)
    const yogini = (await getDashasCapability.handler({ ...dashaArgs, system: 'yogini' }, undefined)).content as Record<string, unknown>
    expect(KEY in yogini).toBe(false)
    expect(calls.some((c) => c.sql.includes('level_n = 1 AND start_date <= $3::date'))).toBe(false)
  })

  it('opt-in include_cross_check attaches the lord cross-check even when the page does not serve the current Mahadasha', async () => {
    // page row spans 1990-1995 only: it does not contain today
    dashasDb()
    const original = queryMock.getMockImplementation()!
    queryMock.mockImplementation(async (sql: string, params: unknown[]) => {
      if (sql.includes('replacement_fence AS')) {
        return { rows: [{ replacement_in_progress: false, eligible_build_id: 'build-a', rows: [
          { ayanamsha_id: LAHIRI, system_id: 'vimshottari', level_n: 1, lord_graha: 'Mars', start_date: '1990-01-01', end_date: '1995-01-01', citation_ref: 'c' }] }] }
      }
      return original(sql, params)
    })
    const plain = (await getDashasCapability.handler({ chart_id: CHART, window_start: '1990-01-01', window_end: '1995-01-01' }, undefined)).content as Record<string, unknown>
    expect(KEY in plain).toBe(false)
    const opt = cc((await getDashasCapability.handler({ chart_id: CHART, window_start: '1990-01-01', window_end: '1995-01-01', include_cross_check: true }, undefined)).content)
    expect(opt.scope).toBe('requested_facts')
  })
})

// ── query_discoveries ─────────────────────────────────────────────────────────────────────────────
const FAMILIES = [
  { discovery_class: 'c1', discovery_subsystem: 's1', hypothesis_text: 'motif found everywhere' },
  { discovery_class: 'c2', discovery_subsystem: 's2', hypothesis_text: 'motif missing under raman' },
]
function discoveriesDb(opts: { stored?: readonly string[]; missingUnder?: Record<string, string[]> } = {}) {
  const stored = opts.stored ?? AYANAMSHA_SERVE_ORDER
  const missingUnder = opts.missingUnder ?? { 'motif missing under raman': ['raman'] }
  const calls: Array<{ sql: string; params: unknown[] }> = []
  const familyRow = (f: (typeof FAMILIES)[number], ids: readonly string[]) => ({
    ...f, member_count: ids.length, ayanamsha_count: ids.length, ayanamsha_ids: [...ids],
    member_discovery_ids: [], best_composite_discovery_rank: 1, max_non_obviousness_score: 1, max_consequence_score: 1,
    affected_domains_array: [], affected_domains_variant_count: 1, surface_reading: null, depth_reading: null,
    why_an_acharya_misses_it: null, novelty_class: null,
  })
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    calls.push({ sql, params })
    const pooled = !/ayanamsha_id = \$\d/.test(sql)
    if (sql.includes('JOIN unnest(')) {
      return { rows: [...stored].sort().flatMap((aya) => FAMILIES
        .filter((f) => !(missingUnder[f.hypothesis_text] ?? []).includes(aya))
        .map((f) => ({ ayanamsha_id: aya, ...f }))) }
    }
    if (sql.includes('SELECT DISTINCT ayanamsha_id FROM bodha_discoveries')) return { rows: [...stored].sort().map((ayanamsha_id) => ({ ayanamsha_id })) }
    if (sql.includes('array_agg(DISTINCT ayanamsha_id)')) {
      return { rows: FAMILIES.map((f) => familyRow(f, pooled ? stored.filter((a) => !(missingUnder[f.hypothesis_text] ?? []).includes(a)) : [LAHIRI])) }
    }
    if (sql.includes('COUNT(DISTINCT ayanamsha_id)')) return { rows: [{ n: String(pooled ? stored.length : 1) }] }
    if (sql.includes('GROUP BY discovery_class')) return { rows: [{ total: '2' }] }
    if (sql.includes('COUNT(*)::text')) return { rows: [{ total: '2' }] }
    if (sql.includes('SELECT discovery_id')) return { rows: [] }
    return { rows: [] }
  })
  return calls
}

describe('query_discoveries: the "n/N ayanamshas agree" chip is rebuilt as the labelled cross-check', () => {
  beforeEach(() => { queryMock.mockReset() })

  it('default (Lahiri): no "1/1 ayanamshas agree" anywhere; the cross-check is advertised, not computed', async () => {
    const calls = discoveriesDb()
    const res = await queryDiscoveriesCapability.handler({ chart_id: CHART }, undefined)
    const content = res.content as Record<string, any>
    expect(content.ayanamsha_id).toBe(LAHIRI)
    expect(JSON.stringify(content)).not.toMatch(/\d+\/\d+ ayanamshas agree/)
    expect(content.discovery_families.every((f: Cc) => !('ayanamsha_agreement' in f) && !(KEY in f))).toBe(true)
    expect(content.ayanamsha_cross_check_available).toBe(true)
    expect(calls.some((c) => c.sql.includes('JOIN unnest('))).toBe(false)
  })

  it('include_cross_check: per-family labelled cross-check computed from the OTHER ayanamshas; primary families unchanged', async () => {
    discoveriesDb()
    const plain = (await queryDiscoveriesCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, any>
    const res = (await queryDiscoveriesCapability.handler({ chart_id: CHART, include_cross_check: true }, undefined)).content as Record<string, any>
    const strip = (fs: Cc[]) => fs.map(({ [KEY]: _x, ...rest }) => rest)
    expect(strip(res.discovery_families)).toEqual(strip(plain.discovery_families))
    const [everywhere, missing] = res.discovery_families.map(cc)
    expect(everywhere.summary).toBe('Agrees across all five ayanamshas')
    expect(everywhere.others.map((o: Cc) => o.ayanamsha_id)).toEqual(OTHERS_IN_ORDER)
    expect(missing.agreement).toBe('dissent')
    expect(missing.summary).toBe('Dissent: Raman: same motif absent (primary present)')
    expect(missing.heading).toBe('Cross-check, not the reading')
  })

  it('a single-ayanamsha chart gets not_available/single_ayanamsha_chart (never "1/1")', async () => {
    discoveriesDb({ stored: [LAHIRI] })
    const content = (await queryDiscoveriesCapability.handler({ chart_id: CHART, include_cross_check: true }, undefined)).content as Record<string, any>
    expect(content[KEY]).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(JSON.stringify(content)).not.toMatch(/1\/1|\d+\/\d+ ayanamshas agree/)
    expect(content.discovery_families.every((f: Cc) => !(KEY in f))).toBe(true)
  })

  it('an explicit ayanamsha filter (krishnamurti) never says "1/1 ayanamshas agree" and anchors on the requested one', async () => {
    discoveriesDb()
    const content = (await queryDiscoveriesCapability.handler({ chart_id: CHART, ayanamsha_id: 'kp', include_cross_check: true }, undefined)).content as Record<string, any>
    expect(JSON.stringify(content)).not.toMatch(/\d+\/\d+ ayanamshas agree/)
    expect(cc(content.discovery_families[0]).primary_id).toBe('krishnamurti')
  })

  it('"all" is unchanged: the raw pooled chip, no envelope', async () => {
    const calls = discoveriesDb()
    const content = (await queryDiscoveriesCapability.handler({ chart_id: CHART, ayanamsha_id: 'all', include_cross_check: true }, undefined)).content as Record<string, any>
    expect(content.ayanamsha_scope).toBe('all')
    expect(content.discovery_families[0].ayanamsha_agreement).toBe('5/5 ayanamshas agree')
    expect(content.discovery_families[1].ayanamsha_agreement).toBe('4/5 ayanamshas agree')
    expect(KEY in content).toBe(false)
    expect(content.discovery_families.every((f: Cc) => !(KEY in f))).toBe(true)
    expect(calls.some((c) => c.sql.includes('JOIN unnest('))).toBe(false)
  })
})

// ── query_pratijna ────────────────────────────────────────────────────────────────────────────────
function pratijnaDb(opts: { stored?: readonly string[]; status?: Record<string, string> } = {}) {
  const stored = opts.stored ?? AYANAMSHA_SERVE_ORDER
  const status = opts.status ?? {}
  const perSystem = Object.fromEntries(AYANAMSHA_SERVE_ORDER.map((a) => [a, { varga_sign: 'Leo', dignity_state: a === 'raman' ? 'own' : 'friend', band: 0.5 }]))
  const lahiriRow = {
    pratijna_id: 'p1', ayanamsha_id: LAHIRI, event_class_id: 'career_rise', status: 'promised', grade: 'A',
    varga_confirmation: { varga: 'D10', graha: 'Sun', per_system: perSystem, consensus_dignity: 'friend', unanimous: false, dissent: [{ ayanamsha_id: 'raman' }] },
    supporting_signal_ids: null, contradicting_signal_ids: null, derivation: {}, formula_version: 'v4', computed_date: '2026-10-01',
  }
  const calls: Array<{ sql: string; params: unknown[] }> = []
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    calls.push({ sql, params })
    if (sql.includes('event_class_id = ANY($3::text[])')) {
      return { rows: [...stored].sort().map((aya) => ({ event_class_id: 'career_rise', ayanamsha_id: aya, status: status[aya] ?? 'promised' })) }
    }
    if (sql.includes('COUNT(*)::text')) return { rows: [{ total: '1' }] }
    if (sql.includes('FROM bodha_pratijna')) return { rows: [lahiriRow] }
    return { rows: [] }
  })
  return calls
}

describe('query_pratijna: labelled cross-check beside the pooled consensus chip', () => {
  beforeEach(() => { queryMock.mockReset() })

  it('default: the Lahiri row, the consensus chip untouched, no envelope', async () => {
    const calls = pratijnaDb()
    const content = (await queryPratijnaCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, any>
    expect(content.ayanamsha_id).toBe(LAHIRI)
    expect(content.rows[0].ayanamsha_id).toBe(LAHIRI)
    expect(content.rows[0].consensus_chip).toBe('4/5 agree: friend (1 dissent)') // derived pooled value, kept
    expect(KEY in content.rows[0]).toBe(false)
    expect(content.ayanamsha_cross_check_available).toBe(true)
    expect(calls.some((c) => c.sql.includes('event_class_id = ANY($3::text[])'))).toBe(false)
  })

  it('include_cross_check: status from the other ayanamshas + varga dignity from per_system; dissent named with its value', async () => {
    pratijnaDb({ status: { krishnamurti: 'denied' } })
    const plain = (await queryPratijnaCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, any>
    const content = (await queryPratijnaCapability.handler({ chart_id: CHART, include_cross_check: true }, undefined)).content as Record<string, any>
    const { [KEY]: x, ...rowRest } = content.rows[0]
    const { ayanamsha_cross_check_available: _a, ...plainRest } = plain
    void plainRest
    expect(rowRest).toEqual(plain.rows[0])
    expect(x.others.map((o: Cc) => o.ayanamsha_id)).toEqual(OTHERS_IN_ORDER)
    expect(x.agreement).toBe('dissent')
    expect(x.summary).toBe('Dissent: Krishnamurti: status denied (primary promised); Raman: varga dignity own (primary friend)')
  })

  it('single-ayanamsha chart -> not_available/single_ayanamsha_chart', async () => {
    pratijnaDb({ stored: [LAHIRI] })
    const content = (await queryPratijnaCapability.handler({ chart_id: CHART, include_cross_check: true }, undefined)).content as Record<string, any>
    expect(content[KEY]).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(KEY in content.rows[0]).toBe(false)
  })

  it('"all" unchanged: no envelope', async () => {
    pratijnaDb()
    const content = (await queryPratijnaCapability.handler({ chart_id: CHART, ayanamsha_id: 'all', include_cross_check: true }, undefined)).content as Record<string, any>
    expect(content.ayanamsha_scope).toBe('all')
    expect(KEY in content).toBe(false)
    expect(KEY in content.rows[0]).toBe(false)
  })
})

// ── table test over every surface changed in PR-3 ─────────────────────────────────────────────────
describe('every PR-3 surface: Lahiri primary, include_cross_check absent => no envelope except the identity facts, "all" raw', () => {
  const surfaces = [
    { name: 'get_positions', cap: getPositionsCapability, setup: () => positionsDb(), identity: true, args: {} },
    { name: 'get_dashas', cap: getDashasCapability, setup: () => dashasDb(), identity: true, args: dashaArgs },
    { name: 'query_discoveries', cap: queryDiscoveriesCapability, setup: () => discoveriesDb(), identity: false, args: {} },
    { name: 'query_pratijna', cap: queryPratijnaCapability, setup: () => pratijnaDb(), identity: false, args: {} },
  ]
  beforeEach(() => {
    queryMock.mockReset()
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
  })

  it.each(surfaces)('$name declares the boolean include_cross_check input', ({ cap }) => {
    expect((cap.input_schema as Record<string, any>)['include_cross_check']?.type).toBe('boolean')
  })

  it.each(surfaces)('$name: default is Lahiri; the envelope appears on the default call only for identity-fact surfaces', async ({ cap, setup, identity, args }) => {
    setup()
    const content = (await cap.handler({ chart_id: CHART, ...args }, undefined)).content as Record<string, any>
    expect(content.ayanamsha_id).toBe(LAHIRI)
    expect(KEY in content).toBe(identity)
    if (!identity) expect(content.rows.every((r: Cc) => !(KEY in r))).toBe(true)
  })

  it.each(surfaces)('$name: "all" is the raw option and carries no envelope', async ({ cap, setup, args }) => {
    setup()
    const content = (await cap.handler({ chart_id: CHART, ...args, ayanamsha_id: 'all' }, undefined)).content as Record<string, any>
    expect(content.ayanamsha_scope).toBe('all')
    expect(KEY in content).toBe(false)
  })
})
