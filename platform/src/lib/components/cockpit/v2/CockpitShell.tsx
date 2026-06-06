'use client'

import { useState } from 'react'
import { CockpitHeader } from './CockpitHeader'
import { TabBar } from './TabBar'
import { DataAssetsView } from './DataAssetsView'
import { WorkflowView } from './WorkflowView'
import { AgentsView } from './AgentsView'
import { useChartContext } from '@/hooks/useChartContext'

type Tab = 'data' | 'workflow' | 'agents'

interface Props {
  chartId: string
}

export function CockpitShell({ chartId }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('data')
  const { chartName, birthDate, birthPlace } = useChartContext(chartId)

  console.log('[Shell] render — chartName=', chartName, 'birthDate=', birthDate)

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
      />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      {activeTab === 'data' && <DataAssetsView chartId={chartId} />}
      {activeTab === 'workflow' && <WorkflowView />}
      {activeTab === 'agents' && <AgentsView />}
    </div>
  )
}
