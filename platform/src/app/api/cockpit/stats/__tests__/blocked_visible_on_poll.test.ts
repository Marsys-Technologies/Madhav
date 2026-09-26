/**
 * Packet B1 — R-2 (review B1_rereview_20260926T190244Z.md, "THE BIG ONE").
 *
 * THE DEFECT: `fetchAllCounts` never read `asset_throughput.last_error` at all —
 * `base.error` was null on EVERY path (the rows_written shortcut AND the count_sql
 * path), so `deriveState`'s `if (error)` branch — which holds the ENTIRE 'blocked'
 * check this packet added — was unreachable for a real cascade victim in any mode,
 * including `?mode=live`. The reviewer executed the real `deriveState` against the
 * 10 real production blocked pairs and found 9 of 10 rendering 'lit' (green,
 * "built"), 1 rendering 'dormant', zero rendering 'error', zero rendering
 * 'blocked' — seven of those ten on the native's own chart (482012f1).
 *
 * THE FIX: `errorFromThroughput(tp)` in route.ts now surfaces `tp.last_error` as
 * `error`, gated on `tp.state === 'error'` (never unconditionally — a blind
 * pass-through was rejected against live data: exactly one production row,
 * bg_transit_engine, is state='lit' with a stale never-cleared last_error that
 * would have been wrongly flipped to 'error').
 *
 * THE DECISIVE PROOF this file exists for: the REAL `GET` handler, fed the EXACT
 * real production column values for the 7 (of the reviewer's original 10) pairs
 * that are STILL genuine cascade blocks as of this session (re-measured; 2 of the
 * original 10 — ga_condition, ga_structural — have since resolved via a later
 * successful build, expected population drift; see EVENTS.jsonl's own documented
 * drift finding), must render 'blocked', not 'lit' or 'dormant'. All 7 measured
 * live 2026-09-27, from `asset_throughput` + `build_run_assets` joined to
 * `build_runs`, on chart 482012f1 (the native's own chart) — copied verbatim, not
 * paraphrased or rounded.
 *
 * A companion pair (mi_bhara) is included as the negative control: its latest
 * BLOCKED-text row is the TIMEOUT-mislabeled form (Decision 2/3 — a root cause
 * wearing cascade-victim text, excluded from disposition='blocked_dependency' by
 * the migration 1095 backfill predicate). It must render 'error', never
 * 'blocked' — proving this fix does not paper over Decision 2's own distinction.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const UID = 'owner-uid'

function makeReq(): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/stats?chart_id=${CHART_ID}`)
}

// ── Verbatim real production tuples (measured live, 2026-09-27) ────────────────
// asset_throughput: state, rows_written, last_built_at, last_error
// build_run_assets (latest row, joined via build_runs): ended_at (== last_built_at
// in every one of these 7 — the C-5(b) shared-NOW() binding holds), error text.
// disposition/blocked_by_asset_id are what migration 1095's backfill predicate
// WOULD assign (state='error' AND error LIKE 'BLOCKED:%' AND NOT the timeout
// pattern) — the migration has not applied in production yet (confirmed absent
// this session), so this is the fixture's one simulated field; every other value
// is copied verbatim from a live read-only query.
const REAL_BLOCKED = [
  {
    asset_id: 'mi_adhilepa', rows_written: 112270, has_substeps: false,
    error: 'BLOCKED: upstream dependency(ies) mi_gunanaka did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.708535+00', blocked_by: 'mi_gunanaka',
  },
  {
    asset_id: 'mi_bhavisya', rows_written: 278, has_substeps: false,
    error: 'BLOCKED: upstream dependency(ies) ph_phaladesa, ph_pramana did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.672507+00', blocked_by: 'ph_phaladesa, ph_pramana',
  },
  {
    asset_id: 'mi_darshana', rows_written: 115, has_substeps: true,
    error: 'BLOCKED: upstream dependency(ies) mi_adhilepa, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.7534+00', blocked_by: 'mi_adhilepa, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha',
  },
  {
    asset_id: 'mi_gunanaka', rows_written: 9, has_substeps: false,
    error: 'BLOCKED: upstream dependency(ies) mi_pramana did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.690124+00', blocked_by: 'mi_pramana',
  },
  {
    asset_id: 'mi_pariksha', rows_written: 1664, has_substeps: true,
    error: 'BLOCKED: upstream dependency(ies) mi_pramana did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.655163+00', blocked_by: 'mi_pramana',
  },
  {
    asset_id: 'mi_pramana', rows_written: 63, has_substeps: true,
    error: 'BLOCKED: upstream dependency(ies) mi_bhavisya did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.627032+00', blocked_by: 'mi_bhavisya',
  },
  {
    asset_id: 'mi_sambandha', rows_written: 24, has_substeps: false,
    error: 'BLOCKED: upstream dependency(ies) mi_bhavisya, mi_pariksha, mi_pramana did not complete in this run; skipped to avoid building on incomplete data',
    ts: '2026-08-21 02:36:53.726749+00', blocked_by: 'mi_bhavisya, mi_pariksha, mi_pramana',
  },
] as const

// The negative control — timeout-mislabeled, must render 'error', never 'blocked'.
const MI_BHARA = {
  asset_id: 'mi_bhara', rows_written: 0, has_substeps: false,
  error: 'BLOCKED: upstream dependency(ies) timeout:600s did not complete in this run; skipped to avoid building on incomplete data',
  ts: '2026-08-21 02:28:16.524173+00',
}

function registryRowsFor(assetIds: string[]) {
  return assetIds.map(asset_id => {
    const a = [...REAL_BLOCKED, MI_BHARA].find(x => x.asset_id === asset_id)!
    return {
      asset_id, count_sql: `SELECT count(*) FROM some_table WHERE chart_id=$1`,
      size_sql: null, scope: 'per_chart', is_active: true, target_floor: 0,
      asset_type: 'data', asset_kind: 'data', health_probe: null,
      service_health: null, last_invoked_at: null, last_selftest_at: null,
      has_substeps: a.has_substeps,
    }
  })
}

function setupMocks() {
  const allAssets = [...REAL_BLOCKED, MI_BHARA]
  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockQuery.mockImplementation((sql: string) => {
    const s = sql.replace(/\s+/g, ' ')
    if (/FROM profiles/.test(s)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/FROM chart_grants/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/owner_id[\s\S]*FROM charts/.test(s)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/information_schema\.columns/.test(s)) return Promise.resolve({ rows: [{ present: 1 }], rowCount: 1 })
    if (/FROM asset_registry/.test(s)) {
      return Promise.resolve({ rows: registryRowsFor(allAssets.map(a => a.asset_id)), rowCount: allAssets.length })
    }
    if (/FROM asset_throughput/.test(s)) {
      return Promise.resolve({
        rows: allAssets.map(a => ({
          asset_id: a.asset_id, state: 'error', last_built_at: a.ts,
          rows_written: a.rows_written, last_error: a.error,
        })),
        rowCount: allAssets.length,
      })
    }
    if (/FROM build_substep_progress/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_run_assets bra[\s\S]*JOIN build_runs/.test(s)) {
      if (/asset_id = ANY/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 }) // no global assets here
      return Promise.resolve({
        rows: [
          ...REAL_BLOCKED.map(a => ({
            asset_id: a.asset_id, disposition: 'blocked_dependency', blocked_by_asset_id: a.blocked_by, ended_at: a.ts,
          })),
          // mi_bhara: the timeout-mislabeled row — migration 1095's backfill predicate
          // excludes it (Decision 3), so disposition stays NULL.
          { asset_id: MI_BHARA.asset_id, disposition: null, blocked_by_asset_id: null, ended_at: MI_BHARA.ts },
        ],
        rowCount: allAssets.length,
      })
    }
    // count_sql path is never reached here (rows_written is non-null for all 8
    // fixtures — even mi_bhara's 0 satisfies `!= null` — so every one takes the
    // shortcut path). Fallback kept honest regardless.
    if (/count\(\*\)/.test(s)) return Promise.resolve({ rows: [{ count: '0' }], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
})

describe('cockpit stats route — the 7 real production blocked pairs render blocked, not lit (Packet B1, R-2)', () => {
  it('THE DECISIVE ASSERTION: all 7 real cascade-blocked assets render state=blocked, not lit/dormant/error', async () => {
    setupMocks()
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    const byId = new Map(body.data.assets.map((a: { asset_id: string; state: string }) => [a.asset_id, a]))
    for (const a of REAL_BLOCKED) {
      const rendered = byId.get(a.asset_id) as { state: string; blocked_by_asset_id?: string | null } | undefined
      expect(rendered, `${a.asset_id} missing from response`).toBeTruthy()
      expect(rendered!.state, `${a.asset_id} rendered ${rendered!.state}, expected blocked (rows_written=${a.rows_written} > 0 — this is EXACTLY the shape that used to fall through to 'lit')`).toBe('blocked')
      expect(rendered!.blocked_by_asset_id).toBe(a.blocked_by)
    }
  })

  it('THE NEGATIVE CONTROL: mi_bhara (timeout-mislabeled, Decision 2/3) still renders error, never blocked', async () => {
    setupMocks()
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const mibhara = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'mi_bhara')
    expect(mibhara.state).toBe('error')
  })

  it('BEFORE the fix (error hard-coded null, simulating the pre-R-2 code) every one of the 7 rendered lit — pinning the regression this proof catches', async () => {
    // Reproduces the reviewer's own finding directly against this fixture: with
    // `error` forced null (the exact pre-fix behaviour), rows_written > 0 makes
    // deriveState fall through to 'lit' for every asset here except mi_gunanaka
    // (rows_written=9, still > 0 -> also lit). This test does NOT call the route;
    // it calls the real deriveState directly with error forced null, to document
    // the regression this file's main assertion guards against.
    const { deriveState } = await import('../deriveState')
    for (const a of REAL_BLOCKED) {
      const state = deriveState(
        { has_substeps: a.has_substeps, target_floor: 0 },
        a.rows_written, /* error forced null, simulating pre-R-2 */ null, 'error', null, 'blocked_dependency',
      )
      expect(state, `${a.asset_id} with error forced null`).toBe('lit')
    }
  })
})
