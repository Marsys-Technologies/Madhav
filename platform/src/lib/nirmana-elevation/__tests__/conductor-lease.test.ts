import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const queryMock = vi.fn()
const releaseMock = vi.fn()
const connectMock = vi.fn()
vi.mock('../campaign-control-writer', () => ({
  getNirmanaCampaignControlWriterPool: async () => ({ connect: (...args: unknown[]) => connectMock(...args) }),
}))

import { acquireNirmanaConductorLease, NIRMANA_CONDUCTOR_PRINCIPAL } from '../conductor'

describe('Nirmana conductor lease', () => {
  beforeEach(() => {
    queryMock.mockReset()
    releaseMock.mockReset()
    connectMock.mockReset().mockResolvedValue({ query: queryMock, release: releaseMock })
  })

  it('acquires a new monotonically fenced lease under a transaction advisory lock', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] }) // BEGIN
      .mockResolvedValueOnce({ rows: [] }) // advisory lock
      .mockResolvedValueOnce({ rows: [{ status: 'enabled', max_layer: 'L0', expires_at: '2030-01-01T00:00:00.000Z', allowed_actions: [] }] })
      .mockResolvedValueOnce({ rows: [] }) // previous lease
      .mockResolvedValueOnce({ rows: [{ lease_id: '11111111-1111-4111-8111-111111111111', fence: 1, expires_at: '2030-01-01T00:15:00.000Z' }] })
      .mockResolvedValueOnce({ rows: [] }) // COMMIT

    await expect(acquireNirmanaConductorLease(NIRMANA_CONDUCTOR_PRINCIPAL)).resolves.toMatchObject({ fence: 1 })

    expect(String(queryMock.mock.calls[1]?.[0])).toContain('pg_advisory_xact_lock')
    expect(String(queryMock.mock.calls[4]?.[0])).toContain('INSERT INTO nirmana_evidence.nirmana_elevation_conductor_leases')
    expect(queryMock.mock.calls[4]?.[1]).toEqual([NIRMANA_CONDUCTOR_PRINCIPAL, 1, 'T0,F0,L0'])
    expect(releaseMock).toHaveBeenCalledOnce()
  })

  it('rejects the monitor identity before it opens a database connection', async () => {
    await expect(acquireNirmanaConductorLease('amjis-nirmana-monitor@madhav-astrology.iam.gserviceaccount.com'))
      .rejects.toThrow(/dedicated Nirmana conductor/)
    expect(connectMock).not.toHaveBeenCalled()
  })
})
