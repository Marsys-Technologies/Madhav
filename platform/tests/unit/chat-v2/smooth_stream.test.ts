/**
 * Y-S3 — Smooth-Stream V2
 *
 * Tests getSmoothStreamTransform() flag gate:
 *   - flag=true → transform returned (truthy)
 *   - flag=false → undefined returned
 *   - MAX_WORD_BUFFER_MS exported and equal to 80
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('server-only', () => ({}))

// Provide a fake smoothStream so the module can import without AI SDK side-effects
vi.mock('ai', () => ({
  smoothStream: (opts: unknown) => ({ __smoothStream: true, opts }),
}))

// Mock getFlag — overridden per test
const flagValues: Record<string, boolean> = { R10_SMOOTH_STREAM_V2: true }
vi.mock('@/lib/config/index', () => ({
  getFlag: (key: string) => flagValues[key] ?? false,
}))

import { getSmoothStreamTransform, MAX_WORD_BUFFER_MS } from '@/lib/streaming/smooth_stream'

describe('smooth_stream — getSmoothStreamTransform (Y-S3)', () => {
  beforeEach(() => {
    flagValues.R10_SMOOTH_STREAM_V2 = true
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('MAX_WORD_BUFFER_MS is 80', () => {
    expect(MAX_WORD_BUFFER_MS).toBe(80)
  })

  it('returns a transform when R10_SMOOTH_STREAM_V2=true', () => {
    flagValues.R10_SMOOTH_STREAM_V2 = true
    const transform = getSmoothStreamTransform()
    expect(transform).toBeDefined()
    expect(transform).not.toBeNull()
  })

  it('returns undefined when R10_SMOOTH_STREAM_V2=false', () => {
    flagValues.R10_SMOOTH_STREAM_V2 = false
    const transform = getSmoothStreamTransform()
    expect(transform).toBeUndefined()
  })

  it('transform is configured with delayInMs=MAX_WORD_BUFFER_MS and chunking=word', () => {
    flagValues.R10_SMOOTH_STREAM_V2 = true
    const transform = getSmoothStreamTransform() as unknown as { opts: { delayInMs: number; chunking: string } }
    expect(transform.opts.delayInMs).toBe(MAX_WORD_BUFFER_MS)
    expect(transform.opts.chunking).toBe('word')
  })
})
