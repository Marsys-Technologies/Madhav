import { describe, expect, it } from 'vitest'
import {
  NirmanaElevationSnapshotSchema,
  projectNirmanaElevationSnapshot,
  type NirmanaElevationRawSources,
} from '../snapshot'
import { canonicalManifestDigest } from '../definitions'

const observedAt = '2026-08-25T09:00:00.000Z'

function sources(overrides: Partial<NirmanaElevationRawSources> = {}): NirmanaElevationRawSources {
  return {
    asset_registry: [
      {
        asset_id: 'bg_prashna_rules',
        english_name: 'Prashna Rules',
        layer: 'brahmagyan',
        sort_order: 1,
        has_writer: true,
        asset_type: 'data',
        asset_kind: 'data',
        is_active: true,
        depends_on: [],
      },
    ],
    asset_throughput: [{ asset_id: 'bg_prashna_rules', state: 'lit', last_built_at: observedAt }],
    build_runs: [],
    build_run_assets: [],
    build_substep_progress: [],
    campaign_definitions: [],
    campaign_events: [],
    ...overrides,
  }
}

describe('projectNirmanaElevationSnapshot', () => {
  it('starts in takeover/catalogue reconciliation and refuses denominator claims before a frozen definition', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources(), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({
      campaign_id: 'nirmana-elevation',
      definition_revision: null,
      definition_status: 'reconciling',
      campaign_status: 'takeover',
      current_layer: null,
      current_wave: null,
    })
    expect(snapshot.progress).toMatchObject({
      denominator_status: 'reconciling',
      assets_total: null,
      buildable_assets_total: null,
      assets_frozen: 0,
      accepted_rebuilds: 0,
    })
    expect(snapshot.layers).toHaveLength(6)
    expect(snapshot.layers.every((layer) => layer.assets_total === null)).toBe(true)
    expect(snapshot.assets).toEqual(expect.arrayContaining([
      expect.objectContaining({
        asset_id: 'bg_prashna_rules',
        readiness_state: 'lit',
        lifecycle_state: 'unverified',
        progress_mode: 'not_applicable',
      }),
    ]))
    expect(NirmanaElevationSnapshotSchema.safeParse(snapshot).success).toBe(true)
  })

  it('keeps current-run progress separate from persistent lit readiness', () => {
    const snapshot = projectNirmanaElevationSnapshot(
      sources({
        build_runs: [{ id: 'run-1', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
        build_run_assets: [{ run_id: 'run-1', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      }),
      { generatedAt: observedAt },
    )

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      readiness_state: 'lit',
      current_run_state: 'building',
      progress_mode: 'indeterminate',
      work_committed: null,
      work_total: null,
    })
    expect(snapshot.active_runs).toEqual([
      expect.objectContaining({
        run_id: 'run-1',
        active_asset_ids: ['bg_prashna_rules'],
        completed_assets: 0,
        planned_assets: 1,
      }),
    ])
  })

  it('does not let an uncorroborated frozen event turn primary evidence into elevation progress', () => {
    const snapshot = projectNirmanaElevationSnapshot(
      sources({
        campaign_events: [{
          campaign_id: 'nirmana-elevation',
          definition_revision: 'v1',
          event_type: 'asset_frozen',
          entity_type: 'asset',
          entity_id: 'bg_prashna_rules',
          layer: 'L0',
          evidence_payload: {},
          source_kind: 'campaign_evidence',
          source_ref: 'event:unverified',
          observed_at: observedAt,
          recorded_at: observedAt,
        }],
      }),
      { generatedAt: observedAt },
    )

    expect(snapshot.progress.assets_frozen).toBe(0)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('unverified')
  })

  it('counts an asset frozen only after a frozen manifest, all lifecycle receipts, and a completed build-run receipt agree', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted',
      'optimization_verdict_accepted',
      'accepted_rebuild_observed',
      'integrity_verified',
      'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      event_type,
      entity_type: 'asset',
      entity_id: 'bg_prashna_rules',
      layer: 'L0',
      evidence_payload: {},
      source_kind: 'campaign_evidence',
      source_ref: event_type === 'accepted_rebuild_observed' ? 'build_run:run-1' : `event:${event_type}`,
      observed_at: observedAt,
      recorded_at: observedAt,
    }))
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation',
        definition_revision: 'v1',
        definition_status: 'frozen',
        manifest: { assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] },
        manifest_sha256: canonicalManifestDigest({ assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] }),
        created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'run-1', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-1', asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.assets_total).toBe(1)
    expect(snapshot.progress.assets_frozen).toBe(1)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('frozen')
  })

  it('withholds a claimed frozen denominator whose canonical manifest digest does not verify', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation',
        definition_revision: 'v1',
        definition_status: 'frozen',
        manifest: { assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] },
        manifest_sha256: '0'.repeat(64),
        created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })
})
