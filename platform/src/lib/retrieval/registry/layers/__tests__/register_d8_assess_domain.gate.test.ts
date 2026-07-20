/**
 * D8 Assess-Domain Gate Test
 * ==========================
 * Verifies that all D8_CAPABILITY_URIS are registered and pass the
 * chart-agnostic gate (7 rules). Runs as part of CI.
 *
 * GATE A: only tests the per-wave registration; does not re-test L0-L5 caps.
 */

import { describe, it, expect, beforeAll } from 'vitest'
import {
  registerD8AssessDomainCapabilities,
  D8_CAPABILITY_URIS,
  TEMPORAL_EMPTY_REASON,
} from '../register_d8_assess_domain'
import { clearRegistry, getAllCapabilities, hasCapability } from '../../index'
import { checkAllCapabilities, checkTextForNativeLeak } from '../../chart_agnostic_gate'

describe('D8 Assess-Domain — capability registration gate', () => {
  beforeAll(() => {
    clearRegistry()
    registerD8AssessDomainCapabilities()
  })

  it('registers all 5 D8 URIs', () => {
    for (const uri of D8_CAPABILITY_URIS) {
      expect(hasCapability(uri), `Missing capability: ${uri}`).toBe(true)
    }
    expect(D8_CAPABILITY_URIS.length).toBe(5)
  })

  it('all D8 capabilities pass the chart-agnostic gate (7 rules)', () => {
    const allCaps = getAllCapabilities()
    const d8Caps = allCaps.filter(c => (D8_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    const violations = checkAllCapabilities(d8Caps)
    expect(violations, violations.map(v => `${v.uri}: ${v.rule}`).join('\n')).toHaveLength(0)
  })

  it('all D8 capabilities are per_chart with chart_id in required_inputs', () => {
    const allCaps = getAllCapabilities()
    const d8Caps = allCaps.filter(c => (D8_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    for (const cap of d8Caps) {
      expect(cap.scope, `${cap.uri} should be per_chart`).toBe('per_chart')
      expect(
        cap.required_inputs?.includes('chart_id'),
        `${cap.uri} is per_chart but required_inputs missing chart_id`
      ).toBe(true)
    }
    expect(d8Caps.length).toBe(5)
  })

  it('all D8 capabilities emit references (F1 compliance)', () => {
    const allCaps = getAllCapabilities()
    const d8Caps = allCaps.filter(c => (D8_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    for (const cap of d8Caps) {
      expect(cap.emits_references, `${cap.uri} must set emits_references=true`).toBe(true)
    }
  })

  it('assess_* tools use traversal_level L-DOMAIN; yoga bridge uses L-SIGNAL', () => {
    const allCaps = getAllCapabilities()
    const d8Caps = allCaps.filter(c => (D8_CAPABILITY_URIS as readonly string[]).includes(c.uri))
    for (const cap of d8Caps) {
      if (cap.uri.includes('assess_')) {
        expect(cap.traversal_level, `${cap.uri} should be L-DOMAIN`).toBe('L-DOMAIN')
      } else if (cap.uri.includes('yoga_activation_by_dasha')) {
        expect(cap.traversal_level, `${cap.uri} should be L-SIGNAL`).toBe('L-SIGNAL')
      }
    }
  })

  // Regression protection for the GT-32/GT-54 TEMPORAL_EMPTY_REASON leak: this imports the
  // REAL exported constant from register_d8_assess_domain.ts (not a synthetic copy) and runs
  // it through the real chart-agnostic-gate scanner. If a future edit reintroduces a
  // native-derived cardinality literal or chart-phrase into this string, this test catches it.
  it('TEMPORAL_EMPTY_REASON (real constant) has zero checkTextForNativeLeak violations', () => {
    const violations = checkTextForNativeLeak(TEMPORAL_EMPTY_REASON, 'd8_temporal_empty_reason')
    expect(violations, violations.map(v => `${v.rule}: ${v.detail ?? ''}`).join('\n')).toHaveLength(0)
  })
})
