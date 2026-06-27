/**
 * Chart-Agnostic Gate — Unit Tests
 * ==================================
 * Proves the gate catches each forbidden pattern.
 * Per the D1 brief §2: unit tests proving the gate catches each forbidden pattern.
 *
 * Test matrix:
 *   T1 — per_chart capability missing chart_id in required_inputs → FAIL
 *   T2 — literal native chart_id in description → FAIL
 *   T3 — literal phantom chart_id in description → FAIL
 *   T4 — native name 'Abhisek Mohanty' in description → FAIL
 *   T5 — native birthdate '1984-02-05' in description → FAIL
 *   T6 — 'Bhubaneswar' in description → FAIL
 *   T7 — per_chart chart_id field has a default value → FAIL
 *   T8 — literal native chart_id in chart_id field description → FAIL
 *   T9 — global scope with chart_id in required_inputs → FAIL
 *   T10 — missing D1 contract fields (archetype, traversal_level, etc.) → FAIL
 *   T11 — clean per_chart capability → PASS
 *   T12 — clean global capability → PASS
 *   T13 — multiple violations on one capability → all reported
 *   T14 — ephemeris_cache_native_lifetime exemption (native description allowed) → PASS
 */

import { describe, it, expect } from 'vitest'
import {
  checkCapability,
  checkAllCapabilities,
  runChartAgnosticGate,
  NATIVE_CHART_ID,
  PHANTOM_CHART_ID,
} from './chart_agnostic_gate'
import type { CapabilityDescriptor } from './types'

// ── Helper: build a minimal valid per_chart capability ────────────────────────

function makePerChart(overrides: Partial<CapabilityDescriptor> = {}): CapabilityDescriptor {
  return {
    uri: 'marsys://tool/L1/test_tool',
    type: 'tool',
    layer: 'L1',
    name: 'test_tool',
    description: 'Retrieves data for a given chart UUID.',
    input_schema: {
      chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>)', required: true },
    },
    required_inputs: ['chart_id'],
    scope: 'per_chart',
    archetype: 'flat_fact',
    traversal_level: 'L-SIGNAL',
    tool_role: 'leaf',
    emits_references: true,
    lel_capable: false,
    llm_hints: { agentic: { cost_class: 'cheap' } },
    async handler() { return { content: {}, is_error: false } },
    ...overrides,
  } as CapabilityDescriptor
}

// ── Helper: build a minimal valid global capability ───────────────────────────

