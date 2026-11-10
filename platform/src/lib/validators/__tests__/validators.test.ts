import { describe, it, expect, vi } from 'vitest'
import { p1Validator } from '../p1_layer_separation'
import { p2Validator } from '../p2_citation'
import { p5Validator } from '../p5_signal_id_resolution'
import { runAll, summarize } from '../index'
import type { ValidationResult } from '../types'

// Mock telemetry so tests don't emit logs
vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordLatency: vi.fn(),
    recordMetric: vi.fn(),
  },
}))

// ─────────────────────────────────────────────────────────────────────────────
// P1 — Layer Separation
// ─────────────────────────────────────────────────────────────────────────────

describe('P1 — Layer Separation', () => {
  it('pass: text with no interpretive sentences', async () => {
    const text = 'Mars is in the 7th house. The native was born in 1984.'
    const result = await p1Validator.validate(text)
    expect(result.vote).toBe('pass')
    expect(result.validator_id).toBe('p1_layer_separation')
  })

  it('pass: all interpretive sentences have citations', async () => {
    const text =
      'This suggests a strong karaka placement [F.012]. It likely indicates career success [SIG.MSR.CAREER_RISE_001].'
    const result = await p1Validator.validate(text)
    expect(result.vote).toBe('pass')
  })

  it('fail: interpretive sentence without any citation', async () => {
    const text = 'This suggests a problematic placement with no citation.'
    const result = await p1Validator.validate(text)
    expect(result.vote).toBe('fail')
    expect(result.reason).toMatch(/lack citations/)
  })

  it('fail: all interpretive sentences lack citations', async () => {
    const text =
      'This indicates a strong placement. It likely shows a good period. This implies career growth.'
    const result = await p1Validator.validate(text)
    expect(result.vote).toBe('fail')
  })

  it('warn: mix — some interpretive sentences have citations, some do not (≤50% missing)', async () => {
    // 2 interpretive sentences total, 1 has citation (50% missing = borderline)
    // To ensure >50% have citations (warn zone): 3 sentences, 1 missing
    const text = [
      'This suggests a strong 10th lord placement [F.011].',
      'It likely indicates dharma activation [SIG.MSR.DHARMA_001].',
      'This implies some challenge ahead without citation.',
    ].join(' ')
    const result = await p1Validator.validate(text)
    expect(result.vote).toBe('warn')
    expect(result.reason).toMatch(/lack citations/)
  })

  it('fail: non-string input', async () => {
    const result = await p1Validator.validate(42)
    expect(result.vote).toBe('fail')
  })

  it('exposes correct metadata', () => {
    expect(p1Validator.id).toBe('p1_layer_separation')
    expect(p1Validator.applies_at).toBe('synthesis')
    expect(p1Validator.version).toBeTruthy()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// P2 — Citation Validator
// ─────────────────────────────────────────────────────────────────────────────

describe('P2 — Citation Validator', () => {
  it('pass: valid citations present', async () => {
    const text = 'The placement suggests career strength SIG.MSR.087.'
    const result = await p2Validator.validate(text)
    expect(result.vote).toBe('pass')
  })

  it('pass: no citations and no interpretive content', async () => {
    const text = 'Mars is in Aries. Saturn is in Capricorn.'
    const result = await p2Validator.validate(text)
    expect(result.vote).toBe('pass')
  })

  it('warn: no SIG.MSR.NNN citations with interpretive content', async () => {
    // Old SIG.MSR.CAREER_001 style (non-3-digit) is not matched by current regex.
    // Interpretive content + no citations → warn.
    const text = 'This suggests a strong career period without signal reference.'
    const result = await p2Validator.validate(text)
    expect(result.vote).toBe('warn')
  })

  it('fail: non-string input', async () => {
    const result = await p2Validator.validate(null)
    expect(result.vote).toBe('fail')
  })

  it('warn: interpretive content but zero citations', async () => {
    const text = 'This suggests a strong placement without any bracketed reference.'
    const result = await p2Validator.validate(text)
    expect(result.vote).toBe('warn')
    expect(result.reason).toMatch(/no citations/)
  })

  it('pass: multiple SIG.MSR.NNN citations', async () => {
    const text = 'Per SIG.MSR.001 and SIG.MSR.142, Mars indicates strength in the 10th house.'
    const result = await p2Validator.validate(text)
    expect(result.vote).toBe('pass')
  })

  it('exposes correct metadata', () => {
    expect(p2Validator.id).toBe('p2_citation')
    expect(p2Validator.applies_at).toBe('synthesis')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// P5 — Signal ID Resolution
// ─────────────────────────────────────────────────────────────────────────────

describe('P5 — Signal ID Resolution', () => {
  it('pass: valid SIG.MSR signal IDs', async () => {
    const text = 'See SIG.MSR.CAREER_RISE_001 and SIG.MSR.HEALTH_ALERT_007 for details.'
    const result = await p5Validator.validate(text)
    expect(result.vote).toBe('pass')
    expect(result.reason).toMatch(/valid format/)
  })

  it('pass: no signal IDs in text', async () => {
    const text = 'Mars is in the 7th house. Saturn aspects the 10th lord.'
    const result = await p5Validator.validate(text)
    expect(result.vote).toBe('pass')
    expect(result.reason).toMatch(/No SIG\.MSR/)
  })

  it('fail: malformed signal ID — too long', async () => {
    const longComponent = 'A'.repeat(80)   // SIG.MSR. + 80 = 88 chars > 80
    const text = `See SIG.MSR.${longComponent} for details.`
    const result = await p5Validator.validate(text)
    expect(result.vote).toBe('fail')
    expect(result.reason).toMatch(/malformed/)
  })

  it('fail: non-string input', async () => {
    const result = await p5Validator.validate({ foo: 'bar' })
    expect(result.vote).toBe('fail')
  })

  it('pass: multiple valid signal IDs', async () => {
    const text = 'SIG.MSR.DHARMA_001 and SIG.MSR.KARMA_002 both apply here.'
    const result = await p5Validator.validate(text)
    expect(result.vote).toBe('pass')
  })

  it('exposes correct metadata', () => {
    expect(p5Validator.id).toBe('p5_signal_id_resolution')
    expect(p5Validator.applies_at).toBe('synthesis')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// runAll
// ─────────────────────────────────────────────────────────────────────────────

describe('runAll', () => {
  it('runs all three validators for applies_at=synthesis', async () => {
    const text = 'Mars is in the 7th house.'
    const results = await runAll(text, 'synthesis')
    expect(results).toHaveLength(3)
    const ids = results.map((r) => r.validator_id)
    expect(ids).toContain('p1_layer_separation')
    expect(ids).toContain('p2_citation')
    expect(ids).toContain('p5_signal_id_resolution')
  })

  it('returns empty array for applies_at=bundle', async () => {
    const results = await runAll('any input', 'bundle')
    expect(results).toEqual([])
  })

  it('passes context through to validators without error', async () => {
    const text = 'The placement suggests strength [F.001].'
    const context = { manifest_fingerprint: 'abc123' }
    const results = await runAll(text, 'synthesis', context)
    expect(results).toHaveLength(3)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// summarize
// ─────────────────────────────────────────────────────────────────────────────

describe('summarize', () => {
  const makeResult = (id: string, vote: 'pass' | 'warn' | 'fail'): ValidationResult => ({
    validator_id: id,
    validator_version: '1.0.0',
    vote,
  })

  it('all pass → overall pass', () => {
    const results = [
      makeResult('p1', 'pass'),
      makeResult('p2', 'pass'),
      makeResult('p5', 'pass'),
    ]
    const { overall, failures } = summarize(results)
    expect(overall).toBe('pass')
    expect(failures).toHaveLength(0)
  })

  it('any fail → overall fail', () => {
    const results = [
      makeResult('p1', 'pass'),
      makeResult('p2', 'fail'),
      makeResult('p5', 'warn'),
    ]
    const { overall, failures } = summarize(results)
    expect(overall).toBe('fail')
    expect(failures).toHaveLength(1)
    expect(failures[0].validator_id).toBe('p2')
  })

  it('fail beats warn — multiple fails', () => {
    const results = [
      makeResult('p1', 'fail'),
      makeResult('p2', 'warn'),
      makeResult('p5', 'fail'),
    ]
    const { overall, failures } = summarize(results)
    expect(overall).toBe('fail')
    expect(failures).toHaveLength(2)
  })

  it('warn (no fails) → overall warn', () => {
    const results = [
      makeResult('p1', 'pass'),
      makeResult('p2', 'warn'),
      makeResult('p5', 'pass'),
    ]
    const { overall } = summarize(results)
    expect(overall).toBe('warn')
  })

  it('by_validator maps each validator to its vote', () => {
    const results = [
      makeResult('p1', 'pass'),
      makeResult('p2', 'fail'),
      makeResult('p5', 'warn'),
    ]
    const { by_validator } = summarize(results)
    expect(by_validator['p1']).toBe('pass')
    expect(by_validator['p2']).toBe('fail')
    expect(by_validator['p5']).toBe('warn')
  })

  it('empty results → overall pass', () => {
    const { overall, failures } = summarize([])
    expect(overall).toBe('pass')
    expect(failures).toHaveLength(0)
  })
})
