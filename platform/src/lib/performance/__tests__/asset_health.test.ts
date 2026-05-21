import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockReadFileSync } = vi.hoisted(() => ({
  mockReadFileSync: vi.fn(),
}))

vi.mock('fs', () => ({
  default: {
    readFileSync: mockReadFileSync,
  },
  readFileSync: mockReadFileSync,
}))

const mockManifest = {
  generated_at: '2026-05-14T00:00:00Z',
  entry_count: 7,
  entries: [
    {
      canonical_id: 'FORENSIC',
      path: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
      layer: 'L1',
      status: 'CURRENT',
      version: '8',
      expose_to_chat: true,
      tool_name: 'query_forensic',
    },
    {
      canonical_id: 'LEL',
      path: '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md',
      layer: 'L1',
      status: 'LIVING',
      version: '1.6',
      expose_to_chat: true,
    },
    {
      canonical_id: 'MSR',
      path: '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md',
      layer: 'L2.5',
      status: 'CURRENT',
      version: '3.1',
      expose_to_chat: true,
      tool_name: 'query_msr',
    },
    {
      canonical_id: 'OLD_PLAN',
      path: '00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md',
      layer: 'governance',
      status: 'SUPERSEDED',
    },
    {
      canonical_id: 'DEAD_FILE',
      path: '00_ARCHITECTURE/DEAD.md',
      layer: 'governance',
      status: 'DEAD_DATA',
    },
    {
      canonical_id: 'CLOSED_FILE',
      path: '00_ARCHITECTURE/CLOSED.md',
      layer: 'governance',
      status: 'GOVERNANCE_CLOSED',
    },
    {
      canonical_id: 'NO_STATUS',
      path: '00_ARCHITECTURE/UNKNOWN.md',
      // no layer, no status
    },
  ],
}

import { getAssetCatalog } from '../asset_health'

beforeEach(() => {
  mockReadFileSync.mockReset()
  mockReadFileSync.mockReturnValue(JSON.stringify(mockManifest))
})

describe('getAssetCatalog()', () => {
  it('returns correct totalCount', () => {
    const catalog = getAssetCatalog()
    expect(catalog.totalCount).toBe(7)
  })

  it('counts only entries with tool_name as reachable', () => {
    const catalog = getAssetCatalog()
    // tool_name present: FORENSIC, MSR → 2
    expect(catalog.reachableCount).toBe(2)
  })

  it('groups entries by layer correctly', () => {
    const catalog = getAssetCatalog()
    expect(catalog.byLayer['L1']).toHaveLength(2)
    expect(catalog.byLayer['L2.5']).toHaveLength(1)
    expect(catalog.byLayer['governance']).toHaveLength(3)
    // no-layer entry goes to 'Other'
    expect(catalog.byLayer['Other']).toHaveLength(1)
  })

  it('assigns correct health badges: CURRENT→green, LIVING→yellow, SUPERSEDED→red', () => {
    const catalog = getAssetCatalog()
    const l1 = catalog.byLayer['L1']
    const forensic = l1.find((e) => e.canonical_id === 'FORENSIC')
    const lel = l1.find((e) => e.canonical_id === 'LEL')
    const governance = catalog.byLayer['governance']
    const oldPlan = governance.find((e) => e.canonical_id === 'OLD_PLAN')
    expect(forensic?.health).toBe('green')
    expect(lel?.health).toBe('yellow')
    expect(oldPlan?.health).toBe('red')
  })

  it('assigns red badge to DEAD_DATA and GOVERNANCE_CLOSED', () => {
    const catalog = getAssetCatalog()
    const governance = catalog.byLayer['governance']
    const dead = governance.find((e) => e.canonical_id === 'DEAD_FILE')
    const closed = governance.find((e) => e.canonical_id === 'CLOSED_FILE')
    expect(dead?.health).toBe('red')
    expect(closed?.health).toBe('red')
  })

  it('assigns gray badge when status is missing', () => {
    const catalog = getAssetCatalog()
    const other = catalog.byLayer['Other']
    const noStatus = other.find((e) => e.canonical_id === 'NO_STATUS')
    expect(noStatus?.health).toBe('gray')
  })
})
