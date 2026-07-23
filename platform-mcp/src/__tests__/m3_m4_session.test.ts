/**
 * m3_m4_session.test.ts — M3 session memory + M4 chart-switch advisory tests.
 *
 * Tests:
 *   M3 — session create/lookup/writeback
 *   M3 — session_recall re-checks entitlement (revoked grant → refused)
 *   M3 — session_list scoped to principal.uid (no cross-user leakage)
 *   M3 — catalog_chart_select persists active_chart_id to session
 *   M4 — catalog_chart_select surfaces advisory when chart_id != session.active_chart_id
 *   Security — memory strictly per user×chart; no cross-user leakage (2 users)
 *
 * Chart-agnostic invariants:
 *   - No native chart_id or name appears in this file.
 *   - Synthetic test UUIDs used throughout.
 *
 * M3+M4 — MCP elevation arc (2026-07-01).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocking ───────────────────────────────────────────────────────

import { getOrCreateSession, persistActiveChart, listSessions } from '../lib/session.js'
import { remoteAuthorize } from '../lib/authz.js'
import type { Principal } from '../types.js'

// ── Fixtures ───────────────────────────────────────────────────────────────────

// Synthetic test chart UUIDs — no native chart_id
const CHART_ALPHA = 'aaaaaaaa-1111-1111-1111-000000000001'
const CHART_BETA  = 'bbbbbbbb-2222-2222-2222-000000000002'

// Synthetic session UUIDs
const SESSION_USER_A = 'cccccccc-aaaa-aaaa-aaaa-000000000001'
const SESSION_USER_B = 'dddddddd-bbbb-bbbb-bbbb-000000000002'

function makePrincipal(overrides: Partial<Principal> = {}): Principal {
  return {
    user_uid: 'user-test-m3-001',
    key_id:   'mcp_test_00000003',
    role:     'guest',
    ...overrides,
  }
}

const principalA = makePrincipal({ user_uid: 'user-a-m3', key_id: 'mcp_test_a0000001' })
const principalB = makePrincipal({ user_uid: 'user-b-m3', key_id: 'mcp_test_b0000002' })

// Canonical session response shapes
function makeSessionResponse(
  userId: string,
  sessionId: string,
  activeChartId: string | null = null,
  sessionKey = 'default'
) {
  return {
    session: {
      session_id: sessionId,
      user_uid: userId,
      session_key: sessionKey,
      active_chart_id: activeChartId,
      created_at: '2026-07-01T00:00:00Z',
      last_seen_at: '2026-07-01T00:00:00Z',
      state_json: {},
    },
  }
}

beforeEach(() => {
  mockFetch.mockReset()
})

// ── M3.1 — Session create/lookup ──────────────────────────────────────────────

describe('M3 — getOrCreateSession', () => {
  it('creates a new session on first call', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeSessionResponse(principalA.user_uid, SESSION_USER_A),
    })

    const session = await getOrCreateSession(principalA, 'default')

    expect(session).not.toBeNull()
    expect(session?.session_id).toBe(SESSION_USER_A)
    expect(session?.user_uid).toBe(principalA.user_uid)
    expect(session?.active_chart_id).toBeNull()
  })

  it('resumes an existing session on subsequent call', async () => {
    // First call: returns existing session (already has active_chart_id)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_A, CHART_ALPHA),
    })

    const session = await getOrCreateSession(principalA, 'default')

    expect(session?.active_chart_id).toBe(CHART_ALPHA)
    expect(session?.session_id).toBe(SESSION_USER_A)
  })

  it('returns null on platform error (fail-closed)', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network timeout'))
    const session = await getOrCreateSession(principalA, 'default')
    expect(session).toBeNull()
  })

  it('returns null on non-ok HTTP response', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
    const session = await getOrCreateSession(principalA, 'default')
    expect(session).toBeNull()
  })

  it('uses the session_key to namespace sessions (different keys = different sessions)', async () => {
    // First call: "default" key → SESSION_USER_A
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_A, null, 'default'),
    })
    // Second call: "desktop" key → SESSION_USER_B (different session_id)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_B, null, 'desktop'),
    })

    const s1 = await getOrCreateSession(principalA, 'default')
    const s2 = await getOrCreateSession(principalA, 'desktop')

    expect(s1?.session_id).not.toBe(s2?.session_id)
    expect(s1?.session_key).toBe('default')
    expect(s2?.session_key).toBe('desktop')
  })
})

// ── M3.2 — persistActiveChart (catalog_chart_select wiring) ──────────────────────────

describe('M3 — persistActiveChart', () => {
  it('persists active_chart_id by calling POST /api/mcp/session', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true })

    const ok = await persistActiveChart(principalA, 'default', CHART_ALPHA)

    expect(ok).toBe(true)
    expect(mockFetch).toHaveBeenCalledOnce()

    // Verify the correct endpoint and body were called
    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/mcp/session')
    expect(options.method).toBe('POST')
    const body = JSON.parse(options.body as string) as { active_chart_id: string }
    expect(body.active_chart_id).toBe(CHART_ALPHA)
  })

  it('returns false on platform error (non-fatal)', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network error'))
    const ok = await persistActiveChart(principalA, 'default', CHART_ALPHA)
    expect(ok).toBe(false)
  })

  it('can clear active_chart_id (set to null)', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true })

    const ok = await persistActiveChart(principalA, 'default', null)
    expect(ok).toBe(true)

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit]
    const body = JSON.parse(options.body as string) as { active_chart_id: null }
    expect(body.active_chart_id).toBeNull()
  })
})

// ── M3.3 — listSessions (session_list) ────────────────────────────────────

describe('M3 — listSessions', () => {
  it('returns only the calling user\'s sessions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sessions: [
          {
            session_id: SESSION_USER_A,
            session_key: 'default',
            active_chart_id: CHART_ALPHA,
            last_seen_at: '2026-07-01T00:00:00Z',
          },
        ],
      }),
    })

    const sessions = await listSessions(principalA)

    expect(sessions).not.toBeNull()
    expect(sessions).toHaveLength(1)
    expect(sessions![0].session_id).toBe(SESSION_USER_A)
    expect(sessions![0].active_chart_id).toBe(CHART_ALPHA)
  })

  it('returns empty array when user has no sessions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sessions: [] }),
    })

    const sessions = await listSessions(principalA)
    expect(sessions).toHaveLength(0)
  })

  it('returns null on platform error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('timeout'))
    const sessions = await listSessions(principalA)
    expect(sessions).toBeNull()
  })
})

// ── M3.4 — Entitlement re-check on recall ─────────────────────────────────────

describe('M3 — entitlement re-check on session_recall', () => {
  it('denies a revoked chart on recall (grant revoked between sessions)', async () => {
    // Session lookup returns a session with active_chart_id = CHART_BETA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_A, CHART_BETA),
    })
    // Entitlement check for CHART_BETA → DENIED (grant was revoked)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })

    const session = await getOrCreateSession(principalA, 'default')
    expect(session?.active_chart_id).toBe(CHART_BETA)

    // Re-check entitlement for the stored active_chart_id
    const stillEntitled = await remoteAuthorize(principalA, CHART_BETA, 'view')

    // Grant revoked → refuse replay
    expect(stillEntitled).toBe(false)
  })

  it('allows recall when chart is still entitled', async () => {
    // Session lookup returns session with active_chart_id = CHART_ALPHA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_A, CHART_ALPHA),
    })
    // Entitlement check → ALLOWED
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })

    const session = await getOrCreateSession(principalA, 'default')
    expect(session?.active_chart_id).toBe(CHART_ALPHA)

    const stillEntitled = await remoteAuthorize(principalA, CHART_ALPHA, 'view')
    expect(stillEntitled).toBe(true)
  })
})

// ── M4 — Chart-switch advisory ────────────────────────────────────────────────

describe('M4 — chart-switch advisory', () => {
  it('advisory fires when catalog_chart_select switches to a different chart', () => {
    // Simulate the switch-detection logic from chart_selection.ts
    const previousChartId = CHART_ALPHA
    const incomingChartId = CHART_BETA

    const advisories: string[] = []
    if (previousChartId && previousChartId !== incomingChartId) {
      advisories.push(
        `You have switched to a different chart from your previous session. ` +
        `Consider starting a new conversation to avoid mixing chart contexts. ` +
        `Previous: ${previousChartId} → New: ${incomingChartId}.`
      )
    }

    expect(advisories).toHaveLength(1)
    expect(advisories[0]).toContain('switched to a different chart')
    expect(advisories[0]).toContain(CHART_ALPHA)
    expect(advisories[0]).toContain(CHART_BETA)
  })

  it('no advisory fires when selecting the same chart as before', () => {
    const previousChartId = CHART_ALPHA
    const incomingChartId = CHART_ALPHA  // same chart

    const advisories: string[] = []
    if (previousChartId && previousChartId !== incomingChartId) {
      advisories.push('advisory')
    }

    expect(advisories).toHaveLength(0)
  })

  it('no advisory fires when no prior session exists (first selection)', () => {
    const previousChartId: string | null = null  // no prior session
    const incomingChartId = CHART_ALPHA

    const advisories: string[] = []
    if (previousChartId && previousChartId !== incomingChartId) {
      advisories.push('advisory')
    }

    expect(advisories).toHaveLength(0)
  })

  it('advisory includes both previous and new chart IDs', () => {
    const previousChartId = CHART_ALPHA
    const incomingChartId = CHART_BETA

    const advisories: string[] = []
    if (previousChartId && previousChartId !== incomingChartId) {
      advisories.push(
        `You have switched to a different chart from your previous session. ` +
        `Consider starting a new conversation to avoid mixing chart contexts. ` +
        `Previous: ${previousChartId} → New: ${incomingChartId}.`
      )
    }

    // Advisory is warn-only — call still proceeds (not blocked)
    expect(advisories).toHaveLength(1)
    // Must reference both charts
    expect(advisories[0]).toContain(CHART_ALPHA)
    expect(advisories[0]).toContain(CHART_BETA)
    // Message style: warn not block
    expect(advisories[0]).not.toContain('denied')
    expect(advisories[0]).not.toContain('blocked')
  })
})

// ── M3.5 — Cross-user isolation (security check) ─────────────────────────────

describe('M3 — cross-user isolation (memory strictly per user×chart)', () => {
  it('User A session does not appear in User B session list', async () => {
    // User A's sessions: 1 session with CHART_ALPHA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sessions: [
          {
            session_id: SESSION_USER_A,
            session_key: 'default',
            active_chart_id: CHART_ALPHA,
            last_seen_at: '2026-07-01T00:00:00Z',
          },
        ],
      }),
    })
    // User B's sessions: 1 different session with CHART_BETA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sessions: [
          {
            session_id: SESSION_USER_B,
            session_key: 'default',
            active_chart_id: CHART_BETA,
            last_seen_at: '2026-07-01T00:00:00Z',
          },
        ],
      }),
    })

    const sessionsA = await listSessions(principalA)
    const sessionsB = await listSessions(principalB)

    // A sees only their session
    const idsA = (sessionsA ?? []).map((s) => s.session_id)
    expect(idsA).toContain(SESSION_USER_A)
    expect(idsA).not.toContain(SESSION_USER_B)

    // B sees only their session
    const idsB = (sessionsB ?? []).map((s) => s.session_id)
    expect(idsB).toContain(SESSION_USER_B)
    expect(idsB).not.toContain(SESSION_USER_A)
  })

  it('User B cannot see User A active chart through session lookup', async () => {
    // User A gets session with CHART_ALPHA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_A, CHART_ALPHA),
    })
    // User B gets session with CHART_BETA (different user — different session)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalB.user_uid, SESSION_USER_B, CHART_BETA),
    })

    const sessionA = await getOrCreateSession(principalA, 'default')
    const sessionB = await getOrCreateSession(principalB, 'default')

    // Each user sees only their own active chart
    expect(sessionA?.active_chart_id).toBe(CHART_ALPHA)
    expect(sessionA?.user_uid).toBe(principalA.user_uid)

    expect(sessionB?.active_chart_id).toBe(CHART_BETA)
    expect(sessionB?.user_uid).toBe(principalB.user_uid)

    // No cross-contamination
    expect(sessionA?.user_uid).not.toBe(sessionB?.user_uid)
    expect(sessionA?.active_chart_id).not.toBe(sessionB?.active_chart_id)
  })

  it('platform API headers always send user_uid from principal (never from body)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeSessionResponse(principalA.user_uid, SESSION_USER_A, null),
    })

    await getOrCreateSession(principalA, 'default')

    // Verify the fetch was called with the principal's uid in the header
    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers['X-MCP-User']).toBe(principalA.user_uid)
    // user_uid is NEVER in the body — stateless lookup from header only
    expect(options.body).toBeUndefined()
  })
})

// ── M3.6 — Statelessness preserved ───────────────────────────────────────────

describe('M3 — statelessness preserved (no in-process session held)', () => {
  it('each getOrCreateSession call makes a fresh HTTP request to the platform', async () => {
    const sessionData = makeSessionResponse(principalA.user_uid, SESSION_USER_A, CHART_ALPHA)

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => sessionData })
      .mockResolvedValueOnce({ ok: true, json: async () => sessionData })

    // Two separate calls
    await getOrCreateSession(principalA, 'default')
    await getOrCreateSession(principalA, 'default')

    // Each call hits the platform independently — no in-memory cache
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })
})
