/**
 * server_tool_registration.test.ts
 * No-tier assertion test suite.
 *
 * D0.5 (2026-06-28): replaces server_tier_visibility.test.ts.
 * Stream A 3.tier_excision (2026-05-28) removed audience_tier from Principal.
 * House rules collapsed to a single universal variant (D0.5).
 *
 * This test asserts:
 * 1. Principal type has no audience_tier field.
 * 2. house_rules resource exports getHouseRules() (universal, no tier arg).
 * 3. The universal variant file loads and contains the quality bar marker.
 */

import { describe, it, expect } from 'vitest'
import type { Principal } from '../types.js'
import { getHouseRules } from '../resources/house_rules.js'

// ── No-tier Principal assertion ───────────────────────────────────────────────

describe('Principal — no audience_tier (tier system excised)', () => {
  it('Principal type has user_uid and key_id only', () => {
    const p: Principal = {
      user_uid: 'uid-test',
      key_id: 'key-test',
    }
    expect(p.user_uid).toBe('uid-test')
    expect(p.key_id).toBe('key-test')
    // @ts-expect-error — audience_tier must not exist on Principal
    expect(p.audience_tier).toBeUndefined()
  })

  it('Principal object has no audience_tier property at runtime', () => {
    const p: Principal = { user_uid: 'uid-x', key_id: 'key-x' }
    expect(Object.prototype.hasOwnProperty.call(p, 'audience_tier')).toBe(false)
  })
})

// ── Universal house rules assertion ──────────────────────────────────────────

describe('house_rules — universal variant (no tier conditioning)', () => {
  it('getHouseRules() returns a non-empty string', () => {
    const rules = getHouseRules()
    expect(typeof rules).toBe('string')
    expect(rules.length).toBeGreaterThan(100)
  })

  it('universal rules contain the quality bar section', () => {
    const rules = getHouseRules()
    expect(rules).toContain('Acharya-grade')
  })

  it('universal rules contain the PPL discipline section', () => {
    const rules = getHouseRules()
    expect(rules).toContain('log_prediction')
  })

  it('universal rules contain the B.11 Floor section', () => {
    const rules = getHouseRules()
    expect(rules).toContain('B.11')
  })

  it('universal rules do NOT contain tier-conditional language', () => {
    const rules = getHouseRules()
    // These tier-specific labels should not appear in the universal variant
    expect(rules).not.toContain('Tier: super_admin')
    expect(rules).not.toContain('Tier: acharya')
    expect(rules).not.toContain('Tier: client')
  })

  it('getHouseRules() accepts no arguments (no tier parameter)', () => {
    // If tier gating existed, this would require a tier argument
    const fn = getHouseRules
    expect(fn.length).toBe(0)  // no required parameters
  })
})
