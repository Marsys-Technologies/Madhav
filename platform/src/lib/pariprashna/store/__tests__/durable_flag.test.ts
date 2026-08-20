import { describe, it, expect } from 'vitest'
import { configService } from '@/lib/config/index'
import { DURABLE_PERSISTENCE_FLAG, isDurablePersistenceEnabled } from '../durable_flag'

describe('durable persistence flag (P2-D, PPR-10)', () => {
  it('defaults to false — ships dark', () => {
    expect(isDurablePersistenceEnabled()).toBe(false)
  })

  it('reads through configService.getFlag, the one flag read site', () => {
    configService.setFlag(DURABLE_PERSISTENCE_FLAG, true)
    expect(isDurablePersistenceEnabled()).toBe(true)
    configService.setFlag(DURABLE_PERSISTENCE_FLAG, false)
    expect(isDurablePersistenceEnabled()).toBe(false)
  })
})
