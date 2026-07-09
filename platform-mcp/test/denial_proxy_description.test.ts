/**
 * R5.1 C2 item 3 (Denial ≠ empty) — proxy-side error description.
 *
 * The MCP-facing proxy helpers (registry_bridge.ts's callPlatformPrimitive,
 * register_p1_aliases.ts's callPlatformPrim) used to collapse ANY non-2xx response from
 * /api/mcp/primitives/{tool} into a generic "failed (401)" string, losing the platform's
 * distinct `entitlement_denied` / `denial` signal by the time it reaches the MCP tool
 * caller. Asserts the description helpers now surface the denial legibly, and still fall
 * back to a generic message for every other error shape (never invents a denial that
 * wasn't actually reported).
 */
import { describe, it, expect } from 'vitest'
import { describeProxyFailure } from '../src/tools/registry_bridge.js'
import { describePrimFailure } from '../src/tools/register_p1_aliases.js'

const DENIAL_BODY = JSON.stringify({
  ok: false,
  trace_id: '',
  error: { class: 'entitlement_denied', message: 'AUTHZ_DENIED: caller does not have view access to chart cb73cd3d-9eba-4220-9902-0de91566e980.' },
  denial: {
    reason: 'entitlement',
    chart_id: 'cb73cd3d-9eba-4220-9902-0de91566e980',
    permission_found: 'deny',
    permission_required: 'view',
    distinct_from_empty: true,
  },
})

describe('describeProxyFailure (registry_bridge)', () => {
  it('surfaces ENTITLEMENT_DENIED with the chart_id and required permission when the platform returns the distinct denial envelope', () => {
    const msg = describeProxyFailure('query_chart_facts', 401, DENIAL_BODY)
    expect(msg).toContain('ENTITLEMENT_DENIED')
    expect(msg).toContain('cb73cd3d-9eba-4220-9902-0de91566e980')
    expect(msg).toContain('view')
  })

  it('falls back to a generic message for a non-denial error (never invents a denial that was not reported)', () => {
    const msg = describeProxyFailure('query_chart_facts', 500, 'internal error')
    expect(msg).not.toContain('ENTITLEMENT_DENIED')
    expect(msg).toContain('failed (500)')
  })
})

describe('describePrimFailure (register_p1_aliases)', () => {
  it('surfaces ENTITLEMENT_DENIED the same way as the registry_bridge proxy', () => {
    const msg = describePrimFailure('ganita_chart_facts_get', 401, DENIAL_BODY)
    expect(msg).toContain('ENTITLEMENT_DENIED')
    expect(msg).toContain('cb73cd3d-9eba-4220-9902-0de91566e980')
  })

  it('falls back to a generic message for a non-denial error', () => {
    const msg = describePrimFailure('ganita_chart_facts_get', 500, 'boom')
    expect(msg).not.toContain('ENTITLEMENT_DENIED')
  })
})
