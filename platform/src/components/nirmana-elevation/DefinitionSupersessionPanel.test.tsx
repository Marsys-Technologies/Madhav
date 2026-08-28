import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fixtureV2, planAdaptationSnapshot } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { DefinitionSupersessionPanel } from './DefinitionSupersessionPanel'

const observationId = '55555555-5555-4555-8555-555555555555'
const currentDigest = 'c'.repeat(64)
const candidateDigest = 'd'.repeat(64)
const catalogueDigest = 'e'.repeat(64)

function supersessionSnapshot(): NirmanaElevationSnapshotV2 {
  const snapshot = structuredClone(planAdaptationSnapshot) as unknown as NirmanaElevationSnapshotV2
  snapshot.campaign.definition_revision = 'v1'
  snapshot.campaign.definition_status = 'frozen'
  snapshot.program_sync = {
    status: 'plan_adaptation_required',
    source_observation_id: observationId,
    observed_at: '2026-08-27T05:00:00.000Z',
    age_seconds: 120,
    affected_asset_ids: ['bg_prashna_rules'],
    current_definition_sha256: currentDigest,
    candidate_definition_sha256: candidateDigest,
    candidate_catalogue_sha256: catalogueDigest,
  }
  snapshot.active_runs = []
  snapshot.audit = { receipts: [], raw_ledger_refs: [] }
  snapshot.release = {
    ...snapshot.release,
    production_in_sync: true,
  }
  for (const source of snapshot.sources) {
    Object.assign(source, {
      state: 'fresh', observed_at: '2026-08-27T05:00:00.000Z', age_seconds: 120,
      error_code: null, error_message: null,
    })
  }
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

describe('DefinitionSupersessionPanel', () => {
  it('renders only an evidence-bound, unused, fresh plan-adaptation candidate', () => {
    const snapshot = supersessionSnapshot()
    const { rerender } = render(<DefinitionSupersessionPanel snapshot={snapshot} />)

    expect(screen.getByRole('heading', { name: 'Supersede the frozen definition' })).toBeVisible()
    expect(screen.getByText((content) => content.startsWith(observationId))).toBeVisible()
    expect(screen.getByText(currentDigest)).toBeVisible()
    expect(screen.getByText(candidateDigest)).toBeVisible()
    expect(screen.getByText(catalogueDigest)).toBeVisible()
    expect(screen.getByText(`ntap-20260827-${observationId}`)).toBeVisible()
    expect(screen.getByText(/never submits a caller-provided manifest/i)).toBeVisible()

    const unavailable = supersessionSnapshot()
    unavailable.sources.find((source) => source.source_id === 'program_monitor')!.state = 'unavailable'
    rerender(<DefinitionSupersessionPanel snapshot={unavailable} />)
    expect(screen.queryByRole('button', { name: 'Supersede definition' })).not.toBeInTheDocument()

    const hasReceipts = supersessionSnapshot()
    hasReceipts.audit = structuredClone(fixtureV2.audit)
    rerender(<DefinitionSupersessionPanel snapshot={hasReceipts} />)
    expect(screen.queryByRole('button', { name: 'Supersede definition' })).not.toBeInTheDocument()

    const active = supersessionSnapshot()
    active.active_runs = structuredClone(fixtureV2.active_runs)
    rerender(<DefinitionSupersessionPanel snapshot={active} />)
    expect(screen.queryByRole('button', { name: 'Supersede definition' })).not.toBeInTheDocument()

    const outOfSync = supersessionSnapshot()
    outOfSync.release.production_in_sync = false
    rerender(<DefinitionSupersessionPanel snapshot={outOfSync} />)
    expect(screen.queryByRole('button', { name: 'Supersede definition' })).not.toBeInTheDocument()
  })

  it('posts only the strict candidate-bound supersession command after confirmation', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const onSuperseded = vi.fn().mockResolvedValue(true)
    render(<DefinitionSupersessionPanel snapshot={supersessionSnapshot()} onSuperseded={onSuperseded} />)

    fireEvent.click(screen.getByRole('button', { name: 'Supersede definition' }))
    expect(confirm).toHaveBeenCalledWith(expect.stringMatching(/governed plan replacement.*not permission to start or resume/i))
    expect(fetch).not.toHaveBeenCalled()

    confirm.mockReturnValue(true)
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ outcome: 'superseded' }, 201))
    fireEvent.click(screen.getByRole('button', { name: 'Supersede definition' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    const [, requestInit] = vi.mocked(fetch).mock.calls[0]
    expect(JSON.parse(String(requestInit?.body))).toEqual({
      command: 'supersede_definition',
      campaign_id: 'nirmana-elevation',
      expected_current_revision: 'v1',
      expected_current_manifest_sha256: currentDigest,
      source_observation_id: observationId,
      expected_candidate_sha256: candidateDigest,
      expected_candidate_catalogue_sha256: catalogueDigest,
      new_definition_revision: `ntap-20260827-${observationId}`,
    })
    expect(JSON.parse(String(requestInit?.body))).not.toHaveProperty('manifest')
    await waitFor(() => expect(onSuperseded).toHaveBeenCalledTimes(1))
    expect(screen.getByRole('status')).toHaveTextContent(/definition superseded/i)
  })

  it('fails closed with bounded copy when the server rejects a stale candidate', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ error: `Candidate ${'f'.repeat(64)} changed at postgresql${'://private-host'}` }, 409)))

    render(<DefinitionSupersessionPanel snapshot={supersessionSnapshot()} />)
    fireEvent.click(screen.getByRole('button', { name: 'Supersede definition' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/no longer meets the supersession safeguards/i)
    expect(document.body).not.toHaveTextContent('private-host')
    expect(document.body).not.toHaveTextContent('f'.repeat(64))
  })
})
