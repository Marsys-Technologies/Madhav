/**
 * five_ayanamsha_fake_db.ts — a tiny disposable SQL SIMULATOR for the Lahiri-primary contract tests.
 *
 * No database. `query(sql, params)` reads the SQL text and the bound params the way Postgres would
 * for the handful of constructs the registry handlers use, over a fixture that holds ALL FIVE
 * ayanamshas' rows plus a few `INVARIANT` sentinel rows, with the krishnamurti rows listed FIRST
 * and Lahiri LAST, and each ayanamsha holding more rows than one handler page (the worst case for
 * "Lahiri hidden behind other ayanamshas' rows on page 1"):
 *
 *   - ayanamsha predicate: `ayanamsha_id = $n`, `ayanamsha_id IN ($n, 'INVARIANT')`,
 *     `ayanamsha_id = ANY($n)`, `ayanamsha_id = '<literal>'` (alias-qualified or not);
 *   - ordering: an ORDER BY that carries the AYANAMSHA_SERVE_ORDER expression sorts by serve order
 *     (Lahiri first; INVARIANT last); an ORDER BY that names `ayanamsha_id` any other way sorts
 *     alphabetically (krishnamurti first, the pre-PR-2 behaviour); no ayanamsha in the ORDER BY
 *     keeps fixture order (krishnamurti first);
 *   - LIMIT / OFFSET: `LIMIT $n OFFSET $m` or literals;
 *   - `COUNT(*)` statements answer the filtered row count.
 *
 * It is a model of the SQL contract, not of Postgres: it exists so ONE table-driven test can assert
 * "page 1 is Lahiri" across every handler without a database.
 */
import { AYANAMSHA_SERVE_ORDER } from '../../constants'

export const KRISHNAMURTI_FIRST_FIXTURE_ORDER = [
  'krishnamurti',
  'true_chitra',
  'raman',
  'surya_siddhanta_classical',
  'lahiri_chitrapaksha',
] as const

export interface FixtureRow extends Record<string, unknown> {
  ayanamsha_id: string
}

/** More rows per ayanamsha than any handler's default page (largest default page is 500). */
export const ROWS_PER_AYANAMSHA = 620
export const INVARIANT_ROWS = 3

export function buildFiveAyanamshaFixture(): FixtureRow[] {
  const rows: FixtureRow[] = []
  for (const ayanamsha_id of KRISHNAMURTI_FIRST_FIXTURE_ORDER) {
    for (let i = 0; i < ROWS_PER_AYANAMSHA; i += 1) {
      rows.push({
        fact_id: `${ayanamsha_id}-${i}`,
        id: `${ayanamsha_id}-${i}`,
        chart_id: '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
        ayanamsha_id,
        fact_category: 'graha_position',
        fact_subject: 'SUN',
        fact_key: `k${String(i).padStart(4, '0')}`,
        fact_value_text: 'x',
        fact_value_num: i,
        fact_value_jsonb: null,
        citation_ref: `ref-${ayanamsha_id}-${i}`,
        citation_human: null,
        verification_pass_status: 'single',
      })
    }
  }
  for (let i = 0; i < INVARIANT_ROWS; i += 1) {
    rows.push({
      fact_id: `INVARIANT-${i}`, id: `INVARIANT-${i}`, chart_id: '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
      ayanamsha_id: 'INVARIANT', fact_category: 'panchanga_tithi', fact_subject: 'BIRTH',
      fact_key: `inv${i}`, fact_value_text: 'x', fact_value_num: null, fact_value_jsonb: null,
      citation_ref: `ref-INVARIANT-${i}`, citation_human: null, verification_pass_status: 'single',
    })
  }
  return rows
}

export interface SimulatedStatement {
  sql: string
  params: unknown[]
  /** Statement carries an ayanamsha predicate (so the filter was simulated). */
  filtered: boolean
  /** The ORDER BY carries the AYANAMSHA_SERVE_ORDER expression. */
  serveOrdered: boolean
  /** Rows a page statement (LIMIT) returned; empty for non-page statements. */
  page: FixtureRow[]
  isPage: boolean
  /** The SELECT list names ayanamsha_id (or `*`): the returned rows carry an ayanamsha. */
  selectsAyanamsha: boolean
  /** Rows returned by any non-COUNT statement (page or not). */
  rows: FixtureRow[]
}

