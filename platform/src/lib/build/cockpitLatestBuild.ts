import 'server-only'
import { query } from '@/lib/db/client'

/** Observed latest-run metadata only; callers authorize chart/build access first. */
export async function readCockpitLatestBuild(id: string) {
  let latestBuild: { build_id: string; status: string; created_at: string } | null = null
  let latestBuildUnavailable = false
  try {
    const { rows: buildRows } = await query<{
      build_id: string
      status: string
      created_at: string
    }>(
      `SELECT id AS build_id, state AS status, created_at
       FROM build_runs WHERE chart_id=$1 ORDER BY created_at DESC LIMIT 1`,
      [id],
    )
    latestBuild = buildRows[0] ?? null
  } catch {
    latestBuildUnavailable = true
  }
  return { latestBuild, latestBuildUnavailable }
}
