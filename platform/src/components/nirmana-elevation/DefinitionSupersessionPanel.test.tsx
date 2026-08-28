import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { planAdaptationSnapshot } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
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
    supersession_eligible: true,
    supersession_blockers: [],
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
  it('renders only an evidence-bound candidate when the server-derived eligibility contract permits it', () => {
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
    unavailable.program_sync = { ...unavailable.program_sync, supersession_eligible: false, supersession_blockers: ['runtime_not_quiet'] }
    rerender(<DefinitionSupersessionPanel snapshot={unavailable} />)
    expect(screen.queryByRole('button', { name: 'Supersede definition' })).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(/monitored runtime is not quiet/i)

    const candidateChangedOnServer = supersessionSnapshot()
    candidateChangedOnServer.program_sync = { ...candidateChangedOnServer.program_sync, supersession_eligible: false, supersession_blockers: ['candidate_mismatch'] }
    rerender(<DefinitionSupersessionPanel snapshot={candidateChangedOnServer} />)
    expect(screen.queryByRole('button', { name: 'Supersede definition' })).not.toBeInTheDocument()
  })

  it('posts only the strict candidate-bound supersession command after confirmation', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const onRefresh = vi.fn().mockResolvedValue(true)
    render(<DefinitionSupersessionPanel snapshot={supersessionSnapshot()} onRefresh={onRefresh} />)

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
    await waitFor(() => expect(onRefresh).toHaveBeenCalledTimes(1))
    expect(screen.getByRole('status')).toHaveTextContent(/definition superseded/i)
  })

  it('latches a 409 refusal and refreshes before allowing another request', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ error: `Candidate ${'f'.repeat(64)} changed at postgresql${'://private-host'}` }, 409)))
    const onRefresh = vi.fn().mockResolvedValue(true)

    const { rerender } = render(<DefinitionSupersessionPanel snapshot={supersessionSnapshot()} onRefresh={onRefresh} />)
    fireEvent.click(screen.getByRole('button', { name: 'Supersede definition' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/safely refused this proposal/i)
    expect(onRefresh).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: 'Supersede definition' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Supersede definition' }))
    expect(fetch).toHaveBeenCalledTimes(1)
    const changedIdentity = supersessionSnapshot()
    changedIdentity.program_sync = {
      ...changedIdentity.program_sync,
      candidate_definition_sha256: '9'.repeat(64),
    }
    rerender(<DefinitionSupersessionPanel snapshot={changedIdentity} onRefresh={onRefresh} />)
    expect(screen.getByRole('button', { name: 'Supersede definition' })).toBeEnabled()
    expect(document.body).not.toHaveTextContent('private-host')
    expect(document.body).not.toHaveTextContent('f'.repeat(64))
  })

  it('treats a malformed success response as indeterminate and locks the candidate', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ outcome: 'created' }, 200)))
    const onRefresh = vi.fn().mockResolvedValue(true)

    render(<DefinitionSupersessionPanel snapshot={supersessionSnapshot()} onRefresh={onRefresh} />)
    fireEvent.click(screen.getByRole('button', { name: 'Supersede definition' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/not a definitive supersession outcome/i)
    expect(onRefresh).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: 'Supersede definition' })).toBeDisabled()
  })

  it('never sends a duplicate request while the first request is pending', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise<Response>(() => {})))

    render(<DefinitionSupersessionPanel snapshot={supersessionSnapshot()} />)
    const button = screen.getByRole('button', { name: 'Supersede definition' })
    fireEvent.click(button)
    fireEvent.click(button)

    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
