import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { EditRebuildConfirmDialog, type ChangedField } from '../EditRebuildConfirmDialog'

const CHANGES: ChangedField[] = [
  { key: 'birth_time', label: 'Birth time', before: '10:43', after: '10:44' },
  { key: 'birth_place', label: 'Birth place', before: 'Bhubaneswar', after: 'Cuttack' },
]

function renderDialog(overrides: Partial<Parameters<typeof EditRebuildConfirmDialog>[0]> = {}) {
  const props = {
    chartName: 'Test Native',
    open: true,
    changes: CHANGES,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    ...overrides,
  }
  render(<EditRebuildConfirmDialog {...props} />)
  return props
}

describe('EditRebuildConfirmDialog', () => {
  it('is a labelled dialog about recomputing this chart', () => {
    renderDialog()
    expect(screen.getByRole('dialog', { name: /recompute test native/i })).toBeInTheDocument()
  })

  it('lists every changed field with its before and after value', () => {
    renderDialog()
    for (const change of CHANGES) {
      const row = screen.getByTestId(`change-${change.key}`)
      expect(row).toHaveTextContent(change.label)
      expect(row).toHaveTextContent(change.before)
      expect(row).toHaveTextContent(change.after)
    }
  })

  it('states replacement, read-only archival and visible progress — and never asks to delete or recreate', () => {
    renderDialog()
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveTextContent(/previous computed results will be replaced/i)
    expect(dialog).toHaveTextContent(/existing Paripraśna conversations will be archived read-only/i)
    expect(dialog).toHaveTextContent(/progress stays visible on the chart workspace/i)
    expect(dialog).not.toHaveTextContent(/delete|recreate/i)
  })

  it('confirms with Save and recompute and cancels with Cancel', () => {
    const props = renderDialog()
    fireEvent.click(screen.getByRole('button', { name: 'Save and recompute' }))
    expect(props.onConfirm).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(props.onCancel).toHaveBeenCalled()
  })

  it('renders nothing when closed', () => {
    renderDialog({ open: false })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
