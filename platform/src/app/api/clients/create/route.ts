/**
 * POST /api/clients/create
 *
 * Hardened chart-creation endpoint with:
 *   1. Authentication — 401 if not authenticated.
 *   2. Rate limiting — max 5 chart creates per user per hour (owner_id window).
 *      429 with retry_after seconds if exceeded.
 *   3. Input validation — structured 422 on any field error.
 *   4. Idempotency — X-Idempotency-Key header support; idempotency_key column
 *      used if present in charts table, gracefully skipped if absent.
 *   5. Chart creation — inserts into charts + pyramid_layers.
 *      Returns { chart_id, client_id, redirect_url, ayanamshas }.
 *
 * [BUILD-ORCH-D-05]
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// ─── Constants ───────────────────────────────────────────────────────────────

export const VALID_AYANAMSHAS = [
  'lahiri',
  'true_chitra',
  'kp',
  'raman',
  'surya_siddhanta',
] as const

export type Ayanamsha = (typeof VALID_AYANAMSHAS)[number]
export const DEFAULT_AYANAMSHAS: Ayanamsha[] = [...VALID_AYANAMSHAS]

const RATE_LIMIT_MAX = 5
const RATE_LIMIT_WINDOW_SECONDS = 3600 // 1 hour

const VALID_AYANAMSHA_SET = new Set<string>(VALID_AYANAMSHAS)
const VALID_GENDERS = new Set(['M', 'F', 'O', 'unknown'])

// ─── Types ───────────────────────────────────────────────────────────────────

interface ValidationError {
  field: string
  message: string
}

interface CreateRequestBody {
  name?: unknown
  birth_date?: unknown
  birth_time?: unknown
  birth_place?: unknown
  lat?: unknown
  lon?: unknown
  tz_offset?: unknown
  ayanamshas?: unknown
  gender?: unknown
  subject_name?: unknown
}

// ─── Validation helpers ───────────────────────────────────────────────────────

function validateBody(body: CreateRequestBody): ValidationError[] {
  const errors: ValidationError[] = []

  // name
  if (body.name === undefined || body.name === null || body.name === '') {
    errors.push({ field: 'name', message: 'name is required' })
  } else if (typeof body.name !== 'string') {
    errors.push({ field: 'name', message: 'name must be a string' })
  } else if (body.name.trim().length === 0) {
    errors.push({ field: 'name', message: 'name must not be empty' })
  } else if (body.name.length > 200) {
    errors.push({ field: 'name', message: 'name must be at most 200 characters' })
  }

  // birth_date
  if (body.birth_date === undefined || body.birth_date === null || body.birth_date === '') {
    errors.push({ field: 'birth_date', message: 'birth_date is required' })
  } else if (typeof body.birth_date !== 'string') {
    errors.push({ field: 'birth_date', message: 'birth_date must be a string' })
  } else {
    const isoDateRe = /^\d{4}-\d{2}-\d{2}$/
    if (!isoDateRe.test(body.birth_date)) {
      errors.push({ field: 'birth_date', message: 'birth_date must be in YYYY-MM-DD format' })
    } else {
      const d = new Date(body.birth_date + 'T00:00:00Z')
      if (isNaN(d.getTime())) {
        errors.push({ field: 'birth_date', message: 'birth_date is not a valid date' })
      } else if (d < new Date('1900-01-01T00:00:00Z')) {
        errors.push({ field: 'birth_date', message: 'birth_date must be 1900-01-01 or later' })
      } else if (d > new Date()) {
        errors.push({ field: 'birth_date', message: 'birth_date must not be in the future' })
      }
    }
  }

  // birth_time
  if (body.birth_time === undefined || body.birth_time === null || body.birth_time === '') {
    errors.push({ field: 'birth_time', message: 'birth_time is required' })
  } else if (typeof body.birth_time !== 'string') {
    errors.push({ field: 'birth_time', message: 'birth_time must be a string' })
  } else {
    const timeRe = /^\d{2}:\d{2}(:\d{2})?$/
    if (!timeRe.test(body.birth_time)) {
      errors.push({ field: 'birth_time', message: 'birth_time must be HH:MM or HH:MM:SS format' })
    }
  }

  // birth_place
  if (body.birth_place === undefined || body.birth_place === null || body.birth_place === '') {
    errors.push({ field: 'birth_place', message: 'birth_place is required' })
  } else if (typeof body.birth_place !== 'string') {
    errors.push({ field: 'birth_place', message: 'birth_place must be a string' })
  } else if (body.birth_place.trim().length === 0) {
    errors.push({ field: 'birth_place', message: 'birth_place must not be empty' })
  }

  // lat
  if (body.lat === undefined || body.lat === null) {
    errors.push({ field: 'lat', message: 'lat is required' })
  } else {
    const lat = Number(body.lat)
    if (isNaN(lat)) {
      errors.push({ field: 'lat', message: 'lat must be a number' })
    } else if (lat < -90 || lat > 90) {
      errors.push({ field: 'lat', message: 'lat must be between -90 and 90' })
    }
  }

  // lon
  if (body.lon === undefined || body.lon === null) {
    errors.push({ field: 'lon', message: 'lon is required' })
  } else {
    const lon = Number(body.lon)
    if (isNaN(lon)) {
      errors.push({ field: 'lon', message: 'lon must be a number' })
    } else if (lon < -180 || lon > 180) {
      errors.push({ field: 'lon', message: 'lon must be between -180 and 180' })
    }
  }

  // tz_offset
  if (body.tz_offset === undefined || body.tz_offset === null) {
    errors.push({ field: 'tz_offset', message: 'tz_offset is required' })
  } else {
    const tz = Number(body.tz_offset)
    if (isNaN(tz)) {
      errors.push({ field: 'tz_offset', message: 'tz_offset must be a number' })
    } else if (tz < -14 || tz > 14) {
      errors.push({ field: 'tz_offset', message: 'tz_offset must be between -14 and 14' })
    }
  }

  // ayanamshas (optional)
  if (body.ayanamshas !== undefined && body.ayanamshas !== null) {
    if (!Array.isArray(body.ayanamshas)) {
      errors.push({ field: 'ayanamshas', message: 'ayanamshas must be an array' })
    } else if (body.ayanamshas.length === 0) {
      errors.push({ field: 'ayanamshas', message: 'ayanamshas must not be empty if provided' })
    } else {
      const invalid = (body.ayanamshas as unknown[]).filter(
        (a) => typeof a !== 'string' || !VALID_AYANAMSHA_SET.has(a as string),
      )
      if (invalid.length > 0) {
        errors.push({
          field: 'ayanamshas',
          message: `Unknown ayanamsha value(s): ${invalid.join(', ')}`,
        })
      }
    }
  }

  // gender (optional)
  if (body.gender !== undefined && body.gender !== null) {
    if (typeof body.gender !== 'string' || !VALID_GENDERS.has(body.gender)) {
      errors.push({
        field: 'gender',
        message: `gender must be one of: ${[...VALID_GENDERS].join(', ')}`,
      })
    }
  }

  return errors
}

// ─── Column existence cache ───────────────────────────────────────────────────
// Cached at module level so the introspection query runs at most once per
// process lifetime. Safe because schema changes require a deploy.

let _idempotencyColumnExists: boolean | null = null

async function idempotencyColumnExists(): Promise<boolean> {
  if (_idempotencyColumnExists !== null) return _idempotencyColumnExists
  try {
    const { rows } = await query<{ exists: boolean }>(
      `SELECT EXISTS (
         SELECT 1 FROM information_schema.columns
         WHERE table_name = 'charts' AND column_name = 'idempotency_key'
       ) AS exists`,
    )
    _idempotencyColumnExists = rows[0]?.exists ?? false
  } catch {
    _idempotencyColumnExists = false
  }
  return _idempotencyColumnExists
}

// ─── Handler ─────────────────────────────────────────────────────────────────

export async function POST(request: Request): Promise<Response> {
  // ── Auth ───────────────────────────────────────────────────────────────────
  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })
  }

  // ── Parse body ─────────────────────────────────────────────────────────────
  let body: CreateRequestBody = {}
  try {
    body = (await request.json()) as CreateRequestBody
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 })
  }

  // ── Input validation ───────────────────────────────────────────────────────
  const validationErrors = validateBody(body)
  if (validationErrors.length > 0) {
    return NextResponse.json(
      { error: 'validation_failed', errors: validationErrors },
      { status: 422 },
    )
  }

  // Coerce validated fields
  const name = (body.name as string).trim()
  const birth_date = body.birth_date as string
  const birth_time = body.birth_time as string
  const birth_place = (body.birth_place as string).trim()
  const lat = Number(body.lat)
  const lon = Number(body.lon)
  const subject_name = typeof body.subject_name === 'string' ? body.subject_name.trim() : name

  const ayanamshas: Ayanamsha[] =
    body.ayanamshas === undefined || body.ayanamshas === null
      ? DEFAULT_AYANAMSHAS
      : (body.ayanamshas as string[]).map((a) => a as Ayanamsha)

  // ── Rate limiting ──────────────────────────────────────────────────────────
  const rateLimitResult = await query<{ count: string; oldest_created_at: string | null }>(
    `SELECT COUNT(*) AS count, MIN(created_at) AS oldest_created_at
     FROM charts
     WHERE owner_id = $1 AND created_at >= NOW() - INTERVAL '1 hour'`,
    [user.uid],
  )
  const recentCount = parseInt(rateLimitResult.rows[0]?.count ?? '0', 10)

  if (recentCount >= RATE_LIMIT_MAX) {
    const oldestCreatedAt = rateLimitResult.rows[0]?.oldest_created_at
    let retryAfter = RATE_LIMIT_WINDOW_SECONDS
    if (oldestCreatedAt) {
      const oldestMs = new Date(oldestCreatedAt).getTime()
      const expiresMs = oldestMs + RATE_LIMIT_WINDOW_SECONDS * 1000
      retryAfter = Math.max(0, Math.ceil((expiresMs - Date.now()) / 1000))
    }
    return NextResponse.json(
      {
        error: 'rate_limit_exceeded',
        limit: RATE_LIMIT_MAX,
        window: '1 hour',
        retry_after: retryAfter,
      },
      { status: 429 },
    )
  }

  // ── Idempotency key check ──────────────────────────────────────────────────
  const idempotencyKey = request.headers.get('X-Idempotency-Key')
  const hasIdempotencyColumn = await idempotencyColumnExists()

  if (idempotencyKey && hasIdempotencyColumn) {
    const existing = await query<{ chart_id: string; client_id: string }>(
      'SELECT chart_id, client_id FROM charts WHERE owner_id=$1 AND idempotency_key=$2 LIMIT 1',
      [user.uid, idempotencyKey],
    )
    if (existing.rows[0]) {
      const row = existing.rows[0]
      return NextResponse.json({
        chart_id: row.chart_id,
        client_id: row.client_id ?? null,
        redirect_url: `/clients/${row.chart_id}/build`,
        ayanamshas,
        idempotent: true,
      })
    }
  }

  // ── Insert chart ───────────────────────────────────────────────────────────
  const owner_id = user.uid
  const client_id = user.uid // legacy column; identical to owner_id during cutover window

  let chart: Record<string, unknown>
  try {
    if (hasIdempotencyColumn && idempotencyKey) {
      const { rows } = await query(
        `INSERT INTO charts
           (client_id, owner_id, name, subject_name, birth_date, birth_time,
            birth_place, birth_lat, birth_lng, idempotency_key)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
         RETURNING *`,
        [
          client_id,
          owner_id,
          name,
          subject_name,
          birth_date,
          birth_time,
          birth_place,
          lat,
          lon,
          idempotencyKey,
        ],
      )
      chart = rows[0]
    } else {
      const { rows } = await query(
        `INSERT INTO charts
           (client_id, owner_id, name, subject_name, birth_date, birth_time,
            birth_place, birth_lat, birth_lng)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
         RETURNING *`,
        [client_id, owner_id, name, subject_name, birth_date, birth_time, birth_place, lat, lon],
      )
      chart = rows[0]
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Chart insert failed.'
    console.error('[api/clients/create] chart INSERT failed', err)
    return NextResponse.json({ error: 'db_error', message }, { status: 500 })
  }

  // ── Seed pyramid_layers ────────────────────────────────────────────────────
  const layers = [
    { layer: 'L1', sublayer: 'facts' },
    { layer: 'L2', sublayer: 'analysis_mode_a' },
    { layer: 'L2', sublayer: 'analysis_mode_b' },
    { layer: 'L2.5', sublayer: 'synthesis' },
    { layer: 'L3', sublayer: 'domain_reports' },
    { layer: 'L4', sublayer: 'query_interface' },
  ]

  try {
    for (const l of layers) {
      await query(
        `INSERT INTO pyramid_layers (chart_id, layer, sublayer, status)
         VALUES ($1,$2,$3,'not_started') ON CONFLICT DO NOTHING`,
        [chart.id, l.layer, l.sublayer],
      )
    }
  } catch (err) {
    await query('DELETE FROM charts WHERE id=$1', [chart.id]).catch(() => {})
    const message = err instanceof Error ? err.message : 'Layer insert failed.'
    console.error('[api/clients/create] pyramid_layers INSERT failed', err)
    return NextResponse.json({ error: 'db_error', message }, { status: 500 })
  }

  // ── Response ───────────────────────────────────────────────────────────────
  return NextResponse.json({
    chart_id: chart.chart_id as string,
    client_id: chart.client_id as string,
    redirect_url: `/clients/${chart.chart_id as string}/build`,
    ayanamshas,
  })
}
