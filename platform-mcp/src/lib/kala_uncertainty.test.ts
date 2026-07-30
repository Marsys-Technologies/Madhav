/**
 * kala_uncertainty.test.ts — ṢAḌ-DARŚANA W1 item 24-lite. Unit tests for the pure
 * Sūkṣma-boundary interval convention (`kala_uncertainty.ts`). No network, no DB — exercises
 * the documented lite-v0 convention directly against constructed `chart_dashas`-shaped rows.
 */
import { describe, it, expect } from 'vitest'
import {
  buildSukshmaBoundaryInterval,
  buildSukshmaBoundaryIntervals,
  SUKSHMA_INTERVAL_CONVENTION_ID,
} from './kala_uncertainty.js'

describe('buildSukshmaBoundaryInterval — item 24-lite convention', () => {
  it('bounds the instant symmetrically by half the period\'s own duration_days', () => {
    const iv = buildSukshmaBoundaryInterval({
      systemId: 'vimshottari',
      lordGraha: 'Mercury',
      edge: 'start',
      instantIso: '2026-08-15T00:00:00.000Z',
      durationDays: 10,
    })
    expect(iv).not.toBeNull()
    expect(iv!.half_span_days).toBe(5)
    expect(iv!.lower_bound_iso).toBe('2026-08-10T00:00:00.000Z')
    expect(iv!.upper_bound_iso).toBe('2026-08-20T00:00:00.000Z')
    expect(iv!.convention_id).toBe(SUKSHMA_INTERVAL_CONVENTION_ID)
    expect(iv!.convention).toContain('NOT the birth-time/ayanāṁśa error-propagation model')
  })

  it('is a pure/deterministic function — same input, byte-identical output', () => {
    const params = { systemId: 'vimshottari', lordGraha: 'Venus', edge: 'end' as const, instantIso: '2027-01-01T12:00:00.000Z', durationDays: 3.5 }
    expect(buildSukshmaBoundaryInterval(params)).toEqual(buildSukshmaBoundaryInterval(params))
  })

  it('never fabricates an interval from an invalid instant', () => {
    expect(buildSukshmaBoundaryInterval({ systemId: 'vimshottari', lordGraha: 'Sun', edge: 'start', instantIso: 'not-a-date', durationDays: 10 })).toBeNull()
  })

  it('never fabricates an interval from a missing/zero/negative duration', () => {
    const base = { systemId: 'vimshottari', lordGraha: 'Sun', edge: 'start' as const, instantIso: '2026-01-01T00:00:00.000Z' }
    expect(buildSukshmaBoundaryInterval({ ...base, durationDays: 0 })).toBeNull()
    expect(buildSukshmaBoundaryInterval({ ...base, durationDays: -1 })).toBeNull()
    expect(buildSukshmaBoundaryInterval({ ...base, durationDays: NaN })).toBeNull()
  })
})

describe('buildSukshmaBoundaryIntervals — row-level convenience (start + end)', () => {
  it('produces both edges for a well-formed chart_dashas-shaped row', () => {
    const ivs = buildSukshmaBoundaryIntervals({
      system_id: 'vimshottari',
      lord_graha: 'Jupiter',
      start_iso: '2026-06-01T00:00:00.000Z',
      end_iso: '2026-06-21T00:00:00.000Z',
      duration_days: 20,
    })
    expect(ivs).toHaveLength(2)
    expect(ivs[0]!.edge).toBe('start')
    expect(ivs[1]!.edge).toBe('end')
    expect(ivs[0]!.half_span_days).toBe(10)
  })

  it('accepts duration_days as a numeric string (Postgres NUMERIC often serializes as string)', () => {
    const ivs = buildSukshmaBoundaryIntervals({
      system_id: 'vimshottari',
      lord_graha: 'Saturn',
      start_iso: '2026-06-01T00:00:00.000Z',
      end_iso: '2026-06-21T00:00:00.000Z',
      duration_days: '20.0',
    })
    expect(ivs).toHaveLength(2)
    expect(ivs[0]!.half_span_days).toBe(10)
  })

  it('honestly serves only the resolvable edge when one boundary instant is missing (never fabricated)', () => {
    const ivs = buildSukshmaBoundaryIntervals({
      system_id: 'vimshottari',
      lord_graha: 'Rahu',
      start_iso: '2026-06-01T00:00:00.000Z',
      end_iso: null,
      duration_days: 20,
    })
    expect(ivs).toHaveLength(1)
    expect(ivs[0]!.edge).toBe('start')
  })

  it('returns an empty array (never fabricated) for a row with no usable duration', () => {
    const ivs = buildSukshmaBoundaryIntervals({
      system_id: 'vimshottari',
      lord_graha: 'Ketu',
      start_iso: '2026-06-01T00:00:00.000Z',
      end_iso: '2026-06-21T00:00:00.000Z',
      duration_days: null,
    })
    expect(ivs).toHaveLength(0)
  })
})
