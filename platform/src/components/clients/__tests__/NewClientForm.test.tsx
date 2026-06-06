/**
 * NewClientForm.test.tsx — functional tests for the rebuilt single-state form
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { NewClientForm } from '../NewClientForm'

// ── Router mock ───────────────────────────────────────────────────────────────

const mockPush = vi.fn()
const mockBack = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}))

// ── fetch mock ────────────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ chart_id: 'chart-123', redirect_url: '/clients/chart-123/build' }),
  })
})

// ── Helper: fill a valid form ──────────────────────────────────────────────────

function fillValidForm() {
  fireEvent.change(screen.getByLabelText(/full name/i), {
    target: { value: 'Abhisek Mohanty' },
  })
  fireEvent.change(screen.getByLabelText(/gender/i), {
    target: { value: 'M' },
  })
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
  fireEvent.change(screen.getByLabelText(/utc offset/i), {
    target: { value: '5.5' },
  })
}

// ═════════════════════════════════════════════════════════════════════════════
// Test cases
// ═════════════════════════════════════════════════════════════════════════════

describe('NewClientForm', () => {

  // ── Test 1: form title, ayanamsha section, footer are present ─────────────
  it('renders title, ayanamsha section, and footer microcopy', () => {
    render(<NewClientForm />)
    expect(screen.getByTestId('form-title').textContent).toContain('Nava Jātaka')
    expect(screen.getByTestId('section-compute')).toBeTruthy()
    expect(screen.getByTestId('footer-microcopy').textContent).toContain('ayanamshas')
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
    // Must use exact API field names
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
    fireEvent.change(screen.getByLabelText(/gender/i), { target: { value: 'M' } })
    fireEvent.change(screen.getByLabelText(/^date/i), { target: { value: '1984-02-05' } })
    fireEvent.change(screen.getByLabelText(/time \(24/i), { target: { value: '10:43' } })
    fireEvent.change(screen.getByLabelText(/birth place/i), { target: { value: 'Bhubaneswar' } })
    fireEvent.change(screen.getByLabelText(/^latitude/i), { target: { value: '20.2961' } })
    fireEvent.change(screen.getByLabelText(/^longitude/i), { target: { value: '85.8245' } })
    fireEvent.change(screen.getByLabelText(/utc offset/i), { target: { value: '5.5' } })

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
    fireEvent.change(screen.getByLabelText(/^date/i), { target: { value: '1984-02-05' } })
    fireEvent.change(screen.getByLabelText(/time \(24/i), { target: { value: '10:43' } })
    fireEvent.change(screen.getByLabelText(/birth place/i), { target: { value: 'Bhubaneswar' } })
    fireEvent.change(screen.getByLabelText(/^latitude/i), { target: { value: '20.2961' } })
    fireEvent.change(screen.getByLabelText(/^longitude/i), { target: { value: '85.8245' } })
    fireEvent.change(screen.getByLabelText(/utc offset/i), { target: { value: '5.5' } })

    fireEvent.click(screen.getByRole('button', { name: /build chart/i }))

    await waitFor(() => {
      const alerts = screen.getAllByRole('alert')
      const msgs = alerts.map((a) => a.textContent).join(' ')
      expect(msgs).toMatch(/select a gender/i)
    })
    expect(mockFetch).not.toHaveBeenCalled()
  })

  // ── Test 6: gender option values are M, F, O, unknown ──────────────────────
  it('gender <option> values are M, F, O, unknown (not male/female)', () => {
    const { container } = render(<NewClientForm />)
    const select = container.querySelector('select#gender') as HTMLSelectElement
    expect(select).toBeTruthy()
    const values = Array.from(select.options).map((o) => o.value)
    expect(values).toContain('M')
    expect(values).toContain('F')
    expect(values).toContain('O')
    expect(values).toContain('unknown')
    expect(values).not.toContain('male')
    expect(values).not.toContain('female')
    expect(values).not.toContain('other')
    expect(values).not.toContain('not-specified')
  })

  // ── Test 7: ayanamsha toggle updates footer counter ────────────────────────
  it('toggling an ayanamsha checkbox updates the footer node count', () => {
    render(<NewClientForm />)
    const counter = screen.getByTestId('footer-microcopy')

    // Default: all 5 selected → 5 × 28 = 140
    expect(counter.textContent).toContain('5 ayanamshas × 28 assets = 140 nodes')

    // Uncheck one (Lahiri)
    const lahiriCheckbox = screen.getByLabelText('Lahiri')
    fireEvent.click(lahiriCheckbox.closest('label')!)

    expect(counter.textContent).toContain('4 ayanamshas × 28 assets = 112 nodes')
  })

  // ── Test 8: Places miss → manual override accordion auto-expands ───────────
  it('manual override accordion auto-expands when birth_place is typed but places_resolved is false', () => {
    render(<NewClientForm />)
    const accordion = screen.getByTestId('manual-override-accordion')

    // Type in birth_place and blur — without Places resolving
    const birthPlaceInput = screen.getByLabelText(/birth place/i)
    fireEvent.change(birthPlaceInput, { target: { value: 'Somewhere Unknown' } })
    fireEvent.blur(birthPlaceInput)

    // The accordion content should be open (latitude input visible)
    expect(accordion.querySelector('input#latitude')).toBeTruthy()
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
