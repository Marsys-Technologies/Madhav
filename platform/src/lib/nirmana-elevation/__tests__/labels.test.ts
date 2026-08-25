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
      .mockResolvedValueOnce({
        rowCount: 1,
        rows: [{ definition_status: 'frozen', manifest: { assets: [{ asset_id: 'ka_smriti' }] } }],
      })
      .mockResolvedValueOnce({ rowCount: 1 })
      .mockResolvedValueOnce({ rowCount: 1 })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .resolves.toBe('created')
    expect(clientQuery).toHaveBeenNthCalledWith(1, 'BEGIN')
    expect(clientQuery).toHaveBeenLastCalledWith('COMMIT')
    expect(release).toHaveBeenCalledOnce()
  })

  it('rolls back a revision that conflicts with an existing receipt', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({
        rowCount: 1,
        rows: [{ definition_status: 'frozen', manifest: { assets: [{ asset_id: 'ka_smriti' }] } }],
      })
      .mockResolvedValueOnce({ rowCount: 0 })
      .mockResolvedValueOnce({ rowCount: 0 })
      .mockResolvedValueOnce({ rows: [{ label_count: 2, digest_matches: false }] })
      .mockResolvedValueOnce({ rows: [{ evidence_payload: { catalogue_sha256: 'f'.repeat(64), asset_count: 2 } }] })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .rejects.toThrow('Label catalogue revision conflicts with an existing receipt.')
    expect(clientQuery).toHaveBeenLastCalledWith('ROLLBACK')
    expect(release).toHaveBeenCalledOnce()
  })

  it('rolls back labels absent from the frozen definition manifest', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce({ rowCount: 1, rows: [{ definition_status: 'frozen', manifest: { assets: [] } }] })
      .mockResolvedValueOnce(undefined)

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .rejects.toThrow('Label catalogue contains an asset absent from the frozen definition.')
    expect(clientQuery).toHaveBeenLastCalledWith('ROLLBACK')
    expect(release).toHaveBeenCalledOnce()
  })
})
