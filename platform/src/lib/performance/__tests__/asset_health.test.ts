import { describe, it, expect } from 'vitest'
import { computeHealthBadge, computeReachability } from '../asset_health'
import type { AssetEntry } from '@/lib/bundle/types'

function entry(overrides: Partial<AssetEntry> = {}): AssetEntry {
  return {
    canonical_id: 'TEST',
    path: 'test/path.md',
    version: '1.0',
    status: 'CURRENT',
    layer: 'L1',
    expose_to_chat: true,
    representations: ['file'],
    interface_version: '1.0',
    fingerprint: 'abc123',
    native_id: 'abhisek',
    ...overrides,
  }
}

describe('computeHealthBadge', () => {
  it('returns green for CURRENT expose_to_chat:true', () => {
    expect(computeHealthBadge(entry({ status: 'CURRENT', expose_to_chat: true }))).toBe('green')
  })

  it('returns green for LIVE', () => {
    expect(computeHealthBadge(entry({ status: 'LIVE', expose_to_chat: true }))).toBe('green')
  })

  it('returns green for ACTIVE', () => {
    expect(computeHealthBadge(entry({ status: 'ACTIVE', expose_to_chat: true }))).toBe('green')
  })

  it('returns yellow for LIVING', () => {
    expect(computeHealthBadge(entry({ status: 'LIVING', expose_to_chat: true }))).toBe('yellow')
  })

  it('returns yellow for STUB', () => {
    expect(computeHealthBadge(entry({ status: 'STUB', expose_to_chat: true }))).toBe('yellow')
  })

  it('returns yellow for DRAFT', () => {
    expect(computeHealthBadge(entry({ status: 'DRAFT', expose_to_chat: true }))).toBe('yellow')
  })

  it('returns red for SUPERSEDED', () => {
    expect(computeHealthBadge(entry({ status: 'SUPERSEDED', expose_to_chat: true }))).toBe('red')
  })

  it('returns red for ARCHIVED', () => {
    expect(computeHealthBadge(entry({ status: 'ARCHIVED', expose_to_chat: true }))).toBe('red')
  })

  it('returns gray for expose_to_chat:false regardless of status', () => {
    expect(computeHealthBadge(entry({ status: 'CURRENT', expose_to_chat: false }))).toBe('gray')
  })

  it('returns gray for governance layer', () => {
    expect(computeHealthBadge(entry({ status: 'CURRENT', expose_to_chat: true, layer: 'governance' }))).toBe('gray')
  })
})

describe('computeReachability', () => {
  it('returns no_tool when bound_tools is empty', () => {
    expect(computeReachability({ ...entry(), bound_tools: [] })).toBe('no_tool')
  })

  it('returns reachable when bound_tools has entries', () => {
    expect(computeReachability({ ...entry(), bound_tools: ['lel_query'] })).toBe('reachable')
  })

  it('returns no_tool when bound_tools is absent', () => {
    expect(computeReachability({ ...entry() })).toBe('no_tool')
  })
})
