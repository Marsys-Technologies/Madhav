/**
 * dashas_fake_db.ts — a tiny disposable SQL SIMULATOR for the get_dashas contract tests.
 *
 * No database. It answers the statements get_dashas issues (receipt + replacement fence + page in ONE
 * statement, the served-depth probe `SELECT MAX(level_n)`, the served-generation receipt probe, the
 * dignity/shadbala re-derivation read) over a fixture of `chart_dashas` rows that holds three systems
 * (vimshottari, vimshottari_kp, yogini) at ALL FIVE ayanamshas:
 *
 *   - ayanamsha predicate: `d.ayanamsha_id = $n` (alias optional);
 *   - system predicate:    `d.system_id = $n`;
 *   - the SS N-368 two-leg KP-system predicate (`pushMixedKpSystemAyanamshaFilter`):
 *       AND ((d.system_id = 'vimshottari_kp' AND d.ayanamsha_id = 'krishnamurti')
 *            OR (d.system_id IS DISTINCT FROM 'vimshottari_kp' [AND d.ayanamsha_id = $n]))
 *     evaluated PER ROW;
 *   - ordering: system_id, AYANAMSHA_SERVE_ORDER (Lahiri first), start_date, level_n, start_iso, dasha_row_id;
 *   - `LIMIT $2 OFFSET $3`.
 *
 * Temporal and level facets are not simulated (every fixture row satisfies the default facets).
 * It is a model of the SQL contract, not of Postgres.
 */
import { AYANAMSHA_SERVE_ORDER } from '../../constants'

export const DASHA_FIXTURE_AYANAMSHAS = [
  'krishnamurti', 'true_chitra', 'raman', 'surya_siddhanta_classical', 'lahiri_chitrapaksha',
] as const
export const DASHA_FIXTURE_SYSTEMS = ['vimshottari', 'vimshottari_kp', 'yogini'] as const
export const DASHA_ROWS_PER_GROUP = 4

export interface DashaFixtureRow extends Record<string, unknown> {
  dasha_row_id: string
  ayanamsha_id: string
  system_id: string
  level_n: number
  start_date: string
}

export function buildDashaFixture(): DashaFixtureRow[] {
  const rows: DashaFixtureRow[] = []
  for (const ayanamsha_id of DASHA_FIXTURE_AYANAMSHAS) {
    for (const system_id of DASHA_FIXTURE_SYSTEMS) {
      for (let i = 0; i < DASHA_ROWS_PER_GROUP; i += 1) {
        rows.push({
          dasha_row_id: `${ayanamsha_id}|${system_id}|${i}`,
          chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
          build_id: '00000000-0000-4000-8000-00000000000a',
          ayanamsha_id,
          system_id,
          level_n: 1 + (i % 2),
          parent_row_id: null,
          lord_graha: 'Moon',
          lord_sign: 'Taurus',
          start_date: `2020-0${i + 1}-01`,
          end_date: `2020-0${i + 1}-28`,
          start_iso: `2020-0${i + 1}-01T00:00:00Z`,
          sandhi_flag: false,
          verification_pass_status: 'single',
          citation_ref: `ref-${ayanamsha_id}-${system_id}-${i}`,
        })
      }
    }
  }
  return rows
}

const TWO_LEG =
  /AND \(\((?:\w+\.)?system_id = '([a-z_]+)' AND (?:\w+\.)?ayanamsha_id = '([a-z_]+)'\) OR \((?:\w+\.)?system_id IS DISTINCT FROM '\1'(?: AND (?:\w+\.)?ayanamsha_id = \$(\d+))?\)\)/

export interface DashaStatement {
  kind: 'page' | 'levels'
  sql: string
  params: unknown[]
  /** Rows the statement selected (page: the LIMIT window; levels: the filtered set). */
  rows: DashaFixtureRow[]
}

function serveIndex(id: string): number {
  const i = (AYANAMSHA_SERVE_ORDER as readonly string[]).indexOf(id)
  return i === -1 ? 99 : i
}

