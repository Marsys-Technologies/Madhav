import { beforeEach, describe, expect, it, vi } from 'vitest'

const checkRpm = vi.hoisted(() => vi.fn())
vi.mock('@/lib/mcp/rate_limiter_core', () => ({ checkRpm }))
import { admitByokTurn } from '../byok_admission'

describe('admitByokTurn', () => {
  beforeEach(() => checkRpm.mockReset().mockReturnValue({ allowed: true }))

  it('rejects hard-cap violations before consuming the rate counter', () => {
    expect(admitByokTurn({ userId: 'a', questionChars: 32_001 })).toEqual({
      allowed: false, code: 'AI_EXECUTION_FAILED',
    })
    expect(checkRpm).not.toHaveBeenCalled()
  })

  it('admits only two concurrent turns and release is idempotent', () => {
    const first = admitByokTurn({ userId: 'b', questionChars: 1 })
    const second = admitByokTurn({ userId: 'b', questionChars: 1 })
    expect(first.allowed).toBe(true)
    expect(second.allowed).toBe(true)
    expect(admitByokTurn({ userId: 'b', questionChars: 1 })).toMatchObject({ allowed: false, code: 'AI_RATE_LIMITED' })
    if (first.allowed) { first.release(); first.release() }
    const replacement = admitByokTurn({ userId: 'b', questionChars: 1 })
    expect(replacement.allowed).toBe(true)
    if (second.allowed) second.release()
    if (replacement.allowed) replacement.release()
  })
})
