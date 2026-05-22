/**
 * /admin/mcp/health — MCP Operator Dashboard (5 tabs).
 *
 * Super-admin only (enforced by admin layout.tsx → getServerUserWithProfile role check).
 * Tabs:
 *   1. Tool Health — sortable table of per-tool metrics + inline caveat editor
 *   2. Data Coverage — per-asset coverage bars + expected vs actual
 *   3. Audit Findings — findings table + drill-down modal + resolve action
 *   4. Predictions / Calibration — placeholder for v3.4-P6 calibration MV
 *   5. Sessions — recent sessions/traces table
 *
 * MCPT v3.1.0-S5
 */

import type { Metadata } from 'next'
import { McpHealthDashboard } from './McpHealthDashboard'

export const metadata: Metadata = {
  title: 'MCP Health — Admin — MARSYS-JIS',
}

export default function McpHealthPage() {
  return <McpHealthDashboard />
}
