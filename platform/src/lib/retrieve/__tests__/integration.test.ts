import { describe, it, expect, vi } from 'vitest'

vi.mock('server-only', () => ({}))

// Mock storage and telemetry so imports of the tool modules don't fail
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))

import { RETRIEVAL_TOOLS, getTool } from '../index'

describe('RETRIEVAL_TOOLS registry integration', () => {
  it('getTool("nonexistent") returns undefined', () => {
    expect(getTool('nonexistent')).toBeUndefined()
  })

  it('vector_search tool is marked secondary', () => {
    const t = getTool('vector_search')
    expect(t?.secondary).toBe(true)
  })

  it('all tools have a name, version, and retrieve function', () => {
    for (const t of RETRIEVAL_TOOLS) {
      expect(typeof t.name).toBe('string')
      expect(t.name.length).toBeGreaterThan(0)
      expect(typeof t.version).toBe('string')
      expect(typeof t.retrieve).toBe('function')
    }
  })

  it('all tool names in registry are unique', () => {
    const names = RETRIEVAL_TOOLS.map(t => t.name)
    const unique = new Set(names)
    expect(unique.size).toBe(names.length)
  })
})
