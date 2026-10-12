/**
 * kp_categories_generic_readers.test.ts — SS N-358 / N-359: "a KP category is served in the KP frame",
 * also when the category arrives through a GENERIC reader that does not own it.
 *
 * Thirteen typed readers pass an explicit `categories` list straight into `fact_category = ANY($2)`
 * and `chart_facts_query` does the same with `category`. Before this sweep a caller asking any of them
 * for `cusp_kp_lords` (the concept_locate pointer for "sub lord" even names chart_facts_query) read
 * the KP chain at the Lahiri primary. After it, every KP-frame category is read at `krishnamurti`
 * whatever ayanamsha_id/scope the caller passed (omitted, the primary, an alias, "all", another
 * stored id, nonsense) and the page says so. A list with no KP category keeps the previous path.
 *
 * No database: the five-ayanamsha SQL simulator holds EVERY category at ALL FIVE ayanamshas with the
 * krishnamurti rows listed FIRST and Lahiri LAST, so a KP row read at Lahiri (or a non-KP row read at
 * krishnamurti) cannot hide. This file FAILS on the pre-sweep handlers (KP rows come back at Lahiri,
 * unlabelled) and passes after.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createFiveAyanamshaFakeDb, KRISHNAMURTI_FIRST_FIXTURE_ORDER, type FixtureRow } from '../../../__tests__/helpers/five_ayanamsha_fake_db'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const ROWS = 3
const KP_CATS = ['cusp_kp_lords', 'graha_kp_lords', 'kp_cuspal_significators', 'kp_house_significators', 'kp_planet_significations', 'kp_ruling_planets_natal']

interface Reader {
  name: string
  /** one category the reader itself owns (the non-KP half of a mixed list) */
  own: string
  call: (args: Record<string, unknown>) => Promise<{ content: unknown; is_error: boolean }>
}

import { getAspectsCapability } from '../get_aspects'
import { getAshtakavargaCapability } from '../get_ashtakavarga'
import { getAvasthsCapability } from '../get_avasthas'
import { getBhavaBalaCapability } from '../get_bhava_bala'
import { getDignityCapability } from '../get_dignity'
import { getDispositorsCapability } from '../get_dispositors'
import { getPanchangaCapability } from '../get_panchanga'
import { getPositionsCapability } from '../get_positions'
import { getSadeSatiCapability } from '../get_sade_sati'
import { getSensitivePointsCapability } from '../get_sensitive_points'
import { getStrengthCapability } from '../get_strength'
import { getStructuralSignalsCapability } from '../get_structural_signals'
import { getYogaDoshaCapability } from '../get_yoga_dosha'
import { getKpCuspsCapability } from '../get_kp_cusps'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import type { CapabilityDescriptor } from '../../../types'
import { isKpFrameCategory } from '../../../kp_categories'

const typed = (name: string, own: string, cap: Pick<CapabilityDescriptor, 'handler'>): Reader => ({
  name,
  own,
  call: (a) => cap.handler({ chart_id: CHART_ID, limit: 500, ...a }, undefined) as never,
})

const readers: Reader[] = [
  typed('get_aspects', 'aspect_parashari_received', getAspectsCapability),
  typed('get_ashtakavarga', 'ashtakavarga_bindu', getAshtakavargaCapability),
  typed('get_avasthas', 'graha_avastha_baladi', getAvasthsCapability),
  typed('get_bhava_bala', 'house_bhava_bala_total', getBhavaBalaCapability),
  typed('get_dignity', 'graha_dignity_per_varga', getDignityCapability),
  typed('get_dispositors', 'graha_dispositor_chain', getDispositorsCapability),
  typed('get_panchanga', 'panchanga_karana', getPanchangaCapability),
  typed('get_positions', 'graha_position', getPositionsCapability),
  typed('get_sade_sati', 'sade_sati_cycle', getSadeSatiCapability),
  typed('get_sensitive_points', 'esoteric_point_avayogi', getSensitivePointsCapability),
  typed('get_strength', 'graha_shadbala_total', getStrengthCapability),
  typed('get_structural', 'sambandha_grade', getStructuralSignalsCapability),
  typed('get_yoga_dosha', 'yoga_label', getYogaDoshaCapability),
]

function fixture(): FixtureRow[] {
  const rows: FixtureRow[] = []
  const cats = [...KP_CATS, ...readers.map((r) => r.own), 'graha_position']
  for (const ayanamsha_id of KRISHNAMURTI_FIRST_FIXTURE_ORDER) {
    for (const fact_category of new Set(cats)) {
      for (let i = 0; i < ROWS; i += 1) {
        rows.push({
          fact_id: `${ayanamsha_id}|${fact_category}|${i}`, chart_id: CHART_ID, ayanamsha_id, fact_category,
          fact_subject: 'SUBJ', fact_key: `k${i}`, formula_id: null, fact_value_text: 'x', fact_value_num: i,
          fact_value_jsonb: null, unit: null, verification_pass_status: 'single', citation_ref: 'c', citation_human: null,
        })
      }
    }
  }
  return rows
}

