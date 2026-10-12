import { beforeEach, expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
import { queryLifeArcCapability } from './query_life_arc'
import { storyViewCapability } from './view_story'
const chart = '11111111-1111-4111-8111-111111111111'
const parva = { id: 1, parva_index: 1, chart_id: chart, dasha_planet: 'Mercury',
  start_year: 2020, end_year: 2027, parva_quality: 'building', theme_keywords: ['career'],
  high_convergence_count: 8838, avg_effective_score: 0.91,
  narrative: { summary: '8838 high-convergence windows.', high_convergence_count: 8838, avg_effective_score: 0.91, quality: 'building' },
  source_citation: 'CODEX:MD=Mercury', computed_at: '2026-08-13T00:00:00Z' }
beforeEach(() => { db.mockReset() })
it('legacy STORY source nulls stale figures and stored prose before narration', async () => {
  db.mockResolvedValue({ rows: [{ ...parva, convergence_source_available: false }] })
  const result = await queryLifeArcCapability.handler!({ chart_id: chart }, {})
  expect(result.content).toMatchObject({ parvas: [{ high_convergence_count: null, avg_effective_score: null,
    convergence_null_reason: 'source_table_empty_for_chart', narrative: { summary: null,
      high_convergence_count: null, avg_effective_score: null, convergence_null_reason: 'source_table_empty_for_chart' } }] })
})
it('published STORY uses the same empty-source qualification', async () => {
  db.mockResolvedValue({ rows: [{ manifest: { manifest_id: 'build', generation: '4.1' }, coverage: [],
    sources: [{ table: 'kala_jivana_parva', total: 1, rows: [{ ...parva, convergence_source_available: false }] }] }] })
  const result = await storyViewCapability.handler!({ chart_id: chart }, {})
  expect(result.content).toMatchObject({ rows: [{ data: { high_convergence_count: null,
    avg_effective_score: null, convergence_null_reason: 'source_table_empty_for_chart', narrative: { summary: null } } }] })
})
it('measured nonempty source preserves recorded figures', async () => {
  db.mockResolvedValue({ rows: [{ ...parva, convergence_source_available: true }] })
  const result = await queryLifeArcCapability.handler!({ chart_id: chart }, {})
  expect(result.content).toMatchObject({ parvas: [{ high_convergence_count: 8838, avg_effective_score: 0.91, narrative: parva.narrative }] })
})
it('a missing detector never promotes populated-looking figures', async () => {
  db.mockResolvedValue({ rows: [parva] })
  const result = await queryLifeArcCapability.handler!({ chart_id: chart }, {})
  expect(result.content).toMatchObject({ parvas: [{ high_convergence_count: null, avg_effective_score: null,
    convergence_null_reason: 'source_availability_unverified' }] })
})

// TEMP fixtures only; execute the actual legacy reader SQL in the caller lane DB.
async function postgres(sql: string, params: unknown[], nonempty: boolean) {
  const { execFileSync } = await import('node:child_process')
  const lane = process.env.KY_LANE
  if (!lane || !/^k[1-8]$/.test(lane)) throw new Error('explicit builder lane required')
  const literal = (v: unknown) => v == null ? 'NULL' : typeof v === 'number' ? String(v) : `'${String(v).replaceAll("'", "''")}'`
  const schema = `
    CREATE TEMP TABLE kala_jivana_parva (id int, chart_id uuid, parva_index int, dasha_planet text, dominant_signal_class text,
      start_year int, end_year int, parva_quality text, theme_keywords text[], high_convergence_count int, avg_effective_score numeric,
      narrative jsonb, source_citation text, computed_at timestamptz);
    CREATE TEMP TABLE kala_convergence (chart_id uuid);
    INSERT INTO kala_jivana_parva VALUES (1, '${chart}', 1, 'Mercury', NULL, 2020, 2027, 'building', '{career}', 8838, 0.91,
      '{"summary":"8838 windows","high_convergence_count":8838,"avg_effective_score":0.91}', 'CODEX:MD=Mercury', '2026-08-13');
    INSERT INTO kala_convergence VALUES ('22222222-2222-4222-8222-222222222222');
    ${nonempty ? `INSERT INTO kala_convergence VALUES ('${chart}');` : ''}
  `
  const output = execFileSync('docker', ['exec', '-i', 'ky-pg', 'psql', '-U', 'postgres', '-d', `ky_${lane}`, '-qAt', '-v', 'ON_ERROR_STOP=1'], {
    input: `BEGIN; ${schema} PREPARE story(uuid,int,int) AS ${sql}; EXECUTE story(${params.map(literal).join(',')}); ROLLBACK;`,
    encoding: 'utf8', timeout: 15000,
  }).trim().split('\n').at(-1)!
  const values = output.split('|')
  return { rows: [{ ...parva, high_convergence_count: Number(values[8]), avg_effective_score: Number(values[9]),
    narrative: JSON.parse(values[10]), convergence_source_available: values.at(-1) === 't' }] }
}
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each([false, true])('actual SQL scopes source availability to the chart (nonempty=%s)', async nonempty => {
  db.mockImplementation((sql, params) => postgres(sql, params, nonempty))
  const result = await queryLifeArcCapability.handler!({ chart_id: chart }, {})
  expect(result).toMatchObject({ is_error: false, content: { parvas: [{
    high_convergence_count: nonempty ? 8838 : null, avg_effective_score: nonempty ? 0.91 : null,
    ...(nonempty ? {} : { convergence_null_reason: 'source_table_empty_for_chart' }),
  }] } })
})
