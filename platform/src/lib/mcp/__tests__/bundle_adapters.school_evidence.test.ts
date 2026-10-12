/**
 * bundle_adapters.school_evidence.test.ts — SS N-365: the LIVE multi-school bundle serves JAIMINI and
 * TAJAKA evidence from data that is actually STORED (it served empty evidence before).
 * ============================================================================================
 * Defects (both found by the N-362 c static pin, reported there, fixed here):
 *   jaimini: buildSchoolSpec asked query_chart_facts for category 'strength_extra' (no writer, no source
 *            reference) -> the jaimini entry was always an empty fact list.
 *   tajaka:  buildSchoolSpec asked query_chart_facts for category 'varshphal' (no writer emits it; the
 *            annual chart lives in the TABLE l1_tajik_varsha_year_lords, written by ga_tajaka and served by
 *            the registry capability get_tajik / MCP name ganita_tajaka_get) -> always empty.
 *
 * DB-free but NOT stubbed at the tool level: the fake /api/mcp/primitives/<tool> endpoint below applies the
 * REAL whitelist (isAllowedSurgicalTool / MCP_TO_RETRIEVAL_TOOL / isPerChartPrimitive) and runs the REAL
 * registry handlers (getToolByName(...).retrieve -> chart_facts_query, get_tajik, with the Lahiri-primary
 * bridge in front of them) against a mocked pg client whose rows are shaped EXACTLY like the writers emit
 * them. So the wire shape (a ToolBundle whose results[0].content is the handler JSON), the accepted tool
 * name, the Lahiri default and the pivoting are the production ones; only the database is a fixture.
 */
import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const hoisted = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: hoisted.mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u-1', audience_tier: 'client', key_id: 'k-1' }
const LAHIRI = 'lahiri_chitrapaksha'
const KRISHNAMURTI = 'krishnamurti'

const HERE = dirname(fileURLToPath(import.meta.url))
const SIDECAR = join(HERE, '..', '..', '..', '..', 'python-sidecar')

const SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

// ── Fixture: chart_facts rows shaped like ga_sensitive_writer.py emits them ───────────────────────
// _build_karakamsa_rows: category karakamsa_position, subject KARAKAMSA, keys sign (text),
//   longitude_d9_sidereal (num), atmakaraka_graha (text).
// _build_arudha_rows: category arudha_pada, subjects ARUDHA_A1..A12 + ARUDHA_SU/MO/MA/ME/JU/VE/SA,
//   keys sign (text), longitude_sidereal (num), house_d1 (num).
// _build_karaka_rows: category karaka_chara_position, TWO schools under the SAME subject names.
interface FactRow {
  fact_id: string
  chart_id: string
  ayanamsha_id: string
  fact_category: string
  fact_subject: string
  fact_key: string
  fact_value_num: number | null
  fact_value_text: string | null
  fact_value_jsonb: null
  unit: null
  verification_pass_status: string
  citation_ref: string
}

function fact(ayanamsha: string, category: string, subject: string, key: string, num: number | null, text: string | null): FactRow {
  return {
    fact_id: `${ayanamsha}:${category}:${subject}:${key}:${text ?? num}`,
    chart_id: CHART_ID,
    ayanamsha_id: ayanamsha,
    fact_category: category,
    fact_subject: subject,
    fact_key: key,
    fact_value_num: num,
    fact_value_text: text,
    fact_value_jsonb: null,
    unit: null,
    verification_pass_status: 'single',
    citation_ref: 'Jaimini Sutram',
  }
}

const GRAHA_ARUDHA_SUBJECTS = ['ARUDHA_SU', 'ARUDHA_MO', 'ARUDHA_MA', 'ARUDHA_ME', 'ARUDHA_JU', 'ARUDHA_VE', 'ARUDHA_SA']

