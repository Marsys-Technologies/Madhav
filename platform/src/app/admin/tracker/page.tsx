/**
 * INF12-S1: Production Tracker — /admin/tracker
 *
 * Build orchestrator status page for super_admin. Shows:
 * - Active/recent builds with per-ayanamsha progress
 * - Session queue status (total/pending/complete from session_queue.yaml)
 * - Per-chart, per-ayanamsha build matrix
 *
 * Auth: super_admin only (inherited from admin layout).
 *
 * [BUILD-ORCH-INF12-S1]
 */

import { query } from '@/lib/db/client'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { redirect } from 'next/navigation'
import styles from './tracker.module.css'

export const dynamic = 'force-dynamic'
export const metadata = { title: 'Build Tracker — MARSYS-JIS Admin' }

// ── DB types ──────────────────────────────────────────────────────────────────

interface BuildRow {
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

interface AyanamshaMatrixRow {
  chart_id: string
  chart_name: string | null
  ayanamsha_id: string
  status: string
  finished_at: string | null
}

// ── Data fetchers ─────────────────────────────────────────────────────────────

async function fetchActiveBuilds(): Promise<BuildRow[] | null> {
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

async function fetchRecentBuilds(): Promise<BuildRow[] | null> {
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

async function fetchAyanamshaMatrix(): Promise<AyanamshaMatrixRow[] | null> {
  // Ayanamsha-per-build tracking removed with decommissioning of `builds` table.
  return null
}

// ── Components ────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    complete: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    queued: 'bg-yellow-100 text-yellow-800',
    cancelling: 'bg-orange-100 text-orange-800',
    cancelled: 'bg-gray-100 text-gray-600',
    failed: 'bg-red-100 text-red-800',
  }
  const cls = colorMap[status] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-mono font-medium ${cls}`}>
      {status}
    </span>
  )
}

function ProgressBar({ complete, total }: { complete: number; total: number }) {
  const pct = total > 0 ? Math.round((complete / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500">{complete}/{total}</span>
    </div>
  )
}

function BuildsTable({ builds, title }: { builds: BuildRow[] | null; title: string }) {
  if (!builds?.length) {
    return (
      <section aria-label={title}>
        <h2>{title}</h2>
        {builds ? <p>No builds.</p> : <p role="alert">Build records could not be read. Reload to try again.</p>}
      </section>
    )
  }
  return (
    <div>
      <h2>{title}</h2>
      <div className={styles.results} role="region" aria-label={`${title} records`} tabIndex={0}>
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50 text-gray-500 text-left">
              <th className="px-3 py-2 border border-gray-200">Chart</th>
              <th className="px-3 py-2 border border-gray-200">Ayanamshas</th>
              <th className="px-3 py-2 border border-gray-200">Status</th>
              <th className="px-3 py-2 border border-gray-200">Progress</th>
              <th className="px-3 py-2 border border-gray-200">Engine</th>
              <th className="px-3 py-2 border border-gray-200">Finished</th>
            </tr>
          </thead>
          <tbody>
            {builds.map((b) => {
              const ayas = b.ayanamsha_ids
                ? (() => {
                    try {
                      return (JSON.parse(b.ayanamsha_ids) as string[]).join(', ')
                    } catch {
                      return b.ayanamsha_ids
                    }
                  })()
                : '—'
              return (
                <tr key={b.build_id} className="even:bg-gray-50 hover:bg-blue-50">
                  <td className="px-3 py-2 border border-gray-200 font-mono">
                    {b.chart_name ?? b.chart_id.slice(0, 8)}
                  </td>
                  <td className="px-3 py-2 border border-gray-200">{ayas}</td>
                  <td className="px-3 py-2 border border-gray-200">
                    <StatusBadge status={b.status} />
                  </td>
                  <td className="px-3 py-2 border border-gray-200">
                    <ProgressBar complete={b.steps_complete} total={b.steps_total} />
                  </td>
                  <td className="px-3 py-2 border border-gray-200 font-mono">
                    {b.engine_version ?? '—'}
                  </td>
                  <td className="px-3 py-2 border border-gray-200 text-gray-500">
                    {b.finished_at ? new Date(b.finished_at).toLocaleString() : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AyanamshaMatrix({ rows }: { rows: AyanamshaMatrixRow[] | null }) {
  if (!rows) return <p>Per-ayanamsha build history is unavailable in this tracker.</p>
  if (rows.length === 0) {
    return <p>No build matrix data.</p>
  }

  const AYANAMSHAS = ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta']
  const byChart = new Map<string, { name: string | null; ayas: Record<string, string> }>()

  for (const r of rows) {
    if (!byChart.has(r.chart_id)) byChart.set(r.chart_id, { name: r.chart_name, ayas: {} })
    byChart.get(r.chart_id)!.ayas[r.ayanamsha_id] = r.status
  }

  const statusIcon: Record<string, string> = {
    complete: '✓',
    running: '⟳',
    queued: '…',
    failed: '✗',
    cancelled: '—',
  }

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-700 mb-2">Ayanamsha Build Matrix</h2>
      <div className="overflow-x-auto">
        <table className="text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50 text-gray-500">
              <th className="px-3 py-2 border border-gray-200 text-left">Chart</th>
              {AYANAMSHAS.map((a) => (
                <th key={a} className="px-2 py-2 border border-gray-200 font-mono">
                  {a}
                  {a === 'lahiri' ? ' (primary)' : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...byChart.entries()].map(([chartId, { name, ayas }]) => (
              <tr key={chartId} className="even:bg-gray-50">
                <td className="px-3 py-2 border border-gray-200 font-mono">
                  {name ?? chartId.slice(0, 8)}
                </td>
                {AYANAMSHAS.map((a) => {
                  const status = ayas[a] ?? 'not_built'
                  const icon = statusIcon[status] ?? '?'
                  const cls =
                    status === 'complete'
                      ? 'text-green-600'
                      : status === 'failed'
                        ? 'text-red-500'
                        : status === 'running'
                          ? 'text-blue-500'
                          : 'text-gray-300'
                  return (
                    <td key={a} className={`px-2 py-2 border border-gray-200 text-center ${cls}`}>
                      {icon}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function TrackerPage() {
  const ctx = await getServerUserWithProfile()
  if (!ctx || ctx.profile.role !== 'super_admin') redirect('/admin')

  const [activeBuilds, recentBuilds, matrixRows] = await Promise.all([
    fetchActiveBuilds(),
    fetchRecentBuilds(),
    fetchAyanamshaMatrix(),
  ])

  return (
    <div className={styles.tracker}>
      <div>
        <h1>Build Orchestrator Tracker</h1>
        <p>Build run records. Reload to check for changes.</p>
      </div>

      <BuildsTable builds={activeBuilds} title={activeBuilds ? `Active Builds (${activeBuilds.length})` : 'Active Builds'} />
      <BuildsTable builds={recentBuilds} title="Recent Builds (last 24h)" />
      <AyanamshaMatrix rows={matrixRows} />
    </div>
  )
}
