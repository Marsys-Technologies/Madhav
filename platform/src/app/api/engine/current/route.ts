/**
 * GET /api/engine/current
 *
 * Returns the current engine version metadata. Public endpoint — no auth required.
 *
 * Behaviour:
 *   1. Queries engine_versions ordered by created_at DESC LIMIT 1.
 *   2. Returns version metadata: version_id, engine_name, version_str, git_sha,
 *      swisseph_ver, created_at.
 *   3. Returns 404 { error: 'No current engine version found' } if table is empty.
 *   4. Cache-Control: max-age=300 (5 minutes — version changes rarely).
 *
 * [BUILD-ORCH-D-06] /api/engine/current engine version endpoint.
 */

import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

// ─── Response shape ──────────────────────────────────────────────────────────

interface EngineVersionResponse {
  version_id: string
  engine_name: string
  version: string
  status: string
  promoted_at: string
  git_sha: string | null
  swisseph_ver: string | null
  jh_parity_sha: string | null
  release_notes_uri: string | null
}

// ─── DB row type ──────────────────────────────────────────────────────────────

interface EngineVersionRow {
  version_id: string
  engine_name: string
  version_str: string
  git_sha: string | null
  swisseph_ver: string | null
  created_at: string
}

// ─── Handler ─────────────────────────────────────────────────────────────────

export async function GET(_request: Request): Promise<Response> {
  const result = await query<EngineVersionRow>(
    `SELECT version_id, engine_name, version_str, git_sha, swisseph_ver, created_at
     FROM engine_versions
     ORDER BY created_at DESC
     LIMIT 1`,
    [],
  )

  if (result.rows.length === 0) {
    return NextResponse.json(
      { error: 'No current engine version found' },
      { status: 404 },
    )
  }

  const row = result.rows[0]

  const body: EngineVersionResponse = {
    version_id: row.version_id,
    engine_name: row.engine_name,
    version: row.version_str,
    status: 'current',
    promoted_at: row.created_at,
    git_sha: row.git_sha ?? null,
    swisseph_ver: row.swisseph_ver ?? null,
    jh_parity_sha: null,
    release_notes_uri: null,
  }

  return NextResponse.json(body, {
    status: 200,
    headers: {
      'Cache-Control': 'max-age=300',
    },
  })
}
