/**
 * kp_categories_frame.test.ts — SS N-358: "a KP category is served in the KP frame".
 *
 * get_karakas and get_nakshatra, called WITHOUT system/domain (default pages) or with an explicit
 * `categories` list, read every KP-frame category (KP_FRAME_CATEGORIES) at `krishnamurti` and say so;
 * every other category keeps the requested/default ayanamsha. No database: the five-ayanamsha SQL
 * simulator (helpers/five_ayanamsha_fake_db.ts) holds EVERY category at ALL FIVE ayanamshas (plus
 * INVARIANT rows), with krishnamurti rows listed FIRST and Lahiri LAST, so a KP row read at Lahiri
 * (or a non-KP row read at krishnamurti) cannot hide.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createFiveAyanamshaFakeDb, KRISHNAMURTI_FIRST_FIXTURE_ORDER, type FixtureRow } from '../../../__tests__/helpers/five_ayanamsha_fake_db'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const ROWS_PER_CATEGORY = 4

const KARAKAS_KP = ['kp_cuspal_significators', 'kp_ruling_planets_natal']
const KARAKAS_OTHER = ['karaka_chara_position', 'karakamsa_position', 'swamsa_position', 'arudha_pada', 'bhava_arudha', 'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance', 'jaimini_tri_deva_role_per_graha']
const NAK_KP = ['graha_kp_lords', 'cusp_kp_lords', 'kp_house_significators', 'kp_planet_significations']
const NAK_OTHER = ['graha_nakshatra_join', 'graha_pada_join', 'graha_gandanta', 'graha_degree_flags', 'nakshatra_dispositor', 'nakshatra_exchange', 'nakshatra_conjunction', 'nakshatra_cogravity', 'graha_tara_bala', 'nakshatra_statistics']
const NAK_INVARIANT = 'nakshatra_cross_ayanamsha'

function fixture(): FixtureRow[] {
  const rows: FixtureRow[] = []
  const cats = [...KARAKAS_KP, ...KARAKAS_OTHER, ...NAK_KP, ...NAK_OTHER]
  for (const ayanamsha_id of KRISHNAMURTI_FIRST_FIXTURE_ORDER) {
    for (const fact_category of cats) {
      for (let i = 0; i < ROWS_PER_CATEGORY; i += 1) {
        rows.push({
          fact_id: `${ayanamsha_id}|${fact_category}|${i}`, chart_id: CHART_ID, ayanamsha_id, fact_category,
          fact_subject: 'SUBJ', fact_key: `k${i}`, formula_id: null, fact_value_text: 'x', fact_value_num: i,
          fact_value_jsonb: null, unit: null, verification_pass_status: 'single', citation_ref: 'c', citation_human: null,
        })
      }
    }
  }
  for (let i = 0; i < 2; i += 1) {
    rows.push({
      fact_id: `INVARIANT|${i}`, chart_id: CHART_ID, ayanamsha_id: 'INVARIANT', fact_category: NAK_INVARIANT,
      fact_subject: 'ALL', fact_key: `inv${i}`, formula_id: null, fact_value_text: 'x', fact_value_num: null,
      fact_value_jsonb: null, unit: null, verification_pass_status: 'single', citation_ref: 'c', citation_human: null,
    })
  }
  return rows
}

const fake = createFiveAyanamshaFakeDb(fixture(), { applyCategoryFilter: true })
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => fake.query(args[0], args[1]),
}))

import { getKarakasCapability } from '../get_karakas'
import { getNakshatraCapability } from '../get_nakshatra'
import { KP_FRAME_LABEL } from '@/lib/retrieval/kp_frame'
import { isKpFrameCategory } from '../../../kp_categories'

type Row = Record<string, unknown>
type Content = Record<string, unknown> & { rows: Row[] }

interface Surface {
  name: string
  call: (args: Record<string, unknown>) => Promise<{ content: unknown; is_error: boolean }>
  kpDefault: string[]
  otherDefault: string[]
  /** categories whose rows are stored under INVARIANT (served with the primary filter) */
  invariant: string[]
  /** the explicit non-KP list used for the mixed cases */
  explicitOther: string[]
}
const surfaces: Surface[] = [
  {
    name: 'get_karakas',
    call: (a) => getKarakasCapability.handler({ chart_id: CHART_ID, limit: 2000, ...a }, undefined) as never,
    kpDefault: KARAKAS_KP, otherDefault: KARAKAS_OTHER, invariant: [], explicitOther: ['arudha_pada', 'swamsa_position'],
  },
  {
    name: 'get_nakshatra',
    call: (a) => getNakshatraCapability.handler({ chart_id: CHART_ID, limit: 2000, ...a }, undefined) as never,
    kpDefault: NAK_KP, otherDefault: NAK_OTHER, invariant: [NAK_INVARIANT], explicitOther: ['graha_gandanta', NAK_INVARIANT],
  },
]

