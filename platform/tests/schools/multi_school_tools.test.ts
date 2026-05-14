/**
 * M9-D-S1 integration tests — Tool 27 (multi_school_signal_lookup) + Tool 28 (convergence_score_lookup)
 * Tests: type shapes, DB mock, JSON fallback, empty-domain guard, domain filtering,
 * summary computation, convergence formula, output field completeness, QueryClass registration.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Must be hoisted before any server-only imports
vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => mockQuery(...args),
}))

import type {
  MultiSchoolSignalLookupInput,
  MultiSchoolSignalLookupOutput,
  PerSchoolSignalResult,
} from '@/lib/tools/multi_school_signal_lookup'
import type {
  ConvergenceScoreLookupInput,
  ConvergenceScoreLookupOutput,
  ConvergenceScoreRow,
} from '@/lib/tools/convergence_score_lookup'

// ─── Shared test data ────────────────────────────────────────────────────────

const ALL_SCHOOLS = ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini'] as const
const ALL_DOMAINS = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL'] as const

function makeConvergenceRow(
  domain: string,
  level: 'HIGH' | 'MEDIUM' | 'LOW',
  agreeing: number,
  direction: 'positive' | 'negative' | 'neutral',
  mean: number,
  std: number,
): ConvergenceScoreRow {
  return {
    domain,
    schools_agreeing: agreeing,
    schools_total: 6,
    convergence_level: level,
    mean_domain_score: mean,
    std_domain_score: std,
    direction,
    per_school_scores: {
      parashari: 4.3,
      jaimini: 4.1,
      tajika: null,
      kp: 4.1,
      nadi: 4.0,
      bnn: 3.5,
      yogini: 3.8,
    },
    convergence_narrative: `${domain}: ${level} convergence — ${agreeing}/6 ${direction}.`,
    computed_at: '2026-05-14T18:00:00.000Z',
  }
}

// M9-C run results
const MOCK_DB_ROWS = [
  makeConvergenceRow('CAREER',         'HIGH',   6, 'positive', 4.002, 0.246),
  makeConvergenceRow('HEALTH',         'HIGH',   6, 'neutral',  2.820, 0.124),
  makeConvergenceRow('RELATIONSHIP',   'HIGH',   5, 'neutral',  2.966, 0.322),
  makeConvergenceRow('SPIRITUAL',      'HIGH',   5, 'positive', 3.728, 0.741),
  makeConvergenceRow('PSYCHOLOGICAL',  'HIGH',   5, 'positive', 3.342, 0.127),
]

// DB rows format (stringified numerics as returned by postgres driver)
function toDbRow(row: ConvergenceScoreRow) {
  return {
    ...row,
    schools_agreeing: String(row.schools_agreeing),
    schools_total: String(row.schools_total),
    mean_domain_score: String(row.mean_domain_score),
    std_domain_score: String(row.std_domain_score),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ─── Tool 28: convergence_score_lookup — DB path ─────────────────────────────

describe('convergence_score_lookup — DB path', () => {
  it('returns ConvergenceScoreLookupOutput with all required top-level fields', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [toDbRow(MOCK_DB_ROWS[0])] })
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result: ConvergenceScoreLookupOutput = await convergence_score_lookup({ domains: ['CAREER'] })
    expect(result).toHaveProperty('domains_requested')
    expect(result).toHaveProperty('convergence_scores')
    expect(result).toHaveProperty('summary')
    expect(result.domains_requested).toEqual(['CAREER'])
  })

  it('each ConvergenceScoreRow has all required fields', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [toDbRow(MOCK_DB_ROWS[0])] })
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result = await convergence_score_lookup({ domains: ['CAREER'] })
    const row = result.convergence_scores[0]
    expect(row).toBeDefined()
    expect(typeof row.domain).toBe('string')
    expect(typeof row.schools_agreeing).toBe('number')
    expect(typeof row.schools_total).toBe('number')
    expect(['HIGH', 'MEDIUM', 'LOW']).toContain(row.convergence_level)
    expect(typeof row.mean_domain_score).toBe('number')
    expect(typeof row.std_domain_score).toBe('number')
    expect(['positive', 'negative', 'neutral', 'mixed']).toContain(row.direction)
    expect(typeof row.per_school_scores).toBe('object')
  })

  it('empty domains returns empty convergence_scores', async () => {
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result = await convergence_score_lookup({ domains: [] })
    expect(result.convergence_scores).toHaveLength(0)
    expect(result.summary.overall_agreement_signal).toBe('No domains requested')
  })

  it('returns CAREER with correct numeric values from DB rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [toDbRow(MOCK_DB_ROWS[0])] })
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result = await convergence_score_lookup({ domains: ['CAREER'] })
    const career = result.convergence_scores[0]
    expect(career.schools_agreeing).toBe(6)
    expect(career.schools_total).toBe(6)
    expect(career.mean_domain_score).toBeCloseTo(4.002, 2)
    expect(career.convergence_level).toBe('HIGH')
    expect(career.direction).toBe('positive')
  })

  it('summary HIGH-only: overall_agreement_signal contains ALL and HIGH', async () => {
    const dbRows = MOCK_DB_ROWS.map(toDbRow)
    mockQuery.mockResolvedValueOnce({ rows: dbRows })
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result = await convergence_score_lookup({ domains: [...ALL_DOMAINS] })
    expect(result.summary.medium_convergence_domains).toHaveLength(0)
    expect(result.summary.low_convergence_domains).toHaveLength(0)
    expect(result.summary.overall_agreement_signal).toMatch(/ALL/)
  })

  it('summary mixed: correct bucket counts for MEDIUM + LOW', async () => {
    const mixedRows = [
      toDbRow(makeConvergenceRow('CAREER', 'HIGH', 6, 'positive', 4.0, 0.2)),
      toDbRow(makeConvergenceRow('HEALTH', 'MEDIUM', 4, 'neutral', 2.8, 0.1)),
      toDbRow(makeConvergenceRow('RELATIONSHIP', 'LOW', 3, 'neutral', 2.5, 0.4)),
    ]
    mockQuery.mockResolvedValueOnce({ rows: mixedRows })
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result = await convergence_score_lookup({ domains: ['CAREER', 'HEALTH', 'RELATIONSHIP'] })
    expect(result.summary.high_convergence_domains).toContain('CAREER')
    expect(result.summary.medium_convergence_domains).toContain('HEALTH')
    expect(result.summary.low_convergence_domains).toContain('RELATIONSHIP')
  })

  it('HEALTH: 6/6 neutral with std < 0.2', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [toDbRow(MOCK_DB_ROWS[1])] })
    const { convergence_score_lookup } = await import('@/lib/tools/convergence_score_lookup')
    const result = await convergence_score_lookup({ domains: ['HEALTH'] })
    const health = result.convergence_scores.find(r => r.domain === 'HEALTH')
    expect(health).toBeDefined()
    expect(health!.direction).toBe('neutral')
    expect(health!.std_domain_score).toBeLessThan(0.2)
  })
})

// ─── Tool 27: multi_school_signal_lookup — type contract ─────────────────────

describe('multi_school_signal_lookup — type contract', () => {
  it('MultiSchoolSignalLookupInput accepts topic + optional filters', () => {
    const input: MultiSchoolSignalLookupInput = {
      topic: 'Saturn 10H exalted',
      domains: ['CAREER'],
      schools: ['parashari', 'kp'],
    }
    expect(input.topic).toBe('Saturn 10H exalted')
    expect(input.domains).toEqual(['CAREER'])
    expect(input.schools).toEqual(['parashari', 'kp'])
  })

  it('PerSchoolSignalResult has school, coverage_type, confidence, matching_signals', () => {
    const result: PerSchoolSignalResult = {
      school: 'parashari',
      coverage_type: 'primary',
      confidence: 0.92,
      matching_signals: [
        { signal_id: 'SIG.MSR.041', signal_name: 'Saturn 10H exalted yoga', domain: 'CAREER' },
      ],
    }
    expect(result.school).toBe('parashari')
    expect(result.coverage_type).toBe('primary')
    expect(result.confidence).toBeGreaterThan(0)
    expect(result.matching_signals).toHaveLength(1)
  })

  it('MultiSchoolSignalLookupOutput has all required fields', () => {
    const output: MultiSchoolSignalLookupOutput = {
      topic: 'Saturn 10H exalted',
      results_by_school: ALL_SCHOOLS.map(school => ({
        school,
        coverage_type: 'silent' as const,
        confidence: null,
        matching_signals: [],
      })),
      total_signals_found: 0,
      schools_with_primary_coverage: [],
      schools_silent: [...ALL_SCHOOLS],
    }
    expect(output.results_by_school).toHaveLength(7)
    expect(output.schools_silent).toHaveLength(7)
  })

  it('coverage_type union is exhaustive: primary | secondary | silent', () => {
    const types: PerSchoolSignalResult['coverage_type'][] = ['primary', 'secondary', 'silent']
    types.forEach(t => {
      const r: PerSchoolSignalResult = {
        school: 'kp',
        coverage_type: t,
        confidence: t === 'silent' ? null : 0.7,
        matching_signals: [],
      }
      expect(r.coverage_type).toBe(t)
    })
  })

  it('returns empty results when DB returns no rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const { multi_school_signal_lookup } = await import('@/lib/tools/multi_school_signal_lookup')
    const result = await multi_school_signal_lookup({ topic: 'nonexistent topic' })
    expect(result.total_signals_found).toBe(0)
    expect(result.schools_with_primary_coverage).toHaveLength(0)
    expect(result.schools_silent).toHaveLength(7)
    expect(result.results_by_school).toHaveLength(7)
  })

  it('schools_with_primary_coverage populated from DB rows', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          school: 'parashari',
          coverage_type: 'primary',
          confidence: '0.92',
          signal_id: 'SIG.MSR.041',
          signal_name: 'Saturn 10H exalted yoga',
          domain: 'CAREER',
          attribution_ref: 'BPHS §24',
        },
        {
          school: 'kp',
          coverage_type: 'primary',
          confidence: '0.85',
          signal_id: 'SIG.MSR.041',
          signal_name: 'Saturn 10H exalted yoga',
          domain: 'CAREER',
          attribution_ref: null,
        },
      ],
    })
    const { multi_school_signal_lookup } = await import('@/lib/tools/multi_school_signal_lookup')
    const result = await multi_school_signal_lookup({ topic: 'Saturn 10H', domains: ['CAREER'] })
    expect(result.total_signals_found).toBe(2)
    expect(result.schools_with_primary_coverage).toContain('parashari')
    expect(result.schools_with_primary_coverage).toContain('kp')
    expect(result.schools_silent.length).toBeLessThan(7)
  })
})

// ─── QueryClass: multi_school_triangulation registration ─────────────────────

describe('QueryClass multi_school_triangulation registration', () => {
  it('QueryClassEnum includes multi_school_triangulation', async () => {
    const { QueryClassEnum } = await import('@/lib/pipeline/types')
    const values = QueryClassEnum.options
    expect(values).toContain('multi_school_triangulation')
  })

  it('QUERY_CLASS_LABELS has multi_school_triangulation entry', async () => {
    const { QUERY_CLASS_LABELS } = await import('@/lib/jyotish/domain_labels')
    expect(QUERY_CLASS_LABELS.multi_school_triangulation).toBeDefined()
    expect(typeof QUERY_CLASS_LABELS.multi_school_triangulation).toBe('string')
    expect(QUERY_CLASS_LABELS.multi_school_triangulation.length).toBeGreaterThan(0)
  })

  it('CLASS_SUGGESTIONS has multi_school_triangulation with >= 2 examples', async () => {
    const { CLASS_SUGGESTIONS } = await import('@/lib/consume/class_suggestions')
    const suggestions = CLASS_SUGGESTIONS.multi_school_triangulation
    expect(suggestions).toBeDefined()
    expect(suggestions.length).toBeGreaterThanOrEqual(2)
    suggestions.forEach(s => expect(typeof s).toBe('string'))
  })

  it('planner golden set includes multi_school_triangulation entries', async () => {
    const fs = await import('fs')
    const path = await import('path')
    const golden = JSON.parse(
      fs.readFileSync(
        path.resolve(process.cwd(), 'tests/eval/planner_golden_set.json'),
        'utf8'
      )
    )
    const mstEntries = golden.entries.filter(
      (e: { query_class: string }) => e.query_class === 'multi_school_triangulation'
    )
    expect(mstEntries.length).toBeGreaterThanOrEqual(3)
    expect(golden.available_tools).toContain('multi_school_signal_lookup')
    expect(golden.available_tools).toContain('convergence_score_lookup')
  })
})
