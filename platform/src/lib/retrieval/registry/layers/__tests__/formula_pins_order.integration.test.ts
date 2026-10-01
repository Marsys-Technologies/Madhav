/**
 * formula_pins_order.integration.test.ts — live-DB proof that the SQL ORDER BY of the three readers is
 * canonical-first AND total, i.e. that page boundaries across TIED rows (one (subject, key) holding
 * several formula rows) neither drop nor repeat a row and never depend on physical order.
 *
 * The unit tests mock query() and so cannot test an ORDER BY at all (a mock returns whatever order it is
 * given). This file runs the real handlers against the real DB. Skipped unless INTEGRATION=true.
 *
 * Run with: INTEGRATION=true DATABASE_URL=... vitest run src/lib/retrieval/registry/layers/__tests__/formula_pins_order.integration.test.ts
 * (read-only: every handler here only SELECTs).
 */
import { describe, expect, it } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'
const describeIf = INTEGRATION ? describe : describe.skip

type Row = Record<string, unknown>
type Handler = (a: Row, c?: unknown) => Promise<{ content: Row; is_error?: boolean }>

async function karakas(args: Row) {
  const { getKarakasCapability } = await import('../L1_ganita/get_karakas')
  return (getKarakasCapability.handler as Handler)({ chart_id: CHART, ayanamsha_id: AYA, ...args })
}
async function sensitive(args: Row) {
  const { getSensitivePointsCapability } = await import('../L1_ganita/get_sensitive_points')
  return (getSensitivePointsCapability.handler as Handler)({ chart_id: CHART, ayanamsha_id: AYA, ...args })
}
async function chartFacts(args: Row) {
  await import('../../catalog')
  const { getCapability } = await import('../../index')
  return (getCapability('marsys://tool/L1/chart_facts_query')!.handler as Handler)({ chart_id: CHART, ayanamsha_id: AYA, ...args })
}

/** Page through a handler with a tiny page size and return every served row in order. */
async function paged(fn: (a: Row) => Promise<{ content: Row }>, base: Row, pageSize: number): Promise<Row[]> {
  const out: Row[] = []
  for (let offset = 0; offset < 5000; offset += pageSize) {
    const rows = ((await fn({ ...base, limit: pageSize, offset })).content['rows'] as Row[]) ?? []
    out.push(...rows)
    if (rows.length < pageSize) break
  }
  return out
}

const ids = (rows: Row[]) => rows.map(r => String(r['fact_id']))

describeIf('multi-formula readers — live SQL order, totality and page boundaries', () => {
  it('get_karakas: every (subject, key) lists the canonical school first; both schools served', async () => {
    const full = ((await karakas({ categories: ['karaka_chara_position'], limit: 2000 })).content['rows'] as Row[])
    expect(full.length).toBeGreaterThan(100)
    const seen = new Map<string, string[]>()
    for (const r of full) {
      const k = `${r['fact_subject']}|${r['fact_key']}`
      seen.set(k, [...(seen.get(k) ?? []), String(r['formula_id'])])
    }
    let multi = 0
    for (const [k, formulas] of seen) {
      if (formulas.length > 1) {
        multi++
        expect(formulas[0], k).toBe('kn_rao_rahu_included')
        expect(new Set(formulas).size, k).toBe(formulas.length)
      }
    }
    expect(multi).toBeGreaterThan(0)
  })

  it('get_karakas: paging with a tiny page size reproduces the full ordered list (no drop, no repeat across tied rows)', async () => {
    const base = { categories: ['karaka_chara_position'] }
    const full = ids((await karakas({ ...base, limit: 2000 })).content['rows'] as Row[])
    for (const pageSize of [1, 3, 7]) {
      const p = ids(await paged(karakas, base, pageSize))
      expect(p, `page size ${pageSize}`).toEqual(full)
      expect(new Set(p).size).toBe(p.length)
    }
  })

  it('get_karakas: two identical calls return an identical order (deterministic)', async () => {
    const a = ids((await karakas({ categories: ['karaka_chara_position'], limit: 2000 })).content['rows'] as Row[])
    const b = ids((await karakas({ categories: ['karaka_chara_position'], limit: 2000 })).content['rows'] as Row[])
    expect(a).toEqual(b)
  })

  it('get_sensitive_points: Yogi lists bphs_93_20 before alt_96_40; Mrityu lists its three in declared order', async () => {
    const rows = ((await sensitive({ categories: ['esoteric_point_yogi', 'esoteric_point_mrityu'], limit: 2000 })).content['rows'] as Row[])
    const group = (cat: string) => {
      const m = new Map<string, string[]>()
      for (const r of rows.filter(x => x['fact_category'] === cat)) {
        const k = `${r['fact_subject']}|${r['fact_key']}`
        m.set(k, [...(m.get(k) ?? []), String(r['formula_id'])])
      }
      return [...m.values()]
    }
    for (const f of group('esoteric_point_yogi')) expect(f).toEqual(['bphs_93_20', 'alt_96_40'])
    for (const f of group('esoteric_point_mrityu')) expect(f).toEqual(['bphs_ch39', 'saravali', 'tajik_aapamrityu'])
  })

  it('get_sensitive_points: paging across tied rows reproduces the full list at page sizes 1, 2 and 5', async () => {
    const base = { categories: ['esoteric_point_yogi', 'esoteric_point_avayogi', 'esoteric_point_mrityu', 'esoteric_point_brahma'] }
    const full = ids((await sensitive({ ...base, limit: 2000 })).content['rows'] as Row[])
    for (const pageSize of [1, 2, 5]) {
      const p = ids(await paged(sensitive, base, pageSize))
      expect(p, `page size ${pageSize}`).toEqual(full)
      expect(new Set(p).size).toBe(p.length)
    }
  })

  it('chart_facts_query pivoted: Yogi headline is the canonical value; Mrityu headline is null with all three listed', async () => {
    const yogi = ((await chartFacts({ category: 'esoteric_point_yogi', fact_subject: 'YOGI_POINT' })).content['facts'] as Row[])[0]!
    const v = (yogi['formula_variants'] as Record<string, Row[]>)['longitude_sidereal']!
    expect(v.map(x => x['formula_id'])).toEqual(['bphs_93_20', 'alt_96_40'])
    expect(yogi['longitude_sidereal']).toBe(v[0]!['value'])

    const mr = ((await chartFacts({ category: 'esoteric_point_mrityu', fact_subject: 'MRITYU_SPHUTA' })).content['facts'] as Row[])[0]!
    expect(mr['longitude_sidereal']).toBeNull()
    expect((mr['formula_null_reasons'] as Row)['longitude_sidereal']).toBe('no_canonical_formula')
    expect(((mr['formula_variants'] as Record<string, Row[]>)['longitude_sidereal']!).map(x => x['formula_id']))
      .toEqual(['bphs_ch39', 'saravali', 'tajik_aapamrityu'])
  })

  it('chart_facts_query rows: ties in (subject, category, key) are canonical-first and stable across pages', async () => {
    const base = { shape: 'rows', category: 'esoteric_point_yogi,karaka_chara_position' }
    const full = ids((await chartFacts({ ...base, limit: 1000 })).content['rows'] as Row[])
    const paged3: string[] = []
    for (let offset = 0; offset < 2000; offset += 3) {
      const rows = (await chartFacts({ ...base, limit: 3, offset })).content['rows'] as Row[]
      paged3.push(...ids(rows))
      if (rows.length < 3) break
    }
    expect(paged3).toEqual(full)
  })
})
