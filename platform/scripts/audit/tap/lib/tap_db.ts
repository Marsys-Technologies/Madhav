/**
 * tap_db.ts — shared DB access + graceful-skip helper for the TAP CI suite
 * (TOTAL_AUDIT_PROTOCOL_v1_0.md §3, Phase 5 of MARSYS_DEFECT_GAP_REGISTER_v2_0.md).
 *
 * Every TAP battery that needs live data (TAP-5, TAP-7, S-13) goes through this
 * helper so that "no DATABASE_URL in this CI runner" produces an explicit,
 * loud SKIPPED-WITH-REASON result (TAP-9 discipline: an absent oracle must be
 * declared, never silently passed). It never returns a false PASS.
 *
 * Local / pipeline usage: point DATABASE_URL at the Cloud SQL Auth Proxy
 * (127.0.0.1:5432) before invoking any tap*.ts script, e.g.:
 *   cloud-sql-proxy <INSTANCE_CONNECTION_NAME> &
 *   DATABASE_URL=postgres://user:pass@127.0.0.1:5432/amjis \
 *     npx tsx --conditions=react-server platform/scripts/audit/tap/tap5_seam_conservation.ts
 */
import type { QueryResult, QueryResultRow } from 'pg'
import { createHash } from 'node:crypto'

export const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/**
 * Short, stable content hash for a single matched line (trimmed, so leading
 * indentation drift doesn't churn the baseline). Used by tap6_method_grep.ts
 * and sc_pointer_validation.ts's ratchet baselines to key on (pattern/instrument,
 * file, line-hash) rather than (pattern/instrument, file) alone — Ring-2
 * review (post-bacade1c) found the coarser key let a second, unrelated
 * occurrence of an already-baselined pattern in an already-baselined file
 * slip through uncaught.
 */
export function lineHash(text: string): string {
  return createHash('sha1').update(text.trim()).digest('hex').slice(0, 12)
}

export type TapDb = {
  available: boolean
  reason?: string
  query<T extends QueryResultRow = QueryResultRow>(sql: string, params?: unknown[]): Promise<QueryResult<T>>
}

/**
 * Lazily attempts to load the project's pg pool (`src/lib/db/client.ts`).
 * Returns { available: false, reason } instead of throwing if DATABASE_URL
 * is unset or the connection fails — callers MUST surface `reason` in their
 * report rather than skip silently.
 */
export async function connectTapDb(): Promise<TapDb> {
  if (!process.env.DATABASE_URL) {
    return {
      available: false,
      reason:
        'DATABASE_URL not set in this environment. Run via Cloud SQL Auth Proxy: ' +
        'cloud-sql-proxy <INSTANCE_CONNECTION_NAME> & then export DATABASE_URL=postgres://.../amjis ' +
        'before invoking this script. See platform/scripts/audit/tap/README.md.',
      query: async () => {
        throw new Error('TapDb not available')
      },
    }
  }
  try {
    const mod = await import('../../../../src/lib/db/client')
    // Cheap connectivity probe — fail fast rather than hang the CI job.
    await mod.query('SELECT 1')
    return { available: true, query: mod.query }
  } catch (err) {
    return {
      available: false,
      reason: `DB connection failed: ${err instanceof Error ? err.message : String(err)}`,
      query: async () => {
        throw new Error('TapDb not available')
      },
    }
  }
}

export type LawResult = {
  id: string
  title: string
  status: 'PASS' | 'FAIL' | 'QUARANTINED' | 'SKIPPED'
  detail: string
  register_rows?: string[]
}

export function printReport(battery: string, results: LawResult[], skipReason?: string): number {
  const report = {
    battery,
    generated_at: new Date().toISOString(),
    skip_reason: skipReason ?? null,
    results,
  }
  console.log(JSON.stringify(report, null, 2))
  console.error(`\n=== ${battery} summary ===`)
  for (const r of results) {
    console.error(`[${r.status}] ${r.id} — ${r.title}`)
  }
  const hardFails = results.filter((r) => r.status === 'FAIL')
  if (skipReason) {
    console.error(`\nSKIPPED-WITH-REASON: ${skipReason}`)
    return 3 // distinct exit code: battery could not run, never conflate with PASS
  }
  return hardFails.length > 0 ? 1 : 0
}
