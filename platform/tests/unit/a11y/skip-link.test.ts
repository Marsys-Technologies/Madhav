import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const src = readFileSync(
  join(__dirname, '../../../src/components/chat/ChatShell.tsx'),
  'utf-8',
)

describe('AC-2 — skip-to-content link', () => {
  it('renders skip link with href="#chat-main"', () => {
    expect(src).toContain('href="#chat-main"')
  })

  it('skip link text is "Skip to chat"', () => {
    expect(src).toContain('Skip to chat')
  })

  it('main element carries id="chat-main" as skip target', () => {
    expect(src).toContain('id="chat-main"')
  })

  it('skip link is sr-only by default', () => {
    expect(src).toContain('sr-only')
  })

  it('skip link becomes visible on keyboard focus (focus:not-sr-only)', () => {
    expect(src).toContain('focus:not-sr-only')
  })

  it('skip link appears before aside (first child of root div)', () => {
    const skipIdx = src.indexOf('href="#chat-main"')
    const asideIdx = src.indexOf('<aside')
    expect(skipIdx).toBeGreaterThan(0)
    expect(skipIdx).toBeLessThan(asideIdx)
  })
})
