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
import type { AssetState } from '../deriveState'
import { mapDbStateToUiState } from '@/components/build_orchestrator/AssetNode'

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

/**
 * SAMĀPTI B-COCKPIT-INCOMPLETE — DVA Ruling 24.
 *
 * THE DEFECT THESE TESTS PIN, stated as it existed on origin/main @ 5f5033a5:
 *
 *   deriveState's only non-lit path for an asset carrying rows was
 *     `if (error) { if (has_substeps && substepsCommitted > 0) return 'partial' } ...`
 *   With `error` NULL, control fell through to `if (actualRows > 0) return 'lit'`.
 *
 *   The Python orchestrator's 'incomplete' write path
 *   (asset_runner.py::_run_data_writer, the SATYA-DĪPA no-op-completion rejection)
 *   executes exactly one UPDATE:
 *     SET state = 'incomplete', rows_written = <rows present>, last_error = NULL
 *   — state 'incomplete', rows PRESENT, error NULL. All three legs of the fallthrough.
 *
 *   So a Python-produced incomplete asset rendered a green LIT badge in the cockpit,
 *   today, in production, while asset_throughput.state honestly read 'incomplete' and
 *   the backend correctly kept every downstream dependant blocked. A falsely-lit
 *   operator surface, and a direct falsification of the convergence assertion
 *   "no asset lit with an incomplete substep plan".
 *
 * THE ACCEPTANCE CRITERION (Ruling 24, verbatim): construct an incomplete asset with
 * actualRows > 0 and confirm the badge is never 'lit' — under BOTH last_error-set and
 * last_error-null conditions. Both conditions are real and both occur in this system:
 * the TypeScript watchdog route writes 'incomplete' WITH a last_error string; the Python
 * path writes it with last_error NULL.
 */
