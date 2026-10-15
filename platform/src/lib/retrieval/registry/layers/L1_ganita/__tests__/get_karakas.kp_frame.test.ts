/**
 * SS N-357 — get_karakas system=kp is the KP branch: Krishnamurti Paddhati has ONE frame by
 * doctrine, so it is read at `krishnamurti` WHATEVER ayanamsha_id / ayanamsha_scope the caller
 * passes, and labelled "KP frame (Krishnamurti ayanamsha)". The non-KP branches are unchanged
 * (Lahiri default, "all" opt-out, unknown id = error). The query layer is mocked.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { getKarakasCapability } from '../get_karakas'
import { KP_FRAME_AYANAMSHA, KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'

type Content = Record<string, unknown>
const calls = () => queryMock.mock.calls.map((c) => ({ sql: String(c[0]), params: (c[1] as unknown[]) ?? [] }))
/** Every ayanamsha-bearing id the SQL was parameterised with (the chart_facts reads: page + count). */
const ayaParams = () => calls().flatMap((c) => c.params.filter((p) => typeof p === 'string' && p !== CHART_ID)) as string[]

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: unknown) =>
    String(sql).includes('COUNT(*)') ? { rows: [{ total: '1' }] } : { rows: [{ fact_id: 'f1', fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti' }] },
  )
})

describe('get_karakas system=kp: read at krishnamurti whatever the caller passes', () => {
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
    const res = await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'kp', ...extra }, undefined)
    expect(res.is_error).toBe(false)
    const ids = ayaParams()
    expect(ids).toContain('krishnamurti')
    expect(ids).toContain(KP_FRAME_AYANAMSHA)
    for (const other of [LAHIRI, 'true_chitra', 'raman', 'surya_siddhanta_classical']) expect(ids).not.toContain(other)
    expect(calls().every((c) => /ayanamsha_id = \$\d+/.test(c.sql))).toBe(true)
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
    const all = (await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'kp', ayanamsha_id: 'all' }, undefined)).content as Content
    expect(all['ayanamsha_note']).toBe("KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope 'all' does not apply here")
    const raman = (await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'kp', ayanamsha_id: 'raman' }, undefined)).content as Content
    expect(String(raman['ayanamsha_note'])).toContain("'raman'")
  })

  it('an explicit krishnamurti request carries the label and no note', async () => {
    const c = (await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'kp', ayanamsha_id: 'krishnamurti' }, undefined)).content as Content
    expect(c['frame_label']).toBe(KP_FRAME_LABEL)
    expect(c['ayanamsha_note']).toBeUndefined()
  })

  it('serves only the kp* categories', async () => {
    await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'kp', ayanamsha_id: LAHIRI }, undefined)
    const cats = calls()[0]!.params[1] as string[]
    expect(cats.length).toBeGreaterThan(0)
    expect(cats.every((c) => c.startsWith('kp'))).toBe(true)
  })
})

describe('get_karakas non-KP branches: unchanged', () => {
  it('system=jaimini, no id -> Lahiri default, no KP label', async () => {
    const res = await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'jaimini' }, undefined)
    expect(calls()[0]!.params).toContain(LAHIRI)
    expect(ayaParams()).not.toContain('krishnamurti')
    const c = res.content as Content
    expect(c['ayanamsha_id']).toBe(LAHIRI)
    expect(c['frame_label']).toBeUndefined()
    expect(c['ayanamsha_note']).toBeUndefined()
  })

  it('no system, no id -> Lahiri default', async () => {
    await getKarakasCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(calls()[0]!.params).toContain(LAHIRI)
  })

  it('system=jaimini + "all" -> pooled (no ayanamsha filter), ayanamsha_scope all', async () => {
    const res = await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'jaimini', ayanamsha_id: 'all' }, undefined)
    expect(calls().every((c) => !/ayanamsha_id = \$\d+/.test(c.sql))).toBe(true)
    expect((res.content as Content)['ayanamsha_scope']).toBe('all')
    expect((res.content as Content)['frame_label']).toBeUndefined()
  })

  it('no system + ayanamsha_scope "all" -> pooled', async () => {
    const res = await getKarakasCapability.handler({ chart_id: CHART_ID, ayanamsha_scope: 'all' }, undefined)
    expect((res.content as Content)['ayanamsha_scope']).toBe('all')
  })

  it('system=jaimini + raman -> raman (the id is honoured outside the KP branch)', async () => {
    await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'jaimini', ayanamsha_id: 'raman' }, undefined)
    expect(calls()[0]!.params).toContain('raman')
  })

  it('system=jaimini + nonsense id -> still an error (validation unchanged)', async () => {
    queryMock.mockClear()
    const res = await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'jaimini', ayanamsha_id: 'not_an_ayanamsha_xyz' }, undefined)
    expect(res.is_error).toBe(true)
    expect(queryMock).not.toHaveBeenCalled()
  })
})