function jaiminiRows(ayanamsha: string, shift: number): FactRow[] {
  const rows: FactRow[] = []
  const d9Idx = (3 + shift) % 12
  rows.push(
    fact(ayanamsha, 'karakamsa_position', 'KARAKAMSA', 'sign', null, SIGNS[d9Idx]!),
    fact(ayanamsha, 'karakamsa_position', 'KARAKAMSA', 'longitude_d9_sidereal', d9Idx * 30, null),
    fact(ayanamsha, 'karakamsa_position', 'KARAKAMSA', 'atmakaraka_graha', null, PLANETS[(2 + shift) % 7]!),
  )
  const arudhaSubjects = [...Array.from({ length: 12 }, (_, h) => `ARUDHA_A${h + 1}`), ...GRAHA_ARUDHA_SUBJECTS]
  arudhaSubjects.forEach((subject, i) => {
    const idx = (i * 5 + shift) % 12
    rows.push(
      fact(ayanamsha, 'arudha_pada', subject, 'sign', null, SIGNS[idx]!),
      fact(ayanamsha, 'arudha_pada', subject, 'longitude_sidereal', idx * 30, null),
      fact(ayanamsha, 'arudha_pada', subject, 'house_d1', idx + 1, null),
    )
  })
  // The two-school chara-karaka rows (same subject names, different assigned_graha): present in the store
  // and deliberately NOT requested by the jaimini spec.
  for (const [school, graha] of [['parashari_rahu_excluded', 'Sun'], ['kn_rao_rahu_included', 'Rahu']] as const) {
    rows.push(
      fact(ayanamsha, 'karaka_chara_position', 'ATMAKARAKA', 'assigned_graha', null, graha),
      fact(ayanamsha, 'karaka_chara_position', 'ATMAKARAKA', 'karaka_school', null, school),
    )
  }
  return rows
}

const FACT_STORE: FactRow[] = [...jaiminiRows(LAHIRI, 0), ...jaiminiRows(KRISHNAMURTI, 4)]

// ── Fixture: l1_tajik_varsha_year_lords rows shaped like ga_tajaka_writer._insert_rows (_COLUMNS) ───
// Hybrid window varsha_year 1..48 (past -> present+5 for the 1984-02-05 native) x ayanamshas.
interface TajikRow {
  varsha_id: string
  chart_id: string
  ayanamsha_id: string
  build_id: string
  varsha_year: number
  varsha_start_iso: string
  varsha_end_iso: string
  year_lord_method: string
  year_lord: string
  candidate_lord_jsonb: Record<string, unknown>
  muntha_position_jsonb: Record<string, unknown>
  applicable_tajik_yogas_array: string[]
  classical_source_citation: string
  ephemeris_audit_jsonb: Record<string, unknown>
  verification_pass_status: string
  citation_ref: string
  citation_human: string
  computed_at: string
}

function tajikRows(ayanamsha: string, shift: number): TajikRow[] {
  const rows: TajikRow[] = []
  for (let y = 1; y <= 48; y++) {
    const munthaIdx = y === 43 && ayanamsha === LAHIRI ? 6 : (y + shift) % 12 // FORENSIC gate: varsha 43 lahiri = Libra
    rows.push({
      varsha_id: `${ayanamsha}:${y}`,
      chart_id: CHART_ID,
      ayanamsha_id: ayanamsha,
      build_id: 'build-1',
      varsha_year: y,
      varsha_start_iso: `${1984 + y - 1}-02-05T00:00:00+05:30`,
      varsha_end_iso: `${1984 + y}-02-04T23:59:59+05:30`,
      year_lord_method: 'panchavargiya_bala',
      year_lord: PLANETS[(y + shift) % 7]!,
      candidate_lord_jsonb: { candidates: [PLANETS[(y + shift) % 7]!] },
      muntha_position_jsonb: { sign: SIGNS[munthaIdx]!, house_from_lagna: munthaIdx + 1 },
      applicable_tajik_yogas_array: ['ithasala'],
      classical_source_citation: 'Tajika Neelakanthi',
      ephemeris_audit_jsonb: { converged: true },
      verification_pass_status: 'two_pass_verified',
      citation_ref: 'ga_tajaka',
      citation_human: 'Tajika Neelakanthi',
      computed_at: '2026-10-10T00:00:00Z',
    })
  }
  return rows
}

const TAJIK_STORE: TajikRow[] = [...tajikRows(LAHIRI, 0), ...tajikRows(KRISHNAMURTI, 3)]

