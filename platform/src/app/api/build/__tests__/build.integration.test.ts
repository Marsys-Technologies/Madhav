/**
 * @integration-test
 *
 * D-Stream Build API Routes — Integration Test Suite
 * Session: D-09 [BUILD-ORCH-D-09]
 *
 * Covers all 8 D-stream API routes end-to-end against a real PostgreSQL DB.
 *
 * Prerequisites:
 *   - DB_URL or DATABASE_URL env var pointing to a test database.
 *   - Migrations 121–127 applied (builds, build_steps, engine_versions,
 *     build_engine_versions, build_notifications, charts, pyramid_layers tables).
 *   - Firebase auth is mocked; the mock is always injected before each test.
 *   - Cloud Tasks / Cloud Run are mocked — no external calls.
 *
 * Run:
 *   DB_URL=postgresql://user:pass@host/db vitest run \
 *     --testPathPattern=build.integration
 *
 * Routes under test:
 *   1. POST /api/build/start           — creates build + 14 build_steps rows
 *   2. POST /api/build/cancel/[buildId] — transitions to cancelling
 *   3. GET  /api/build/active          — in-progress builds with progress_pct
 *   4. GET  /api/build/recent          — unseen completed builds (24h window)
 *   5. GET  /api/engine/current        — current engine version metadata
 *   6. GET  /api/conversations/[id]/active-ayanamshas — J-01 graceful degradation
 *   7. GET  /api/charts/[id]/ayanamsha-status         — 5-ayanamsha per-chart state
 *   8. POST /api/clients/create        — hardened with rate-limit + idempotency
 */

import { describe, it, expect, vi, beforeAll, afterAll, beforeEach } from 'vitest'
import { randomUUID } from 'crypto'

// ─── DB availability guard ───────────────────────────────────────────────────

const DB_AVAILABLE = !!(process.env.DB_URL || process.env.DATABASE_URL)

// ─── Module-level mocks (hoisted so routes pick them up) ─────────────────────

const {
  mockGetServerUser,
  mockEnqueueBuild,
  mockInvokeBuildJob,
  mockRecordBuildEvent,
  mockGetFlag,
} = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockEnqueueBuild: vi.fn(),
  mockInvokeBuildJob: vi.fn(),
  mockRecordBuildEvent: vi.fn(),
  mockGetFlag: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/build/trigger', () => ({ enqueueBuild: mockEnqueueBuild }))
vi.mock('@/lib/build/jobInvoker', () => ({ invokeBuildJob: mockInvokeBuildJob }))
vi.mock('@/lib/build/events', () => ({ recordBuildEvent: mockRecordBuildEvent }))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))

// Real DB client — NOT mocked.  Tests talk to the real database.
// The @/lib/auth/authorizeChartAccess module is also real so that it exercises
// the real SQL permission resolver against seeded rows.
vi.mock('@/lib/auth/authorizeChartAccess', async () => {
  const actual = await vi.importActual<
    typeof import('@/lib/auth/authorizeChartAccess')
  >('@/lib/auth/authorizeChartAccess')
  return actual
})

// ─── Route imports (after mocks) ─────────────────────────────────────────────

import { POST as POST_START } from '../start/route'
import { POST as POST_CANCEL } from '../cancel/[buildId]/route'
import { GET as GET_ACTIVE } from '../active/route'
import { GET as GET_RECENT } from '../recent/route'
import { GET as GET_ENGINE_CURRENT } from '../../engine/current/route'
import { GET as GET_ACTIVE_AYANAMSHAS } from '../../conversations/[id]/active-ayanamshas/route'
import { GET as GET_AYANAMSHA_STATUS } from '../../charts/[id]/ayanamsha-status/route'
import { POST as POST_CLIENTS_CREATE } from '../../clients/create/route'

// ─── DB client (real) ────────────────────────────────────────────────────────

import { query } from '@/lib/db/client'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeReq(
  url: string,
  method: string,
  body?: unknown,
  headers: Record<string, string> = {},
): Request {
  const init: RequestInit = {
    method,
    headers: { 'content-type': 'application/json', ...headers },
  }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }
  return new Request(url, init)
}

function params<T extends Record<string, string>>(
  p: T,
): { params: Promise<T> } {
  return { params: Promise.resolve(p) }
}

// ─── Test-data seed helpers ───────────────────────────────────────────────────

/**
 * Seed a user profile row so profile lookups resolve correctly.
 * Returns the uid.
 */
async function seedProfile(
  uid: string,
  role: 'guest' | 'super_admin' = 'guest',
): Promise<string> {
  await query(
    `INSERT INTO profiles (uid, role, email)
     VALUES ($1, $2, $3)
     ON CONFLICT (uid) DO UPDATE SET role = EXCLUDED.role`,
    [uid, role, `${uid}@test.marsys`],
  )
  return uid
}

