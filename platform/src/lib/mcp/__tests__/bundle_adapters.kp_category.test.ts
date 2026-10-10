/**
 * bundle_adapters.kp_category.test.ts — SS N-362 c: the LIVE multi-school bundle reads the KP school
 * from a category that is actually STORED.
 * ============================================================================================
 * Defect: buildSchoolSpec('kp') asked query_chart_facts for category 'kp_cusp'. No writer emits
 * 'kp_cusp' (platform-mcp school_conventions.ts section 3: "0 rows in production, never existed"),
 * so even with the Krishnamurti pin the KP evidence was EMPTY. The stored category that holds the
 * cusp star/sub-lord chain is 'cusp_kp_lords' (ga_nakshatra, ga_nakshatra_emitters.emit_kp_lords).
 *
 * DB-free. (1) A fake primitives endpoint implements query_chart_facts over a fixture store shaped
 * exactly like the writer's rows, so a wrong category / missing pin / missing chart_id yields an
 * empty or errored KP entry. (2) A static pin proves every chart_facts category the bundle requests
 * is emitted by a ga_* writer, reading the writer sources themselves.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { INVARIANT_STORED_FACT_CATEGORIES } from '../../retrieval/registry/constants'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u-1', audience_tier: 'client', key_id: 'k-1' }
const KP_LABEL = 'KP frame (Krishnamurti ayanamsha)'

const HERE = dirname(fileURLToPath(import.meta.url))
const SIDECAR = join(HERE, '..', '..', '..', '..', 'python-sidecar')

// ── Fixture store: rows shaped EXACTLY like ga_nakshatra_emitters.emit_kp_lords writes them ─────
// Writer (platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py emit_kp_lords): per cusp
//   _row(chart_id, ayanamsha_id, build_id, "cusp_kp_lords", f"CUSP_{h+1:02d}", key, value_text=lord)
// for key in compute_kp_lords(...) = star_lord, sub_lord, sub_sub_lord, prana_lord.
// The lords below are SYNTHETIC fixture values (the test checks plumbing, not astrology); the Lahiri
// copy deliberately differs so a read at the wrong ayanamsha is visible.
const KP_KEYS = ['star_lord', 'sub_lord', 'sub_sub_lord', 'prana_lord'] as const
const PLANETS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']

interface FixtureRow {
  fact_id: string
  chart_id: string
  ayanamsha_id: string
  fact_category: string
  fact_subject: string
  fact_key: string
  fact_value_text: string
}

function writerShapedCuspRows(ayanamshaId: string, shift: number): FixtureRow[] {
  const rows: FixtureRow[] = []
  for (let h = 0; h < 12; h++) {
    const subject = `CUSP_${String(h + 1).padStart(2, '0')}`
    KP_KEYS.forEach((key, k) => {
      rows.push({
        fact_id: `${ayanamshaId}:${subject}:${key}`,
        chart_id: CHART_ID,
        ayanamsha_id: ayanamshaId,
        fact_category: 'cusp_kp_lords',
        fact_subject: subject,
        fact_key: key,
        fact_value_text: PLANETS[(h + k + shift) % 9]!,
      })
    })
  }
  return rows
}

const STORE: FixtureRow[] = [
  ...writerShapedCuspRows('krishnamurti', 0),
  ...writerShapedCuspRows('lahiri_chitrapaksha', 3),
]

interface Recorded { toolName: string; body: Record<string, unknown> }

/**
 * Fake /api/mcp/primitives/<tool>. query_chart_facts mirrors the real handler's contract that matters
 * here: per_chart (no chart_id -> 400 CHART_REQUIRED), ayanamsha defaults to Lahiri when absent,
 * category filter is exact on fact_category, default shape is pivoted (one row per fact_subject,
 * `limit` counts SUBJECTS) and the payload key is `facts`. Everything else answers an empty ok result.
 */
