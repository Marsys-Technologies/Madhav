import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import {
  canonicalManifestDigest,
  createNirmanaElevationDefinition,
  freezeNirmanaElevationDefinition,
  recordNirmanaElevationEvidence,
} from '../definitions'

const manifest = {
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  assets: [{ asset_id: 'bg_prashna_rules', layer: 'L0', execution_obligation: 'build' }],
}

describe('Nirmana elevation definition repository', () => {
  beforeEach(() => queryMock.mockReset())

  it('derives one canonical SHA-256 digest for the validated manifest', () => {
    expect(canonicalManifestDigest(manifest)).toMatch(/^[a-f0-9]{64}$/)
  })

  it('requires the frozen manifest to pin its campaign chart', () => {
    expect(() => canonicalManifestDigest({ assets: manifest.assets })).toThrow(/chart_id/i)
  })

  it('gives JSONB-equivalent manifests the same digest regardless of object-key order', () => {
    const reordered = {
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      assets: [{ execution_obligation: 'build', layer: 'L0', asset_id: 'bg_prashna_rules' }],
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
    queryMock.mockResolvedValueOnce({ rowCount: 1, rows: [] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256: canonicalManifestDigest(manifest),
    })).resolves.toBe('frozen')

    queryMock
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{ definition_status: 'frozen', manifest_sha256: canonicalManifestDigest(manifest) }] })
    await expect(freezeNirmanaElevationDefinition({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', manifest, manifest_sha256: canonicalManifestDigest(manifest),
    })).resolves.toBe('idempotent')
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