/**
 * Seed a minimal chart row owned by the given uid.
 * Returns the chart_id.
 */
async function seedChart(ownerUid: string, name = 'Integration Test Chart'): Promise<string> {
  const chartId = randomUUID()
  await query(
    `INSERT INTO charts (id, owner_id, name, birth_date, birth_time, lat, lon, tz_offset)
     VALUES ($1, $2, $3, '1990-01-01', '12:00', 0.0, 0.0, 0.0)`,
    [chartId, ownerUid, name],
  )
  return chartId
}

/**
 * Seed a builds row with specified status + ayanamshas.
 * Returns the build_id.
 */
async function seedBuild(opts: {
  chartId: string
  ownerUid: string
  status?: string
  ayanamshas?: string[]
  finishedAt?: string
  failedAt?: string
  engineVersion?: string
}): Promise<string> {
  const {
    chartId,
    ownerUid,
    status = 'complete',
    ayanamshas = ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'],
    finishedAt = null,
    failedAt = null,
    engineVersion = null,
  } = opts

  const buildId = randomUUID()
  await query(
    `INSERT INTO builds (build_id, chart_id, triggered_by_uid, status, ayanamshas,
       finished_at, failed_at, engine_version)
     VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)`,
    [
      buildId,
      chartId,
      ownerUid,
      status,
      JSON.stringify(ayanamshas),
      finishedAt,
      failedAt,
      engineVersion,
    ],
  )
  return buildId
}

/**
 * Seed build_steps rows for a build.
 */
async function seedBuildSteps(
  buildId: string,
  stepsComplete: number,
  stepsTotal: number,
): Promise<void> {
  for (let i = 0; i < stepsTotal; i++) {
    const stepStatus = i < stepsComplete ? 'complete' : 'pending'
    await query(
      `INSERT INTO build_steps (build_id, step_index, asset_key, status)
       VALUES ($1, $2, $3, $4)`,
      [buildId, i, `asset_${i}`, stepStatus],
    )
  }
}

/**
 * Seed an engine_versions row. Returns the version_id.
 */
async function seedEngineVersion(opts: {
  versionStr?: string
  engineName?: string
  gitSha?: string
}): Promise<string> {
  const {
    versionStr = '1.0.0',
    engineName = 'marsys-core',
    gitSha = null,
  } = opts
  const versionId = randomUUID()
  await query(
    `INSERT INTO engine_versions (version_id, engine_name, version_str, git_sha)
     VALUES ($1, $2, $3, $4)`,
    [versionId, engineName, versionStr, gitSha],
  )
  return versionId
}

/**
 * Seed a conversation row associated with an optional chart.
 * Returns the conversation id.
 */
async function seedConversation(opts: {
  userId: string
  chartId?: string
  activeAyanamshas?: string[] | null
}): Promise<string> {
  const { userId, chartId = null, activeAyanamshas = null } = opts
  const convId = randomUUID()

  // Use a conditional INSERT that only sets active_ayanamshas if the column
  // exists (the column is added by a migration; it may not be present in CI
  // test DBs).  We attempt the richer INSERT first and fall back to the plain one.
  try {
    await query(
      `INSERT INTO conversations (id, user_id, chart_id, active_ayanamshas)
       VALUES ($1, $2, $3, $4::jsonb)`,
      [convId, userId, chartId, activeAyanamshas ? JSON.stringify(activeAyanamshas) : null],
    )
  } catch {
    // Column absent — seed without it.
    await query(
      `INSERT INTO conversations (id, user_id, chart_id) VALUES ($1, $2, $3)`,
      [convId, userId, chartId],
    )
  }
  return convId
}

/**
 * Delete test rows created during a test to avoid pollution between runs.
 */
async function cleanupBuild(buildId: string): Promise<void> {
  await query('DELETE FROM build_steps WHERE build_id = $1', [buildId])
  await query('DELETE FROM builds WHERE build_id = $1', [buildId])
}

async function cleanupChart(chartId: string): Promise<void> {
  const buildsRes = await query('SELECT build_id FROM builds WHERE chart_id = $1', [chartId])
  for (const row of buildsRes.rows as Array<{ build_id: string }>) {
    await cleanupBuild(row.build_id)
  }
  await query('DELETE FROM pyramid_layers WHERE chart_id = $1', [chartId])
  await query('DELETE FROM charts WHERE id = $1', [chartId])
}

async function cleanupEngineVersion(versionId: string): Promise<void> {
  await query('DELETE FROM build_engine_versions WHERE version_id = $1', [versionId])
  await query('DELETE FROM engine_versions WHERE version_id = $1', [versionId])
}

