import { describe, expect, it, beforeEach, afterEach } from 'vitest'
import { filterLeakedCapabilities } from '@/lib/pipeline/no_leakage_filter'
import { registerCapability, clearRegistry, getAllCapabilities } from '@/lib/retrieval/registry'
import type { CapabilityDescriptor } from '@/lib/retrieval/registry/types'

// ── Fake capability fixtures (isolated registry — cleared before/after each test) ──

function fakeCapability(overrides: Partial<CapabilityDescriptor> & { uri: string }): CapabilityDescriptor {
  return {
    type: 'tool',
    layer: 'L1',
    name: overrides.uri,
    description: 'fixture capability for no_leakage_filter tests',
    handler: async () => ({ ok: true, data: [] }),
    archetype: 'flat_fact',
    traversal_level: 'L-SIGNAL',
    tool_role: 'leaf',
    scope: 'global',
    ...overrides,
  } as CapabilityDescriptor
}

describe('filterLeakedCapabilities', () => {
  beforeEach(() => {
    clearRegistry()
    registerCapability(fakeCapability({ uri: 'marsys://tool/L1/fixture_leaked', calibration_context_only: true }))
    registerCapability(fakeCapability({ uri: 'marsys://tool/L1/fixture_explicit_false', calibration_context_only: false }))
    registerCapability(fakeCapability({ uri: 'marsys://tool/L1/fixture_absent' }))
  })

  afterEach(() => {
    clearRegistry()
  })

  it('drops only capabilities flagged calibration_context_only: true (URI-as-name form)', () => {
    const result = filterLeakedCapabilities([
      'marsys://tool/L1/fixture_leaked',
      'marsys://tool/L1/fixture_explicit_false',
      'marsys://tool/L1/fixture_absent',
    ])
    expect(result).toEqual([
      'marsys://tool/L1/fixture_explicit_false',
      'marsys://tool/L1/fixture_absent',
    ])
  })

  it('is a pure function — does not mutate the input array', () => {
    const input = [
      'marsys://tool/L1/fixture_leaked',
      'marsys://tool/L1/fixture_absent',
    ]
    const copy = [...input]
    filterLeakedCapabilities(input)
    expect(input).toEqual(copy)
  })

  it('fails open on a tool name with no registered capability (unresolvable name)', () => {
    const result = filterLeakedCapabilities(['no_such_tool_at_all'])
    expect(result).toEqual(['no_such_tool_at_all'])
  })

  it('returns an empty array when every capability is leaked', () => {
    const result = filterLeakedCapabilities(['marsys://tool/L1/fixture_leaked'])
    expect(result).toEqual([])
  })

  it('handles an empty input array', () => {
    expect(filterLeakedCapabilities([])).toEqual([])
  })

  it('sanity: fixture registry actually has the leaked capability registered', () => {
    // Guards against a false-negative test — confirms our fixture setup is real,
    // not silently no-op'd (e.g. registerCapability throwing and being swallowed).
    const uris = getAllCapabilities().map((c) => c.uri)
    expect(uris).toContain('marsys://tool/L1/fixture_leaked')
  })
})
