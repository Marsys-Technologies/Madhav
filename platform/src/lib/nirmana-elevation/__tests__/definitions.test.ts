import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import {
  canonicalManifestDigest,
  canonicalRegistryContractDigest,
  createNirmanaElevationDefinition,
  freezeNirmanaElevationDefinition,
  recordNirmanaElevationEvidence,
} from '../definitions'

const registry_contract = {
  sort_order: 1,
  scope: 'global' as const,
  asset_kind: 'data' as const,
  catalog_status: 'CURRENT' as const,
  is_active: true,
  has_writer: true,
  target_table: 'bg_prashna_rules',
  count_sql: 'SELECT count(*) FROM bg_prashna_rules',
  integrity_check_sql: null,
  health_probe: null,
  natural_key_partition: null,
  superseded_by: null,
  data_disposition: null,
  dead_flag: null,
}
const manifestAsset = {
  asset_id: 'bg_prashna_rules',
  layer: 'L0' as const,
  wave_index: 0,
  execution_obligation: 'build' as const,
  depends_on: [],
  registry_contract,
  registry_fingerprint_sha256: canonicalRegistryContractDigest({
    asset_id: 'bg_prashna_rules',
    layer: 'L0',
    depends_on: [],
    registry_contract,
  }),
}
const manifest = {
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  assets: [manifestAsset],
}
const reconciledT0Manifest = JSON.parse(readFileSync(
  new URL('../../../../../00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_0.json', import.meta.url),
  'utf8',
))

function registryRowsFor(candidate: typeof manifest | typeof reconciledT0Manifest) {
  const layerNames = { L0: 'brahmagyan', L1: 'ganita', L2: 'bodha', L3: 'kala', L4: 'phala', L5: 'mimamsa' } as const
  return candidate.assets.map((asset: typeof manifestAsset) => ({
    asset_id: asset.asset_id,
    layer: layerNames[asset.layer],
    depends_on: asset.depends_on,
    ...asset.registry_contract,
  }))
}