function stubPrimitives(): { calls: Recorded[] } {
  const calls: Recorded[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/api/mcp/bundles/cache/store')) return { ok: true, status: 200, json: async () => ({ ok: true }) }
    const raw = init?.body ? JSON.parse(String(init.body)) as Record<string, unknown> : {}
    const body = (raw['params'] as Record<string, unknown>) ?? raw
    const toolName = url.split('/api/mcp/primitives/')[1] ?? 'unknown'
    calls.push({ toolName, body })
    if (toolName !== 'query_chart_facts') return { ok: true, status: 200, json: async () => ({ ok: true, result: {} }) }
    if (!body['chart_id']) {
      return { ok: false, status: 400, json: async () => ({ ok: false, error: { error_class: 'validation', message: 'CHART_REQUIRED' } }) }
    }
    const ayanamsha = String(body['ayanamsha_id'] ?? 'lahiri_chitrapaksha')
    const wanted = String(body['category'] ?? '').split(',').map(c => c.trim()).filter(Boolean)
    const limit = Math.min(Number(body['limit'] ?? 100), 1000)
    const rowCap = limit * 20 // the handler's raw-row fetch cap, (offset + limit) * 20
    const matched = STORE
      .filter(r => r.chart_id === body['chart_id'] && r.ayanamsha_id === ayanamsha && wanted.includes(r.fact_category))
      .slice(0, rowCap)
    const bySubject = new Map<string, Record<string, unknown>>()
    for (const r of matched) {
      if (!bySubject.has(r.fact_subject)) bySubject.set(r.fact_subject, { fact_subject: r.fact_subject, fact_category: r.fact_category })
      bySubject.get(r.fact_subject)![r.fact_key] = r.fact_value_text
    }
    const facts = Array.from(bySubject.values()).slice(0, limit)
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: true, result: { chart_id: body['chart_id'], ayanamsha_id: ayanamsha, shape: 'pivoted', facts, returned_count: facts.length, limit, total: bySubject.size } }),
    }
  }))
  return { calls }
}

beforeEach(() => { vi.resetModules() })
afterEach(() => { vi.unstubAllGlobals() })

async function runBundle(withChart = true): Promise<{ calls: Recorded[]; envelope: Record<string, unknown> }> {
  const { calls } = stubPrimitives()
  const { executeMultiSchoolBundle } = await import('../bundle_adapters')
  let envelope: Record<string, unknown> | undefined
  await executeMultiSchoolBundle(
    withChart ? { claim: 'career', tier: 'client', chart_id: CHART_ID } : { claim: 'career', tier: 'client' },
    PRINCIPAL,
    (event) => { if (event.type === 'bundle.completed') envelope = (event as unknown as { envelope: Record<string, unknown> }).envelope },
  )
  return { calls, envelope: envelope! }
}

describe('multi_school_bundle KP evidence is non-empty and labelled (SS N-362 c)', () => {
  it('fixture is shaped like the writer: 12 cusps x 4 keys = 48 rows, subjects CUSP_01..CUSP_12', () => {
    const kp = STORE.filter(r => r.ayanamsha_id === 'krishnamurti')
    expect(kp).toHaveLength(48)
    expect(new Set(kp.map(r => r.fact_subject)).size).toBe(12)
    expect(kp[0]!.fact_subject).toBe('CUSP_01')
  })

  it('kp_evidence carries the 12 cusp chains read at krishnamurti, with frame_label', async () => {
    const { envelope } = await runBundle()
    const entries = envelope['bundle_entries'] as Array<Record<string, unknown>>
    const kp = entries.find(e => e['sub_tool'] === 'kp_evidence')!
    expect(kp['errored']).toBe(false)
    expect(kp['frame_label']).toBe(KP_LABEL)
    const result = (kp['data'] as { result: Record<string, unknown> }).result
    expect(result['ayanamsha_id']).toBe('krishnamurti')
    const facts = result['facts'] as Array<Record<string, unknown>>
    expect(facts.length).toBeGreaterThan(0)
    expect(facts).toHaveLength(12)
    expect(facts.map(f => f['fact_subject'])).toEqual(Array.from({ length: 12 }, (_, h) => `CUSP_${String(h + 1).padStart(2, '0')}`))
    for (const f of facts) {
      expect(f['fact_category']).toBe('cusp_kp_lords')
      for (const key of KP_KEYS) expect(typeof f[key]).toBe('string')
    }
    // the values are the krishnamurti copy (shift 0), not the Lahiri copy (shift 3): CUSP_01 sub_lord
    expect(facts[0]!['sub_lord']).toBe(PLANETS[1])
    expect(facts[0]!['sub_lord']).not.toBe(PLANETS[(0 + 1 + 3) % 9])
    expect(envelope['school_frames']).toEqual({ kp: KP_LABEL })
  })

  it('the KP primitive call asks for the stored category at krishnamurti with the chart, never kp_cusp', async () => {
    const { calls } = await runBundle()
    const kpCall = calls.find(c => c.toolName === 'query_chart_facts' && c.body['ayanamsha_id'] === 'krishnamurti')
    expect(kpCall, 'KP primitive call').toBeDefined()
    expect(kpCall!.body['category']).toBe('cusp_kp_lords')
    expect(kpCall!.body['ayanamsha_id']).toBe('krishnamurti')
    expect(kpCall!.body['chart_id']).toBe(CHART_ID)
    expect(kpCall!.body['limit']).toBe(20)
    for (const c of calls) expect(c.body['category']).not.toBe('kp_cusp')
    // limit counts pivoted SUBJECTS: 12 cusps fit in 20, and the raw-row cap (limit * 20 = 400) covers 48 rows
    expect(12).toBeLessThanOrEqual(20)
    expect(48).toBeLessThanOrEqual(20 * 20)
  })

  it('without a chart_id the entry errors honestly (no fabricated evidence)', async () => {
    const { envelope } = await runBundle(false)
    const entries = envelope['bundle_entries'] as Array<Record<string, unknown>>
    const kp = entries.find(e => e['sub_tool'] === 'kp_evidence')!
    expect(kp['errored']).toBe(true)
    expect(kp['upstream_status']).toBe(400)
  })
})

