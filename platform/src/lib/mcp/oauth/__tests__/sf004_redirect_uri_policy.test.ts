/**
 * SF-004 (PARIŚEṢA-V4): registration-time redirect_uri policy.
 * See 00_ARCHITECTURE/briefs/parisesa/SF004_OAUTH_BINDING_CONTRACT_v1_0.md §5.
 */
import { describe, it, expect } from 'vitest'
import { isRegistrableRedirectUri } from '../redirect_uri_policy'

describe('isRegistrableRedirectUri — SF-004 registration hygiene', () => {
  it('accepts a plain https: URI', () => {
    expect(isRegistrableRedirectUri('https://example.com/cb')).toBe(true)
  })

  it('accepts https: with a path and query string', () => {
    expect(isRegistrableRedirectUri('https://example.com/oauth/cb?foo=bar')).toBe(true)
  })

  it('accepts http: on localhost (dev loopback, RFC 8252 §7.3)', () => {
    expect(isRegistrableRedirectUri('http://localhost:3000/cb')).toBe(true)
  })

  it('accepts http: on 127.0.0.1', () => {
    expect(isRegistrableRedirectUri('http://127.0.0.1:8080/cb')).toBe(true)
  })

  it('accepts http: on IPv6 loopback [::1]', () => {
    expect(isRegistrableRedirectUri('http://[::1]:3000/cb')).toBe(true)
  })

  it('rejects javascript: URIs', () => {
    expect(isRegistrableRedirectUri('javascript:alert(1)')).toBe(false)
  })

  it('rejects data: URIs', () => {
    expect(isRegistrableRedirectUri('data:text/html,<script>alert(1)</script>')).toBe(false)
  })

  it('rejects http: on a non-loopback host', () => {
    expect(isRegistrableRedirectUri('http://evil.example/cb')).toBe(false)
  })

  it('rejects a fragment-bearing URI', () => {
    expect(isRegistrableRedirectUri('https://example.com/cb#fragment')).toBe(false)
  })

  it('rejects a wildcard host', () => {
    expect(isRegistrableRedirectUri('https://*.evil.example/cb')).toBe(false)
  })

  it('rejects a wildcard path', () => {
    expect(isRegistrableRedirectUri('https://example.com/*')).toBe(false)
  })

  it('rejects file: URIs', () => {
    expect(isRegistrableRedirectUri('file:///etc/passwd')).toBe(false)
  })

  it('rejects a custom app-private URI scheme (RFC 8252 native-app pattern) — deliberate scope limit', () => {
    expect(isRegistrableRedirectUri('com.example.app:/callback')).toBe(false)
  })

  it('rejects a malformed / unparseable string', () => {
    expect(isRegistrableRedirectUri('not a uri at all')).toBe(false)
  })

  it('rejects an empty string', () => {
    expect(isRegistrableRedirectUri('')).toBe(false)
  })

  it('rejects a URI with no authority at all (throws out of the URL parser)', () => {
    expect(isRegistrableRedirectUri('https://')).toBe(false)
    expect(isRegistrableRedirectUri('https:///')).toBe(false)
  })

  it('a triple-slash form that the URL parser resolves to a real host is still just a normal https: URI — not a bypass', () => {
    // `new URL('https:///cb')` resolves to hostname 'cb' (the WHATWG parser
    // treats the segment after the empty authority as the host, not a
    // degenerate empty one) — this is a parser quirk, not a security hole:
    // the raw string is what gets stored and later exact-matched at
    // /authorize, never re-parsed/re-normalized, so this cannot be used to
    // register one string and have it match a different one later.
    expect(isRegistrableRedirectUri('https:///cb')).toBe(true)
  })

  it('accepts uppercase scheme (HTTPS://) — URL parser lower-cases protocol', () => {
    expect(isRegistrableRedirectUri('HTTPS://example.com/cb')).toBe(true)
  })
})