beforeEach(() => fake.reset())

const byFrame = (rows: Row[]) => ({
  kp: rows.filter((r) => isKpFrameCategory(r['fact_category'])),
  other: rows.filter((r) => !isKpFrameCategory(r['fact_category'])),
})
const sqlText = () => fake.statements.map((s) => s.sql.replace(/\s+/g, ' ')).join('\n')
const idsOf = (rows: Row[]) => new Set(rows.map((r) => r['ayanamsha_id']))

/** [label, args, expected ayanamsha of the NON-KP rows (null = pooled), note expected] */
const requests: Array<[string, Record<string, unknown>, string | null | 'error', boolean]> = [
  ['no id', {}, LAHIRI, false],
  ['the Lahiri primary id', { ayanamsha_id: LAHIRI }, LAHIRI, true],
  ['the alias LAHIRI', { ayanamsha_id: 'LAHIRI' }, LAHIRI, true],
  ['raman', { ayanamsha_id: 'raman' }, 'raman', true],
  ['explicit krishnamurti', { ayanamsha_id: 'krishnamurti' }, 'krishnamurti', false],
  ['"all"', { ayanamsha_id: 'all' }, null, true],
  ['ayanamsha_scope "all"', { ayanamsha_scope: 'all' }, null, true],
  ['a nonsense id', { ayanamsha_id: 'not_an_ayanamsha_xyz' }, 'error', false],
]

