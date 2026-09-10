/**
 * kala_e8_register.test.ts — unit tests for the E8 non-elevations register.
 *
 * Per KALA_SUPREME_ELEVATION_v1_0.md §14:
 *   "E8 the non-elevations register (§13) — standing constraints, carried as
 *   a ledger row and verified respected at every wave gate; the only E-row
 *   that is never 'built', only 'held'."
 *
 * These tests enforce the structural invariants that wave-gate reviewers rely on:
 *  1. All IDs are unique.
 *  2. HELD entries have no lifted_by.
 *  3. LIFTED entries have a non-null lifted_by.
 *  4. All registered dates are well-formed ISO dates.
 *  5. Each of the five §13-seeded constraints is present and HELD.
 *  6. heldNonElevations() returns only HELD entries.
 *  7. lookupNonElevation() resolves known IDs and returns undefined for unknowns.
 *
 * SAMPURTI G12 (2026-08-10).
 */

import {
  KALA_E8_NON_ELEVATIONS,
  heldNonElevations,
  lookupNonElevation,
  type NonElevationEntry,
} from './kala_e8_register.js'

// ── Structural invariants ─────────────────────────────────────────────────────

describe('KALA_E8_NON_ELEVATIONS — structural invariants', () => {
  it('has at least one entry (the register is populated, not vacuously empty)', () => {
    expect(KALA_E8_NON_ELEVATIONS.length).toBeGreaterThan(0)
  })

  it('all entry IDs are unique (no duplicate registration)', () => {
    const ids = KALA_E8_NON_ELEVATIONS.map((e) => e.id)
    const unique = new Set(ids)
    expect(unique.size).toBe(ids.length)
  })

  it('HELD entries have no lifted_by', () => {
    const violations = KALA_E8_NON_ELEVATIONS.filter(
      (e) => e.disposition === 'HELD' && e.lifted_by !== null,
    )
    expect(violations).toHaveLength(0)
  })

  it('LIFTED entries have a non-null lifted_by', () => {
    const violations = KALA_E8_NON_ELEVATIONS.filter(
      (e) => e.disposition === 'LIFTED' && e.lifted_by === null,
    )
    expect(violations).toHaveLength(0)
  })

  it('all registered dates are well-formed ISO YYYY-MM-DD strings', () => {
    for (const entry of KALA_E8_NON_ELEVATIONS) {
      expect(entry.registered).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      const d = new Date(entry.registered)
      expect(Number.isNaN(d.getTime())).toBe(false)
    }
  })

  it('all entries have non-empty constraint, rationale, and scope', () => {
    for (const entry of KALA_E8_NON_ELEVATIONS) {
      expect(entry.constraint.trim().length).toBeGreaterThan(0)
      expect(entry.rationale.trim().length).toBeGreaterThan(0)
      expect(entry.scope.trim().length).toBeGreaterThan(0)
    }
  })
})

// ── §13 mandated constraints ──────────────────────────────────────────────────
// KALA_SUPREME_ELEVATION_v1_0.md §13 names three explicit non-elevations plus
// the praśna and strangler-fig constraints. All five must be present and HELD.

const MANDATED_IDS = [
  'NO_LLM_IN_SERVING_PATH',
  'NO_PERCENTAGES_BEFORE_CALIBRATION',
  'NO_SUB_DAY_TRANSIT_PRECISION_BEFORE_GOCHARA_2',
  'NO_PRASHNA_AT_EVERY_QUERY',
  'STRANGLER_FIG_DISCIPLINE',
] as const

describe('§13 mandated constraints are present and HELD', () => {
  for (const id of MANDATED_IDS) {
    it(`${id} exists and is HELD`, () => {
      const entry = lookupNonElevation(id)
      expect(entry).toBeDefined()
      expect((entry as NonElevationEntry).disposition).toBe('HELD')
    })
  }
})

// ── heldNonElevations() ───────────────────────────────────────────────────────

describe('heldNonElevations()', () => {
  it('returns only HELD entries', () => {
    const held = heldNonElevations()
    expect(held.every((e) => e.disposition === 'HELD')).toBe(true)
  })

  it('length equals the count of HELD entries in the full register', () => {
    const heldCount = KALA_E8_NON_ELEVATIONS.filter((e) => e.disposition === 'HELD').length
    expect(heldNonElevations().length).toBe(heldCount)
  })

  it('includes all five §13-mandated constraints (all currently HELD)', () => {
    const heldIds = new Set(heldNonElevations().map((e) => e.id))
    for (const id of MANDATED_IDS) {
      expect(heldIds.has(id)).toBe(true)
    }
  })
})

// ── lookupNonElevation() ──────────────────────────────────────────────────────

describe('lookupNonElevation()', () => {
  it('resolves known IDs to their entry', () => {
    const entry = lookupNonElevation('NO_LLM_IN_SERVING_PATH')
    expect(entry).toBeDefined()
    expect(entry?.id).toBe('NO_LLM_IN_SERVING_PATH')
  })

  it('returns undefined for an unknown ID (§N.8 — absent signal is null, not green)', () => {
    const entry = lookupNonElevation('DOES_NOT_EXIST')
    expect(entry).toBeUndefined()
  })

  it('is consistent with the full register (result is same object)', () => {
    for (const registered of KALA_E8_NON_ELEVATIONS) {
      const found = lookupNonElevation(registered.id)
      expect(found).toBe(registered)
    }
  })
})
