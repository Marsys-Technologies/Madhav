'use client'

/**
 * AssetTable v2 — per-layer asset table per VISUAL_CONTRACT v2
 * §"Page 2 §4 Per-layer asset tables".
 *
 * Layout:
 *   - Section heading per layer: Sanskrit · English · L-tag · N of M complete
 *   - 5-column rows: row_num | name + subtitle | progress bar | row count | status
 *   - Per-row Rebuild icon button (calls onRebuild(asset_id) prop)
 *   - Cascade hint footer
 *
 * Names sourced from lib/jyotish/asset_names.ts — never inlined.
 * All colours from theme tokens — no raw hex in this file.
 *
 * [C-S7]
 */

import { useState } from 'react'
import {
  ASSET_NAMES,
  LAYER_NAMES,
  assetsByLayer,
  type AssetKey,
  type LayerKey,
} from '@/lib/jyotish/asset_names'
import { CascadePreviewModal } from './CascadePreviewModal'
import { ServiceHealthBadge, ServiceLastInvokedLabel } from './ServiceHealthBadge'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AssetRow {
  assetId: string
  status: string
  rowCount: number
  progress?: number // 0-1
  lastUpdated?: string
  // Service-kind fields (populated for service assets; undefined for data assets)
  assetKind?: 'data' | 'service' | 'artifact' | null
  serviceHealth?: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | null
  lastInvokedAt?: string | null
}

interface Props {
  buildId: string
  chartId: string
  assets: AssetRow[]
  onRebuild?: (assetId: string) => void
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<string, string> = {
  pending:  'Pending',
  queued:   'Queued',
  running:  'Running',
  complete: 'Complete',
  success:  'Complete',
  failed:   'Failed',
  skipped:  'Skipped',
}

const STATUS_COLOR: Record<string, string> = {
  pending:  'var(--text-tertiary, #5d5b54)',
  queued:   'var(--text-tertiary, #5d5b54)',
  running:  'var(--gold-primary, #d4a648)',
  complete: 'var(--success, #9bd49a)',
  success:  'var(--success, #9bd49a)',
  failed:   'var(--danger, #e89a9a)',
  skipped:  'var(--text-tertiary, #5d5b54)',
}

function StatusPill({ status }: { status: string }) {
  const label = STATUS_LABEL[status] ?? status
  const color = STATUS_COLOR[status] ?? 'var(--text-secondary, #888373)'
  return (
    <span
      data-testid={`status-pill-${status}`}
      style={{
        fontFamily: 'var(--font-sans, Inter, sans-serif)',
        fontSize: 11,
        color,
        background: `${color}18`,
        padding: '2px 8px',
        borderRadius: 999,
        border: `1px solid ${color}40`,
        whiteSpace: 'nowrap',
      }}
    >
      {label}
    </span>
  )
}

function MiniProgressBar({ progress = 0 }: { progress?: number }) {
  const pct = `${Math.min(100, Math.max(0, progress * 100)).toFixed(0)}%`
  return (
    <div
      style={{
        width: 60,
        height: 4,
        background: 'var(--obsidian-border, #1f1c17)',
        borderRadius: 999,
        overflow: 'hidden',
      }}
    >
      <div
        data-testid="mini-progress-fill"
        style={{
          width: pct,
          height: '100%',
          background: 'var(--gold-primary, #d4a648)',
          borderRadius: 999,
          transition: 'width var(--transition-bar, 300ms ease-in-out)',
        }}
      />
    </div>
  )
}

// ── Layer section ─────────────────────────────────────────────────────────────

interface LayerSectionProps {
  layer: LayerKey
  assets: AssetRow[]
  buildId: string
  chartId: string
  rowOffset: number
  onRebuild?: (assetId: string) => void
  onCascade: (assetId: string) => void
}

function LayerSection({
  layer,
  assets,
  buildId,
  chartId,
  rowOffset,
  onRebuild,
  onCascade,
}: LayerSectionProps) {
  const layerMeta = LAYER_NAMES[layer]
  const keys = assetsByLayer(layer)
  const completeCount = assets.filter(
    (a) => a.status === 'complete' || a.status === 'success',
  ).length
  const tag = layer.replace('_', '.')

  const statusByKey = new Map<string, AssetRow>(assets.map((a) => [a.assetId, a]))

  return (
    <div data-testid={`layer-section-${layer}`}>
      {/* Section heading */}
      <div
        className="flex items-baseline gap-2 px-4 py-2"
        style={{ borderBottom: '1px solid var(--obsidian-border, #1f1c17)' }}
      >
        <span
          style={{
            fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
            fontStyle: 'italic',
            fontSize: 15,
            color: 'var(--gold-primary, #d4a648)',
          }}
        >
          {layerMeta.sanskrit}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-sans, Inter, sans-serif)',
            fontSize: 12,
            color: 'var(--text-secondary, #888373)',
          }}
        >
          · {layerMeta.english}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
            fontSize: 10,
            color: 'var(--text-tertiary, #5d5b54)',
            letterSpacing: '0.08em',
          }}
        >
          {tag}
        </span>
        <span
          data-testid={`layer-count-${layer}`}
          style={{
            fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
            fontSize: 10,
            color: completeCount === keys.length
              ? 'var(--success, #9bd49a)'
              : 'var(--text-tertiary, #5d5b54)',
            marginLeft: 'auto',
          }}
        >
          {completeCount} of {keys.length} complete
        </span>
      </div>

      {/* Rows */}
      {keys.map((key, i) => {
        const entry = ASSET_NAMES[key]
        const row = statusByKey.get(key)
        const rowNum = String(rowOffset + i + 1).padStart(2, '0')
        const status = row?.status ?? 'pending'
        const progress = row?.progress
        const rowCount = row?.rowCount ?? 0

        const isService = row?.assetKind === 'service' || row?.status === 'service_ok'

        return (
          <div
            key={key}
            data-testid={`asset-row-${key}`}
            className="grid items-center px-4 py-2"
            style={{
              gridTemplateColumns: '32px 1fr 72px 80px 88px 80px',
              gap: 8,
              borderBottom: '1px solid var(--obsidian-border, #1f1c17)40',
            }}
          >
            {/* Row number */}
            <span
              style={{
                fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                fontSize: 10,
                color: 'var(--text-tertiary, #5d5b54)',
              }}
            >
              {rowNum}
            </span>

            {/* Name + subtitle */}
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
                  fontSize: 15,
                  color: 'var(--text-primary, #e8e6df)',
                }}
              >
                {entry.sanskrit}
              </div>
              <div
                style={{
                  fontFamily: 'var(--font-sans, Inter, sans-serif)',
                  fontSize: 10,
                  color: 'var(--text-tertiary, #5d5b54)',
                }}
              >
                {entry.subtitle}
              </div>
            </div>

            {/* Progress bar */}
            <MiniProgressBar progress={progress} />

            {/* Row count — or service health badge for service-kind assets */}
            {isService ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                <ServiceHealthBadge health={row?.serviceHealth ?? null} compact lastInvokedAt={row?.lastInvokedAt} />
                <ServiceLastInvokedLabel lastInvokedAt={row?.lastInvokedAt} />
              </div>
            ) : (
              <span
                style={{
                  fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                  fontSize: 11,
                  color: 'var(--text-secondary, #888373)',
                  textAlign: 'right',
                }}
              >
                {rowCount > 0 ? rowCount.toLocaleString() : '—'}
              </span>
            )}

            {/* Status pill */}
            <StatusPill status={status} />

            {/* Rebuild action */}
            <button
              data-testid={`rebuild-btn-${key}`}
              onClick={() => {
                onCascade(key)
                onRebuild?.(key)
              }}
              style={{
                fontFamily: 'var(--font-sans, Inter, sans-serif)',
                fontSize: 11,
                color: 'var(--gold-primary, #d4a648)',
                background: 'none',
                border: '1px solid var(--gold-deep, #5a3a1f)',
                borderRadius: 4,
                padding: '2px 8px',
                cursor: 'pointer',
              }}
            >
              Rebuild
            </button>
          </div>
        )
      })}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

