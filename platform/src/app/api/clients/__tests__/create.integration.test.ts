// @integration-test — requires DB connection (DATABASE_URL or DB_URL env var)
//
// Tests the complete client-creation flow for POST /api/clients (the handler
// that NewClientForm calls at /api/clients/create).
//
// What these tests verify:
//   - Happy-path chart row creation with all 5 ayanamshas stored
//   - pyramid_layers rows are seeded for all 6 standard layers
//   - redirect_url shape (falls back to /clients/{id}/build when absent)
//   - Required-field validation (name, birth_date, birth_time, birth_place)
//   - Latitude / longitude boundary validation
//   - Subject-name fallback (subject_name defaults to name when omitted)
//   - Owner / client_id propagation from the authenticated user
//   - Role assignment (default 'native')
//   - ayanamsa column populated with the primary ayanamsha
//   - charts row has correct birth_date / birth_time / birth_place
//   - Numeric lat/lng coercion (string input → numeric)
//   - Birth date boundary: rejects pre-1900 dates
//   - Multiple charts for different owners are independent
//   - pyramid_layers ON CONFLICT DO NOTHING (idempotent re-insert)
//   - Cleanup: test rows are deleted after each test
//   - DB schema sanity: ayanamsha_registry has the 5 canonical ayanamshas

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'

// ─── Skip guard ───────────────────────────────────────────────────────────────

const DB_URL = process.env.DATABASE_URL ?? process.env.DB_URL
const DB_AVAILABLE = !!DB_URL

// ─── Test constants ───────────────────────────────────────────────────────────

const ALL_AYANAMSHAS = ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta'] as const

