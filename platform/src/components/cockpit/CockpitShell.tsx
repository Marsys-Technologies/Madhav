'use client'

/**
 * CockpitShell — client-side cockpit page shell
 * Obsidian theme, top bar + left sidebar + tabbed main content
 * [PHASE-C-02]
 */

import { useState, useCallback } from 'react'
import { BuildControlsBar } from './BuildControlsBar'
import { LiveBuildGraph } from './LiveBuildGraph'
import { AssetTable, type AssetRow } from './AssetTable'

// ─── Types ────────────────────────────────────────────────────────────────────

interface BuildMeta {
  build_id: string
  status: string
  created_at: string
  ayanamshas: string[]
}

interface Props {
  chartId: string
  chartName: string
  birthDate: string
  birthTime: string
  birthPlace: string
  latestBuild: BuildMeta | null
}

type Tab = 'graph' | 'ayanamsha' | 'assets' | 'eventlog' | 'preview'

const TABS: { id: Tab; label: string }[] = [
  { id: 'graph',     label: 'Live Graph' },
  { id: 'ayanamsha', label: 'By Ayanamsha' },
  { id: 'assets',    label: 'Assets' },
  { id: 'eventlog',  label: 'Event Log' },
  { id: 'preview',   label: 'Data Preview' },
]

// ─── Status pill ──────────────────────────────────────────────────────────────

function StatusPill({ status }: { status: string | undefined }) {
  const map: Record<string, { label: string; cls: string }> = {
    queued:    { label: 'BUILDING',  cls: 'bg-[#d4a648]/10 text-[#d4a648] animate-pulse' },
    running:   { label: 'BUILDING',  cls: 'bg-[#d4a648]/10 text-[#d4a648] animate-pulse' },
    success:   { label: 'COMPLETE',  cls: 'bg-[#4a8c5c]/10 text-[#4a8c5c]' },
    failed:    { label: 'FAILED',    cls: 'bg-[#9c3a2a]/10 text-[#9c3a2a]' },
    partial:   { label: 'PARTIAL',   cls: 'bg-[#c8842a]/10 text-[#c8842a]' },
    cancelled: { label: 'STOPPED',   cls: 'bg-[#5a5550]/10 text-[#5a5550]' },
  }
  const cfg = status ? (map[status] ?? { label: 'IDLE', cls: 'bg-[#1a1820] text-[#8a8070]' }) : { label: 'IDLE', cls: 'bg-[#1a1820] text-[#8a8070]' }
  return (
    <span className={`rounded-md px-2 py-0.5 text-xs font-mono font-semibold ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

// ─── Build meta card ──────────────────────────────────────────────────────────

function BuildMetaCard({ build }: { build: BuildMeta | null }) {
  if (!build) {
    return (
      <div className="rounded-lg border border-[#1a1820] bg-[#08070a] p-4 text-[#5a5550] text-sm">
        No builds yet.
      </div>
    )
  }
  const started = new Date(build.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })
  return (
    <div className="rounded-lg border border-[#1a1820] bg-[#08070a] p-4 text-sm space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[#8a8070]">Build ID</span>
        <span className="font-mono text-[#c8bfb0] text-xs">{build.build_id.slice(0, 8)}…</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[#8a8070]">Started</span>
        <span className="text-[#c8bfb0] text-xs">{started}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[#8a8070]">Status</span>
        <StatusPill status={build.status} />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[#8a8070]">Ayanamshas</span>
        <span className="text-[#c8bfb0] text-xs">{build.ayanamshas?.length ?? 0}</span>
      </div>
    </div>
  )
}

// ─── Main shell ───────────────────────────────────────────────────────────────

export function CockpitShell({ chartId, chartName, birthDate, birthTime, birthPlace, latestBuild }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('graph')
  const [currentBuild, setCurrentBuild] = useState<BuildMeta | null>(latestBuild)
  const [assets, setAssets] = useState<AssetRow[]>([])

  const handleBuildStart = useCallback((buildId?: string) => {
    if (buildId) {
      setCurrentBuild((prev) => prev
        ? { ...prev, build_id: buildId, status: 'running' }
        : { build_id: buildId, status: 'running', created_at: new Date().toISOString(), ayanamshas: [] }
      )
    }
  }, [])

  return (
    <div className="min-h-screen bg-[#08070a] text-[#f5f0e8] flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b border-[#1a1820] px-6 py-3 bg-[#0d0c10]">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="font-serif text-lg text-[#d4a648] leading-tight">{chartName}</h1>
            <p className="text-xs text-[#8a8070] mt-0.5">
              {birthDate} · {birthTime} · {birthPlace}
            </p>
          </div>
          <StatusPill status={currentBuild?.status} />
        </div>
        <BuildControlsBar
          chartId={chartId}
          buildId={currentBuild?.build_id}
          buildStatus={currentBuild?.status}
          onBuildStart={handleBuildStart}
        />
      </div>

      {/* Body: sidebar + main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar */}
        <aside className="w-72 shrink-0 border-r border-[#1a1820] bg-[#0d0c10] flex flex-col gap-4 p-4 overflow-y-auto">
          <div>
            <p className="text-xs text-[#5a5550] uppercase tracking-widest mb-2">Current Build</p>
            <BuildMetaCard build={currentBuild} />
          </div>

          {/* Build history placeholder */}
          <div>
            <p className="text-xs text-[#5a5550] uppercase tracking-widest mb-2">Build History</p>
            {latestBuild ? (
              <div className="rounded-lg border border-[#1a1820] bg-[#08070a] px-3 py-2 text-xs text-[#5a5550]">
                {latestBuild.build_id.slice(0, 8)}… · {latestBuild.status}
              </div>
            ) : (
              <div className="text-xs text-[#5a5550]">No prior builds.</div>
            )}
          </div>
        </aside>

        {/* Main content area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex items-center gap-1 border-b border-[#1a1820] px-4 pt-3 pb-0 bg-[#0d0c10]">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 text-sm rounded-t-md transition-colors ${
                  activeTab === tab.id
                    ? 'text-[#d4a648] border-b-2 border-[#d4a648] bg-transparent font-medium'
                    : 'text-[#8a8070] hover:text-[#c8bfb0]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-auto p-6">
            {activeTab === 'graph' && (
              <LiveBuildGraph
                buildId={currentBuild?.build_id ?? ''}
                chartId={chartId}
              />
            )}

            {activeTab === 'ayanamsha' && (
              <div className="text-[#5a5550] text-sm">
                Per-ayanamsha breakdown — available once build completes.
              </div>
            )}

            {activeTab === 'assets' && (
              <AssetTable
                buildId={currentBuild?.build_id ?? ''}
                chartId={chartId}
                assets={assets}
              />
            )}

            {activeTab === 'eventlog' && (
              <div className="text-[#5a5550] text-sm">
                Event log — streams build events as they arrive.
              </div>
            )}

            {activeTab === 'preview' && (
              <div className="text-[#5a5550] text-sm">
                Data preview — query the built assets here.
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
