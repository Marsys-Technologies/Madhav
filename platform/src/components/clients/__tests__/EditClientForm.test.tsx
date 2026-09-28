/**
 * EditClientForm — display-only vs recompute flow (Jātaka chart workspace, Task 7).
 *
 * The client hint only picks copy and whether to confirm; the server decides.
 * The form always PATCHes /api/charts/<id> and returns to the workspace.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'

const { mockPush, mockRefresh } = vi.hoisted(() => ({ mockPush: vi.fn(), mockRefresh: vi.fn() }))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush, refresh: mockRefresh, back: vi.fn() }) }))
vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))

vi.mock('../NewClientForm', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../NewClientForm')>()),
  // Stand-in for the shared Google Places element: one button resolves a place.
  PlacesAutocompleteNew: ({ onPlaceResolved }: { onPlaceResolved: (r: unknown) => void }) => (
    <>
      <button
        type="button"
        onClick={() => onPlaceResolved({ description: 'Cuttack, Odisha, India', lat: 20.4625, lng: 85.883, utcOffsetMinutes: 330, timezone_id: 'Asia/Kolkata', tz_offset: '5.5' })}
      >
        Pick Cuttack
      </button>
      <button
        type="button"
        onClick={() => onPlaceResolved({ description: 'Somewhere', lat: 20.4625, lng: 85.883, utcOffsetMinutes: 330, timezone_id: 'Mars/Olympus_Mons', tz_offset: '5.5' })}
      >
        Pick unknown zone
      </button>
    </>
  ),
}))

import { EditClientForm, type EditableChart } from '../EditClientForm'

const CHART: EditableChart = {
  id: 'c1',
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  timezone_id: 'Asia/Kolkata',
  tz_offset_hours: 5.5,
  ayanamshas: ['lahiri'],
}

const fetchMock = vi.fn()

function respond(status: number, body: unknown) {
  fetchMock.mockResolvedValueOnce({ ok: status >= 200 && status < 300, status, json: async () => body })
}

function sentBody() {
  return JSON.parse(fetchMock.mock.calls[0][1].body as string)
}

beforeEach(() => {
  vi.clearAllMocks()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('EditClientForm — structure', () => {
  it('groups fields into Identity, Birth coordinates, Time standard and Computation frame', () => {
    render(<EditClientForm chart={CHART} />)
    for (const name of ['Identity', 'Birth coordinates', 'Time standard', 'Computation frame']) {
      expect(screen.getByRole('group', { name })).toBeInTheDocument()
    }
  })

  it('shows the effective offset the server will verify', () => {
    render(<EditClientForm chart={CHART} />)
    expect(screen.getByTestId('effective-offset')).toHaveTextContent('UTC+05:30')
  })
})

describe('EditClientForm — display-only edits', () => {
  it('a name-only edit saves directly, with Save changes and no dialog', async () => {
    respond(200, { data: { mode: 'display-only', chartId: 'c1', changedFields: ['name'] } })
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^full name/i), { target: { value: 'Renamed Native' } })
    const submit = screen.getByRole('button', { name: 'Save changes' })
    fireEvent.click(submit)
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/charts/c1')
    expect(fetchMock.mock.calls[0][1].method).toBe('PATCH')
    expect(sentBody()).toMatchObject({ name: 'Renamed Native', birth_time: '10:43', lat: 20.2961, lon: 85.8245, tz_offset: 5.5, ayanamshas: ['lahiri'] })
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/clients/c1'))
  })
})

describe('EditClientForm — computation-affecting edits', () => {
  it.each([
    ['birth date', /^date of birth/i, '1984-02-06'],
    ['birth time', /^time of birth/i, '10:44'],
    ['latitude', /^latitude/i, '20.4625'],
    ['longitude', /^longitude/i, '85.883'],
  ])('a %s change asks to Save and recompute and confirms first', async (_label, field, value) => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(field), { target: { value } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('a timezone change recomputes', async () => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^timezone/i), { target: { value: 'Asia/Dhaka' } })
    expect(screen.getByRole('button', { name: 'Save and recompute' })).toBeInTheDocument()
  })

  it('an ayanāṃśa change recomputes', async () => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    expect(screen.getByRole('button', { name: 'Save and recompute' })).toBeInTheDocument()
  })

  it('the dialog lists each before/after change and the archive notice', async () => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^time of birth/i), { target: { value: '10:44' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    const row = await screen.findByTestId('change-birth_time')
    expect(row).toHaveTextContent('10:43')
    expect(row).toHaveTextContent('10:44')
    expect(screen.getByRole('dialog')).toHaveTextContent(/archived read-only/i)
  })

  it('202 recompute-started returns to the workspace', async () => {
    respond(202, { data: { mode: 'recompute-started', chartId: 'c1', changedFields: ['birth_time'], runId: 'r1' } })
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^time of birth/i), { target: { value: '10:44' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Save and recompute' }))
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/clients/c1'))
    expect(sentBody()).toMatchObject({ birth_time: '10:44' })
  })

  it('503 JOB_DISPATCH_FAILED returns to the workspace in its Needs rebuild state', async () => {
    respond(503, {
      error: 'Chart details were saved, but the rebuild did not start.',
      code: 'JOB_DISPATCH_FAILED',
      data: { mode: 'needs-rebuild', chartId: 'c1', changedFields: ['birth_time'], runId: 'r9', error: 'spawn' },
    })
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^time of birth/i), { target: { value: '10:44' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Save and recompute' }))
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/clients/c1?status=needs-rebuild&run=r9'))
  })

  it('dialog Cancel returns focus to the submit trigger and sends nothing', async () => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^time of birth/i), { target: { value: '10:44' } })
    const submit = screen.getByRole('button', { name: 'Save and recompute' })
    fireEvent.click(submit)
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Cancel' }))
    await waitFor(() => expect(document.activeElement).toBe(submit))
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('EditClientForm — server refusals keep the form', () => {
  it('409 keeps values and announces the build in progress', async () => {
    respond(409, { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE' })
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^full name/i), { target: { value: 'Renamed Native' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/build is in progress/i)
    expect(screen.getByLabelText(/^full name/i)).toHaveValue('Renamed Native')
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('422 maps server field errors onto the matching inputs', async () => {
    respond(422, { error: 'Some chart details are invalid.', code: 'VALIDATION_FAILED', fields: { lat: 'Latitude out of range', tz_offset: 'Offset disagrees' } })
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^full name/i), { target: { value: 'Renamed Native' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByText('Latitude out of range')).toBeInTheDocument()
    expect(screen.getByText('Offset disagrees')).toBeInTheDocument()
    expect(screen.getByLabelText(/^latitude/i)).toHaveAttribute('aria-invalid', 'true')
  })

  it('a chart with no stored timezone requires one before saving', async () => {
    render(<EditClientForm chart={{ ...CHART, timezone_id: null, tz_offset_hours: null }} />)
    expect(screen.getByText(/choose the birth timezone/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('EditClientForm — computation-safe birthplace', () => {
  it('refuses a new place typed without new coordinates, naming what to reselect, and sends nothing', async () => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^birth place/i), { target: { value: 'Cuttack, Odisha' } })
    expect(screen.getByRole('note', { name: /reselect/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    expect(await screen.findByText(/reselect the new place/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^latitude/i)).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText(/^longitude/i)).toHaveAttribute('aria-invalid', 'true')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('accepts a new place entered with its own coordinates', async () => {
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^birth place/i), { target: { value: 'Cuttack, Odisha' } })
    fireEvent.change(screen.getByLabelText(/^latitude/i), { target: { value: '20.4625' } })
    fireEvent.change(screen.getByLabelText(/^longitude/i), { target: { value: '85.883' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
  })

  it('a selected place updates place, coordinates and timezone together', async () => {
    vi.stubEnv('NEXT_PUBLIC_GOOGLE_MAPS_API_KEY', 'test-key')
    respond(202, { data: { mode: 'recompute-started', chartId: 'c1', changedFields: ['birth_place'], runId: 'r2' } })
    render(<EditClientForm chart={{ ...CHART, timezone_id: 'Asia/Dhaka', tz_offset_hours: 6 }} />)
    fireEvent.click(screen.getByRole('button', { name: 'Pick Cuttack' }))
    expect(screen.getByLabelText(/^birth place/i)).toHaveValue('Cuttack, Odisha, India')
    expect(screen.getByLabelText(/^latitude/i)).toHaveValue(20.4625)
    expect(screen.getByLabelText(/^longitude/i)).toHaveValue(85.883)
    expect(screen.getByLabelText(/^timezone/i)).toHaveValue('Asia/Kolkata')
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Save and recompute' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(sentBody()).toMatchObject({ birth_place: 'Cuttack, Odisha, India', lat: 20.4625, lon: 85.883, timezone_id: 'Asia/Kolkata', tz_offset: 5.5 })
    vi.unstubAllEnvs()
  })

  it('a selected place whose timezone is not a known IANA zone leaves the timezone to be chosen', async () => {
    vi.stubEnv('NEXT_PUBLIC_GOOGLE_MAPS_API_KEY', 'test-key')
    render(<EditClientForm chart={CHART} />)
    fireEvent.click(screen.getByRole('button', { name: 'Pick unknown zone' }))
    expect(screen.getByLabelText(/^timezone/i)).toHaveValue('')
    vi.unstubAllEnvs()
  })

  it('shows the server’s birthplace field errors when it refuses the change', async () => {
    respond(422, { error: 'Reselect the new birth place.', code: 'VALIDATION_FAILED', fields: { birth_place: 'Server says reselect the place.', lat: 'Enter the latitude of the new place.' } })
    render(<EditClientForm chart={CHART} />)
    fireEvent.change(screen.getByLabelText(/^full name/i), { target: { value: 'Renamed Native' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByText('Server says reselect the place.')).toBeInTheDocument()
    expect(screen.getByLabelText(/^birth place/i)).toHaveAttribute('aria-invalid', 'true')
  })
})
