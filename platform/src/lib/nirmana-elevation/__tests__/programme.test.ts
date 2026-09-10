import { describe, expect, it } from 'vitest'
import {
  PRE_L0_STAGE_IDS,
  POST_L5_STAGE_IDS,
  PROGRAMME_ARC_PHASES,
  PROGRAMME_O_WAVE_WPS,
  PROGRAMME_POST_WAVE_ADDENDA,
  PROGRAMME_WAVE_IDS,
  PROGRAMME_WAVES,
} from '../programme'
import { NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from '../vocab'

describe('programme manifest', () => {
  it('declares exactly 6 waves, one per milestone, in milestone order', () => {
    expect(PROGRAMME_WAVES.map((w) => w.wave_id)).toEqual(PROGRAMME_WAVE_IDS)
    expect(PROGRAMME_WAVES.map((w) => w.milestone_id)).toEqual(NIRMANA_MILESTONE_IDS)
  })

  it('declares exactly 3 O-wave WPs, all merged with a verified merged_pr, as stable history', () => {
    expect(PROGRAMME_O_WAVE_WPS.map((wp) => wp.wp_id)).toEqual(['WP-1', 'WP-2', 'WP-3'])
    for (const wp of PROGRAMME_O_WAVE_WPS) {
      expect(wp.status).toBe('merged')
      expect(wp.merged_pr).toBeDefined()
      expect(Number.isInteger(wp.merged_pr?.number)).toBe(true)
      expect(wp.note).toContain('verified via gh pr view')
    }
    expect(PROGRAMME_O_WAVE_WPS.find((wp) => wp.wp_id === 'WP-1')?.merged_pr?.number).toBe(1697)
    expect(PROGRAMME_O_WAVE_WPS.find((wp) => wp.wp_id === 'WP-2')?.merged_pr?.number).toBe(1699)
    expect(PROGRAMME_O_WAVE_WPS.find((wp) => wp.wp_id === 'WP-3')?.merged_pr?.number).toBe(1698)
  })

  it('keeps WP-6 out of PROGRAMME_O_WAVE_WPS, in a separate post-wave addenda array', () => {
    expect(PROGRAMME_O_WAVE_WPS.some((wp) => wp.wp_id === 'WP-6')).toBe(false)
    expect(PROGRAMME_POST_WAVE_ADDENDA.map((wp) => wp.wp_id)).toEqual(['WP-6'])
    const wp6 = PROGRAMME_POST_WAVE_ADDENDA[0]
    expect(wp6?.status).toBe('merged')
    expect(wp6?.merged_pr?.number).toBe(1781)
    expect(wp6?.note).toContain('NOT O-wave scope')
  })

  it('declares exactly 4 arc phases; LAYERS and PHASE_Z cannot declare an evidence-derived state', () => {
    expect(PROGRAMME_ARC_PHASES.map((p) => p.phase_id)).toEqual(['PHASE_A', 'O_WAVE', 'LAYERS', 'PHASE_Z'])

    const phaseA = PROGRAMME_ARC_PHASES.find((p) => p.phase_id === 'PHASE_A')
    expect(phaseA?.declared_state).toBe('completed')
    expect(phaseA?.provenance).toBe('repo_declared')

    const oWave = PROGRAMME_ARC_PHASES.find((p) => p.phase_id === 'O_WAVE')
    expect(oWave?.declared_state).toBe('completed')
    expect(oWave?.provenance).toBe('repo_declared')

    // §N.8 guard: the manifest is structurally incapable of declaring these — they are
    // evidence-derived downstream, so this file must not fabricate a status for them.
    const layers = PROGRAMME_ARC_PHASES.find((p) => p.phase_id === 'LAYERS')
    expect(layers?.declared_state).toBeNull()
    expect(layers?.provenance).toBe('evidence_derived')

    const phaseZ = PROGRAMME_ARC_PHASES.find((p) => p.phase_id === 'PHASE_Z')
    expect(phaseZ?.declared_state).toBeNull()
    expect(phaseZ?.provenance).toBe('evidence_derived')
  })

  it('PRE_L0_STAGE_IDS is exactly the stages before L0, in order', () => {
    expect(PRE_L0_STAGE_IDS).toEqual(['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION'])
    expect(NIRMANA_STAGE_IDS.slice(0, PRE_L0_STAGE_IDS.length)).toEqual(PRE_L0_STAGE_IDS)
  })

  it('POST_L5_STAGE_IDS is exactly CLOSING, COMPLETE', () => {
    expect(POST_L5_STAGE_IDS).toEqual(['CLOSING', 'COMPLETE'])
  })
})
