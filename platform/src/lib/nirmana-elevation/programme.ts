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

export type ProgrammeWpId = 'WP-1' | 'WP-2' | 'WP-3' | 'WP-6'
export type ProgrammeWpStatus = 'not_started' | 'in_progress' | 'merged'

export interface ProgrammeWpMergeRecord {
  number: number
  merged_at: string
}

export interface ProgrammeOWaveWpDeclaration {
  wp_id: ProgrammeWpId
  name: string
  status: ProgrammeWpStatus
  merged_pr?: ProgrammeWpMergeRecord
  note: string
}

/**
 * Repo-declared, not evidence-derived (CLAUDE.md §N.8 / plan Ruling R3/R5). All three
 * O-wave WPs are now stable, closed history — the race that made the original snapshot
 * go stale within 24 hours is over. Verified via `gh pr view <number>` by exact PR
 * number on 2026-09-05 (gh search is unreliable for these titles and is what produced
 * the original stale snapshot).
 */
export const PROGRAMME_O_WAVE_WPS: readonly ProgrammeOWaveWpDeclaration[] = [
  {
    wp_id: 'WP-1',
    name: 'Truthful invalidation (delta-directional staleness)',
    status: 'merged',
    merged_pr: { number: 1697, merged_at: '2026-09-03T23:18:59Z' },
    note: 'verified via gh pr view 1697, 2026-09-05 — stable history',
  },
  {
    wp_id: 'WP-2',
    name: 'Delta-skip',
    status: 'merged',
    merged_pr: { number: 1699, merged_at: '2026-09-04T00:21:53Z' },
    note: 'verified via gh pr view 1699, 2026-09-05 — stable history',
  },
  {
    wp_id: 'WP-3',
    name: 'Total plans',
    status: 'merged',
    merged_pr: { number: 1698, merged_at: '2026-09-03T23:55:49Z' },
    note: 'verified via gh pr view 1698, 2026-09-05 — stable history',
  },
]

/**
 * WP-6 "blast radius" (#1781, charter C13/D-NATIVE-05) is a post-O-wave addendum, not
 * O-wave scope (plan §3.4: WP-4/5/6 are out of O-wave scope). Kept in its own array so
 * `PROGRAMME_O_WAVE_WPS` stays exactly the 3 WPs the O-wave itself declared.
 */
export const PROGRAMME_POST_WAVE_ADDENDA: readonly ProgrammeOWaveWpDeclaration[] = [
  {
    wp_id: 'WP-6',
    name: 'Blast radius — dispatch refuses unacknowledged downstream destruction (charter C13 / D-NATIVE-05)',
    status: 'merged',
    merged_pr: { number: 1781, merged_at: '2026-09-05T04:57:25Z' },
    note: 'post-O-wave addendum — NOT O-wave scope per plan §3.4; verified via gh pr view 1781, 2026-09-05',
  },
]

export const PROGRAMME_ARC_PHASE_IDS = ['PHASE_A', 'O_WAVE', 'LAYERS', 'PHASE_Z'] as const
export type ProgrammeArcPhaseId = typeof PROGRAMME_ARC_PHASE_IDS[number]
export type ProgrammeArcPhaseState = 'completed' | 'in_progress' | 'pending' | null
export type ProgrammeArcPhaseProvenance = 'repo_declared' | 'evidence_derived'

export interface ProgrammeArcPhaseDeclaration {
  phase_id: ProgrammeArcPhaseId
  label: string
  declared_state: ProgrammeArcPhaseState
  provenance: ProgrammeArcPhaseProvenance
  note: string
}

/**
 * The four-phase arc strip. LAYERS and PHASE_Z carry `declared_state: null` by
 * construction — their state is evidence-derived downstream (per-layer ledger counts,
 * closing-stage receipts); this manifest is structurally incapable of declaring it
 * (CLAUDE.md §N.8 — a status must be backed by a real detector, or be null).
 */
export const PROGRAMME_ARC_PHASES: readonly ProgrammeArcPhaseDeclaration[] = [
  {
    phase_id: 'PHASE_A',
    label: 'Phase A',
    declared_state: 'completed',
    provenance: 'repo_declared',
    note: 'repo-declared — plan\'s own "PHASE A (COMPLETE)" line',
  },
  {
    phase_id: 'O_WAVE',
    label: 'O-Wave',
    declared_state: 'completed',
    provenance: 'repo_declared',
    note: 'repo-declared — all three O-wave WPs (WP-1/2/3) merged; see PROGRAMME_O_WAVE_WPS',
  },
  {
    phase_id: 'LAYERS',
    label: 'Layers',
    declared_state: null,
    provenance: 'evidence_derived',
    note: 'evidence-derived downstream from per-layer ledger counts — this manifest never declares it',
  },
  {
    phase_id: 'PHASE_Z',
    label: 'Phase Z',
    declared_state: null,
    provenance: 'evidence_derived',
    note: 'evidence-derived downstream from closing-stage receipts — this manifest never declares it',
  },
]

const L0_INDEX = NIRMANA_STAGE_IDS.indexOf('L0')

/** The 5 stages that fold into PHASE A's collapsed history (plan Ruling R1). */
export const PRE_L0_STAGE_IDS: readonly NirmanaStageId[] = NIRMANA_STAGE_IDS.slice(0, L0_INDEX)

/** The stages that map onto PHASE Z. */
export const POST_L5_STAGE_IDS: readonly NirmanaStageId[] = ['CLOSING', 'COMPLETE']
