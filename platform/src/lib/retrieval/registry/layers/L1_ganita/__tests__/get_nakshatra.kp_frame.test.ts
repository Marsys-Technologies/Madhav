/**
 * SS N-357 — get_nakshatra domain=kp is the KP branch: Krishnamurti Paddhati has ONE frame by
 * doctrine, so it is read at `krishnamurti` WHATEVER ayanamsha_id / ayanamsha_scope the caller
 * passes, and labelled "KP frame (Krishnamurti ayanamsha)". The non-KP domains are unchanged
 * (Lahiri default + INVARIANT sentinel, "all" opt-out, unknown id = error). Query layer mocked.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { getNakshatraCapability } from '../get_nakshatra'
import { KP_FRAME_AYANAMSHA, KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const KP_DOMAIN_CATEGORIES = ['graha_kp_lords', 'cusp_kp_lords', 'kp_house_significators', 'kp_planet_significations']

type Content = Record<string, unknown>
const calls = () => queryMock.mock.calls.map((c) => ({ sql: String(c[0]).replace(/\s+/g, ' '), params: (c[1] as unknown[]) ?? [] }))

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [{ fact_id: 'f1', fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti' }] })
})

describe('get_nakshatra domain=kp: read at krishnamurti whatever the caller passes', () => {
  const cases: Array<[string, Record<string, unknown>, boolean]> = [
    ['the Lahiri primary id', { ayanamsha_id: LAHIRI }, true],
    ['no id', {}, false],
    ['"all"', { ayanamsha_id: 'all' }, true],
    ['ayanamsha_scope "all"', { ayanamsha_scope: 'all' }, true],
    ['the alias "kp"', { ayanamsha_id: 'kp' }, false],
    ['the alias "LAHIRI"', { ayanamsha_id: 'LAHIRI' }, true],
    ['a nonsense id', { ayanamsha_id: 'not_an_ayanamsha_xyz' }, true],
    ['raman', { ayanamsha_id: 'raman' }, true],
  ]

  it.each(cases)('%s -> SQL param krishnamurti, labelled', async (_name, extra, noteExpected) => {
    const res = await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'kp', ...extra }, undefined)
    expect(res.is_error).toBe(false)
    const [call] = calls()
    expect(call!.params[1]).toEqual(KP_DOMAIN_CATEGORIES)
    // $5 is the single ayanamsha predicate, after chart, categories, limit, offset
    expect(call!.params[4]).toBe('krishnamurti')
    expect(call!.params[4]).toBe(KP_FRAME_AYANAMSHA)
    expect(call!.sql).toContain("ayanamsha_id IN ($5, 'INVARIANT')")
    for (const other of [LAHIRI, 'true_chitra', 'raman', 'surya_siddhanta_classical']) expect(call!.params).not.toContain(other)
    const content = res.content as Content
    expect(content['ayanamsha_id']).toBe('krishnamurti')
    expect(content['ayanamsha_scope']).toBeUndefined()
    expect(content['frame_label']).toBe(KP_FRAME_LABEL)
    expect(content['frame_label']).toBe('KP frame (Krishnamurti ayanamsha)')
    if (noteExpected) {
      expect(String(content['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
      expect(String(content['ayanamsha_note'])).toContain('does not apply here')
    } else {
      expect(content['ayanamsha_note']).toBeUndefined()
    }
  })

  it('the note names the request that was not applied', async () => {
    const all = (await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'kp', ayanamsha_id: 'all' }, undefined)).content as Content
    expect(all['ayanamsha_note']).toBe("KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope 'all' does not apply here")
    const raman = (await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'kp', ayanamsha_id: 'raman' }, undefined)).content as Content
    expect(String(raman['ayanamsha_note'])).toContain("'raman'")
  })

  it('an explicit krishnamurti request carries the label and no note', async () => {
    const c = (await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'kp', ayanamsha_id: 'krishnamurti' }, undefined)).content as Content
    expect(c['frame_label']).toBe(KP_FRAME_LABEL)
    expect(c['ayanamsha_note']).toBeUndefined()
  })

  it('an empty KP page is still read at krishnamurti and labelled, with the empty reason at krishnamurti', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    const c = (await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'kp', ayanamsha_id: LAHIRI }, undefined)).content as Content
    expect(calls()[0]!.params[4]).toBe('krishnamurti')
    expect(c['frame_label']).toBe(KP_FRAME_LABEL)
    expect(String(c['empty_reason'])).toContain("ayanamsha 'krishnamurti'")
  })
})

describe('get_nakshatra non-KP domains: unchanged', () => {
  it('domain=identity, no id -> Lahiri default (+INVARIANT), no KP label', async () => {
    const res = await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'identity' }, undefined)
    expect(calls()[0]!.params[4]).toBe(LAHIRI)
    expect(calls()[0]!.sql).toContain("ayanamsha_id IN ($5, 'INVARIANT')")
    const c = res.content as Content
    expect(c['ayanamsha_id']).toBe(LAHIRI)
    expect(c['frame_label']).toBeUndefined()
    expect(c['ayanamsha_note']).toBeUndefined()
  })

  // SS N-358: the DEFAULT page now names KP categories, so it is a mixed page (see get_nakshatra.kp_categories.test.ts);
  // the non-KP intent of this check is kept with an explicit non-KP category list.
  it('no domain, non-KP category list, no id -> Lahiri default', async () => {
    await getNakshatraCapability.handler({ chart_id: CHART_ID, categories: ['graha_gandanta'] }, undefined)
    expect(calls()[0]!.params[4]).toBe(LAHIRI)
  })

  it('domain=relational + "all" -> pooled (no ayanamsha filter), ayanamsha_scope all', async () => {
    const res = await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'relational', ayanamsha_id: 'all' }, undefined)
    expect(calls()[0]!.sql).not.toMatch(/ayanamsha_id (=|IN) \(?\$5/)
    expect(calls()[0]!.params).toHaveLength(4)
    const c = res.content as Content
    expect(c['ayanamsha_scope']).toBe('all')
    expect(c['frame_label']).toBeUndefined()
  })

  it('no domain + non-KP category list + ayanamsha_scope "all" -> pooled', async () => {
    const res = await getNakshatraCapability.handler({ chart_id: CHART_ID, categories: ['graha_gandanta'], ayanamsha_scope: 'all' }, undefined)
    expect((res.content as Content)['ayanamsha_scope']).toBe('all')
    expect(calls()[0]!.params).toHaveLength(4)
  })

  it('domain=strength + raman -> raman', async () => {
    await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'strength', ayanamsha_id: 'raman' }, undefined)
    expect(calls()[0]!.params[4]).toBe('raman')
  })

  it('domain=identity + nonsense id -> still an error, no SQL (validation unchanged)', async () => {
    const res = await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'identity', ayanamsha_id: 'not_an_ayanamsha_xyz' }, undefined)
    expect(res.is_error).toBe(true)
    expect(queryMock).not.toHaveBeenCalled()
  })
})
