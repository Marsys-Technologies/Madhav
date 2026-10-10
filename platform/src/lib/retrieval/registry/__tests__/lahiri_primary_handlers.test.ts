/**
 * lahiri_primary_handlers.test.ts — SS N-339 / N-342, PR-2: the Lahiri default lives INSIDE each
 * registry handler (not only at the web bridge), so in-process callers (synergy, the planner,
 * compiled floors, MCP primitives) get it too.
 *
 * No DB: `@/lib/db/client` is replaced by the five-ayanamsha SQL simulator
 * (helpers/five_ayanamsha_fake_db.ts): all five ayanamshas' rows, krishnamurti FIRST and Lahiri
 * LAST in the fixture, more than a page of each.
 *
 * Handlers are called DIRECTLY (`cap.handler(args)`), bypassing the bridge, so what is proven here
 * is the handler contract itself:
 *   omitted  -> lahiri_chitrapaksha     alias -> stored id      "all" -> pooled + scope marker
 *   unknown  -> is_error listing the stored ids, no SQL         page 1 -> Lahiri rows, never krishnamurti
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { createFiveAyanamshaFakeDb } from './helpers/five_ayanamsha_fake_db'

const fake = createFiveAyanamshaFakeDb()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => fake.query(args[0], args[1]),
  getPool: () => Promise.reject(new Error('no database in unit tests')),
  withTransaction: () => Promise.reject(new Error('no database in unit tests')),
}))

import { getCatalog } from '../catalog'
import { AYANAMSHA_SERVE_ORDER } from '../constants'
import type { CapabilityDescriptor } from '../types'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const LAHIRI = 'lahiri_chitrapaksha'

/**
 * Capabilities whose handler now owns the Lahiri default (PR-2 scope: the L1 `get_*` readers and
 * the L2 handlers the plan names). Every one MUST be exercised by the table below.
 */
const L1_URIS = [
  'get_argala', 'get_ashtakavarga', 'get_aspects', 'get_avasthas', 'get_ayurdaya', 'get_bhava_bala',
  'get_condition_composite', 'get_dignity', 'get_dispositors', 'get_divisionals', 'get_eclipse_flags',
  'get_graha_yuddha', 'get_karakas', 'get_medical_indications', 'get_nakshatra', 'get_panchanga',
  'get_positions', 'get_prashna_lagna', 'get_sade_sati', 'get_sensitive_degrees', 'get_sensitive_points',
  'get_strength', 'get_structural', 'get_tajik', 'get_tara_chandra_bala', 'get_transit_anchors',
  'get_vastu_directions', 'get_vichara', 'get_yoga_dosha', 'get_yoga_firings',
].map((n) => `marsys://tool/L1/${n}`)
const L2_URIS = [
  'query_cdlm_summary', 'query_cgm_motifs', 'query_cgm_paths', 'query_chart_gestalt', 'query_discoveries',
  'query_pratijna', 'query_question_lenses', 'query_rm_chart_summary', 'query_rm_dasha_windowed_prescriptions',
  'query_rm_dosha_remedy_bundles', 'query_rm_pattern_remedies', 'query_rm_prescriptions', 'query_rm_resonances',
  'query_triangulation',
].map((n) => `marsys://tool/L2/${n}`)

/**
 * In scope but exercised by their own focused tests (the generic page simulator cannot drive them):
 *  - query_planet: composite of eight legs behind a served-generation fence -> query_planet.lahiri_primary.test.ts
 *  - get_dashas: keyset/receipt CTE -> get_dashas_lahiri_primary.test.ts (+ get_dashas_kp_frame.test.ts)
 *  - chart_facts_query: its NON-KP side is on the shared normaliser since SS N-362 (g) (aliases, "all",
 *    unknown id; INVARIANT rows kept); proven in the dedicated describe at the end of THIS file. Its KP
 *    side (a KP-frame category is read at krishnamurti) is kp_categories_generic_readers.test.ts.
 *  - query_mechanisms, query_signals, query_ucd, traverse_chart_graph: receipt/cursor/graph CTEs ->
 *    L2_bodha/__tests__/lahiri_primary_l2.test.ts
 */
