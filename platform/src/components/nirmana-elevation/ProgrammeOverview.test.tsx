import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { ProgrammeOverview } from './ProgrammeOverview'

function snapshotFixture(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

describe('ProgrammeOverview', () => {
  it('renders the overall percent, position label, and a real aria-valuenow', () => {
    const snapshot = snapshotFixture()
    snapshot.programme = {
      ...snapshot.programme,
      overall: { earned: 34, required: 100, percent: 34 },
      position_label: '34% · 29/128 frozen',
    }

    render(<ProgrammeOverview snapshot={snapshot} />)

    const bar = screen.getByRole('progressbar', { name: /overall asset elevation completion/i })
    expect(bar).toHaveAttribute('aria-valuenow', '34')
    expect(bar).toHaveAttribute('aria-valuemin', '0')
    expect(bar).toHaveAttribute('aria-valuemax', '100')
    expect(screen.getByText('34%')).toBeVisible()
    expect(screen.getByText(`${snapshot.progress.assets_frozen} of ${snapshot.progress.assets_total} assets frozen.`, { exact: false })).toBeVisible()
  })

  it('floors the percent instead of rounding (199/200 reads 99%, not 100%)', () => {
    const snapshot = snapshotFixture()
    snapshot.programme = {
      ...snapshot.programme,
      overall: { earned: 199, required: 200, percent: 99 },
    }

    render(<ProgrammeOverview snapshot={snapshot} />)

    expect(screen.getByText('99%')).toBeVisible()
    expect(screen.queryByText('100%')).not.toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: /overall asset elevation completion/i })).toHaveAttribute('aria-valuenow', '99')
  })

  it('renders an explicit "—" and omits aria-valuenow when the percent is null, never a fabricated 0', () => {
    const snapshot = snapshotFixture()
    snapshot.programme = {
      ...snapshot.programme,
      overall: { earned: 0, required: 0, percent: null },
      position_label: 'Execution not yet evidenced',
    }

    render(<ProgrammeOverview snapshot={snapshot} />)

    const bar = screen.getByRole('progressbar', { name: /overall asset elevation completion/i })
    expect(bar).not.toHaveAttribute('aria-valuenow')
    expect(screen.getByText('—')).toBeVisible()
    expect(screen.queryByText('0%')).not.toBeInTheDocument()
  })

  it('renders the 4-phase arc strip with a provenance chip on every chip, and an O-Wave popover listing WPs plus the post-wave addendum', () => {
    const snapshot = snapshotFixture()

    render(<ProgrammeOverview snapshot={snapshot} />)

    const arc = screen.getByLabelText('Programme arc')
    expect(within(arc).getByText('Phase A')).toBeVisible()
    expect(within(arc).getByText('O-Wave')).toBeVisible()
    expect(within(arc).getByText('Layers')).toBeVisible()
    expect(within(arc).getByText('Phase Z')).toBeVisible()
    // Every one of the 4 chips carries a provenance chip (repo-declared or evidence-derived).
    expect(within(arc).getAllByText(/^(Repo-declared|Evidence-derived)$/)).toHaveLength(4)

    const oWaveSummary = within(arc).getByText('O-Wave')
    fireEvent.click(oWaveSummary)
    for (const wp of snapshot.programme.o_wave.wps) {
      expect(wp.status).toBe('merged')
      const prSuffix = wp.merged_pr ? ` · PR #${wp.merged_pr.number}` : ''
      expect(screen.getByText(`${wp.name}: ${wp.status}${prSuffix}`)).toBeVisible()
    }
    for (const addendum of snapshot.programme.o_wave.addenda) {
      const prSuffix = addendum.merged_pr ? ` · PR #${addendum.merged_pr.number}` : ''
      expect(screen.getByText(`${addendum.name}: ${addendum.status}${prSuffix} (post-wave addendum)`)).toBeVisible()
    }
  })
})
