/**
 * Lane G1-G · PPR-13 item 3 — THE TOOL-SEQUENCE ANOMALY TRACE.
 *
 * TA §14A.1 rules this control is "a trace flag, NOT a block". The first
 * describe below is that ruling written as a test, so a future edit that turns
 * the monitor into a gate fails here rather than in production.
 */
import { describe, it, expect } from 'vitest'

import { ToolSequenceMonitor, DEFAULT_MAX_CALLS_PER_TOOL, MIN_TOTAL_CALL_CEILING } from '../tool_sequence'

const AUTHORIZED = ['ganita_dashas_get', 'ganita_positions_get', 'bodha_signals_get']

describe('the ruling: flag, never block', () => {
  it('record() returns nothing and cannot refuse a call', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    expect(m.record('exfiltrate_all_charts')).toBeUndefined()
    expect(m.anomalous).toBe(true)
  })

  it('never throws, whatever it is handed', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    expect(() => m.record(undefined as unknown as string)).not.toThrow()
    expect(() => m.record('')).not.toThrow()
  })
})

describe('unplanned_tool — the agentic loop diverging from the authorized plan', () => {
  it('is silent while every call is in-plan', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    for (const t of AUTHORIZED) m.record(t)
    expect(m.anomalous).toBe(false)
    expect(m.traceFlag()).toMatchObject({ anomalous: false, anomaly_count: 0, total_calls: 3 })
  })

  it('fires on a tool the plan never authorized', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    m.record('ganita_dashas_get')
    m.record('ganita_medical_get')
    expect(m.anomalies).toEqual([
      { code: 'unplanned_tool', tool_name: 'ganita_medical_get', at_call_index: 2 },
    ])
    expect(m.severity()).toBe('warn')
  })

  it('reports the same unplanned tool ONCE, but a second unplanned tool separately', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    m.record('rogue_a')
    m.record('rogue_a')
    m.record('rogue_a')
    m.record('rogue_b')
    expect(m.anomalies.filter((a) => a.code === 'unplanned_tool')).toHaveLength(2)
  })
})

describe('excluded_capability_attempted — the highest-signal detector', () => {
  it('fires, and escalates the severity, when a deliberately-removed capability is called', () => {
    // The capability was in the registry, was considered, and was taken away by
    // HS-1/HS-4 or NO-LEAKAGE. There is no benign story for asking again.
    const m = new ToolSequenceMonitor({
      authorized: AUTHORIZED,
      forbidden: ['ganita_ayurdaya_get'],
    })
    m.record('ganita_dashas_get')
    m.record('ganita_ayurdaya_get')
    expect(m.anomalies).toEqual([
      { code: 'excluded_capability_attempted', tool_name: 'ganita_ayurdaya_get', at_call_index: 2 },
    ])
    expect(m.severity()).toBe('error')
  })

  it('reports a forbidden call ONCE, not also as unplanned', () => {
    const m = new ToolSequenceMonitor({ authorized: [], forbidden: ['x'] })
    m.record('x')
    expect(m.anomalies).toHaveLength(1)
    expect(m.anomalies[0].code).toBe('excluded_capability_attempted')
  })
})

describe('volume detectors', () => {
  it('repeat_call_excess fires once, on the call that crosses the per-tool cap', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    for (let i = 0; i < DEFAULT_MAX_CALLS_PER_TOOL + 3; i++) m.record('ganita_dashas_get')
    const repeats = m.anomalies.filter((a) => a.code === 'repeat_call_excess')
    expect(repeats).toHaveLength(1)
    expect(repeats[0].at_call_index).toBe(DEFAULT_MAX_CALLS_PER_TOOL + 1)
  })

  it('does not fire at exactly the cap', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED })
    for (let i = 0; i < DEFAULT_MAX_CALLS_PER_TOOL; i++) m.record('ganita_dashas_get')
    expect(m.anomalies.filter((a) => a.code === 'repeat_call_excess')).toHaveLength(0)
  })

  it('sequence_length_excess uses max(floor, authorized × 3)', () => {
    // A one-tool plan still gets the floor, so adaptive re-entry is not
    // penalised for a narrow plan.
    const m = new ToolSequenceMonitor({ authorized: ['a'], maxCallsPerTool: 10_000 })
    for (let i = 0; i < MIN_TOTAL_CALL_CEILING; i++) m.record('a')
    expect(m.anomalies.filter((a) => a.code === 'sequence_length_excess')).toHaveLength(0)
    m.record('a')
    expect(m.anomalies.filter((a) => a.code === 'sequence_length_excess')).toHaveLength(1)
  })
})

describe('the trace flag is wire-safe (gate 11 [integrity])', () => {
  it('carries codes and counts only — never a raw capability name', () => {
    const m = new ToolSequenceMonitor({ authorized: AUTHORIZED, forbidden: ['ganita_ayurdaya_get'] })
    m.record('ganita_ayurdaya_get')
    m.record('some_rogue_tool')

    const trace = m.traceFlag()
    const serialized = JSON.stringify(trace)
    expect(serialized).not.toContain('ganita_ayurdaya_get')
    expect(serialized).not.toContain('some_rogue_tool')
    expect(trace.codes.sort()).toEqual(['excluded_capability_attempted', 'unplanned_tool'])
    expect(trace.anomaly_count).toBe(2)
    expect(trace.total_calls).toBe(2)
  })

  it('the raw names ARE available on `.anomalies` for the server log', () => {
    const m = new ToolSequenceMonitor({ authorized: [] })
    m.record('rogue')
    expect(m.anomalies[0].tool_name).toBe('rogue')
  })
})
