/**
 * kp_no_false_note.test.ts — SS N-368 (1): NO FALSE NOTES.
 *
 * When the web bridge INJECTS the Lahiri default (`ayanamsha_id: lahiri_chitrapaksha` + the server
 * marker `ayanamsha_injected: true`) the caller asked for nothing, so a KP read must NOT say "the
 * requested ayanamsha_id/scope '...' does not apply here". The note is for an EXPLICIT request only:
 * an explicit non-Krishnamurti id (Lahiri included, an alias, raman, "all", scope "all", nonsense).
 * The frame itself (`ayanamsha_id: 'krishnamurti'`, `frame_label` / `kp_frame`) is ALWAYS there.
 *
 * Covers every KP read that can emit `ayanamsha_note`: get_karakas (system=kp, KP categories, the
 * mixed default page), get_nakshatra (domain=kp, KP categories, the mixed default page), get_kp_cusps,
 * the thirteen typed readers and chart_facts_query. (get_dashas is in get_dashas_kp_frame.test.ts and
 * get_dashas_kp_system_all.test.ts.)
 *
 * No database: the five-ayanamsha SQL simulator. This file FAILS on the pre-N-368 code (the injected
 * Lahiri is reported as a request that was not applied) and passes after.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createFiveAyanamshaFakeDb, KRISHNAMURTI_FIRST_FIXTURE_ORDER, type FixtureRow } from '../../../__tests__/helpers/five_ayanamsha_fake_db'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const KP_CATS = ['cusp_kp_lords', 'graha_kp_lords', 'kp_cuspal_significators', 'kp_house_significators', 'kp_planet_significations', 'kp_ruling_planets_natal']

import { getKarakasCapability } from '../get_karakas'
import { getNakshatraCapability } from '../get_nakshatra'
import { getKpCuspsCapability } from '../get_kp_cusps'
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
import { getCatalog } from '../../../catalog'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import type { CapabilityDescriptor } from '../../../types'

function fixture(owns: string[]): FixtureRow[] {
  const rows: FixtureRow[] = []
  const cats = [...KP_CATS, ...owns, 'graha_position', 'karaka_chara', 'sade_sati_cycle', 'graha_avastha_baladi']
  for (const ayanamsha_id of KRISHNAMURTI_FIRST_FIXTURE_ORDER) {
    for (const fact_category of new Set(cats)) {
      for (let i = 0; i < 2; i += 1) {
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

const readerOwn: Array<[string, string, Pick<CapabilityDescriptor, 'handler'>]> = [
  ['get_aspects', 'aspect_parashari_received', getAspectsCapability],
  ['get_ashtakavarga', 'ashtakavarga_bindu', getAshtakavargaCapability],
  ['get_avasthas', 'graha_avastha_baladi', getAvasthsCapability],
  ['get_bhava_bala', 'house_bhava_bala_total', getBhavaBalaCapability],
  ['get_dignity', 'graha_dignity_per_varga', getDignityCapability],
  ['get_dispositors', 'graha_dispositor_chain', getDispositorsCapability],
  ['get_panchanga', 'panchanga_karana', getPanchangaCapability],
  ['get_positions', 'graha_position', getPositionsCapability],
  ['get_sade_sati', 'sade_sati_cycle', getSadeSatiCapability],
  ['get_sensitive_points', 'esoteric_point_avayogi', getSensitivePointsCapability],
  ['get_strength', 'graha_shadbala_total', getStrengthCapability],
  ['get_structural', 'sambandha_grade', getStructuralSignalsCapability],
  ['get_yoga_dosha', 'yoga_label', getYogaDoshaCapability],
]

const fake = createFiveAyanamshaFakeDb(fixture(readerOwn.map((r) => r[1])), { applyCategoryFilter: true })
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => fake.query(args[0], args[1]),
}))

type Content = Record<string, unknown>
beforeEach(() => fake.reset())

const sqlParams = () => fake.statements.flatMap((s) => s.params).flatMap((p) => (Array.isArray(p) ? p : [p]))

/**
 * [label, extra args, the value the note must name (null = NO note)].
 * `ayanamsha_injected: true` is what the web bridge adds when it fills in the Lahiri default.
 */
const requests: Array<[string, Record<string, unknown>, string | null]> = [
  ['id omitted (direct call)', {}, null],
  ['bridge-injected Lahiri', { ayanamsha_id: LAHIRI, ayanamsha_injected: true }, null],
  ['the marker alone, no id', { ayanamsha_injected: true }, null],
  ['explicit krishnamurti', { ayanamsha_id: 'krishnamurti' }, null],
  ['explicit Lahiri (no marker)', { ayanamsha_id: LAHIRI }, LAHIRI],
  ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }, 'LAHIRI'],
  ['raman', { ayanamsha_id: 'raman' }, 'raman'],
  ['"all"', { ayanamsha_id: 'all' }, 'all'],
  ['scope "all" (what the bridge sends for "all")', { ayanamsha_scope: 'all' }, 'all'],
  ['a marker cannot mask an explicit non-primary id', { ayanamsha_id: 'raman', ayanamsha_injected: true }, 'raman'],
  ['a nonsense id', { ayanamsha_id: 'not_an_ayanamsha_xyz' }, 'not_an_ayanamsha_xyz'],
]

/** Assert the note rule + the always-present frame + nothing leaked. */
function expectNoteRule(c: Content, requested: string | null, via: string) {
  if (requested === null) {
    expect(c['ayanamsha_note'], `${via}: false note`).toBeUndefined()
  } else {
    expect(String(c['ayanamsha_note']), `${via}: note missing`).toContain('KP has one frame by doctrine (Krishnamurti)')
    expect(String(c['ayanamsha_note'])).toContain(`'${requested}'`)
  }
  // the server marker is a transport detail: never in a response, never bound to SQL
  expect(JSON.stringify(c)).not.toContain('ayanamsha_injected')
  expect(sqlParams()).not.toContain(true)
}

