'use client'

import { useState } from 'react'
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

  // isBuilding stub for this phase
  const isBuilding = false
  void isBuilding

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
      <CockpitHeader chartId={chartId} />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      {activeTab === 'data' && <DataAssetsView chartId={chartId} />}
      {activeTab === 'workflow' && <WorkflowView />}
      {activeTab === 'agents' && <AgentsView />}
    </div>
  )
}