describe('deriveState — incomplete is never lit (SAMĀPTI B-COCKPIT-INCOMPLETE, DVA Ruling 24)', () => {
  const PY_ERROR = null                 // Python path: asset_runner.py sets last_error = NULL
  const TS_ERROR =                      // TypeScript watchdog path: sets an explanatory string
    "orphan-watchdog: heartbeat went stale while a substep plan was in flight. 12 substep(s) " +
    "committed and 4210 data row(s) are present, but this route cannot prove the plan finished, " +
    "so the asset was NOT promoted to 'lit'."

  it('ACCEPTANCE — incomplete + rows present is never lit, under BOTH error conditions', () => {
    const asset = { has_substeps: true, target_floor: 10_000 }

    // Condition A — last_error NULL (the Python orchestrator path; the live defect).
    const nullErrorBadge = deriveState(asset, 4210, PY_ERROR, 'incomplete', 12)
    expect(nullErrorBadge).not.toBe('lit')
    expect(nullErrorBadge).toBe('incomplete')

    // Condition B — last_error SET (the TypeScript watchdog path).
    const setErrorBadge = deriveState(asset, 4210, TS_ERROR, 'incomplete', 12)
    expect(setErrorBadge).not.toBe('lit')
    expect(setErrorBadge).toBe('incomplete')

    // And the point of Ruling 24's structural clause: one stored state, one badge.
    // The presence or absence of a diagnostic STRING must not change what the asset IS.
    expect(nullErrorBadge).toBe(setErrorBadge)
  })

  it('holds across the whole plausible input space, not just one row count', () => {
    // Every combination that can reach this function for a state='incomplete' row.
    const rowCounts = [1, 42, 4210, 585_710]
    const errors: (string | null)[] = [null, TS_ERROR, 'timeout', '']
    const substeps: (number | null)[] = [null, 0, 1, 303]
    const hasSubsteps = [true, false]
    const floors: (number | null)[] = [null, 0, 10_000]

    for (const rows of rowCounts)
      for (const err of errors)
        for (const committed of substeps)
          for (const hs of hasSubsteps)
            for (const target_floor of floors) {
              const badge = deriveState({ has_substeps: hs, target_floor }, rows, err, 'incomplete', committed)
              expect(
                badge,
                `rows=${rows} error=${JSON.stringify(err)} committed=${committed} has_substeps=${hs} floor=${target_floor}`
              ).toBe('incomplete')
            }
  })

  it('the branch is keyed on the state column, not on rows — 0 rows and null rows are also incomplete', () => {
    // Reading asset_throughput.state is the mechanism (Ruling 24 clause 3). It must not
    // quietly depend on a second signal that a future change could remove.
    expect(deriveState({ has_substeps: true }, 0, null, 'incomplete', 0)).toBe('incomplete')
    expect(deriveState({ has_substeps: true }, null, null, 'incomplete', null)).toBe('incomplete')
    // Including the target_floor=0 "0 rows is correct and complete" carve-out, which must
    // NOT rescue an incomplete asset into lit.
    expect(deriveState({ has_substeps: true, target_floor: 0 }, 0, null, 'incomplete', 0)).toBe('incomplete')
  })

  it('service and not_migrated still short-circuit ahead of it (ordering unchanged)', () => {
    expect(deriveState({ asset_type: 'service' }, 99, null, 'incomplete', 3)).toBe('service_ok')
    expect(deriveState({ asset_kind: 'service' }, 99, null, 'incomplete', 3)).toBe('service_ok')
    expect(deriveState({ is_active: false }, 99, null, 'incomplete', 3)).toBe('not_migrated')
  })

  it('does not disturb any other state — the branch is additive, not a rewrite', () => {
    expect(deriveState({ target_floor: null }, 42, null, 'lit', null)).toBe('lit')
    expect(deriveState({ target_floor: null }, 42, null, 'building', null)).toBe('building')
    expect(deriveState({ target_floor: null }, 0, null, 'stale', null)).toBe('stale')
    expect(deriveState({ target_floor: null }, 0, null, 'dormant', null)).toBe('dormant')
    expect(deriveState({ has_substeps: true }, null, 'boom', 'error', 7)).toBe('partial')
    expect(deriveState({ has_substeps: false }, null, 'boom', 'error', 7)).toBe('error')
    expect(deriveState({ target_floor: 0 }, 0, null, 'lit', null)).toBe('lit')
  })

  it('the belt-and-braces error path still works — neither mechanism is now load-bearing alone', () => {
    // Ruling 24: the last_error-keyed mitigation becomes belt-and-braces, NOT the sole
    // mechanism. Prove it is still there: if a future write path emitted 'error' rather
    // than 'incomplete' for a mid-plan asset, the partial downgrade still catches it.
    expect(deriveState({ has_substeps: true }, 4210, 'timeout', 'error', 12)).toBe('partial')
    // And prove the new mechanism does not need it: state alone suffices.
    expect(deriveState({ has_substeps: true }, 4210, null, 'incomplete', 12)).toBe('incomplete')
  })
})

describe('cockpit surfaces never collapse incomplete into a done-equivalent', () => {
  it('mapDbStateToUiState maps incomplete to its own state, never to complete', () => {
    expect(mapDbStateToUiState('incomplete')).toBe('incomplete')
    expect(mapDbStateToUiState('incomplete')).not.toBe('complete')
    // Guard against the fallback swallowing it back: an unmapped state returns 'pending',
    // which would be a false report in the other direction (claims no data exists).
    expect(mapDbStateToUiState('incomplete')).not.toBe('pending')
    // Unchanged neighbours.
    expect(mapDbStateToUiState('lit')).toBe('complete')
    expect(mapDbStateToUiState('error')).toBe('failed')
    expect(mapDbStateToUiState('totally-unknown-state')).toBe('pending')
  })

  it('incomplete is a member of the served AssetState contract', () => {
    // Compile-time assertion made runtime-visible: if 'incomplete' were dropped from the
    // union in deriveState.ts, this file would stop type-checking.
    const s: AssetState = 'incomplete'
    expect(s).toBe('incomplete')
  })
})