// ── Mocked pg client: answers exactly the SQL shapes get_tajik and chart_facts_query issue ─────────
function fakeQuery(sql: string, params: unknown[] = []): Promise<{ rows: Record<string, unknown>[] }> {
  const compact = sql.replace(/\s+/g, ' ')
  if (/FROM charts/.test(compact)) return Promise.resolve({ rows: [{ birth_date: '1984-02-05' }] })

  // get_tajik: Source 1 (hadda chart_facts, not fetched by default) count
  if (/COUNT\(\*\)::int AS n FROM chart_facts/.test(compact)) return Promise.resolve({ rows: [{ n: 0 }] })

  // get_tajik: Source 2 (l1_tajik_varsha_year_lords). No year selector in the bundle call, so the only
  // filter after chart_id is the ayanamsha (when the bridge injected it).
  if (/FROM l1_tajik_varsha_year_lords/.test(compact)) {
    const ayanamsha = /AND ayanamsha_id = \$2/.test(compact) ? String(params[1]) : null
    const matched = TAJIK_STORE.filter(r => r.chart_id === params[0] && (ayanamsha === null || r.ayanamsha_id === ayanamsha))
    if (/COUNT\(\*\)::int AS n/.test(compact)) return Promise.resolve({ rows: [{ n: matched.length }] })
    const offset = Number(params[params.length - 1])
    const limit = Number(params[params.length - 2])
    let ordered: TajikRow[]
    if (/ORDER BY ABS\(varsha_year - \$\d+\)/.test(compact)) {
      const current = Number(params[params.length - 3])
      ordered = [...matched].sort((a, b) => Math.abs(a.varsha_year - current) - Math.abs(b.varsha_year - current) || a.varsha_year - b.varsha_year || a.ayanamsha_id.localeCompare(b.ayanamsha_id))
    } else {
      ordered = [...matched].sort((a, b) => a.varsha_year - b.varsha_year || a.ayanamsha_id.localeCompare(b.ayanamsha_id))
    }
    return Promise.resolve({ rows: ordered.slice(offset, offset + limit) as unknown as Record<string, unknown>[] })
  }

  // chart_facts_query: WHERE chart_id = $1 AND ayanamsha_id IN ($2,'INVARIANT') AND fact_category = ANY($3)
  if (/FROM chart_facts/.test(compact) && /ayanamsha_id IN \(\$2, 'INVARIANT'\)/.test(compact)) {
    const categories = params[2] as string[]
    const matched = FACT_STORE.filter(r => r.chart_id === params[0] && [String(params[1]), 'INVARIANT'].includes(r.ayanamsha_id) && categories.includes(r.fact_category))
    if (/COUNT\(DISTINCT fact_subject\)/.test(compact)) {
      return Promise.resolve({ rows: [{ total: new Set(matched.map(r => r.fact_subject)).size }] })
    }
    const cap = Number(params[params.length - 1])
    const ordered = [...matched].sort((a, b) => a.fact_subject.localeCompare(b.fact_subject) || a.fact_category.localeCompare(b.fact_category) || a.fact_key.localeCompare(b.fact_key))
    return Promise.resolve({ rows: ordered.slice(0, cap) as unknown as Record<string, unknown>[] })
  }
  return Promise.resolve({ rows: [] })
}

// ── Fake /api/mcp/primitives/<tool>: REAL whitelist + REAL handlers, fixture database ──────────────
interface Recorded { toolName: string; body: Record<string, unknown> }

type Registry = typeof import('@/lib/retrieval/registry/tool_name_bridge')
let registry: Registry
let bundle: typeof import('../bundle_adapters')

beforeAll(async () => {
  await import('@/lib/retrieval/registry/catalog')
  registry = await import('@/lib/retrieval/registry/tool_name_bridge')
  bundle = await import('../bundle_adapters')
}, 120_000)

beforeEach(() => {
  hoisted.mockQuery.mockReset()
  hoisted.mockQuery.mockImplementation(fakeQuery)
  // pin "today" so the handler's current-year-first default is deterministic: 2026-10-10 is inside varsha 43
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-10-10T12:00:00Z'))
})
afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