describe('get_karakas', () => {
  const call = (a: Record<string, unknown>) => getKarakasCapability.handler({ chart_id: CHART_ID, limit: 500, ...a }, undefined) as Promise<{ content: Content; is_error: boolean }>

  describe.each([
    ['system=kp', { system: 'kp' }],
    ['a KP-only categories list', { categories: ['kp_cuspal_significators', 'kp_ruling_planets_natal'] }],
  ] as Array<[string, Record<string, unknown>]>)('%s', (_n, base) => {
    it.each(requests)('%s', async (_label, extra, requested) => {
      const res = await call({ ...base, ...extra })
      expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
      expect(res.content['ayanamsha_id']).toBe('krishnamurti')
      expect(res.content['frame_label']).toBe(KP_FRAME_LABEL)
      expectNoteRule(res.content, requested, 'get_karakas KP')
    })
  })

  it.each(requests.filter(([l]) => l !== 'a nonsense id'))('the mixed default page: %s', async (_label, extra, requested) => {
    const res = await call(extra)
    expect(res.is_error).toBe(false)
    expect((res.content['kp_frame'] as Content)['ayanamsha_id']).toBe('krishnamurti')
    expect((res.content['kp_frame'] as Content)['frame_label']).toBe(KP_FRAME_LABEL)
    expectNoteRule(res.content, requested, 'get_karakas mixed')
  })
})

describe('get_nakshatra', () => {
  const call = (a: Record<string, unknown>) => getNakshatraCapability.handler({ chart_id: CHART_ID, limit: 500, ...a }, undefined) as Promise<{ content: Content; is_error: boolean }>

  describe.each([
    ['domain=kp', { domain: 'kp' }],
    ['a KP-only categories list', { categories: ['cusp_kp_lords', 'graha_kp_lords'] }],
  ] as Array<[string, Record<string, unknown>]>)('%s', (_n, base) => {
    it.each(requests)('%s', async (_label, extra, requested) => {
      const res = await call({ ...base, ...extra })
      expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
      expect(res.content['ayanamsha_id']).toBe('krishnamurti')
      expect(res.content['frame_label']).toBe(KP_FRAME_LABEL)
      expectNoteRule(res.content, requested, 'get_nakshatra KP')
    })
  })

  it.each(requests.filter(([l]) => l !== 'a nonsense id'))('the mixed default page: %s', async (_label, extra, requested) => {
    const res = await call(extra)
    expect(res.is_error).toBe(false)
    expect((res.content['kp_frame'] as Content)['ayanamsha_id']).toBe('krishnamurti')
    expectNoteRule(res.content, requested, 'get_nakshatra mixed')
  })
})

describe('get_kp_cusps', () => {
  const call = (a: Record<string, unknown>) => getKpCuspsCapability.handler({ chart_id: CHART_ID, ...a }, undefined) as Promise<{ content: Content; is_error: boolean }>

  it.each(requests)('%s', async (_label, extra, requested) => {
    const res = await call(extra)
    expect(res.is_error).toBe(false)
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['kp_frame_label']).toBe(KP_FRAME_LABEL)
    expect(res.content['kp_frame_ayanamsha_id']).toBe('krishnamurti')
    expectNoteRule(res.content, requested, 'get_kp_cusps')
  })
})

describe.each(readerOwn)('%s (typed reader, KP category through a caller list)', (_name, own, cap) => {
  const call = (a: Record<string, unknown>) => cap.handler({ chart_id: CHART_ID, limit: 500, ...a }, undefined) as Promise<{ content: Content; is_error: boolean }>

  it.each(requests)('KP-only list: %s', async (_label, extra, requested) => {
    const res = await call({ categories: ['cusp_kp_lords'], ...extra })
    expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['frame_label']).toBe(KP_FRAME_LABEL)
    expectNoteRule(res.content, requested, 'typed reader KP-only')
  })

  it.each(requests.filter(([l]) => l !== 'a nonsense id'))('mixed list: %s', async (_label, extra, requested) => {
    const res = await call({ categories: ['cusp_kp_lords', own], ...extra })
    expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
    expect((res.content['kp_frame'] as Content)['ayanamsha_id']).toBe('krishnamurti')
    expectNoteRule(res.content, requested, 'typed reader mixed')
  })
})

describe('chart_facts_query', () => {
  const cap = () => getCatalog().find((c) => c.name === 'chart_facts_query')!
  const call = (a: Record<string, unknown>) =>
    cap().handler({ chart_id: CHART_ID, shape: 'rows', limit: 100, ...a }, undefined) as Promise<{ content: Content; is_error: boolean }>

  it.each(requests)('KP-only category: %s', async (_label, extra, requested) => {
    const res = await call({ category: 'cusp_kp_lords', ...extra })
    expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(res.content['frame_label']).toBe(KP_FRAME_LABEL)
    expectNoteRule(res.content, requested, 'chart_facts_query KP-only')
  })

  it.each(requests.filter(([l]) => l !== 'a nonsense id'))('mixed list: %s', async (_label, extra, requested) => {
    const res = await call({ category: 'cusp_kp_lords,graha_position', ...extra })
    expect(res.is_error, JSON.stringify(res.content).slice(0, 200)).toBe(false)
    expect((res.content['kp_frame'] as Content)['ayanamsha_id']).toBe('krishnamurti')
    expectNoteRule(res.content, requested, 'chart_facts_query mixed')
  })
})
