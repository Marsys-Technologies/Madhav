/**
 * envelope_version_w3l1.test.ts — W3-L1 (GT-47 / W-9) envelope_version honesty contract.
 *
 * Before this fix, `buildRetrievalEnvelope` hardcoded `envelope_version: 'v1'` on EVERY
 * response regardless of the actual wire shape — a v3-format response (response_format:
 * 'v3', chart_header/epistemic/timing/coverage populated) still claimed `envelope_version:
 * 'v1'`. A caller that branched on `envelope_version` alone (rather than `response_format`)
 * was silently lied to about which shape it actually received. This suite proves the fix:
 * `envelope_version` now agrees with `response_format` on both wire paths.
 */
import { describe, it, expect } from 'vitest'
import { buildRetrievalEnvelope, type V3Envelope } from '@/lib/retrieval/envelope'

describe('W3-L1 envelope_version honesty', () => {
  it('legacy format: envelope_version is v1 (unchanged, byte-identical to pre-fix wire shape)', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content: { a: 1 } }, 'legacy')
    expect(env.envelope_version).toBe('v1')
    expect('response_format' in env).toBe(false)
  })

  it('v3 format: envelope_version now honestly reads v3 (the bug this lane fixes)', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content: { a: 1 } }, 'v3') as V3Envelope
    expect(env.envelope_version).toBe('v3')
    expect(env.response_format).toBe('v3')
  })

  it('default (no format arg) stays legacy — v3 remains strictly opt-in', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content: { a: 1 } })
    expect(env.envelope_version).toBe('v1')
  })

  it('v3 envelope never disagrees between envelope_version and response_format', () => {
    const env = buildRetrievalEnvelope(
      { tool: 'get_chart_orientation', content: {}, chart_header: null },
      'v3',
    ) as V3Envelope
    // The exact live-production defect this lane closes: envelope_version and
    // response_format must never diverge on a v3 response.
    expect(env.envelope_version).toBe(env.response_format)
  })
})