const LAYERS: LayerKey[] = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']

export function AssetTable({ buildId, chartId, assets, onRebuild }: Props) {
  const [cascadeAsset, setCascadeAsset] = useState<string | null>(null)

  function handleCascade(assetId: string) {
    setCascadeAsset(assetId)
  }

  // Total rows per layer for row numbering offset
  let rowOffset = 0

  return (
    <>
      <div
        data-testid="asset-table"
        style={{
          background: 'var(--obsidian-panel, #0a0908)',
          border: '1px solid var(--obsidian-border, #1f1c17)',
          borderRadius: 12,
          overflow: 'hidden',
        }}
      >
        {LAYERS.map((layer) => {
          const layerKeys = assetsByLayer(layer)
          const section = (
            <LayerSection
              key={layer}
              layer={layer}
              assets={assets.filter((a) =>
                layerKeys.includes(a.assetId as AssetKey),
              )}
              buildId={buildId}
              chartId={chartId}
              rowOffset={rowOffset}
              onRebuild={onRebuild}
              onCascade={handleCascade}
            />
          )
          rowOffset += layerKeys.length
          return section
        })}

        {/* Footer cascade hint */}
        <div
          data-testid="cascade-hint"
          style={{
            padding: '10px 16px',
            fontFamily: 'var(--font-sans, Inter, sans-serif)',
            fontSize: 11,
            color: 'var(--text-tertiary, #5d5b54)',
            borderTop: '1px solid var(--obsidian-border, #1f1c17)',
          }}
        >
          Click any row to Rebuild just that asset · the cascade preview will show
          downstream nodes that get invalidated and recomputed
        </div>
      </div>

      {cascadeAsset && (
        <CascadePreviewModal
          open={true}
          onClose={() => setCascadeAsset(null)}
          assetId={cascadeAsset}
          buildId={buildId}
          chartId={chartId}
          onConfirm={() => setCascadeAsset(null)}
        />
      )}
    </>
  )
}
