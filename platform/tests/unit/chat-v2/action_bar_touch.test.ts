/**
 * C.5 — Action bar always-visible on touch devices.
 *
 * Source-level assertions that the action bar divs use @media(hover:hover)
 * guards instead of bare opacity-0 group-hover:opacity-100, so the bar
 * remains visible on touch viewports where :hover never fires.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const src = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)

describe('C.5 — action bar touch visibility', () => {
  it('user action bar uses @media(hover:hover) guard instead of bare opacity-0', () => {
    expect(src).toContain(
      '[@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100',
    )
  })

  it('bare opacity-0 group-hover:opacity-100 is not used on action bar divs', () => {
    // The old pattern that breaks on touch devices must not appear
    expect(src).not.toContain('"flex items-center gap-2 opacity-0 group-hover:opacity-100')
  })

  it('both user and assistant action bars have the touch guard (two occurrences)', () => {
    const matches = src.match(/\[@media\(hover:hover\)\]:opacity-0 \[@media\(hover:hover\)\]:group-hover:opacity-100/g)
    expect(matches).toHaveLength(2)
  })

  it('transition-opacity is preserved on both action bar divs', () => {
    const matches = src.match(/\[@media\(hover:hover\)\]:opacity-0.*?transition-opacity/g)
    expect(matches).toHaveLength(2)
  })
})