const fake = createFiveAyanamshaFakeDb(fixture(), { applyCategoryFilter: true })
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => fake.query(args[0], args[1]),
}))

import { getCatalog } from '../../../catalog'

type Row = Record<string, unknown>
type Content = Record<string, unknown> & { rows: Row[] }

beforeEach(() => fake.reset())

const sqlParams = () => fake.statements.flatMap((s) => s.params).flatMap((p) => (Array.isArray(p) ? p : [p]))
const idsOf = (rows: Row[]) => new Set(rows.map((r) => r['ayanamsha_id']))

/** [label, extra args] — every way a caller can (not) name an ayanamsha */
const requests: Array<[string, Record<string, unknown>]> = [
  ['no id', {}],
  ['the Lahiri primary id', { ayanamsha_id: LAHIRI }],
  ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }],
  ['raman', { ayanamsha_id: 'raman' }],
  ['"all"', { ayanamsha_id: 'all' }],
  ['ayanamsha_scope "all"', { ayanamsha_scope: 'all' }],
  ['a nonsense id', { ayanamsha_id: 'not_an_ayanamsha_xyz' }],
]

describe('the readers are the real registered capabilities', () => {
  it('every reader of this file is in the catalog under its own name', () => {
    const names = new Set(getCatalog().map((c) => c.name))
    for (const r of readers) expect(names.has(r.name), r.name).toBe(true)
  })
})