export function createDashasFakeDb(fixture: DashaFixtureRow[] = buildDashaFixture(), opts: { replacement?: boolean } = {}) {
  const statements: DashaStatement[] = []
  let replacement = opts.replacement === true

  function filter(sqlIn: string, params: unknown[]): DashaFixtureRow[] {
    let sql = sqlIn
    let rows = fixture.slice()
    const leg = TWO_LEG.exec(sql)
    if (leg) {
      const kpSystem = leg[1]!
      const kpAya = leg[2]!
      const other = leg[3] ? String(params[Number(leg[3]) - 1]) : null
      rows = rows.filter((r) => (r.system_id === kpSystem ? r.ayanamsha_id === kpAya : other === null || r.ayanamsha_id === other))
      sql = sql.replace(TWO_LEG, ' ')
    }
    for (const m of sql.matchAll(/(?:\bd\.|\s)ayanamsha_id = \$(\d+)/g)) {
      const v = String(params[Number(m[1]) - 1])
      rows = rows.filter((r) => r.ayanamsha_id === v)
    }
    for (const m of sql.matchAll(/(?:\bd\.|\s)system_id = \$(\d+)/g)) {
      const v = String(params[Number(m[1]) - 1])
      rows = rows.filter((r) => r.system_id === v)
    }
    return rows
  }

  async function query(sqlRaw: unknown, paramsRaw?: unknown): Promise<{ rows: Record<string, unknown>[]; rowCount: number }> {
    const sql = String(sqlRaw).replace(/\s+/g, ' ')
    const params = Array.isArray(paramsRaw) ? paramsRaw : []
    if (sql.includes('replacement_fence AS')) {
      // The page statement: WHERE is the part after `WHERE d.chart_id`, before ORDER BY.
      const where = /WHERE (d\.chart_id[\s\S]*?) ORDER BY/.exec(sql)?.[1] ?? ''
      let rows = filter(where, params)
      rows = rows.slice().sort((a, b) =>
        a.system_id.localeCompare(b.system_id)
        || serveIndex(a.ayanamsha_id) - serveIndex(b.ayanamsha_id)
        || a.start_date.localeCompare(b.start_date)
        || a.level_n - b.level_n
        || String(a.start_iso).localeCompare(String(b.start_iso))
        || a.dasha_row_id.localeCompare(b.dasha_row_id))
      const limit = Number(params[1])
      const offset = Number(params[2])
      const page = rows.slice(offset, offset + limit)
      statements.push({ kind: 'page', sql: String(sqlRaw), params, rows: page })
      return {
        rows: [{ replacement_in_progress: replacement, eligible_build_id: 'build-a', rows: page.map((r) => ({ ...r })) }],
        rowCount: 1,
      }
    }
    if (sql.startsWith('SELECT MAX(level_n)')) {
      const where = /FROM chart_dashas WHERE ([\s\S]*)$/.exec(sql)?.[1] ?? ''
      const rows = filter(where, params)
      statements.push({ kind: 'levels', sql: String(sqlRaw), params, rows })
      return { rows: [{ max_level: rows.length ? Math.max(...rows.map((r) => r.level_n)) : null }], rowCount: 1 }
    }
    if (sql.includes('FROM asset_provenance_receipts receipt') && sql.includes('AS rows_build_id')) {
      return {
        rows: [{
          asset_id: 'ga_vargas', partition_key: '__whole_asset__', receipt_version: 'v1',
          receipt_build_id: 'build-vargas', rows_build_id: 'build-vargas', receipt_state: 'proven',
          freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
          receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build',
          observed_at: '2026-09-07T00:00:00Z',
        }],
        rowCount: 1,
      }
    }
    return { rows: [], rowCount: 0 }
  }

  return {
    query,
    statements,
    pages: () => statements.filter((s) => s.kind === 'page'),
    levelQueries: () => statements.filter((s) => s.kind === 'levels'),
    reset: () => { statements.length = 0; replacement = opts.replacement === true },
    setReplacement: (on: boolean) => { replacement = on },
  }
}

export function installSigningKey(): () => void {
  const prev = { kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID, key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT }
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
  process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
  return () => {
    if (prev.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = prev.kid
    if (prev.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = prev.key
  }
}
