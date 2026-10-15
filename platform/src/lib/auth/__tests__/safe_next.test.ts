/**
 * SS N-379 (iv) — the ONE validator for the post-login `next` parameter.
 * Same-origin RELATIVE paths only, allowlisted to /share/ and /clients/.
 */
import { describe, expect, it } from 'vitest'
import { safeNextPath, SAFE_NEXT_MAX_LENGTH } from '../safe_next'

describe('safeNextPath: accepted', () => {
  it.each(['/share/AbC123xyz0', '/clients/abc-123/edit', '/clients/9f1c2b3a-0000-4000-8000-000000000000'])(
    'accepts %s unchanged',
    (p) => {
      expect(safeNextPath(p)).toBe(p)
    },
  )
})

describe('safeNextPath: open-redirect and encoding tricks are refused', () => {
  const bad: Array<[string, unknown]> = [
    ['protocol-relative', '//evil.com'],
    ['slash backslash', '/\\evil.com'],
    ['backslash slash', '\\/evil.com'],
    ['encoded protocol-relative', '%2F%2Fevil.com'],
    ['slash + encoded slash', '/%2Fevil.com'],
    ['slash + encoded backslash', '/%5Cevil.com'],
    ['javascript scheme', 'javascript:alert(1)'],
    ['slash javascript', '/javascript:alert(1)'],
    ['absolute https', 'https://evil.com'],
    ['absolute https allowlisted-looking', 'https://evil.com/share/abc'],
    ['dot-dot', '/share/../evil'],
    ['encoded dot-dot', '/share/%2e%2e/evil'],
    ['double-encoded dot-dot', '/share/%252e%252e/evil'],
    ['encoded dot-dot upper', '/share/%2E%2E/evil'],
    ['encoded CRLF', '/share/x%0d%0aLocation:evil'],
    ['encoded NUL', '/share/x%00'],
    ['encoded tab', '/share/x%09y'],
    ['double-encoded CRLF', '/share/x%250d%250a'],
    ['double-encoded slash slash after prefix', '/share/%252F%252Fevil.com'],
    ['literal newline', '/share/x\n'],
    ['literal CR', '/share/x\r'],
    ['literal tab', '/share/x\t'],
    ['leading space', ' /share/x'],
    ['trailing space', '/share/x '],
    ['inner space', '/share/x y'],
    ['unicode whitespace (nbsp)', '/share/x y'],
    ['unicode line separator', '/share/x y'],
    ['control char', '/share/x\u0001'],
    ['DEL', '/share/x\u007f'],
    ['backslash inside allowlisted path', '/share/x\\y'],
    ['colon inside path', '/share/a:b'],
    ['query string', '/share/abc?x=1'],
    ['fragment', '/share/abc#frag'],
    ['empty segment', '/share//abc'],
    ['malformed percent escape', '/share/100%'],
    ['dot segment', '/share/./abc'],
    ['empty string', ''],
    ['null', null],
    ['undefined', undefined],
    ['number', 42],
    ['object', {}],
    ['array', ['/share/abc']],
    ['very long string', '/share/' + 'a'.repeat(5000)],
    ['not allowlisted /dashboard', '/dashboard'],
    ['not allowlisted /', '/'],
    ['not allowlisted /login', '/login'],
    ['not allowlisted /admin/x', '/admin/x'],
    ['prefix lookalike /shared/x', '/shared/x'],
    ['prefix lookalike /clientsX/x', '/clientsX/x'],
    ['case: /Share/x', '/Share/x'],
    ['no trailing slash /clients', '/clients'],
    ['no trailing slash /share', '/share'],
    ['bare prefix /share/', '/share/'],
    ['bare prefix /clients/', '/clients/'],
  ]
  it.each(bad)('%s -> null', (_name, raw) => {
    expect(safeNextPath(raw as string | null | undefined)).toBeNull()
  })

  it('the length cap is exactly 512', () => {
    expect(SAFE_NEXT_MAX_LENGTH).toBe(512)
    const ok = '/share/' + 'a'.repeat(512 - '/share/'.length)
    expect(ok.length).toBe(512)
    expect(safeNextPath(ok)).toBe(ok)
    expect(safeNextPath(ok + 'a')).toBeNull()
  })
})