describe.each(surfaces)('$name', (s) => {
  describe('DEFAULT page (no system / domain / categories): KP categories at krishnamurti, the rest at the requested id', () => {
    it.each(requests)('%s', async (_label, extra, otherAya, noteExpected) => {
      const res = await s.call(extra)
      if (otherAya === 'error') {
        // the non-KP part cannot be served at an unknown id: same error as before, no SQL at all
        expect(res.is_error).toBe(true)
        expect(JSON.stringify(res.content)).toContain(LAHIRI)
        expect(fake.statements).toEqual([])
        return
      }
      expect(res.is_error).toBe(false)
      const c = res.content as Content
      const { kp, other } = byFrame(c.rows)

      // KP rows: present for every KP category of the page, ONLY from krishnamurti, labelled per row
      expect(kp.length).toBe(s.kpDefault.length * ROWS_PER_CATEGORY)
      expect(new Set(kp.map((r) => r['fact_category']))).toEqual(new Set(s.kpDefault))
      expect(idsOf(kp)).toEqual(new Set(['krishnamurti']))
      for (const r of kp) expect(r['frame_label']).toBe(KP_FRAME_LABEL)

      // non-KP rows: unchanged semantics (primary id + INVARIANT sentinel; pooled five for "all"), never labelled
      expect(other.length).toBeGreaterThan(0)
      for (const r of other) expect(r['frame_label']).toBeUndefined()
      const expectedIds = otherAya === null ? new Set([...KRISHNAMURTI_FIRST_FIXTURE_ORDER, ...(s.invariant.length ? ['INVARIANT'] : [])])
        : new Set([otherAya, ...(s.invariant.length ? ['INVARIANT'] : [])])
      expect(idsOf(other)).toEqual(expectedIds)
      if (otherAya === LAHIRI) expect(idsOf(other).has('krishnamurti')).toBe(false)

      // page-level echo describes the non-KP rows; the KP part is declared beside it
      if (otherAya === null) expect(c['ayanamsha_scope']).toBe('all')
      else expect(c['ayanamsha_id']).toBe(otherAya)
      expect(c['kp_frame']).toEqual({ ayanamsha_id: 'krishnamurti', frame_label: KP_FRAME_LABEL, categories: s.kpDefault })
      if (noteExpected) {
        expect(String(c['ayanamsha_note'])).toContain('KP has one frame by doctrine (Krishnamurti)')
        expect(String(c['ayanamsha_note'])).toContain('does not apply to the KP-frame rows')
      } else {
        expect(c['ayanamsha_note']).toBeUndefined()
      }
    })

    it('ONE query with the two-leg predicate, no extra binds, and the page order unchanged', async () => {
      await s.call({ ayanamsha_id: LAHIRI })
      const sql = sqlText()
      expect(sql).toMatch(/AND \(\(fact_category = ANY\(ARRAY\['[a-z_',]+'\]::text\[\]\) AND ayanamsha_id = 'krishnamurti'\) OR \(fact_category <> ALL\(ARRAY\['[a-z_',]+'\]::text\[\]\) AND ayanamsha_id (=|IN) /)
      // the KP leg is a constant: only chart, categories, the primary id, limit, offset are bound
      for (const st of fake.statements) {
        const bound = st.params.filter((p) => typeof p === 'string' && p !== CHART_ID)
        expect(bound).toEqual([LAHIRI])
      }
      expect(sqlText()).toMatch(/ORDER BY fact_category, array_position\(ARRAY\[[^\]]*\]::text\[\], ayanamsha_id::text\), ayanamsha_id, /)
      expect(fake.statements.filter((st) => st.isPage)).toHaveLength(1)
    })

    it('pagination is consistent: pages are disjoint, their union is the unpaged set, KP rows never leave krishnamurti', async () => {
      const full = ((await s.call({})).content as Content).rows
      const seen: string[] = []
      for (let offset = 0; offset < full.length + 5; offset += 7) {
        const page = ((await s.call({ limit: 7, offset })).content as Content).rows
        for (const r of page) {
          seen.push(String(r['fact_id']))
          if (isKpFrameCategory(r['fact_category'])) {
            expect(r['ayanamsha_id']).toBe('krishnamurti')
            expect(r['frame_label']).toBe(KP_FRAME_LABEL)
          }
        }
      }
      expect(seen.length).toBe(full.length)
      expect(new Set(seen).size).toBe(full.length)
      expect(new Set(seen)).toEqual(new Set(full.map((r) => String(r['fact_id']))))
    })
  })

  describe('explicit categories = KP only: the whole page at krishnamurti, labelled', () => {
    it.each(requests)('%s', async (label, extra) => {
      const res = await s.call({ categories: s.kpDefault, ...extra })
      expect(res.is_error).toBe(false)
      const c = res.content as Content
      expect(c.rows.length).toBe(s.kpDefault.length * ROWS_PER_CATEGORY)
      expect(idsOf(c.rows)).toEqual(new Set(['krishnamurti']))
      for (const r of c.rows) expect(r['frame_label']).toBe(KP_FRAME_LABEL)
      expect(c['ayanamsha_id']).toBe('krishnamurti')
      expect(c['ayanamsha_scope']).toBeUndefined()
      expect(c['frame_label']).toBe(KP_FRAME_LABEL)
      const askedOther = !['no id', 'explicit krishnamurti'].includes(label)
      expect(c['ayanamsha_note'] !== undefined).toBe(askedOther)
      // no Lahiri / other-ayanamsha bind anywhere
      const values = fake.statements.flatMap((st) => st.params).flatMap((p) => (Array.isArray(p) ? p : [p]))
      for (const other of [LAHIRI, 'true_chitra', 'raman', 'surya_siddhanta_classical']) expect(values).not.toContain(other)
    })
  })

  describe('explicit MIXED list (KP + non-KP)', () => {
    const list = [...s.kpDefault.slice(0, 2), ...s.explicitOther]
    it.each(requests)('%s', async (_label, extra, otherAya, noteExpected) => {
      const res = await s.call({ categories: list, ...extra })
      if (otherAya === 'error') {
        expect(res.is_error).toBe(true)
        expect(fake.statements).toEqual([])
        return
      }
      expect(res.is_error).toBe(false)
      const c = res.content as Content
      const { kp, other } = byFrame(c.rows)
      expect(new Set(kp.map((r) => r['fact_category']))).toEqual(new Set(s.kpDefault.slice(0, 2)))
      expect(kp.length).toBe(2 * ROWS_PER_CATEGORY)
      expect(idsOf(kp)).toEqual(new Set(['krishnamurti']))
      for (const r of kp) expect(r['frame_label']).toBe(KP_FRAME_LABEL)
      for (const r of other) expect(r['frame_label']).toBeUndefined()
      const invariantListed = s.explicitOther.some((x) => s.invariant.includes(x))
      const expectedIds = otherAya === null ? new Set([...KRISHNAMURTI_FIRST_FIXTURE_ORDER, ...(invariantListed ? ['INVARIANT'] : [])])
        : new Set([otherAya, ...(invariantListed ? ['INVARIANT'] : [])])
      expect(idsOf(other)).toEqual(expectedIds)
      expect(c['kp_frame']).toEqual({ ayanamsha_id: 'krishnamurti', frame_label: KP_FRAME_LABEL, categories: s.kpDefault.slice(0, 2) })
      expect(c['ayanamsha_note'] !== undefined).toBe(noteExpected)
      expect(c['categories']).toEqual(list)
    })
  })

  describe('no KP category involved: the previous path, byte for byte', () => {
    it.each(requests)('%s', async (_label, extra, otherAya) => {
      const res = await s.call({ categories: s.explicitOther, ...extra })
      if (otherAya === 'error') {
        expect(res.is_error).toBe(true)
        return
      }
      const c = res.content as Content
      for (const r of c.rows) expect(r['frame_label']).toBeUndefined()
      for (const key of ['kp_frame', 'ayanamsha_note', 'frame_label']) expect(c[key], key).toBeUndefined()
      const sql = sqlText()
      expect(sql).not.toMatch(/<> ALL/)
      const values = fake.statements.flatMap((st) => st.params).flatMap((p) => (Array.isArray(p) ? p : [p]))
      if (otherAya !== 'krishnamurti') expect(values).not.toContain('krishnamurti')
      if (otherAya === null) expect(c['ayanamsha_scope']).toBe('all')
      else expect(c['ayanamsha_id']).toBe(otherAya)
    })
  })
})

describe('system=kp / domain=kp branches (SS N-357) are unchanged, and now also label each row', () => {
  it('get_karakas system=kp', async () => {
    const c = (await getKarakasCapability.handler({ chart_id: CHART_ID, system: 'kp', ayanamsha_id: LAHIRI }, undefined)).content as Content
    expect(idsOf(c.rows)).toEqual(new Set(['krishnamurti']))
    expect(c['frame_label']).toBe(KP_FRAME_LABEL)
    expect(c.rows.every((r) => r['frame_label'] === KP_FRAME_LABEL)).toBe(true)
    expect(c['kp_frame']).toBeUndefined()
  })
  it('get_nakshatra domain=kp', async () => {
    const c = (await getNakshatraCapability.handler({ chart_id: CHART_ID, domain: 'kp', ayanamsha_id: 'all' }, undefined)).content as Content
    expect(idsOf(c.rows)).toEqual(new Set(['krishnamurti']))
    expect(c['frame_label']).toBe(KP_FRAME_LABEL)
    expect(c.rows.every((r) => r['frame_label'] === KP_FRAME_LABEL)).toBe(true)
  })
})

describe('get_karakas total and get_nakshatra rows honour the two-leg predicate', () => {
  it('get_karakas total equals KP rows (one ayanamsha) + other rows (primary) on the default page', async () => {
    const c = (await getKarakasCapability.handler({ chart_id: CHART_ID, limit: 3 }, undefined)).content as Content
    expect(c.rows).toHaveLength(3)
    expect(c['total']).toBe((KARAKAS_KP.length + KARAKAS_OTHER.length) * ROWS_PER_CATEGORY)
  })
  it('get_karakas total under "all": KP rows once (krishnamurti), the rest pooled over five ayanamshas', async () => {
    const c = (await getKarakasCapability.handler({ chart_id: CHART_ID, limit: 3, ayanamsha_id: 'all' }, undefined)).content as Content
    expect(c['total']).toBe((KARAKAS_KP.length + KARAKAS_OTHER.length * 5) * ROWS_PER_CATEGORY)
  })
  it('an empty mixed page says so and keeps the KP frame declared in empty_reason', async () => {
    const c = (await getNakshatraCapability.handler({ chart_id: CHART_ID, categories: ['cusp_kp_lords', 'graha_gandanta'], offset: 9999 }, undefined)).content as Content
    expect(c.rows).toHaveLength(0)
    expect(String(c['empty_reason'])).toContain("KP-frame categories read at 'krishnamurti'")
  })
})
