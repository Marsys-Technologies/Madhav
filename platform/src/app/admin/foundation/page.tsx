/**
 * /admin/foundation — Brahmagyan Infrastructure View
 *
 * Admin-only page (layout already gates super_admin + active; this page
 * double-checks and also redirects if somehow reached without the layout).
 *
 * Renders:
 *   1. Single-band L0 (Brahmagyan) tower — status, asset count, pips for the
 *      global foundation layer (not chart-specific).
 *   2. Infrastructure checklist — DB tables (proxy for migration applied),
 *      GCS bucket env-var presence, MCP tool registry count.
 *
 * WS-1-S3-C
 */

import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import type { Layer } from '@/components/brahma/LayerTower'
import { L0TowerIsland } from './L0TowerIsland'

// ── Brahma migration checks ─────────────────────────────────────────────────
// We use table existence as a proxy for "migration applied" since the project
// uses named (not numbered) migration files in platform/migrations/.
// Each entry names the canonical table seeded by that migration and a label.
const BRAHMA_TABLE_CHECKS: { table: string; label: string }[] = [
  { table: 'brahmagyan_texts',     label: 'Brahmagyan reference texts (brahmagyan_texts)' },
  { table: 'pyramid_layers',       label: 'Pyramid layer registry (pyramid_layers)' },
  { table: 'build_manifests',      label: 'Build manifests (build_manifests)' },
  { table: 'ganita_positions',     label: 'Gaṇita positions (ganita_positions)' },
  { table: 'chart_facts',          label: 'Chart facts (chart_facts)' },
  { table: 'rag_chunks',           label: 'RAG classical texts (rag_chunks)' },
]

// ── GCS bucket config (env-var presence) ───────────────────────────────────
// We cannot ping GCS from a server component without credentials; instead we
// check whether the relevant env-vars are set in the runtime.
const GCS_PREFIXES: { label: string; envKey: string }[] = [
  { label: 'Upload bucket',      envKey: 'GCS_BUCKET_NAME' },
  { label: 'Asset storage root', envKey: 'BRAHMA_GCS_BUCKET' },
  { label: 'Build artifact bucket', envKey: 'BRAHMA_ARTIFACT_BUCKET' },
]

// ── Data helpers ────────────────────────────────────────────────────────────

async function checkTableExists(tableName: string): Promise<boolean> {
  try {
    const { rows } = await query<{ exists: boolean }>(
      `SELECT EXISTS (
         SELECT 1 FROM information_schema.tables
         WHERE table_schema = 'public' AND table_name = $1
       ) AS exists`,
      [tableName],
    )
    return rows[0]?.exists ?? false
  } catch {
    return false
  }
}

async function getToolCount(): Promise<number | null> {
  try {
    const { rows } = await query<{ cnt: string }>(`SELECT COUNT(*) AS cnt FROM capability_tool_registry`)
    return parseInt(rows[0]?.cnt ?? '0', 10)
  } catch {
    return null
  }
}

async function getL0LayerStatus(): Promise<Layer> {
  // Query pyramid_layers for all charts — L0 is global infrastructure.
  // For the single-band tower we compute an aggregate across all charts.
  try {
    const { rows } = await query<{ status: string; sublayer: string | null }>(
      `SELECT status, sublayer FROM pyramid_layers WHERE layer = 'L0' LIMIT 100`,
    )
    const assets = rows.map((r) => ({
      asset_key: r.sublayer ?? 'L0',
      status: normalizeLayerStatus(r.status),
    }))
    const allBuilt = assets.length > 0 && assets.every((a) => a.status === 'built')
    const anyBuilding = assets.some((a) => a.status === 'building')
    const anyFailed = assets.some((a) => a.status === 'failed')
    return {
      layer: 'L0',
      name: 'Brahmagyan — Foundation',
      status: assets.length === 0 ? 'not-built' : allBuilt ? 'built' : anyBuilding ? 'building' : anyFailed ? 'failed' : 'not-built',
      asset_count: assets.length,
      assets,
    }
  } catch {
    // pyramid_layers table doesn't exist yet — show not-built
    return {
      layer: 'L0',
      name: 'Brahmagyan — Foundation',
      status: 'not-built',
      asset_count: 0,
      assets: [],
    }
  }
}

function normalizeLayerStatus(raw: string | null): 'built' | 'building' | 'failed' | 'attention' | 'not-built' {
  switch (raw) {
    case 'complete':
    case 'built':
      return 'built'
    case 'building':
    case 'in_progress':
      return 'building'
    case 'failed':
      return 'failed'
    case 'attention':
      return 'attention'
    default:
      return 'not-built'
  }
}

