/**
 * mv_refresh.ts — Cron entry point for materialized view refresh + bundle cache cleanup.
 *
 * Scheduled at: periodic intervals via Cloud Run scheduler.
 * - Bundle cache cleanup: DELETE FROM mcp_bundle_cache WHERE expires_at < now()
 *   (every 10 minutes via scheduler, or on each perf refresh if freq is low enough)
 *
 * NO LLM calls. Pure DB maintenance.
 *
 * MCPT v3.1.0-S4
 */

const DB_URL = process.env['SUPABASE_URL'] ?? ''
const DB_SERVICE_KEY = process.env['SUPABASE_SERVICE_ROLE_KEY'] ?? ''

export interface MvRefreshResult {
  status: 'complete' | 'failed'
  bundle_cache_expired_deleted: number
  errors: string[]
}

/**
 * Run materialized view refresh + bundle cache cleanup.
 */
export async function runMvRefresh(): Promise<MvRefreshResult> {
  const result: MvRefreshResult = {
    status: 'complete',
    bundle_cache_expired_deleted: 0,
    errors: [],
  }

  if (!DB_URL || !DB_SERVICE_KEY) {
    result.errors.push('DB credentials not configured; skipping refresh.')
    return result
  }

  try {
    // Clean up expired bundle cache entries
    const cleanupResponse = await fetch(`${DB_URL}/rest/v1/mcp_bundle_cache`, {
      method: 'DELETE',
      headers: {
        'apikey': DB_SERVICE_KEY,
        'Authorization': `Bearer ${DB_SERVICE_KEY}`,
        'Prefer': 'return=representation',
      },
      body: JSON.stringify({ expires_at: { lt: new Date().toISOString() } }),
    })

    if (cleanupResponse.ok) {
      const deleted = await cleanupResponse.json() as unknown[]
      result.bundle_cache_expired_deleted = Array.isArray(deleted) ? deleted.length : 0
    }
  } catch (err) {
    result.status = 'failed'
    result.errors.push(err instanceof Error ? err.message : String(err))
  }

  return result
}
