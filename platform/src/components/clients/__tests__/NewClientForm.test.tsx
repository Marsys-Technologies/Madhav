/**
 * NewClientForm.test.tsx — functional tests for the rebuilt single-state form
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { NewClientForm } from '../NewClientForm'

// ── Router mock ───────────────────────────────────────────────────────────────

const mockPush = vi.fn()
const mockBack = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}))

// ── @react-google-maps/api mock ───────────────────────────────────────────────
// Top-level vi.mock (hoisted). Behaviour is controlled by a mutable object so
// individual tests can set isLoaded=true without re-hoisting a new factory.

const _jsApiLoader = { isLoaded: false, loadError: undefined as Error | undefined }

vi.mock('@react-google-maps/api', () => ({
  useJsApiLoader: () => ({ isLoaded: _jsApiLoader.isLoaded, loadError: _jsApiLoader.loadError }),
}))

// ── fetch mock ────────────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

beforeEach(() => {
  vi.clearAllMocks()
  // Reset Places loader state — keeps existing tests unaffected (no key → plain input shown)
  _jsApiLoader.isLoaded = false
  _jsApiLoader.loadError = undefined
  mockFetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ chart_id: 'chart-123', redirect_url: '/clients/chart-123/build' }),
  })
})

// ── Helper: select gender via the custom combobox ─────────────────────────────

function selectGender(value: 'M' | 'F' | 'O' | 'unknown') {
  const labelMap = { M: /^male$/i, F: /^female$/i, O: /^other$/i, unknown: /prefer not/i }
  // Open the custom dropdown
  fireEvent.click(screen.getByRole('combobox', { name: /gender/i }))
  // Pick the option
  fireEvent.mouseDown(screen.getByRole('option', { name: labelMap[value] }))
}

// ── Helper: fill a valid form ──────────────────────────────────────────────────

function fillValidForm() {
  fireEvent.change(screen.getByLabelText(/full name/i), {
    target: { value: 'Abhisek Mohanty' },
  })
  selectGender('M')
  // Date field uses dd-MMM-yyyy display format
  fireEvent.change(screen.getByLabelText(/^date/i), {
    target: { value: '05-Feb-1984' },
  })
  // "Time (24 h)" — use precise pattern to avoid matching "Timezone"
  fireEvent.change(screen.getByLabelText(/time \(24/i), {
    target: { value: '10:43' },
  })
  fireEvent.change(screen.getByLabelText(/birth place/i), {
    target: { value: 'Bhubaneswar, Odisha, India' },
  })
  fireEvent.change(screen.getByLabelText(/^latitude/i), {
    target: { value: '20.2961' },
  })
  fireEvent.change(screen.getByLabelText(/^longitude/i), {
    target: { value: '85.8245' },
  })
  // tz_offset and timezone_id are derived silently (R5.2) — no UI field to fill
}

// ═════════════════════════════════════════════════════════════════════════════
// Test cases
// ═════════════════════════════════════════════════════════════════════════════

describe('NewClientForm', () => {

  // ── Test 1: form title, ayanamsha section, and footer buttons present ──────
  it('renders title, ayanamsha section, and three footer buttons', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-title').textContent).toContain('Nava Jātaka')
    expect(screen.getByTestId('section-compute')).toBeTruthy()
    // R3.3: footer has 3 buttons, no microcopy testid
    expect(screen.getByRole('button', { name: /build chart/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /save chart/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeTruthy()
  })

  // ── Test 2: exactly ONE full name input ────────────────────────────────────
  it('renders exactly one input with label matching "Full name"', () => {
    render(<NewClientForm />)
    const inputs = screen.getAllByLabelText(/full name/i)
    expect(inputs).toHaveLength(1)
    expect((inputs[0] as HTMLInputElement).type).toBe('text')
  })

  // ── Test 3: valid submit POSTs correct body ─────────────────────────────────
  it('submits correct API body when all fields are valid', async () => {
    render(<NewClientForm />)
    fillValidForm()

    fireEvent.click(screen.getByRole('button', { name: /build chart/i }))

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/clients/create')
    expect(opts.method).toBe('POST')

    const body = JSON.parse(opts.body as string)
    expect(body).toHaveProperty('name', 'Abhisek Mohanty')
    expect(body).toHaveProperty('birth_date', '1984-02-05')
    expect(body).toHaveProperty('birth_time', '10:43')
    expect(body).toHaveProperty('birth_place', 'Bhubaneswar, Odisha, India')
    expect(body).toHaveProperty('lat', 20.2961)
    expect(body).toHaveProperty('lon', 85.8245)
    expect(body).toHaveProperty('tz_offset', 5.5)
    expect(body).toHaveProperty('gender', 'M')
    expect(body).toHaveProperty('ayanamshas')
    expect(Array.isArray(body.ayanamshas)).toBe(true)
    // Must NOT send dead fields
    expect(body).not.toHaveProperty('full_name')
    expect(body).not.toHaveProperty('latitude')
    expect(body).not.toHaveProperty('longitude')
    expect(body).not.toHaveProperty('timezone_offset')
    expect(body).not.toHaveProperty('tier')
    expect(body).not.toHaveProperty('notes')
    expect(body).not.toHaveProperty('year_from')
    expect(body).not.toHaveProperty('year_to')
    expect(body).not.toHaveProperty('verification')
    expect(body).not.toHaveProperty('calendar')
    expect(body).not.toHaveProperty('visibility')
    expect(body).not.toHaveProperty('relationship_type')
    expect(body).not.toHaveProperty('reference_chart_id')
  })

  // ── Test 4: empty full_name → validation error, no POST ───────────────────
  it('shows full_name error and does not POST when full_name is empty', async () => {
    render(<NewClientForm />)
    // fill everything except full_name
    selectGender('M')
    fireEvent.change(screen.getByLabelText(/^date/i), { target: { value: '05-Feb-1984' } })
    fireEvent.change(screen.getByLabelText(/time \(24/i), { target: { value: '10:43' } })
    fireEvent.change(screen.getByLabelText(/birth place/i), { target: { value: 'Bhubaneswar' } })
    fireEvent.change(screen.getByLabelText(/^latitude/i), { target: { value: '20.2961' } })
    fireEvent.change(screen.getByLabelText(/^longitude/i), { target: { value: '85.8245' } })

    fireEvent.click(screen.getByRole('button', { name: /build chart/i }))

    await waitFor(() => {
      const alerts = screen.getAllByRole('alert')
      const msgs = alerts.map((a) => a.textContent).join(' ')
      expect(msgs).toMatch(/full name is required/i)
    })
    expect(mockFetch).not.toHaveBeenCalled()
  })

  // ── Test 5: gender unselected → validation error ───────────────────────────
  it('shows gender error when gender is not selected', async () => {
    render(<NewClientForm />)
    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Test User' } })
    fireEvent.change(screen.getByLabelText(/^date/i), { target: { value: '05-Feb-1984' } })
    fireEvent.change(screen.getByLabelText(/time \(24/i), { target: { value: '10:43' } })
    fireEvent.change(screen.getByLabelText(/birth place/i), { target: { value: 'Bhubaneswar' } })
    fireEvent.change(screen.getByLabelText(/^latitude/i), { target: { value: '20.2961' } })
    fireEvent.change(screen.getByLabelText(/^longitude/i), { target: { value: '85.8245' } })

    // Do NOT select gender — leave it empty
    fireEvent.click(screen.getByRole('button', { name: /build chart/i }))

    await waitFor(() => {
      const alerts = screen.getAllByRole('alert')
      const msgs = alerts.map((a) => a.textContent).join(' ')
      expect(msgs).toMatch(/select a gender/i)
    })
    expect(mockFetch).not.toHaveBeenCalled()
  })

  // ── Test 6: custom gender dropdown renders the correct options ─────────────
  // R3.6: gender is now a custom listbox (no native <select>).
  it('gender custom dropdown exposes M, F, O, unknown options', () => {
    render(<NewClientForm />)
    // Open the combobox
    fireEvent.click(screen.getByRole('combobox', { name: /gender/i }))
    // All four value-bearing options must be present
    expect(screen.getByRole('option', { name: /^male$/i })).toBeTruthy()
    expect(screen.getByRole('option', { name: /^female$/i })).toBeTruthy()
    expect(screen.getByRole('option', { name: /^other$/i })).toBeTruthy()
    expect(screen.getByRole('option', { name: /prefer not/i })).toBeTruthy()
    // Selecting 'Male' closes the dropdown and updates the displayed value
    fireEvent.mouseDown(screen.getByRole('option', { name: /^male$/i }))
    expect(screen.getByRole('combobox', { name: /gender/i }).textContent).toContain('Male')
  })

  // ── Test 7: toggling an ayanamsha checkbox changes the selection ───────────
  // R3.3: footer-microcopy is removed; verify the checkbox state itself.
  it('toggling an ayanamsha checkbox changes the checked state', () => {
    render(<NewClientForm />)
    // Default: Lahiri is checked
    const lahiriCheckbox = screen.getByLabelText('Lahiri') as HTMLInputElement
    expect(lahiriCheckbox.checked).toBe(true)

    // Uncheck Lahiri
    fireEvent.click(lahiriCheckbox.closest('label')!)
    expect(lahiriCheckbox.checked).toBe(false)

    // Re-check
    fireEvent.click(lahiriCheckbox.closest('label')!)
    expect(lahiriCheckbox.checked).toBe(true)
  })

  // ── Test 8: Lat/lng fields always in DOM (R5.4 — blur no longer toggles override) ──
  // R5.3 removed the blur handler that used to call setManualOpen(true). Lat/lng are
  // always rendered (R4.3/R5.4), so clicking elsewhere on the page never shows/hides them.
  it('lat/lng fields are always in the DOM; clicking elsewhere does not toggle override', () => {
    render(<NewClientForm />)
    const accordion = screen.getByTestId('manual-override-accordion')

    // lat/lng always present — no trigger needed
    expect(accordion.querySelector('input#latitude')).toBeTruthy()
    expect(accordion.querySelector('input#longitude')).toBeTruthy()

    // Typing in birth_place and blurring must NOT toggle manualOpen
    const birthPlaceInput = screen.getByLabelText(/birth place/i)
    fireEvent.change(birthPlaceInput, { target: { value: 'Somewhere Unknown' } })
    fireEvent.blur(birthPlaceInput)

    // lat/lng still there (were never hidden, blur did not do anything extra)
    expect(accordion.querySelector('input#latitude')).toBeTruthy()
  })

  // ── Test 8b: R4.3 — lat/lng ALWAYS visible; checkbox controls editability ────
  it('R4.3: lat/lng fields are always in the DOM; checkbox toggles readOnly state', () => {
    render(<NewClientForm />)
    const accordion = screen.getByTestId('manual-override-accordion')

    // In test env (no Maps key) the checkbox is checked (manualOpen=true) by default.
    const checkbox = accordion.querySelector('input[type="checkbox"]') as HTMLInputElement
    expect(checkbox).toBeTruthy()
    expect(checkbox.checked).toBe(true)           // no-key fallback: editable by default

    const latInput = screen.getByLabelText(/^latitude/i) as HTMLInputElement
    expect(latInput).toBeTruthy()                 // always present in DOM
    expect(latInput.readOnly).toBe(false)         // editable when checked

    // Uncheck → fields become read-only but stay in DOM
    fireEvent.click(checkbox.closest('label')!)
    expect(accordion.querySelector('input#latitude')).toBeTruthy()  // still present
    expect((accordion.querySelector('input#latitude') as HTMLInputElement).readOnly).toBe(true)

    // Re-check → editable again
    fireEvent.click(checkbox.closest('label')!)
    expect((accordion.querySelector('input#latitude') as HTMLInputElement).readOnly).toBe(false)
  })

  // ── Test 9b: R5.1 — gmp-select with placePrediction.toPlace() populates lat/lng ──
  // R5.1 fix: PlaceAutocompleteElement fires gmp-select with event.placePrediction
  // (not event.place). The handler calls pp.toPlace() then place.fetchFields().
  // R5.2: Time Zone API is also called after fetchFields; mocked via fetch.
  it('R5.1: gmp-select(placePrediction) triggers fetchFields and writes lat/lng to form state', async () => {
    _jsApiLoader.isLoaded = true

    let capturedEl: HTMLElement | null = null

    const mockFetchFields = vi.fn().mockResolvedValue({})
    const mockPlace = {
      location: { lat: () => 20.2961, lng: () => 85.8245 },
      formattedAddress: 'Bhubaneswar, Odisha, India',
      displayName: 'Bhubaneswar',
      fetchFields: mockFetchFields,
    }
    // R5.1: event carries placePrediction with a toPlace() method
    const mockPlacePrediction = { toPlace: vi.fn().mockReturnValue(mockPlace) }

    vi.stubGlobal('google', {
      maps: {
        importLibrary: vi.fn().mockImplementation(async (lib: string) => {
          if (lib !== 'places') return {}
          return {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            PlaceAutocompleteElement: function PlaceAutocompleteElement(_opts: any) {
              const el = document.createElement('div')
              capturedEl = el
              return el
            },
          }
        }),
      },
    })

    // R5.2: mock fetch to return a TZ API response for the timezone URL; else chart API response
    mockFetch.mockImplementation(async (url: unknown) => {
      if (typeof url === 'string' && url.includes('maps.googleapis.com/maps/api/timezone')) {
        return {
          ok: true, status: 200,
          json: async () => ({ status: 'OK', timeZoneId: 'Asia/Kolkata', rawOffset: 19800, dstOffset: 0 }),
        }
      }
      return {
        ok: true, status: 200,
        json: async () => ({ chart_id: 'chart-123', redirect_url: '/clients/chart-123/build' }),
      }
    })

    const origKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = 'test-key-r5'

    render(<NewClientForm />)

    await waitFor(() => expect(capturedEl).not.toBeNull(), { timeout: 2000 })

    // Dispatch gmp-select with placePrediction (R5.1 API shape)
    await act(async () => {
      const event = Object.assign(new Event('gmp-select'), { placePrediction: mockPlacePrediction })
      capturedEl!.dispatchEvent(event)
      await new Promise((r) => setTimeout(r, 50))
    })

    // placePrediction.toPlace() was called
    expect(mockPlacePrediction.toPlace).toHaveBeenCalled()
    // fetchFields was called with the correct fields (no addressComponents in R5)
    expect(mockFetchFields).toHaveBeenCalledWith({
      fields: ['location', 'displayName', 'formattedAddress'],
    })

    // lat/lng state is populated — DOM value must be the real number, not placeholder
    await waitFor(() => {
      expect((screen.getByLabelText(/^latitude/i) as HTMLInputElement).value).toBe('20.2961')
      expect((screen.getByLabelText(/^longitude/i) as HTMLInputElement).value).toBe('85.8245')
    })

    if (origKey === undefined) {
      delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    } else {
      process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = origKey
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (globalThis as any).google
  })

  // ── Test 9: successful POST → router.push with redirect_url ───────────────
  it('redirects to redirect_url on successful POST', async () => {
    render(<NewClientForm />)
    fillValidForm()

    fireEvent.click(screen.getByRole('button', { name: /build chart/i }))

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/clients/chart-123/build'))
  })

  // ── Test 10: 422 response → errors distributed by field ───────────────────
  it('distributes 422 errors to the correct form fields', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        error: 'validation_failed',
        errors: [
          { field: 'name',       message: 'name is required' },
          { field: 'lat',        message: 'lat must be between -90 and 90' },
          { field: 'birth_date', message: 'birth_date must be in YYYY-MM-DD format' },
        ],
      }),
    })

    render(<NewClientForm />)
    fillValidForm()

    fireEvent.click(screen.getByRole('button', { name: /build chart/i }))

    await waitFor(() => {
      const alerts = screen.getAllByRole('alert')
      const text = alerts.map((a) => a.textContent).join(' ')
      expect(text).toContain('name is required')
      expect(text).toContain('lat must be between -90 and 90')
      expect(text).toContain('birth_date must be in YYYY-MM-DD format')
    })
  })

})