describe('Nirmana elevation definition repository', () => {
  beforeEach(() => queryMock.mockReset())

  it('derives one canonical SHA-256 digest for the validated manifest', () => {
    expect(canonicalManifestDigest(manifest)).toMatch(/^[a-f0-9]{64}$/)
  })

  it('requires the frozen manifest to pin its campaign chart', () => {
    expect(() => canonicalManifestDigest({ assets: manifest.assets })).toThrow(/chart_id/i)
    expect(() => canonicalManifestDigest({ ...manifest, chart_id: '11111111-1111-4111-8111-111111111111' })).toThrow(/chart_id/i)
  })

  it('gives JSONB-equivalent manifests the same digest regardless of object-key order', () => {
    const reordered = {
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      assets: [{
        registry_fingerprint_sha256: manifestAsset.registry_fingerprint_sha256,
        registry_contract: { ...registry_contract },
        depends_on: [],
        execution_obligation: 'build',
        wave_index: 0,
        layer: 'L0',
        asset_id: 'bg_prashna_rules',
      }],
    }
    expect(canonicalManifestDigest(reordered)).toBe(canonicalManifestDigest(manifest))
  })

  it('accepts every formal non-build execution obligation in a frozen denominator', () => {
    const nonBuildManifest = {
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      assets: [
        { asset_id: 'bg_non_build_producer', layer: 'L0', execution_obligation: 'build' },
        ...['probe', 'static_acceptance', 'source_acceptance', 'empty_acceptance', 'retired_with_disposition'].map((execution_obligation, index) => ({
          asset_id: `bg_non_build_${index}`,
          layer: 'L0',
          execution_obligation,
        })),
        { asset_id: 'bg_non_build_covered', layer: 'L0', execution_obligation: 'producer_covered', producer_id: 'bg_non_build_producer' },
      ],
    }

    expect(() => canonicalManifestDigest(nonBuildManifest)).not.toThrow()
  })

  it('validates the full 128-asset T0 manifest, exact DAG waves, and registry fingerprints', async () => {
    expect(reconciledT0Manifest.assets).toHaveLength(128)
    expect(canonicalManifestDigest(reconciledT0Manifest)).toBe('c0097895ab6b5318e8b9a2c34de34f7fe685eedfe9b8fb2293abe78593a5a3c4')

    queryMock
      .mockResolvedValueOnce({ rows: registryRowsFor(reconciledT0Manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      definition_revision: 't0-v1',
      manifest: reconciledT0Manifest,
      manifest_sha256: canonicalManifestDigest(reconciledT0Manifest),
    })).resolves.toBe('frozen')
  })

  it('rejects a mismatched digest before attempting an insert or freeze', async () => {
    await expect(createNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      definition_status: 'reconciling',
      manifest,
      manifest_sha256: '0'.repeat(64),
      created_by: 'admin-1',
    })).rejects.toThrow(/digest/i)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('persists only a validated definition revision', async () => {
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    await expect(createNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      definition_status: 'reconciling',
      manifest,
      manifest_sha256: canonicalManifestDigest(manifest),
      created_by: 'admin-1',
    })).resolves.toBe('created')

    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(queryMock.mock.calls[0][0]).toContain('ON CONFLICT (campaign_id, definition_revision) DO NOTHING')
  })

  it('accepts an exact retried definition revision without overwriting its first receipt', async () => {
    queryMock
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{ definition_status: 'reconciling', manifest_sha256: canonicalManifestDigest(manifest) }] })

    await expect(createNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'reconciling', manifest,
      manifest_sha256: canonicalManifestDigest(manifest), created_by: 'admin-2',
    })).resolves.toBe('idempotent')
    expect(queryMock).toHaveBeenCalledTimes(2)
  })

  it('freezes only the exact prior reconciling manifest and accepts an exact retry', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 1, rows: [] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256: canonicalManifestDigest(manifest),
    })).resolves.toBe('frozen')

    queryMock
      .mockResolvedValueOnce({ rows: registryRowsFor(manifest) })
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{ definition_status: 'frozen', manifest_sha256: canonicalManifestDigest(manifest) }] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256: canonicalManifestDigest(manifest),
    })).resolves.toBe('idempotent')
  })

  it('refuses to freeze when any pinned registry contract differs from the live row', async () => {
    const driftedRows = registryRowsFor(manifest)
    driftedRows[0].count_sql = 'SELECT count(*) FROM a_different_table'
    queryMock.mockResolvedValueOnce({ rows: driftedRows })

    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest,
      manifest_sha256: canonicalManifestDigest(manifest),
    })).rejects.toThrow(/live registry contract/i)
    expect(queryMock).toHaveBeenCalledTimes(1)
  })

  it('records evidence idempotently within its campaign definition revision', async () => {
    queryMock.mockResolvedValue({ rowCount: 1, rows: [] })
    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
      event_type: 'integrity_verified',
      entity_type: 'asset',
      entity_id: 'bg_prashna_rules',
      layer: 'L0',
      evidence_payload: { receipt: 'test' },
      source_kind: 'test',
      source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z',
      recorded_by: 'admin-1',
    })).resolves.toBe('created')

    expect(queryMock.mock.calls[0][0]).toContain('ON CONFLICT (campaign_id, definition_revision, idempotency_key) DO NOTHING')
  })

  it('rejects a reused evidence idempotency key whose immutable receipt differs', async () => {
    queryMock
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
        event_type: 'integrity_verified', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { receipt: 'first' }, source_kind: 'test', source_ref: 'test:receipt',
        observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
      }] })

    await expect(recordNirmanaElevationEvidence({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
      event_type: 'integrity_verified', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { receipt: 'second' }, source_kind: 'test', source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    })).rejects.toThrow(/idempotency key/i)
  })

  it('accepts an exact retried evidence receipt without overwriting the original actor', async () => {
    const input = {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', idempotency_key: 'asset:bg_prashna_rules:integrity:v1',
      event_type: 'integrity_verified', entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
      evidence_payload: { receipt: 'first' }, source_kind: 'test', source_ref: 'test:receipt',
      observed_at: '2026-08-25T09:00:00.000Z', recorded_by: 'admin-1',
    }
    queryMock
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [input] })
    await expect(recordNirmanaElevationEvidence(input)).resolves.toBe('idempotent')
  })
})
