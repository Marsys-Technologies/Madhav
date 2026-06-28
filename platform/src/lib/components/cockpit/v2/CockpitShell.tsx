'use client'

import { useCallback, useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { DUR } from './motion'
import { CockpitHeader } from './CockpitHeader'
import { TabBar } from './TabBar'
import { DataAssetsView } from './DataAssetsView'
import { WorkflowView } from './WorkflowView'
import { AgentsView } from './AgentsView'
import { ClearConfirmModal } from './ClearConfirmModal'
import { useChartContext } from '@/hooks/useChartContext'
import { useActiveRun } from '@/hooks/useActiveRun'
import type { AssetWithState } from './LiveDependencyGraph'

type Tab = 'data' | 'workflow' | 'agents'

interface ClearPreview {
  tables: { table: string; rows: number; error?: string }[]
  total_rows: number
  affected_assets: string[]
  not_clearable_assets?: { id: string; label: string }[]
  downstream_stale_assets: string[]
  downstream_stale_assets_labeled?: { id: string; label: string; layer?: string; sanskrit_name?: string }[]
  assets_clearable?: { id: string; label: string; rows: number }[]
  assets_reset_only?: { id: string; label: string }[]
  scope_label?: string | null
  preview_hash: string
  requires_typed_confirmation?: string
  layer_summary?: { layer: string; rows: number; asset_count: number }[]
}

interface ChartMeta {
  subject_name: string | null
  birth_date: string | null
  birth_time?: string | null
  birth_place: string | null
}

interface Props {
  chartId: string
  initialChartMeta?: ChartMeta | null
}

export function CockpitShell({ chartId, initialChartMeta }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('data')
  const { chartName, birthDate, birthTime, birthPlace } = useChartContext(chartId, initialChartMeta)

  // Asset state summary — populated by DataAssetsView via onAssetsReady (merged state list)
  const [assetStates, setAssetStates] = useState<{ asset_id: string; state: string }[]>([])

  // Single useActiveRun instance — lifted from CockpitHeader and DataAssetsView.
  // Previously both components had their own 5s polling loop to the same endpoint.
  const { run: activeRun, refresh: refreshRun } = useActiveRun(chartId)
  const isBuilding = activeRun !== null

  // Global clear modal state — clearModalOpen lets us show the modal immediately
  // (with isLoading skeleton) while clearPreview is still being fetched.
  const [clearModalOpen, setClearModalOpen] = useState(false)
  const [clearPreview, setClearPreview] = useState<ClearPreview | null>(null)
  const [clearLoading, setClearLoading] = useState(false)

  // Whether the clear is part of a Rebuild flow (chains a build POST after clear)
  const [rebuildMode, setRebuildMode] = useState(false)

  // handleAssetsReady: receives the merged (assets + stats + SSE overlay) list from
  // DataAssetsView. Used for error badge count (Task 7) and header label logic.
  const handleAssetsReady = useCallback((assets: AssetWithState[]) => {
    setAssetStates(assets.map(a => ({ asset_id: a.asset_id, state: a.state })))
  }, [])

  // Open the modal immediately, then fetch preview async (loading skeleton while waiting).
  const openGlobalClearModal = useCallback(async (isRebuild = false) => {
    setClearModalOpen(true)
    setClearPreview(null)
    setClearLoading(true)
    setRebuildMode(isRebuild)
    try {
      const r = await fetch('/api/cockpit/clear', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope: 'global', scope_target: null }),
      })
      const body = await r.json()
      if (!r.ok) throw new Error(body.error ?? 'Failed to fetch clear preview')
      setClearPreview(body.preview)
    } catch (e) {
      toast.error((e as Error).message)
      setClearModalOpen(false)
    } finally {
      setClearLoading(false)
    }
  }, [chartId])

  const handleGlobalClear = useCallback(() => {
    openGlobalClearModal(false)
  }, [openGlobalClearModal])

  const handleGlobalRebuild = useCallback(() => {
    openGlobalClearModal(true)
  }, [openGlobalClearModal])

  // Called by ClearConfirmModal after a successful clear — chains a build POST when rebuildMode is set
  const handleAfterClear = useCallback(async () => {
    if (!rebuildMode) return
    setRebuildMode(false)
    const r = await fetch('/api/cockpit/runs', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chart_id: chartId, scope: 'global', scope_target: null, action: 'build' }),
    })
    const body = await r.json()
    if (!r.ok) throw new Error(body.error ?? 'Failed to start build after clear')
  }, [rebuildMode, chartId])

  const handleClearSuccess = useCallback(() => {
    setClearModalOpen(false)
    setClearPreview(null)
    setRefreshKey(k => k + 1)
  }, [])

  const handleClearClose = useCallback(() => {
    setClearModalOpen(false)
    setClearPreview(null)
    setRebuildMode(false)
  }, [])

  const [proMode, setProMode] = useState(false)

  // Incrementing this key triggers DataAssetsView to re-fetch all live data.
  const [refreshKey, setRefreshKey] = useState(0)
  const handleRefreshed = useCallback(() => setRefreshKey(k => k + 1), [])

  // Error badge count — derived from the merged state list that DataAssetsView
  // reports via onAssetsReady. No extra polling needed.
  const errorCount = assetStates.filter(a => a.state === 'error').length

  // The chart identity + telemetry + actions, compact — rides at the top of the
  // scrolling ledger column (no full-width header card; graph gets the height).
  const headerEl = (
    <CockpitHeader
      variant="inline"
      chartId={chartId}
      chartName={chartName}
      birthDate={birthDate}
      birthTime={birthTime}
      birthPlace={birthPlace}
      assets={assetStates}
      activeRun={activeRun}
      isBuilding={isBuilding}
      errorCount={errorCount}
      proMode={proMode}
      onProModeToggle={() => setProMode(p => !p)}
      onGlobalClear={clearLoading ? undefined : handleGlobalClear}
      onGlobalRebuild={clearLoading ? undefined : handleGlobalRebuild}
      onRefreshed={handleRefreshed}
      onRunRefresh={refreshRun}
    />
  )

  return (
    <div
      className="marsys-cockpit"
      style={{
        background: 'var(--black)',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        color: 'var(--on-dark)',
        padding: '8px 16px 16px',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Cockpit-wide a11y + micro-interaction unifiers (component-scoped so they
          load reliably in dev; mirrored in globals.css for production builds). */}
      <style>{`
        .marsys-cockpit button:focus-visible { outline: 1px solid var(--gold-core); outline-offset: 2px; border-radius: 4px; }
        .marsys-cockpit [data-icon-btn] { transition: transform 0.15s ease, color 0.15s, background 0.15s; }
        .marsys-cockpit [data-icon-btn]:hover { transform: translateY(-1px); }
        @media (prefers-reduced-motion: reduce) { .marsys-cockpit [data-icon-btn]:hover { transform: none; } }
      `}</style>
      {/* Pro-only tab switcher — the lone "Data assets" tab is dropped in normal mode */}
      {proMode && (
        <div style={{ marginBottom: '4px', flexShrink: 0 }}>
          <TabBar activeTab={activeTab} onTabChange={setActiveTab} proMode={proMode} />
        </div>
      )}
      {activeTab === 'data' && (
        <motion.div
          key="tab-data"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: DUR.micro }}
          style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
        >
          <DataAssetsView
            chartId={chartId}
            onAssetsReady={handleAssetsReady}
            header={headerEl}
            refreshKey={refreshKey}
            activeRun={activeRun}
            refreshRun={refreshRun}
          />
        </motion.div>
      )}
      {activeTab === 'workflow' && proMode && (
        <motion.div key="tab-workflow" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: DUR.micro }} style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          {headerEl}
          <WorkflowView chartId={chartId} />
        </motion.div>
      )}
      {activeTab === 'agents' && proMode && (
        <motion.div key="tab-agents" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: DUR.micro }} style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          {headerEl}
          <AgentsView chartId={chartId} />
        </motion.div>
      )}

      {clearModalOpen && (
        <ClearConfirmModal
          chartId={chartId}
          scope="global"
          scopeTarget={null}
          preview={clearPreview}
          isLoading={clearLoading}
          onClose={handleClearClose}
          onSuccess={handleClearSuccess}
          onAfterClear={handleAfterClear}
        />
      )}
    </div>
  )
}
