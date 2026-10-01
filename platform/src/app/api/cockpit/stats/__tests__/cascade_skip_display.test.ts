/**
 * Suvarna Track I-3 (display side) — a cascade-skipped consumer must read as
 * "blocked by upstream", never as the asset's own red `error`.
 *
 * Canonical case (mi_bhavisya, chart 482012f1): asset_throughput.state='error' with a
 * 'BLOCKED: upstream dependency(ies) ph_phaladesa, ph_pramana did not complete ...'
 * last_error (written by the FROZEN runner's _mark_asset_blocked), while its
 * build_run_assets row carries disposition='blocked_dependency'. The throughput state is
 * left exactly as the runner writes it; only the DISPLAYED state is derived from the
 * structural disposition (never from sniffing the message text).
 *
 * Remaining gaps closed here (the B1 route already mapped the latest matching row):
 *  1. the disposition is bound to the throughput write by ended_at === last_built_at, but the
 *     "latest build_run_assets row" proxy lost that binding whenever a LATER row (queued /
 *     aborted, no throughput write) existed for the asset — the cascade victim then read red;
 *  2. blocked_by_asset_id is NULL for every pre-migration-1201 row (history), so the operator
 *     saw "blocked by upstream failure" with no name — the immediate blockers are named in the
 *     runner's own message, used here ONLY as a label fallback, never as the blocked signal.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'
import { blockersFromBlockedMessage } from '../throughputError'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const UID = 'owner-uid'
const BLOCK_MSG =
  'BLOCKED: upstream dependency(ies) ph_phaladesa, ph_pramana did not complete in this run; skipped to avoid building on incomplete data'
const T_ERR = '2026-08-21 02:36:53.123456+00'

interface RunRow { asset_id: string; created: number; state: string; disposition: string | null; blocked_by_asset_id: string | null; ended_at: string | null }

function setup(opts: { tpError: string | null; rows: RunRow[]; blockedByColumn?: boolean }) {
  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockQuery.mockImplementation((sql: string) => {
    const s = sql.replace(/\s+/g, ' ')
    if (/FROM profiles/.test(s)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/FROM chart_grants/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/owner_id[\s\S]*FROM charts/.test(s)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/information_schema\.columns/.test(s)) {
      return Promise.resolve({ rows: opts.blockedByColumn === false ? [] : [{ present: 1 }], rowCount: 1 })
    }
    if (/FROM asset_registry/.test(s)) {
      return Promise.resolve({
        rows: [{
          asset_id: 'mi_bhavisya', count_sql: null, size_sql: null, scope: 'per_chart', is_active: true,
          target_floor: null, asset_type: 'data', asset_kind: 'data', health_probe: null,
          service_health: null, last_invoked_at: null, last_selftest_at: null, has_substeps: false,
        }],
        rowCount: 1,
      })
    }
    if (/FROM asset_throughput/.test(s)) {
      return Promise.resolve({
        rows: [{ asset_id: 'mi_bhavisya', state: 'error', last_built_at: T_ERR, rows_written: null, last_error: opts.tpError }],
        rowCount: 1,
      })
    }
    if (/FROM build_substep_progress/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_run_assets bra[\s\S]*JOIN build_runs/.test(s)) {
      if (/asset_id = ANY/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
      // Honour the SQL's own predicates so the test exercises the route's query, not just its mapping.
      let rows = opts.rows
      if (/bra\.disposition = 'blocked_dependency'/.test(s)) rows = rows.filter(r => r.disposition === 'blocked_dependency')
      if (/bra\.state = 'error'/.test(s)) rows = rows.filter(r => r.state === 'error')
      const latest = [...rows].sort((a, b) => b.created - a.created)[0]
      return Promise.resolve({ rows: latest ? [latest] : [], rowCount: latest ? 1 : 0 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

async function stat() {
  const { GET } = await import('../route')
  const res = await GET(new NextRequest(`http://localhost/api/cockpit/stats?chart_id=${CHART_ID}`))
  const body = await res.json()
  return body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'mi_bhavisya')
}

const blockedRow = (over: Partial<RunRow> = {}): RunRow => ({
  asset_id: 'mi_bhavisya', created: 100, state: 'error', disposition: 'blocked_dependency',
  blocked_by_asset_id: null, ended_at: T_ERR, ...over,
})

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
})

describe('cascade skip is displayed as blocked-by-upstream, not error (Track I-3)', () => {
  it('CANONICAL mi_bhavisya: throughput error + latest row blocked_dependency (historical, blocked_by NULL) -> blocked, blockers named from the runner message', async () => {
    setup({ tpError: BLOCK_MSG, rows: [blockedRow()] })
    const a = await stat()
    expect(a.state).toBe('blocked')
    expect(a.blocked_by_asset_id).toBe('ph_phaladesa, ph_pramana')
    expect(a.blocked_by_source).toBe('message')
  })

  it('a recorded blocked_by_asset_id column value wins over the message and is labelled as the column', async () => {
    setup({ tpError: BLOCK_MSG, rows: [blockedRow({ blocked_by_asset_id: 'ph_pramana' })] })
    const a = await stat()
    expect(a.state).toBe('blocked')
    expect(a.blocked_by_asset_id).toBe('ph_pramana')
    expect(a.blocked_by_source).toBe('column')
  })

  it('a LATER row for the asset that never touched throughput (queued/aborted) no longer hides the block that produced the current error', async () => {
    setup({
      tpError: BLOCK_MSG,
      rows: [
        blockedRow({ created: 100 }),
        { asset_id: 'mi_bhavisya', created: 200, state: 'aborted', disposition: null, blocked_by_asset_id: null, ended_at: null },
      ],
    })
    const a = await stat()
    expect(a.state).toBe('blocked')
  })

  it('NEGATIVE: a genuine error with no disposition stays error (red) and carries no blocker fields', async () => {
    setup({
      tpError: 'psycopg2.errors.UndefinedColumn: column "x" does not exist',
      rows: [{ asset_id: 'mi_bhavisya', created: 100, state: 'error', disposition: null, blocked_by_asset_id: null, ended_at: T_ERR }],
    })
    const a = await stat()
    expect(a.state).toBe('error')
    expect(a.blocked_by_asset_id).toBeUndefined()
    expect(a.blocked_by_source).toBeUndefined()
  })

  it('NEGATIVE: a BLOCKED-looking message WITHOUT a blocked_dependency row stays error — the text is never the signal', async () => {
    setup({
      tpError: BLOCK_MSG,
      rows: [{ asset_id: 'mi_bhavisya', created: 100, state: 'error', disposition: null, blocked_by_asset_id: null, ended_at: T_ERR }],
    })
    expect((await stat()).state).toBe('error')
    vi.resetModules()
    setup({ tpError: BLOCK_MSG, rows: [] })
    expect((await stat()).state).toBe('error')
  })

  it('NEGATIVE: a blocked row from a DIFFERENT (older) attempt than the current throughput error stays error', async () => {
    setup({
      tpError: 'Timeout: writer exceeded 600s',
      rows: [blockedRow({ ended_at: '2026-08-01 00:00:00.000000+00' })],
    })
    expect((await stat()).state).toBe('error')
  })

  it('column absent (pre-1201 environment): degrades to no names from the column, still blocked only when a disposition row matches', async () => {
    setup({ tpError: BLOCK_MSG, rows: [blockedRow()], blockedByColumn: false })
    const a = await stat()
    expect(a.state).toBe('blocked')
    expect(a.blocked_by_source).toBe('message')
  })
})

describe('blockersFromBlockedMessage (label fallback only)', () => {
  it('parses the runner message and sorts nothing away', () => {
    expect(blockersFromBlockedMessage(BLOCK_MSG)).toBe('ph_phaladesa, ph_pramana')
    expect(blockersFromBlockedMessage(
      'BLOCKED: upstream dependency(ies) ph_nimitta did not complete in this run; skipped to avoid building on incomplete data',
    )).toBe('ph_nimitta')
  })
  it('returns null for anything that is not the runner BLOCKED message, or empty', () => {
    expect(blockersFromBlockedMessage(null)).toBeNull()
    expect(blockersFromBlockedMessage('Timeout: writer exceeded 600s')).toBeNull()
    expect(blockersFromBlockedMessage('BLOCKED: upstream dependency(ies)  did not complete in this run;')).toBeNull()
  })
})