// ── Page ────────────────────────────────────────────────────────────────────

export default async function AdminFoundationPage() {
  // Auth guard (layout already handles this but double-check here)
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
  if (ctx.profile.status !== 'active') redirect('/login')

  // Fetch all data in parallel
  const [l0Layer, tableChecks, toolCount] = await Promise.all([
    getL0LayerStatus(),
    Promise.all(BRAHMA_TABLE_CHECKS.map(async (c) => ({
      ...c,
      ok: await checkTableExists(c.table),
    }))),
    getToolCount(),
  ])

  const gcsChecks = GCS_PREFIXES.map((g) => ({
    ...g,
    value: process.env[g.envKey] ?? null,
  }))

  const migrationOkCount = tableChecks.filter((c) => c.ok).length
  const gcsOkCount = gcsChecks.filter((g) => g.value).length

  return (
    <div data-testid="admin-foundation-page" className="mx-auto max-w-4xl space-y-8 py-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Brahmagyan Foundation</h1>
        <p className="mt-1 text-sm text-gray-500">
          Global infrastructure view for the L0 (Brahmagyan) bedrock layer.
          This layer is shared across all charts and built once by an admin.
        </p>
      </div>

      {/* ── 1. Single-band L0 tower ─────────────────────────────────────── */}
      <section aria-labelledby="section-tower">
        <h2 id="section-tower" className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
          L0 Layer Status
        </h2>
        {/* LayerTower is 'use client' — render as a standalone island */}
        <L0TowerIsland layer={l0Layer} />
      </section>

      {/* ── 2. Infrastructure checklist ────────────────────────────────── */}
      <section aria-labelledby="section-infra">
        <h2 id="section-infra" className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
          Infrastructure Checklist
        </h2>
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">

          {/* DB migrations (table existence checks) */}
          <div className="border-b border-gray-100 px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">DB migrations</span>
              <span className={`text-xs font-semibold ${migrationOkCount === tableChecks.length ? 'text-emerald-700' : 'text-amber-700'}`}>
                {migrationOkCount}/{tableChecks.length} tables present
              </span>
            </div>
          </div>
          <table className="w-full text-sm" aria-label="Brahma migration / table checklist">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Table / migration</th>
                <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tableChecks.map((c) => (
                <tr key={c.table} data-testid={`migration-row-${c.table}`}>
                  <td className="px-4 py-2.5 text-gray-700 font-mono text-xs">{c.label}</td>
                  <td className="px-4 py-2.5 text-right">
                    {c.ok ? (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700" aria-label="present">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        present
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700" aria-label="missing">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        missing
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* GCS buckets */}
          <div className="border-t border-gray-200 border-b border-gray-100 px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">GCS buckets</span>
              <span className={`text-xs font-semibold ${gcsOkCount === gcsChecks.length ? 'text-emerald-700' : 'text-amber-700'}`}>
                {gcsOkCount}/{gcsChecks.length} env-vars set
              </span>
            </div>
          </div>
          <table className="w-full text-sm" aria-label="GCS bucket env-var checklist">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Bucket / env-var</th>
                <th scope="col" className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {gcsChecks.map((g) => (
                <tr key={g.envKey} data-testid={`gcs-row-${g.envKey}`}>
                  <td className="px-4 py-2.5 text-gray-700">
                    <span className="block text-sm">{g.label}</span>
                    <span className="font-mono text-xs text-gray-400">{g.envKey}</span>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    {g.value ? (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700" aria-label="configured">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        configured
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700" aria-label="not set">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                        not set
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Tool health */}
          <div className="border-t border-gray-200 border-b border-gray-100 px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">MCP tool registry</span>
              <span className={`text-xs font-semibold ${toolCount !== null && toolCount > 0 ? 'text-emerald-700' : 'text-amber-700'}`}>
                {toolCount === null ? 'table missing' : `${toolCount} tools registered`}
              </span>
            </div>
          </div>
          <div className="px-4 py-3 bg-gray-50">
            {toolCount === null ? (
              <p className="text-xs text-red-600">
                capability_tool_registry table not found — apply migration 070_capability_tool_registry.sql.
              </p>
            ) : toolCount === 0 ? (
              <p className="text-xs text-amber-700">
                No tools registered. Run the GISMCP seeding script to populate the registry.
              </p>
            ) : (
              <p className="text-xs text-gray-600">
                {toolCount} tools are registered in the capability_tool_registry.{' '}
                View the full tool list at{' '}
                <a href="/admin/mcp" className="underline hover:text-gray-900">
                  /admin/mcp
                </a>
                .
              </p>
            )}
          </div>

        </div>
      </section>
    </div>
  )
}

