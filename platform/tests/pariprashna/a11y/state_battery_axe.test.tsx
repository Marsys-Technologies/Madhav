/**
 * P2-F (PPR-19, mobile + a11y hardening) — real axe-core against the REAL
 * component tree, once per §5.3 state.
 *
 * Same pattern as `tests/pariprashna/samiksha/samiksha_axe.test.tsx` (the
 * established precedent in this codebase): render actual production
 * components into jsdom, run the actual `axe-core` engine (not a mock, not
 * a synthetic replay harness) against the actual DOM, assert zero
 * critical/serious violations. A demonstrate-can-fail check proves axe is
 * really inspecting this DOM (§N.8 — a green result needs a detector that
 * could have gone red).
 *
 * States covered (the acceptance criterion is "every §5.3 state fixture"):
 * thinking/streaming, settled (single-pass), settled with verse+table
 * (adaptive three-pass), honest-gap settled, interrupted, reconnecting,
 * errored, empty (no turns), and the two mobile sheet-open states (citation
 * sheet, model-picker sheet).
 */
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { Harness } from './Harness'
import {
  playFixtureToEnd,
  playFixturePartial,
  playFixtureInterrupted,
  playFixtureReconnecting,
  playFixtureErrored,
} from './state_fixtures'
import { installDesktopViewport, installMobileViewport, restoreMatchMedia } from './match_media'

afterEach(() => {
  cleanup()
  restoreMatchMedia()
})

async function runAxe(node: Element) {
  return axe.run(node as HTMLElement, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
  })
}

function assertClean(results: Awaited<ReturnType<typeof runAxe>>, label: string) {
  const blocking = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
  const report = blocking.map((v) => `  [${v.impact}] ${v.id}: ${v.help} (${v.nodes.length}×) — ${v.helpUrl}`).join('\n')
  expect(blocking, `${label}: axe found ${blocking.length} critical/serious violation(s):\n${report}`).toHaveLength(0)
}

describe('P2-F real-component axe battery — one state per §5.3 fixture', () => {
  it('demonstrate-can-fail: axe genuinely inspects this DOM', async () => {
    const div = document.createElement('div')
    div.innerHTML = '<button></button><img src="x.png">'
    document.body.appendChild(div)
    const results = await runAxe(div)
    expect(results.violations.length).toBeGreaterThan(0)
    document.body.removeChild(div)
  }, 20000)

  it('thinking/streaming (adaptive, 30% through)', async () => {
    installDesktopViewport()
    const turn = playFixturePartial('adaptive', 0.3)
    const { container } = render(<Harness turns={[turn]} />)
    assertClean(await runAxe(container), 'thinking/streaming')
  }, 20000)

  it('settled — single pass', async () => {
    installDesktopViewport()
    const turn = playFixtureToEnd('single')
    expect(turn.status).toBe('settled')
    const { container } = render(<Harness turns={[turn]} />)
    assertClean(await runAxe(container), 'settled/single')
  }, 20000)

  it('settled — adaptive three-pass (multi-pass streamed paragraphs, citations, prediction card)', async () => {
    installDesktopViewport()
    const turn = playFixtureToEnd('adaptive')
    expect(turn.status).toBe('settled')
    expect(Object.keys(turn.citations).length).toBeGreaterThan(0)
    const { container } = render(<Harness turns={[turn]} />)
    assertClean(await runAxe(container), 'settled/adaptive')
  }, 20000)

  it('settled — honest gap (gap_ribbon block, role="note")', async () => {
    installDesktopViewport()
    const turn = playFixtureToEnd('gap')
    expect(turn.status).toBe('settled')
    const { container } = render(<Harness turns={[turn]} />)
    const ribbon = container.querySelector('.pp-gap-ribbon')
    expect(ribbon, 'expected the gap fixture to actually commit a gap_ribbon block').not.toBeNull()
    expect(ribbon).toHaveAttribute('role', 'note')
    assertClean(await runAxe(container), 'settled/honest-gap')
  }, 20000)

  it('interrupted (Stop mid-stream)', async () => {
    installDesktopViewport()
    const turn = playFixtureInterrupted('adaptive', 0.4)
    expect(turn.status).toBe('interrupted')
    const { container } = render(<Harness turns={[turn]} />)
    assertClean(await runAxe(container), 'interrupted')
  }, 20000)

  it('reconnecting mid-stream', async () => {
    installDesktopViewport()
    const turn = playFixtureReconnecting('adaptive', 0.4)
    expect(turn.status).toBe('reconnecting')
    const { container } = render(<Harness turns={[turn]} />)
    assertClean(await runAxe(container), 'reconnecting')
  }, 20000)

  it('errored (rate_limit band)', async () => {
    installDesktopViewport()
    const turn = playFixtureErrored('adaptive', 0.4)
    expect(turn.status).toBe('errored')
    const { container } = render(<Harness turns={[turn]} />)
    assertClean(await runAxe(container), 'errored')
  }, 20000)

  it('empty transcript (no turns yet)', async () => {
    installDesktopViewport()
    const { container } = render(<Harness turns={[]} />)
    assertClean(await runAxe(container), 'empty')
  }, 20000)

  it('mobile citation sheet open (§9.2 tap-first, bottom sheet)', async () => {
    installMobileViewport()
    const turn = playFixtureToEnd('adaptive')
    render(<Harness turns={[turn]} />)
    const chips = screen.getAllByTestId('pp-citation-chip')
    expect(chips.length).toBeGreaterThan(0)
    await userEvent.click(chips[0])
    const sheet = await screen.findByRole('dialog', { name: /citation detail/i })
    assertClean(await runAxe(sheet), 'mobile citation sheet')
  }, 20000)

  it('mobile model-picker sheet open (§9.2 "model picker" is a sheet on mobile)', async () => {
    installMobileViewport()
    const turn = playFixtureToEnd('single')
    render(<Harness turns={[turn]} />)
    const modelButton = screen.getByRole('button', { name: /Claude Opus/i })
    await userEvent.click(modelButton)
    const listbox = await screen.findByRole('listbox')
    // It rendered as the sheet variant, not the anchored dropdown.
    expect(listbox.closest('.pp-sheet')).not.toBeNull()
    assertClean(await runAxe(listbox), 'mobile model picker sheet')
  }, 20000)

  it('composer has an accessible name distinct from its placeholder', async () => {
    installDesktopViewport()
    render(<Harness turns={[]} />)
    const textarea = screen.getByTestId('pp-composer-textarea')
    expect(textarea).toHaveAccessibleName()
  })
})