function makeGlobal(overrides: Partial<CapabilityDescriptor> = {}): CapabilityDescriptor {
  return {
    uri: 'marsys://tool/L0/test_global',
    type: 'tool',
    layer: 'L0',
    name: 'test_global',
    description: 'Queries the yoga catalog. No chart required.',
    input_schema: {
      yoga_name: { type: 'string', description: 'Partial match on yoga name.' },
    },
    required_inputs: [],
    scope: 'global',
    archetype: 'flat_fact',
    traversal_level: 'L-OVERVIEW',
    tool_role: 'leaf',
    emits_references: false,
    lel_capable: false,
    llm_hints: { agentic: { cost_class: 'cheap' } },
    async handler() { return { content: {}, is_error: false } },
    ...overrides,
  } as CapabilityDescriptor
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('chart_agnostic_gate', () => {

  // T1 — per_chart missing chart_id in required_inputs
  it('T1: FAILS when per_chart capability omits chart_id from required_inputs', () => {
    const cap = makePerChart({ required_inputs: ['ayanamsha_id'] })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-1-PER_CHART_MISSING_CHART_ID')).toBe(true)
  })

  it('T1b: FAILS when per_chart capability has empty required_inputs', () => {
    const cap = makePerChart({ required_inputs: [] })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-1-PER_CHART_MISSING_CHART_ID')).toBe(true)
  })

  // T2 — literal native chart_id in description
  it('T2: FAILS when native chart_id appears in description', () => {
    const cap = makePerChart({
      description: `Retrieve data for chart ${NATIVE_CHART_ID}.`,
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-2-NATIVE_ID_IN_DESCRIPTION')).toBe(true)
  })

  // T3 — literal phantom chart_id in description
  it('T3: FAILS when phantom chart_id appears in description', () => {
    const cap = makePerChart({
      description: `Retrieves chart data (legacy id: ${PHANTOM_CHART_ID}-0000-0000-0000-000000000000).`,
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-2-PHANTOM_ID_IN_DESCRIPTION')).toBe(true)
  })

  // T4 — native name in description
  it('T4: FAILS when "Abhisek Mohanty" appears in description', () => {
    const cap = makePerChart({
      description: 'Returns dasha periods for Abhisek Mohanty.',
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION')).toBe(true)
  })

  // T5 — native birthdate in description
  it('T5: FAILS when "1984-02-05" (native birthdate) appears in description', () => {
    const cap = makePerChart({
      description: 'Date range defaults to 1984-02-05 through present.',
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION')).toBe(true)
  })

  // T6 — 'Bhubaneswar' in description
  it('T6: FAILS when "Bhubaneswar" (native birthplace) appears in description', () => {
    const cap = makePerChart({
      description: 'Ephemeris data for Bhubaneswar coordinates.',
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION')).toBe(true)
  })

  // T7 — per_chart chart_id field has a default value
  it('T7: FAILS when per_chart chart_id input_schema has a default value', () => {
    const cap = makePerChart({
      input_schema: {
        chart_id: {
          type: 'string',
          description: 'Chart UUID',
          required: true,
          default: NATIVE_CHART_ID,
        },
      },
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-4-CHART_ID_HAS_DEFAULT')).toBe(true)
  })

  it('T7b: FAILS when per_chart chart_id input_schema has any default (even non-uuid)', () => {
    const cap = makePerChart({
      input_schema: {
        chart_id: {
          type: 'string',
          description: 'Chart UUID',
          required: true,
          default: 'some-default',
        },
      },
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-4-CHART_ID_HAS_DEFAULT')).toBe(true)
  })

  // T8 — native chart_id in chart_id field description
  it('T8: FAILS when chart_id input_schema description contains the native uuid', () => {
    const cap = makePerChart({
      input_schema: {
        chart_id: {
          type: 'string',
          description: `UUID of the chart (canonical native: ${NATIVE_CHART_ID})`,
          required: true,
        },
      },
    })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-5-NATIVE_ID_IN_CHART_ID_FIELD_DESCRIPTION')).toBe(true)
  })

  // T9 — global scope with chart_id in required_inputs
  it('T9: FAILS when global scope capability lists chart_id in required_inputs', () => {
    const cap = makeGlobal({ required_inputs: ['chart_id', 'yoga_name'] })
    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-6-GLOBAL_SCOPE_HAS_CHART_ID_REQUIRED')).toBe(true)
  })

  // T10 — missing D1 contract fields
  it('T10: FAILS when D1 contract fields are missing', () => {
    const cap = {
      uri: 'marsys://tool/L1/old_tool',
      type: 'tool' as const,
      layer: 'L1' as const,
      name: 'old_tool',
      description: 'An old capability without D1 fields.',
      required_inputs: ['chart_id'],
      scope: 'per_chart' as const,
      // Missing: archetype, traversal_level, tool_role, emits_references, lel_capable
      async handler() { return { content: {}, is_error: false } },
    } as unknown as CapabilityDescriptor

    const violations = checkCapability(cap)
    expect(violations.some(v => v.rule === 'RULE-7-MISSING_D1_CONTRACT_FIELDS')).toBe(true)
    // Should list the missing fields
    const d1Violation = violations.find(v => v.rule === 'RULE-7-MISSING_D1_CONTRACT_FIELDS')
    expect(d1Violation?.detail).toContain('archetype')
    expect(d1Violation?.detail).toContain('traversal_level')
    expect(d1Violation?.detail).toContain('tool_role')
    expect(d1Violation?.detail).toContain('emits_references')
    expect(d1Violation?.detail).toContain('lel_capable')
  })

  // T11 — clean per_chart capability → PASS
  it('T11: PASSES a clean per_chart capability', () => {
    const cap = makePerChart()
    const violations = checkCapability(cap)
    expect(violations).toHaveLength(0)
  })

  // T12 — clean global capability → PASS
  it('T12: PASSES a clean global capability', () => {
    const cap = makeGlobal()
    const violations = checkCapability(cap)
    expect(violations).toHaveLength(0)
  })

  // T13 — multiple violations on one capability → all reported
  it('T13: Reports all violations when multiple rules fail on one capability', () => {
    const cap = makePerChart({
      required_inputs: [],                               // T1: missing chart_id
      description: `Returns data for ${NATIVE_CHART_ID} (Abhisek Mohanty).`, // T2 + T4
    })
    const violations = checkCapability(cap)
    // Should catch RULE-1, RULE-2, RULE-3 at minimum
    expect(violations.length).toBeGreaterThanOrEqual(3)
    const rules = violations.map(v => v.rule)
    expect(rules).toContain('RULE-1-PER_CHART_MISSING_CHART_ID')
    expect(rules).toContain('RULE-2-NATIVE_ID_IN_DESCRIPTION')
    expect(rules).toContain('RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION')
  })

  // T14 — ephemeris_cache_native_lifetime exemption
  it('T14: ephemeris_cache_native_lifetime is exempt from native-identifier description check', () => {
    const cap: CapabilityDescriptor = {
      uri: 'marsys://resource/ephemeris-cache/native-lifetime',
      type: 'resource' as const,
      layer: 'L0' as const,
      name: 'ephemeris_cache_native_lifetime',
      description: 'Ephemeris for Abhisek Mohanty lifetime (1984-2070). Born 1984-02-05 Bhubaneswar.',
      scope: 'global' as const,
      archetype: 'orientation_digest' as const,
      traversal_level: 'L-OVERVIEW' as const,
      tool_role: 'umbrella' as const,
      emits_references: false,
      lel_capable: false,
      async handler() { return { content: {}, is_error: false } },
    }
    const violations = checkCapability(cap)
    // RULE-3 should NOT fire for this URI
    expect(violations.some(v => v.rule === 'RULE-3-NATIVE_IDENTIFIER_IN_DESCRIPTION')).toBe(false)
  })

  // ── checkAllCapabilities tests ────────────────────────────────────────────────

  it('checkAllCapabilities: returns empty array for all-clean registry', () => {
    const caps: CapabilityDescriptor[] = [makePerChart(), makeGlobal()]
    const violations = checkAllCapabilities(caps)
    expect(violations).toHaveLength(0)
  })

  it('checkAllCapabilities: collects violations across multiple capabilities', () => {
    const bad1 = makePerChart({ required_inputs: [] })
    const bad2 = makeGlobal({ description: 'Returns Abhisek Mohanty chart data.' })
    const violations = checkAllCapabilities([bad1, bad2])
    expect(violations.length).toBeGreaterThanOrEqual(2)
  })

  // ── runChartAgnosticGate tests ────────────────────────────────────────────────

  it('runChartAgnosticGate: does not throw for a clean registry', () => {
    const caps: CapabilityDescriptor[] = [makePerChart(), makeGlobal()]
    expect(() => runChartAgnosticGate(caps)).not.toThrow()
  })

  it('runChartAgnosticGate: throws for a dirty registry', () => {
    const dirty = makePerChart({ required_inputs: [] })
    expect(() => runChartAgnosticGate([dirty])).toThrow(/RULE-1-PER_CHART_MISSING_CHART_ID/)
  })

  it('runChartAgnosticGate: error message includes file:line-style URI + rule + detail', () => {
    const dirty = makePerChart({ required_inputs: [] })
    let message = ''
    try {
      runChartAgnosticGate([dirty])
    } catch (err) {
      message = err instanceof Error ? err.message : String(err)
    }
    expect(message).toContain('marsys://tool/L1/test_tool')
    expect(message).toContain('RULE-1-PER_CHART_MISSING_CHART_ID')
    expect(message).toContain('required_inputs')
  })

  // ── Edge cases ────────────────────────────────────────────────────────────────

  it('PASS: per_chart with additional required_inputs beyond chart_id', () => {
    const cap = makePerChart({ required_inputs: ['chart_id', 'graha', 'ayanamsha_id'] })
    const violations = checkCapability(cap)
    expect(violations).toHaveLength(0)
  })

  it('PASS: global tool with chart_id as optional (not required) input', () => {
    // e.g. a tool that accepts chart_id optionally but does not require it
    const cap = makeGlobal({
      input_schema: {
        chart_id: { type: 'string', description: 'Optional chart filter' },
        yoga_name: { type: 'string', description: 'Yoga name' },
      },
      required_inputs: ['yoga_name'],
    })
    const violations = checkCapability(cap)
    expect(violations).toHaveLength(0)
  })

  it('PASS: description with placeholder <chart_uuid> instead of literal uuid', () => {
    const cap = makePerChart({
      description: 'Returns positions for chart <chart_uuid>.',
    })
    const violations = checkCapability(cap)
    expect(violations).toHaveLength(0)
  })
})
