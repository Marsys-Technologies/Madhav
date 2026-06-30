/**
 * authz.ts — Remote chart authorization helper for the MCP sidecar.
 *
 * Calls POST /api/mcp/authz on the platform to check whether a principal
 * is allowed to access a specific chart. Used by chart-scoped tool handlers
 * that call the Python sidecar directly (phala, mimamsa, holistic tools).
 *
 * Returns true when authorized, false when denied.
 * Never throws — callers receive false on any network or parse error.
 *
 * M0 entitlement gate (2026-06-30).
 */

import type { Principal } from '../types.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

/**
 * Check whether principal may access chart_id.
 *
 * @param principal  The MCP principal from Bearer key validation.
 * @param chartId    The chart_id to gate against.
 * @param required   'view' for reads (default); 'all' for writes (record_outcome).
 * @returns true if authorized, false if denied or on error (fail-closed).
 */
export async function remoteAuthorize(
  principal: Principal,
  chartId: string,
  required: 'view' | 'all' = 'view'
): Promise<boolean> {
  try {
    const response = await fetch(`${PLATFORM_URL}/api/mcp/authz`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      },
      body: JSON.stringify({ user_uid: principal.user_uid, chart_id: chartId, required }),
      signal: AbortSignal.timeout(5000),
    })
    if (!response.ok) return false
    const data = (await response.json()) as { authorized?: boolean }
    return data.authorized === true
  } catch {
    return false
  }
}
