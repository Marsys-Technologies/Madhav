/**
 * SAMĪKṢĀ accessibility gate — PB-3 lane L-3 acceptance criterion "axe clean on the tab".
 *
 * Renders the REAL, populated `<SamiksaReview>` (all three sections + badge + slider + resolve
 * keyboard grid) into jsdom and runs the REAL axe-core engine against the rendered DOM — not a
 * visual guess, not a mock. A demonstrate-can-fail check follows: axe genuinely flags a
 * deliberately broken control, proving the engine is actually inspecting this DOM.
 */
import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, cleanup, fireEvent, within } from '@testing-library/react'
import axe from 'axe-core'
import { SamiksaReview } from '@/components/pariprashna/samiksha/SamiksaReview'
import { makeFixtureVm, noopActions } from './fixture'

afterEach(cleanup)

async function runAxe(node: Element) {
  const results = await axe.run(node as HTMLElement, {
    // WCAG 2 A/AA rule set — the meaningful bar for a real product surface.
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
  })
  return results
}

describe('SamiksaReview accessibility (real axe-core)', () => {
  it('has no axe violations across the three sections + badge', async () => {
    const { container } = render(<SamiksaReview vm={makeFixtureVm()} actions={noopActions} />)
    const results = await runAxe(container)
    const summary = results.violations.map((v) => `${v.id}: ${v.nodes.length}× — ${v.help}`)
    expect(summary, `axe violations:\n${summary.join('\n')}`).toEqual([])
  }, 20000)

  it('keeps populated predictions and source links readable without mutation controls', async () => {
    const vm = makeFixtureVm()
    const actions = { ...noopActions, confirm: vi.fn(), resolve: vi.fn(), batchResolve: vi.fn() }
    const view = render(<SamiksaReview vm={vm} actions={actions} />)
    const links = () => within(view.container).getAllByRole('link').map(link => link.getAttribute('href'))
    const fullAccessLinks = links()
    fireEvent.click(within(view.container).getAllByRole('button', { name: 'Log to Samīkṣā' })[0])
    expect(actions.confirm).toHaveBeenCalledWith({ rowId: vm.awaiting[0].id, probability: 0.6 })
    const row = within(view.container).getByRole('listitem', { name: /^Prediction:/ })
    fireEvent.keyDown(row, { key: 'h' })
    fireEvent.keyDown(row, { key: 'Enter' })
    expect(actions.resolve).toHaveBeenCalledWith({ rowId: vm.resolvable[0].id, outcome: 'happened' })

    view.rerender(<SamiksaReview vm={vm} actions={null} />)
    expect(view.container).toHaveTextContent('Read-only')
    for (const prediction of [...vm.awaiting, ...vm.open, ...vm.resolvable]) {
      expect(view.container).toHaveTextContent(prediction.claim_text)
    }
    expect(links()).toEqual(fullAccessLinks)
    expect(within(view.container).queryAllByRole('button')).toEqual([])
    expect(within(view.container).queryAllByRole('slider')).toEqual([])
    expect(within(view.container).queryAllByRole('radio')).toEqual([])
    expect(view.container.querySelector('li[tabindex]')).toBeNull()
    const readOnlyRow = within(view.container).getByText(vm.resolvable[0].claim_text)
    fireEvent.keyDown(readOnlyRow, { key: 'h' })
    fireEvent.keyDown(readOnlyRow, { key: 'Enter', ctrlKey: true })
    expect(actions.resolve).toHaveBeenCalledTimes(1)
    expect(actions.batchResolve).not.toHaveBeenCalled()
    expect((await runAxe(view.container)).violations).toEqual([])
  }, 20000)

  it('axe actually inspects this DOM (demonstrate-can-fail: an unlabeled control is flagged)', async () => {
    // A button with no accessible name is a real WCAG failure; if axe returned clean here the
    // gate above would be meaningless. This proves the engine sees THIS document.
    const div = document.createElement('div')
    div.innerHTML = '<button></button><img src="x.png">'
    document.body.appendChild(div)
    const results = await runAxe(div)
    expect(results.violations.length).toBeGreaterThan(0)
    document.body.removeChild(div)
  }, 20000)
})