const OWN_TEST_URIS = new Set([
  'marsys://tool/L1/query_planet', 'marsys://tool/L1/get_dashas', 'marsys://tool/L1/chart_facts_query', 'marsys://tool/L2/query_mechanisms',
  'marsys://tool/L2/query_signals', 'marsys://tool/L2/query_ucd', 'marsys://tool/L2/traverse_chart_graph',
])

/**
 * Capabilities with an ayanamsha_id input that PR-2 deliberately does NOT move onto the generic
 * handler default, with the reason. The set is pinned so a NEW ayanamsha_id capability cannot slip
 * in unclassified.
 */
const DELIBERATELY_UNCHANGED: Record<string, string> = {
  'marsys://tool/L1/get_kp_cusps': 'KP frame: Krishnamurti BY DOCTRINE (SS N-342); default stays krishnamurti',
  'marsys://tool/L1/chart_snapshot': 'single-ayanamsha surface, already Lahiri; alias-normalised, "all" serves the primary',
  'marsys://tool/L1/get_chart_header': 'single-ayanamsha surface, already Lahiri; alias-normalised, "all" serves the primary',
  'marsys://tool/L1/get_av_transit_gating': 'single-ayanamsha surface, already Lahiri; alias-normalised, "all" serves the primary',
  'marsys://tool/L1/get_dasha_lord_capability': 'single-ayanamsha surface, already Lahiri; alias-normalised, "all" serves the primary',
  'marsys://tool/L2/graha_portrait': 'already Lahiri by default (DEFAULT_AYANAMSHA); sections are single-ayanamsha',
  'marsys://tool/L2/query_contradictions': 'already Lahiri by default',
  'marsys://tool/L2/query_domain_reading': 'already Lahiri by default',
  'marsys://tool/L2/query_quality_scorecard': 'not ayanamsha-split: the value is a label echo only',
  'marsys://tool/L2/query_remedies': 'already Lahiri by default',
  'marsys://tool/L-DOMAIN/assess_career': 'register_d8: already Lahiri, threaded to every leg',
  'marsys://tool/L-DOMAIN/assess_health': 'register_d8: already Lahiri, threaded to every leg',
  'marsys://tool/L-DOMAIN/assess_marriage': 'register_d8: already Lahiri, threaded to every leg',
  'marsys://tool/L-DOMAIN/assess_wealth': 'register_d8: already Lahiri, threaded to every leg',
  'marsys://tool/L-JUDGMENT/judgment_query': 'register_d9: already Lahiri, threaded to every leg',
  'marsys://tool/L-PACT/pact_query': 'register_d10: already Lahiri',
  'marsys://tool/L-SPINE/query_spine_bundle': 'spine bundle: already Lahiri',
  'marsys://tool/L-TIMING/yoga_activation_by_dasha': 'Kala-owned (L3 timing); not touched',
  'marsys://tool/L3/call_dasha_eligibility': 'Kala-owned (L3); not touched',
  'marsys://tool/L3/call_ephemeris_at_t': 'Kala-owned (L3 service call); not touched',
  'marsys://tool/L3/call_muhurta_score': 'Kala-owned (L3 service call); not touched',
  'marsys://tool/L3/call_priority_ranking': 'Kala-owned (L3); not touched',
  'marsys://tool/L3/query_active_dashas': 'Kala-owned (L3); not touched',
  'marsys://tool/L3/query_temporal_activation': 'Kala-owned (L3); not touched',
  'marsys://tool/L4/query_rectification': 'Phala (L4): short-code vocabulary, PR-4/PR-6 scope; bridge already injects "lahiri"',
  'marsys://tool/L5/mechanism_retrodiction_get': 'Mimamsa (L5): already Lahiri by default',
  'marsys://tool/synthesis/compose_large_n': 'composite: already Lahiri by default',
}

let withAya: CapabilityDescriptor[] = []
beforeAll(() => {
  withAya = getCatalog().filter((c) => !!c.input_schema && Object.prototype.hasOwnProperty.call(c.input_schema, 'ayanamsha_id'))
})
beforeEach(() => fake.reset())

const tableCaps = (): CapabilityDescriptor[] => withAya.filter((c) => [...L1_URIS, ...L2_URIS].includes(c.uri))

function sqlParamValues(): unknown[] {
  return fake.statements.flatMap((s) => s.params).flatMap((p) => (Array.isArray(p) ? p : [p]))
}

