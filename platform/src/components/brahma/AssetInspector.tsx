'use client'

/**
 * AssetInspector — Right-panel detail view for a single build asset.
 *
 * Fetches /api/assets/[chartId]/[assetKey] and displays:
 *   - asset_key, layer, status chip
 *   - row_count, provenance (build_id, ayanamsha_id, computed_at)
 *   - gate_verdict badge
 *   - 3 sample rows in a small table
 *
 * Opened by clicking a pip in LayerTower.
 * Closed via onClose() (✕ button or pressing Escape).
 */

import { useEffect, useState, useCallback } from 'react'

interface Provenance {
  build_id: string | null
  ayanamsha_id: string | null
  computed_at: string | null
}

interface SampleRow {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  source_section: string
  build_id: string
  created_at: string
}

interface AssetDetail {
  asset_key: string
  chart_id: string
  layer: string
  status: string
  row_count: number
  provenance: Provenance | null
  gate_verdict: 'passed' | 'amber' | 'failed'
  sample_rows: SampleRow[]
}

interface AssetInspectorProps {
  chartId: string
  assetKey: string | null
  onClose: () => void
}

// ── Gate verdict badge ─────────────────────────────────────────────────────────

const GATE_COLORS: Record<string, string> = {
  passed: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
  amber: 'bg-amber-100 text-amber-800 border border-amber-300',
  failed: 'bg-red-100 text-red-800 border border-red-300',
}

const GATE_ICONS: Record<string, string> = {
  passed: '✓',
  amber: '△',
  failed: '✗',
}

function GateBadge({ verdict }: { verdict: 'passed' | 'amber' | 'failed' }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${GATE_COLORS[verdict] ?? GATE_COLORS.failed}`}
      role="status"
      aria-label={`Gate verdict: ${verdict}`}
    >
      <span aria-hidden="true">{GATE_ICONS[verdict]}</span>
      {verdict}
    </span>
  )
}

// ── Status chip ────────────────────────────────────────────────────────────────

const STATUS_CHIP: Record<string, string> = {
  complete: 'bg-emerald-100 text-emerald-800',
  built: 'bg-emerald-100 text-emerald-800',
  in_progress: 'bg-amber-100 text-amber-800 animate-pulse',
  building: 'bg-amber-100 text-amber-800 animate-pulse',
  failed: 'bg-red-100 text-red-800',
  not_started: 'bg-gray-100 text-gray-500',
  'not-built': 'bg-gray-100 text-gray-500',
}

function StatusChip({ status }: { status: string }) {
  const cls = STATUS_CHIP[status] ?? STATUS_CHIP.not_started
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>
  )
}

// ── Provenance section ─────────────────────────────────────────────────────────

function ProvenanceSection({ provenance }: { provenance: Provenance | null }) {
  if (!provenance) {
    return <p className="text-sm text-gray-400 italic">No provenance data</p>
  }
  const items = [
    { label: 'Build ID', value: provenance.build_id ?? '—' },
    { label: 'Ayanamsha', value: provenance.ayanamsha_id ?? '—' },
    { label: 'Computed at', value: provenance.computed_at ? new Date(provenance.computed_at).toLocaleString() : '—' },
  ]
  return (
    <dl className="divide-y divide-gray-100 text-sm">
      {items.map((item) => (
        <div key={item.label} className="flex justify-between py-1.5">
          <dt className="text-gray-500">{item.label}</dt>
          <dd className="font-mono text-xs text-gray-800 truncate max-w-[180px]" title={item.value}>
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

// ── Sample rows table ──────────────────────────────────────────────────────────

function SampleRowsTable({ rows }: { rows: SampleRow[] }) {
  if (!rows.length) {
    return <p className="text-sm text-gray-400 italic">No rows found</p>
  }
  return (
    <div className="overflow-x-auto rounded border border-gray-200">
      <table className="min-w-full text-xs" aria-label="Sample asset rows">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-2 py-1.5 text-left text-gray-500 font-medium">fact_id</th>
            <th className="px-2 py-1.5 text-left text-gray-500 font-medium">div</th>
            <th className="px-2 py-1.5 text-left text-gray-500 font-medium">value</th>
            <th className="px-2 py-1.5 text-left text-gray-500 font-medium">source</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((row) => (
            <tr key={row.fact_id} className="hover:bg-gray-50">
              <td className="px-2 py-1.5 font-mono text-gray-700 max-w-[100px] truncate" title={row.fact_id}>
                {row.fact_id}
              </td>
              <td className="px-2 py-1.5 text-gray-600">{row.divisional_chart}</td>
              <td className="px-2 py-1.5 text-gray-700 max-w-[120px] truncate" title={String(row.value_text ?? row.value_number ?? '—')}>
                {row.value_text ?? row.value_number ?? '—'}
              </td>
              <td className="px-2 py-1.5 text-gray-500 max-w-[100px] truncate" title={row.source_section}>
                {row.source_section}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── AssetInspector ─────────────────────────────────────────────────────────────

export function AssetInspector({ chartId, assetKey, onClose }: AssetInspectorProps) {
  const [data, setData] = useState<AssetDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAsset = useCallback(async () => {
    if (!assetKey) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/assets/${chartId}/${assetKey}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as AssetDetail
      setData(json)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load asset')
    } finally {
      setLoading(false)
    }
  }, [chartId, assetKey])

  useEffect(() => {
    void fetchAsset()
  }, [fetchAsset])

  // Dismiss on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  if (!assetKey) return null

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 w-96 bg-white shadow-2xl border-l border-gray-200 flex flex-col"
      role="dialog"
      aria-modal="true"
      aria-label={`Asset inspector: ${assetKey}`}
      data-testid="asset-inspector"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div>
          <h2 className="font-semibold text-gray-900 text-sm">{assetKey}</h2>
          <p className="text-xs text-gray-500 mt-0.5">Asset Inspector</p>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          aria-label="Close inspector"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" aria-label="Loading" />
          </div>
        )}

        {error && !loading && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {error}
            <button
              onClick={() => void fetchAsset()}
              className="ml-2 underline text-red-600 hover:text-red-800"
            >
              Retry
            </button>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Status row */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                {data.layer}
              </span>
              <StatusChip status={data.status} />
              <GateBadge verdict={data.gate_verdict} />
            </div>

            {/* Row count */}
            <div className="rounded-lg bg-gray-50 border border-gray-200 px-4 py-3 flex items-center justify-between">
              <span className="text-sm text-gray-600">Row count</span>
              <span className="font-semibold text-lg tabular-nums text-gray-900">
                {data.row_count.toLocaleString()}
              </span>
            </div>

            {/* Provenance */}
            <section aria-label="Provenance">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Provenance
              </h3>
              <ProvenanceSection provenance={data.provenance} />
            </section>

            {/* Sample rows */}
            <section aria-label="Sample rows">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Sample rows (up to 3)
              </h3>
              <SampleRowsTable rows={data.sample_rows} />
            </section>
          </>
        )}
      </div>

      {/* Footer: refresh button */}
      {data && (
        <div className="border-t border-gray-200 px-4 py-3">
          <button
            onClick={() => void fetchAsset()}
            disabled={loading}
            className="w-full text-sm text-indigo-600 hover:text-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>
      )}
    </div>
  )
}
