/**
 * wp13i_apex_assess_dedup.test.ts — WP-1.3(i) / LCA-11 apex_ / assess_ dedup proof
 * ================================================================================
 * LCA-11: the four apex_*_assess tools (register_p1_aliases.ts) were strict
 * near-duplicates of the canonical assess_* tools (registry_bridge.ts) — BOTH
 * families resolved to the SAME registry URI (marsys://tool/L-DOMAIN/assess_*).
 *
 * Disposition (§7.3): apex_*_assess RETIRED; capability preserved on the canonical
 * assess_* tools, which now also carry the two tuning params the apex_* variants
 * uniquely exposed (max_signals_per_lens / max_contradictions) — a strict superset,
 * so NO capability is lost.
 *
 * This test registers both tool sets against a mock McpServer and proves:
 *   1. NO apex_*_assess tool name is registered any more (duplicate surface gone).
 *   2. All four canonical assess_* tools ARE still registered (capability reachable).
 *   3. Each canonical assess_* tool exposes the migrated tuning params (no drop).
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { registerP1AliasTools } from '../tools/register_p1_aliases.js'
import { registerRegistryBridgeTools } from '../tools/registry_bridge.js'
import type { Principal } from '../types.js'

function makePrincipal(): Principal {
  return { user_uid: 'user-test-wp13i', key_id: 'mcp_test_wp13i01', role: 'guest' }
}

interface Registered { name: string; schema: Record<string, unknown> }

const registered = new Map<string, Registered>()

beforeAll(() => {
  registered.clear()
  const mockServer = {
    tool: (...args: unknown[]) => {
      // server.tool(name, description, schema, handler)
      const name = args[0] as string
      const schema = (args[2] as Record<string, unknown>) ?? {}
      registered.set(name, { name, schema })
    },
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const srv = mockServer as any
  const principal = makePrincipal()
  registerRegistryBridgeTools(srv, principal)
  registerP1AliasTools(srv, principal)
})

const APEX = ['apex_marriage_assess', 'apex_career_assess', 'apex_health_assess', 'apex_wealth_assess']
const ASSESS = ['assess_marriage', 'assess_career', 'assess_health', 'assess_wealth']

describe('WP-1.3(i)/LCA-11 — apex_*_assess duplicate family retired', () => {
  it('registers ZERO apex_*_assess tools (redundant surface removed)', () => {
    for (const name of APEX) {
      expect(registered.has(name), `${name} should be retired but is still registered`).toBe(false)
    }
  })
})

describe('WP-1.3(i)/LCA-11 — capability still reachable via canonical assess_*', () => {
  it('registers all four canonical assess_* tools', () => {
    for (const name of ASSESS) {
      expect(registered.has(name), `${name} must remain registered (capability reachability)`).toBe(true)
    }
  })

  it('canonical assess_* tools expose the migrated tuning params (no capability drop)', () => {
    for (const name of ASSESS) {
      const schema = registered.get(name)!.schema
      expect(Object.keys(schema), `${name} missing max_signals_per_lens`).toContain('max_signals_per_lens')
      expect(Object.keys(schema), `${name} missing max_contradictions`).toContain('max_contradictions')
      expect(Object.keys(schema)).toContain('chart_id')
    }
  })
})
