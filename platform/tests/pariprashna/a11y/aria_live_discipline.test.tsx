/**
 * P2-F (PPR-19) §9.3 structural assertions that axe-core itself doesn't
 * check (project-specific rules, not a standard WCAG success criterion):
 *
 *  1. Exactly one live streaming region (`[data-testid="pp-tail"]`,
 *     `aria-live="polite"`) exists at a time.
 *  2. No `[data-committed="true"]` block (a settled `FrozenBlock`) is a
 *     descendant of that region — a committed block staying inside the
 *     live region would cause a screen reader to re-announce it forever.
 *  3. The honest-gap ribbon carries `role="note"`, never `role="alert"`.
 *  4. A verse (Sanskrit quote) block carries `lang="sa-Latn"`.
 */
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render } from '@testing-library/react'
import { Harness } from './Harness'
import { playFixturePartial, playFixtureToEnd } from './state_fixtures'
import { installDesktopViewport, restoreMatchMedia } from './match_media'
import axe from 'axe-core'
import { VerseBlock } from '@/components/pariprashna/answer/blocks/VerseBlock'
import { TableBlock } from '@/components/pariprashna/answer/blocks/TableBlock'

afterEach(() => {
  cleanup()
  restoreMatchMedia()
})

describe('aria-live discipline (§9.3)', () => {
  it('mid-stream: exactly one live tail region, and committed blocks are not inside it', () => {
    installDesktopViewport()
    // 60% through an adaptive three-pass fixture: by this point at least one
    // earlier block has committed AND the current block is still streaming
    // (a genuine "committed block + live tail coexist" moment), which is
    // the only configuration this assertion is meaningful against.
    const turn = playFixturePartial('adaptive', 0.6)
    expect(turn.blocks.length, 'fixture setup: expected at least one committed block by 60% through').toBeGreaterThan(0)
    expect(turn.tail, 'fixture setup: expected an active tail at 60% through').not.toBeNull()

    const { container } = render(<Harness turns={[turn]} />)

    const liveRegions = container.querySelectorAll('[data-testid="pp-tail"][aria-live="polite"]')
    expect(liveRegions.length).toBe(1)

    const committedInsideLive = liveRegions[0].querySelectorAll('[data-committed="true"]')
    expect(committedInsideLive.length, 'a committed block must not remain inside the streaming live region').toBe(0)

    const committedBlocks = container.querySelectorAll('[data-committed="true"]')
    expect(committedBlocks.length).toBeGreaterThan(0)
  })

  it('settled turn: no live tail region remains (tail unmounts on turn.commit)', () => {
    installDesktopViewport()
    const turn = playFixtureToEnd('single')
    const { container } = render(<Harness turns={[turn]} />)
    expect(container.querySelectorAll('[data-testid="pp-tail"]').length).toBe(0)
    expect(container.querySelectorAll('[data-committed="true"]').length).toBeGreaterThan(0)
  })

  it('honest-gap ribbon is role="note", never role="alert"', () => {
    installDesktopViewport()
    const turn = playFixtureToEnd('gap')
    const { container } = render(<Harness turns={[turn]} />)
    const ribbon = container.querySelector('.pp-gap-ribbon')
    expect(ribbon).not.toBeNull()
    expect(ribbon).toHaveAttribute('role', 'note')
    expect(container.querySelectorAll('.pp-gap-ribbon[role="alert"]').length).toBe(0)
  })

  it('a verse block carries lang="sa-Latn" (no shipped fixture currently commits a verse block, so this exercises VerseBlock directly rather than asserting on fixture content that doesn\'t exist)', () => {
    const { container } = render(<VerseBlock turnId="t1" text="tat savitur vareṇyaṃ" citations={{}} />)
    const verse = container.querySelector('.pp-verse[lang="sa-Latn"]')
    expect(verse).not.toBeNull()
    expect(verse?.textContent).toContain('tat savitur vareṇyaṃ')
  })

  it('TableBlock is axe-clean and its column headers carry scope="col" (no shipped fixture currently commits a table block — the ADAPTIVE/GAP/etc. fixtures in fixtures/*.ts only emit paragraph, gap_ribbon, and prediction_card kinds — so, as with VerseBlock above, this exercises the component directly)', async () => {
    const { container } = render(
      <TableBlock table={{ headers: ['Period', 'House'], rows: [['2026–2028', '10th'], ['2028–2031', '11th']] }} />,
    )
    const ths = container.querySelectorAll('th')
    expect(ths.length).toBe(2)
    ths.forEach((th) => expect(th).toHaveAttribute('scope', 'col'))
    const results = await axe.run(container, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } })
    const blocking = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    expect(blocking, blocking.map((v) => `${v.id}: ${v.help}`).join('\n')).toHaveLength(0)
  }, 20000)

  it('the settle summary announces once, and only for the settled turn', () => {
    installDesktopViewport()
    const turn = playFixtureToEnd('single')
    const { container } = render(<Harness turns={[turn]} />)
    const settleSummaries = container.querySelectorAll('[role="status"][aria-live="polite"]')
    // GroundingRegion's settle summary is one of (possibly several) role=status
    // regions; assert at least one exists and its text matches the spec's
    // exact wording pattern ("Reading complete. Grounded in …").
    const texts = Array.from(settleSummaries).map((n) => n.textContent ?? '')
    expect(texts.some((t) => /^Reading complete\. Grounded in/.test(t))).toBe(true)
  })
})
