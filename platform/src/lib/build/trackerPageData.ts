import 'server-only'
import { query } from '@/lib/db/client'

/** Build tracker reads only; the page admits the operator before calling. */
// ── DB types ──────────────────────────────────────────────────────────────────

export interface BuildRow {
  build_id: string
  chart_id: string
  chart_name: string | null
  status: string
  queued_at: string | null
  started_at: string | null
  finished_at: string | null
  ayanamsha_ids: string | null
  steps_complete: number
  steps_total: number
  engine_version: string | null
}

export interface AyanamshaMatrixRow {
  chart_id: string
  chart_name: string | null
  ayanamsha_id: string
  status: string
  finished_at: string | null
}

// ── Data fetchers ─────────────────────────────────────────────────────────────

export async function fetchActiveBuilds(): Promise<BuildRow[] | null> {
  try {
    const { rows } = await query<BuildRow>(
      `SELECT
         b.id AS build_id,
         b.chart_id,
         c.subject_name AS chart_name,
         b.state AS status,
         b.created_at AS queued_at,
         b.started_at,
         b.ended_at AS finished_at,
         NULL::text AS ayanamsha_ids,
         NULL::text AS engine_version,
         COUNT(bra.asset_id) FILTER (WHERE bra.state = 'complete')::int AS steps_complete,
         COUNT(bra.asset_id)::int AS steps_total
       FROM build_runs b
       LEFT JOIN charts c ON c.id = b.chart_id
       LEFT JOIN build_run_assets bra ON bra.run_id = b.id
      WHERE b.state IN ('planned', 'running', 'paused')
      GROUP BY b.id, c.subject_name
      ORDER BY b.created_at DESC
      LIMIT 20`,
      [],
    )
    return rows
  } catch {
    return null
  }
}

export async function fetchRecentBuilds(): Promise<BuildRow[] | null> {
  try {
    const { rows } = await query<BuildRow>(
      `SELECT
         b.id AS build_id,
         b.chart_id,
         c.subject_name AS chart_name,
         b.state AS status,
         b.created_at AS queued_at,
         b.started_at,
         b.ended_at AS finished_at,
         NULL::text AS ayanamsha_ids,
         NULL::text AS engine_version,
         COUNT(bra.asset_id) FILTER (WHERE bra.state = 'complete')::int AS steps_complete,
         COUNT(bra.asset_id)::int AS steps_total
       FROM build_runs b
       LEFT JOIN charts c ON c.id = b.chart_id
       LEFT JOIN build_run_assets bra ON bra.run_id = b.id
      WHERE b.state IN ('completed', 'failed', 'stopped')
        AND b.ended_at >= NOW() - INTERVAL '24 hours'
      GROUP BY b.id, c.subject_name
      ORDER BY b.ended_at DESC
      LIMIT 30`,
      [],
    )
    return rows
  } catch {
    return null
  }
}

export async function fetchAyanamshaMatrix(): Promise<AyanamshaMatrixRow[] | null> {
  // Ayanamsha-per-build tracking removed with decommissioning of `builds` table.
  return null
}

