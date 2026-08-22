/**
 * SF-004 (PARIŚEṢA-V4): registration-time redirect_uri policy.
 *
 * Mirrors platform/src/lib/mcp/oauth/__tests__/sf004_redirect_uri_policy.test.ts
 * one-for-one — this package's redirect_uri_policy.ts is a deliberate,
 * disclosed duplicate (the two packages don't share a module boundary; see
 * that file's own header). Both copies must stay in lockstep, so both test
 * files assert the identical behavior.
 *
 * See 00_ARCHITECTURE/briefs/parisesa/SF004_OAUTH_BINDING_CONTRACT_v1_0.md §5.
 */
import { describe, it, expect } from 'vitest'
import { isRegistrableRedirectUri } from '../oauth/redirect_uri_policy.js'

describe('isRegistrableRedirectUri — SF-004 registration hygiene (platform-mcp copy)', () => {
  it('accepts a plain https: URI', () => {
    expect(isRegistrableRedirectUri('https://example.com/cb')).toBe(true)
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

  it('rejects a custom app-private URI scheme — deliberate scope limit', () => {
    expect(isRegistrableRedirectUri('com.example.app:/callback')).toBe(false)
  })

  it('rejects a malformed / unparseable string', () => {
    expect(isRegistrableRedirectUri('not a uri at all')).toBe(false)
  })

  it('rejects an empty string', () => {
    expect(isRegistrableRedirectUri('')).toBe(false)
  })
})
