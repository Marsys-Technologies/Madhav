/**
 * POST /api/build/mark-viewed
 *
 * Marks one or more builds as seen by the authenticated user.
 * Inserts rows into notification_views (ON CONFLICT DO NOTHING — idempotent).
 *
 * Request body: { build_ids: string[], source?: 'toast' | 'dashboard' | 'email' | 'push' }
 * Response: { marked: number }
 *
 * Auth: Firebase UID required — 401 if unauthenticated.
 * [BUILD-ORCH-I-03]
 */

import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

type Source = 'toast' | 'dashboard' | 'email' | 'push'

interface MarkViewedBody {
  build_ids?: string[]
  source?: Source
}

const VALID_SOURCES: Source[] = ['toast', 'dashboard', 'email', 'push']

export async function POST(request: Request): Promise<Response> {
  const user = await getServerUser()
  if (!user) {
    return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })
  }

  let body: MarkViewedBody = {}
  try {
    body = (await request.json()) as MarkViewedBody
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 })
  }

  const buildIds = body.build_ids
  if (!Array.isArray(buildIds) || buildIds.length === 0) {
    return NextResponse.json({ error: 'build_ids must be a non-empty array' }, { status: 400 })
  }

  // Validate all entries are non-empty strings
  const invalidEntry = buildIds.find((id) => typeof id !== 'string' || id.trim() === '')
  if (invalidEntry !== undefined) {
    return NextResponse.json({ error: 'all build_ids must be non-empty strings' }, { status: 400 })
  }

  const source: Source | null =
    body.source && VALID_SOURCES.includes(body.source) ? body.source : null

  // Insert one row per build_id, ON CONFLICT DO NOTHING (idempotent)
  // We use unnest to batch-insert efficiently.
  const result = await query<{ count: string }>(
    `
    INSERT INTO notification_views (build_id, user_id, source)
    SELECT
      unnest($1::uuid[]),
      $2::text,
      $3::text
    ON CONFLICT ON CONSTRAINT nv_unique_per_user DO NOTHING
    `,
    [buildIds, user.uid, source],
  )

  // rowCount reflects actual inserts (skips already-viewed)
  const marked = result.rowCount ?? 0

  return NextResponse.json({ marked })
}
