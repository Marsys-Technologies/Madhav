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

import { getFreshnessReport } from '../freshness'

// Helper to build a manifest JSON string
function makeManifest(entries: Record<string, unknown>[]) {
  return JSON.stringify({ generated_at: '2026-05-01T00:00:00Z', entry_count: entries.length, entries })
}

// A date clearly older than 90 days (use a fixed old date)
const OLD_DATE = '2020-01-01'
// A date clearly within 90 days of any reasonable "now"
const RECENT_DATE = new Date(Date.now() - 10 * 86_400_000).toISOString().slice(0, 10)

beforeEach(() => {
  mockReadFileSync.mockReset()
})

describe('getFreshnessReport()', () => {
  it('returns stale entries for SUPERSEDED status', () => {
    mockReadFileSync.mockReturnValue(
      makeManifest([
        { canonical_id: 'OLD_PLAN', path: '00_ARCHITECTURE/OLD.md', layer: 'governance', status: 'SUPERSEDED' },
        { canonical_id: 'CURRENT_DOC', path: '00_ARCHITECTURE/CURRENT.md', layer: 'governance', status: 'CURRENT' },
      ])
    )
    const report = getFreshnessReport()
    expect(report.stale_assets).toHaveLength(1)
    expect(report.stale_assets[0].canonical_id).toBe('OLD_PLAN')
    expect(report.stale_assets[0].status).toBe('SUPERSEDED')
    expect(report.stale_assets[0].path).toBe('00_ARCHITECTURE/OLD.md')
  })

  it('returns stale entries for DEAD_DATA status', () => {
    mockReadFileSync.mockReturnValue(
      makeManifest([
        { canonical_id: 'DEAD_FILE', path: '00_ARCHITECTURE/DEAD.md', layer: 'governance', status: 'DEAD_DATA' },
        { canonical_id: 'ANOTHER_DEAD', path: '00_ARCHITECTURE/DEAD2.md', layer: 'governance', status: 'DEAD_DATA' },
        { canonical_id: 'ALIVE', path: 'some/file.md', layer: 'L1', status: 'LIVING' },
      ])
    )
    const report = getFreshnessReport()
    expect(report.stale_assets).toHaveLength(2)
    expect(report.stale_assets.every((a) => a.status === 'DEAD_DATA')).toBe(true)
  })

  it('returns aging entry when last_updated is older than threshold', () => {
    mockReadFileSync.mockReturnValue(
      makeManifest([
        {
          canonical_id: 'STALE_ASSET',
          path: '01_FACTS_LAYER/OLD.md',
          layer: 'L1',
          status: 'CURRENT',
          last_updated: OLD_DATE,
        },
      ])
    )
    const report = getFreshnessReport(90)
    expect(report.aging_assets).toHaveLength(1)
    expect(report.aging_assets[0].canonical_id).toBe('STALE_ASSET')
    expect(report.aging_assets[0].last_updated).toBe(OLD_DATE)
    expect(report.aging_assets[0].days_since_update).toBeGreaterThan(90)
  })

  it('does NOT return aging entry when last_updated is within threshold', () => {
    mockReadFileSync.mockReturnValue(
      makeManifest([
        {
          canonical_id: 'FRESH_ASSET',
          path: '01_FACTS_LAYER/FRESH.md',
          layer: 'L1',
          status: 'CURRENT',
          last_updated: RECENT_DATE,
        },
      ])
    )
    const report = getFreshnessReport(90)
    expect(report.aging_assets).toHaveLength(0)
  })

  it('returns empty arrays when all entries are healthy (no stale, no aging)', () => {
    mockReadFileSync.mockReturnValue(
      makeManifest([
        { canonical_id: 'FORENSIC', path: '01_FACTS_LAYER/FORENSIC.md', layer: 'L1', status: 'CURRENT' },
        { canonical_id: 'LEL', path: '01_FACTS_LAYER/LEL.md', layer: 'L1', status: 'LIVING' },
        { canonical_id: 'MSR', path: '025_HOLISTIC_SYNTHESIS/MSR.md', layer: 'L2.5', status: 'CURRENT' },
      ])
    )
    const report = getFreshnessReport()
    expect(report.stale_assets).toHaveLength(0)
    expect(report.aging_assets).toHaveLength(0)
  })

  it('total_scanned equals the number of manifest entries', () => {
    const entries = [
      { canonical_id: 'A', path: 'a.md', layer: 'L1', status: 'CURRENT' },
      { canonical_id: 'B', path: 'b.md', layer: 'L1', status: 'SUPERSEDED' },
      { canonical_id: 'C', path: 'c.md', layer: 'governance', status: 'DEAD_DATA' },
      { canonical_id: 'D', path: 'd.md', layer: 'governance', status: 'LIVING' },
    ]
    mockReadFileSync.mockReturnValue(makeManifest(entries))
    const report = getFreshnessReport()
    expect(report.total_scanned).toBe(4)
  })

  it('uses canonical_id falling back to tool_name then "unknown" for display', () => {
    mockReadFileSync.mockReturnValue(
      makeManifest([
        // no canonical_id, has tool_name
        { tool_name: 'query_foo', path: 'foo.md', layer: 'L1', status: 'SUPERSEDED' },
        // no canonical_id, no tool_name
        { path: 'bar.md', layer: 'L1', status: 'DEAD_DATA' },
      ])
    )
    const report = getFreshnessReport()
    expect(report.stale_assets[0].canonical_id).toBe('query_foo')
    expect(report.stale_assets[1].canonical_id).toBe('unknown')
  })

  it('respects a custom agingThresholdDays parameter', () => {
    // Use 30-day threshold; last_updated 45 days ago should trigger, 10 days ago should not
    const fortyFiveDaysAgo = new Date(Date.now() - 45 * 86_400_000).toISOString().slice(0, 10)
    const tenDaysAgo = new Date(Date.now() - 10 * 86_400_000).toISOString().slice(0, 10)
    mockReadFileSync.mockReturnValue(
      makeManifest([
        { canonical_id: 'A', path: 'a.md', layer: 'L1', status: 'CURRENT', last_updated: fortyFiveDaysAgo },
        { canonical_id: 'B', path: 'b.md', layer: 'L1', status: 'CURRENT', last_updated: tenDaysAgo },
      ])
    )
    const report = getFreshnessReport(30)
    expect(report.aging_assets).toHaveLength(1)
    expect(report.aging_assets[0].canonical_id).toBe('A')
  })
})
