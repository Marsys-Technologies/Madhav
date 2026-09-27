/**
 * AI choice replay discovery.
 *
 * The standalone replay server does not mount the production React surface,
 * so this gate deliberately proves only the implementation's stable visual
 * and interaction contract. Persistence and role routing require the genuine
 * authenticated surface and are not claimed here.
 */
import { readFile } from 'node:fs/promises'
import { test, expect } from '@playwright/test'

test.describe('AI choice — composer geometry and choreography', () => {
  test('keeps AI → Depth → Length and the exact three-row internal-scroll composer', async () => {
    const source = await readFile('src/components/pariprashna/composer/Composer.tsx', 'utf8')
    const ai = source.indexOf('<AiChoicePicker')
    const depth = source.indexOf('eyebrow="Depth"')
    const length = source.indexOf('eyebrow="Length"')

    expect(ai).toBeGreaterThan(-1)
    expect(depth).toBeGreaterThan(ai)
    expect(length).toBeGreaterThan(depth)
    expect(source).toContain('const MIN_LINES = 3')
    expect(source).toContain('const COMPOSER_HEIGHT_PX = 96')
    expect(source).toContain('overflowY: \'auto\'')
  })

  test('retains the grouped desktop/mobile picker and keyboard dismissal contract', async () => {
    const source = await readFile('src/components/pariprashna/composer/AiChoicePicker.tsx', 'utf8')

    expect(source).toContain("['Provider connections', 'Custom configurations', 'Local CLIs']")
    expect(source).toContain("event.key === 'Enter' || event.key === ' '")
    expect(source).toContain("event.key === 'Escape'")
    expect(source).toContain('pp-sheet')
    expect(source).toContain('aria-label="AI choices"')
  })
})
