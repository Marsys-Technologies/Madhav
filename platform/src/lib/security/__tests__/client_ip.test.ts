// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { getTrustedClientIp, ipRateLimitKey, TRUSTED_PROXY_HOPS, trustedProxyHops } from '../client_ip'

const h = (xff?: string, extra: Record<string, string> = {}) => {
  const headers = new Headers(extra)
  if (xff !== undefined) headers.set('x-forwarded-for', xff)
  return headers
}

describe('getTrustedClientIp (SS N-373 item 4)', () => {
  it('documents the hop count: one trusted infrastructure hop by default', () => {
    expect(TRUSTED_PROXY_HOPS).toBe(1)
  })

  it('single entry (Google appended the peer) -> that entry', () => {
    expect(getTrustedClientIp(h('203.0.113.9'))).toBe('203.0.113.9')
  })

  it('SPOOFED leftmost entry is ignored: the rightmost (Google-appended) hop wins', () => {
    expect(getTrustedClientIp(h('1.1.1.1, 203.0.113.9'))).toBe('203.0.113.9')
  })

  it('many spoofed leftmost entries are all ignored', () => {
    expect(getTrustedClientIp(h('9.9.9.9, 8.8.8.8, 7.7.7.7, 203.0.113.9'))).toBe('203.0.113.9')
  })

  it('whitespace around entries is tolerated', () => {
    expect(getTrustedClientIp(h('  6.6.6.6 ,   203.0.113.9  '))).toBe('203.0.113.9')
  })

  it('two requests that differ ONLY in the spoofed prefix map to the same client', () => {
    const a = getTrustedClientIp(h('10.0.0.1, 203.0.113.9'))
    const b = getTrustedClientIp(h('10.0.0.2, 203.0.113.9'))
    expect(a).toBe(b)
  })

  it('hops=2 trusts the second-from-right entry and ignores everything left of it', () => {
    expect(getTrustedClientIp(h('spoof, 203.0.113.9, 130.211.0.1'), 2)).toBe('203.0.113.9')
    expect(getTrustedClientIp(h('1.1.1.1, 2.2.2.2, 203.0.113.9, 130.211.0.1'), 2)).toBe('203.0.113.9')
  })

  it('fewer entries than trusted hops -> null (never falls back to a client-controlled entry)', () => {
    expect(getTrustedClientIp(h('203.0.113.9'), 2)).toBeNull()
  })

  it('missing / empty header -> null', () => {
    expect(getTrustedClientIp(h())).toBeNull()
    expect(getTrustedClientIp(h(''))).toBeNull()
    expect(getTrustedClientIp(h(' , '))).toBeNull()
  })

  it('a non-IP value at the trusted position -> null', () => {
    expect(getTrustedClientIp(h('1.2.3.4, not-an-ip'))).toBeNull()
    expect(getTrustedClientIp(h('1.2.3.4, <script>'))).toBeNull()
  })

  it('single-value forwarding headers are ignored entirely', () => {
    const headers = h(undefined, { 'x-real-ip': '6.6.6.6', 'cf-connecting-ip': '6.6.6.6', 'true-client-ip': '6.6.6.6' })
    expect(getTrustedClientIp(headers)).toBeNull()
    const both = h('203.0.113.9', { 'x-real-ip': '6.6.6.6' })
    expect(getTrustedClientIp(both)).toBe('203.0.113.9')
  })

  it('IPv4-mapped IPv6 is normalised to the IPv4 form', () => {
    expect(getTrustedClientIp(h('::ffff:203.0.113.9'))).toBe('203.0.113.9')
  })

  it('IPv6 is accepted and lower-cased', () => {
    expect(getTrustedClientIp(h('spoof, 2001:DB8::1'))).toBe('2001:db8::1')
  })
})

describe('trustedProxyHops', () => {
  it('defaults to TRUSTED_PROXY_HOPS when unset', () => {
    expect(trustedProxyHops({})).toBe(TRUSTED_PROXY_HOPS)
  })
  it('accepts a sane override', () => {
    expect(trustedProxyHops({ MARSYS_TRUSTED_PROXY_HOPS: '2' })).toBe(2)
  })
  it('rejects 0, negatives, non-integers, garbage and absurd values (back to the default)', () => {
    for (const bad of ['0', '-1', '1.5', 'abc', '', '9', '99']) {
      expect(trustedProxyHops({ MARSYS_TRUSTED_PROXY_HOPS: bad })).toBe(TRUSTED_PROXY_HOPS)
    }
  })
})

describe('ipRateLimitKey', () => {
  it('null -> one shared bucket', () => {
    expect(ipRateLimitKey(null)).toBe('unknown')
  })
  it('IPv4 is used as-is', () => {
    expect(ipRateLimitKey('203.0.113.9')).toBe('203.0.113.9')
  })
  it('IPv6 collapses to its /64 so an attacker cannot rotate through a /64 to evade the limit', () => {
    const a = ipRateLimitKey('2001:db8:1:2:aaaa:bbbb:cccc:dddd')
    const b = ipRateLimitKey('2001:db8:1:2::1')
    const c = ipRateLimitKey('2001:db8:1:3::1')
    expect(a).toBe(b)
    expect(a).not.toBe(c)
    expect(a).toBe('2001:db8:1:2::/64')
  })
})
