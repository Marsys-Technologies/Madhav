import type { NirmanaStageId } from './projection'
import { NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from './vocab'

type NirmanaMilestoneId = typeof NIRMANA_MILESTONE_IDS[number]

export const PROGRAMME_WAVE_IDS = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6'] as const
export type ProgrammeWaveId = typeof PROGRAMME_WAVE_IDS[number]

export interface ProgrammeWaveDefinition {
  wave_id: ProgrammeWaveId
  label: string
  milestone_id: NirmanaMilestoneId
}

/**
 * 1:1 mapping onto NIRMANA_MILESTONE_IDS — six programme sub-waves, six existing
 * asset milestones. Never merge or split these; see plan Ruling R3.
 */
export const PROGRAMME_WAVES: readonly ProgrammeWaveDefinition[] = [
  { wave_id: 'W1', label: 'ANALYZE', milestone_id: 'analysed' },
  { wave_id: 'W2', label: 'DECIDE', milestone_id: 'decision_accepted' },
  { wave_id: 'W3', label: 'IMPLEMENT', milestone_id: 'built_or_dispositioned' },
  { wave_id: 'W4', label: 'EXECUTE', milestone_id: 'deployed_and_executed' },
  { wave_id: 'W5', label: 'VERIFY+CAPSULE', milestone_id: 'verified' },
  { wave_id: 'W6', label: 'FREEZE', milestone_id: 'frozen' },
]

export type ProgrammeWpId = 'WP-1' | 'WP-2' | 'WP-3'
export type ProgrammeWpStatus = 'not_started' | 'in_progress' | 'merged'

export interface ProgrammeOWaveWpDeclaration {
  wp_id: ProgrammeWpId
  name: string
  status: ProgrammeWpStatus
  note: string
}

/**
 * Repo-declared, not evidence-derived (CLAUDE.md §N.8 / plan Ruling R5). Updated by the
 * O-wave PRs themselves as they merge — this file's values are a snapshot as of the PR
 * that introduces it, verified against live PR state at write time (see Task 1 Step 1).
 */
export const PROGRAMME_O_WAVE_WPS: readonly ProgrammeOWaveWpDeclaration[] = [
  {
    wp_id: 'WP-1',
    name: 'Truthful invalidation (delta-directional staleness)',
    status: 'not_started',
    note: 'repo-declared — flipped by the WP-1 PR on merge, not evidence-derived',
  },
  {
    wp_id: 'WP-2',
    name: 'Delta-skip',
    status: 'not_started',
    note: 'repo-declared — flipped by the WP-2 PR on merge, not evidence-derived',
  },
  {
    wp_id: 'WP-3',
    name: 'Total plans',
    status: 'not_started',
    note: 'repo-declared — flipped by the WP-3 PR on merge, not evidence-derived',
  },
]

const L0_INDEX = NIRMANA_STAGE_IDS.indexOf('L0')

/** The 5 stages that fold into PHASE A's collapsed history (plan Ruling R1). */
export const PRE_L0_STAGE_IDS: readonly NirmanaStageId[] = NIRMANA_STAGE_IDS.slice(0, L0_INDEX)

/** The stages that map onto PHASE Z. */
export const POST_L5_STAGE_IDS: readonly NirmanaStageId[] = ['CLOSING', 'COMPLETE']
