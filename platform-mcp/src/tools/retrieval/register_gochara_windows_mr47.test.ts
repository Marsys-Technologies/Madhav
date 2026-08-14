/**
 * register_gochara_windows_mr47.test.ts — PARIṢKĀRA MR-47 / ADJUDICATOR
 * ruling PK-R-10 tests.
 *
 * PK-R-10 (corrected PK-R-7(iv)): a point-canonical class's R8.12
 * flat-production row (temporal_shape='interval', resolution=NULL) must
 * conform iff BOTH (1) it carries stored `shape_conformance=
 * 'point_class_context_envelope'`, derived from `brahma_event_ontology` at
 * WRITE time (migration 570's backfill / the writer's run_substep), and
 * (2) it serves `is_timing_window=false` under a point-class-specific
 * `blocked_reason` — NOT the generic `resolution_unavailable` fallback that
 * previously applied to every NULL-resolution, non-point, non-chain row
 * regardless of WHY resolution was NULL.
 *
 * Coverage:
 *   - deriveResolutionDisclosure: a row whose stored shape_conformance is
 *     'point_class_context_envelope' earns the new, class-specific
 *     'point_class_context_envelope' blocked_reason instead of the generic
 *     'resolution_unavailable'.
 *   - A row with shape_conformance='ontology_match' (or missing/null, e.g.
 *     a pre-migration-570 row) still falls through to the generic
 *     'resolution_unavailable' reason — this fix narrows ONLY the specific
 *     case PK-R-10 named, never silently changes behavior for any other row.
 *   - is_timing_window stays false either way (this fix only refines WHY,
 *     never flips whether a row earns is_timing_window=true).
 *
 * Unit tests (no live DB) — mirrors register_gochara_windows_mr11.test.ts's
 * `makeRow` pattern exactly.
 */

import { describe, it, expect } from 'vitest'
import {
  deriveResolutionDisclosure,
  type GocharaWindowRow,
} from './register_gochara_windows.js'

const LAMBDA_V3_COARSE_ARGMAX = 'gochara_lambda_v3_coarse_argmax'

function makeRow(overrides: Partial<GocharaWindowRow> = {}): GocharaWindowRow {
  return {
    id: 1,
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    event_class: 'marriage',
    temporal_shape: 'interval',
    window_start: '2013-01-01',
    window_end: '2013-01-08',
    peak_date: '2013-01-04',
    milestone_id: null,
    is_irreversibility_milestone: false,
    signed_intensity: 0.7,
    raw_intensity: 0.7,
    valence: 'neutral',
    is_adverse: false,
    active_sentences: [],
    contributing_systems: [],
    suppression_state: {},
    peak_basis: LAMBDA_V3_COARSE_ARGMAX,
    calibration_state: 'structural_prior',
    source: 'live',
    computed_at: '2026-08-11T00:00:00Z',
    continuity_state: null,
    plateau_disclosure: null,
    ...overrides,
  }
}

describe('deriveResolutionDisclosure — PK-R-10 point-class-envelope reason (MR-47)', () => {
  it('a row with shape_conformance="point_class_context_envelope" earns the class-specific reason, not the generic fallback', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'interval',
        resolution: null,
        shape_conformance: 'point_class_context_envelope',
      })
    )
    expect(d).toEqual({
      resolution: null,
      resolution_source: 'unavailable',
      is_timing_window: false,
      timing_window_blocked_reason: 'point_class_context_envelope',
    })
  })

  it('a row with shape_conformance="ontology_match" still falls through to the generic reason (this fix never widens beyond the named case)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'interval',
        resolution: null,
        shape_conformance: 'ontology_match',
      })
    )
    expect(d.timing_window_blocked_reason).toBe('resolution_unavailable')
    expect(d.is_timing_window).toBe(false)
  })

  it('a pre-migration-570 row (shape_conformance undefined/null) still gets the generic reason — no regression for unbackfilled rows', () => {
    const dUndefined = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'interval', resolution: null })
    )
    expect(dUndefined.timing_window_blocked_reason).toBe('resolution_unavailable')

    const dNull = deriveResolutionDisclosure(
      makeRow({ temporal_shape: 'interval', resolution: null, shape_conformance: null })
    )
    expect(dNull.timing_window_blocked_reason).toBe('resolution_unavailable')
  })

  it('shape_conformance is IGNORED for a point-shaped row (PK-R-1 floor still wins outright)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'point',
        resolution: null,
        shape_conformance: 'point_class_context_envelope',
      })
    )
    expect(d.is_timing_window).toBe(true)
    expect(d.timing_window_blocked_reason).toBeNull()
  })

  it('shape_conformance is IGNORED for an era-resolution row (clause 1 still wins outright)', () => {
    const d = deriveResolutionDisclosure(
      makeRow({
        temporal_shape: 'interval',
        resolution: 'era',
        shape_conformance: 'point_class_context_envelope',
      })
    )
    expect(d.timing_window_blocked_reason).toBe('era_resolution')
  })
})
