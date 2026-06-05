'use client'

import { useState, useEffect, useRef } from 'react'
import { CockpitHeader } from './CockpitHeader'
import { TabBar } from './TabBar'
import { DataAssetsView } from './DataAssetsView'
import { WorkflowView } from './WorkflowView'
import { AgentsView } from './AgentsView'

type Tab = 'data' | 'workflow' | 'agents'

interface Props {
  chartId: string
}

export function CockpitShell({ chartId }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('data')
  const [sidecarHealthy, setSidecarHealthy] = useState(false)
  const healthIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/sidecar/health', { cache: 'no-store' })
        setSidecarHealthy(res.ok)
      } catch {
        setSidecarHealthy(false)
      }
    }

    checkHealth()
    healthIntervalRef.current = setInterval(checkHealth, 30_000)

    return () => {
      if (healthIntervalRef.current) clearInterval(healthIntervalRef.current)
    }
  }, [])

  // isBuilding stub for this phase
  const isBuilding = false

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
      <CockpitHeader chartId={chartId} sidecarHealthy={sidecarHealthy} />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      {activeTab === 'data' && <DataAssetsView chartId={chartId} />}
      {activeTab === 'workflow' && <WorkflowView />}
      {activeTab === 'agents' && <AgentsView />}
    </div>
  )
}
