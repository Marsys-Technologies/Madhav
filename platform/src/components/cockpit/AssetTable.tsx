'use client'

/**
 * AssetTable — tabular view of build assets with per-row actions
 * [PHASE-C-04]
 */

import { useState } from 'react'
import { ASSET_NAMES } from '@/lib/jyotish/asset_names'

type AssetMeta = { english: string; sanskrit: string; subtitle: string; layer: string }
const ASSET_LOOKUP = ASSET_NAMES as Record<string, AssetMeta | undefined>
import { CascadePreviewModal } from './CascadePreviewModal'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AssetRow {
  assetId: string
  status: string
  rowCount: number
  lastUpdated: string
}

interface Props {
  buildId: string
  chartId: string
  assets: AssetRow[]
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function layerDot(assetId: string) {
  const layer = ASSET_LOOKUP[assetId]?.layer
  const color = layer === 'L1' ? '#d4a648' : layer === 'L25' ? '#e8c878' : '#f8e6a8'
  return (
    <span
      className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
      style={{ background: color }}
      title={layer ?? '?'}
    />
  )
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending:  'bg-[#1a1820] text-[#5a5550]',
    queued:   'bg-[#1a1820] text-[#5a5550]',
    running:  'bg-[#d4a648]/10 text-[#d4a648]',
    success:  'bg-[#4a8c5c]/10 text-[#4a8c5c]',
    failed:   'bg-[#9c3a2a]/10 text-[#9c3a2a]',
    skipped:  'bg-[#5a5550]/10 text-[#5a5550]',
  }
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${map[status] ?? 'bg-[#1a1820] text-[#8a8070]'}`}>
      {status}
    </span>
  )
}

async function postAction(url: string, body: Record<string, string>) {
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

// ─── Component ────────────────────────────────────────────────────────────────

export function AssetTable({ buildId, chartId, assets }: Props) {
  const [cascadeAsset, setCascadeAsset] = useState<string | null>(null)

  if (assets.length === 0) {
    return (
      <div className="text-[#5a5550] text-sm py-8 text-center">
        No asset data yet — start a build to populate this table.
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-[#1a1820]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#1a1820] text-[#5a5550] text-xs uppercase tracking-wider">
              <th className="px-4 py-3 text-left w-6" />
              <th className="px-4 py-3 text-left">Asset</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Rows</th>
              <th className="px-4 py-3 text-right">Updated</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((row, idx) => (
              <tr
                key={row.assetId}
                className={`border-b border-[#1a1820]/50 hover:bg-[#0d0c10] transition-colors ${idx % 2 === 0 ? 'bg-transparent' : 'bg-[#0d0c10]/30'}`}
              >
                <td className="px-4 py-3">{layerDot(row.assetId)}</td>
                <td className="px-4 py-3 text-[#c8bfb0]">
                  {ASSET_LOOKUP[row.assetId]?.english ?? row.assetId}
                </td>
                <td className="px-4 py-3">
                  <StatusPill status={row.status} />
                </td>
                <td className="px-4 py-3 text-right font-mono text-[#8a8070]">
                  {row.rowCount.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right text-[#5a5550] text-xs">
                  {row.lastUpdated ? new Date(row.lastUpdated).toLocaleTimeString() : '—'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    {row.status !== 'running' && (
                      <button
                        onClick={() => setCascadeAsset(row.assetId)}
                        className="text-xs text-[#d4a648] hover:text-[#e8c878] transition-colors"
                      >
                        Rebuild
                      </button>
                    )}
                    {row.status === 'running' && (
                      <button
                        onClick={() => postAction('/api/build/asset/stop', { build_id: buildId, asset_id: row.assetId })}
                        className="text-xs text-[#9c3a2a] hover:text-[#c8502a] transition-colors"
                      >
                        Stop
                      </button>
                    )}
                    {(row.status === 'pending' || row.status === 'queued') && (
                      <button
                        onClick={() => postAction('/api/build/asset/skip', { build_id: buildId, asset_id: row.assetId })}
                        className="text-xs text-[#5a5550] hover:text-[#8a8070] transition-colors"
                      >
                        Skip
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {cascadeAsset && (
        <CascadePreviewModal
          isOpen={true}
          onClose={() => setCascadeAsset(null)}
          rootAssetId={cascadeAsset}
          plan={[cascadeAsset]}
          onConfirm={() => setCascadeAsset(null)}
        />
      )}
    </>
  )
}
