import { describe, expect, it } from 'vitest'
import {
  NirmanaElevationSnapshotSchema,
  NirmanaElevationSnapshotV1Schema,
  NirmanaElevationSnapshotV2Schema,
  type NirmanaElevationSnapshotV2,
} from '../types'
import { fixtureV2 } from './fixture-v2'

const expectedStageIds = [
  'BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION',
  'L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'CLOSING', 'COMPLETE',
]

function copyFixture(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

const v1Fixture = {
  schema_version: '1.0', generation: 'b'.repeat(64), generated_at: '2026-08-26T00:00:00.000Z',
  campaign: { campaign_id: 'nirmana-elevation', definition_revision: null, definition_status: 'reconciling', campaign_status: 'takeover', current_layer: null, current_wave: null },
  progress: { denominator_status: 'reconciling', assets_total: null, assets_frozen: 0, layers_total: 6, layers_frozen: 0, buildable_assets_total: null, accepted_rebuilds: 0 },
  layers: [], assets: [], active_runs: [],
  release: { main_sha: null, deployed_sha: null, deployed_revision: null, production_in_sync: null, observed_at: null },
  sources: [], data_quality: { verdict: 'unknown', gaps: [], contradictions: [] },
} as const

describe('Nirmana elevation snapshot v2 contract', () => {
  it('parses the fixture only as schema version 2.0', () => {
    expect(NirmanaElevationSnapshotV2Schema.safeParse(fixtureV2).success).toBe(true)
    expect(NirmanaElevationSnapshotV1Schema.safeParse(fixtureV2).success).toBe(false)
    expect(NirmanaElevationSnapshotSchema.parse(fixtureV2).schema_version).toBe('2.0')
  })

  it('contains exactly the 13 governed stages in order', () => {
    expect(expectedStageIds).toHaveLength(13)
    expect(fixtureV2.stages).toHaveLength(13)
    expect(fixtureV2.stages.map((stage) => stage.stage_id)).toEqual(expectedStageIds)
    expect(NirmanaElevationSnapshotV2Schema.safeParse(fixtureV2).success).toBe(true)
  })

  it('allows a null current stage when no valid transition is known', () => {
    const snapshot = copyFixture()
    snapshot.campaign.current_stage = null
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(true)
  })

  it('rejects a bare layer without its governed layer name', () => {
    const snapshot = copyFixture()
    delete (snapshot.layers[0] as { layer_name?: string }).layer_name
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(false)
  })

  it('rejects an asset without separate identity fields and milestones', () => {
    const snapshot = copyFixture()
    delete (snapshot.assets[0] as { english_name?: string }).english_name
    delete (snapshot.assets[0] as { milestones?: unknown }).milestones
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(false)
  })

  it('accepts complete, incomplete, and unversioned-fallback identity quality', () => {
    expect(NirmanaElevationSnapshotV2Schema.safeParse(fixtureV2).success).toBe(true)
    const snapshot = copyFixture()
    snapshot.assets[1].sanskrit_name = null
    snapshot.assets[1].description = null
    snapshot.assets[1].identity_quality = 'incomplete'
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(true)

    snapshot.assets[1].identity_quality = 'unversioned_fallback'
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(true)
  })

  it('requires structured legacy aliases with their own stable asset identity', () => {
    const snapshot = copyFixture()
    const asset = snapshot.assets.find((candidate) => candidate.asset_id === 'ka_smriti')
    if (!asset) throw new Error('Projected fixture must include ka_smriti.')
    asset.legacy_aliases = [{ asset_id: 'A22', sanskrit_name: 'Varsha-Darshan', english_name: 'Yearly Vision' }]
    const parsed = NirmanaElevationSnapshotV2Schema.parse(snapshot)
    expect(parsed.assets.find((candidate) => candidate.asset_id === 'ka_smriti')?.legacy_aliases[0]?.asset_id).toBe('A22')

    asset.legacy_aliases = ['Per-varsha digest'] as unknown as Array<{ asset_id: string; sanskrit_name: string | null; english_name: string | null }>
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(false)
  })

  it('accepts null milestone counters for an unresolved obligation', () => {
    const snapshot = copyFixture()
    snapshot.assets[0].execution_obligation = 'unresolved'
    snapshot.assets[0].milestones_earned = null
    snapshot.assets[0].milestones_required = null
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(true)
  })

  it('computes determinate milestone counters around not-applicable milestones', () => {
    const snapshot = copyFixture()
    const asset = snapshot.assets.find((candidate) => candidate.asset_id === 'bg_prashna_rules')!
    asset.milestones[5].state = 'not_applicable'
    asset.milestones_required = 5
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(true)
  })

  it('rejects contradictory determinate milestone counters', () => {
    const snapshot = copyFixture()
    const asset = snapshot.assets.find((candidate) => candidate.asset_id === 'bg_prashna_rules')!
    asset.milestones_earned = 6
    asset.milestones_required = 6
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(false)
  })

  it('accepts a v1 fixture through the compatibility union', () => {
    expect(NirmanaElevationSnapshotV1Schema.safeParse(v1Fixture).success).toBe(true)
    expect(NirmanaElevationSnapshotSchema.safeParse(v1Fixture).success).toBe(true)
  })

  it('requires the normalized v2 operational-state and server audit contracts', () => {
    const snapshot = copyFixture()
    delete (snapshot.assets.find((candidate) => candidate.asset_id === 'bg_prashna_rules') as { campaign_state?: string }).campaign_state
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(false)

    const legacyWave = copyFixture()
    ;(legacyWave.layers[0].waves[0] as { state: string }).state = 'running'
    expect(NirmanaElevationSnapshotV2Schema.safeParse(legacyWave).success).toBe(false)

    const noAudit = copyFixture()
    delete (noAudit as { audit?: unknown }).audit
    expect(NirmanaElevationSnapshotV2Schema.safeParse(noAudit).success).toBe(false)
  })
})
