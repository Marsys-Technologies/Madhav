import { describe, expect, it } from 'vitest'
import {
  NirmanaElevationSnapshotSchema,
  projectNirmanaElevationSnapshot,
  type NirmanaElevationRawSources,
} from '../snapshot'
import { canonicalManifestDigest } from '../definitions'

const observedAt = '2026-08-25T09:00:00.000Z'
const canonicalChartId = '482012f1-710e-4a25-994a-93821f5871aa'

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
        build_runs: [{ id: 'run-1', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
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
        manifest: { chart_id: canonicalChartId, assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] },
        manifest_sha256: canonicalManifestDigest({ chart_id: canonicalChartId, assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] }),
        created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'run-1', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-1', asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.assets_total).toBe(1)
    expect(snapshot.progress.assets_frozen).toBe(1)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('frozen')
  })

  it('requires a build asset accepted-rebuild receipt to name the completed build run exactly', () => {
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
      source_ref: event_type === 'accepted_rebuild_observed' ? 'build_run:run-not-complete' : `event:${event_type}`,
      observed_at: observedAt,
      recorded_at: observedAt,
    }))
    const manifest = { chart_id: canonicalChartId, assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] }
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'run-complete', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-complete', asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.accepted_rebuilds).toBe(0)
    expect(snapshot.progress.assets_frozen).toBe(0)
  })

  it('rejects an accepted build receipt when its otherwise-complete run belongs to a different chart', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules',
      layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence',
      source_ref: event_type === 'accepted_rebuild_observed' ? 'build_run:cross-chart-run' : `event:${event_type}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))
    const manifest = { chart_id: canonicalChartId, assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] }
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'cross-chart-run', chart_id: '11111111-1111-4111-8111-111111111111', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'cross-chart-run', asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ accepted_rebuilds: 0, assets_frozen: 0 })
  })

  it('accepts formal non-build dispositions and producer-covered evidence without a rebuild of the logical asset', () => {
    const assetIds = ['bg_source', 'bg_producer', 'bg_covered']
    const manifest = {
      chart_id: canonicalChartId,
      assets: [
        { asset_id: 'bg_source', layer: 'L0', execution_obligation: 'source_acceptance' },
        { asset_id: 'bg_producer', layer: 'L0', execution_obligation: 'build' },
        { asset_id: 'bg_covered', layer: 'L0', execution_obligation: 'producer_covered', producer_id: 'bg_producer' },
      ],
    }
    const lifecycleEvents = assetIds.flatMap((asset_id) => [
      'asset_analysis_accepted',
      'optimization_verdict_accepted',
      'integrity_verified',
      'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: asset_id,
      layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: `event:${event_type}:${asset_id}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))).concat([
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'source_accepted', entity_type: 'asset', entity_id: 'bg_source',
        layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: 'source:canonical', observed_at: observedAt, recorded_at: observedAt,
      },
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_producer',
        layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: 'build_run:producer-run', observed_at: observedAt, recorded_at: observedAt,
      },
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'producer_covered', entity_type: 'asset', entity_id: 'bg_covered',
        layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: 'build_run:producer-run', observed_at: observedAt, recorded_at: observedAt,
      },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetIds.map((asset_id, sort_order) => ({
        asset_id, english_name: asset_id, layer: 'brahmagyan', sort_order, has_writer: true, asset_type: 'data', asset_kind: 'data', is_active: true, depends_on: [],
      })),
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'producer-run', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'producer-run', asset_id: 'bg_producer', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ assets_frozen: 3, accepted_rebuilds: 1 })
    expect(snapshot.layers[0]).toMatchObject({ rebuilt_or_dispositioned: 3, frozen: 3 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_source')?.lifecycle_state).toBe('frozen')
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_covered')?.lifecycle_state).toBe('frozen')
  })

  it('withholds a frozen denominator that gives a producer-covered asset a dangling or non-build producer', () => {
    const assetIds = ['bg_source', 'bg_covered']
    const manifest = {
      chart_id: canonicalChartId,
      assets: [
        { asset_id: 'bg_source', layer: 'L0', execution_obligation: 'source_acceptance' },
        { asset_id: 'bg_covered', layer: 'L0', execution_obligation: 'producer_covered', producer_id: 'bg_source' },
      ],
    }
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetIds.map((asset_id, sort_order) => ({
        asset_id, english_name: asset_id, layer: 'brahmagyan', sort_order, has_writer: true, asset_type: 'data', asset_kind: 'data', is_active: true, depends_on: [],
      })),
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('withholds a frozen denominator that gives a producer-covered asset a missing producer', () => {
    const manifest = {
      chart_id: canonicalChartId,
      assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'producer_covered', producer_id: 'bg_missing' }],
    }
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('uses the latest active run for an asset rather than a historical run row that happens to arrive later', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources({
      build_runs: [
        { id: 'run-current', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: '2026-08-25T10:00:00.000Z', started_at: '2026-08-25T10:00:00.000Z' },
        { id: 'run-historical', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt },
      ],
      build_run_assets: [
        { run_id: 'run-current', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: '2026-08-25T10:00:00.000Z', ended_at: null, error: null },
        { run_id: 'run-historical', asset_id: 'bg_prashna_rules', position: 1, state: 'error', started_at: observedAt, ended_at: observedAt, error: 'obsolete failure' },
      ],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: 'building',
      blocker: null,
      progress_mode: 'indeterminate',
    })
  })

  it('keeps a running execution ahead of a newer planned retry for the same asset', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources({
      build_runs: [
        { id: 'run-running', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt },
        { id: 'run-planned-retry', chart_id: canonicalChartId, state: 'planned', current_asset_id: 'bg_prashna_rules', created_at: '2026-08-25T10:00:00.000Z', started_at: null },
      ],
      build_run_assets: [
        { run_id: 'run-running', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null },
        { run_id: 'run-planned-retry', asset_id: 'bg_prashna_rules', position: 1, state: 'planned', started_at: null, ended_at: null, error: null },
      ],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: 'building',
      progress_mode: 'indeterminate',
    })
  })

  it('withholds a claimed frozen denominator whose canonical manifest digest does not verify', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation',
        definition_revision: 'v1',
        definition_status: 'frozen',
        manifest: { chart_id: canonicalChartId, assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }] },
        manifest_sha256: '0'.repeat(64),
        created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })
})
