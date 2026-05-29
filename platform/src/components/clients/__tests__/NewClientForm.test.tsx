/**
 * NewClientForm.test.tsx — B-11 gate tests
 *
 * Covers:
 *  - All required fields rendered
 *  - Ayanamsha checkboxes all checked by default
 *  - Individual ayanamsha unchecking
 *  - At-least-one ayanamsha validation
 *  - Name required validation
 *  - Birth date future-date validation
 *  - Submit calls /api/clients/create with correct payload
 *  - Loading state during submission
 *  - Success redirect to redirect_url
 *  - API error message display
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NewClientForm, AYANAMSHA_OPTIONS } from '../NewClientForm'

// ─── Mock next/navigation ────────────────────────────────────────────────────

const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// ─── Helpers ─────────────────────────────────────────────────────────────────

function renderForm() {
  return render(<NewClientForm />)
}

/** Fill in the minimum valid form values */
async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/full name/i), 'Test Native')
  await user.selectOptions(screen.getByLabelText(/gender/i), 'male')
  await user.type(screen.getByLabelText(/birth date/i), '1990-01-01')
  await user.type(screen.getByLabelText(/birth time/i), '10:30')
  await user.type(screen.getByLabelText(/birth place/i), 'Bhubaneswar, India')
  await user.type(screen.getByLabelText(/latitude/i), '20.2960')
  await user.type(screen.getByLabelText(/longitude/i), '85.8246')
  await user.type(screen.getByLabelText(/timezone offset/i), '5.5')
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('NewClientForm', () => {

  beforeEach(() => {
    mockPush.mockReset()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ── 1. Renders all required fields ────────────────────────────────────────

  it('renders the Full Name field', () => {
    renderForm()
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
  })

  it('renders the Gender select', () => {
    renderForm()
    expect(screen.getByLabelText(/gender/i)).toBeInTheDocument()
  })

  it('renders the Birth Date field', () => {
    renderForm()
    expect(screen.getByLabelText(/birth date/i)).toBeInTheDocument()
  })

  it('renders the Birth Time field', () => {
    renderForm()
    expect(screen.getByLabelText(/birth time/i)).toBeInTheDocument()
  })

  it('renders the Birth Place field', () => {
    renderForm()
    expect(screen.getByLabelText(/birth place/i)).toBeInTheDocument()
  })

  it('renders the Latitude field', () => {
    renderForm()
    expect(screen.getByLabelText(/latitude/i)).toBeInTheDocument()
  })

  it('renders the Longitude field', () => {
    renderForm()
    expect(screen.getByLabelText(/longitude/i)).toBeInTheDocument()
  })

  it('renders the Timezone Offset field', () => {
    renderForm()
    expect(screen.getByLabelText(/timezone offset/i)).toBeInTheDocument()
  })

  it('renders the submit button with correct label', () => {
    renderForm()
    expect(screen.getByRole('button', { name: /create chart & start build/i })).toBeInTheDocument()
  })

  // ── 2. Ayanamsha checkboxes all checked by default ───────────────────────

  it('renders all 5 ayanamsha checkboxes', () => {
    renderForm()
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(AYANAMSHA_OPTIONS.length)
  })

  it('all ayanamsha checkboxes are checked by default', () => {
    renderForm()
    const checkboxes = screen.getAllByRole('checkbox')
    for (const cb of checkboxes) {
      expect(cb).toBeChecked()
    }
  })

  it('renders Lahiri checkbox label', () => {
    renderForm()
    expect(screen.getByRole('checkbox', { name: /lahiri/i })).toBeInTheDocument()
  })

  it('renders KP checkbox label', () => {
    renderForm()
    expect(screen.getByRole('checkbox', { name: /kp/i })).toBeInTheDocument()
  })

  // ── 3. Can uncheck individual ayanamsha ───────────────────────────────────

  it('can uncheck an individual ayanamsha checkbox', async () => {
    const user = userEvent.setup()
    renderForm()
    const lahiriCb = screen.getByRole('checkbox', { name: /lahiri/i })
    expect(lahiriCb).toBeChecked()
    await user.click(lahiriCb)
    expect(lahiriCb).not.toBeChecked()
  })

  it('unchecking one leaves others still checked', async () => {
    const user = userEvent.setup()
    renderForm()
    const lahiriCb = screen.getByRole('checkbox', { name: /lahiri/i })
    await user.click(lahiriCb)
    const remaining = screen.getAllByRole('checkbox').filter((cb) => cb !== lahiriCb)
    for (const cb of remaining) {
      expect(cb).toBeChecked()
    }
  })

  // ── 4. Cannot uncheck all ayanamshas (at-least-one validation) ───────────

  it('shows ayanamsha validation error when all unchecked and form submitted', async () => {
    const user = userEvent.setup()
    renderForm()
    // Uncheck all
    const checkboxes = screen.getAllByRole('checkbox')
    for (const cb of checkboxes) {
      await user.click(cb)
    }
    const submitBtn = screen.getByRole('button', { name: /create chart & start build/i })
    await user.click(submitBtn)
    expect(await screen.findByText(/at least one ayanamsha must be selected/i)).toBeInTheDocument()
  })

  // ── 5. Name field shows validation error when empty ───────────────────────

  it('shows required error for Full Name when empty on submit', async () => {
    const user = userEvent.setup()
    renderForm()
    await user.click(screen.getByRole('button', { name: /create chart & start build/i }))
    expect(await screen.findByText(/full name is required/i)).toBeInTheDocument()
  })

  // ── 6. Birth date validates — rejects future dates ────────────────────────

  it('shows error when birth date is in the future', async () => {
    const user = userEvent.setup()
    renderForm()
    const futureDateInput = screen.getByLabelText(/birth date/i)
    // Set to a far-future date via fireEvent (userEvent type on date input is tricky)
    fireEvent.change(futureDateInput, { target: { value: '2099-12-31' } })
    await user.click(screen.getByRole('button', { name: /create chart & start build/i }))
    expect(await screen.findByText(/birth date cannot be in the future/i)).toBeInTheDocument()
  })

  // ── 7. Submit calls /api/clients/create with correct payload ──────────────

  it('calls /api/clients/create with the correct payload on valid submit', async () => {
    const user = userEvent.setup()
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ id: 'abc123', redirect_url: '/clients/abc123/build' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )
    renderForm()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: /create chart & start build/i }))

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledOnce()
    })

    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/clients/create')
    expect(init.method).toBe('POST')

    const body = JSON.parse(init.body as string)
    expect(body.full_name).toBe('Test Native')
    expect(body.gender).toBe('male')
    expect(body.birth_date).toBe('1990-01-01')
    expect(body.birth_time).toBe('10:30')
    expect(body.ayanamshas).toEqual(AYANAMSHA_OPTIONS.map((o) => o.id))
  })

  // ── 8. Loading state shown during submission ──────────────────────────────

  it('shows loading label on button while request is in flight', async () => {
    const user = userEvent.setup()
    let resolveRequest!: (v: Response) => void
    vi.spyOn(globalThis, 'fetch').mockReturnValueOnce(
      new Promise<Response>((res) => { resolveRequest = res })
    )
    renderForm()
    await fillValidForm(user)

    await act(async () => {
      await user.click(screen.getByRole('button', { name: /create chart & start build/i }))
    })

    expect(screen.getByRole('button', { name: /creating chart/i })).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()

    // Resolve so the test cleans up
    resolveRequest(
      new Response(JSON.stringify({ id: 'x', redirect_url: '/clients/x/build' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  // ── 9. Success redirects to redirect_url ──────────────────────────────────

  it('redirects to redirect_url from API response on success', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(
        JSON.stringify({ id: 'client-42', redirect_url: '/clients/client-42/build' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    )
    renderForm()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: /create chart & start build/i }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/clients/client-42/build')
    })
  })

  // ── 10. API error message is displayed ────────────────────────────────────

  it('displays API error message when server returns an error', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(
        JSON.stringify({ error: 'Duplicate client record' }),
        { status: 422, headers: { 'Content-Type': 'application/json' } }
      )
    )
    renderForm()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: /create chart & start build/i }))

    expect(await screen.findByText(/duplicate client record/i)).toBeInTheDocument()
  })

  it('displays fallback error message when API returns no error field', async () => {
    const user = userEvent.setup()
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({}), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      })
    )
    renderForm()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: /create chart & start build/i }))

    expect(await screen.findByText(/failed to create client/i)).toBeInTheDocument()
  })
})
