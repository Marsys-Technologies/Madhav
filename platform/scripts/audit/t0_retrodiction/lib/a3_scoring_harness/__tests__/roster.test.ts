/**
 * roster.test.ts — D-4b permission-bridge lane. Proves the ACTIVE_ROSTER
 * shape (13 evaluable contenders, no NOT-EVALUABLE stubs) independent of
 * any live sidecar call.
 */
import { describe, it, expect } from 'vitest'
import { buildActiveRoster, buildActiveRosterWithEnsemble, NOT_EVALUABLE_MODEL_IDS } from '../roster'
import { PERMISSION_SYSTEM_IDS } from '../permission_model'

describe('buildActiveRoster', () => {
  it('is exactly 13 models: pratyantar_lord + the 12 PERMISSION standalone generators', () => {
    const roster = buildActiveRoster({ marriage: { Venus: 1.0 } }, { sidecarUrl: 'http://fake' })
    expect(roster).toHaveLength(13)
    const ids = roster.map((m) => m.modelId)
    expect(ids).toContain('pratyantar_lord')
    for (const sid of PERMISSION_SYSTEM_IDS) expect(ids).toContain(sid)
  })

  it('never includes a NOT-EVALUABLE contender (midpoint_triangle, transit_kernel)', () => {
    const roster = buildActiveRoster({ marriage: { Venus: 1.0 } }, { sidecarUrl: 'http://fake' })
    const ids = roster.map((m) => m.modelId)
    for (const notEvaluable of NOT_EVALUABLE_MODEL_IDS) expect(ids).not.toContain(notEvaluable)
  })
})

describe('buildActiveRosterWithEnsemble', () => {
  it('is the 13-model roster plus exactly one hierarchical_ensemble entry (14 total)', () => {
    const roster = buildActiveRosterWithEnsemble({ marriage: { Venus: 1.0 } }, { sidecarUrl: 'http://fake' })
    expect(roster).toHaveLength(14)
    expect(roster.filter((m) => m.modelId === 'hierarchical_ensemble')).toHaveLength(1)
  })
})
