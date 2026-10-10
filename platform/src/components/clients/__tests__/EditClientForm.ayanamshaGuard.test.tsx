/**
 * EditClientForm — ayanamsha edit policy (SS N-319) and the prefill fix (D-04).
 *
 * block_all: the selection is read-only with the plain message and is never
 * sent. warn: a strong confirm dialog, then `confirm_destructive: true`.
 * off: the original behaviour. In every policy the ayanamsha list is sent only
 * when the user changed it, so saving another field is never an ayanamsha edit,
 * even when the stored value is long-form or holds an id the form cannot offer.
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
  PlacesAutocompleteNew: () => null,
}))

import { EditClientForm, splitStoredAyanamshas, type EditableChart } from '../EditClientForm'
import type { AyanamshaEditPolicy } from '@/lib/charts/ayanamshaEditGuard'

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
const respond = (status: number, body: unknown) =>
  fetchMock.mockResolvedValueOnce({ ok: status >= 200 && status < 300, status, json: async () => body })
const sentBody = () => JSON.parse(fetchMock.mock.calls[0][1].body as string)
const mount = (policy: AyanamshaEditPolicy, chart: EditableChart = CHART) =>
  render(<EditClientForm chart={chart} ayanamshaEditPolicy={policy} />)
const rename = () => fireEvent.change(screen.getByLabelText(/^full name/i), { target: { value: 'Renamed Native' } })

beforeEach(() => {
  vi.clearAllMocks()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('splitStoredAyanamshas (prefill)', () => {
  it('folds long and legacy spellings to the options’ short ids', () => {
    expect(splitStoredAyanamshas(['lahiri_chitrapaksha', 'krishnamurti'])).toEqual({ selectable: ['lahiri', 'kp'], legacy: [] })
  })

  it('returns ids the form cannot offer as legacy instead of dropping them', () => {
    expect(splitStoredAyanamshas(['lahiri', 'fagan_bradley'])).toEqual({ selectable: ['lahiri'], legacy: ['fagan_bradley'] })
  })

  it('deduplicates and handles an empty list', () => {
    expect(splitStoredAyanamshas(['lahiri', 'lahiri_chitrapaksha'])).toEqual({ selectable: ['lahiri'], legacy: [] })
    expect(splitStoredAyanamshas([])).toEqual({ selectable: [], legacy: [] })
  })
})

describe('EditClientForm — block_all', () => {
  it('shows the selection read-only with the plain message and no checkboxes', () => {
    mount('block_all')
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    expect(within(screen.getByTestId('ayanamshas-readonly')).getByText('Lahiri')).toBeInTheDocument()
    const note = screen.getByTestId('ayanamshas-blocked-note')
    expect(note).toHaveTextContent(/ayanamsha of an existing chart can't be changed here/i)
    expect(note).toHaveTextContent(/contact support/i)
  })

  it('shows a long-form stored value as its option and lists an unknown stored id', () => {
    mount('block_all', { ...CHART, ayanamshas: ['lahiri_chitrapaksha', 'fagan_bradley'] })
    const list = screen.getByTestId('ayanamshas-readonly')
    expect(within(list).getByText('Lahiri')).toBeInTheDocument()
    expect(within(list).getByText('fagan_bradley')).toBeInTheDocument()
  })

  it('a name-only edit is a plain Save changes that sends no ayanamshas and no flag', async () => {
    respond(200, { data: { mode: 'display-only', chartId: 'c1', changedFields: ['name'] } })
    mount('block_all')
    rename()
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(sentBody()).toMatchObject({ name: 'Renamed Native' })
    expect(sentBody()).not.toHaveProperty('ayanamshas')
    expect(sentBody()).not.toHaveProperty('confirm_destructive')
  })

  it('a birth-time edit still recomputes (the standard dialog) without sending ayanamshas', async () => {
    respond(202, { data: { mode: 'recompute-started', chartId: 'c1', changedFields: ['birth_time'], runId: 'r1' } })
    mount('block_all')
    fireEvent.change(screen.getByLabelText(/^time of birth/i), { target: { value: '10:44' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save and recompute' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ birth_time: '10:44' })
    expect(sentBody()).not.toHaveProperty('ayanamshas')
  })

  it('shows the server’s refusal message if the server policy was stricter than the page', async () => {
    respond(403, {
      error: "The ayanamsha of an existing chart can't be changed here. Contact support if it must change.",
      code: 'AYANAMSHA_EDIT_BLOCKED',
    })
    mount('warn')
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: /erase results/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/can't be changed here/i)
    expect(mockPush).not.toHaveBeenCalled()
  })
})

describe('EditClientForm — warn', () => {
  it('shows today’s selector plus a warning note', () => {
    mount('warn')
    expect(screen.getByRole('checkbox', { name: 'KP' })).toBeInTheDocument()
    expect(screen.getByTestId('ayanamshas-warn-note')).toHaveTextContent(/erases all built results/i)
  })

  it('an ayanamsha change opens a strong confirm dialog; Cancel sends nothing', async () => {
    mount('warn')
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent(/erases every built result for this chart and archives its conversations/i)
    expect(dialog).toHaveTextContent(/requires your confirmation/i)
    expect(within(dialog).getByTestId('ayanamsha-before-after')).toHaveTextContent('Lahiri')
    expect(within(dialog).getByTestId('ayanamsha-before-after')).toHaveTextContent('KP')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))
    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument())
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('confirming sends the new list with confirm_destructive: true', async () => {
    respond(202, { data: { mode: 'recompute-started', chartId: 'c1', changedFields: ['ayanamshas'], runId: 'r1' } })
    mount('warn')
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: /erase results/i }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ ayanamshas: ['kp', 'lahiri'], confirm_destructive: true })
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/clients/c1'))
  })

  it('a name-only edit does not ask, and sends no ayanamshas and no flag', async () => {
    respond(200, { data: { mode: 'display-only', chartId: 'c1', changedFields: ['name'] } })
    mount('warn')
    rename()
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(sentBody()).not.toHaveProperty('ayanamshas')
    expect(sentBody()).not.toHaveProperty('confirm_destructive')
  })

  it('a birth-time edit uses the standard recompute dialog and sends no flag', async () => {
    respond(202, { data: { mode: 'recompute-started', chartId: 'c1', changedFields: ['birth_time'], runId: 'r1' } })
    mount('warn')
    fireEvent.change(screen.getByLabelText(/^time of birth/i), { target: { value: '10:44' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    const dialog = await screen.findByRole('dialog')
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save and recompute' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(sentBody()).not.toHaveProperty('confirm_destructive')
    expect(sentBody()).not.toHaveProperty('ayanamshas')
  })

  it('shows the server’s needs-confirmation message rather than the build-in-progress copy', async () => {
    respond(409, {
      error: 'Changing the ayanamsha of an existing chart erases all built results for this chart and archives its conversations. This change requires confirmation.',
      code: 'AYANAMSHA_EDIT_NEEDS_CONFIRMATION',
    })
    mount('warn')
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: /erase results/i }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/requires confirmation/i)
    expect(alert).not.toHaveTextContent(/build is in progress/i)
  })
})

describe('EditClientForm — off', () => {
  it('is today’s behaviour: the standard dialog, the new list, no confirm flag', async () => {
    respond(202, { data: { mode: 'recompute-started', chartId: 'c1', changedFields: ['ayanamshas'], runId: 'r1' } })
    mount('off')
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    expect(screen.queryByTestId('ayanamshas-warn-note')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    const dialog = await screen.findByRole('dialog')
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save and recompute' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(sentBody()).toMatchObject({ ayanamshas: ['kp', 'lahiri'] })
    expect(sentBody()).not.toHaveProperty('confirm_destructive')
  })

  it('refuses to save an emptied selection when the user changed it', () => {
    mount('off')
    fireEvent.click(screen.getByRole('checkbox', { name: 'Lahiri' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    expect(screen.getByText('Select at least one ayanāṃśa.')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('EditClientForm — untouched ayanamsha never counts as an edit (D-04)', () => {
  it.each<AyanamshaEditPolicy>(['block_all', 'warn', 'off'])(
    '%s: a stored list with an id the options do not offer stays a display-only save',
    async (policy) => {
      respond(200, { data: { mode: 'display-only', chartId: 'c1', changedFields: ['name'] } })
      mount(policy, { ...CHART, ayanamshas: ['lahiri_chitrapaksha', 'fagan_bradley'] })
      rename()
      // No recompute hint: the legacy id must not make the untouched list look changed.
      expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
      await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      expect(sentBody()).not.toHaveProperty('ayanamshas')
    },
  )

  it('a long-form stored value shows its short-id checkbox checked and untouched', () => {
    mount('off', { ...CHART, ayanamshas: ['lahiri_chitrapaksha'] })
    expect(screen.getByRole('checkbox', { name: 'Lahiri' })).toBeChecked()
    rename()
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument()
  })

  it('toggling an option and toggling it back is not a change either', async () => {
    mount('off')
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'KP' }))
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument()
  })
})
