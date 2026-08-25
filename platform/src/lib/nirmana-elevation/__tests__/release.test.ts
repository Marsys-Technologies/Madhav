import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import { loadNirmanaReleaseStatus } from '../release'

const observedAt = new Date('2026-08-25T09:00:00.000Z')

function cloudRun({
  traffic = [{ percent: 100, revision: 'projects/madhav-astrology/locations/asia-south1/revisions/amjis-web-01704-mvb' }],
  templateLabels,
  revisionLabels,
}: {
  traffic?: Array<{ percent?: number; revision?: string }>
  templateLabels?: Record<string, string>
  revisionLabels?: Record<string, string>
} = {}) {
  return {
    getService: vi.fn().mockResolvedValue([{ traffic, template: { labels: templateLabels } }]),
    getRevision: vi.fn().mockResolvedValue([{ labels: revisionLabels }]),
  }
}

describe('loadNirmanaReleaseStatus', () => {
  beforeEach(() => vi.restoreAllMocks())
  afterEach(() => vi.useRealTimers())

  it('reports independent main and serving-revision observations while withholding a commit-unproven sync verdict', async () => {
    const result = await loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ sha: 'a'.repeat(40) }), { status: 200 })),
      cloudRunClient: cloudRun() as never,
    })

    expect(result.release).toEqual({
      main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01704-mvb',
      production_in_sync: null, observed_at: observedAt.toISOString(),
    })
    expect(result.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({ source_id: 'github_main', state: 'fresh' }),
      expect.objectContaining({ source_id: 'cloud_run_web', state: 'fresh' }),
      expect.objectContaining({ source_id: 'artifact_registry_commit', state: 'unknown' }),
    ]))
    expect(result.gaps).toContain('Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.')
  })

  it('isolates unavailable GitHub observations without inventing a main SHA', async () => {
    const result = await loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue(new Response(null, { status: 503 })),
      cloudRunClient: cloudRun() as never,
    })

    expect(result.release).toMatchObject({ main_sha: null, deployed_revision: 'amjis-web-01704-mvb', production_in_sync: null })
    expect(result.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'github_main', state: 'unavailable' })]))
    expect(result.gaps).toContain('Authoritative GitHub main revision is unavailable; release sync is withheld.')
  })

  it('isolates unavailable Cloud Run observations without inventing a serving revision', async () => {
    const unavailableCloudRun = { getService: vi.fn().mockRejectedValue(new Error('ADC unavailable')) }
    const result = await loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ sha: 'b'.repeat(40) }), { status: 200 })),
      cloudRunClient: unavailableCloudRun as never,
    })

    expect(result.release).toMatchObject({ main_sha: 'b'.repeat(40), deployed_revision: null, production_in_sync: null })
    expect(result.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'cloud_run_web', state: 'unavailable' })]))
    expect(result.gaps).toContain('Authoritative Cloud Run serving revision is unavailable; release sync is withheld.')
  })

  it('treats split serving traffic as unavailable instead of choosing a revision arbitrarily', async () => {
    const result = await loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ sha: 'c'.repeat(40) }), { status: 200 })),
      cloudRunClient: cloudRun({ traffic: [
        { percent: 50, revision: 'projects/madhav-astrology/locations/asia-south1/revisions/amjis-web-old' },
        { percent: 50, revision: 'projects/madhav-astrology/locations/asia-south1/revisions/amjis-web-new' },
      ] }) as never,
    })

    expect(result.release).toMatchObject({ deployed_revision: null, production_in_sync: null })
    expect(result.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'cloud_run_web', state: 'unavailable' })]))
  })

  it('uses a valid commit label from the exact serving revision', async () => {
    const result = await loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ sha: 'd'.repeat(40) }), { status: 200 })),
      cloudRunClient: cloudRun({ revisionLabels: { 'commit-sha': 'd'.repeat(40) } }) as never,
    })

    expect(result.release).toMatchObject({ deployed_sha: 'd'.repeat(40), production_in_sync: true })
    expect(result.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({ source_id: 'artifact_registry_commit', state: 'fresh', error: null }),
    ]))
    expect(result.gaps).not.toContain('Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.')
  })

  it('withholds a desired-template commit label when the serving revision has no provenance', async () => {
    const result = await loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue(new Response(JSON.stringify({ sha: 'e'.repeat(40) }), { status: 200 })),
      cloudRunClient: cloudRun({
        templateLabels: { 'commit-sha': 'e'.repeat(40) },
      }) as never,
    })

    expect(result.release).toMatchObject({ deployed_sha: null, production_in_sync: null })
  })

  it('times out a stalled release source and returns a degraded observation', async () => {
    vi.useFakeTimers()
    const stalledFetch = vi.fn(() => new Promise<Response>(() => {}))
    const resultPromise = loadNirmanaReleaseStatus({ now: observedAt, fetchFn: stalledFetch, cloudRunClient: cloudRun() as never })

    await vi.advanceTimersByTimeAsync(5_000)
    const result = await resultPromise

    expect(result.release).toMatchObject({ main_sha: null, deployed_revision: 'amjis-web-01704-mvb', production_in_sync: null })
    expect(result.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'github_main', state: 'unavailable', error: expect.stringContaining('timed out') })]))
  })

  it('times out a stalled GitHub response body after headers arrive', async () => {
    vi.useFakeTimers()
    const resultPromise = loadNirmanaReleaseStatus({
      now: observedAt,
      fetchFn: vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => new Promise(() => {}) } as unknown as Response),
      cloudRunClient: cloudRun() as never,
    })

    await vi.advanceTimersByTimeAsync(5_000)
    const result = await resultPromise

    expect(result.release.main_sha).toBeNull()
    expect(result.sources).toEqual(expect.arrayContaining([expect.objectContaining({ source_id: 'github_main', state: 'unavailable', error: expect.stringContaining('timed out') })]))
  })
})