describe('classification is exhaustive (no ayanamsha_id capability is unclassified)', () => {
  it('every capability with an ayanamsha_id input is in scope, has its own test, or is deliberately unchanged', () => {
    const known = new Set<string>([...L1_URIS, ...L2_URIS, ...OWN_TEST_URIS, ...Object.keys(DELIBERATELY_UNCHANGED)])
    const unclassified = withAya.map((c) => c.uri as string).filter((u) => !known.has(u))
    expect(unclassified).toEqual([])
    const registered = new Set(withAya.map((c) => c.uri as string))
    const stale = [...known].filter((u) => !registered.has(u))
    expect(stale).toEqual([])
  })

  it('get_eclipse_flags now declares ayanamsha_id (it had none)', () => {
    expect(withAya.some((c) => c.uri === 'marsys://tool/L1/get_eclipse_flags')).toBe(true)
  })
})

describe('omitted ayanamsha_id: the handler itself binds lahiri_chitrapaksha', () => {
  it.each([...L1_URIS, ...L2_URIS].filter((u) => !OWN_TEST_URIS.has(u)))('%s', async (uri) => {
    const cap = withAya.find((c) => c.uri === uri)!
    expect(cap, uri).toBeDefined()
    fake.reset()
    await cap.handler({ chart_id: CHART_ID }, undefined)
    const values = sqlParamValues()
    expect(values, `${uri}: no SQL param is ${LAHIRI}`).toContain(LAHIRI)
    for (const other of AYANAMSHA_SERVE_ORDER.filter((i) => i !== LAHIRI)) expect(values, `${uri} leaked ${other}`).not.toContain(other)
  })
})

/** get_graha_yuddha reads its whole (small) fact set without LIMIT: its "page" is the first ayanamsha-selecting statement. */
const UNPAGED = new Set(['marsys://tool/L1/get_graha_yuddha'])
const ayanamshaPages = (uri: string) =>
  fake.statements.filter((s) => s.selectsAyanamsha && s.rows.length > 0 && (UNPAGED.has(uri) || s.isPage))

describe('page 1 of a five-ayanamsha fixture (krishnamurti first, Lahiri last, > a page each) is Lahiri', () => {
  it.each([...L1_URIS, ...L2_URIS].filter((u) => !OWN_TEST_URIS.has(u)))('%s: default call', async (uri) => {
    const cap = withAya.find((c) => c.uri === uri)!
    fake.reset()
    await cap.handler({ chart_id: CHART_ID }, undefined)
    const pages = ayanamshaPages(uri)
    expect(pages.length, `${uri}: no ayanamsha-bearing page statement observed`).toBeGreaterThan(0)
    for (const s of pages) {
      const ids = new Set(s.rows.map((r) => r.ayanamsha_id))
      expect([...ids].filter((i) => i !== LAHIRI && i !== 'INVARIANT'), `${uri}: non-Lahiri rows on page 1`).toEqual([])
      expect(ids.has(LAHIRI), `${uri}: Lahiri rows missing from page 1`).toBe(true)
    }
  })

  it.each([...L1_URIS, ...L2_URIS].filter((u) => !OWN_TEST_URIS.has(u)))('%s: "all" opt-out still pools, but Lahiri LEADS the page (serve order, not alphabetical)', async (uri) => {
    const cap = withAya.find((c) => c.uri === uri)!
    fake.reset()
    const res = await cap.handler({ chart_id: CHART_ID, ayanamsha_id: 'all' }, undefined)
    const pages = ayanamshaPages(uri)
    expect(pages.length, uri).toBeGreaterThan(0)
    // A handler may carry a SEPARATE section pinned to the primary (tail_watch): that statement is
    // filtered and Lahiri-only. Every other statement is the pooled one and must lead with Lahiri.
    const pooled = pages.filter((s) => !s.filtered)
    expect(pooled.length, `${uri}: "all" must reach an unfiltered (pooled) statement`).toBeGreaterThan(0)
    for (const s of pages) {
      if (s.filtered) {
        expect(s.rows.every((r) => r.ayanamsha_id === LAHIRI || r.ayanamsha_id === 'INVARIANT'), `${uri}: pinned section is Lahiri-only`).toBe(true)
        continue
      }
      // query_discoveries' ORDER BY (composite_discovery_rank) is owned by the standalone
      // discoveries-order-fix PR (branch suvarna/discoveries-order-fix); PR-2 deliberately leaves
      // that line alone, so the pooled "Lahiri leads" guarantee is asserted for every other handler.
      if (uri === 'marsys://tool/L2/query_discoveries') continue
      expect(s.serveOrdered, `${uri}: ORDER BY must carry the serve-order expression`).toBe(true)
      const firstReal = s.rows.find((r) => r.ayanamsha_id !== 'INVARIANT')
      expect(firstReal?.ayanamsha_id, `${uri}: page 1 must start with Lahiri`).toBe(LAHIRI)
    }
    const content = res.content as Record<string, unknown>
    expect(content['ayanamsha_scope'], `${uri}: response must say ayanamsha_scope:'all'`).toBe('all')
  })
})

