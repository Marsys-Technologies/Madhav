/**
 * @integration-test
 *
 * sessions.provenance_stamp.integration.test.ts — live-DB verification of
 * getOrRefreshProvenanceStamp (R5 W4 provenance-stamp serving, design §10.6/§31.3/§31.5).
 * ==============================================================================================
 * Verifies against the REAL `build_runs` table (migration 171) for the native chart
 * (482012f1) — the actual currently-live build tracker (NOT the phantom `builds` table
 * referenced by dead legacy schema in 0001_brahma_baseline.sql, which does not exist on
 * the live DB; confirmed live during development — see the JL entry for the full trace).
 *
 * Uses a synthetic test user (never the native's own uid) so this test never touches a
 * real session row; cleans up its own mcp_sessions row after each test.
 *
 * Gated on DB_AVAILABLE (same pattern as address_resolver.integration.test.ts) — runs
 * against a real PostgreSQL DB when DB_URL/DATABASE_URL is set, skips cleanly otherwise.
 *
 * Run:
 *   DATABASE_URL=postgresql://... vitest run --testPathPattern=sessions.provenance_stamp.integration
 */

import { describe, it, expect, afterEach } from 'vitest'
import { query } from '@/lib/db/client'
import { getOrCreateSession, getOrRefreshProvenanceStamp, deleteSession } from './sessions'

const DB_AVAILABLE = !!(process.env.DB_URL || process.env.DATABASE_URL)

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const TEST_USER = 'r5-w4-session-pin-test-user'
const TEST_SESSION_KEY = 'r5-w4-session-pin-integration-test'

const maybeDescribe = DB_AVAILABLE ? describe : describe.skip

maybeDescribe('getOrRefreshProvenanceStamp — live DB, native chart (482012f1)', () => {
  afterEach(async () => {
    // Clean up: delete the synthetic test session (never touches any real user's session).
    const { rows } = await query<{ session_id: string }>(
      `SELECT session_id::text FROM mcp_sessions WHERE user_uid = $1 AND session_key = $2`,
      [TEST_USER, TEST_SESSION_KEY],
    )
    for (const row of rows) {
      await deleteSession(row.session_id, TEST_USER)
    }
  })

  it('resolves a real build_id from build_runs for the native chart on first stamp (no fabrication)', async () => {
    const session = await getOrCreateSession(TEST_USER, TEST_SESSION_KEY)
    const { pin, drift, judgment_flags } = await getOrRefreshProvenanceStamp(
      session.session_id,
      TEST_USER,
      NATIVE_CHART_ID,
    )

    expect(drift).toBe(false) // first stamp of the session — nothing to drift from
    expect(judgment_flags).toEqual([])
    expect(pin.chart_id).toBe(NATIVE_CHART_ID)
    expect(pin.priors_version).toBe('1.0') // ranking/priors_config.ts PRIORS_VERSION, frozen
    // The native chart has real completed build_runs rows (verified live during development) —
    // build_id must be a real UUID, never null/fabricated for a chart with build history.
    expect(pin.build_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/)
    expect(pin.build_status).toBe('completed')
  })

  it('persists the stamp and re-resolves the SAME stamp (no drift) on a second call — the §10.6 contract', async () => {
    const session = await getOrCreateSession(TEST_USER, TEST_SESSION_KEY)
    const first = await getOrRefreshProvenanceStamp(session.session_id, TEST_USER, NATIVE_CHART_ID)
    const second = await getOrRefreshProvenanceStamp(session.session_id, TEST_USER, NATIVE_CHART_ID)

    expect(second.drift).toBe(false)
    expect(second.judgment_flags).toEqual([])
    expect(second.pin.build_id).toBe(first.pin.build_id)
    expect(second.pin.pinned_at).toBe(first.pin.pinned_at) // untouched — genuinely reused, not recomputed
  })

  it('re-keys the stamp by chart_id inside one session (§31.3 mitigation): stamping a second synthetic chart_id does not disturb the first', async () => {
    const OTHER_CHART_ID = '00000000-0000-0000-0000-000000000000' // has no build_runs rows — honest null
    const session = await getOrCreateSession(TEST_USER, TEST_SESSION_KEY)

    const nativePin = await getOrRefreshProvenanceStamp(session.session_id, TEST_USER, NATIVE_CHART_ID)
    const otherPin = await getOrRefreshProvenanceStamp(session.session_id, TEST_USER, OTHER_CHART_ID)
    const nativePinAgain = await getOrRefreshProvenanceStamp(session.session_id, TEST_USER, NATIVE_CHART_ID)

    expect(otherPin.pin.build_id).toBeNull() // no build_runs row for this synthetic chart — honest, not fabricated
    expect(nativePinAgain.pin.build_id).toBe(nativePin.pin.build_id) // unaffected by stamping the other chart
    expect(nativePinAgain.pin.pinned_at).toBe(nativePin.pin.pinned_at) // reused, not recomputed
  })
})
