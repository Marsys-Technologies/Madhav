import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { BaselineAcceptancePanel } from './BaselineAcceptancePanel'

const observationId = '77777777-7777-4777-8777-777777777777'
const definitionDigest = 'd'.repeat(64)
const catalogueDigest = 'e'.repeat(64)

function baselineMissingSnapshot(): NirmanaElevationSnapshotV2 {
  const snapshot = structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
  snapshot.campaign.definition_revision = null
  snapshot.campaign.definition_status = 'reconciling'
  snapshot.program_sync = {
    status: 'baseline_missing',
    source_observation_id: observationId,
    observed_at: '2026-08-27T05:00:00.000Z',
    age_seconds: 120,
    affected_asset_ids: [],
    current_definition_sha256: null,
    candidate_definition_sha256: definitionDigest,
    candidate_catalogue_sha256: catalogueDigest,
  }
  const monitor = snapshot.sources.find((source) => source.source_id === 'program_monitor')
  if (!monitor) throw new Error('Fixture must include the program monitor source.')
  Object.assign(monitor, {
    state: 'fresh',
    observed_at: '2026-08-27T05:00:00.000Z',
    age_seconds: 120,
    error_code: null,
    error_message: null,
  })
  return snapshot
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('BaselineAcceptancePanel', () => {
  it('shows only a fresh baseline proposal and summarizes its bounded scope', () => {
    const snapshot = baselineMissingSnapshot()
    const { rerender } = render(<BaselineAcceptancePanel snapshot={snapshot} />)

    expect(screen.getByRole('heading', { name: 'Current baseline proposal' })).toBeVisible()
    expect(screen.getByText(`${snapshot.assets.length} registry assets`)).toBeVisible()
    expect(screen.getByText('27 Aug 2026, 10:30:00')).toBeVisible()
    const candidate = screen.getByText('Candidate:').parentElement
    expect(candidate).toHaveTextContent(`Definition ${definitionDigest.slice(0, 12)}…`)
    expect(candidate).toHaveTextContent(`Labels ${catalogueDigest.slice(0, 12)}…`)
    expect(document.body).not.toHaveTextContent(definitionDigest)
    expect(document.body).not.toHaveTextContent(catalogueDigest)

    const stale = baselineMissingSnapshot()
    const monitor = stale.sources.find((source) => source.source_id === 'program_monitor')!
    monitor.state = 'stale'
    rerender(<BaselineAcceptancePanel snapshot={stale} />)
    expect(screen.queryByRole('button', { name: 'Accept current baseline' })).not.toBeInTheDocument()
    expect(screen.getByText(/acceptance is withheld until the monitor observation.*all tracker sources are fresh/i)).toBeVisible()

    const changed = baselineMissingSnapshot()
    changed.program_sync.status = 'plan_adaptation_required'
    rerender(<BaselineAcceptancePanel snapshot={changed} />)
    expect(screen.queryByRole('button', { name: 'Accept current baseline' })).not.toBeInTheDocument()
  })

  it('posts the exact observed candidate only after explicit local confirmation', async () => {
    const snapshot = baselineMissingSnapshot()
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const onAccepted = vi.fn().mockResolvedValue(true)
    const { rerender } = render(<BaselineAcceptancePanel snapshot={snapshot} onAccepted={onAccepted} />)

    fireEvent.click(screen.getByRole('button', { name: 'Accept current baseline' }))
    expect(confirm).toHaveBeenCalledWith(expect.stringMatching(/does not start or resume campaign work/i))
    expect(fetch).not.toHaveBeenCalled()

    let resolveRequest: (response: Response) => void = () => undefined
    const pending = new Promise<Response>((resolve) => { resolveRequest = resolve })
    confirm.mockReturnValue(true)
    vi.mocked(fetch).mockReturnValueOnce(pending)
    rerender(<BaselineAcceptancePanel snapshot={snapshot} onAccepted={onAccepted} />)

    fireEvent.click(screen.getByRole('button', { name: 'Accept current baseline' }))
    expect(screen.getByRole('button', { name: 'Accepting current baseline' })).toBeDisabled()
    expect(fetchMock).toHaveBeenCalledWith('/api/admin/nirmana-elevation/evidence', expect.objectContaining({
      method: 'POST',
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
    }))
    const [, requestInit] = vi.mocked(fetch).mock.calls[0]
    expect(JSON.parse(String(requestInit?.body))).toEqual({
      command: 'accept_baseline_candidate',
      definition_revision: `ntap-20260827-${observationId}`,
      source_observation_id: observationId,
      expected_candidate_sha256: definitionDigest,
      expected_candidate_catalogue_sha256: catalogueDigest,
    })

    resolveRequest(jsonResponse({ outcome: 'created' }, 201))
    await waitFor(() => expect(onAccepted).toHaveBeenCalledTimes(1))
    expect(screen.getByRole('status')).toHaveTextContent(/baseline accepted/i)
  })

  it('uses bounded recovery copy for a guarded conflict', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({
      error: `Candidate ${'f'.repeat(64)} changed at postgresql${'://private-host'}`,
    }, 409)))

    render(<BaselineAcceptancePanel snapshot={baselineMissingSnapshot()} />)
    fireEvent.click(screen.getByRole('button', { name: 'Accept current baseline' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/proposal changed or another baseline was accepted/i)
    expect(document.body).not.toHaveTextContent('private-host')
    expect(document.body).not.toHaveTextContent('f'.repeat(64))
  })
})