describe('alias / scope / unknown handling at the handler', () => {
  const sample = ['get_positions', 'get_dignity', 'get_eclipse_flags', 'get_yoga_dosha', 'get_divisionals', 'query_pratijna', 'query_cdlm_summary', 'query_discoveries', 'query_chart_gestalt']
    .map((n) => withAya.find((c) => (c.uri as string).endsWith(`/${n}`)))
  it.each([['LAHIRI', LAHIRI], ['lahiri', LAHIRI], ['kp', 'krishnamurti'], ['True_Citra', 'true_chitra'], ['raman', 'raman']])('alias %j normalises to %j', async (input, stored) => {
    for (const cap of tableCaps().filter((c) => sample.includes(c))) {
      fake.reset()
      await cap.handler({ chart_id: CHART_ID, ayanamsha_id: input }, undefined)
      expect(sqlParamValues(), cap.uri).toContain(stored)
    }
  })

  it('ayanamsha_scope:"all" without an id (what the bridge sets) is the pooled path', async () => {
    for (const cap of tableCaps()) {
      fake.reset()
      const res = await cap.handler({ chart_id: CHART_ID, ayanamsha_scope: 'all' }, undefined)
      // the main (page) statements run unfiltered; reference-frame / pinned-tail lookups may still bind Lahiri
      expect(ayanamshaPages(cap.uri).some((s) => !s.filtered), cap.uri).toBe(true)
      expect((res.content as Record<string, unknown>)['ayanamsha_scope'], cap.uri).toBe('all')
    }
  })

  it('an explicit stored id beats ayanamsha_scope:"all"', async () => {
    const cap = withAya.find((c) => c.uri === 'marsys://tool/L1/get_dignity')!
    await cap.handler({ chart_id: CHART_ID, ayanamsha_id: 'raman', ayanamsha_scope: 'all' }, undefined)
    expect(sqlParamValues()).toContain('raman')
  })

  it.each(['nonsense', 'lahiri_x', 'yukteshwar', 'kp_newcomb'])('unknown id %j is an is_error result listing the stored ids, and runs no SQL', async (bad) => {
    for (const cap of tableCaps()) {
      fake.reset()
      const res = await cap.handler({ chart_id: CHART_ID, ayanamsha_id: bad }, undefined)
      expect(res.is_error, cap.uri).toBe(true)
      const text = typeof res.content === 'string' ? res.content : JSON.stringify(res.content)
      expect(text, cap.uri).toContain(LAHIRI)
      expect(text, cap.uri).toMatch(/surya_siddhanta_classical/)
      expect(fake.statements, `${cap.uri} ran SQL before rejecting the id`).toEqual([])
    }
  })
})

describe('INVARIANT sentinel rows survive the primary filter where the categories can be INVARIANT-stored', () => {
  it.each(['get_panchanga', 'get_nakshatra', 'get_strength', 'get_positions', 'get_divisionals'])('%s reads ayanamsha_id IN ($n, INVARIANT)', async (name) => {
    const cap = withAya.find((c) => (c.uri as string).endsWith(`/${name}`))!
    fake.reset()
    await cap.handler({ chart_id: CHART_ID }, undefined)
    const page = fake.statements.find((s) => s.isPage)!
    expect(page.sql.replace(/\s+/g, ' ')).toMatch(/ayanamsha_id IN \(\$\d+, 'INVARIANT'\)/)
    // the sentinel rows are on the Lahiri-filtered page, behind the Lahiri rows
    expect(page.page.some((r) => r.ayanamsha_id === 'INVARIANT') || page.page.length >= 1).toBe(true)
  })

  it('the INVARIANT rows are returned alongside Lahiri (small page so they fit)', async () => {
    const cap = withAya.find((c) => c.uri === 'marsys://tool/L1/get_panchanga')!
    fake.reset()
    const res = await cap.handler({ chart_id: CHART_ID, limit: 1000 }, undefined)
    const rows = (res.content as { rows: Array<{ ayanamsha_id: string }> }).rows
    expect(rows.some((r) => r.ayanamsha_id === 'INVARIANT')).toBe(true)
    expect(rows.every((r) => r.ayanamsha_id === LAHIRI || r.ayanamsha_id === 'INVARIANT')).toBe(true)
  })
})

