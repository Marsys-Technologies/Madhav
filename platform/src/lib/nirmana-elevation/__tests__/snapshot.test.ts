import { describe, expect, it } from 'vitest'
import {
  NirmanaElevationSnapshotSchema,
  projectNirmanaElevationSnapshot,
  type NirmanaElevationRawSources,
} from '../snapshot'
import { canonicalManifestDigest, canonicalRegistryContractDigest } from '../definitions'

const observedAt = '2026-08-25T09:00:00.000Z'
const canonicalChartId = '482012f1-710e-4a25-994a-93821f5871aa'

type RegistryAsset = NirmanaElevationRawSources['asset_registry'][number]
type ManifestSpec = {
  asset_id: string
  layer?: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'
  wave_index?: number
  execution_obligation: 'build' | 'probe' | 'producer_covered' | 'static_acceptance' | 'source_acceptance' | 'empty_acceptance' | 'retired_with_disposition' | 'unresolved'
  producer_id?: string
  covered_asset_ids?: string[]
}

function registryAsset(overrides: Partial<RegistryAsset> = {}): RegistryAsset {
  return {
    asset_id: 'bg_prashna_rules', english_name: 'Prashna Rules', layer: 'brahmagyan', scope: 'per_chart',
    sort_order: 1, has_writer: true, asset_type: 'data', asset_kind: 'data', catalog_status: 'CURRENT',
    is_active: true, depends_on: [], target_table: 'bg_prashna_rules',
    count_sql: 'SELECT count(*) FROM bg_prashna_rules', integrity_check_sql: null, health_probe: null,
    natural_key_partition: null, superseded_by: null, data_disposition: null, dead_flag: null,
    ...overrides,
  }
}

function manifestFor(registry: RegistryAsset[], specs: ManifestSpec[]) {
  const registryById = new Map(registry.map((asset) => [asset.asset_id, asset]))
  return {
    chart_id: canonicalChartId,
    assets: specs.map((spec) => {
      const row = registryById.get(spec.asset_id)
      if (!row) throw new Error(`missing test registry row ${spec.asset_id}`)
      const layer = spec.layer ?? ({ brahmagyan: 'L0', ganita: 'L1', bodha: 'L2', kala: 'L3', phala: 'L4', mimamsa: 'L5' } as const)[row.layer]
      const registry_contract = {
        sort_order: row.sort_order, scope: row.scope, asset_kind: row.asset_kind, catalog_status: row.catalog_status,
        is_active: row.is_active, has_writer: row.has_writer, target_table: row.target_table, count_sql: row.count_sql,
        integrity_check_sql: row.integrity_check_sql, health_probe: row.health_probe,
        natural_key_partition: row.natural_key_partition, superseded_by: row.superseded_by,
        data_disposition: row.data_disposition, dead_flag: row.dead_flag,
      }
      const asset = {
        ...spec,
        layer,
        wave_index: spec.wave_index ?? 0,
        depends_on: row.depends_on ?? [],
        registry_contract,
      }
      return {
        ...asset,
        registry_fingerprint_sha256: canonicalRegistryContractDigest({
          asset_id: asset.asset_id, layer: asset.layer, depends_on: asset.depends_on, registry_contract,
        }),
      }
    }),
  }
}

const defaultRegistry = [registryAsset()]
const defaultManifest = () => manifestFor(defaultRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])