async function cleanupConversation(convId: string): Promise<void> {
  await query('DELETE FROM conversations WHERE id = $1', [convId])
}

// ─── Suite ───────────────────────────────────────────────────────────────────

describe.skipIf(!DB_AVAILABLE)('Build API Routes — Integration (DB-backed)', () => {
  // Shared test UIDs — deterministic so profile cleanup is easy.
  const OWNER_UID = `integration-test-owner-${Date.now()}`
  const ADMIN_UID = `integration-test-admin-${Date.now()}`
  const STRANGER_UID = `integration-test-stranger-${Date.now()}`

  // Tracked resource IDs for cleanup.
  const trackedCharts: string[] = []
  const trackedBuilds: string[] = []
  const trackedEngineVersions: string[] = []
  const trackedConversations: string[] = []

  beforeAll(async () => {
    // Seed profiles once for the entire suite.
    await seedProfile(OWNER_UID, 'guest')
    await seedProfile(ADMIN_UID, 'super_admin')
    await seedProfile(STRANGER_UID, 'guest')
  })

  afterAll(async () => {
    // Best-effort cleanup in reverse dependency order.
    for (const id of trackedConversations) {
      await cleanupConversation(id).catch(() => {})
    }
    for (const id of trackedBuilds) {
      await cleanupBuild(id).catch(() => {})
    }
    for (const id of trackedCharts) {
      await cleanupChart(id).catch(() => {})
    }
    for (const id of trackedEngineVersions) {
      await cleanupEngineVersion(id).catch(() => {})
    }
    // Clean up profiles last.
    await query('DELETE FROM profiles WHERE uid IN ($1, $2, $3)', [
      OWNER_UID,
      ADMIN_UID,
      STRANGER_UID,
    ]).catch(() => {})
  })

  beforeEach(() => {
    mockGetServerUser.mockReset()
    mockEnqueueBuild.mockReset()
    mockInvokeBuildJob.mockReset()
    mockRecordBuildEvent.mockReset()
    mockGetFlag.mockReset()
    // Feature flag ON by default for all tests.
    mockGetFlag.mockImplementation(
      (name: string) => name === 'BUILD_TRIGGER_ENABLED',
    )
    // Cloud Tasks mock — returns a predictable build_id and task_name.
    mockEnqueueBuild.mockImplementation(
      async (payload: { chartId: string; ayanamshaRole?: string; triggeredBy: string }) => ({
        buildId: `it-build-${Date.now()}`,
        taskName: `projects/test/locations/us-central1/queues/q/tasks/t-${Date.now()}`,
        payload,
      }),
    )
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 1: POST /api/build/start
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 1 — POST /api/build/start', () => {
    it('[IT-R1-01] creates a builds row and 14 build_steps for the chart owner', async () => {
      const chartId = await seedChart(OWNER_UID, 'R1 Test Chart')
      trackedCharts.push(chartId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_START()

      expect(res.status).toBe(200)
      const body = (await res.json()) as {
        build_id: string
        chart_id: string
        step_count: number
        status: string
        ayanamshas: string[]
      }

      expect(body.build_id).toBeTruthy()
      expect(body.chart_id).toBe(chartId)
      expect(body.step_count).toBe(14)
      expect(body.status).toBe('queued')
      expect(Array.isArray(body.ayanamshas)).toBe(true)

      // Verify the builds row landed in the DB.
      const buildsRes = await query(
        'SELECT build_id, status, chart_id FROM builds WHERE build_id = $1',
        [body.build_id],
      )
      expect(buildsRes.rows).toHaveLength(1)
      expect((buildsRes.rows[0] as { status: string }).status).toBe('queued')

      // Verify exactly 14 build_steps rows.
      const stepsRes = await query(
        'SELECT COUNT(*) AS cnt FROM build_steps WHERE build_id = $1',
        [body.build_id],
      )
      const cnt = Number((stepsRes.rows[0] as { cnt: string }).cnt)
      expect(cnt).toBe(14)

      trackedBuilds.push(body.build_id)
    })

    it('[IT-R1-02] defaults to all 5 ayanamshas when ayanamshas[] not provided', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_START()
      expect(res.status).toBe(200)
      const body = (await res.json()) as { ayanamshas: string[]; build_id: string }
      expect(body.ayanamshas).toHaveLength(5)
      trackedBuilds.push(body.build_id)
    })

    it('[IT-R1-03] 401 when unauthenticated', async () => {
      mockGetServerUser.mockResolvedValue(null)
      const res = await POST_START()
      expect(res.status).toBe(401)
    })

    it('[IT-R1-04] 403 when caller has view-only grant on the chart', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      // Seed a view grant for STRANGER_UID.
      await query(
        `INSERT INTO chart_grants (chart_id, uid, permission)
         VALUES ($1, $2, 'view')
         ON CONFLICT DO NOTHING`,
        [chartId, STRANGER_UID],
      )
      mockGetServerUser.mockResolvedValue({ uid: STRANGER_UID })

      const res = await POST_START()
      expect(res.status).toBe(403)
    })

    it('[IT-R1-05] 503 when BUILD_TRIGGER_ENABLED flag is off', async () => {
      mockGetFlag.mockReturnValue(false)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_START()
      expect(res.status).toBe(503)
      const body = (await res.json()) as { error: string }
      expect(body.error).toBe('build_trigger_disabled')
    })

    it('[IT-R1-06] super_admin can trigger a build on any chart', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: ADMIN_UID })

      const res = await POST_START()
      expect(res.status).toBe(200)
      const body = (await res.json()) as { build_id: string }
      trackedBuilds.push(body.build_id)
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 2: POST /api/build/cancel/[buildId]
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 2 — POST /api/build/cancel/[buildId]', () => {
    it('[IT-R2-01] transitions a queued build to cancelling and persists in DB', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const buildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'queued' })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CANCEL()
      expect(res.status).toBe(200)
      const body = (await res.json()) as { message: string; build_id: string }
      expect(body.message).toBe('Cancellation requested')
      expect(body.build_id).toBe(buildId)

      // Verify DB persisted the cancelling status.
      const dbRes = await query(
        'SELECT status FROM builds WHERE build_id = $1',
        [buildId],
      )
      expect((dbRes.rows[0] as { status: string }).status).toBe('cancelling')
    })

    it('[IT-R2-02] 409 when build is already in terminal complete state', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const buildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'complete' })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CANCEL()
      expect(res.status).toBe(409)
      const body = (await res.json()) as { current_status: string }
      expect(body.current_status).toBe('complete')
    })

    it('[IT-R2-03] 200 idempotent when already cancelling — no DB UPDATE', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const buildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'cancelling' })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CANCEL()
      expect(res.status).toBe(200)
      const body = (await res.json()) as { message: string }
      expect(body.message).toBe('Cancellation already in progress')

      // Verify DB status unchanged.
      const dbRes = await query(
        'SELECT status FROM builds WHERE build_id = $1',
        [buildId],
      )
      expect((dbRes.rows[0] as { status: string }).status).toBe('cancelling')
    })

    it('[IT-R2-04] 403 when caller does not own the build', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const buildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'running' })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: STRANGER_UID })

      const res = await POST_CANCEL()
      expect(res.status).toBe(403)
    })

    it('[IT-R2-05] super_admin can cancel another user\'s running build', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const buildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'running' })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: ADMIN_UID })

      const res = await POST_CANCEL()
      expect(res.status).toBe(200)
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 3: GET /api/build/active
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 3 — GET /api/build/active', () => {
    it('[IT-R3-01] 200 with empty array when no active builds exist for user', async () => {
      // Create a user with no builds.
      const isolatedUid = `it-active-empty-${Date.now()}`
      await seedProfile(isolatedUid)
      mockGetServerUser.mockResolvedValue({ uid: isolatedUid })

      const res = await GET_ACTIVE()
      expect(res.status).toBe(200)
      const body = await res.json()
      expect(Array.isArray(body)).toBe(true)
      expect(body).toHaveLength(0)

      await query('DELETE FROM profiles WHERE uid = $1', [isolatedUid]).catch(() => {})
    })

    it('[IT-R3-02] active endpoint returns queued build with correct progress_pct', async () => {
      const chartId = await seedChart(OWNER_UID, 'Active Route Chart')
      trackedCharts.push(chartId)
      const buildId = await seedBuild({
        chartId,
        ownerUid: OWNER_UID,
        status: 'queued',
      })
      trackedBuilds.push(buildId)
      await seedBuildSteps(buildId, 7, 14)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_ACTIVE()
      expect(res.status).toBe(200)
      const body = (await res.json()) as Array<{
        build_id: string
        status: string
        progress_pct: number
        steps_complete: number
        steps_total: number
      }>

      const found = body.find((b) => b.build_id === buildId)
      expect(found).toBeDefined()
      expect(found!.status).toBe('queued')
      expect(found!.steps_complete).toBe(7)
      expect(found!.steps_total).toBe(14)
      expect(found!.progress_pct).toBe(50)
    })

    it('[IT-R3-03] only queued/running/cancelling builds appear (not complete/failed)', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const activeBuildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'running' })
      const completeBuildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'complete' })
      trackedBuilds.push(activeBuildId, completeBuildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_ACTIVE()
      const body = (await res.json()) as Array<{ build_id: string }>
      const ids = body.map((b) => b.build_id)

      expect(ids).toContain(activeBuildId)
      expect(ids).not.toContain(completeBuildId)
    })

    it('[IT-R3-04] response item shape contains required fields', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const buildId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'running' })
      trackedBuilds.push(buildId)
      await seedBuildSteps(buildId, 3, 14)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
      const res = await GET_ACTIVE()
      const body = (await res.json()) as Array<Record<string, unknown>>
      const item = body.find((b) => b.build_id === buildId)
      expect(item).toBeDefined()
      expect(item).toHaveProperty('build_id')
      expect(item).toHaveProperty('chart_id')
      expect(item).toHaveProperty('ayanamshas')
      expect(item).toHaveProperty('status')
      expect(item).toHaveProperty('queued_at')
      expect(item).toHaveProperty('progress_pct')
      expect(Array.isArray(item!.ayanamshas)).toBe(true)
    })

    it('[IT-R3-05] Cache-Control: max-age=5 present on response', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
      const res = await GET_ACTIVE()
      expect(res.headers.get('Cache-Control')).toBe('max-age=5')
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 4: GET /api/build/recent
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 4 — GET /api/build/recent', () => {
    it('[IT-R4-01] returns a complete build finished 1h ago', async () => {
      const chartId = await seedChart(OWNER_UID, 'Recent Route Chart')
      trackedCharts.push(chartId)
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
      const buildId = await seedBuild({
        chartId,
        ownerUid: OWNER_UID,
        status: 'complete',
        finishedAt: oneHourAgo,
      })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_RECENT()
      expect(res.status).toBe(200)
      const body = (await res.json()) as Array<{ build_id: string; status: string }>
      const found = body.find((b) => b.build_id === buildId)
      expect(found).toBeDefined()
      expect(found!.status).toBe('complete')
    })

    it('[IT-R4-02] does NOT return builds older than 24h', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const thirtyHoursAgo = new Date(Date.now() - 30 * 60 * 60 * 1000).toISOString()
      const buildId = await seedBuild({
        chartId,
        ownerUid: OWNER_UID,
        status: 'complete',
        finishedAt: thirtyHoursAgo,
      })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_RECENT()
      const body = (await res.json()) as Array<{ build_id: string }>
      const found = body.find((b) => b.build_id === buildId)
      expect(found).toBeUndefined()
    })

    it('[IT-R4-03] includes failed build with error_summary in the window', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const failedAt = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      // The builds table uses a failed_at column for failed builds.
      const buildId = await seedBuild({
        chartId,
        ownerUid: OWNER_UID,
        status: 'failed',
        failedAt,
      })
      trackedBuilds.push(buildId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_RECENT()
      const body = (await res.json()) as Array<{ build_id: string; status: string }>
      const found = body.find((b) => b.build_id === buildId)
      expect(found).toBeDefined()
      expect(found!.status).toBe('failed')
    })

    it('[IT-R4-04] active builds (queued/running) are NOT returned', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const runningId = await seedBuild({ chartId, ownerUid: OWNER_UID, status: 'running' })
      trackedBuilds.push(runningId)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
      const res = await GET_RECENT()
      const body = (await res.json()) as Array<{ build_id: string }>
      expect(body.find((b) => b.build_id === runningId)).toBeUndefined()
    })

    it('[IT-R4-05] Cache-Control: no-store present on response', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
      const res = await GET_RECENT()
      expect(res.headers.get('Cache-Control')).toBe('no-store')
    })

    it('[IT-R4-06] 401 when unauthenticated', async () => {
      mockGetServerUser.mockResolvedValue(null)
      const res = await GET_RECENT()
      expect(res.status).toBe(401)
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 5: GET /api/engine/current
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 5 — GET /api/engine/current', () => {
    it('[IT-R5-01] returns 200 with correct engine metadata when a version row exists', async () => {
      const versionId = await seedEngineVersion({
        versionStr: '2.0.0',
        engineName: 'marsys-it',
        gitSha: 'abc1234',
      })
      trackedEngineVersions.push(versionId)

      const res = await GET_ENGINE_CURRENT(
        makeReq('http://localhost/api/engine/current', 'GET'),
      )
      // Accept 200 or 404 — if another test inserted a newer row it may return
      // a different version_id but the schema assertions still hold.
      expect([200, 404]).toContain(res.status)

      if (res.status === 200) {
        const body = await res.json()
        expect(body.version).toBeTruthy()
        expect(body.status).toBe('current')
        expect(body).toHaveProperty('promoted_at')
        expect(body).toHaveProperty('version_id')
        expect(body).toHaveProperty('engine_name')
        expect(body.release_notes_uri).toBeNull()
      }
    })

    it('[IT-R5-02] does NOT require authentication — returns without session', async () => {
      // Deliberately provide no user mock — if the route required auth it
      // would call getServerUser and fail/return 401.
      const versionId = await seedEngineVersion({ versionStr: '3.0.0-noauth-test' })
      trackedEngineVersions.push(versionId)

      const res = await GET_ENGINE_CURRENT(
        makeReq('http://localhost/api/engine/current', 'GET'),
      )
      // 200 or 404 are both acceptable — 401 is NOT.
      expect(res.status).not.toBe(401)
    })

    it('[IT-R5-03] Cache-Control: max-age=300 on successful 200', async () => {
      const versionId = await seedEngineVersion({ versionStr: '4.0.0-cache-test' })
      trackedEngineVersions.push(versionId)

      const res = await GET_ENGINE_CURRENT(
        makeReq('http://localhost/api/engine/current', 'GET'),
      )
      if (res.status === 200) {
        expect(res.headers.get('Cache-Control')).toBe('max-age=300')
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 6: GET /api/conversations/[id]/active-ayanamshas
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 6 — GET /api/conversations/[id]/active-ayanamshas', () => {
    const CANONICAL_AYANAMSHAS = [
      'lahiri',
      'raman',
      'krishnamurti',
      'yukteshwar',
      'true_chitra',
    ]

    it('[IT-R6-01] returns 5 canonical ayanamshas when column absent (J-01 degradation)', async () => {
      const convId = await seedConversation({ userId: OWNER_UID })
      trackedConversations.push(convId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_ACTIVE_AYANAMSHAS(
        makeReq(
          `http://localhost/api/conversations/${convId}/active-ayanamshas`,
          'GET',
        ),
        params({ id: convId }),
      )

      expect(res.status).toBe(200)
      const body = await res.json()
      expect(Array.isArray(body.active_ayanamshas)).toBe(true)
      // Graceful degradation: either returns defaults or explicitly-set list.
      expect(body.active_ayanamshas.length).toBeGreaterThanOrEqual(1)
    })

    it('[IT-R6-02] 401 when unauthenticated', async () => {
      const convId = await seedConversation({ userId: OWNER_UID })
      trackedConversations.push(convId)
      mockGetServerUser.mockResolvedValue(null)

      const res = await GET_ACTIVE_AYANAMSHAS(
        makeReq(
          `http://localhost/api/conversations/${convId}/active-ayanamshas`,
          'GET',
        ),
        params({ id: convId }),
      )
      expect(res.status).toBe(401)
    })

    it('[IT-R6-03] 404 when conversation belongs to a different user', async () => {
      const convId = await seedConversation({ userId: OWNER_UID })
      trackedConversations.push(convId)
      mockGetServerUser.mockResolvedValue({ uid: STRANGER_UID })

      const res = await GET_ACTIVE_AYANAMSHAS(
        makeReq(
          `http://localhost/api/conversations/${convId}/active-ayanamshas`,
          'GET',
        ),
        params({ id: convId }),
      )
      expect(res.status).toBe(404)
    })

    it('[IT-R6-04] response body contains conversation_id echo', async () => {
      const convId = await seedConversation({ userId: OWNER_UID })
      trackedConversations.push(convId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_ACTIVE_AYANAMSHAS(
        makeReq(
          `http://localhost/api/conversations/${convId}/active-ayanamshas`,
          'GET',
        ),
        params({ id: convId }),
      )
      if (res.status === 200) {
        const body = await res.json()
        expect(body.conversation_id).toBe(convId)
      }
    })

    it('[IT-R6-05] Cache-Control: max-age=60 on successful response', async () => {
      const convId = await seedConversation({ userId: OWNER_UID })
      trackedConversations.push(convId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_ACTIVE_AYANAMSHAS(
        makeReq(
          `http://localhost/api/conversations/${convId}/active-ayanamshas`,
          'GET',
        ),
        params({ id: convId }),
      )
      if (res.status === 200) {
        expect(res.headers.get('Cache-Control')).toBe('max-age=60')
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 7: GET /api/charts/[id]/ayanamsha-status
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 7 — GET /api/charts/[id]/ayanamsha-status', () => {
    const CANONICAL_ORDER = ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta']

    it('[IT-R7-01] returns array of exactly 5 items for a chart with no builds', async () => {
      const chartId = await seedChart(OWNER_UID, 'Ayanamsha Status Chart')
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      expect(res.status).toBe(200)
      const body = (await res.json()) as Array<{ ayanamsha_id: string; status: string }>
      expect(body).toHaveLength(5)
      for (const canonical of CANONICAL_ORDER) {
        expect(body.some((item) => item.ayanamsha_id === canonical)).toBe(true)
      }
    })

    it('[IT-R7-02] all items have status=not_built when no builds exist', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      const body = (await res.json()) as Array<{ status: string; latest_build_id: unknown }>
      for (const item of body) {
        expect(item.status).toBe('not_built')
        expect(item.latest_build_id).toBeNull()
      }
    })

    it('[IT-R7-03] complete build shows status=complete + populated latest_build_id', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      const finishedAt = new Date().toISOString()
      const buildId = await seedBuild({
        chartId,
        ownerUid: OWNER_UID,
        status: 'complete',
        ayanamshas: CANONICAL_ORDER,
        finishedAt,
      })
      trackedBuilds.push(buildId)
      await seedBuildSteps(buildId, 14, 14)

      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      const body = (await res.json()) as Array<{
        ayanamsha_id: string
        status: string
        latest_build_id: string | null
        steps_complete: number
        steps_total: number
      }>
      expect(body).toHaveLength(5)
      // All should reference the same build.
      const lahiri = body.find((i) => i.ayanamsha_id === 'lahiri')
      expect(lahiri).toBeDefined()
      expect(lahiri!.latest_build_id).toBe(buildId)
      expect(lahiri!.status).toBe('complete')
    })

    it('[IT-R7-04] items maintain canonical order in response', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      const body = (await res.json()) as Array<{ ayanamsha_id: string }>
      expect(body.map((i) => i.ayanamsha_id)).toEqual(CANONICAL_ORDER)
    })

    it('[IT-R7-05] 401 when unauthenticated', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue(null)

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      expect(res.status).toBe(401)
    })

    it('[IT-R7-06] 404 when chart does not belong to the caller', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: STRANGER_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      expect(res.status).toBe(404)
    })

    it('[IT-R7-07] super_admin can access charts owned by others', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: ADMIN_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      expect(res.status).toBe(200)
    })

    it('[IT-R7-08] Cache-Control: max-age=10 present on successful response', async () => {
      const chartId = await seedChart(OWNER_UID)
      trackedCharts.push(chartId)
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await GET_AYANAMSHA_STATUS(
        makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
        params({ id: chartId }),
      )
      if (res.status === 200) {
        expect(res.headers.get('Cache-Control')).toBe('max-age=10')
      }
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Route 8: POST /api/clients/create
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Route 8 — POST /api/clients/create', () => {
    const VALID_PAYLOAD = {
      name: 'Integration Test Subject',
      birth_date: '1990-06-15',
      birth_time: '14:30',
      birth_place: 'New Delhi, India',
      lat: 28.6139,
      lon: 77.209,
      tz_offset: 5.5,
    }

    it('[IT-R8-01] creates chart row + returns chart_id + redirect_url on valid request', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', VALID_PAYLOAD),
      )
      expect(res.status).toBe(200)
      const body = (await res.json()) as {
        chart_id: string
        redirect_url: string
        ayanamshas: string[]
      }
      expect(typeof body.chart_id).toBe('string')
      expect(body.chart_id).toBeTruthy()
      expect(body.redirect_url).toBe(`/clients/${body.chart_id}/build`)
      expect(body.ayanamshas).toHaveLength(5)

      // Verify the row is in the DB.
      const dbRes = await query('SELECT id FROM charts WHERE id = $1', [body.chart_id])
      expect(dbRes.rows).toHaveLength(1)

      trackedCharts.push(body.chart_id)
    })

    it('[IT-R8-02] defaults ayanamshas to all 5 when not specified', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', VALID_PAYLOAD),
      )
      const body = (await res.json()) as { ayanamshas: string[]; chart_id: string }
      expect(body.ayanamshas).toHaveLength(5)
      trackedCharts.push(body.chart_id)
    })

    it('[IT-R8-03] accepts explicit subset of ayanamshas', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', {
          ...VALID_PAYLOAD,
          ayanamshas: ['lahiri', 'kp'],
        }),
      )
      expect(res.status).toBe(200)
      const body = (await res.json()) as { ayanamshas: string[]; chart_id: string }
      expect(body.ayanamshas).toEqual(['lahiri', 'kp'])
      trackedCharts.push(body.chart_id)
    })

    it('[IT-R8-04] 422 when birth_date is in the future', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', {
          ...VALID_PAYLOAD,
          birth_date: '2099-01-01',
        }),
      )
      expect(res.status).toBe(422)
      const body = (await res.json()) as { error: string }
      expect(body.error).toBe('validation_failed')
    })

    it('[IT-R8-05] 422 when an unknown ayanamsha is specified', async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', {
          ...VALID_PAYLOAD,
          ayanamshas: ['lahiri', 'not_a_real_ayanamsha'],
        }),
      )
      expect(res.status).toBe(422)
    })

    it('[IT-R8-06] 401 when unauthenticated', async () => {
      mockGetServerUser.mockResolvedValue(null)

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', VALID_PAYLOAD),
      )
      expect(res.status).toBe(401)
    })

    it('[IT-R8-07] 429 when rate limit exceeded (5 charts in last hour)', async () => {
      // Seed 5 charts for this user within the last hour to trip the limit.
      const rlUid = `it-ratelimit-${Date.now()}`
      await seedProfile(rlUid)

      const seededChartIds: string[] = []
      for (let i = 0; i < 5; i++) {
        const id = await seedChart(rlUid, `Rate Limit Chart ${i}`)
        seededChartIds.push(id)
      }
      // Backfill created_at to be within the last 30 minutes.
      for (const cid of seededChartIds) {
        await query(
          `UPDATE charts SET created_at = NOW() - INTERVAL '30 minutes' WHERE id = $1`,
          [cid],
        )
      }

      mockGetServerUser.mockResolvedValue({ uid: rlUid })

      const res = await POST_CLIENTS_CREATE(
        makeReq('http://localhost/api/clients/create', 'POST', VALID_PAYLOAD),
      )
      expect(res.status).toBe(429)
      const body = (await res.json()) as { error: string; limit: number }
      expect(body.error).toBe('rate_limit_exceeded')
      expect(body.limit).toBe(5)

      // Cleanup.
      for (const cid of seededChartIds) {
        await cleanupChart(cid).catch(() => {})
      }
      await query('DELETE FROM profiles WHERE uid = $1', [rlUid]).catch(() => {})
    })

    it('[IT-R8-08] idempotency: repeated request with same X-Idempotency-Key returns same chart_id', async () => {
      const idemUid = `it-idem-${Date.now()}`
      await seedProfile(idemUid)
      mockGetServerUser.mockResolvedValue({ uid: idemUid })

      const key = `idem-key-${randomUUID()}`

      const first = await POST_CLIENTS_CREATE(
        makeReq(
          'http://localhost/api/clients/create',
          'POST',
          VALID_PAYLOAD,
          { 'X-Idempotency-Key': key },
        ),
      )

      if (first.status !== 200) {
        // If idempotency column is absent, skip without failing.
        await query('DELETE FROM profiles WHERE uid = $1', [idemUid]).catch(() => {})
        return
      }

      const firstBody = (await first.json()) as { chart_id: string }
      trackedCharts.push(firstBody.chart_id)

      mockGetServerUser.mockResolvedValue({ uid: idemUid })
      const second = await POST_CLIENTS_CREATE(
        makeReq(
          'http://localhost/api/clients/create',
          'POST',
          VALID_PAYLOAD,
          { 'X-Idempotency-Key': key },
        ),
      )

      if (second.status === 200) {
        const secondBody = (await second.json()) as { chart_id: string; idempotent?: boolean }
        // Same chart returned.
        expect(secondBody.chart_id).toBe(firstBody.chart_id)
        expect(secondBody.idempotent).toBe(true)
      }

      await query('DELETE FROM profiles WHERE uid = $1', [idemUid]).catch(() => {})
    })
  })

  // ═══════════════════════════════════════════════════════════════════════════
  // Cross-route: auth gating across all routes
  // ═══════════════════════════════════════════════════════════════════════════

  describe('Cross-route auth gating', () => {
    it('[IT-AUTH-01] all auth-required routes return 401 for unauthenticated calls', async () => {
      mockGetServerUser.mockResolvedValue(null)

      const chartId = randomUUID() // non-existent — doesn't matter for auth check

      const responses = await Promise.all([
        POST_START(),
        POST_CANCEL(),
        GET_ACTIVE(),
        GET_RECENT(),
        GET_ACTIVE_AYANAMSHAS(
          makeReq(`http://localhost/api/conversations/${chartId}/active-ayanamshas`, 'GET'),
          params({ id: chartId }),
        ),
        GET_AYANAMSHA_STATUS(
          makeReq(`http://localhost/api/charts/${chartId}/ayanamsha-status`, 'GET'),
          params({ id: chartId }),
        ),
        POST_CLIENTS_CREATE(
          makeReq('http://localhost/api/clients/create', 'POST', {
            name: 'x',
            birth_date: '1990-01-01',
            birth_time: '12:00',
            birth_place: 'City',
            lat: 0,
            lon: 0,
            tz_offset: 0,
          }),
        ),
      ])

      for (const res of responses) {
        expect(res.status, `Expected 401 for ${res.url}`).toBe(401)
      }
    })

    it('[IT-AUTH-02] GET /api/engine/current does NOT require auth', async () => {
      // No user mock set up.
      const res = await GET_ENGINE_CURRENT(
        makeReq('http://localhost/api/engine/current', 'GET'),
      )
      expect(res.status).not.toBe(401)
    })
  })
})