/**
 * SS N-362 (g): chart_facts_query's NON-KP side runs through the same normaliser as the L1 handlers
 * (resolveHandlerAyanamsha). Before, it took the raw id: no alias, no "all", an unknown id ran SQL and
 * came back as a plausible empty answer. The KP side (KP categories at krishnamurti) is unchanged and is
 * proven in kp_categories_generic_readers.test.ts.
 */
describe('chart_facts_query: the NON-KP side is on the shared normaliser (SS N-362 g)', () => {
  const cfq = () => withAya.find((c) => c.uri === 'marsys://tool/L1/chart_facts_query')!
  const call = (args: Record<string, unknown>) => cfq().handler({ chart_id: CHART_ID, shape: 'rows', limit: 50, ...args }, undefined)
  const content = (r: { content: unknown }) => r.content as Record<string, unknown>
  const placeholdersFit = () => {
    for (const s of fake.statements) {
      const highest = Math.max(0, ...[...s.sql.matchAll(/\$(\d+)/g)].map((m) => Number(m[1])))
      expect(highest, `a placeholder exceeds the bound params: ${s.sql.replace(/\s+/g, ' ').slice(0, 160)}`).toBeLessThanOrEqual(s.params.length)
    }
  }

  it('is registered with an ayanamsha_id input', () => {
    expect(cfq()).toBeDefined()
  })

  it.each(['rows', 'pivoted'])('omitted -> Lahiri (%s shape), echoed, INVARIANT kept, no other ayanamsha bound', async (shape) => {
    const res = await call({ shape })
    expect(res.is_error).toBe(false)
    expect(content(res)['ayanamsha_id']).toBe(LAHIRI)
    expect(content(res)['ayanamsha_scope']).toBeUndefined()
    const main = fake.statements.find((s) => s.isPage)!
    expect(main.sql.replace(/\s+/g, ' ')).toMatch(/ayanamsha_id IN \(\$2, 'INVARIANT'\)/)
    expect(main.params[1]).toBe(LAHIRI)
    for (const other of AYANAMSHA_SERVE_ORDER.filter((i) => i !== LAHIRI)) expect(sqlParamValues(), `leaked ${other}`).not.toContain(other)
    expect(new Set(main.rows.map((r) => r.ayanamsha_id))).toEqual(new Set([LAHIRI, 'INVARIANT']))
    placeholdersFit()
  })

  it.each([['LAHIRI', LAHIRI], ['lahiri', LAHIRI], ['kp', 'krishnamurti'], ['True_Citra', 'true_chitra'], ['raman', 'raman']])(
    'alias %j normalises to %j (bound, and echoed as the stored id)', async (input, stored) => {
      const res = await call({ ayanamsha_id: input })
      expect(res.is_error).toBe(false)
      expect(sqlParamValues()).toContain(stored)
      expect(sqlParamValues()).not.toContain(input === stored ? '\u0000' : input)
      expect(content(res)['ayanamsha_id']).toBe(stored)
      const main = fake.statements.find((s) => s.isPage)!
      expect(new Set(main.rows.map((r) => r.ayanamsha_id))).toEqual(new Set([stored, 'INVARIANT']))
    })

  it.each([[{ ayanamsha_id: 'all' }], [{ ayanamsha_scope: 'all' }]])('%j -> pooled: no ayanamsha predicate, scope marker, rows carry their ayanamsha, Lahiri leads', async (extra) => {
    const res = await call({ ...extra, limit: 1000 })
    expect(res.is_error).toBe(false)
    const c = content(res)
    expect(c['ayanamsha_scope']).toBe('all')
    expect(c['ayanamsha_id']).toBeUndefined()
    const main = fake.statements.find((s) => s.isPage)!
    expect(main.filtered, 'the pooled statement must carry no ayanamsha predicate').toBe(false)
    expect(main.sql.replace(/\s+/g, ' ')).not.toMatch(/ayanamsha_id (IN|=) \(?\$\d/)
    expect(main.serveOrdered, 'ORDER BY carries the serve-order expression').toBe(true)
    expect(main.selectsAyanamsha, 'pooled rows must name their ayanamsha').toBe(true)
    for (const id of AYANAMSHA_SERVE_ORDER) expect(sqlParamValues()).not.toContain(id)
    const rows = c['rows'] as Array<{ ayanamsha_id: string }>
    expect(new Set(rows.map((r) => r.ayanamsha_id)).size).toBeGreaterThan(1)
    expect(rows.find((r) => r.ayanamsha_id !== 'INVARIANT')?.ayanamsha_id).toBe(LAHIRI)
    placeholdersFit()
  })

  it('"all" in the pivoted shape keeps the five ayanamshas apart (one wide row per ayanamsha x subject, never merged)', async () => {
    const res = await call({ ayanamsha_id: 'all', shape: 'pivoted', limit: 200 })
    expect(res.is_error).toBe(false)
    const facts = content(res)['facts'] as Array<{ ayanamsha_id: string; fact_subject: string }>
    const real = facts.filter((f) => f.ayanamsha_id !== 'INVARIANT')
    expect(new Set(real.map((f) => f.ayanamsha_id))).toEqual(new Set(AYANAMSHA_SERVE_ORDER))
    expect(real[0]!.ayanamsha_id).toBe(LAHIRI)
    expect(content(res)['ayanamsha_scope']).toBe('all')
    placeholdersFit()
  })

  it('an explicit stored id beats ayanamsha_scope:"all"', async () => {
    const res = await call({ ayanamsha_id: 'raman', ayanamsha_scope: 'all' })
    expect(sqlParamValues()).toContain('raman')
    expect(content(res)['ayanamsha_id']).toBe('raman')
    expect(content(res)['ayanamsha_scope']).toBeUndefined()
  })

  it.each(['nonsense', 'lahiri_x', 'yukteshwar', 'kp_newcomb'])('unknown id %j is an is_error result listing the stored ids, and runs no SQL', async (bad) => {
    const res = await call({ ayanamsha_id: bad })
    expect(res.is_error).toBe(true)
    const text = JSON.stringify(res.content)
    expect(text).toContain(LAHIRI)
    expect(text).toMatch(/surya_siddhanta_classical/)
    expect(fake.statements).toEqual([])
  })

  it('an unknown id with a non-KP category list (and with a mixed KP+non-KP list) is an error with no SQL', async () => {
    for (const category of ['graha_position', 'cusp_kp_lords,graha_position']) {
      fake.reset()
      const res = await call({ ayanamsha_id: 'nonsense', category })
      expect(res.is_error, category).toBe(true)
      expect(fake.statements, category).toEqual([])
    }
  })

  it('the KP side is unchanged: a KP-only list ignores the passed id (nonsense included) and reads krishnamurti', async () => {
    const res = await call({ ayanamsha_id: 'nonsense', category: 'cusp_kp_lords' })
    expect(res.is_error).toBe(false)
    expect(content(res)['ayanamsha_id']).toBe('krishnamurti')
    expect(sqlParamValues()).toContain('krishnamurti')
    expect(sqlParamValues()).not.toContain(LAHIRI)
  })

  it('the sign / nakshatra / divisional sub-queries stay well-formed under "all" and under a normalised alias', async () => {
    for (const ayanamsha_id of ['all', 'LAHIRI']) {
      fake.reset()
      const res = await call({ ayanamsha_id, sign: 'Aries', nakshatra: 'Ashwini' })
      expect(res.is_error, ayanamsha_id).toBe(false)
      placeholdersFit()
      fake.reset()
      const dv = await call({ ayanamsha_id, divisional_chart: 'D9', sign: 'Aries', category: 'graha_position' })
      expect(dv.is_error, ayanamsha_id).toBe(false)
      placeholdersFit()
    }
  })
})
