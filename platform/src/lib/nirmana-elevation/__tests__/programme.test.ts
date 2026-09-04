import { describe, expect, it } from 'vitest'
import {
  PRE_L0_STAGE_IDS,
  POST_L5_STAGE_IDS,
  PROGRAMME_O_WAVE_WPS,
  PROGRAMME_WAVE_IDS,
  PROGRAMME_WAVES,
} from '../programme'
import { NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from '../vocab'

describe('programme manifest', () => {
  it('declares exactly 6 waves, one per milestone, in milestone order', () => {
    expect(PROGRAMME_WAVES.map((w) => w.wave_id)).toEqual(PROGRAMME_WAVE_IDS)
    expect(PROGRAMME_WAVES.map((w) => w.milestone_id)).toEqual(NIRMANA_MILESTONE_IDS)
  })

  it('declares exactly 3 O-wave WPs, all repo-declared, none guessed merged without a source', () => {
    expect(PROGRAMME_O_WAVE_WPS.map((wp) => wp.wp_id)).toEqual(['WP-1', 'WP-2', 'WP-3'])
    for (const wp of PROGRAMME_O_WAVE_WPS) {
      expect(['not_started', 'in_progress', 'merged']).toContain(wp.status)
      expect(wp.note).toContain('repo-declared')
    }
  })

  it('PRE_L0_STAGE_IDS is exactly the stages before L0, in order', () => {
    expect(PRE_L0_STAGE_IDS).toEqual(['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION'])
    expect(NIRMANA_STAGE_IDS.slice(0, PRE_L0_STAGE_IDS.length)).toEqual(PRE_L0_STAGE_IDS)
  })

  it('POST_L5_STAGE_IDS is exactly CLOSING, COMPLETE', () => {
    expect(POST_L5_STAGE_IDS).toEqual(['CLOSING', 'COMPLETE'])
  })
})
