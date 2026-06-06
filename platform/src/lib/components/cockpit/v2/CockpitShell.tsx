'use client'

import { useCallback, useState } from 'react'
import { toast } from 'sonner'
import { CockpitHeader } from './CockpitHeader'
import { TabBar } from './TabBar'
import { DataAssetsView } from './DataAssetsView'
import { WorkflowView } from './WorkflowView'
import { AgentsView } from './AgentsView'
import { ClearConfirmModal } from './ClearConfirmModal'
import { useChartContext } from '@/hooks/useChartContext'
import type { AssetWithState } from './LiveDependencyGraph'

type Tab = 'data' | 'workflow' | 'agents'

interface ClearPreview {
  tables: { table: string; rows: number }[]
  total_rows: number
  affected_assets: string[]
  downstream_stale_assets: string[]
  preview_hash: string
  requires_typed_confirmation?: string
}

interface Props {
  chartId: string
}

export function CockpitShell({ chartId }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('data')
  const { chartName, birthDate, birthPlace } = useChartContext(chartId)

  // Asset state summary — populated by DataAssetsView via onAssetsReady
  const [assetStates, setAssetStates] = useState<{ state: string }[]>([])

  // Global clear modal state
  const [clearPreview, setClearPreview] = useState<ClearPreview | null>(null)
  const [clearLoading, setClearLoading] = useState(false)

  // Whether the clear is part of a Rebuild flow (chains a build POST after clear)
  const [rebuildMode, setRebuildMode] = useState(false)

  console.log('[Shell] render — chartName=', chartName, 'birthDate=', birthDate)

  const handleAssetsReady = useCallback((assets: AssetWithState[]) => {
    setAssetStates(assets.map(a => ({ state: a.state })))
  }, [])

  // Fetch a global clear preview and open the modal
  const openGlobalClearModal = useCallback(async (isRebuild = false) => {
    setClearLoading(true)
    try {
      const r = await fetch('/api/cockpit/clear', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope: 'global', scope_target: null }),
      })
      const body = await r.json()
      if (!r.ok) throw new Error(body.error ?? 'Failed to fetch clear preview')
      setRebuildMode(isRebuild)
      setClearPreview(body.preview)
    } catch (e) {
      toast.error((e as Error).message)
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
    setClearPreview(null)
  }, [])

  const handleClearClose = useCallback(() => {
    setClearPreview(null)
    setRebuildMode(false)
  }, [])

  const [proMode, setProMode] = useState(false)

  return (
    <div
      className="marsys-cockpit"
      style={{
        background: 'var(--black)',
        minHeight: '100vh',
        color: 'var(--on-dark)',
        padding: '16px',
        boxSizing: 'border-box',
      }}
    >
      <CockpitHeader
        chartId={chartId}
        chartName={chartName}
        birthDate={birthDate}
        birthPlace={birthPlace}
        assets={assetStates}
        proMode={proMode}
        onProModeToggle={() => setProMode(p => !p)}
        onGlobalClear={clearLoading ? undefined : handleGlobalClear}
        onGlobalRebuild={clearLoading ? undefined : handleGlobalRebuild}
      />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} proMode={proMode} />
      {activeTab === 'data' && (
        <DataAssetsView chartId={chartId} onAssetsReady={handleAssetsReady} />
      )}
      {activeTab === 'workflow' && proMode && <WorkflowView chartId={chartId} />}
      {activeTab === 'agents' && proMode && <AgentsView chartId={chartId} />}
      {(activeTab === 'workflow' || activeTab === 'agents') && !proMode && (
        <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--on-dark-faint)', fontFamily: 'var(--ui-stack)', fontSize: '14px' }}>
          Enable Pro view to access this tab.
        </div>
      )}

      {clearPreview && (
        <ClearConfirmModal
          chartId={chartId}
          scope="global"
          scopeTarget={null}
          preview={clearPreview}
          onClose={handleClearClose}
          onSuccess={handleClearSuccess}
          onAfterClear={handleAfterClear}
        />
      )}
    </div>
  )
}
