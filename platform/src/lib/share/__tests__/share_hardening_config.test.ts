// @vitest-environment node
/**
 * SS N-376 / PR-S4 — config-level pins: share response headers (item 3) and the
 * selective-share flag default (item 5).
 */
import { describe, expect, it } from 'vitest'
import nextConfig from '../../../../next.config'
import { DEFAULT_FLAGS } from '@/lib/config/feature_flags'
import { createConfigService } from '@/lib/config/index'

describe('next.config headers for /share/* (item 3)', () => {
  it('sends X-Robots-Tag, Referrer-Policy and Cache-Control on /share/:path*', async () => {
    expect(typeof nextConfig.headers).toBe('function')
    const rules = await nextConfig.headers!()
    const rule = rules.find((r) => r.source === '/share/:path*')
    expect(rule).toBeDefined()
    const h = Object.fromEntries(rule!.headers.map((x) => [x.key.toLowerCase(), x.value]))
    expect(h['x-robots-tag']).toBe('noindex, nofollow')
    expect(h['referrer-policy']).toBe('no-referrer')
    expect(h['cache-control']).toBe('private, no-store')
  })
})

describe('R10_SELECTIVE_SHARE flag (item 5)', () => {
  it('is declared and defaults ON', () => {
    expect((DEFAULT_FLAGS as Record<string, boolean>).R10_SELECTIVE_SHARE).toBe(true)
  })

  it('MARSYS_FLAG_R10_SELECTIVE_SHARE=false overrides it off; unset leaves it on', () => {
    const prev = process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
    try {
      delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
      expect(createConfigService().getFlag('R10_SELECTIVE_SHARE' as never)).toBe(true)
      process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
      expect(createConfigService().getFlag('R10_SELECTIVE_SHARE' as never)).toBe(false)
    } finally {
      if (prev === undefined) delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
      else process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = prev
    }
  })
})
