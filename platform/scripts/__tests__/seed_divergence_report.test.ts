/**
 * Seed divergence-report + NULL-fill-gate tests
 * (Nirmāṇa WORK_QUEUE M0-T35; implements rulings D-27 §2(a)/§2(b) and D-28 §1).
 *
 * THE TWO DEFECTS THESE TESTS EXIST TO CATCH.
 *
 *   1. `target_floor = EXCLUDED.target_floor` in the seeder's `ON CONFLICT DO UPDATE SET`.
 *      `target_floor` is a MEASURED field — I7 sets a floor to the measured achieved count —
 *      and a declarative source file structurally cannot hold a measured value. So every seed
 *      run silently reverted every rung's Conform-stage measurement, with exit 0 (D-19; D-27
 *      §2(a)). 27 cells diverge today.
 *
 *   2. The upsert resolved every other divergence by execution order. Whoever ran last won,
 *      silently. For `count_sql` and `depends_on` — DECLARED-BUT-VERIFIABLE, legitimately
 *      authored in source AND checkable against reality — that is not an answer, it is the
 *      absence of one (D-27 §2(b)). And for a live NULL it is worse than a wrong answer: a NULL
 *      can be an UNDECIDED QUESTION written down, and a `??` default answers it invisibly,
 *      producing a row indistinguishable from a correctly-derived one that no later detector
 *      can find (D-28 §1).
 *
 * WHY THE FILE IS READ AS TEXT. Ruling D-13 standing-instructs every agent not to import from
 * `asset_registry_seed.ts` — it exports `ASSETS` and its `main()` runs `INSERT INTO
 * asset_registry … ON CONFLICT DO UPDATE` against the control-plane table this campaign is
 * auditing. D-13's own words: "read it, or parse it, or copy what you need". So the claims about
 * that FILE are asserted against its bytes, and the claims about the MACHINERY are asserted
 * against `seed_divergence_report.ts`, which is pure — no `pg`, no `main()`, no import-time side
 * effect — and may be imported freely.
 *
 * Nothing in this file connects to a database, and no test here can cause the seeder to run.
 *
 * NOTE ON WHAT "PASSES" MEANS HERE. The seeder cannot complete a run today: `validateFormulas()`
 * aborts on `bg_cohort`'s `COHORT_SIZE` (a pre-existing, unrelated R0 defect, deliberately not
 * fixed — I13), and D-17's DRY_RUN refusal fires before that. So no test can observe a live seed
 * run, and none pretends to. The gate's behaviour is proven on fixtures; the file's shape is
 * proven on its bytes.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import {
  buildDivergenceReport,
  cellToken,
  classifyCell,
  DECLARED_BUT_VERIFIABLE_COLUMNS,
  deriveSeedRow,
  enforceNullFillGate,
  formatDivergenceReport,
  GUARDED_COLUMNS,
  NULL_FILL_ACK_ENV,
  NullFillGateError,
  nullFillCells,
  onConflictUpdatedColumns,
  parseNullFillAcknowledgement,
  type SeedAssetLike,
  type SeedRow,
} from '../seed/seed_divergence_report'

const SEED_PATH = path.resolve(__dirname, '../seed/asset_registry_seed.ts')
const SEED_SRC = fs.readFileSync(SEED_PATH, 'utf8')

/**
 * The registry upsert STATEMENT alone, not the whole file.
 *
 * Feeding `onConflictUpdatedColumns` an entire source file happens to work here, but only
 * accidentally — the parser would otherwise run on into the `asset_coefficients` upsert further
 * down (it does exactly that against a pre-M0-T35 seeder, returning 26 columns rather than 22).
 * Slicing the hoisted `ASSET_UPSERT_SQL` constant makes the tests read the one statement the
 * seeder actually parses at runtime.
 *
 * Falls back to the whole file when the constant is absent, which is the pre-M0-T35 shape — so
 * these tests still produce a meaningful failure against HEAD rather than an unrelated crash.
 */
function seedUpsertStatement(): string {
  const tok = 'const ASSET_UPSERT_SQL = `'
  const i = SEED_SRC.indexOf(tok)
  if (i < 0) return SEED_SRC
  const rest = SEED_SRC.slice(i + tok.length)
  const end = rest.indexOf('`')
  return end < 0 ? SEED_SRC : rest.slice(0, end)
}

/** The `ON CONFLICT … DO UPDATE SET` body of the real seeder, as text. */
function seedSetClauseBody(): string {
  const stmt = seedUpsertStatement()
  const m = /ON\s+CONFLICT\s*\([^)]*\)\s*DO\s+UPDATE\s+SET/i.exec(stmt)
  expect(m, 'seeder must contain an ON CONFLICT … DO UPDATE SET').not.toBeNull()
  return stmt.slice(m!.index + m![0].length)
}