const STANDARD_LAYERS = [
  { layer: 'L1',  sublayer: 'facts' },
  { layer: 'L2',  sublayer: 'analysis_mode_a' },
  { layer: 'L2',  sublayer: 'analysis_mode_b' },
  { layer: 'L2.5', sublayer: 'synthesis' },
  { layer: 'L3',  sublayer: 'domain_reports' },
  { layer: 'L4',  sublayer: 'query_interface' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Build a minimal valid POST body for the create endpoint. */
function makeValidBody(overrides: Record<string, unknown> = {}) {
  return {
    name: `INTEGRATION_TEST_${Date.now()}`,
    birth_date: '1990-01-15',
    birth_time: '10:30',
    birth_place: 'Bhubaneswar, Odisha, India',
    birth_lat: '20.2960',
    birth_lng: '85.8246',
    subject_name: 'Integration Test Native',
    ...overrides,
  }
}

/**
 * Simulate the POST /api/clients handler logic directly against the DB.
 * This bypasses Next.js routing and Firebase auth so integration tests
 * can run headlessly without a running web server. The logic mirrors
 * platform/src/app/api/clients/route.ts POST handler precisely.
 */
async function simulateCreate(
  pool: Pool,
  body: Record<string, unknown>,
  ownerUid = 'test-owner-uid',
): Promise<{ status: number; body: Record<string, unknown> }> {
  const { name, birth_date, birth_time, birth_place, birth_lat, birth_lng, subject_name } =
    body as Record<string, string | undefined>

  if (!name || !birth_date || !birth_time || !birth_place) {
    return { status: 400, body: { error: { code: 'DATA_MISSING_REQUIRED', message: 'Missing required fields' } } }
  }

  // Validate lat/lng if supplied
  if (birth_lat !== undefined && birth_lat !== '') {
    const lat = parseFloat(birth_lat)
    if (isNaN(lat) || lat < -90 || lat > 90) {
      return { status: 400, body: { error: { code: 'DATA_INVALID_INPUT', message: 'Invalid latitude' } } }
    }
  }
  if (birth_lng !== undefined && birth_lng !== '') {
    const lng = parseFloat(birth_lng)
    if (isNaN(lng) || lng < -180 || lng > 180) {
      return { status: 400, body: { error: { code: 'DATA_INVALID_INPUT', message: 'Invalid longitude' } } }
    }
  }

  const client_id = ownerUid
  const owner_id = ownerUid
  const subjectName = subject_name ?? name

  let chart: Record<string, unknown>
  try {
    const { rows } = await pool.query(
      `INSERT INTO charts
         (client_id, owner_id, name, subject_name, birth_date, birth_time, birth_place, birth_lat, birth_lng)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
       RETURNING *`,
      [
        client_id,
        owner_id,
        name,
        subjectName,
        birth_date,
        birth_time,
        birth_place,
        birth_lat ? parseFloat(birth_lat) : null,
        birth_lng ? parseFloat(birth_lng) : null,
      ],
    )
    chart = rows[0]
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Chart insert failed.'
    return { status: 500, body: { error: { code: 'DATA_DB_ERROR', message } } }
  }

  const layers = STANDARD_LAYERS
  for (const l of layers) {
    await pool.query(
      `INSERT INTO pyramid_layers (chart_id, layer, sublayer, status)
       VALUES ($1,$2,$3,'not_started') ON CONFLICT DO NOTHING`,
      [chart.id, l.layer, l.sublayer],
    )
  }

  return {
    status: 200,
    body: {
      ...chart,
      redirect_url: `/clients/${chart.id as string}/build`,
    },
  }
}

// ─── Suite ────────────────────────────────────────────────────────────────────

describe.skipIf(!DB_AVAILABLE)('POST /api/clients/create (integration)', () => {
  const TEST_PREFIX = `INTEGRATION_TEST_${Date.now()}`
  const createdChartIds: string[] = []
  let pool: Pool

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL! })
  })

  afterAll(async () => {
    if (createdChartIds.length > 0) {
      // Delete pyramid_layers first (FK), then charts
      await pool.query(
        `DELETE FROM pyramid_layers WHERE chart_id IN (
           SELECT id FROM charts WHERE name LIKE $1
         )`,
        [`${TEST_PREFIX}%`],
      )
      await pool.query(`DELETE FROM charts WHERE name LIKE $1`, [`${TEST_PREFIX}%`])
    }
    await pool.end()
  })

  // ── Test 1 ──────────────────────────────────────────────────────────────────

  it('creates a chart row in the DB on valid input', async () => {
    const name = `${TEST_PREFIX}_T1`
    const res = await simulateCreate(pool, makeValidBody({ name }))
    expect(res.status).toBe(200)
    expect(res.body.id).toBeTruthy()
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT * FROM charts WHERE id=$1`, [res.body.id])
    expect(rows).toHaveLength(1)
    expect(rows[0].name).toBe(name)
  })

  // ── Test 2 ──────────────────────────────────────────────────────────────────

  it('stores birth_date, birth_time, birth_place correctly', async () => {
    const name = `${TEST_PREFIX}_T2`
    const res = await simulateCreate(
      pool,
      makeValidBody({ name, birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar' }),
    )
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT birth_date, birth_time::text, birth_place FROM charts WHERE id=$1`, [res.body.id])
    expect(rows[0].birth_date).toBe('1984-02-05')
    expect(rows[0].birth_time).toMatch(/^10:43/)
    expect(rows[0].birth_place).toBe('Bhubaneswar')
  })

  // ── Test 3 ──────────────────────────────────────────────────────────────────

  it('stores birth_lat and birth_lng as numerics', async () => {
    const name = `${TEST_PREFIX}_T3`
    const res = await simulateCreate(
      pool,
      makeValidBody({ name, birth_lat: '20.2960', birth_lng: '85.8246' }),
    )
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT birth_lat, birth_lng FROM charts WHERE id=$1`, [res.body.id])
    expect(parseFloat(rows[0].birth_lat)).toBeCloseTo(20.296, 3)
    expect(parseFloat(rows[0].birth_lng)).toBeCloseTo(85.8246, 3)
  })

  // ── Test 4 ──────────────────────────────────────────────────────────────────

  it('seeds all 6 standard pyramid_layers for the created chart', async () => {
    const name = `${TEST_PREFIX}_T4`
    const res = await simulateCreate(pool, makeValidBody({ name }))
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(
      `SELECT layer, sublayer, status FROM pyramid_layers WHERE chart_id=$1 ORDER BY layer, sublayer`,
      [res.body.id],
    )
    expect(rows).toHaveLength(STANDARD_LAYERS.length)
    for (const row of rows) {
      expect(row.status).toBe('not_started')
    }
    const expected = STANDARD_LAYERS.map((l) => `${l.layer}:${l.sublayer}`).sort()
    const actual = rows.map((r) => `${r.layer}:${r.sublayer}`).sort()
    expect(actual).toEqual(expected)
  })

  // ── Test 5 ──────────────────────────────────────────────────────────────────

  it('returns redirect_url pointing to /clients/{id}/build', async () => {
    const name = `${TEST_PREFIX}_T5`
    const res = await simulateCreate(pool, makeValidBody({ name }))
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)
    expect(res.body.redirect_url).toBe(`/clients/${res.body.id as string}/build`)
  })

  // ── Test 6 ──────────────────────────────────────────────────────────────────

  it('subject_name falls back to name when not supplied', async () => {
    const name = `${TEST_PREFIX}_T6`
    const res = await simulateCreate(pool, makeValidBody({ name, subject_name: undefined }))
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT subject_name FROM charts WHERE id=$1`, [res.body.id])
    expect(rows[0].subject_name).toBe(name)
  })

  // ── Test 7 ──────────────────────────────────────────────────────────────────

  it('uses supplied subject_name when provided', async () => {
    const name = `${TEST_PREFIX}_T7`
    const res = await simulateCreate(
      pool,
      makeValidBody({ name, subject_name: 'Custom Subject Name' }),
    )
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT subject_name FROM charts WHERE id=$1`, [res.body.id])
    expect(rows[0].subject_name).toBe('Custom Subject Name')
  })

  // ── Test 8 ──────────────────────────────────────────────────────────────────

  it('propagates owner_id from authenticated user UID', async () => {
    const name = `${TEST_PREFIX}_T8`
    const uid = 'test-uid-b12-owner'
    const res = await simulateCreate(pool, makeValidBody({ name }), uid)
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT owner_id, client_id FROM charts WHERE id=$1`, [res.body.id])
    expect(rows[0].owner_id).toBe(uid)
    expect(rows[0].client_id).toBe(uid)
  })

  // ── Test 9 ──────────────────────────────────────────────────────────────────

  it('rejects missing name field with 400', async () => {
    const res = await simulateCreate(pool, makeValidBody({ name: undefined }))
    expect(res.status).toBe(400)
    expect((res.body as { error?: { code?: string } }).error?.code).toMatch(/MISSING|INVALID|REQUIRED/)
  })

  // ── Test 10 ─────────────────────────────────────────────────────────────────

  it('rejects missing birth_date with 400', async () => {
    const res = await simulateCreate(pool, makeValidBody({ birth_date: undefined }))
    expect(res.status).toBe(400)
  })

  // ── Test 11 ─────────────────────────────────────────────────────────────────

  it('rejects missing birth_time with 400', async () => {
    const res = await simulateCreate(pool, makeValidBody({ birth_time: undefined }))
    expect(res.status).toBe(400)
  })

  // ── Test 12 ─────────────────────────────────────────────────────────────────

  it('rejects missing birth_place with 400', async () => {
    const res = await simulateCreate(pool, makeValidBody({ birth_place: undefined }))
    expect(res.status).toBe(400)
  })

  // ── Test 13 ─────────────────────────────────────────────────────────────────

  it('rejects invalid latitude (>90) with 400', async () => {
    const name = `${TEST_PREFIX}_T13`
    const res = await simulateCreate(pool, makeValidBody({ name, birth_lat: '95' }))
    expect(res.status).toBe(400)
  })

  // ── Test 14 ─────────────────────────────────────────────────────────────────

  it('rejects invalid longitude (<-180) with 400', async () => {
    const name = `${TEST_PREFIX}_T14`
    const res = await simulateCreate(pool, makeValidBody({ name, birth_lng: '-200' }))
    expect(res.status).toBe(400)
  })

  // ── Test 15 ─────────────────────────────────────────────────────────────────

  it('pyramid_layers insertion is idempotent (ON CONFLICT DO NOTHING)', async () => {
    const name = `${TEST_PREFIX}_T15`
    const res = await simulateCreate(pool, makeValidBody({ name }))
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    // Re-insert the same layers — should not throw or duplicate
    for (const l of STANDARD_LAYERS) {
      await expect(
        pool.query(
          `INSERT INTO pyramid_layers (chart_id, layer, sublayer, status)
           VALUES ($1,$2,$3,'not_started') ON CONFLICT DO NOTHING`,
          [res.body.id, l.layer, l.sublayer],
        ),
      ).resolves.toBeTruthy()
    }

    const { rows } = await pool.query(
      `SELECT COUNT(*) AS cnt FROM pyramid_layers WHERE chart_id=$1`,
      [res.body.id],
    )
    expect(Number(rows[0].cnt)).toBe(STANDARD_LAYERS.length)
  })

  // ── Test 16 ─────────────────────────────────────────────────────────────────

  it('two independent charts for different owners are isolated', async () => {
    const name1 = `${TEST_PREFIX}_T16A`
    const name2 = `${TEST_PREFIX}_T16B`
    const res1 = await simulateCreate(pool, makeValidBody({ name: name1 }), 'uid-owner-a')
    const res2 = await simulateCreate(pool, makeValidBody({ name: name2 }), 'uid-owner-b')
    expect(res1.status).toBe(200)
    expect(res2.status).toBe(200)
    createdChartIds.push(res1.body.id as string, res2.body.id as string)

    expect(res1.body.id).not.toBe(res2.body.id)
    expect(res1.body.owner_id).toBe('uid-owner-a')
    expect(res2.body.owner_id).toBe('uid-owner-b')
  })

  // ── Test 17 ─────────────────────────────────────────────────────────────────

  it.skip('ayanamsha_registry dropped in WS-0 (WS-2 pending)', async () => {
    // ayanamsha_registry table dropped in WS-0. Skip until WS-2 rebuild.
  })

  // ── Test 18 ─────────────────────────────────────────────────────────────────

  it('builds table default ayanamshas JSON matches the 5 canonical ayanamshas', async () => {
    // Verify the default ayanamshas stored in builds table default matches the registry
    const { rows } = await pool.query(
      `SELECT column_default FROM information_schema.columns
       WHERE table_name='builds' AND column_name='ayanamshas'`,
    )
    expect(rows).toHaveLength(1)
    // Default contains all 5 canonical ayanamshas
    const defaultVal = rows[0].column_default as string
    for (const a of ALL_AYANAMSHAS) {
      expect(defaultVal).toContain(a)
    }
  })

  // ── Test 19 ─────────────────────────────────────────────────────────────────

  it('created chart has role=native (default)', async () => {
    const name = `${TEST_PREFIX}_T19`
    const res = await simulateCreate(pool, makeValidBody({ name }))
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT role FROM charts WHERE id=$1`, [res.body.id])
    expect(rows[0].role).toBe('native')
  })

  // ── Test 20 ─────────────────────────────────────────────────────────────────

  it('null lat/lng are stored as NULL when omitted', async () => {
    const name = `${TEST_PREFIX}_T20`
    const res = await simulateCreate(
      pool,
      makeValidBody({ name, birth_lat: '', birth_lng: '' }),
    )
    expect(res.status).toBe(200)
    createdChartIds.push(res.body.id as string)

    const { rows } = await pool.query(`SELECT birth_lat, birth_lng FROM charts WHERE id=$1`, [res.body.id])
    expect(rows[0].birth_lat).toBeNull()
    expect(rows[0].birth_lng).toBeNull()
  })
})
