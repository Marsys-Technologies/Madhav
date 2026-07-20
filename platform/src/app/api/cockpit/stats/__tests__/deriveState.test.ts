/**
 * Badge-honesty unit tests (pre-D-4b readiness pass, 2026-07-21).
 *
 * The cockpit previously reported the same 'error' state for a genuinely broken writer
 * and a heavy (has_substeps) writer that had merely hit its own writer_timeout_seconds
 * mid-materialization (a safely resumable situation, per ka_gochara_sweep's own substep-
 * resumption ledger). deriveState now distinguishes them: any committed-substep evidence
 * for a has_substeps asset in the 'error' state downgrades the badge to 'partial'.
 */
import { describe, it, expect } from 'vitest'
import { deriveState } from '../deriveState'

describe('deriveState — badge-honesty (partial vs error)', () => {
  it('reports error for a non-substep asset with an error, regardless of substep count arg', () => {
    expect(
      deriveState({ has_substeps: false }, null, 'some real failure', 'error', 5)
    ).toBe('error')
  })

  it('reports error for a has_substeps asset with an error but zero committed substeps', () => {
    expect(
      deriveState({ has_substeps: true }, null, 'BLOCKED: upstream dependency(ies) timeout:1800s ...', 'error', 0)
    ).toBe('error')
  })

  it('reports error for a has_substeps asset with an error and null (unknown) substep count', () => {
    expect(
      deriveState({ has_substeps: true }, null, 'BLOCKED: upstream dependency(ies) timeout:1800s ...', 'error', null)
    ).toBe('error')
  })

  it('reports partial for a has_substeps asset with an error and >0 committed substeps', () => {
    expect(
      deriveState({ has_substeps: true }, null, 'BLOCKED: upstream dependency(ies) timeout:1800s ...', 'error', 3)
    ).toBe('partial')
  })

  it('never reports partial when there is no error at all, even with substep evidence', () => {
    // lit takes priority when rows are actually present -- partial is strictly an
    // error-state refinement, never a replacement for a genuinely healthy 'lit'.
    expect(
      deriveState({ has_substeps: true, target_floor: null }, 42, null, 'lit', 3)
    ).toBe('lit')
  })

  it('service/not_migrated/is_active=false still short-circuit before the partial check', () => {
    expect(deriveState({ asset_type: 'service', has_substeps: true }, null, 'x', 'error', 5)).toBe('service_ok')
    expect(deriveState({ is_active: false, has_substeps: true }, null, 'x', 'error', 5)).toBe('not_migrated')
  })
})
