import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

// Hoist fs mocks so they are available before module import
const { mockReadFileSync, mockReaddirSync, mockExistsSync } = vi.hoisted(() => ({
  mockReadFileSync: vi.fn(),
  mockReaddirSync: vi.fn(),
  mockExistsSync: vi.fn(),
}))

vi.mock('fs', () => ({
  default: {
    readFileSync: mockReadFileSync,
    readdirSync: mockReaddirSync,
    existsSync: mockExistsSync,
  },
  readFileSync: mockReadFileSync,
  readdirSync: mockReaddirSync,
  existsSync: mockExistsSync,
}))

import { getConflictSummary } from '../conflict_summary'
import type { ConflictRecord } from '../../icr/types'

// ─────────────────────────────────────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────────────────────────────────────

const REPO_ROOT = '/fake/repo'

function makeDetectorOutput(conflicts: ConflictRecord[]): string {
  return JSON.stringify({
    generated_at: '2026-05-21T00:00:00Z',
    corpus_version: 'MSR_v3_0.md',
    conflict_count: conflicts.length,
    conflicts,
  })
}

const BASE_CONFLICT: ConflictRecord = {
  conflict_id: 'DIS.013',
  conflict_class: 'A',
  signal_ids_affected: ['MSR.377'],
  description: 'signal_name asserts sign(s) [Gemini] but falsifier confirms [Virgo] — sign/house mismatch.',
  detected_at: '2026-05-21T08:39:06.325Z',
  evidence: 'some evidence text',
}

const AUTO_CONFLICT: ConflictRecord = {
  conflict_id: 'DIS.AUTO.214',
  conflict_class: 'A',
  signal_ids_affected: ['MSR.214'],
  description: 'signal_name asserts sign(s) [Aries, Leo] but falsifier confirms [Aries].',
  detected_at: '2026-05-21T08:39:06.323Z',
  evidence: 'other evidence',
}

