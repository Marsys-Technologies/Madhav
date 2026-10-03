/**
 * Pravāha B (steward M20261003T020844-29ec) — STATIC contract of migration 1243 (the two INERT Gochara asset_registry rows).
 *
 * What this proves, from the migration's own text: it inserts exactly the rows the seed defines (every column, in the seed upsert's own
 * column order), they are inert, and it contains no statement that could change anything else. The live proof against a real PostgreSQL
 * (the gap check, the idempotent re-apply, the loud failures, nothing else touched) is
 * python-sidecar/tests/test_migration_1243_inert_registry_rows.py.
 *
 * ka_gochara_v5's seed row ships with the a53 branch, not with main: until that branch is merged this tree's seed has no such row and the
 * column-by-column comparison for it is reported as SKIPPED (not passed) — it becomes live the moment the seed row lands.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { ASSETS, ASSET_REGISTRY_UPSERT_SQL, assetRegistryWriterGovernance } from '../../../scripts/seed/asset_registry_seed'

const FILE = '1243_ka_gochara_inert_registry_rows.sql'
const SQL = fs.readFileSync(path.resolve(__dirname, '../../../migrations', FILE), 'utf8')

type Cell = string | number | boolean | null | unknown[] | Record<string, unknown>

/** Strip `--` comments that are outside string literals, keeping the string literals intact. */
function stripComments(sql: string): string {
  let out = ''
  let inStr = false
  for (let i = 0; i < sql.length; i++) {
    const c = sql[i]
    if (inStr) {
      out += c
      if (c === "'") { if (sql[i + 1] === "'") { out += "'"; i++ } else inStr = false }
    } else if (c === "'") { inStr = true; out += c }
    else if (c === '-' && sql[i + 1] === '-') { while (i < sql.length && sql[i] !== '\n') i++; out += '\n' }
    else out += c
  }
  return out
}

/** Split `s` on top-level commas (outside quotes and brackets). */
function splitTop(s: string): string[] {
  const parts: string[] = []
  let depth = 0, inStr = false, cur = ''
  for (let i = 0; i < s.length; i++) {
    const c = s[i]
    if (inStr) {
      cur += c
      if (c === "'") { if (s[i + 1] === "'") { cur += "'"; i++ } else inStr = false }
      continue
    }
    if (c === "'") { inStr = true; cur += c; continue }
    if (c === '(' || c === '[') depth++
    if (c === ')' || c === ']') depth--
    if (c === ',' && depth === 0) { parts.push(cur.trim()); cur = ''; continue }
    cur += c
  }
  if (cur.trim()) parts.push(cur.trim())
  return parts
}

function parseCell(tok: string): Cell {
  if (tok === 'NULL') return null
  if (tok === 'true') return true
  if (tok === 'false') return false
  if (/^-?\d+(\.\d+)?$/.test(tok)) return Number(tok)
  if (tok === "'{}'::text[]") return []
  let m = tok.match(/^'((?:[^']|'')*)'::jsonb$/)
  if (m) return JSON.parse(m[1].replace(/''/g, "'"))
  m = tok.match(/^'((?:[^']|'')*)'$/)
  if (m) return m[1].replace(/''/g, "'")
  throw new Error(`unparsed value token: ${tok.slice(0, 80)}`)
}

const CODE = stripComments(SQL)
const columns = (() => {
  const m = CODE.match(/INSERT INTO asset_registry \(([^)]*)\)\s*VALUES/)
  if (!m) throw new Error('INSERT column list not found')
  return m[1].split(',').map(c => c.trim())
})()
const tuples = (() => {
  const m = CODE.match(/\bVALUES\s*([\s\S]*?)\s*ON CONFLICT/)
  if (!m) throw new Error('VALUES block not found')
  const body = m[1]
  const rows: Record<string, Cell>[] = []
  let depth = 0, inStr = false, start = -1
  for (let i = 0; i < body.length; i++) {
    const c = body[i]
    if (inStr) { if (c === "'") { if (body[i + 1] === "'") i++; else inStr = false } continue }
    if (c === "'") { inStr = true; continue }
    if (c === '(' || c === '[') { if (depth === 0 && c === '(') start = i + 1; depth++ }
    if (c === ')' || c === ']') { depth--; if (depth === 0 && c === ')') {
      const cells = splitTop(body.slice(start, i)).map(parseCell)
      expect(cells.length, 'cells per tuple').toBe(columns.length)
      rows.push(Object.fromEntries(columns.map((col, k) => [col, cells[k]])))
    } }
  }
  return rows
})()
const rowOf = (id: string) => tuples.find(r => r.asset_id === id)

/** The seed upsert's own INSERT column list — the migration must follow it exactly (names and order). */
const seedColumns = (() => {
  const m = ASSET_REGISTRY_UPSERT_SQL.match(/INSERT INTO asset_registry \(([\s\S]*?)\)\s*VALUES/)
  if (!m) throw new Error('seed INSERT column list not found')
  return m[1].split(',').map(c => c.trim())
})()

const LAYER_NAMES: Record<string, string> = { brahmagyan: 'Brahmagyan', ganita: 'Gaṇita', bodha: 'Bodha', kala: 'Kāla', phala: 'Phala', mimamsa: 'Mīmāṃsā' }
const LAYER_INDICES: Record<string, string> = { brahmagyan: 'L0', ganita: 'L1', bodha: 'L2', kala: 'L3', phala: 'L4', mimamsa: 'L5' }

