/**
 * kp_cusps_bridge_no_inject.test.ts — SS N-368 (Lahiri primary, PR-4), the platform half of the MCP
 * `ganita_kp_cusps_get` alignment: for the KP-frame capability `get_kp_cusps`, the two platform entry
 * points inject NOTHING when the caller named no ayanamsha, and the REAL handler then reads krishnamurti.
 *
 *   - web bridge: getToolByName('marsys://tool/L1/get_kp_cusps').retrieve(...)  (injects Lahiri for ordinary
 *     capabilities; KP_FRAME_CAPABILITY_URIS are exempt);
 *   - MCP capability route: applyAyanamshaContractForCapability(cap, args, { inject: false }).
 *
 * The handler is spied, not replaced (call-through); the database is a recording stub (no DB). What this
 * proves: the args the handler receives carry no ayanamsha_id and no injection marker, and the SQL is bound
 * to 'krishnamurti'. (The "does not apply" note itself is PR-2's handler; it lands with the batch and is
 * covered by PR-2's kp_no_false_note.bridge.test.ts.)
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const hoisted = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: hoisted.mockQuery }))

import { getCapability } from '../index'
import { getCatalog } from '../catalog'
import { getToolByName } from '../tool_name_bridge'
import { applyAyanamshaContractForCapability, shouldInjectPrimaryAyanamsha } from '../../chart_facts_helpers'
import { KP_FRAME_CAPABILITY_URIS } from '../constants'
import type { CapabilityDescriptor } from '../types'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const URI = 'marsys://tool/L1/get_kp_cusps'

function cap(): CapabilityDescriptor {
  getCatalog()
  const c = (getCapability(URI as never) ?? getCatalog().find((x) => x.uri === URI)) as CapabilityDescriptor
  expect(c).toBeDefined()
  return c
}

beforeEach(() => {
  hoisted.mockQuery.mockReset()
  hoisted.mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
})
afterEach(() => { vi.restoreAllMocks() })

function boundAyanamshaIds(): unknown[] {
  return hoisted.mockQuery.mock.calls.map(([, params]) => (params as unknown[])[1])
}

describe('get_kp_cusps is a KP-frame capability: no Lahiri injection anywhere', () => {
  it('is in KP_FRAME_CAPABILITY_URIS, declares ayanamsha_id, and shouldInjectPrimaryAyanamsha is false', () => {
    expect(KP_FRAME_CAPABILITY_URIS.has(URI)).toBe(true)
    expect(Object.prototype.hasOwnProperty.call(cap().input_schema ?? {}, 'ayanamsha_id')).toBe(true)
    expect(shouldInjectPrimaryAyanamsha({ uri: URI }, { chart_id: CHART_ID })).toBe(false)
  })

  it('MCP route contract (inject:false): an omitted id stays omitted, no marker', () => {
    const out = applyAyanamshaContractForCapability(cap(), { chart_id: CHART_ID }, { inject: false })
    expect(out).not.toHaveProperty('ayanamsha_id')
    expect(out).not.toHaveProperty('ayanamsha_injected')
  })

  it('MCP route contract: an explicit id is kept (alias -> stored id), "all" becomes the unfiltered scope', () => {
    expect(applyAyanamshaContractForCapability(cap(), { chart_id: CHART_ID, ayanamsha_id: 'LAHIRI' }, { inject: false }))
      .toMatchObject({ ayanamsha_id: 'lahiri_chitrapaksha' })
    const all = applyAyanamshaContractForCapability(cap(), { chart_id: CHART_ID, ayanamsha_id: 'all' }, { inject: false })
    expect(all).not.toHaveProperty('ayanamsha_id')
    expect(all).toMatchObject({ ayanamsha_scope: 'all' })
  })

  it('web bridge -> REAL handler: no ayanamsha_id / marker reaches the handler and the SQL reads krishnamurti', async () => {
    const c = cap()
    const spy = vi.spyOn(c, 'handler')
    const tool = getToolByName(URI)
    expect(tool, 'getToolByName(get_kp_cusps)').toBeDefined()
    await tool!.retrieve({ chart_id: CHART_ID }, {})
    expect(spy).toHaveBeenCalledTimes(1)
    const received = spy.mock.calls[0]![0] as Record<string, unknown>
    expect(received).not.toHaveProperty('ayanamsha_id')
    expect(received).not.toHaveProperty('ayanamsha_injected')
    expect(hoisted.mockQuery).toHaveBeenCalled()
    expect(boundAyanamshaIds()).toEqual(expect.arrayContaining(['krishnamurti']))
    expect(boundAyanamshaIds().every((id) => id === 'krishnamurti')).toBe(true)
  })

  it('direct handler call with no id (what the MCP route does after the contract): krishnamurti, labelled by the wrapper', async () => {
    const res = await cap().handler({ chart_id: CHART_ID }, {} as never) as { content: Record<string, unknown> }
    expect(res.content['ayanamsha_id']).toBe('krishnamurti')
    expect(boundAyanamshaIds().every((id) => id === 'krishnamurti')).toBe(true)
  })
})
