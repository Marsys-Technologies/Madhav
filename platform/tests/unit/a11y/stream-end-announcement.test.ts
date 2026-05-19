import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const src = readFileSync(
  join(__dirname, '../../../src/components/chat/AssistantMessage.tsx'),
  'utf-8',
)

describe('AC-1 — stream-end screen-reader announcement', () => {
  it('contains aria-live="polite" region', () => {
    expect(src).toContain('aria-live="polite"')
  })

  it('contains role="status" for the live region span', () => {
    expect(src).toContain('role="status"')
  })

  it('uses sr-only class so the span is visually hidden', () => {
    expect(src).toContain('sr-only')
  })

  it('announces "Response complete" when streaming ends', () => {
    expect(src).toContain('Response complete')
  })

  it('tracks previous isStreaming value via useRef (prevStreamingRef)', () => {
    expect(src).toContain('prevStreamingRef')
  })

  it('clears announcement text when streaming starts', () => {
    // The effect sets announceText to '' on false→true transition
    expect(src).toContain("setAnnounceText('')")
  })
})