function sources(overrides: Partial<NirmanaElevationRawSources> = {}): NirmanaElevationRawSources {
  return {
    asset_registry: defaultRegistry,
    asset_throughput: [{ asset_id: 'bg_prashna_rules', chart_id: canonicalChartId, state: 'lit', last_built_at: observedAt }],
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
        readiness_state: 'unknown',
        lifecycle_state: 'unverified',
        progress_mode: 'not_applicable',
      }),
    ]))
    expect(NirmanaElevationSnapshotSchema.safeParse(snapshot).success).toBe(true)
  })

  it('projects available release observations while withholding a commit-unproven sync verdict', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources(), {
      generatedAt: observedAt,
      releaseStatus: {
        release: {
          main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01704-mvb',
          production_in_sync: null, observed_at: observedAt,
        },
        sources: [
          { source_id: 'github_main', provenance: 'GitHub public commits API', state: 'fresh', observed_at: observedAt, age_seconds: 0, error: null },
          { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'fresh', observed_at: observedAt, age_seconds: 0, error: null },
          { source_id: 'artifact_registry_commit', provenance: 'Serving revision immutable commit provenance', state: 'unknown', observed_at: observedAt, age_seconds: null, error: 'No immutable deployment commit SHA is present on the serving revision.' },
        ],
        gaps: ['Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.'],
      },
    })

    expect(snapshot.release).toMatchObject({ main_sha: 'a'.repeat(40), deployed_sha: null, production_in_sync: null })
    expect(snapshot.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({ source_id: 'github_main', state: 'fresh' }),
      expect.objectContaining({ source_id: 'artifact_registry_commit', state: 'unknown' }),
    ]))
    expect(snapshot.data_quality.gaps).toContain('Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.')
  })

  it('keeps current-run progress separate from persistent lit readiness', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(
      sources({
        campaign_definitions: [{
          campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
          manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
        }],
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

  it('derives the campaign layer and wave from the selected canonical active run', () => {
    const manifest = manifestFor(defaultRegistry, [{ asset_id: 'bg_prashna_rules', wave_index: 0, execution_obligation: 'build' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{ id: 'run-current', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-current', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({ current_layer: 'L0', current_wave: 0 })
    expect(snapshot.layers[0]?.state).toBe('open')
  })

  it('retains the latest terminal asset error when no active retry has replaced it', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{ id: 'failed-run', chart_id: canonicalChartId, state: 'failed', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'failed-run', asset_id: 'bg_prashna_rules', position: 1, state: 'running', started_at: observedAt, ended_at: observedAt, error: 'writer failed its integrity check' }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: null,
      blocker: 'writer failed its integrity check',
    })
  })

  it('retains terminal failure context while a later run retries the asset', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [
        { id: 'failed-run', chart_id: canonicalChartId, state: 'failed', current_asset_id: 'bg_prashna_rules', created_at: '2026-08-25T09:00:00.000Z', started_at: '2026-08-25T09:00:00.000Z' },
        { id: 'retry-run', chart_id: canonicalChartId, state: 'planned', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: null },
      ],
      build_run_assets: [
        { run_id: 'failed-run', asset_id: 'bg_prashna_rules', position: 1, state: 'error', started_at: '2026-08-25T09:00:00.000Z', ended_at: '2026-08-25T09:01:00.000Z', error: 'writer failed its integrity check' },
        { run_id: 'retry-run', asset_id: 'bg_prashna_rules', position: 1, state: 'planned', started_at: null, ended_at: null, error: null },
      ],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: 'planned',
      blocker: 'Previous failed run failed-run: writer failed its integrity check; retry run retry-run is planned.',
    })
  })

  it('labels cross-attempt substep receipts as historical resumable work, not current progress', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{ id: 'run-current', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-current', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      build_substep_progress: [{ chart_id: canonicalChartId, asset_id: 'bg_prashna_rules', committed: 7, last_progress_at: observedAt }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      progress_mode: 'indeterminate',
      work_committed: null,
      work_total: null,
      current_unit_label: 'Historical resumable work: 7 committed substeps',
    })
  })

  it('credits a global manifest asset through the mandatory canonical-chart cockpit build receipt', () => {
    const assetRegistry = [registryAsset({ scope: 'global' })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])
    const lifecycleEvents = [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules',
      layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: event_type === 'accepted_rebuild_observed' ? 'build_run:canonical-global-run' : `event:${event_type}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      asset_throughput: [{ asset_id: 'bg_prashna_rules', chart_id: null, state: 'lit', last_built_at: observedAt }],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'canonical-global-run', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'canonical-global-run', asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('frozen')
  })

  it('never credits an F0 machinery canary as an accepted campaign rebuild', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'accepted_rebuild_observed',
        entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0', evidence_payload: {},
        source_kind: 'campaign_evidence', source_ref: 'build_run:f0-canary-run',
        observed_at: observedAt, recorded_at: observedAt,
      }],
      build_runs: [{
        id: 'f0-canary-run', chart_id: canonicalChartId, state: 'completed', current_asset_id: null,
        created_at: observedAt, started_at: observedAt, triggered_by: 'nirmana-f0-machinery-canary',
      }],
      build_run_assets: [{
        run_id: 'f0-canary-run', asset_id: 'bg_prashna_rules', position: 1, state: 'complete',
        started_at: observedAt, ended_at: observedAt, error: null,
      }],
    } as Partial<NirmanaElevationRawSources>), { generatedAt: observedAt })

    expect(snapshot.progress.accepted_rebuilds).toBe(0)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('catalogued')
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
    const manifest = defaultManifest()
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
        manifest,
        manifest_sha256: canonicalManifestDigest(manifest),
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
    const manifest = defaultManifest()
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
    const manifest = defaultManifest()
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

  it('withholds a build-obligated denominator for an active registry asset cockpit cannot dispatch', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules',
      layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence',
      source_ref: event_type === 'accepted_rebuild_observed' ? 'build_run:run-1' : `event:${event_type}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))
    const assetRegistry = [registryAsset({ has_writer: false })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'run-1', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-1', asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'reconciling', buildable_assets_total: null, accepted_rebuilds: 0, assets_frozen: 0 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('unverified')
  })

  it('allows an active non-writer asset to freeze only through its frozen formal non-build disposition', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'source_accepted', 'integrity_verified', 'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: 'lel_events',
      layer: 'L5', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: `event:${event_type}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))
    const assetRegistry = [registryAsset({
      asset_id: 'lel_events', english_name: 'Life Events', layer: 'mimamsa', sort_order: 0,
      has_writer: false, catalog_status: 'DRAFT', target_table: null,
      count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1',
    })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'lel_events', execution_obligation: 'source_acceptance' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', buildable_assets_total: 0, accepted_rebuilds: 0, assets_frozen: 1 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'lel_events')).toMatchObject({
      execution_obligation: 'source_acceptance',
      lifecycle_state: 'frozen',
    })
  })

  it('accepts formal non-build dispositions and producer-covered evidence without a rebuild of the logical asset', () => {
    const assetIds = ['lel_events', 'bg_transit_rules', 'bg_transit_engine']
    const assetRegistry = [
      registryAsset({
        asset_id: 'lel_events', english_name: 'Life Events', layer: 'mimamsa', sort_order: 0,
        has_writer: false, catalog_status: 'DRAFT', target_table: null,
        count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1',
      }),
      registryAsset({ asset_id: 'bg_transit_rules', english_name: 'Transit Rules', sort_order: 1, target_table: 'bg_transit_rules', count_sql: 'SELECT count(*) FROM bg_transit_rules' }),
      registryAsset({ asset_id: 'bg_transit_engine', english_name: 'Transit Engine', sort_order: 2, has_writer: false, target_table: 'bg_transit_engine', count_sql: 'SELECT count(*) FROM bg_transit_engine' }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'lel_events', execution_obligation: 'source_acceptance' },
      { asset_id: 'bg_transit_rules', execution_obligation: 'build', covered_asset_ids: ['bg_transit_engine'] },
      { asset_id: 'bg_transit_engine', execution_obligation: 'producer_covered', producer_id: 'bg_transit_rules' },
    ])
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
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'source_accepted', entity_type: 'asset', entity_id: 'lel_events',
        layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: 'source:canonical', observed_at: observedAt, recorded_at: observedAt,
      },
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'accepted_rebuild_observed', entity_type: 'asset', entity_id: 'bg_transit_rules',
        layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: 'build_run:producer-run', observed_at: observedAt, recorded_at: observedAt,
      },
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'producer_covered', entity_type: 'asset', entity_id: 'bg_transit_engine',
        layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence', source_ref: 'build_run:producer-run', observed_at: observedAt, recorded_at: observedAt,
      },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: 'producer-run', chart_id: canonicalChartId, state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'producer-run', asset_id: 'bg_transit_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ assets_frozen: 3, accepted_rebuilds: 1 })
    expect(snapshot.layers[0]).toMatchObject({ rebuilt_or_dispositioned: 2, frozen: 2 })
    expect(snapshot.layers[5]).toMatchObject({ rebuilt_or_dispositioned: 1, frozen: 1 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'lel_events')?.lifecycle_state).toBe('frozen')
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.lifecycle_state).toBe('frozen')
  })

  it('withholds a frozen denominator that gives a producer-covered asset a dangling or non-build producer', () => {
    const assetIds = ['bg_source', 'bg_covered']
    const assetRegistry = assetIds.map((asset_id, sort_order) => registryAsset({ asset_id, english_name: asset_id, sort_order, target_table: asset_id, count_sql: `SELECT count(*) FROM ${asset_id}` }))
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_source', execution_obligation: 'source_acceptance' },
      { asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: 'bg_source' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('withholds a frozen denominator that gives a producer-covered asset a missing producer', () => {
    const assetRegistry = [registryAsset({
      asset_id: 'bg_sign_medical', english_name: 'Sign Medical', has_writer: false,
      target_table: 'bg_sign_medical', count_sql: 'SELECT count(*) FROM bg_sign_medical',
    })]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_sign_medical', execution_obligation: 'producer_covered', producer_id: 'bg_medical_mappings' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('uses the latest active run for an asset rather than a historical run row that happens to arrive later', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
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
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
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

  it('does not project a different chart\'s throughput as canonical readiness', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_throughput: [{ asset_id: 'bg_prashna_rules', chart_id: '11111111-1111-4111-8111-111111111111', state: 'lit', last_built_at: observedAt }],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.readiness_state).toBe('unknown')
  })

  it('does not expose another chart\'s active run in the campaign projection', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{ id: 'other-chart-run', chart_id: '11111111-1111-4111-8111-111111111111', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'other-chart-run', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.active_runs).toEqual([])
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.current_run_state).toBeNull()
  })

  it('does not use another chart\'s substep receipts for canonical active progress', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{ id: 'canonical-run', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'canonical-run', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      build_substep_progress: [{ chart_id: '11111111-1111-4111-8111-111111111111', asset_id: 'bg_prashna_rules', committed: 99, last_progress_at: observedAt }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.current_unit_label).toBe('execution in progress')
  })

  it('retains only explicitly global throughput rows as safe shared evidence', () => {
    const assetRegistry = [registryAsset({ scope: 'global' })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      asset_throughput: [
        { asset_id: 'bg_prashna_rules', chart_id: null, state: 'lit', last_built_at: observedAt },
        { asset_id: 'bg_prashna_rules', chart_id: '11111111-1111-4111-8111-111111111111', state: 'error', last_built_at: observedAt },
      ],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.readiness_state).toBe('lit')
  })

  it('keeps an adjudicated retired asset inside the frozen denominator', () => {
    const assetRegistry = [
      registryAsset(),
      registryAsset({
        asset_id: 'ka_gochara_sweep', english_name: 'Retired Gochara Sweep', layer: 'kala', sort_order: 105,
        is_active: false, catalog_status: 'RETIRED', target_table: 'kala_gochara_windows',
        count_sql: "SELECT count(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'",
        superseded_by: 'bg_prashna_rules', data_disposition: 'RETAINED_AS_CAPITAL',
      }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_prashna_rules', execution_obligation: 'build' },
      { asset_id: 'ka_gochara_sweep', execution_obligation: 'retired_with_disposition' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 2 })
    expect(snapshot.assets.map((asset) => asset.asset_id)).toContain('ka_gochara_sweep')
  })

  it('keeps the frozen denominator while blocking unaccepted per-asset registry-contract drift', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: [registryAsset({ count_sql: 'SELECT count(*) FROM drifted_table' })],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.assets[0]).toMatchObject({
      lifecycle_state: 'blocked',
      blocker: expect.stringContaining('registry contract changed after the frozen T0 definition'),
    })
    expect(snapshot.assets[0].evidence_refs).toEqual(expect.arrayContaining([
      `registry:t0:${manifest.assets[0].registry_fingerprint_sha256}`,
      expect.stringMatching(/^registry:live:[a-f0-9]{64}$/),
    ]))
    expect(snapshot.assets[0].evidence_refs.find((reference) => reference.startsWith('registry:live:')))
      .not.toBe(`registry:live:${manifest.assets[0].registry_fingerprint_sha256}`)
    expect(snapshot.data_quality.gaps).toContain('1 asset registry contract has changed without a matching accepted analysis fingerprint.')
    expect(snapshot.data_quality.contradictions).toEqual(['bg_prashna_rules'])
  })

  it('accepts governed contract evolution only when asset analysis pins the current registry fingerprint', () => {
    const manifest = defaultManifest()
    const driftedRegistry = [registryAsset({ count_sql: 'SELECT count(*) FROM evolved_table' })]
    const currentFingerprint = canonicalRegistryContractDigest({
      asset_id: 'bg_prashna_rules',
      layer: 'L0',
      depends_on: [],
      registry_contract: {
        ...manifest.assets[0].registry_contract,
        count_sql: 'SELECT count(*) FROM evolved_table',
      },
    })
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: driftedRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_analysis_accepted',
        entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { registry_fingerprint_sha256: currentFingerprint, analysis_digest: 'a'.repeat(64) },
        source_kind: 'git_commit', source_ref: `git:${'b'.repeat(40)}`,
        observed_at: observedAt, recorded_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.assets[0]).toMatchObject({ lifecycle_state: 'catalogued', blocker: null })
    expect(snapshot.assets[0].evidence_refs).toEqual(expect.arrayContaining([
      `registry:live:${currentFingerprint}`,
      `registry:accepted:${currentFingerprint}`,
      `analysis:sha256:${'a'.repeat(64)}`,
    ]))
    expect(snapshot.data_quality.gaps).not.toContain(expect.stringContaining('registry contract has changed'))
    expect(snapshot.data_quality.contradictions).toEqual([])
  })

  it('does not let a stale analysis receipt accept a later registry-contract mutation', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: [registryAsset({ count_sql: 'SELECT count(*) FROM later_mutation' })],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_analysis_accepted',
        entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { registry_fingerprint_sha256: 'c'.repeat(64), analysis_digest: 'a'.repeat(64) },
        source_kind: 'git_commit', source_ref: `git:${'b'.repeat(40)}`,
        observed_at: observedAt, recorded_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.assets[0]).toMatchObject({ lifecycle_state: 'blocked' })
    expect(snapshot.data_quality.contradictions).toEqual(['bg_prashna_rules'])
  })

  it('still fails closed when the current registry changes the frozen asset/DAG identity', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: [registryAsset({ layer: 'ganita' })],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'reconciling', assets_total: null })
  })

  it('withholds a claimed frozen denominator whose canonical manifest digest does not verify', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation',
        definition_revision: 'v1',
        definition_status: 'frozen',
        manifest,
        manifest_sha256: '0'.repeat(64),
        created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })
})
