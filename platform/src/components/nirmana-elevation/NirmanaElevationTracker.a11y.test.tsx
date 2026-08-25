import axe from 'axe-core'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { NirmanaElevationTrackerView } from './NirmanaElevationTracker'

const wcagRunOptions = {
  runOnly: {
    type: 'tag' as const,
    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
  },
}

function snapshotV2(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

function renderTracker() {
  return render(
    <NirmanaElevationTrackerView
      snapshot={snapshotV2()}
      fetchedAt={new Date('2026-08-25T09:00:00.000Z')}
    />,
  )
}

describe('NirmanaElevationTracker accessibility', () => {
  it('is axe-clean with the current layer collapsed to its default asset summary', async () => {
    const { container } = renderTracker()

    const results = await axe.run(container, wcagRunOptions)

    expect(results.violations.map(({ id }) => id)).toEqual([])
  })

  it('is axe-clean with the current layer and asset expanded', async () => {
    const user = userEvent.setup()
    const { container } = renderTracker()
    await user.click(screen.getByRole('button', { name: /show details for bg_prashna_rules/i }))

    const results = await axe.run(container, wcagRunOptions)

    expect(results.violations.map(({ id }) => id)).toEqual([])
  })

  it('demonstrates that axe detects an unnamed control', async () => {
    const { container } = render(<button />)

    const results = await axe.run(container)

    expect(results.violations.map(({ id }) => id)).toContain('button-name')
  })
})

describe('NirmanaElevationTracker responsive structure', () => {
  it('stacks wave assets on mobile and adds columns only at desktop breakpoints', () => {
    renderTracker()

    const assetGrid = screen.getByText('bg_prashna_rules').closest('div.grid')
    if (!assetGrid) throw new Error('Wave asset grid is missing.')
    expect(assetGrid).toHaveClass('grid', 'gap-3', 'lg:grid-cols-2', 'xl:grid-cols-3')
    expect([...assetGrid.classList].filter((className) => /^grid-cols-/.test(className))).toEqual([])
  })

  it('keeps the Now/Next rail fluid at mobile widths', () => {
    renderTracker()

    const rail = screen.getByLabelText('Now, next, then campaign rail')
    expect(rail).toHaveClass('grid', 'gap-2', 'lg:grid-cols-4')
    expect([...rail.classList]).not.toEqual(expect.arrayContaining([
      expect.stringMatching(/^(?:w|min-w|max-w)-/),
    ]))
  })

  it('wraps bilingual asset names and avoids horizontal operational-canvas scrolling', async () => {
    const user = userEvent.setup()
    const { container } = renderTracker()
    await user.click(screen.getByRole('button', { name: /show details for bg_prashna_rules/i }))

    for (const name of [screen.getByText('Praśna Rules'), screen.getByText('Prashna Rules')]) {
      expect(name).not.toHaveClass('truncate', 'overflow-hidden', 'text-ellipsis', 'whitespace-nowrap')
      expect(name.parentElement).toHaveClass('min-w-0')
    }
    const horizontalScroller = [...container.querySelectorAll<HTMLElement>('[class]')].find((element) => (
      [...element.classList].some((className) => className === 'overflow-x-auto' || className.endsWith(':overflow-x-auto'))
    ))
    expect(horizontalScroller).toBeUndefined()
  })
})
