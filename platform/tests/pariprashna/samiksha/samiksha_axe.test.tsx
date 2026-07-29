/**
 * SAMĪKṢĀ accessibility gate — PB-3 lane L-3 acceptance criterion "axe clean on the tab".
 *
 * Renders the REAL, populated `<SamiksaReview>` (all three sections + badge + slider + resolve
 * keyboard grid) into jsdom and runs the REAL axe-core engine against the rendered DOM — not a
 * visual guess, not a mock. A demonstrate-can-fail check follows: axe genuinely flags a
 * deliberately broken control, proving the engine is actually inspecting this DOM.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'
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
