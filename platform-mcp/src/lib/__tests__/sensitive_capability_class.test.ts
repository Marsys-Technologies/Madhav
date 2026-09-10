/**
 * P1 lane G1-A — sensitive-class capabilities are excluded from `consult`.
 *
 * PARIPRASHNA_ARCHITECTURE §2 (doors table) and SAFETY_PRIVACY_TENANCY §3 /
 * abuse case A6. Tested at the REQUEST-TIME gate rather than against the
 * generated manifest, because that is the layer that holds even when the
 * checked-in profile artifact is stale.
 */
import { describe, it, expect } from 'vitest'

import { getAllowedToolNames, resolveMcpProfile, applyProfileGate } from '../mcp_profile.js'
import {
  SENSITIVE_CLASS_CAPABILITIES,
  isSensitiveClassCapability,
  subtractSensitiveClass,
} from '../sensitive_capability_class.js'

describe('the consult allowlist carries no sensitive-class tool', () => {
  it('every sensitive-class name is absent from the resolved consult allowlist', () => {
    const allowed = getAllowedToolNames('consult')
    expect(allowed).not.toBeNull()
    for (const name of SENSITIVE_CLASS_CAPABILITIES) {
      expect(allowed!.has(name), `${name} must not be reachable on the consult profile`).toBe(false)
    }
  })

  it('the consult profile is still non-empty — the exclusion did not empty it', () => {
    expect(getAllowedToolNames('consult')!.size).toBeGreaterThan(0)
  })

  it('`full` is untouched (null = no filter) — it is a scope-gated surface', () => {
    expect(getAllowedToolNames('full')).toBeNull()
  })
})

describe('the gate is registration-time, so an unlisted tool has no dispatch path', () => {
  it('a sensitive tool registration is a no-op under the consult profile', () => {
    const registered: string[] = []
    const server = { tool: (name: string) => registered.push(name) }
    const gate = applyProfileGate(server, 'consult')
    server.tool('get_ayurdaya')
    server.tool('assess_health')
    server.tool('chart_snapshot')
    expect(registered).not.toContain('get_ayurdaya')
    expect(registered).not.toContain('assess_health')
    expect(registered).toContain('chart_snapshot')
    expect(gate.blockedAttempts).toContain('get_ayurdaya')
  })

  it('an unscoped OAuth grant resolves to consult — the population this protects', () => {
    expect(resolveMcpProfile({ authKind: 'oauth', oauthScopes: ['mcp:tools'] })).toBe('consult')
    expect(resolveMcpProfile({ authKind: 'oauth', oauthScopes: undefined })).toBe('consult')
  })
})

describe('subtractSensitiveClass reports what it removed', () => {
  it('returns the removed names rather than silently filtering', () => {
    const { allowed, removed } = subtractSensitiveClass(
      new Set(['chart_snapshot', 'get_ayurdaya', 'assess_health']),
    )
    expect(removed.sort()).toEqual(['assess_health', 'get_ayurdaya'])
    expect([...allowed]).toEqual(['chart_snapshot'])
  })

  it('is a no-op on a clean set', () => {
    const { removed } = subtractSensitiveClass(new Set(['chart_snapshot']))
    expect(removed).toEqual([])
  })
})

describe('what is deliberately NOT sensitive-class', () => {
  it('astrologically-sensitive degree tools are ordinary chart work', () => {
    expect(isSensitiveClassCapability('get_sensitive_degrees')).toBe(false)
    expect(isSensitiveClassCapability('get_sensitive_points')).toBe(false)
  })
})