describe.each(readers)('$name', (r) => {
  describe('an explicit list naming ONLY KP categories is read wholly at krishnamurti', () => {
    it.each(requests)('%s', async (_label, extra) => {
      const res = await r.call({ categories: ['cusp_kp_lords', 'kp_ruling_planets_natal'], ...extra })
      expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
      const c = res.content as Content
      expect(c.rows.length).toBe(2 * ROWS)
      expect(idsOf(c.rows)).toEqual(new Set(['krishnamurti']))
      for (const row of c.rows) expect(row['frame_label']).toBe(KP_FRAME_LABEL)
      expect(c['ayanamsha_id']).toBe('krishnamurti')
      expect(c['frame_label']).toBe(KP_FRAME_LABEL)
      expect(c['ayanamsha_scope']).toBeUndefined()
      // no statement of the call ever bound the Lahiri primary
      expect(sqlParams()).not.toContain(LAHIRI)
      // the caller asked for another frame: it is told that the request did not apply
      const asked = JSON.stringify(extra) !== '{}'
      if (asked) expect(String(c['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
    })

    it('an explicit krishnamurti request is the canonical frame with no note', async () => {
      const res = await r.call({ categories: ['cusp_kp_lords'], ayanamsha_id: 'krishnamurti' })
      const c = res.content as Content
      expect(idsOf(c.rows)).toEqual(new Set(['krishnamurti']))
      expect(c['ayanamsha_note']).toBeUndefined()
    })
  })

  describe('a MIXED list reads KP categories at krishnamurti and the rest at the requested id', () => {
    const mixed = (own: string) => ['cusp_kp_lords', own, 'graha_kp_lords']

    it.each(requests.filter(([l]) => l !== 'a nonsense id'))('%s', async (label, extra) => {
      const res = await r.call({ categories: mixed(r.own), ...extra })
      expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
      const c = res.content as Content
      const kp = c.rows.filter((row) => isKpFrameCategory(row['fact_category']))
      const other = c.rows.filter((row) => !isKpFrameCategory(row['fact_category']))
      expect(kp.length).toBe(2 * ROWS)
      expect(idsOf(kp)).toEqual(new Set(['krishnamurti']))
      for (const row of kp) expect(row['frame_label']).toBe(KP_FRAME_LABEL)
      expect(other.length).toBeGreaterThan(0)
      for (const row of other) expect(row['frame_label']).toBeUndefined()
      const pooled = label === '"all"' || label === 'ayanamsha_scope "all"'
      const want = pooled ? new Set<string>(KRISHNAMURTI_FIRST_FIXTURE_ORDER) : new Set([label === 'raman' ? 'raman' : LAHIRI])
      expect(idsOf(other)).toEqual(want)
      expect(c['kp_frame']).toEqual({ ayanamsha_id: 'krishnamurti', frame_label: KP_FRAME_LABEL, categories: ['cusp_kp_lords', 'graha_kp_lords'] })
    })

    it('a nonsense id is still an error for the non-KP part, with no SQL', async () => {
      const res = await r.call({ categories: mixed(r.own), ayanamsha_id: 'not_an_ayanamsha_xyz' })
      expect(res.is_error).toBe(true)
      expect(fake.statements).toEqual([])
    })
  })

  describe('a list with NO KP category keeps the previous path', () => {
    it('is read at the Lahiri primary, unlabelled, no KP fields', async () => {
      const res = await r.call({ categories: [r.own] })
      expect(res.is_error).toBe(false)
      const c = res.content as Content
      expect(c.rows.length).toBeGreaterThan(0)
      expect(idsOf(c.rows)).toEqual(new Set([LAHIRI]))
      for (const row of c.rows) expect(row['frame_label']).toBeUndefined()
      expect(c['ayanamsha_id']).toBe(LAHIRI)
      expect(c['kp_frame']).toBeUndefined()
      expect(c['frame_label']).toBeUndefined()
    })
  })
})

describe('chart_facts_query (query_chart_facts / ganita_chart_facts_get)', () => {
  const cap = () => getCatalog().find((c) => c.name === 'chart_facts_query')!
  const call = (args: Record<string, unknown>) =>
    cap().handler({ chart_id: CHART_ID, shape: 'rows', limit: 100, ...args }, undefined) as Promise<{ content: Content; is_error: boolean }>

  it('is registered', () => {
    expect(cap()).toBeDefined()
  })

  it.each(requests)('a KP-only category: %s', async (_label, extra) => {
    const res = await call({ category: 'cusp_kp_lords', ...extra })
    expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
    expect(res.content.rows.length).toBe(ROWS)
    expect(idsOf(res.content.rows)).toEqual(new Set(['krishnamurti']))
    for (const row of res.content.rows) expect(row['frame_label']).toBe(KP_FRAME_LABEL)
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['frame_label']).toBe(KP_FRAME_LABEL)
    expect(sqlParams()).not.toContain(LAHIRI)
  })

  it('a comma list of KP categories is KP-only too (pivoted shape labels each fact)', async () => {
    const res = await call({ category: 'cusp_kp_lords,graha_kp_lords', shape: 'pivoted' })
    const facts = (res.content as unknown as { facts: Row[] }).facts
    expect(facts.length).toBeGreaterThan(0)
    for (const f of facts) expect(f['frame_label']).toBe(KP_FRAME_LABEL)
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(sqlParams()).not.toContain(LAHIRI)
  })

  it.each([
    ['no id', {}, LAHIRI],
    ['the Lahiri primary id', { ayanamsha_id: LAHIRI }, LAHIRI],
    ['raman', { ayanamsha_id: 'raman' }, 'raman'],
  ] as Array<[string, Record<string, unknown>, string]>)('a mixed list: %s', async (_label, extra, otherAya) => {
    const res = await call({ category: 'cusp_kp_lords,graha_position', ...extra })
    expect(res.is_error).toBe(false)
    const rows = res.content.rows
    const kp = rows.filter((r) => isKpFrameCategory(r['fact_category']))
    const other = rows.filter((r) => !isKpFrameCategory(r['fact_category']))
    expect(kp.length).toBe(ROWS)
    expect(idsOf(kp)).toEqual(new Set(['krishnamurti']))
    for (const row of kp) expect(row['frame_label']).toBe(KP_FRAME_LABEL)
    expect(other.length).toBe(ROWS)
    expect(idsOf(other)).toEqual(new Set([otherAya]))
    for (const row of other) expect(row['frame_label']).toBeUndefined()
    expect(res.content['kp_frame']).toEqual({ ayanamsha_id: 'krishnamurti', frame_label: KP_FRAME_LABEL, categories: ['cusp_kp_lords'] })
  })

  it('a non-KP category keeps the previous path (Lahiri default, no KP fields)', async () => {
    const res = await call({ category: 'graha_position' })
    expect(idsOf(res.content.rows)).toEqual(new Set([LAHIRI]))
    expect(res.content['frame_label']).toBeUndefined()
    expect(res.content['kp_frame']).toBeUndefined()
    for (const row of res.content.rows) expect(row['frame_label']).toBeUndefined()
  })
})

describe('get_kp_cusps labels the frame it was read in (SS N-362 b: one frame, a passed non-KP id is ignored)', () => {
  const call = (args: Record<string, unknown>) =>
    getKpCuspsCapability.handler({ chart_id: CHART_ID, ...args }, undefined) as Promise<{ content: Record<string, unknown>; is_error: boolean }>

  it('omitted: krishnamurti and the canonical label, no note', async () => {
    const res = await call({})
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['kp_frame_label']).toBe(KP_FRAME_LABEL)
    expect(res.content['kp_frame_ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['ayanamsha_note']).toBeUndefined()
  })

  it('an explicit non-KP id is IGNORED: krishnamurti is read, the label stays canonical, the note says the request did not apply', async () => {
    const res = await call({ ayanamsha_id: LAHIRI })
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['kp_frame_label']).toBe(KP_FRAME_LABEL)
    expect(res.content['kp_frame_ayanamsha_id']).toBe('krishnamurti')
    expect(String(res.content['ayanamsha_note'])).toContain(`the requested ayanamsha_id/scope '${LAHIRI}' does not apply here`)
    expect(sqlParams()).not.toContain(LAHIRI)
  })
})
