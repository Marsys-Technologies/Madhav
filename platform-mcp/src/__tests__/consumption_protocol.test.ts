/**
 * consumption_protocol.test.ts — WP-1.6 (P-12) served-protocol registration proof.
 *
 * Proves the E3 served consumption PROTOCOL is registered as an MCP resource and
 * is retrievable (the resource read handler returns the protocol text), and that
 * the demand_side_chase guided prompt registers. No live server / DB required —
 * uses the mock-server pattern (same as chart_bundle_resource.test.ts).
 */
import { describe, it, expect, vi } from 'vitest'
import { registerConsumptionProtocol, CONSUMPTION_PROTOCOL_TEXT } from '../resources/consumption_protocol.js'
import { registerPrompts } from '../prompts/index.js'
import type { Principal } from '../types.js'

// S-3 (GT-35): registerPrompts now requires a principal so the vidhi_plan prompt it registers
// can run its M0 entitlement gate. Unused by the other prompts these tests exercise.
const TEST_PRINCIPAL: Principal = { user_uid: 'u-consumption-protocol-test', key_id: 'k-cp-test', role: 'guest' }

function makeMockServer() {
  const resourceHandlers = new Map<string, (...a: unknown[]) => unknown>()
  const promptDefs = new Map<string, { description: string; handler: (...a: unknown[]) => unknown }>()
  return {
    resource: vi.fn((name: string, _t: unknown, handler: unknown) => {
      resourceHandlers.set(name, handler as (...a: unknown[]) => unknown)
    }),
    prompt: vi.fn((name: string, description: string, _schema: unknown, handler: unknown) => {
      promptDefs.set(name, { description, handler: handler as (...a: unknown[]) => unknown })
    }),
    getResourceHandler: (name: string) => resourceHandlers.get(name),
    getPrompt: (name: string) => promptDefs.get(name),
  }
}

describe('WP-1.6 served consumption protocol — resource', () => {
  it('registers the consumption-protocol resource', () => {
    const server = makeMockServer()
    registerConsumptionProtocol(server as never)
    expect(server.resource).toHaveBeenCalledTimes(1)
    expect(server.getResourceHandler('consumption-protocol')).toBeTypeOf('function')
  })

  it('is retrievable: the read handler returns the protocol text at marsys://consumption-protocol', async () => {
    const server = makeMockServer()
    registerConsumptionProtocol(server as never)
    const handler = server.getResourceHandler('consumption-protocol')!
    const result = (await handler(new URL('marsys://consumption-protocol'))) as {
      contents: Array<{ uri: string; mimeType: string; text: string }>
    }
    expect(result.contents).toHaveLength(1)
    const c = result.contents[0]!
    expect(c.uri).toBe('marsys://consumption-protocol')
    expect(c.mimeType).toBe('text/markdown')
    expect(c.text).toBe(CONSUMPTION_PROTOCOL_TEXT)
  })

  it('teaches the five demand-side moves + honest exhaustion', () => {
    const t = CONSUMPTION_PROTOCOL_TEXT
    expect(t).toMatch(/E3/)
    expect(t).toMatch(/expected-evidence set/i)
    expect(t).toMatch(/received-vs-needed|received.*needed/i)
    expect(t).toMatch(/honest(ly)? exhaust/i)
    expect(t).toMatch(/bonus, never the frame/i)
    // names every exhaustion reason from the tracker schema
    for (const reason of ['no_route', 'route_empty', 'route_error', 'not_applicable', 'budget_exhausted', 'superseded']) {
      expect(t, `protocol should name reason ${reason}`).toContain(reason)
    }
    // points at the companion surfaces
    expect(t).toContain('CONCEPT_CAPABILITY_MAP.json')
    expect(t).toContain('acquisition_tracker.ts')
    expect(t).toContain('demand_side_chase')
  })
})

describe('WP-1.6 served consumption protocol — guided prompt', () => {
  it('registers demand_side_chase alongside the 3 existing prompts', () => {
    const server = makeMockServer()
    registerPrompts(server as never, TEST_PRINCIPAL)
    expect(server.getPrompt('demand_side_chase')).toBeDefined()
    // the 3 pre-existing R5 prompts still register (no regression)
    for (const p of ['orient_chart', 'assess_domain', 'find_active_yogas']) {
      expect(server.getPrompt(p), `existing prompt ${p} must still register`).toBeDefined()
    }
  })

  it('demand_side_chase emits the five-move chase for the given chart + question', async () => {
    const server = makeMockServer()
    registerPrompts(server as never, TEST_PRINCIPAL)
    const def = server.getPrompt('demand_side_chase')!
    const chart = '482012f1-710e-4a25-994a-93821f5871aa'
    const out = (await def.handler({ chart_id: chart, question: 'How is the marriage?', domain: 'marriage' })) as {
      messages: Array<{ role: string; content: { type: string; text: string } }>
    }
    const text = out.messages[0]!.content.text
    expect(text).toContain(chart)
    expect(text).toContain('How is the marriage?')
    expect(text).toContain('marsys://consumption-protocol')
    expect(text).toMatch(/MOVE 1/)
    expect(text).toMatch(/MOVE 5/)
    expect(text).toMatch(/exhaust/i)
  })
})
