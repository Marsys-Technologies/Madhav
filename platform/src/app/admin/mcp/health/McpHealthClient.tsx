'use client'
/**
 * McpHealthClient — Tab shell for the MCP Health Dashboard (v3.4-S1)
 *
 * Tab 4 (Predictions/Calibration) is implemented fully.
 * Tabs 1–3, 5 show placeholders until WT-A merges their components.
 */

import { useState } from 'react'
import { PredictionsCalibration } from './tabs/PredictionsCalibration'

type Tab = 'tool-health' | 'data-coverage' | 'audit-findings' | 'calibration' | 'sessions'

const TABS: { id: Tab; label: string }[] = [
  { id: 'tool-health',    label: 'Tool Health' },
  { id: 'data-coverage',  label: 'Data Coverage' },
  { id: 'audit-findings', label: 'Audit Findings' },
  { id: 'calibration',    label: 'Predictions / Calibration' },
  { id: 'sessions',       label: 'Sessions' },
]

function PlaceholderTab({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border p-10 text-center">
      <p className="text-sm text-muted-foreground font-medium">{label}</p>
      <p className="text-xs text-muted-foreground mt-1">
        Implemented in WT-A (v3.1.0-S5). Available after feature/mcpt-foundation merges.
      </p>
    </div>
  )
}

export function McpHealthClient() {
  const [activeTab, setActiveTab] = useState<Tab>('calibration')

  return (
    <div>
      {/* Tab nav */}
      <div className="flex border-b border-border mb-6 gap-1">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={[
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border',
            ].join(' ')}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'tool-health'    && <PlaceholderTab label="Tool Health" />}
      {activeTab === 'data-coverage'  && <PlaceholderTab label="Data Coverage" />}
      {activeTab === 'audit-findings' && <PlaceholderTab label="Audit Findings" />}
      {activeTab === 'calibration'    && <PredictionsCalibration />}
      {activeTab === 'sessions'       && <PlaceholderTab label="Sessions" />}
    </div>
  )
}
