/**
 * Unit tests — α6 feature flag reconciliation.
 *
 * Verifies CHAT_V2_ENABLED is defined in DEFAULT_FLAGS and defaults to false.
 */
import { describe, it, expect } from 'vitest'
import { DEFAULT_FLAGS } from '@/lib/config/feature_flags'

describe('feature flags — α6 reconciliation', () => {
  it('CHAT_V2_ENABLED is defined in DEFAULT_FLAGS', () => {
    expect('CHAT_V2_ENABLED' in DEFAULT_FLAGS).toBe(true)
  })

  it('CHAT_V2_ENABLED defaults to false (dark-launched)', () => {
    expect(DEFAULT_FLAGS.CHAT_V2_ENABLED).toBe(false)
  })

  it('CONSUME_UI_V2_ENABLED defaults to true (matches prod deploy.yml)', () => {
    expect(DEFAULT_FLAGS.CONSUME_UI_V2_ENABLED).toBe(true)
  })
})
