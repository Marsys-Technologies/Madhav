/**
 * P2-F (PPR-19) — regression canary for the CSS-only §9 fixes: reads the
 * actual `pariprashna.css` source and asserts the specific rules this lane
 * added are still present. Cheap, but real: it fails if any of these rules
 * is ever accidentally deleted or reworded away from its normative intent,
 * which a pure axe/DOM test wouldn't catch (axe doesn't check touch-target
 * size or `prefers-contrast` support).
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const css = readFileSync(join(__dirname, '../../../src/components/pariprashna/pariprashna.css'), 'utf-8')

describe('pariprashna.css — §9 mobile/a11y rules present', () => {
  it('citation chip hit area extends to 40x40 via a pseudo-element, visual box unchanged', () => {
    expect(css).toMatch(/\.pp-chip::before\s*\{[^}]*width:\s*max\(40px/)
    expect(css).toMatch(/\.pp-chip::before\s*\{[^}]*height:\s*40px/)
    // The visible box (M6 fixed geometry) is untouched — still 20/16.
    expect(css).toMatch(/\.pp-chip\s*\{[^}]*min-width:\s*20px/)
    expect(css).toMatch(/\.pp-chip\s*\{[^}]*height:\s*16px/)
  })

  it('composer Stop/Send action grows to 44px on touch/mobile', () => {
    expect(css).toMatch(/\(pointer:\s*coarse\)/)
    expect(css).toMatch(/\.pp-composer-action\s*\{[^}]*width:\s*44px/)
    expect(css).toMatch(/\.pp-composer-action\s*\{[^}]*height:\s*44px/)
  })

  it('sheets (citation card + mobile pickers) contain overscroll', () => {
    expect(css).toMatch(/\.pp-sheet-scrim,\s*\n?\s*\.pp-sheet\s*\{[^}]*overscroll-behavior:\s*contain/)
  })

  it('prefers-contrast: more bumps hairline/ink-dim tokens', () => {
    expect(css).toMatch(/@media \(prefers-contrast: more\)/)
    const block = css.slice(css.indexOf('@media (prefers-contrast: more)'))
    expect(block).toMatch(/--pp-rule:\s*rgba\(201, 162, 76, 0\.5\)/)
    expect(block).toMatch(/--pp-ink-dim:\s*rgba\(235, 227, 210, 0\.8\)/)
  })
})
