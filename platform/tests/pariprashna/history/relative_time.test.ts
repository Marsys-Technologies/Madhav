import { describe, it, expect } from 'vitest'
import { formatRelativeTime } from '@/components/pariprashna/history/relativeTime'

describe('formatRelativeTime', () => {
  const now = Date.parse('2026-08-19T12:00:00Z')

  it('reads "now" inside the 45s just-happened window', () => {
    expect(formatRelativeTime(now - 10_000, now)).toBe('now')
  })

  it('renders minutes once past the just-happened window', () => {
    expect(formatRelativeTime(now - 5 * 60_000, now)).toBe('5m')
  })

  it('renders hours past 60 minutes', () => {
    expect(formatRelativeTime(now - 3 * 3_600_000, now)).toBe('3h')
  })

  it('renders days past 24 hours', () => {
    expect(formatRelativeTime(now - 2 * 86_400_000, now)).toBe('2d')
  })

  it('renders months past 30 days', () => {
    expect(formatRelativeTime(now - 40 * 86_400_000, now)).toBe('1mo')
  })

  it('never goes negative for a clock-skew future timestamp', () => {
    expect(formatRelativeTime(now + 10_000, now)).toBe('now')
  })
})
