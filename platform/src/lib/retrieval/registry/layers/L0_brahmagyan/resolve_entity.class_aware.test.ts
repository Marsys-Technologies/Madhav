/**
 * TI-L0-14 (SS Q4, option a): resolve_entity is class-aware and no longer silently picks one of
 * several matching (class, id) rows.
 *
 * What this proves, against a fake ontology that evaluates the handler's real SQL semantics
 * (the filter and the ORDER BY are re-implemented here; the live statement is also asserted to
 * contain them verbatim):
 *   - served ids do NOT change: for every name, `canonical_id` / `entity_class` equal what the
 *     previous `LIMIT 1` query returned (same ORDER BY);
 *   - a name in two classes now reports `ambiguous: true` plus every candidate;
 *   - `entity_class` restricts the match, so a caller can ask for the yoga or the dosha;
 *   - (env-gated) against a copy of the production ontology, for EVERY name string it carries the
 *     handler's real statement picks the previous winner and `ambiguous` is exact;
 *   - not-found keeps its shape (+ ambiguous:false, candidates: []).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

type Row = {
  canonical_id: string; entity_class: string; canonical_name_en: string; canonical_name_sa: string | null
  synonyms: string[]; description: string | null; source_citation: string
}
const mk = (canonical_id: string, entity_class: string, en: string, syn: string[] = []): Row => ({
  canonical_id, entity_class, canonical_name_en: en, canonical_name_sa: null, synonyms: syn, description: null, source_citation: 'x',
})
const ONTOLOGY: Row[] = [
  mk('kemadruma', 'yoga', 'Kemadruma Yoga', ['kemadruma']),
  mk('kemadruma', 'dosha', 'Kemadruma Dosha', ['Kemadruma Dosha']),
  mk('navamsa', 'concept', 'Navamsa', ['D9', 'navamsa']),
  mk('d9', 'varga', 'Navamsa (D9)', ['D9']),
  mk('jupiter', 'planet', 'Jupiter', ['guru', 'Jupiter']),
  mk('phaladeepika', 'school', 'Phaladeepika', ['phaladeepika']),
  mk('phaladeepika', 'text', 'Phaladeepika', ['phaladeepika']),
]

let lastSql = ''
let lastParams: unknown[] = []
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params: unknown[]) => {
    lastSql = sql; lastParams = params
    const [name, cls] = params as [string, string | null]
    const rows = ONTOLOGY.filter((r) =>
      (r.synonyms.includes(name) || r.canonical_name_en.toLowerCase() === name.toLowerCase() ||
       (r.canonical_name_sa ?? '').toLowerCase() === name.toLowerCase()) &&
      (cls === null || r.entity_class === cls))
    rows.sort((a, b) =>
      Number(b.entity_class === 'varga') - Number(a.entity_class === 'varga') ||
      a.entity_class.localeCompare(b.entity_class) || a.canonical_id.localeCompare(b.canonical_id))
    return { rows }
  }),
}))

import { resolveEntityCapability } from './resolve_entity'
type H = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
const call = (a: Record<string, unknown>) => (resolveEntityCapability.handler as H)(a)

// the previous behaviour: the same filter + ORDER BY, LIMIT 1
const previousWinner = (name: string) => {
  const rows = ONTOLOGY.filter((r) => r.synonyms.includes(name) || r.canonical_name_en.toLowerCase() === name.toLowerCase())
  rows.sort((a, b) => Number(b.entity_class === 'varga') - Number(a.entity_class === 'varga') ||
    a.entity_class.localeCompare(b.entity_class) || a.canonical_id.localeCompare(b.canonical_id))
  return rows[0]
}

describe('resolve_entity - class-aware (TI-L0-14)', () => {
  beforeEach(() => { lastSql = ''; lastParams = [] })

  it('keeps the previous winner for every name (no served id moves)', async () => {
    for (const name of ['Kemadruma Dosha', 'kemadruma', 'D9', 'Jupiter', 'guru', 'phaladeepika', 'Navamsa']) {
      const res = (await call({ name })).content
      const prev = previousWinner(name)
      expect([res.canonical_id, res.entity_class]).toEqual([prev.canonical_id, prev.entity_class])
    }
  })

  it('reports ambiguity with every candidate when a name belongs to two classes', async () => {
    const res = (await call({ name: 'phaladeepika' })).content
    expect(res.ambiguous).toBe(true)
    expect(res.candidates).toEqual([
      { canonical_id: 'phaladeepika', entity_class: 'school' },
      { canonical_id: 'phaladeepika', entity_class: 'text' },
    ])
  })

  it('reports the varga/concept tie on D9 and still picks varga first', async () => {
    const res = (await call({ name: 'D9' })).content
    expect(res.entity_class).toBe('varga')
    expect(res.ambiguous).toBe(true)
    expect((res.candidates as { entity_class: string }[]).map((c) => c.entity_class)).toEqual(['varga', 'concept'])
  })

  it('an unambiguous name is ambiguous:false with no candidates', async () => {
    const res = (await call({ name: 'Jupiter' })).content
    expect(res.ambiguous).toBe(false)
    expect(res.candidates).toEqual([])
  })

  it('entity_class selects the class; the filter is passed to the database', async () => {
    const dosha = (await call({ name: 'Kemadruma Dosha', entity_class: 'dosha' })).content
    expect(dosha.entity_class).toBe('dosha')
    expect(lastParams).toEqual(['Kemadruma Dosha', 'dosha'])
    const text = (await call({ name: 'phaladeepika', entity_class: 'text' })).content
    expect([text.entity_class, text.ambiguous]).toEqual(['text', false])
    const none = (await call({ name: 'phaladeepika', entity_class: 'yoga' })).content
    expect(none.not_found).toBe(true)
  })

  it('not-found keeps its shape and adds the disclosure fields', async () => {
    const res = (await call({ name: 'zzz' })).content
    expect(res).toMatchObject({ canonical_id: null, entity_class: null, not_found: true, ambiguous: false, candidates: [], input: 'zzz' })
  })

  it('the statement keeps the deterministic ORDER BY and is bounded', async () => {
    await call({ name: 'Jupiter' })
    expect(lastSql).toContain("ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id")
    expect(lastSql).toMatch(/LIMIT 25/)
    expect(lastSql).toContain('$2::text IS NULL OR entity_class = $2')
  })

  it('name is still required', async () => {
    expect((await call({})).is_error).toBe(true)
  })

  it('declares the new optional input and mentions ambiguity in the description', () => {
    expect(resolveEntityCapability.input_schema).toHaveProperty('entity_class')
    expect(resolveEntityCapability.required_inputs).toEqual(['name'])
    expect(resolveEntityCapability.description).toMatch(/ambiguous=true/)
  })
})

// ── real PostgreSQL census (env-gated) ───────────────────────────────────────────
// L0D_ONTOLOGY_CLONE_CONNINFO = libpq-style JSON {"host","port","user","database"} of a DISPOSABLE database whose name
// ends in _test and holds a copy of brahma_ontology (production public reference data, 741 rows). For EVERY name string
// the ontology carries, the handler's REAL statement picks the same winner as the previous `LIMIT 1` statement, and
// `ambiguous` is true exactly when more than one distinct (class, id) matches.
const CLONE = process.env.L0D_ONTOLOGY_CLONE_CONNINFO
describe.skipIf(!CLONE)('resolve_entity - real database census (TI-L0-14)', () => {
  it('keeps the winner of the previous statement for every ontology name and flags ambiguity exactly', async () => {
    const info = JSON.parse(CLONE as string) as { host: string; port: number; user: string; database: string }
    expect(info.database.endsWith('_test')).toBe(true)
    const { Client } = await import('pg')
    const db = new Client(info)
    await db.connect()
    try {
      const names = new Set<string>()
      const all = await db.query('SELECT canonical_name_en, canonical_name_sa, synonyms FROM brahma_ontology')
      for (const r of all.rows) { names.add(r.canonical_name_en); if (r.canonical_name_sa) names.add(r.canonical_name_sa); for (const s of r.synonyms) names.add(s) }
      const { query } = await import('@/lib/db/client')
      ;(query as unknown as { mockImplementation: (f: unknown) => void }).mockImplementation(async (sql: string, params: unknown[]) => {
        const r = await db.query(sql, params as unknown[])
        return { rows: r.rows }
      })
      let ambiguous = 0
      for (const name of names) {
        const prev = await db.query(
          `SELECT canonical_id, entity_class FROM brahma_ontology
            WHERE $1 = ANY(synonyms) OR lower(canonical_name_en) = lower($1) OR lower(canonical_name_sa) = lower($1)
            ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id LIMIT 1`, [name])
        const res = (await call({ name })).content
        expect([res.canonical_id, res.entity_class]).toEqual([prev.rows[0]?.canonical_id ?? null, prev.rows[0]?.entity_class ?? null])
        const distinct = await db.query(
          `SELECT count(DISTINCT (entity_class, canonical_id))::int AS n FROM brahma_ontology
            WHERE $1 = ANY(synonyms) OR lower(canonical_name_en) = lower($1) OR lower(canonical_name_sa) = lower($1)`, [name])
        expect(res.ambiguous).toBe(distinct.rows[0].n > 1)
        if (res.ambiguous) ambiguous += 1
      }
      expect(names.size).toBeGreaterThan(2000)
      expect(ambiguous).toBeGreaterThan(0)
    } finally {
      await db.end()
    }
  })
})