function stubPrimitives(): { calls: Recorded[] } {
  const calls: Recorded[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/api/mcp/bundles/cache/store')) return { ok: true, status: 200, json: async () => ({ ok: true }) }
    const raw = init?.body ? JSON.parse(String(init.body)) as Record<string, unknown> : {}
    const body = (raw['params'] as Record<string, unknown>) ?? raw
    const toolName = url.split('/api/mcp/primitives/')[1] ?? 'unknown'
    calls.push({ toolName, body })
    const reject = (status: number, message: string) => ({ ok: false, status, json: async () => ({ ok: false, error: { class: 'validation', message } }) })
    if (!registry.isAllowedSurgicalTool(toolName)) return reject(400, `Tool not in surgical whitelist: ${toolName}`)
    if (toolName !== 'query_chart_facts' && toolName !== 'query_varshphal' && toolName !== 'query_varshaphala') {
      return { ok: true, status: 200, json: async () => ({ ok: true, result: {} }) } // other tools: out of scope here
    }
    const chartId = body['chart_id'] as string | undefined
    if (registry.isPerChartPrimitive(toolName) && !chartId) return reject(400, 'CHART_REQUIRED')
    const tool = registry.getToolByName(registry.MCP_TO_RETRIEVAL_TOOL[toolName]!)
    if (!tool) return reject(500, 'Retrieval tool not found in registry')
    try {
      const result = await tool.retrieve({ chart_id: chartId }, body)
      return { ok: true, status: 200, json: async () => ({ ok: true, result }) }
    } catch (err) {
      return { ok: false, status: 500, json: async () => ({ ok: false, error: { class: 'orchestrator_error', message: String(err) } }) }
    }
  }))
  return { calls }
}

async function runBundle(withChart = true): Promise<{ calls: Recorded[]; entries: Array<Record<string, unknown>>; envelope: Record<string, unknown> }> {
  const { calls } = stubPrimitives()
  let envelope: Record<string, unknown> | undefined
  await bundle.executeMultiSchoolBundle(
    withChart ? { claim: 'career', tier: 'client', chart_id: CHART_ID } : { claim: 'career', tier: 'client' },
    PRINCIPAL,
    (event) => { if (event.type === 'bundle.completed') envelope = (event as unknown as { envelope: Record<string, unknown> }).envelope },
  )
  return { calls, entries: envelope!['bundle_entries'] as Array<Record<string, unknown>>, envelope: envelope! }
}

/** The primitives wire shape: envelope.result is a ToolBundle whose results[0].content is the handler JSON. */
function handlerContent(entry: Record<string, unknown>): Record<string, unknown> {
  const data = entry['data'] as { result: { tool_name: string; results: Array<{ content: string }> } }
  expect(data.result.results).toHaveLength(1)
  return JSON.parse(data.result.results[0]!.content) as Record<string, unknown>
}

function entryOf(entries: Array<Record<string, unknown>>, name: string): Record<string, unknown> {
  const e = entries.find(x => x['sub_tool'] === name)
  expect(e, `${name} entry`).toBeDefined()
  return e!
}