const SERVE_EXPR = /array_position\(\s*ARRAY\[\s*'lahiri_chitrapaksha'/i

function serveIndex(id: string): number {
  const i = (AYANAMSHA_SERVE_ORDER as readonly string[]).indexOf(id)
  return i === -1 ? 99 : i
}

function paramAt(params: unknown[], n: string): unknown {
  return params[Number(n) - 1]
}

export function createFiveAyanamshaFakeDb(fixture: FixtureRow[] = buildFiveAyanamshaFixture()) {
  const statements: SimulatedStatement[] = []

  function allowedIds(sql: string, params: unknown[]): Set<string> | null {
    let allowed: Set<string> | null = null
    const add = (ids: string[]) => {
      const set = new Set(ids)
      allowed = allowed === null ? set : new Set([...allowed].filter((x) => set.has(x)))
    }
    for (const m of sql.matchAll(/ayanamsha_id\s+IN\s*\(\s*\$(\d+)\s*,\s*'INVARIANT'\s*\)/gi)) {
      add([String(paramAt(params, m[1]!)), 'INVARIANT'])
    }
    for (const m of sql.matchAll(/ayanamsha_id\s*=\s*ANY\(\s*\$(\d+)/gi)) {
      const v = paramAt(params, m[1]!)
      add(Array.isArray(v) ? v.map(String) : [String(v)])
    }
    for (const m of sql.matchAll(/ayanamsha_id\s*=\s*\$(\d+)/gi)) add([String(paramAt(params, m[1]!))])
    for (const m of sql.matchAll(/ayanamsha_id\s*=\s*'([a-z_]+)'/gi)) {
      if (m[1] !== 'tropical') add([m[1]!])
    }
    return allowed
  }

  async function query(sqlRaw: unknown, paramsRaw?: unknown): Promise<{ rows: Record<string, unknown>[]; rowCount: number }> {
    const sql = String(sqlRaw)
    const params = Array.isArray(paramsRaw) ? paramsRaw : []
    const allowed = allowedIds(sql, params)
    let rows = allowed ? fixture.filter((r) => allowed.has(r.ayanamsha_id)) : fixture.slice()
    const orderBy = /ORDER BY([\s\S]*?)(?:LIMIT|$)/i.exec(sql)?.[1] ?? ''
    const serveOrdered = SERVE_EXPR.test(orderBy)
    if (serveOrdered) {
      rows = rows.map((r, idx) => ({ r, idx })).sort((a, b) => serveIndex(a.r.ayanamsha_id) - serveIndex(b.r.ayanamsha_id) || a.idx - b.idx).map((x) => x.r)
    } else if (/ayanamsha_id/.test(orderBy)) {
      rows = rows.map((r, idx) => ({ r, idx })).sort((a, b) => (a.r.ayanamsha_id < b.r.ayanamsha_id ? -1 : a.r.ayanamsha_id > b.r.ayanamsha_id ? 1 : a.idx - b.idx)).map((x) => x.r)
    }
    const isCount = /COUNT\(\*\)/i.test(sql) && !/LIMIT/i.test(sql)
    if (isCount) {
      statements.push({ sql, params, filtered: allowed !== null, serveOrdered, page: [], isPage: false, selectsAyanamsha: false, rows: [] })
      const n = rows.length
      return { rows: [{ total: String(n), n, total_count: n, count: n }], rowCount: 1 }
    }
    const lim = /LIMIT\s+(?:\$(\d+)|(\d+))/i.exec(sql)
    const off = /OFFSET\s+(?:\$(\d+)|(\d+))/i.exec(sql)
    let isPage = false
    if (lim) {
      isPage = true
      const limit = lim[1] ? Number(paramAt(params, lim[1])) : Number(lim[2])
      const offset = off ? (off[1] ? Number(paramAt(params, off[1])) : Number(off[2])) : 0
      rows = rows.slice(Number.isFinite(offset) ? offset : 0, (Number.isFinite(offset) ? offset : 0) + (Number.isFinite(limit) ? limit : rows.length))
    }
    // Bare columns only: `array_agg(DISTINCT ayanamsha_id)` / `COUNT(DISTINCT ayanamsha_id)` are aggregates,
    // not an ayanamsha-per-row result.
    let selectList = sql.split(/\bFROM\b/i)[0] ?? ''
    for (let i = 0; i < 6; i += 1) selectList = selectList.replace(/\b\w+\s*\([^()]*\)/g, ' ')
    const selectsAyanamsha = /\bayanamsha_id\b/.test(selectList) || /SELECT\s+(?:DISTINCT\s+)?(?:\w+\.)?\*/i.test(selectList)
    statements.push({ sql, params, filtered: allowed !== null, serveOrdered, page: isPage ? rows : [], isPage, selectsAyanamsha, rows })
    return { rows: rows.map((r) => ({ ...r })), rowCount: rows.length }
  }

  return { query, statements, reset: () => { statements.length = 0 } }
}
