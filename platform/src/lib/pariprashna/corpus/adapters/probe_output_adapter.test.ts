import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { describe, expect, it } from 'vitest'

import { turnObservationFromProbeOutput } from './probe_output_adapter'
import { baseFixture } from '../__tests__/test_helpers'

// Real probe/ask.ts output captured live this session (2026-08-28) against
// the deployed web door for the synthetic test chart 1c826d5a — see EDIR
// V3-E-016 for the full context of what this specific turn revealed.
const LIVE_PROBE_RECORD_PATH = join(
  __dirname,
  '../../../../../scripts/probe/out/8b9486f2-dabc-469e-873b-b27afc49cbb5.json',
)

describe('turnObservationFromProbeOutput', () => {
  it('extracts a real, schema-valid receipt from a live probe record’s receipt.define event', () => {
    const record = JSON.parse(readFileSync(LIVE_PROBE_RECORD_PATH, 'utf8'))
    const fixture = baseFixture()
    const obs = turnObservationFromProbeOutput(record, fixture)

    expect(obs.fixture).toBe(fixture)
    expect(obs.proseText).toBe(record.prose)
    expect(obs.receipt).not.toBeNull()
    expect(obs.receipt?.chart_id).toBe('1c826d5a-41cb-4450-b4dc-59d440e5f75a')
    expect(obs.receipt?.evidence_grades.status).toBe('measured')
    // turnMetrics has no equivalent SSE event in probe/ask.ts's current capture —
    // honestly null, never fabricated.
    expect(obs.turnMetrics).toBeNull()
  })

  it('returns receipt: null (never throws, never fabricates) when no receipt.define event is present', () => {
    const record = { prose: 'some prose', events: [{ type: 'turn.open', raw: {} }] }
    const fixture = baseFixture()
    const obs = turnObservationFromProbeOutput(record, fixture)
    expect(obs.receipt).toBeNull()
    expect(obs.proseText).toBe('some prose')
  })

  it('returns receipt: null when a receipt.define event exists but fails schema validation', () => {
    const record = {
      prose: 'some prose',
      events: [{ type: 'receipt.define', raw: { receipt: { not: 'a valid receipt shape' } } }],
    }
    const fixture = baseFixture()
    const obs = turnObservationFromProbeOutput(record, fixture)
    expect(obs.receipt).toBeNull()
  })

  it('honestly reports proseText: null when the probe record has no prose field', () => {
    const record = { events: [] }
    const fixture = baseFixture()
    const obs = turnObservationFromProbeOutput(record, fixture)
    expect(obs.proseText).toBeNull()
  })
})
