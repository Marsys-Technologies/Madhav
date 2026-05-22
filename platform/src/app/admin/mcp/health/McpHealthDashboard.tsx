/**
 * McpHealthDashboard — Client-side tabbed dashboard for /admin/mcp/health.
 *
 * Five tabs using the project's Tabs UI component (base-ui/react/tabs).
 * Data fetched via React Query from the /api/mcp/health/* endpoints built in S4.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ToolHealth } from './tabs/ToolHealth'
import { DataCoverage } from './tabs/DataCoverage'
import { AuditFindings } from './tabs/AuditFindings'
import { PredictionsCalibration } from './tabs/PredictionsCalibration'
import { Sessions } from './tabs/Sessions'

const TABS = [
  { value: 'tool-health',        label: 'Tool Health' },
  { value: 'data-coverage',      label: 'Data Coverage' },
  { value: 'audit-findings',     label: 'Audit Findings' },
  { value: 'predictions',        label: 'Predictions / Calibration' },
  { value: 'sessions',           label: 'Sessions' },
] as const

export function McpHealthDashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-serif text-3xl font-medium tracking-wide text-brand-gold-cream">
          MCP Health Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Operator view: tool health, data coverage, audit findings, calibration, and session traces.
        </p>
      </div>

      {/* Tabs */}
      <Tabs
        defaultValue="tool-health"
      >
        <TabsList>
          {TABS.map(tab => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="tool-health" className="mt-4">
          <ToolHealth />
        </TabsContent>

        <TabsContent value="data-coverage" className="mt-4">
          <DataCoverage />
        </TabsContent>

        <TabsContent value="audit-findings" className="mt-4">
          <AuditFindings />
        </TabsContent>

        <TabsContent value="predictions" className="mt-4">
          <PredictionsCalibration />
        </TabsContent>

        <TabsContent value="sessions" className="mt-4">
          <Sessions />
        </TabsContent>
      </Tabs>
    </div>
  )
}
