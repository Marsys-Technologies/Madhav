import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/tools/convergence_score_lookup', () => ({
  convergence_score_lookup: vi.fn(),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))
vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))
vi.mock('@/lib/schemas', () => ({
  validate: vi.fn().mockReturnValue({ valid: true, errors: [] }),
}))

import { convergence_score_lookup } from '@/lib/tools/convergence_score_lookup'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool } from '../convergence_score_lookup_tool'
import type { QueryPlan } from '../types'

const mockFn = vi.mocked(convergence_score_lookup)

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000030',
  query_text: 'inter-school convergence all domains',
  query_class: 'multi_school_triangulation',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['convergence_score_lookup'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

function makeScore(domain: string, level: 'HIGH' | 'MEDIUM' | 'LOW') {
  return {
    domain,
    schools_agreeing: level === 'HIGH' ? 6 : level === 'MEDIUM' ? 4 : 2,
    schools_total: 7,
    convergence_level: level,
    mean_domain_score: level === 'HIGH' ? 0.8 : level === 'MEDIUM' ? 0.5 : 0.2,
    std_domain_score: 0.1,
    direction: 'positive' as const,
    per_school_scores: { parashari: 0.8, jaimini: 0.7 },
    convergence_narrative: `${domain} convergence ${level}`,
    computed_at: '2026-05-14T00:00:00.000Z',
  }
}

function makeOutput(domains: string[], level: 'HIGH' | 'MEDIUM' | 'LOW' = 'HIGH') {
  const scores = domains.map(d => makeScore(d, level))
  return {
    domains_requested: domains,
    convergence_scores: scores,
    summary: {
      high_convergence_domains: level === 'HIGH' ? domains : [],
      medium_convergence_domains: level === 'MEDIUM' ? domains : [],
      low_convergence_domains: level === 'LOW' ? domains : [],
      overall_agreement_signal: 'test signal',
    },
  }
}

const ALL_FIVE = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']

beforeEach(() => {
  vi.clearAllMocks()
})

describe('convergence_score_lookup_tool', () => {
  it('returns ToolBundle with one result per domain when no params supplied (happy path)', async () => {
    mockFn.mockResolvedValue(makeOutput(ALL_FIVE))

    const bundle = await tool.retrieve(basePlan, {})

    expect(bundle.results).toHaveLength(5)
    expect(bundle.tool_name).toBe('convergence_score_lookup')
    expect(mockFn).toHaveBeenCalledWith(
      expect.objectContaining({ domains: ALL_FIVE })
    )
  })

  it('passes singular domain param through and filters to that domain', async () => {
    mockFn.mockResolvedValue(makeOutput(['RELATIONSHIP']))

    const bundle = await tool.retrieve(basePlan, { domain: 'RELATIONSHIP' })

    expect(mockFn).toHaveBeenCalledWith(
      expect.objectContaining({ domains: ['RELATIONSHIP'] })
    )
    expect(bundle.results).toHaveLength(1)
    const parsed = JSON.parse(bundle.results[0].content)
    expect(parsed.domain).toBe('RELATIONSHIP')
  })

  it('applies min_level post-filter and returns empty results without error', async () => {
    // LOW scores should be filtered out when min_level: 'HIGH'
    mockFn.mockResolvedValue(makeOutput(ALL_FIVE, 'LOW'))

    const bundle = await tool.retrieve(basePlan, { min_level: 'HIGH' })

    expect(bundle.results).toHaveLength(0)
    expect(bundle.tool_name).toBe('convergence_score_lookup')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('propagates bare function error and logs to writeToolExecutionLog', async () => {
    mockFn.mockRejectedValue(new Error('convergence table missing'))

    await expect(tool.retrieve(basePlan)).rejects.toThrow('convergence table missing')

    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 'error',
        tool_name: 'convergence_score_lookup',
        error_code: 'convergence table missing',
      })
    )
  })

  it('returns valid ToolBundle shape with correct confidence mapping for HIGH level', async () => {
    mockFn.mockResolvedValue(makeOutput(['CAREER'], 'HIGH'))

    const bundle = await tool.retrieve(basePlan, { domain: 'CAREER' })

    expect(bundle.tool_name).toBe('convergence_score_lookup')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('convergence_scores')
    expect(bundle.results[0].confidence).toBe(0.95)   // HIGH
    expect(bundle.results[0].significance).toBe(0.9)
  })
})