/** The seed's main() derivation of the 28 bound parameters, as the upsert receives them (JSON columns as parsed objects). */
function seedValues(id: string): Record<string, Cell> | null {
  const a = ASSETS.find(x => x.asset_id === id)
  if (!a) return null
  const [hasWriter, hasSubsteps, timeout] = assetRegistryWriterGovernance(a)
  const v: Record<string, Cell> = {
    asset_id: a.asset_id, layer: a.layer, sort_order: a.sort_order, sanskrit_name: a.sanskrit_name, english_name: a.english_name,
    english_description: a.english_description, storage_type: a.storage_type, target_table: a.target_table, count_sql: a.count_sql,
    size_sql: a.size_sql, target_floor: a.target_floor, expected_volume_formula: a.expected_volume_formula,
    expected_volume_inputs: a.expected_volume_inputs ?? null, volume_explanation: a.volume_explanation, depends_on: a.depends_on,
    scope: a.scope, is_active: a.is_active, estimated_seconds: a.estimated_seconds,
    asset_type: a.asset_type ?? 'data', layer_name: a.layer_name ?? LAYER_NAMES[a.layer] ?? a.layer, layer_index: a.layer_index ?? LAYER_INDICES[a.layer] ?? null,
    provides_apis: a.provides_apis ?? null, health_probe: a.health_probe ?? null,
    catalog_status: a.catalog_status ?? (a.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT'), asset_kind: a.asset_kind ?? 'data',
    has_writer: hasWriter, has_substeps: hasSubsteps, writer_timeout_seconds: timeout,
  }
  return v
}

const IDS = ['ka_gochara_v4_41_candidate', 'ka_gochara_v5'] as const
const SEED_HAS_V5 = ASSETS.some(a => a.asset_id === 'ka_gochara_v5')

describe('migration 1243 — the two inert Gochara registry rows (static contract)', () => {
  it('uses the seed upsert\'s own 28-column list, in the same order', () => {
    expect(seedColumns).toHaveLength(28)
    expect(columns).toEqual(seedColumns)
  })

  it('inserts exactly the two rows, each once', () => {
    expect(tuples.map(r => r.asset_id)).toEqual([...IDS])
  })

  it('every column of ka_gochara_v4_41_candidate equals the seed entry (byte for byte, including the long text)', () => {
    const want = seedValues('ka_gochara_v4_41_candidate')
    expect(want, 'seed row for ka_gochara_v4_41_candidate').not.toBeNull()
    expect(rowOf('ka_gochara_v4_41_candidate')).toEqual(want)
  })

  // Reported as SKIPPED, not passed, on a tree whose seed has no ka_gochara_v5 row (main until the a53 branch merges).
  it.runIf(SEED_HAS_V5)('every column of ka_gochara_v5 equals the seed entry', () => {
    expect(rowOf('ka_gochara_v5')).toEqual(seedValues('ka_gochara_v5'))
  })

  it('both rows are inert planners-wise: inactive, a registered-writer row, dependency-free, no seed asset depends on them', () => {
    for (const id of IDS) {
      const r = rowOf(id)!
      expect(r.is_active, id).toBe(false)
      expect(r.has_writer, id).toBe(true)
      expect(r.depends_on, id).toEqual([])
      expect(r.scope, id).toBe('per_chart')
      expect(r.layer, id).toBe('kala')
      expect(ASSETS.filter(a => (a.depends_on ?? []).includes(id)).map(a => a.asset_id), id).toEqual([])
    }
  })

  it('is one idempotent INSERT … ON CONFLICT (asset_id) DO NOTHING and nothing that could change anything else', () => {
    expect(CODE.match(/ON CONFLICT \(asset_id\) DO NOTHING/g)).toHaveLength(1)
    expect(CODE).not.toMatch(/\bDO UPDATE\b/i)
    // The only statement is the DO block; strip string literals and look for any other verb.
    const noStrings = CODE.replace(/'(?:[^']|'')*'/g, "''")
    expect(noStrings).not.toMatch(/\b(UPDATE|DELETE|DROP|ALTER|GRANT|REVOKE|TRUNCATE|CREATE|COPY|SET\s+ROLE|COMMIT|ROLLBACK)\b/i)
    expect(noStrings.match(/\bINSERT INTO\b/gi)).toHaveLength(1)
    expect(noStrings).toMatch(/INSERT INTO asset_registry/)
  })

  it('is ROWS-ONLY: no function, no grant, no revoke, no DDL — so the routine runner role (USAGE without CREATE on public) can apply it', () => {
    const noStrings = CODE.replace(/'(?:[^']|'')*'/g, "''")
    expect(noStrings).not.toMatch(/\b(CREATE|ALTER|DROP|GRANT|REVOKE|FUNCTION|SECURITY DEFINER|TRIGGER)\b/i)
    expect(SQL).not.toMatch(/ka_gochara_staged_candidate_has_runtime_evidence/)
  })

  it('carries the three post-checks (nothing else touched, both rows exist and inert, no dependents) and raises on failure', () => {
    expect(CODE).toMatch(/xmin = pg_current_xact_id\(\)::xid/)
    expect(CODE).toMatch(/asset_id NOT IN \('ka_gochara_v4_41_candidate', 'ka_gochara_v5'\)/)
    expect(CODE).toMatch(/is_active IS FALSE/)
    expect(CODE).toMatch(/has_writer IS TRUE/)
    expect(CODE).toMatch(/depends_on && ARRAY\['ka_gochara_v4_41_candidate', 'ka_gochara_v5'\]/)
    expect(CODE.match(/RAISE EXCEPTION/g)!.length).toBeGreaterThanOrEqual(3)
  })

  it('is a routine migration: not in the protected public-schema set', async () => {
    const { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } = await import('../../../scripts/migrate')
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
  })
})
