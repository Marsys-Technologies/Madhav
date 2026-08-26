// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const clientQuery = vi.fn()
const release = vi.fn()
vi.mock('@/lib/db/client', () => ({
  getPool: async () => ({ connect: async () => ({ query: clientQuery, release }) }),
}))

import {
  canonicalLabelCatalogueDigest,
  recordNirmanaElevationLabelCatalogue,
} from '../labels'

const input = {
  campaign_id: 'nirmana-elevation' as const,
  definition_revision: 'r1',
  catalogue_revision: 'labels-v1',
  labels: [{
    asset_id: 'ka_smriti',
    sanskrit_name: 'Kala Smriti',
    english_name: 'Per-varsha digest',
    description: 'Produces a year-by-year digest of annual chart features.',
    legacy_aliases: [{ asset_id: 'A22', sanskrit_name: 'Varsha-Darshan', english_name: 'Yearly Vision' }],
    source_ref: 'PARIKSHA/ASSET_REGISTRY.md#kala-smriti',
  }],
  catalogue_sha256: '',
  recorded_by: 'admin-1',
}

describe('Nirmana label catalogue', () => {
  beforeEach(() => { clientQuery.mockReset(); release.mockReset() })

  it('has an order-independent canonical digest', () => {
    const second = { ...input.labels[0], asset_id: 'sphurana', legacy_aliases: [] }
    expect(canonicalLabelCatalogueDigest([input.labels[0], second]))
      .toBe(canonicalLabelCatalogueDigest([second, input.labels[0]]))
  })

  it('records labels and the acceptance receipt in one transaction', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({
        rowCount: 1,
        rows: [{ definition_status: 'frozen', manifest: { assets: [{ asset_id: 'ka_smriti' }] } }],
      })
      .mockResolvedValueOnce({ rowCount: 0, rows: [] })
      .mockResolvedValueOnce({ rows: [{ label_count: 0, digest_matches: false }] })
      .mockResolvedValueOnce({ rowCount: 1 })
      .mockResolvedValueOnce({ rowCount: 1 })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .resolves.toBe('created')
    expect(clientQuery).toHaveBeenNthCalledWith(1, 'BEGIN')
    expect(clientQuery).toHaveBeenNthCalledWith(2,
      'SELECT pg_advisory_xact_lock(hashtextextended($1, 0))',
      ['nirmana-elevation:r1:labels-v1'])
    expect(clientQuery).toHaveBeenLastCalledWith('COMMIT')
    expect(release).toHaveBeenCalledOnce()
  })

  it('treats a sequential retry with the same revision digest and count as idempotent', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({
        rowCount: 1,
        rows: [{ definition_status: 'frozen', manifest: { assets: [{ asset_id: 'ka_smriti' }] } }],
      })
      .mockResolvedValueOnce({ rows: [{ evidence_payload: { catalogue_sha256: digest, asset_count: 1 } }] })
      .mockResolvedValueOnce({ rows: [{ label_count: 1, digest_matches: true }] })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .resolves.toBe('idempotent')
    expect(clientQuery.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_asset_labels'))).toBe(false)
    expect(clientQuery).toHaveBeenLastCalledWith('COMMIT')
    expect(release).toHaveBeenCalledOnce()
  })

  it('takes a revision transaction lock before rejecting a concurrent-shape digest conflict without inserts', async () => {
    const secondLabel = { ...input.labels[0], asset_id: 'sphurana', legacy_aliases: [] }
    const digest = canonicalLabelCatalogueDigest([secondLabel])
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({
        rowCount: 1,
        rows: [{ definition_status: 'frozen', manifest: { assets: [{ asset_id: 'sphurana' }] } }],
      })
      .mockResolvedValueOnce({ rows: [{ evidence_payload: { catalogue_sha256: canonicalLabelCatalogueDigest(input.labels), asset_count: 1 } }] })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, labels: [secondLabel], catalogue_sha256: digest }))
      .rejects.toThrow('Label catalogue revision conflicts with an existing receipt.')
    expect(clientQuery).toHaveBeenNthCalledWith(2,
      'SELECT pg_advisory_xact_lock(hashtextextended($1, 0))',
      ['nirmana-elevation:r1:labels-v1'])
    expect(clientQuery.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_asset_labels'))).toBe(false)
    expect(clientQuery.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(false)
    expect(clientQuery).toHaveBeenLastCalledWith('ROLLBACK')
  })

  it('rejects a same-digest revision receipt with a different asset count before either insert', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({
        rowCount: 1,
        rows: [{ definition_status: 'frozen', manifest: { assets: [{ asset_id: 'ka_smriti' }] } }],
      })
      .mockResolvedValueOnce({ rows: [{ evidence_payload: { catalogue_sha256: digest, asset_count: 2 } }] })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .rejects.toThrow('Label catalogue revision conflicts with an existing receipt.')
    expect(clientQuery).toHaveBeenNthCalledWith(4, expect.stringContaining('FROM nirmana_elevation_campaign_events'), [
      'nirmana-elevation', 'r1', 'asset-label-catalogue:labels-v1',
    ])
    expect(clientQuery.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_asset_labels'))).toBe(false)
    expect(clientQuery.mock.calls.some(([sql]) => String(sql).includes('INSERT INTO nirmana_elevation_campaign_events'))).toBe(false)
    expect(clientQuery).toHaveBeenLastCalledWith('ROLLBACK')
    expect(release).toHaveBeenCalledOnce()
  })

  it('rolls back labels absent from the frozen definition manifest', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_status: 'frozen', manifest: { assets: [] } }] })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .rejects.toThrow('Label catalogue contains an asset absent from the frozen definition.')
    expect(clientQuery).toHaveBeenLastCalledWith('ROLLBACK')
    expect(release).toHaveBeenCalledOnce()
  })
})
