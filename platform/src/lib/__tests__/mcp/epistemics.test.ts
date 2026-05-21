/**
 * epistemics.test.ts — Unit tests for MCP envelope builders.
 *
 * Tests: buildEnvelope(), buildErrorEnvelope(), buildEpistemicsBlock(),
 *        buildSynthesisAudit().
 */

import { describe, it, expect } from 'vitest'
import {
  buildEnvelope,
  buildErrorEnvelope,
  buildEpistemicsBlock,
  buildSynthesisAudit,
} from '@/lib/mcp/epistemics'

// ── buildEpistemicsBlock ───────────────────────────────────────────────────────

describe('buildEpistemicsBlock', () => {
  it('returns required fields with defaults', () => {
    const block = buildEpistemicsBlock({ surgical: false })
    expect(block.surgical).toBe(false)
    expect(block.confidence_band).toBe('medium')
    expect(block.horizon_days).toBeNull()
    expect(block.falsifier).toBeNull()
  })

  it('preserves explicit surgical=true', () => {
    const block = buildEpistemicsBlock({ surgical: true, confidence_band: 'high' })
    expect(block.surgical).toBe(true)
    expect(block.confidence_band).toBe('high')
  })

  it('accepts horizon_days and falsifier for predictive', () => {
    const block = buildEpistemicsBlock({
      surgical: false,
      confidence_band: 'medium',
      horizon_days: 90,
      falsifier: 'Native relocates before 2027',
    })
    expect(block.horizon_days).toBe(90)
    expect(block.falsifier).toBe('Native relocates before 2027')
  })
})

// ── buildSynthesisAudit ───────────────────────────────────────────────────────

describe('buildSynthesisAudit', () => {
  it('holistic_read_passed=true when L2.5 tool fires', () => {
    const audit = buildSynthesisAudit({
      tools_fired: ['msr_sql', 'chart_facts_query'],
    })
    expect(audit.holistic_read_passed).toBe(true)
    expect(audit.l25_tools_fired).toContain('msr_sql')
    expect(audit.l25_tools_fired).not.toContain('chart_facts_query')
  })

  it('holistic_read_passed=false when no L2.5 tool fires', () => {
    const audit = buildSynthesisAudit({
      tools_fired: ['chart_facts_query', 'lel_query'],
    })
    expect(audit.holistic_read_passed).toBe(false)
    expect(audit.l25_tools_fired).toHaveLength(0)
  })

  it('includes provided dominant_signals and domains_touched', () => {
    const audit = buildSynthesisAudit({
      tools_fired: ['cgm_graph_walk'],
      dominant_signals: ['SIG.MSR.001', 'SIG.MSR.002'],
      domains_touched: ['career', 'finance'],
    })
    expect(audit.dominant_signals).toEqual(['SIG.MSR.001', 'SIG.MSR.002'])
    expect(audit.domains_touched).toEqual(['career', 'finance'])
  })

  it('generates a default l25_contribution_summary', () => {
    const audit = buildSynthesisAudit({
      tools_fired: ['msr_sql', 'cgm_graph_walk'],
    })
    expect(audit.l25_contribution_summary).toContain('L2.5')
  })

  it('shows bypass message when no L2.5 tools', () => {
    const audit = buildSynthesisAudit({ tools_fired: [] })
    expect(audit.l25_contribution_summary).toContain('bypassed')
  })
})

// ── buildEnvelope ─────────────────────────────────────────────────────────────

describe('buildEnvelope', () => {
  const baseEpistemics = buildEpistemicsBlock({ surgical: false })

  it('returns ok=true with required fields', () => {
    const env = buildEnvelope({
      trace_id: 'qry-001',
      audience_tier: 'super_admin',
      epistemics: baseEpistemics,
      result: { answer_markdown: 'Test answer' },
    })
    expect(env.ok).toBe(true)
    expect(env.trace_id).toBe('qry-001')
    expect(env.audience_tier).toBe('super_admin')
    expect(env.epistemics).toBe(baseEpistemics)
  })

  it('defaults empty arrays for optional fields', () => {
    const env = buildEnvelope({
      trace_id: 'x',
      audience_tier: 'client',
      epistemics: baseEpistemics,
      result: {},
    })
    expect(env.citations).toEqual([])
    expect(env.predictions_logged).toEqual([])
    expect(env.suggested_followups).toEqual([])
    expect(env.warnings).toEqual([])
    expect(env.plan).toBeNull()
    expect(env.synthesis_audit).toBeNull()
  })

  it('preserves provided warnings array', () => {
    const env = buildEnvelope({
      trace_id: 'x',
      audience_tier: 'client',
      epistemics: baseEpistemics,
      result: {},
      warnings: ['B.11 floor enforced'],
    })
    expect(env.warnings).toContain('B.11 floor enforced')
  })
})

// ── buildErrorEnvelope ────────────────────────────────────────────────────────

describe('buildErrorEnvelope', () => {
  it('returns ok=false with error fields', () => {
    const env = buildErrorEnvelope({
      error_class: 'auth',
      message: 'Invalid API key',
    })
    expect(env.ok).toBe(false)
    expect(env.error.class).toBe('auth')
    expect(env.error.message).toBe('Invalid API key')
    expect(env.trace_id).toBe('')
  })

  it('includes remediation when provided', () => {
    const env = buildErrorEnvelope({
      trace_id: 'qry-err',
      error_class: 'rate_limit',
      message: 'Too many requests',
      remediation: 'Wait 60 seconds and retry',
    })
    expect(env.trace_id).toBe('qry-err')
    expect(env.error.remediation).toBe('Wait 60 seconds and retry')
  })

  it('covers all error classes', () => {
    const classes = ['auth', 'validation', 'planner_error', 'orchestrator_error', 'rate_limit', 'internal'] as const
    for (const cls of classes) {
      const env = buildErrorEnvelope({ error_class: cls, message: 'test' })
      expect(env.error.class).toBe(cls)
    }
  })
})