// ── Static pin: every chart_facts category the bundle requests is emitted by a ga_* writer ──────

function walkPy(dir: string): string[] {
  const out: string[] = []
  for (const name of readdirSync(dir)) {
    if (name === '__tests__' || name === 'tests' || name === '__pycache__') continue
    const full = join(dir, name)
    if (statSync(full).isDirectory()) out.push(...walkPy(full))
    else if (name.endsWith('.py')) out.push(full)
  }
  return out
}

const WRITER_DIRS = [join(SIDECAR, 'ga_writers'), join(SIDECAR, 'pipeline', 'orchestrator', 'writers')]

function categoryIsEmittedByAWriter(category: string): boolean {
  const literal = new RegExp(`["']${category}["']`)
  return WRITER_DIRS.some(dir => walkPy(dir).some(f => literal.test(readFileSync(f, 'utf8'))))
}

/**
 * Phantom categories still requested by the OTHER school specs of the same function (SS N-362 c finding;
 * NOT fixed here, only the KP case is). The test asserts this list is exactly the set of requested
 * chart_facts categories that no writer emits, so a new phantom fails the test and a fixed one forces
 * the entry to be removed.
 */
const KNOWN_PHANTOM_CATEGORIES: Record<string, string> = {
  jaimini: 'strength_extra',
  tajaka: 'varshphal',
}

describe('multi_school_bundle requests only stored fact categories (static pin)', () => {
  it('KP category is emitted by ga_nakshatra, per cusp, with the four lord keys, and is not INVARIANT', () => {
    const emitters = readFileSync(join(SIDECAR, 'ga_writers', 'ga_nakshatra_emitters.py'), 'utf8')
    expect(emitters).toMatch(/_row\(chart_id, ayanamsha_id, build_id, "cusp_kp_lords", cusp_subj, key,/)
    expect(emitters).toContain('cusp_subj = f"CUSP_{h+1:02d}"')
    const compute = readFileSync(join(SIDECAR, 'ga_writers', 'ga_nakshatra_compute.py'), 'utf8')
    for (const key of KP_KEYS) expect(compute).toContain(`"${key}":`)
    const orchestrated = readFileSync(join(SIDECAR, 'pipeline', 'orchestrator', 'writers', 'ga_nakshatra.py'), 'utf8')
    expect(orchestrated).toMatch(/GA_NAKSHATRA_FACT_CATEGORIES = \[[^\]]*"cusp_kp_lords"/s)
    // per-ayanamsha, so the Krishnamurti pin is meaningful: a KP chain is never stored under INVARIANT
    expect(INVARIANT_STORED_FACT_CATEGORIES.has('cusp_kp_lords')).toBe(false)
  })

  it('kp_categories.ts (when present: PR-2) lists the category the bundle requests', async () => {
    const path = join(HERE, '..', '..', 'retrieval', 'registry', 'kp_categories.ts')
    if (!existsSync(path)) return // lands with PR-2; the writer proof above is the standing guard
    const mod = await import(/* @vite-ignore */ path) as { KP_FRAME_CATEGORIES: readonly string[] }
    const { KP_SCHOOL_FACT_CATEGORY } = await import('../bundle_adapters')
    expect(mod.KP_FRAME_CATEGORIES).toContain(KP_SCHOOL_FACT_CATEGORY)
  })

  it('every chart_facts category in buildSchoolSpec is a writer-emitted category, except the listed phantoms', async () => {
    const { buildSchoolSpec } = await import('../bundle_adapters')
    const requested: Record<string, string> = {}
    for (const school of ['parashara', 'jaimini', 'kp', 'tajaka'] as const) {
      const spec = buildSchoolSpec(school)
      if (spec?.toolName === 'query_chart_facts') requested[school] = String(spec.params['category'])
    }
    expect(requested['kp']).toBe('cusp_kp_lords')
    expect(categoryIsEmittedByAWriter('cusp_kp_lords')).toBe(true)
    const unproven = Object.fromEntries(Object.entries(requested).filter(([, c]) => !categoryIsEmittedByAWriter(c)))
    expect(unproven).toEqual(KNOWN_PHANTOM_CATEGORIES)
    // the negative control: the old KP name really is unwritten, so the check can fail
    expect(categoryIsEmittedByAWriter('kp_cusp')).toBe(false)
  })
})
