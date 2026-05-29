import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { parseMsrSignals } from '../msr_parser'

const content = readFileSync(resolve(__dirname, '../../../../../025_HOLISTIC_SYNTHESIS/MSR_v5_0.md'), 'utf-8')

describe('parseMsrSignals', () => {
  const signals = parseMsrSignals(content)

  it('parses 573 signals', () => {
    expect(signals).toHaveLength(573)
  })

  it('first signal has correct signal_id', () => {
    expect(signals[0].signal_id).toBe('SIG.MSR.001')
  })

  it('first signal has claim_text', () => {
    expect(signals[0].claim_text).toBeTruthy()
    expect(signals[0].claim_text.length).toBeGreaterThan(5)
  })

  it('all signals have valid confidence (0-1)', () => {
    for (const s of signals) {
      expect(s.confidence).toBeGreaterThanOrEqual(0)
      expect(s.confidence).toBeLessThanOrEqual(1)
    }
  })

  it('all signals have valid significance (0-1)', () => {
    for (const s of signals) {
      expect(s.significance).toBeGreaterThanOrEqual(0)
      expect(s.significance).toBeLessThanOrEqual(1)
    }
  })

  it('all signals have native_id abhisek_mohanty', () => {
    for (const s of signals) {
      expect(s.native_id).toBe('abhisek_mohanty')
    }
  })

  it('all signals have source_file', () => {
    for (const s of signals) {
      expect(s.source_file).toBe('MSR_v5_0.md')
    }
  })

  it('sample signal has is_forward_looking=false for natal-permanent', () => {
    // SIG.MSR.001 is natal-permanent
    expect(signals[0].is_forward_looking).toBe(false)
  })
})
