/**
 * Unit tests — feature flag defaults.
 *
 * CHAT_V2_ENABLED removed at §M.16 (2026-05-18); tests for it retired.
 */
import { describe, it, expect } from 'vitest'
import { DEFAULT_FLAGS } from '@/lib/config/feature_flags'

describe('feature flags — defaults', () => {
  it('CONSUME_UI_V2_ENABLED defaults to true (matches prod deploy.yml)', () => {
    expect(DEFAULT_FLAGS.CONSUME_UI_V2_ENABLED).toBe(true)
  })
})
