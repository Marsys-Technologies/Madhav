import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import * as fs from 'node:fs'
import * as path from 'node:path'

/**
 * D.4 — LEL toggle "no amber" regression guard.
 *
 * The brand-consistent palette uses gold-family tokens (`--brand-gold`,
 * `text-muted-foreground`); amber-* Tailwind classes are reserved for
 * trace/error surfaces and must not appear on the LEL toggle. Mocking
 * the full ConsumeChat tree is heavy; we use two complementary strategies:
 *
 *   1. Source-level guard — the toggle's class strings in ConsumeChat.tsx
 *      contain no `amber-` token in the LEL toggle button block.
 *   2. Render-level guard — a stub that reproduces the production classes
 *      on/off, asserting the rendered DOM matches the brand palette.
 */

// Post-§M.16, the LEL toggle lives in ConsumeChatV2.tsx (setLelEnabled).
const consumeChatPath = path.resolve(__dirname, '..', 'ConsumeChatV2.tsx')
const source = fs.readFileSync(consumeChatPath, 'utf8')

function extractLelButtonBlock(src: string): string {
  // The LEL toggle button is the first <button onClick={() => setLelContextEnabled(...) }>.
  const start = src.indexOf('setLelEnabled')
  expect(start).toBeGreaterThan(-1)
  // Grab a generous slice forward to cover the className array.
  return src.slice(start, start + 1200)
}

// LEL toggle rendered in isolation (mirrors production class logic in
// ConsumeChat.tsx — keep these two in sync).
function LelToggleStub({ enabled }: { enabled: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={enabled}
      className={[
        'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors',
        enabled
          ? 'bg-[var(--brand-gold)]/15 text-[var(--brand-gold)] ring-1 ring-[var(--brand-gold)]/40 hover:bg-[var(--brand-gold)]/20'
          : 'bg-muted/40 text-muted-foreground ring-1 ring-border hover:bg-muted/60',
      ].join(' ')}
    >
      Life Events: {enabled ? 'On' : 'Off'}
    </button>
  )
}

describe('LEL toggle — D.4 no-amber regression guard', () => {
  it('source: LEL toggle button block contains no amber-* Tailwind class', () => {
    const block = extractLelButtonBlock(source)
    expect(block).not.toMatch(/\bamber-/)
  })

  it('render OFF: no amber-* class anywhere in the rendered DOM', () => {
    const { container } = render(<LelToggleStub enabled={false} />)
    expect(container.innerHTML).not.toMatch(/\bamber-/)
  })

  it('render OFF: button uses muted/foreground brand-consistent state', () => {
    const { container } = render(<LelToggleStub enabled={false} />)
    const btn = container.querySelector('button')!
    const cls = btn.className
    expect(cls).toMatch(/text-muted-foreground/)
    expect(cls).not.toMatch(/\bamber-/)
  })

  it('render ON: button uses gold-family classes and no amber', () => {
    const { container } = render(<LelToggleStub enabled />)
    const btn = container.querySelector('button')!
    const cls = btn.className
    expect(cls).toMatch(/--brand-gold/)
    expect(cls).not.toMatch(/\bamber-/)
    expect(btn.getAttribute('aria-pressed')).toBe('true')
  })
})
