/**
 * γ4 — Component tests for ValidatorFailureBand + ValidatorFooterChip
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ValidatorFailureBand } from '../ValidatorFailureBand'
import { ValidatorFooterChip } from '../ValidatorFooterChip'

// ── ValidatorFailureBand ───────────────────────────────────────────────────────

describe('ValidatorFailureBand', () => {
  it('renders the hard-fail banner with role=alert', () => {
    render(
      <ValidatorFailureBand
        issues={['SIG.MSR.001 missing']}
        isSuperAdmin={false}
        onOpenDetails={() => {}}
      />,
    )
    const band = screen.getByTestId('v2-validator-failure-band')
    expect(band).toBeInTheDocument()
    expect(band.getAttribute('role')).toBe('alert')
  })

  it('shows "Citation validation failed" heading', () => {
    render(
      <ValidatorFailureBand
        issues={['layer mismatch']}
        isSuperAdmin={false}
        onOpenDetails={() => {}}
      />,
    )
    expect(screen.getByText('Citation validation failed')).toBeInTheDocument()
  })

  it('shows generic summary for non-super_admin (issues hidden)', () => {
    render(
      <ValidatorFailureBand
        issues={['SIG.MSR.001 missing', 'SIG.MSR.002 layer mismatch']}
        isSuperAdmin={false}
        onOpenDetails={() => {}}
      />,
    )
    expect(screen.queryByText('SIG.MSR.001 missing')).not.toBeInTheDocument()
    expect(screen.getByText(/One or more citations could not be verified/)).toBeInTheDocument()
  })

  it('shows full issue list for super_admin', () => {
    render(
      <ValidatorFailureBand
        issues={['SIG.MSR.001 missing', 'SIG.MSR.002 layer mismatch']}
        isSuperAdmin={true}
        onOpenDetails={() => {}}
      />,
    )
    expect(screen.getByText('SIG.MSR.001 missing')).toBeInTheDocument()
    expect(screen.getByText('SIG.MSR.002 layer mismatch')).toBeInTheDocument()
  })

  it('shows generic summary for super_admin when issues list is empty', () => {
    render(
      <ValidatorFailureBand
        issues={[]}
        isSuperAdmin={true}
        onOpenDetails={() => {}}
      />,
    )
    expect(screen.getByText(/One or more citations could not be verified/)).toBeInTheDocument()
  })

  it('calls onOpenDetails when Details button is clicked', () => {
    const onOpenDetails = vi.fn()
    render(
      <ValidatorFailureBand
        issues={[]}
        isSuperAdmin={false}
        onOpenDetails={onOpenDetails}
      />,
    )
    fireEvent.click(screen.getByTestId('v2-validator-failure-details-btn'))
    expect(onOpenDetails).toHaveBeenCalledOnce()
  })
})

// ── ValidatorFooterChip ────────────────────────────────────────────────────────

describe('ValidatorFooterChip', () => {
  it('renders the soft-fail chip with role=status', () => {
    render(
      <ValidatorFooterChip
        issues={['low confidence']}
        isSuperAdmin={false}
        onOpenDetails={() => {}}
      />,
    )
    const chip = screen.getByTestId('v2-validator-footer-chip')
    expect(chip).toBeInTheDocument()
    const inner = chip.querySelector('[role="status"]')
    expect(inner).not.toBeNull()
  })

  it('shows "Validation warning" for non-super_admin', () => {
    render(
      <ValidatorFooterChip
        issues={['low confidence citation']}
        isSuperAdmin={false}
        onOpenDetails={() => {}}
      />,
    )
    expect(screen.getByText('Validation warning')).toBeInTheDocument()
  })

  it('shows "Citation warning" label for super_admin when issue exists', () => {
    render(
      <ValidatorFooterChip
        issues={['low confidence citation']}
        isSuperAdmin={true}
        onOpenDetails={() => {}}
      />,
    )
    expect(screen.getByText('Citation warning')).toBeInTheDocument()
  })

  it('adds title tooltip for super_admin', () => {
    render(
      <ValidatorFooterChip
        issues={['SIG.MSR.001 low confidence']}
        isSuperAdmin={true}
        onOpenDetails={() => {}}
      />,
    )
    const inner = screen.getByRole('status')
    expect(inner.getAttribute('title')).toBe('SIG.MSR.001 low confidence')
  })

  it('has no title tooltip for non-super_admin', () => {
    render(
      <ValidatorFooterChip
        issues={['SIG.MSR.001 low confidence']}
        isSuperAdmin={false}
        onOpenDetails={() => {}}
      />,
    )
    const inner = screen.getByRole('status')
    expect(inner.getAttribute('title')).toBeNull()
  })

  it('calls onOpenDetails when Details link is clicked', () => {
    const onOpenDetails = vi.fn()
    render(
      <ValidatorFooterChip
        issues={[]}
        isSuperAdmin={false}
        onOpenDetails={onOpenDetails}
      />,
    )
    fireEvent.click(screen.getByTestId('v2-validator-chip-details-btn'))
    expect(onOpenDetails).toHaveBeenCalledOnce()
  })
})
