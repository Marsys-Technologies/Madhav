/**
 * kp_descriptor_text.test.ts: the MCP-side tool text for KP-frame reads agrees with the one-frame rule
 * (Lahiri-primary combined batch). ganita_kp_cusps_get ALWAYS reads krishnamurti (the platform handler
 * ignores any passed id and reports a different explicit id in ayanamsha_note), so its description and
 * ayanamsha_id text must not say the id selects another ayanamsha. The shared chart-facts and dasha tools
 * carry the KP exception. Behaviour is pinned by kp_cusps_one_frame.test.ts and kp_reaching_wrappers.test.ts.
 */
import { describe, it, expect, vi } from 'vitest'
import type { z } from 'zod'

process.env['SERVICE_TOKEN'] = 'test-service-token'
vi.mock('../src/lib/authz.js', () => ({ remoteAuthorize: vi.fn().mockResolvedValue(true) }))

import { registerP1GanitaTools } from '../src/tools/register_p1_ganita.js'
import { registerP1AliasTools } from '../src/tools/register_p1_aliases.js'
import { registerRegistryBridgeTools } from '../src/tools/registry_bridge.js'

const PRINCIPAL = { user_uid: 'test-uid', audience_tier: 'super_admin' as const, key_id: 'test-key-001' }
const LABEL = 'KP frame (Krishnamurti ayanamsha)'

interface Captured { description: string; schema: Record<string, z.ZodTypeAny> }

function capture(register: (server: never, principal: never) => void): Map<string, Captured> {
  const tools = new Map<string, Captured>()
  const server = {
    tool: (name: string, description: string, schema: Record<string, z.ZodTypeAny>) => {
      tools.set(name, { description, schema })
    },
  }
  register(server as never, PRINCIPAL as never)
  return tools
}

function describeOf(tools: Map<string, Captured>, tool: string, field: string): string {
  const t = tools.get(tool)
  expect(t, `${tool} registered`).toBeDefined()
  const f = t!.schema[field]
  expect(f, `${tool}.${field}`).toBeDefined()
  return String((f as z.ZodTypeAny).description ?? '')
}

describe('MCP KP descriptor text', () => {
  it('ganita_kp_cusps_get: always krishnamurti; the id is accepted but not applied', () => {
    const tools = capture(registerP1GanitaTools as never)
    const t = tools.get('ganita_kp_cusps_get')!
    expect(t.description).toContain(LABEL)
    expect(t.description).toMatch(/always reads krishnamurti, whatever ayanamsha_id is passed/)
    expect(t.description).not.toMatch(/inspect the KP chain in another stored ayanamsha/)
    expect(t.description).not.toMatch(/Defaults to the KP-canonical/)
    const idText = describeOf(tools, 'ganita_kp_cusps_get', 'ayanamsha_id')
    expect(idText).toMatch(/NOT applied/)
    expect(idText).toMatch(/ayanamsha_note/)
    expect(idText).not.toMatch(/Also: lahiri_chitrapaksha/)
  })

  it('ganita_chart_facts_get and the dasha tools carry the KP exception', () => {
    const tools = capture(registerP1AliasTools as never)
    const cf = tools.get('ganita_chart_facts_get')!
    expect(cf.description).toMatch(/KP-frame categories[^;]*always read at krishnamurti/)
    expect(describeOf(tools, 'ganita_chart_facts_get', 'ayanamsha_id')).toMatch(/KP exception \(one frame by doctrine\)/)
    for (const name of ['ganita_dashas_get', 'ganita_dasha_periods_get', 'query_dasha_periods']) {
      const t = tools.get(name)
      expect(t, name).toBeDefined()
      expect(t!.description, name).toMatch(/system=vimshottari_kp[^.]*always read at krishnamurti/)
      expect(describeOf(tools, name, 'ayanamsha_id'), name).toMatch(/system=vimshottari_kp\) is always read at krishnamurti/)
      expect(describeOf(tools, name, 'system'), name).toMatch(/vimshottari_kp/)
    }
  })

  it('query_chart_facts: one ayanamsha per page, KP-frame categories excepted', () => {
    const tools = capture(registerRegistryBridgeTools as never)
    const q = tools.get('query_chart_facts')!
    expect(q.description).not.toMatch(/single ayanamsha per call/)
    expect(q.description).toMatch(/KP-frame categories are always read at krishnamurti/)
    expect(describeOf(tools, 'query_chart_facts', 'ayanamsha_id')).toMatch(/KP exception \(one frame by doctrine\)/)
  })
})