// ── Fixture sanity ────────────────────────────────────────────────────────────────────────────────
describe('fixtures are writer-shaped', () => {
  it('jaimini store: 1 KARAKAMSA + 12 ARUDHA_A* + 7 graha arudhas, 3 keys each, plus the two-school karaka rows', () => {
    const l = FACT_STORE.filter(r => r.ayanamsha_id === LAHIRI)
    expect(l.filter(r => r.fact_category === 'karakamsa_position')).toHaveLength(3)
    expect(l.filter(r => r.fact_category === 'arudha_pada')).toHaveLength(19 * 3)
    expect(new Set(l.filter(r => r.fact_category === 'arudha_pada').map(r => r.fact_subject)).size).toBe(19)
    const karaka = l.filter(r => r.fact_category === 'karaka_chara_position' && r.fact_key === 'assigned_graha')
    expect(karaka.map(r => r.fact_subject)).toEqual(['ATMAKARAKA', 'ATMAKARAKA']) // same subject, two schools
  })

  it('tajik store: ga_tajaka _COLUMNS, varsha_year 1..48 x two ayanamshas, FORENSIC varsha 43 lahiri = Libra', () => {
    const writer = readFileSync(join(SIDECAR, 'ga_writers', 'ga_tajaka_writer.py'), 'utf8')
    const columns = /_COLUMNS = \[([^\]]*)\]/s.exec(writer)![1]!.match(/"([a-z_]+)"/g)!.map(c => c.replace(/"/g, ''))
    expect(Object.keys(TAJIK_STORE[0]!).sort()).toEqual([...columns].sort())
    expect(TAJIK_STORE.filter(r => r.ayanamsha_id === LAHIRI)).toHaveLength(48)
    expect(TAJIK_STORE.find(r => r.ayanamsha_id === LAHIRI && r.varsha_year === 43)!.muntha_position_jsonb['sign']).toBe('Libra')
  })
})

// ── TAJAKA ─────────────────────────────────────────────────────────────────────────────────────────
describe('multi_school_bundle tajaka evidence is non-empty (SS N-365)', () => {
  it('the tajaka spec calls the whitelisted varshaphal primitive (get_tajik), not query_chart_facts/varshphal', () => {
    const spec = bundle.buildSchoolSpec('tajaka')!
    expect(spec.toolName).toBe('query_varshphal')
    expect(spec.params).toEqual({ limit: 20 })
    // the name the primitives route accepts, per-chart, mapped to the get_tajik capability
    expect(registry.isAllowedSurgicalTool('query_varshphal')).toBe(true)
    expect(registry.isPerChartPrimitive('query_varshphal')).toBe(true)
    expect(registry.resolveToolUri(registry.MCP_TO_RETRIEVAL_TOOL['query_varshphal']!)).toBe('marsys://tool/L1/get_tajik')
    // ganita_tajaka_get is the platform-mcp tool name, NOT a primitive: the route would 400 it
    expect(registry.isAllowedSurgicalTool('ganita_tajaka_get')).toBe(false)
  })

  it('tajaka_evidence carries the annual-chart rows, current varsha year first, Lahiri primary', async () => {
    const { calls, entries } = await runBundle()
    const call = calls.find(c => c.toolName === 'query_varshphal')
    expect(call, 'tajaka primitive call').toBeDefined()
    expect(call!.body).toEqual({ limit: 20, chart_id: CHART_ID }) // no category, no pin, no invented year
    expect(calls.filter(c => c.body['category'] === 'varshphal')).toHaveLength(0)

    const entry = entryOf(entries, 'tajaka_evidence')
    expect(entry['errored']).toBe(false)
    expect(entry['upstream_status']).toBe(200)
    expect(entry['frame_label']).toBeUndefined()
    expect(typeof entry['latency_ms']).toBe('number')
    expect(entry['signal_ids_available']).toEqual([])
    expect(entry['rows_returned']).toBe(1) // the ToolBundle carries one JSON result (extractRowCount counts results[])

    const content = handlerContent(entry)
    expect(content['chart_id']).toBe(CHART_ID)
    const lords = content['varsha_year_lords'] as { rows: Array<TajikRow & { _source_table: string }>; total: number; returned_count: number; sort: string; current_varsha_year: number }
    expect(lords.rows.length).toBeGreaterThan(0)
    expect(lords.returned_count).toBe(20)
    expect(lords.total).toBe(48) // the Lahiri copy only; the krishnamurti copy (96 rows in total) is not mixed in
    expect(lords.sort).toBe('current_year_first')
    expect(lords.current_varsha_year).toBe(43)
    expect(lords.rows[0]!.varsha_year).toBe(43)
    for (const r of lords.rows) {
      expect(r.ayanamsha_id).toBe(LAHIRI)
      expect(r._source_table).toBe('l1_tajik_varsha_year_lords')
      expect(typeof r.year_lord).toBe('string')
      expect(r.muntha_position_jsonb).toBeDefined()
    }
    // FORENSIC gate row (varsha 43, lahiri): Muntha Libra; the year lord is the lahiri fixture's, not the krishnamurti one
    expect(lords.rows[0]!.muntha_position_jsonb['sign']).toBe('Libra')
    expect(lords.rows[0]!.year_lord).toBe(PLANETS[43 % 7])
    expect(lords.rows[0]!.year_lord).not.toBe(PLANETS[(43 + 3) % 7])

    // the SQL the real handler issued carried the Lahiri primary injected by the bridge (the bundle sent none)
    const tajikSql = hoisted.mockQuery.mock.calls.filter(([sql]) => /FROM l1_tajik_varsha_year_lords/.test(String(sql)))
    expect(tajikSql.length).toBeGreaterThan(0)
    for (const [, params] of tajikSql) expect((params as unknown[])[1]).toBe(LAHIRI)
  })

  it('without a chart_id the tajaka entry errors honestly (400 CHART_REQUIRED), never an empty success', async () => {
    const { entries } = await runBundle(false)
    const entry = entryOf(entries, 'tajaka_evidence')
    expect(entry['errored']).toBe(true)
    expect(entry['upstream_status']).toBe(400)
    expect(entry['data']).toBeUndefined()
  })
})

// ── JAIMINI ────────────────────────────────────────────────────────────────────────────────────────
describe('multi_school_bundle jaimini evidence is non-empty (SS N-365)', () => {
  it('the jaimini spec asks for the stored Jaimini categories, never strength_extra, and omits the two-school karaka category', () => {
    const spec = bundle.buildSchoolSpec('jaimini')!
    expect(spec.toolName).toBe('query_chart_facts')
    expect(spec.params).toEqual({ category: 'karakamsa_position,arudha_pada', limit: 30 })
    expect(String(spec.params['category'])).not.toContain('strength_extra')
    expect(String(spec.params['category'])).not.toContain('karaka_chara_position')
    expect(spec.params).not.toHaveProperty('ayanamsha_id') // Lahiri primary by default
  })

  it('jaimini_evidence carries KARAKAMSA + the 19 arudha padas at the Lahiri primary', async () => {
    const { calls, entries } = await runBundle()
    const call = calls.find(c => c.toolName === 'query_chart_facts' && String(c.body['category']).includes('arudha_pada'))
    expect(call, 'jaimini primitive call').toBeDefined()
    expect(call!.body).toEqual({ category: 'karakamsa_position,arudha_pada', limit: 30, chart_id: CHART_ID })
    expect(calls.filter(c => c.body['category'] === 'strength_extra')).toHaveLength(0)

    const entry = entryOf(entries, 'jaimini_evidence')
    expect(entry['errored']).toBe(false)
    expect(entry['upstream_status']).toBe(200)
    expect(entry['frame_label']).toBeUndefined()
    expect(typeof entry['latency_ms']).toBe('number')
    expect(entry['signal_ids_available']).toEqual([])

    const content = handlerContent(entry)
    expect(content['ayanamsha_id']).toBe(LAHIRI)
    expect(content['shape']).toBe('pivoted')
    const facts = content['facts'] as Array<Record<string, unknown>>
    expect(facts.length).toBeGreaterThan(0)
    expect(facts).toHaveLength(20)
    expect(content['total']).toBe(20)
    expect(content['more_available']).toBe(false)
    const subjects = facts.map(f => String(f['fact_subject']))
    expect(subjects).toContain('KARAKAMSA')
    for (let h = 1; h <= 12; h++) expect(subjects).toContain(`ARUDHA_A${h}`)
    for (const s of GRAHA_ARUDHA_SUBJECTS) expect(subjects).toContain(s)
    // only the requested categories: the two-school karaka_chara_position rows never reach this entry
    expect(new Set(facts.map(f => f['fact_category']))).toEqual(new Set(['karakamsa_position', 'arudha_pada']))
    const karakamsa = facts.find(f => f['fact_subject'] === 'KARAKAMSA')!
    expect(karakamsa['sign']).toBe(SIGNS[3]) // Lahiri copy (shift 0), not the krishnamurti copy (shift 4)
    expect(karakamsa['atmakaraka_graha']).toBe(PLANETS[2])
    expect(typeof karakamsa['longitude_d9_sidereal']).toBe('number')
    for (const f of facts.filter(x => x['fact_category'] === 'arudha_pada')) {
      expect(typeof f['sign']).toBe('string')
      expect(typeof f['longitude_sidereal']).toBe('number')
      expect(typeof f['house_d1']).toBe('number')
    }
    // the SQL carried the Lahiri primary
    const factSql = hoisted.mockQuery.mock.calls.filter(([sql, params]) =>
      /ayanamsha_id IN \(\$2, 'INVARIANT'\)/.test(String(sql).replace(/\s+/g, ' ')) && ((params as unknown[])[2] as string[]).includes('arudha_pada'))
    expect(factSql.length).toBeGreaterThan(0) // the kp school's own krishnamurti read is a different query
    for (const [, params] of factSql) expect((params as unknown[])[1]).toBe(LAHIRI)
  })

  it('without a chart_id the jaimini entry errors honestly (400 CHART_REQUIRED), never an empty success', async () => {
    const { entries } = await runBundle(false)
    const entry = entryOf(entries, 'jaimini_evidence')
    expect(entry['errored']).toBe(true)
    expect(entry['upstream_status']).toBe(400)
  })

  it('both schools are listed as fired in the provenance', async () => {
    const { envelope } = await runBundle()
    const fired = (envelope['provenance'] as { sub_tools_fired: string[] }).sub_tools_fired
    expect(fired).toEqual(expect.arrayContaining(['jaimini_evidence', 'tajaka_evidence']))
  })
})

// ── Negative control: the OLD requests, sent through the same endpoint + store, return nothing ──────
describe('the former phantom requests were empty against the same store (negative control)', () => {
  it.each(['strength_extra', 'varshphal'])('query_chart_facts category=%s -> zero subjects (what the old school specs served)', async (category) => {
    stubPrimitives()
    const res = await fetch('http://x/api/mcp/primitives/query_chart_facts', { method: 'POST', body: JSON.stringify({ params: { category, limit: 20, chart_id: CHART_ID } }) })
    const body = await res.json() as { ok: boolean; result: { results: Array<{ content: string }> } }
    expect(body.ok).toBe(true)
    const content = JSON.parse(body.result.results[0]!.content) as { facts: unknown[]; total: number }
    expect(content.facts).toHaveLength(0)
    expect(content.total).toBe(0)
  })
})

// ── Static proof the data the specs ask for is written by a ga_* writer ────────────────────────────
describe('jaimini and tajaka backing is written by ga_* writers (static)', () => {
  const sensitive = readFileSync(join(SIDECAR, 'ga_writers', 'ga_sensitive_writer.py'), 'utf8')

  it('ga_sensitive emits karakamsa_position (KARAKAMSA) and arudha_pada (ARUDHA_A1..12 + 7 graha arudhas)', () => {
    expect(sensitive).toContain('_make_row("karakamsa_position", "KARAKAMSA", "sign"')
    expect(sensitive).toContain('_make_row("arudha_pada", subj, "sign"')
    expect(sensitive).toContain('subj = f"ARUDHA_A{house_num}"')
    for (const s of GRAHA_ARUDHA_SUBJECTS) expect(sensitive).toContain(`"${s}"`)
  })

  it('ga_sensitive stores karaka_chara_position for TWO schools under shared subject names (why it is not requested)', () => {
    expect(sensitive).toMatch(/\(KARAKA_SCHOOL_PARASHARI, parashari_sorted/)
    expect(sensitive).toMatch(/\(KARAKA_SCHOOL_KN_RAO, knrao_sorted/)
    const roles = readFileSync(join(SIDECAR, 'ga_writers', '_karaka_roles.py'), 'utf8')
    expect(roles).toContain('"ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",\n    "PUTRAKARAKA"') // 7-scheme
    expect(roles).toContain('"PITRIKARAKA", "PUTRAKARAKA"') // 8-scheme, same subject names
  })

  it('ga_tajaka writes l1_tajik_varsha_year_lords (orchestrated asset ga_tajaka)', () => {
    const writer = readFileSync(join(SIDECAR, 'ga_writers', 'ga_tajaka_writer.py'), 'utf8')
    expect(writer).toContain('INSERT INTO l1_tajik_varsha_year_lords')
    const adapter = readFileSync(join(SIDECAR, 'pipeline', 'orchestrator', 'writers', 'ga_tajaka.py'), 'utf8')
    expect(adapter).toContain("@register('ga_tajaka')")
  })

  it('the phantom names are really unwritten (negative control for the pin)', () => {
    const tajaka = readFileSync(join(SIDECAR, 'ga_writers', 'ga_tajaka_writer.py'), 'utf8')
    for (const phantom of ['strength_extra', 'varshphal']) {
      expect(sensitive).not.toContain(`"${phantom}"`)
      expect(tajaka).not.toContain(`"${phantom}"`)
    }
  })
})
