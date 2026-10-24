/**
 * SR-K9-WRITE-SCOPE: which partition of kala_obstruction the served surfaces read.
 *  S1  the predicate is exactly the one services/kala_core/served_generation.py writes (shared literal with
 *      python-sidecar/tests/l3/kala_db/manifest/test_k9_obstruction_scope.py::SERVED_PREDICATE_O)
 *  S2  query_obstruction_periods reads ONLY that partition, for the page and for the disclosed total
 *  S3  the four kala views serve the head's obstruction rows INSTEAD of the legacy rows once the head holds some, while
 *      kala_darshana keeps serving its legacy rows beside the head (real SQL, gated by KALA_VIEW_DB_TESTS like the other
 *      real-SQL oracles)
 */
import { beforeEach, expect, it, vi } from 'vitest'
import { disposableSql } from './disposable_sql.test_support'

const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
beforeEach(() => db.mockReset())

const SERVED_PREDICATE_O = 'o.generation IS NOT DISTINCT FROM (SELECT h.generation FROM kala_layer_head h WHERE h.chart_id = o.chart_id '
  + 'AND EXISTS (SELECT 1 FROM kala_obstruction x WHERE x.chart_id = h.chart_id AND x.generation = h.generation))'

it('S1 the served-partition predicate is the one the Python twin pins', async () => {
  const { servedObstructionPredicate } = await import('./served_obstruction')
  expect(servedObstructionPredicate('o')).toBe(SERVED_PREDICATE_O)
  expect(() => servedObstructionPredicate('o; DROP TABLE x')).toThrow('plain identifier')
})

it('S2 query_obstruction_periods reads the served partition for the page and for the total', async () => {
  const { queryObstructionPeriodsCapability } = await import('./query_obstruction_periods')
  db.mockResolvedValue({ rows: [] })
  await queryObstructionPeriodsCapability.handler({ chart_id: 'chart-1', severity: 'severe' }, undefined)
  expect(db).toHaveBeenCalledTimes(2)
  for (const [sql] of db.mock.calls) {
    expect(sql).toContain(SERVED_PREDICATE_O)
    expect(sql).not.toMatch(/generation IS NULL/)
  }
})

const chart = '11111111-1111-4111-8111-111111111111'
const head = 'CODEX-head'

function viewRows(obstructionGenerations: (string | null)[], darshanaGenerations: (string | null)[], sources: ('kala_darshana' | 'kala_obstruction')[]) {
  const insert = (table: string, generations: (string | null)[]) => generations.map((generation, index) =>
    `INSERT INTO ${table} VALUES (${index + 1}, '${chart}', ${generation === null ? 'NULL' : `'${generation}'`}, 'a${index + 1}', NULL, NULL, NULL, NULL, NULL);`).join('\n')
  return import('./view_common').then(({ viewSql }) => disposableSql(`BEGIN;
    CREATE TEMP TABLE kala_layer_head (chart_id uuid, generation text, published_at timestamptz);
    CREATE TEMP TABLE kala_layer_candidate (chart_id uuid, generation text, build_id uuid, model_digest text, rule_registry_version text, conventions jsonb, state text);
    CREATE TEMP TABLE kala_layer_candidate_grain (chart_id uuid, generation text, grain_key text, result_state text);
    CREATE TEMP TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text);
    CREATE TEMP TABLE kala_darshana (id bigint, chart_id uuid, generation text, assertion_id text, assertion jsonb,
      interval_start timestamptz, interval_end timestamptz, window_start date, window_end date);
    CREATE TEMP TABLE kala_obstruction (LIKE kala_darshana);
    INSERT INTO kala_layer_head VALUES ('${chart}', '${head}', now());
    INSERT INTO kala_layer_candidate VALUES ('${chart}', '${head}', '22222222-2222-4222-8222-222222222222', 'd', 'r', '{}', 'published');
    ${insert('kala_obstruction', obstructionGenerations)}
    ${insert('kala_darshana', darshanaGenerations)}
    PREPARE ky_view(uuid,timestamptz,timestamptz,timestamptz,text,text,int,int,text,text)
      AS ${viewSql({ name: 'now', description: 'fixture', sources, required: [] })};
    EXECUTE ky_view('${chart}', NULL, NULL, NULL, NULL, NULL, 50, 0, NULL, NULL); ROLLBACK;`))
}
const idsOf = (result: Record<string, unknown>[], table: string) => {
  const sources = result[0].sources as { table: string; rows: { id: number }[] }[]
  return sources.find(source => source.table === table)!.rows.map(row => row.id).sort()
}

it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('S3 the head replaces the legacy obstruction rows; darshana still serves both', async () => {
  const both = await viewRows([null, head, 'candidate:x'], [null, head], ['kala_darshana', 'kala_obstruction'])
  expect(idsOf(both, 'kala_obstruction')).toEqual([2])
  expect(idsOf(both, 'kala_darshana')).toEqual([1, 2])
})

it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('S3 a head with no obstruction rows leaves the legacy rows served', async () => {
  const legacyOnly = await viewRows([null, null, 'candidate:x'], [null, head], ['kala_obstruction'])
  expect(idsOf(legacyOnly, 'kala_obstruction')).toEqual([1, 2])
})
