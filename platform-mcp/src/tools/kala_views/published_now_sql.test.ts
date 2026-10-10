/** K7-3: real published-head SQL → installed MCP public-name envelope.
 * Fixtures are TEMP tables inside a rolled-back transaction on ky_k5 only.
 */
import { execFileSync } from 'node:child_process'
import { afterEach, expect, it, vi } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import { registerKalaNowGetTool } from './now.js'
import { nowViewCapability } from '../../../../platform/src/lib/retrieval/registry/layers/L3_kala/view_now'

const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
vi.mock('../../lib/authz.js', () => ({ remoteAuthorize: async () => true }))
vi.mock('../retrieval/register_gochara_windows.js', () => ({ computeGocharaForecast: async () => ({ windows: [] }) }))
const chart = '11111111-1111-4111-8111-111111111111'
const build = '22222222-2222-4222-8222-222222222222'
const principal = { user_uid: 'CODEX-k5', key_id: 'CODEX-k5-key', role: 'guest' as const }
const at = '2026-10-09T12:00:00+05:30'

function postgres(sql: string, params: unknown[], state: string, published: boolean) {
  const lane = process.env.KY_LANE
  if (!lane || !/^k[1-8]$|^v[1-4]$/.test(lane)) throw new Error('explicit disposable lane required')
  const literal = (value: unknown) => value == null ? 'NULL' : typeof value === 'number' ? String(value)
    : `'${String(value).replaceAll("'", "''")}'`
  const fixture = `
    CREATE TEMP TABLE kala_layer_head (chart_id uuid, generation text, published_at timestamptz);
    CREATE TEMP TABLE kala_layer_candidate (chart_id uuid, generation text, build_id uuid,
      model_digest text, rule_registry_version text, conventions jsonb, state text);
    CREATE TEMP TABLE kala_layer_candidate_grain (chart_id uuid, generation text, grain_key text, result_state text);
    CREATE TEMP TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text);
    CREATE TEMP TABLE kala_darshana (id bigint, chart_id uuid, generation text, assertion_id text,
      assertion jsonb, interval_start timestamptz, interval_end timestamptz, window_start date, window_end date);
    CREATE TEMP TABLE kala_obstruction (LIKE kala_darshana);
    INSERT INTO kala_layer_head VALUES ('${chart}', 'CODEX-published', '2026-10-09T00:00:00Z');
    INSERT INTO kala_layer_candidate VALUES ('${chart}', 'CODEX-published', '${build}', 'CODEX-digest',
      'CODEX-rules', '{}', '${published ? 'published' : 'building'}');
    INSERT INTO kala_obstruction VALUES (1, '${chart}', 'CODEX-published', 'CODEX-assertion',
      jsonb_build_object('assertion_id', 'CODEX-assertion', 'operator_role', 'annotation',
        'roots', jsonb_build_object('record_ids', jsonb_build_array('CODEX-window')),
        'payload', jsonb_build_object('effective_state', ${literal(state)}, 'release',
          jsonb_build_object('kind', 'unknown', 'instant', NULL))),
      '2026-10-09T00:00:00Z', '2026-10-10T00:00:00Z', '2026-10-09', '2026-10-09');
    INSERT INTO kala_obstruction SELECT 2, chart_id, 'CODEX-private', assertion_id, assertion,
      interval_start, interval_end, window_start, window_end FROM kala_obstruction WHERE id = 1;
  `
  const output = execFileSync('docker', ['exec', '-i', 'ky-pg', 'psql', '-U', 'postgres', '-d', `ky_${lane}`,
    '-qAt', '-v', 'ON_ERROR_STOP=1'], { encoding: 'utf8', timeout: 15000,
    input: `BEGIN; ${fixture}\nPREPARE ky_view(uuid,timestamptz,timestamptz,timestamptz,text,text,int,int,text,text)
      AS ${sql}; EXECUTE ky_view(${params.map(literal).join(',')}); ROLLBACK;`,
  }).trim().split('\n').at(-1)!
  const [manifest, coverage, sources] = output.split('|').map(value => value ? JSON.parse(value) : null)
  return { rows: [{ manifest, coverage, sources }] }
}

async function installedNow(state: string, published = true) {
  db.mockReset().mockImplementation((sql, params) => postgres(sql, params, state, published))
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}'))
    if (body.uri === 'marsys://tool/L3/now_read') return { ok: true,
      json: async () => ({ ok: true, content: await nowViewCapability.handler!(body.args, {}) }) }
    return { ok: false, status: 503 }
  }))
  let call!: (args: Record<string, unknown>) => Promise<CallToolResult>
  registerKalaNowGetTool({ tool(_name: string, _description: string, shape: z.ZodRawShape,
    callback: (args: Record<string, unknown>) => Promise<CallToolResult>) {
    call = args => callback(z.object(shape).parse(args))
  } } as unknown as McpServer, principal)
  const response = await call({ chart_id: chart, as_of: '2026-10-09', at })
  return (response.structuredContent as { object: Record<string, unknown> }).object.published_now
}
afterEach(() => vi.unstubAllGlobals())

it.runIf(process.env.KALA_VIEW_DB_TESTS === '1').each(['information_unavailable', 'evaluated_silent'])
  ('stored %s survives real SQL and the actual public MCP registration', async state => {
    expect(await installedNow(state)).toMatchObject({ at, status: 'published', empty_reason: null,
      snapshot: { manifest_id: build, generation: 'CODEX-published', rows: [{ source_table: 'kala_obstruction',
        record_id: '1', data: { assertion: { roots: { record_ids: ['CODEX-window'] }, payload: {
          effective_state: state, release: { kind: 'unknown', instant: null },
        } } } }], pagination: { more_available: false } } })
  })
it.runIf(process.env.KALA_VIEW_DB_TESTS === '1')('a private candidate is unavailable through the same public boundary', async () => {
  expect(await installedNow('evaluated_silent', false))
    .toMatchObject({ status: 'information_unavailable', empty_reason: 'unpublished', snapshot: null })
})