// ─────────────────────────────────────────────────────────────────────────────
// Setup
// ─────────────────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockReadFileSync.mockReset()
  mockReaddirSync.mockReset()
  mockExistsSync.mockReset()
})

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe('getConflictSummary()', () => {
  it('returns empty report when ICR_DETECTOR_OUTPUT_v1_0.json does not exist', () => {
    // existsSync returns false for all paths
    mockExistsSync.mockReturnValue(false)

    const report = getConflictSummary(REPO_ROOT)

    expect(report.total).toBe(0)
    expect(report.entries).toHaveLength(0)
    expect(report.resolved_count).toBe(0)
    expect(report.proposed_count).toBe(0)
    expect(report.open_count).toBe(0)
  })

  it('returns RESOLVED status for a conflict whose ID matches a file in RESOLVED/', () => {
    // Detector output exists; RESOLVED/ has DIS.013_MSR_377_resolved.yaml
    mockExistsSync.mockImplementation((p: string) => {
      if (p.includes('ICR_DETECTOR_OUTPUT')) return true
      if (p.includes('RESOLVED')) return true
      if (p.includes('PROPOSED')) return true
      return false
    })
    mockReadFileSync.mockReturnValue(makeDetectorOutput([BASE_CONFLICT]))
    mockReaddirSync.mockImplementation((dir: string) => {
      if (String(dir).includes('RESOLVED')) return ['DIS.013_MSR_377_resolved.yaml']
      return [] // PROPOSED/ is empty
    })

    const report = getConflictSummary(REPO_ROOT)

    expect(report.total).toBe(1)
    expect(report.resolved_count).toBe(1)
    expect(report.proposed_count).toBe(0)
    expect(report.open_count).toBe(0)
    expect(report.entries[0].status).toBe('RESOLVED')
    expect(report.entries[0].conflict_id).toBe('DIS.013')
  })

  it('returns PROPOSED status for a conflict whose ID matches a file in PROPOSED/', () => {
    mockExistsSync.mockImplementation((p: string) => {
      if (p.includes('ICR_DETECTOR_OUTPUT')) return true
      if (p.includes('PROPOSED')) return true
      if (p.includes('RESOLVED')) return true
      return false
    })
    mockReadFileSync.mockReturnValue(makeDetectorOutput([BASE_CONFLICT]))
    mockReaddirSync.mockImplementation((dir: string) => {
      if (String(dir).includes('PROPOSED')) return ['DIS.013_MSR_377_proposed.yaml']
      return [] // RESOLVED/ empty
    })

    const report = getConflictSummary(REPO_ROOT)

    expect(report.total).toBe(1)
    expect(report.resolved_count).toBe(0)
    expect(report.proposed_count).toBe(1)
    expect(report.open_count).toBe(0)
    expect(report.entries[0].status).toBe('PROPOSED')
  })

  it('returns OPEN status for a conflict with no artifact in either directory', () => {
    mockExistsSync.mockImplementation((p: string) => {
      if (p.includes('ICR_DETECTOR_OUTPUT')) return true
      if (p.includes('PROPOSED')) return true
      if (p.includes('RESOLVED')) return true
      return false
    })
    mockReadFileSync.mockReturnValue(makeDetectorOutput([BASE_CONFLICT]))
    // Both dirs are empty
    mockReaddirSync.mockReturnValue([])

    const report = getConflictSummary(REPO_ROOT)

    expect(report.total).toBe(1)
    expect(report.resolved_count).toBe(0)
    expect(report.proposed_count).toBe(0)
    expect(report.open_count).toBe(1)
    expect(report.entries[0].status).toBe('OPEN')
  })

  it('handles multiple conflicts with mixed statuses correctly', () => {
    // DIS.013 → RESOLVED, DIS.AUTO.214 → OPEN
    mockExistsSync.mockReturnValue(true)
    mockReadFileSync.mockReturnValue(
      makeDetectorOutput([BASE_CONFLICT, AUTO_CONFLICT])
    )
    mockReaddirSync.mockImplementation((dir: string) => {
      if (String(dir).includes('RESOLVED')) return ['DIS.013_MSR_377_resolved.yaml']
      return [] // PROPOSED/ empty
    })

    const report = getConflictSummary(REPO_ROOT)

    expect(report.total).toBe(2)
    expect(report.resolved_count).toBe(1)
    expect(report.proposed_count).toBe(0)
    expect(report.open_count).toBe(1)
    const dis013 = report.entries.find(e => e.conflict_id === 'DIS.013')
    const auto214 = report.entries.find(e => e.conflict_id === 'DIS.AUTO.214')
    expect(dis013?.status).toBe('RESOLVED')
    expect(auto214?.status).toBe('OPEN')
  })

  it('RESOLVED takes precedence over PROPOSED when conflict appears in both directories', () => {
    // Edge case: same conflict_id file in both dirs — RESOLVED wins
    mockExistsSync.mockReturnValue(true)
    mockReadFileSync.mockReturnValue(makeDetectorOutput([BASE_CONFLICT]))
    mockReaddirSync.mockImplementation((dir: string) => {
      if (String(dir).includes('RESOLVED')) return ['DIS.013_MSR_377_resolved.yaml']
      if (String(dir).includes('PROPOSED')) return ['DIS.013_MSR_377_proposed.yaml']
      return []
    })

    const report = getConflictSummary(REPO_ROOT)

    expect(report.entries[0].status).toBe('RESOLVED')
    expect(report.resolved_count).toBe(1)
    expect(report.proposed_count).toBe(0)
  })

  it('preserves all ConflictRecord fields on each entry', () => {
    mockExistsSync.mockReturnValue(true)
    mockReadFileSync.mockReturnValue(makeDetectorOutput([BASE_CONFLICT]))
    mockReaddirSync.mockReturnValue([])

    const report = getConflictSummary(REPO_ROOT)
    const entry = report.entries[0]

    expect(entry.conflict_id).toBe(BASE_CONFLICT.conflict_id)
    expect(entry.conflict_class).toBe(BASE_CONFLICT.conflict_class)
    expect(entry.signal_ids_affected).toEqual(BASE_CONFLICT.signal_ids_affected)
    expect(entry.description).toBe(BASE_CONFLICT.description)
    expect(entry.detected_at).toBe(BASE_CONFLICT.detected_at)
    expect(entry.evidence).toBe(BASE_CONFLICT.evidence)
  })
})
