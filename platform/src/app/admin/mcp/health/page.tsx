/**
 * /admin/mcp/health — MCP Performance, Audit & Calibration Dashboard
 *
 * Five tabs per perf brief §7:
 *   1. Tool Health      — mv_tool_metrics_24h (WT-A creates)
 *   2. Data Coverage    — mv_data_source_coverage (WT-A creates)
 *   3. Audit Findings   — mcp_audit_findings (WT-A creates)
 *   4. Predictions / Calibration — mv_calibration_score (THIS FILE, v3.4-S1)
 *   5. Sessions         — tool_execution_log session rollup (WT-A creates)
 *
 * Tabs 1, 2, 3, 5 render placeholder text until WT-A merges their components.
 * Tab 4 (PredictionsCalibration) is fully implemented in this session (v3.4-S1).
 */

import { Suspense } from 'react'
import { McpHealthClient } from './McpHealthClient'

export const dynamic = 'force-dynamic'

export default function McpHealthPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">MCP Health Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Tool health · Data coverage · Audit findings · Calibration · Sessions
          </p>
        </div>
        <Suspense fallback={<div className="text-sm text-muted-foreground">Loading…</div>}>
          <McpHealthClient />
        </Suspense>
      </div>
    </div>
  )
}
