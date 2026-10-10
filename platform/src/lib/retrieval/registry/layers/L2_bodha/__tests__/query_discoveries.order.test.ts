/**
 * query_discoveries — ordering pin (SS N-354).
 *
 * `composite_discovery_rank` is a SCORE written by bo_anveshana
 * (`rank * (1 + corroborating_methods * 0.2)`, sorted DESC by the writer; every other
 * consumer orders DESC), so HIGHER = more salient. This serving tool used to order ASC and
 * therefore listed the WEAKEST findings first, and built each family's "best" rank and
 * narrative fields from its weakest member.
 *
 * The DB is mocked, so a plain mock cannot prove ordering. Instead the mocked `query`
 * EXECUTES the ORDER BY / array_agg(... ORDER BY ...) / MIN|MAX clauses the handler
 * actually emitted against fixture rows with KNOWN scores (a small interpreter with
 * PostgreSQL's NULLS semantics). If the handler's SQL regresses to ASC / MIN, the
 * assertions below fail; a sensitivity test proves the interpreter itself would catch it.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/retrieval/tail/build_tail_watch', () => ({
  buildTailWatch: vi.fn(async () => ({
    tail_watch: [], tail_watch_empty_reason: null, tail_watch_components: [],
  })),
}))
import { query as mockQuery } from '@/lib/db/client'
import { queryDiscoveriesCapability } from '../query_discoveries'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

type Row = Record<string, unknown>

function disc(
  discovery_id: string, composite_discovery_rank: number | null, non_obviousness_score: number | null,
  family: 'X' | 'V' | 'Y' | 'Z', ayanamsha_id: string, narrative: string,
): Row {
  const f = {
    X: { discovery_class: 'c1', discovery_subsystem: 's1', hypothesis_text: 'hyp-X' },
    V: { discovery_class: 'a_class', discovery_subsystem: 's1', hypothesis_text: 'hyp-V' },
    Y: { discovery_class: 'c2', discovery_subsystem: 's1', hypothesis_text: 'hyp-Y' },
    Z: { discovery_class: 'c3', discovery_subsystem: 's1', hypothesis_text: 'hyp-Z' },
  }[family]
  return {
    discovery_id, ayanamsha_id, ...f, composite_discovery_rank, non_obviousness_score,
    consequence_score: 0.5,
    surface_reading: `surface:${narrative}`, depth_reading: `depth:${narrative}`,
    why_an_acharya_misses_it: `why:${narrative}`, novelty_class: `novelty:${narrative}`,
    affected_domains_array: [`dom:${narrative}`],
  }
}

// Insertion order is deliberately WEAKEST-FIRST within family X (d-01 = 0.30 is listed
// before d-02 = 1.20), so a "first row wins" aggregate would pick the wrong narrative.
const FIXTURE: Row[] = [
  disc('d-01', 0.30, 0.5, 'X', 'lahiri_chitrapaksha', 'weak-X'),
  disc('d-02', 1.20, 0.9, 'X', 'raman', 'strong-X'),
  disc('d-03', 0.75, 0.6, 'X', 'kp_newcomb', 'mid-X'),
  disc('d-04', null, 0.99, 'Y', 'lahiri_chitrapaksha', 'null-Y'),
  disc('d-05', 0.75, 0.6, 'Y', 'raman', 'mid-Y'),
  disc('d-06', 0.75, 0.7, 'V', 'lahiri_chitrapaksha', 'mid-V'),
  disc('d-07', null, 0.2, 'Z', 'raman', 'null-Z'),
]

// ── minimal SQL-ORDER-BY interpreter (PostgreSQL NULL ordering semantics) ─────────────────────
interface Term { expr: string; desc: boolean; nullsFirst: boolean }

function splitTop(s: string): string[] {
  const out: string[] = []
  let depth = 0
  let cur = ''
  for (const ch of s) {
    if (ch === '(') depth++
    if (ch === ')') depth--
    if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; continue }
    cur += ch
  }
  if (cur.trim()) out.push(cur.trim())
  return out
}

function parseTerms(clause: string): Term[] {
  return splitTop(clause).map(raw => {
    const m = /^(.*?)\s*(ASC|DESC)?(?:\s+NULLS\s+(FIRST|LAST))?$/is.exec(raw.replace(/\s+/g, ' ').trim())!
    const desc = (m[2] ?? 'ASC').toUpperCase() === 'DESC'
    // PostgreSQL default: NULLs sort as if larger than any value (ASC -> last, DESC -> first)
    const nullsFirst = m[3] ? m[3].toUpperCase() === 'FIRST' : desc
    return { expr: m[1]!.trim(), desc, nullsFirst }
  })
}

function cmp(a: unknown, b: unknown, t: Term): number {
  const an = a === null || a === undefined
  const bn = b === null || b === undefined
  if (an || bn) {
    if (an && bn) return 0
    return an ? (t.nullsFirst ? -1 : 1) : (t.nullsFirst ? 1 : -1)
  }
  const c = (a as number | string) < (b as number | string) ? -1 : (a as number | string) > (b as number | string) ? 1 : 0
  return t.desc ? -c : c
}

function sortBy<T>(items: T[], terms: Term[], get: (item: T, expr: string) => unknown): T[] {
  return [...items].sort((x, y) => {
    for (const t of terms) {
      const c = cmp(get(x, t.expr), get(y, t.expr), t)
      if (c !== 0) return c
    }
    return 0
  })
}

const col = (r: Row, expr: string) => r[expr]

function aggNum(rows: Row[], fn: 'MIN' | 'MAX', column: string): number | null {
  const vals = rows.map(r => r[column]).filter((v): v is number => typeof v === 'number')
  if (vals.length === 0) return null
  return fn === 'MIN' ? Math.min(...vals) : Math.max(...vals)
}

function famGet(members: Row[], expr: string): unknown {
  const m = /^(MIN|MAX)\((\w+)\)$/i.exec(expr)
  if (m) return aggNum(members, m[1]!.toUpperCase() as 'MIN' | 'MAX', m[2]!)
  return members[0]![expr] // a GROUP BY key
}

function runFamilySql(sql: string, rows: Row[]): Row[] {
  const groups = new Map<string, Row[]>()
  for (const r of rows) {
    const k = JSON.stringify([r['discovery_class'], r['discovery_subsystem'], r['hypothesis_text']])
    groups.set(k, [...(groups.get(k) ?? []), r])
  }
  const bestFn = /(MIN|MAX)\(composite_discovery_rank\)\s+AS best_composite_discovery_rank/i.exec(sql)![1]!.toUpperCase() as 'MIN' | 'MAX'
  const aggs = [...sql.matchAll(/\(array_agg\((.+?) ORDER BY ([^)]*?)\)\)(\[[^\]]+\])?\s+AS (\w+)/gis)]
  expect(aggs.length).toBeGreaterThanOrEqual(6) // member ids, domains, 4 narrative fields
  const finalOrder = /GROUP BY[\s\S]*?ORDER BY\s+([\s\S]*?)\s+LIMIT/i.exec(sql)![1]!
  const families = [...groups.values()].map(members => {
    const out: Row = {
      discovery_class: members[0]!['discovery_class'],
      discovery_subsystem: members[0]!['discovery_subsystem'],
      hypothesis_text: members[0]!['hypothesis_text'],
      member_count: members.length,
      ayanamsha_count: new Set(members.map(m => m['ayanamsha_id'])).size,
      ayanamsha_ids: [...new Set(members.map(m => m['ayanamsha_id']))],
      best_composite_discovery_rank: aggNum(members, bestFn, 'composite_discovery_rank'),
      affected_domains_variant_count: 1,
    }
    for (const a of aggs) {
      let expr = a[1]!.trim()
      const to = /^to_jsonb\((\w+)\)$/.exec(expr)
      if (to) expr = to[1]!
      const ordered = sortBy(members, parseTerms(a[2]!), col)
      const slice = a[3]
      const vals = ordered.map(r => r[expr])
      out[a[4]!] = slice === '[1]' ? vals[0] : vals.slice(0, 10)
    }
    ;(out as { __members: Row[] }).__members = members
    return out
  })
  const sorted = sortBy(families, parseTerms(finalOrder), (f, expr) => famGet((f as { __members: Row[] }).__members, expr))
  return sorted.map(f => { const { __members, ...rest } = f as Row & { __members: Row[] }; void __members; return rest })
}

function installFakeDb() {
  ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockImplementation(async (sql: string, params: unknown[] = []) => {
    const q = String(sql)
    const limit = Number(params.at(-2))
    const offset = Number(params.at(-1))
    if (q.includes('array_agg')) {
      return { rows: runFamilySql(q, FIXTURE).slice(offset, offset + limit) }
    }
    if (q.includes(') fam')) {
      return { rows: [{ total: String(new Set(FIXTURE.map(r => `${r['discovery_class']}|${r['hypothesis_text']}`)).size) }] }
    }
    if (q.includes('COUNT(DISTINCT ayanamsha_id)::text AS n')) {
      return { rows: [{ n: String(new Set(FIXTURE.map(r => r['ayanamsha_id'])).size) }] }
    }
    if (q.includes('COUNT(*)::text AS total')) return { rows: [{ total: String(FIXTURE.length) }] }
    const order = /ORDER BY\s+([\s\S]*?)\s+LIMIT/i.exec(q)![1]!
    return { rows: sortBy(FIXTURE, parseTerms(order), col).slice(offset, offset + limit) }
  })
}

type Content = {
  rows: Row[]
  discovery_families: Array<Record<string, unknown>>
  more_available: boolean
  more_families_available: boolean
  total_matching: number
  total_family_count: number
}

async function call(args: Record<string, unknown> = {}): Promise<Content> {
  const res = await queryDiscoveriesCapability.handler({ chart_id: CHART, ...args }, undefined)
  expect(res.is_error).toBe(false)
  return res.content as Content
}

beforeEach(() => {
  ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockReset()
  installFakeDb()
})

const EXPECTED_ROW_ORDER = ['d-02', 'd-06', 'd-03', 'd-05', 'd-01', 'd-04', 'd-07']

describe('query_discoveries — rows are listed STRONGEST first', () => {
  it('orders by composite_discovery_rank DESC, then non_obviousness DESC, then discovery_id ASC, NULL ranks last', async () => {
    const c = await call()
    // d-02 (1.20) first; the 0.75 tie breaks on non_obviousness (d-06 0.7 > d-03 = d-05 0.6),
    // then on discovery_id (d-03 < d-05); d-01 (0.30) is the weakest scored row; NULL ranks last
    // (d-04 before d-07 on non_obviousness 0.99 > 0.2).
    expect(c.rows.map(r => r['discovery_id'])).toEqual(EXPECTED_ROW_ORDER)
  })

  it('never lists the weakest scored finding ahead of a stronger one', async () => {
    const c = await call()
    const scores = c.rows.map(r => r['composite_discovery_rank']).filter((s): s is number => s !== null)
    expect(scores).toEqual([...scores].sort((a, b) => b - a))
    expect(c.rows[0]!['composite_discovery_rank']).toBe(1.2)
  })

  it('is a total order: ties on rank and non_obviousness resolve by discovery_id ASC', async () => {
    const c = await call()
    const ids = c.rows.map(r => r['discovery_id'])
    expect(ids.indexOf('d-03')).toBeLessThan(ids.indexOf('d-05'))
  })

  it('emits the DESC clauses in SQL (no ascending composite_discovery_rank ordering remains)', async () => {
    await call()
    const sqls = (mockQuery as unknown as ReturnType<typeof vi.fn>).mock.calls.map(c => String(c[0]))
    const joined = sqls.join('\n')
    expect(joined).not.toMatch(/composite_discovery_rank\s+ASC/i)
    expect(joined).not.toMatch(/MIN\(composite_discovery_rank\)/i)
    expect(joined).toMatch(/ORDER BY composite_discovery_rank DESC NULLS LAST, non_obviousness_score DESC NULLS LAST, discovery_id ASC/)
  })

  it('harness sensitivity: the interpreter DOES detect the old ascending order', () => {
    const oldOrder = 'composite_discovery_rank ASC NULLS LAST, non_obviousness_score DESC NULLS LAST'
    const ids = sortBy(FIXTURE, parseTerms(oldOrder), col).map(r => r['discovery_id'])
    expect(ids[0]).toBe('d-01') // the weakest scored row first
    expect(ids).not.toEqual(EXPECTED_ROW_ORDER)
  })
})

describe('query_discoveries — families', () => {
  it('best_composite_discovery_rank is the MAX of the members (field name kept)', async () => {
    const c = await call()
    const byHyp = Object.fromEntries(c.discovery_families.map(f => [f['hypothesis_text'], f]))
    expect(byHyp['hyp-X']!['best_composite_discovery_rank']).toBe(1.2) // not 0.30
    expect(byHyp['hyp-V']!['best_composite_discovery_rank']).toBe(0.75)
    expect(byHyp['hyp-Y']!['best_composite_discovery_rank']).toBe(0.75) // NULL member ignored
    expect(byHyp['hyp-Z']!['best_composite_discovery_rank']).toBeNull()
  })

  it('orders families by their best (MAX) score DESC, NULL last, ties by family key', async () => {
    const c = await call()
    // X 1.20; V and Y tie on 0.75 -> discovery_class ASC ('a_class' < 'c2'); Z (all-NULL) last.
    expect(c.discovery_families.map(f => f['hypothesis_text'])).toEqual(['hyp-X', 'hyp-V', 'hyp-Y', 'hyp-Z'])
  })

  it('member_discovery_ids list the highest-scoring member first (weak member listed first in the data)', async () => {
    const c = await call()
    const x = c.discovery_families.find(f => f['hypothesis_text'] === 'hyp-X')!
    expect(x['member_discovery_ids']).toEqual(['d-02', 'd-03', 'd-01'])
    const y = c.discovery_families.find(f => f['hypothesis_text'] === 'hyp-Y')!
    expect(y['member_discovery_ids']).toEqual(['d-05', 'd-04']) // NULL rank member last
  })

  it('family narrative fields come from the HIGHEST-scoring member, not the weakest', async () => {
    const c = await call()
    const x = c.discovery_families.find(f => f['hypothesis_text'] === 'hyp-X')!
    expect(x['surface_reading']).toBe('surface:strong-X')
    expect(x['depth_reading']).toBe('depth:strong-X')
    expect(x['why_an_acharya_misses_it']).toBe('why:strong-X')
    expect(x['novelty_class']).toBe('novelty:strong-X')
    expect(x['affected_domains_array']).toEqual(['dom:strong-X'])
    const y = c.discovery_families.find(f => f['hypothesis_text'] === 'hyp-Y')!
    expect(y['surface_reading']).toBe('surface:mid-Y') // scored member beats the NULL-rank one
  })

  it('every family aggregate orders DESC with a discovery_id tie-break in SQL', async () => {
    await call()
    const fam = (mockQuery as unknown as ReturnType<typeof vi.fn>).mock.calls
      .map(c => String(c[0])).find(s => s.includes('array_agg'))!
    const aggOrders = [...fam.matchAll(/ORDER BY ([^)]*?)\)\)/g)].map(m => m[1])
    expect(aggOrders.length).toBe(6)
    for (const o of aggOrders) expect(o).toBe('composite_discovery_rank DESC NULLS LAST, discovery_id ASC')
    expect(fam).toMatch(/MAX\(composite_discovery_rank\)\s+AS best_composite_discovery_rank/)
    expect(fam).toMatch(/ORDER BY MAX\(composite_discovery_rank\) DESC NULLS LAST,\s+discovery_class ASC NULLS LAST, discovery_subsystem ASC NULLS LAST, hypothesis_text ASC NULLS LAST/)
  })
})

describe('query_discoveries — pagination is stable under the new order', () => {
  it('limit/offset pages of rows concatenate to the full strongest-first order with no overlap', async () => {
    const pages: string[] = []
    for (let offset = 0; offset < FIXTURE.length; offset += 3) {
      const c = await call({ limit: 3, offset })
      expect(c.total_matching).toBe(FIXTURE.length)
      pages.push(...c.rows.map(r => String(r['discovery_id'])))
    }
    expect(pages).toEqual(EXPECTED_ROW_ORDER)
    expect(new Set(pages).size).toBe(pages.length)
  })

  it('more_available tracks the offset window', async () => {
    expect((await call({ limit: 3, offset: 0 })).more_available).toBe(true)
    expect((await call({ limit: 3, offset: 6 })).more_available).toBe(false)
  })

  it('limit/offset pages of families concatenate to the full family order', async () => {
    const seen: unknown[] = []
    for (let offset = 0; offset < 4; offset++) {
      const c = await call({ limit: 1, offset })
      expect(c.total_family_count).toBe(4)
      seen.push(...c.discovery_families.map(f => f['hypothesis_text']))
    }
    expect(seen).toEqual(['hyp-X', 'hyp-V', 'hyp-Y', 'hyp-Z'])
  })

  it('repeated calls return the identical order (deterministic)', async () => {
    const a = await call()
    const b = await call()
    expect(b.rows.map(r => r['discovery_id'])).toEqual(a.rows.map(r => r['discovery_id']))
    expect(b.discovery_families).toEqual(a.discovery_families)
  })
})

describe('query_discoveries — tool description states the score semantics', () => {
  it('says higher = more salient, a score, not a 1..N rank; no stale "1 = most salient" / ASC wording', () => {
    const d = queryDiscoveriesCapability.description
    expect(d).toContain('higher = more salient')
    expect(d).toContain('not a 1..N rank')
    expect(d).toContain('composite_discovery_rank DESC')
    expect(d).not.toContain('1 = most salient')
    expect(d).not.toMatch(/composite_discovery_rank ASC/)
  })
})
