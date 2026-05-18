import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/tools/multi_school_signal_lookup', () => ({
  multi_school_signal_lookup: vi.fn(),
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

import { multi_school_signal_lookup } from '@/lib/tools/multi_school_signal_lookup'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool } from '../multi_school_signal_lookup_tool'
import type { QueryPlan } from '../types'

const mockFn = vi.mocked(multi_school_signal_lookup)

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000020',
  query_text: 'career signals multi-school',
  query_class: 'multi_school_triangulation',
  domains: ['CAREER'],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['multi_school_signal_lookup'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

type School = 'parashari' | 'jaimini' | 'tajika' | 'kp' | 'nadi' | 'bnn' | 'yogini'

function makeSchoolResult(school: School, coverage_type: 'primary' | 'secondary' | 'silent') {
  return {
    school,
    coverage_type,
    confidence: coverage_type === 'primary' ? 0.9 : coverage_type === 'secondary' ? 0.6 : null,
    matching_signals:
      coverage_type === 'silent'
        ? []
        : [{ signal_id: 'SIG.MSR.001', signal_name: 'Saturn in 10H', domain: 'CAREER' }],
  }
}

function makeOutput(schools: School[], coverage_type: 'primary' | 'secondary' | 'silent' = 'primary') {
  const results_by_school = schools.map(s => makeSchoolResult(s, coverage_type))
  return {
    topic: 'career',
    results_by_school,
    total_signals_found: schools.filter(s => coverage_type !== 'silent').length,
    schools_with_primary_coverage: coverage_type === 'primary' ? schools : [],
    schools_silent: coverage_type === 'silent' ? schools : [],
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('multi_school_signal_lookup_tool', () => {
  it('returns ToolBundle with one result per school (happy path)', async () => {
    mockFn.mockResolvedValue(makeOutput(['parashari', 'jaimini', 'kp']))

    const bundle = await tool.retrieve(basePlan, { topic: 'career', domains: ['CAREER'] })

    expect(bundle.results).toHaveLength(3)
    expect(bundle.tool_name).toBe('multi_school_signal_lookup')
    expect(bundle.tool_version).toBe('1.0.0')
  })

  it('passes topic, school, and domain filter params through to bare function', async () => {
    mockFn.mockResolvedValue(makeOutput(['parashari']))

    await tool.retrieve(basePlan, {
      topic: 'health',
      school: 'parashari',
      domain: 'HEALTH',
    })

    expect(mockFn).toHaveBeenCalledWith(
      expect.objectContaining({
        topic: 'health',
        domains: ['HEALTH'],
        schools: ['parashari'],
      })
    )
  })

  it('returns empty matching_signals for silent schools without throwing', async () => {
    mockFn.mockResolvedValue({
      topic: 'unknown',
      results_by_school: [makeSchoolResult('bnn', 'silent')],
      total_signals_found: 0,
      schools_with_primary_coverage: [],
      schools_silent: ['bnn'],
    })

    const bundle = await tool.retrieve(basePlan, { topic: 'unknown' })

    expect(bundle.results).toHaveLength(1)
    const parsed = JSON.parse(bundle.results[0].content)
    expect(parsed.coverage_type).toBe('silent')
    expect(parsed.matching_signals).toHaveLength(0)
    expect(bundle.results[0].confidence).toBe(0.50)
  })

  it('propagates bare function error and logs to writeToolExecutionLog', async () => {
    mockFn.mockRejectedValue(new Error('DB down'))

    await expect(tool.retrieve(basePlan)).rejects.toThrow('DB down')

    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({
        status: 'error',
        tool_name: 'multi_school_signal_lookup',
        error_code: 'DB down',
      })
    )
  })

  it('returns valid ToolBundle shape with correct confidence mapping', async () => {
    mockFn.mockResolvedValue(makeOutput(['parashari'], 'primary'))

    const bundle = await tool.retrieve(basePlan, { topic: 'career' })

    expect(bundle.tool_name).toBe('multi_school_signal_lookup')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('school_signal_coverage')
    expect(bundle.results[0].confidence).toBe(0.95)   // primary
    expect(bundle.results[0].significance).toBe(0.8)
  })
})
