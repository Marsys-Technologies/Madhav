import 'server-only'
import { query } from '@/lib/db/client'

/** Legacy compatibility checkpoint context; not canonical chart readiness. */
export async function readLegacyConsultReadinessNote(chartId: string): Promise<string | undefined> {
  let dataReadinessNote: string | undefined
  try {
    const latestBuildRes = await query<{ build_id: string }>(
      `SELECT build_id FROM build_events WHERE chart_id = $1 ORDER BY emitted_at DESC LIMIT 1`,
      [chartId],
    )
    const latestBuildId = latestBuildRes.rows[0]?.build_id
    if (latestBuildId) {
      const checkpointsRes = await query<{ asset_id: string; status: string }>(
        `SELECT DISTINCT ON (asset_id) asset_id, status
           FROM build_checkpoints
          WHERE build_id = $1
          ORDER BY asset_id, completed_at DESC NULLS LAST`,
        [latestBuildId],
      )
      if (checkpointsRes.rows.length > 0) {
        const readyAssets = checkpointsRes.rows
          .filter(r => r.status === 'success')
          .map(r => r.asset_id)
        const missingAssets = checkpointsRes.rows
          .filter(r => r.status !== 'success')
          .map(r => r.asset_id)
        const total = checkpointsRes.rows.length
        if (missingAssets.length > 0) {
          dataReadinessNote = [
            `Legacy checkpoint summary: observed asset checkpoint results.`,
            `Observed asset checkpoints reporting success: [${readyAssets.join(', ')}].`,
            `Observed asset checkpoints not reporting success: [${missingAssets.join(', ')}].`,
            `Do NOT hallucinate data for unbuilt assets — say "data not yet available" for those domains.`,
            `(${readyAssets.length} of ${total} observed asset checkpoints report success)`,
            `Completeness across current chart assets/data domains is not established.`,
          ].join(' ')
        } else {
          dataReadinessNote = `Legacy checkpoint summary: all ${total} observed asset checkpoints report success. Completeness across current chart assets/data domains is not established.`
        }
      }
    }
  } catch {
    // Non-fatal: readiness check failure does not block synthesis
  }
  return dataReadinessNote
}