// ─────────────────────────────────────────────────────────────────────────────
// DELIVERABLE 1 — target_floor must stop being silently overwritten
// ─────────────────────────────────────────────────────────────────────────────

describe('D-27 §2(a) — target_floor is a MEASURED field the seed must not overwrite', () => {
  it('does not assign target_floor in the ON CONFLICT DO UPDATE SET body', () => {
    const body = seedSetClauseBody()
    // Comments are the one place the name is allowed to appear — the removal has to explain
    // itself or the next reader will "restore" it. Assert on ASSIGNMENTS, not on the word.
    const uncommented = body
      .split('\n')
      .map(l => (l.indexOf('--') < 0 ? l : l.slice(0, l.indexOf('--'))))
      .join('\n')
    expect(uncommented).not.toMatch(/\btarget_floor\s*=/)
  })

  it('the parsed updated-column list has no target_floor', () => {
    const columns = onConflictUpdatedColumns(seedUpsertStatement()).map(c => c.column)
    expect(columns).not.toContain('target_floor')
    // Sanity: the parser did find the other columns, so the assertion above is not vacuous.
    expect(columns).toContain('count_sql')
    expect(columns).toContain('depends_on')
    expect(columns.length).toBeGreaterThan(15)
  })

  it('still INSERTs target_floor — a new row has no measurement to collide with', () => {
    const m = /INSERT\s+INTO\s+asset_registry\s*\(([^)]*)\)/i.exec(SEED_SRC)
    expect(m).not.toBeNull()
    expect(m![1]).toMatch(/\btarget_floor\b/)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// DELIVERABLE 2 — the divergence report and the NULL→value gate
// ─────────────────────────────────────────────────────────────────────────────

describe('the seeder computes the report and enforces the gate BEFORE it writes', () => {
  it('calls buildDivergenceReport and enforceNullFillGate before the upsert loop', () => {
    const report = SEED_SRC.indexOf('buildDivergenceReport(')
    const gate = SEED_SRC.indexOf('enforceNullFillGate(')
    const write = SEED_SRC.indexOf("console.log('Seeding asset_registry...')")
    expect(report, 'seeder must build a divergence report').toBeGreaterThan(0)
    expect(gate, 'seeder must enforce the NULL-fill gate').toBeGreaterThan(0)
    expect(write).toBeGreaterThan(0)
    expect(report).toBeLessThan(write)
    expect(gate).toBeLessThan(write)
  })

  it('derives the report\'s column coverage from the upsert SQL, not a parallel list', () => {
    expect(SEED_SRC).toMatch(/onConflictUpdatedColumns\(\s*ASSET_UPSERT_SQL\s*\)/)
    // and the statement executed is the same constant that was parsed
    expect(SEED_SRC).toMatch(/client\.query\(\s*\n?\s*ASSET_UPSERT_SQL,/)
  })

  it('binds the upsert from the same derived rows the report was built from', () => {
    // deriveSeedRow() must be the only place the `??` defaults live: no second copy of the
    // derivation may survive in the seeder's write path (CLAUDE.md §N.7 item 3).
    expect(SEED_SRC).toMatch(/deriveSeedRow\(asset\)/)
    expect(SEED_SRC).not.toMatch(/const\s+assetKind\s*=\s*asset\.asset_kind\s*\?\?/)
    expect(SEED_SRC).not.toMatch(/const\s+assetType\s*=\s*asset\.asset_type\s*\?\?/)
  })
})

describe('onConflictUpdatedColumns — parsed from the statement, comments and CASE handled', () => {
  const SQL = [
    'INSERT INTO t (a,b) VALUES ($1,$2) ON CONFLICT (a) DO UPDATE SET',
    '  b = EXCLUDED.b,',
    "  -- a comment, with a comma and an x = y inside it",
    "  c = CASE WHEN t.s = 'RETIRED' THEN t.c ELSE EXCLUDED.c END,",
    '  d = coalesce(EXCLUDED.d, t.d)',
  ].join('\n')

  it('returns every assigned column and nothing from the comment prose', () => {
    expect(onConflictUpdatedColumns(SQL).map(c => c.column)).toEqual(['b', 'c', 'd'])
  })

  it('marks CASE assignments guarded and bare ones unguarded', () => {
    const byCol = new Map(onConflictUpdatedColumns(SQL).map(c => [c.column, c.guarded]))
    expect(byCol.get('b')).toBe(false)
    expect(byCol.get('c')).toBe(true)
    expect(byCol.get('d')).toBe(false)  // a function call is not a guard
  })

  it('throws rather than silently returning [] when there is no ON CONFLICT clause', () => {
    expect(() => onConflictUpdatedColumns('SELECT 1')).toThrow(/ON CONFLICT/)
  })

  it('every CASE-guarded column in the REAL seeder has a model in GUARDED_COLUMNS', () => {
    // Neither list may be the sole authority: the SQL and the model must agree in both
    // directions, or the report describes a write the statement will not make.
    const guardedInSql = onConflictUpdatedColumns(seedUpsertStatement())
      .filter(c => c.guarded)
      .map(c => c.column)
      .sort()
    expect(guardedInSql).toEqual(Object.keys(GUARDED_COLUMNS).sort())
  })
})

describe('classifyCell — D-28 §1: NULL→value is its own category', () => {
  it('separates the four outcomes', () => {
    expect(classifyCell(null, null)).toBe('unchanged')
    expect(classifyCell('x', 'x')).toBe('unchanged')
    expect(classifyCell(null, 'L5')).toBe('null_to_value')
    expect(classifyCell('L5', null)).toBe('value_to_null')
    expect(classifyCell('L4', 'L5')).toBe('value_change')
  })

  it('does NOT treat a NULL fill as an ordinary value change', () => {
    expect(classifyCell(null, 'Mīmāṃsā')).not.toBe('value_change')
  })

  it('treats empty string, 0, false and [] as VALUES, not absences', () => {
    // asset_registry.depends_on defaults to ARRAY[]::text[] — an empty dependency list is a
    // declared "no dependencies", and must not trip the gate.
    expect(classifyCell([], ['a'])).toBe('value_change')
    expect(classifyCell(0, 5)).toBe('value_change')
    expect(classifyCell('', 'x')).toBe('value_change')
    expect(classifyCell(false, true)).toBe('value_change')
  })

  it('compares arrays and jsonb structurally, and ignores jsonb key order', () => {
    expect(classifyCell(['a', 'b'], ['a', 'b'])).toBe('unchanged')
    expect(classifyCell(['a', 'b'], ['b', 'a'])).toBe('value_change')  // DAG order is meaningful
    expect(classifyCell({ x: 1, y: 2 }, { y: 2, x: 1 })).toBe('unchanged')
    expect(classifyCell({ x: 1 }, { x: 2 })).toBe('value_change')
  })
})

// ── Fixtures ─────────────────────────────────────────────────────────────────

function asset(over: Partial<SeedAssetLike> & { asset_id: string }): SeedAssetLike {
  return {
    layer: 'mimamsa',
    sort_order: 1,
    sanskrit_name: 's',
    english_name: 'e',
    english_description: 'd',
    storage_type: 'postgres_table',
    target_table: 't',
    count_sql: 'SELECT 1',
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: null,
    depends_on: [],
    scope: 'global',
    is_active: true,
    estimated_seconds: null,
    ...over,
  }
}

function live(over: Record<string, unknown> & { asset_id: string }): SeedRow {
  return {
    layer: 'mimamsa',
    sort_order: 1,
    sanskrit_name: 's',
    english_name: 'e',
    english_description: 'd',
    storage_type: 'postgres_table',
    target_table: 't',
    count_sql: 'SELECT 1',
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: null,
    depends_on: [],
    scope: 'global',
    is_active: true,
    estimated_seconds: null,
    asset_type: 'data',
    layer_name: 'Mīmāṃsā',
    layer_index: 'L5',
    provides_apis: null,
    health_probe: null,
    catalog_status: 'DRAFT',
    asset_kind: 'data',
    ...over,
  }
}

const REAL_COLUMNS = onConflictUpdatedColumns(seedUpsertStatement())

function reportFor(assets: SeedAssetLike[], liveRows: SeedRow[], defaulted?: Set<string>) {
  return buildDivergenceReport({
    liveRows: new Map(liveRows.map(r => [r.asset_id as string, r])),
    seedRows: new Map(assets.map(a => [a.asset_id, deriveSeedRow(a)])),
    columns: REAL_COLUMNS,
    defaultedKeys: defaulted,
  })
}

describe('deriveSeedRow — the ?? default is an ACTIVE WRITE (D-27 §3(a))', () => {
  it('writes asset_kind/asset_type = data when the key is simply absent', () => {
    const row = deriveSeedRow(asset({ asset_id: 'x' }))
    expect(row.asset_kind).toBe('data')
    expect(row.asset_type).toBe('data')
  })

  it('so an omitted key reverts a live service row — the 8-row finding', () => {
    const r = reportFor(
      [asset({ asset_id: 'svc' })],
      [live({ asset_id: 'svc', asset_kind: 'service', asset_type: 'service' })],
    )
    const cols = r.cells.map(c => c.column).sort()
    expect(cols).toEqual(['asset_kind', 'asset_type'])
    expect(r.cells.every(c => c.category === 'value_change')).toBe(true)
    expect(r.cells.every(c => c.seed === 'data')).toBe(true)
  })

  it('derives layer_name/layer_index from §N.1\'s locked lexicon, diacritics intact', () => {
    expect(deriveSeedRow(asset({ asset_id: 'x', layer: 'ganita' })).layer_name).toBe('Gaṇita')
    expect(deriveSeedRow(asset({ asset_id: 'x', layer: 'kala' })).layer_name).toBe('Kāla')
    expect(deriveSeedRow(asset({ asset_id: 'x', layer: 'mimamsa' })).layer_index).toBe('L5')
  })
})

describe('buildDivergenceReport', () => {
  it('classifies a deliberately-held NULL as null_to_value, not value_change', () => {
    // The general shape, with no asset named: a live NULL the seed would fill from a default.
    const r = reportFor(
      [asset({ asset_id: 'held' })],
      [live({ asset_id: 'held', layer_index: null, layer_name: null })],
    )
    const fills = nullFillCells(r)
    expect(fills.map(c => c.column).sort()).toEqual(['layer_index', 'layer_name'])
    expect(fills.every(c => c.category === 'null_to_value')).toBe(true)
    expect(r.counts.null_to_value).toBe(2)
    expect(r.counts.value_change).toBe(0)
  })

  it('flags the DECLARED-BUT-VERIFIABLE columns D-27 §2(b) names', () => {
    const r = reportFor(
      [asset({ asset_id: 'v', count_sql: 'SELECT 2', depends_on: ['a'] })],
      [live({ asset_id: 'v', count_sql: 'SELECT 1', depends_on: ['b'] })],
    )
    const verifiable = r.cells.filter(c => c.verifiable).map(c => c.column).sort()
    expect(verifiable).toEqual([...DECLARED_BUT_VERIFIABLE_COLUMNS].sort())
  })

  it('does not report target_floor at all — it is no longer in the SET clause', () => {
    const r = reportFor(
      [asset({ asset_id: 'f', target_floor: 999 })],
      [live({ asset_id: 'f', target_floor: 12345 })],
    )
    expect(r.cells.map(c => c.column)).not.toContain('target_floor')
  })

  it('honours the MR-06 RETIRED guard rather than announcing a write it will not make', () => {
    const r = reportFor(
      [asset({ asset_id: 'r', catalog_status: 'CURRENT', is_active: true })],
      [live({ asset_id: 'r', catalog_status: 'RETIRED', is_active: false })],
    )
    expect(r.cells.map(c => c.column)).not.toContain('catalog_status')
    expect(r.cells.map(c => c.column)).not.toContain('is_active')
  })

  it('and still reports the guarded columns when the live row is NOT retired', () => {
    // The other branch — the one D-28 §4 records has never been exercised in production.
    const r = reportFor(
      [asset({ asset_id: 'r', catalog_status: 'CURRENT' })],
      [live({ asset_id: 'r', catalog_status: 'DRAFT' })],
    )
    expect(r.cells.map(c => c.column)).toContain('catalog_status')
  })

  it('reports an asset with no live row as a NEW ROW, not as a NULL fill', () => {
    const r = reportFor([asset({ asset_id: 'brand_new' })], [])
    expect(r.newAssetIds).toEqual(['brand_new'])
    expect(r.counts.null_to_value).toBe(0)
    expect(r.cells).toHaveLength(0)
  })

  it('refuses to model a CASE-guarded column it has no guard for', () => {
    expect(() =>
      buildDivergenceReport({
        liveRows: new Map([['x', live({ asset_id: 'x' })]]),
        seedRows: new Map([['x', deriveSeedRow(asset({ asset_id: 'x' }))]]),
        columns: [{ column: 'scope', guarded: true }],
      }),
    ).toThrow(/CASE-guarded in the SQL but has no model/)
  })
})

describe('the NULL→value gate — a real gate, not a printed warning (D-28 §1)', () => {
  const heldNull = () =>
    reportFor(
      [asset({ asset_id: 'held' })],
      [live({ asset_id: 'held', layer_index: null, layer_name: null })],
    )

  it('BLOCKS the run when a NULL fill is unacknowledged', () => {
    expect(() => enforceNullFillGate(heldNull(), new Set())).toThrow(NullFillGateError)
    expect(() => enforceNullFillGate(heldNull(), new Set())).toThrow(/REFUSING TO SEED/)
  })

  it('names every unacknowledged cell and says nothing was written', () => {
    try {
      enforceNullFillGate(heldNull(), new Set())
      throw new Error('gate did not fire')
    } catch (e) {
      const err = e as NullFillGateError
      expect(err).toBeInstanceOf(NullFillGateError)
      expect(err.unacknowledged.sort()).toEqual(['held.layer_index', 'held.layer_name'])
      expect(err.message).toMatch(/NOTHING HAS BEEN WRITTEN/)
      expect(err.message).toContain(NULL_FILL_ACK_ENV)
    }
  })

  it('a PARTIAL acknowledgement still blocks — per cell, not per run', () => {
    expect(() => enforceNullFillGate(heldNull(), new Set(['held.layer_index'])))
      .toThrow(/REFUSING TO SEED/)
  })

  it('passes only when every cell is named explicitly', () => {
    const ack = new Set(['held.layer_index', 'held.layer_name'])
    expect(enforceNullFillGate(heldNull(), ack).sort())
      .toEqual(['held.layer_index', 'held.layer_name'])
  })

  it('rejects a STALE acknowledgement that matches nothing in this report', () => {
    // How a decision made about one report authorises a fill in a later one nobody read.
    const ack = new Set(['held.layer_index', 'held.layer_name', 'gone.layer_index'])
    try {
      enforceNullFillGate(heldNull(), ack)
      throw new Error('gate did not fire')
    } catch (e) {
      const err = e as NullFillGateError
      expect(err.stale).toEqual(['gone.layer_index'])
      expect(err.message).toMatch(/match NOTHING in this report/)
    }
  })

  it('is a no-op when there are no NULL fills — it does not block ordinary runs', () => {
    const r = reportFor(
      [asset({ asset_id: 'v', count_sql: 'SELECT 2' })],
      [live({ asset_id: 'v', count_sql: 'SELECT 1' })],
    )
    expect(r.counts.value_change).toBeGreaterThan(0)
    expect(enforceNullFillGate(r, new Set())).toEqual([])
  })

  it('has no per-asset special case anywhere in the mechanism (D-25 §2(c), D-28 §1)', () => {
    const mechanism = fs.readFileSync(
      path.resolve(__dirname, '../seed/seed_divergence_report.ts'), 'utf8',
    )
    // Comments may DISCUSS the case that exposed the shape; no code path may test for it.
    const code = mechanism
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .split('\n')
      .map(l => (l.indexOf('//') < 0 ? l : l.slice(0, l.indexOf('//'))))
      .join('\n')
    expect(code).not.toMatch(/lel_events/)
    expect(code).not.toMatch(/mi_jivanaghatana/)
    expect(code).not.toMatch(/bg_sky_calendar/)
  })
})

describe('parseNullFillAcknowledgement', () => {
  it('is empty when the variable is unset or blank', () => {
    expect(parseNullFillAcknowledgement({}).size).toBe(0)
    expect(parseNullFillAcknowledgement({ [NULL_FILL_ACK_ENV]: '' }).size).toBe(0)
  })

  it('accepts whitespace- or comma-separated tokens', () => {
    expect([...parseNullFillAcknowledgement({ [NULL_FILL_ACK_ENV]: 'a.b, c.d\ne.f' })].sort())
      .toEqual(['a.b', 'c.d', 'e.f'])
  })
})

describe('formatDivergenceReport', () => {
  it('shows the NULL→value count separately from the value→value count', () => {
    const r = reportFor(
      [asset({ asset_id: 'held', count_sql: 'SELECT 2' })],
      [live({ asset_id: 'held', layer_index: null, count_sql: 'SELECT 1' })],
    )
    const text = formatDivergenceReport(r)
    expect(text).toMatch(/NULL → value\s*:\s*1/)
    expect(text).toMatch(/value → value\s*:\s*1/)
    expect(text).toContain(cellToken('held', 'layer_index'))
    expect(text).toMatch(/DECLARED-BUT-VERIFIABLE/)
  })

  it('marks a cell whose key was never declared as coming from a ?? default', () => {
    const r = reportFor(
      [asset({ asset_id: 'held' })],
      [live({ asset_id: 'held', layer_index: null })],
      new Set([cellToken('held', 'layer_index')]),
    )
    expect(formatDivergenceReport(r)).toMatch(/from a \?\? default/)
  })
})
