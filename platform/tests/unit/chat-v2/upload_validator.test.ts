/**
 * upload_validator — security + unit tests
 *
 * All tests are offline (pure function calls, no I/O).
 * Covers: size, MIME, filename sanitisation, magic-byte (polyglot) checks.
 */
import { describe, it, expect } from 'vitest'
import {
  validateUpload,
  sanitizeFilename,
  UPLOAD_MAX_SIZE,
  ALLOWED_MIME_TYPES,
} from '@/lib/multimodal/upload_validator'

// ─── Magic-byte helpers ───────────────────────────────────────────────────────

function makeHeader(mime: string): Buffer {
  const headers: Record<string, number[]> = {
    'image/jpeg':     [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01],
    'image/png':      [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52],
    'image/gif':      [0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF],
    // WEBP: RIFF....WEBP (offset 8 = WEBP)
    'image/webp':     [0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00, 0x57, 0x45, 0x42, 0x50, 0x56, 0x50, 0x38, 0x20],
    'application/pdf':[0x25, 0x50, 0x44, 0x46, 0x2D, 0x31, 0x2E, 0x34, 0x0A, 0x25, 0xE2, 0xE3, 0xCF, 0xD3, 0x0A, 0x0A],
  }
  return Buffer.from(headers[mime] ?? [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
}

// ─── sanitizeFilename ────────────────────────────────────────────────────────

describe('sanitizeFilename', () => {
  it('preserves a clean filename', () => {
    expect(sanitizeFilename('my-chart.jpg')).toBe('my-chart.jpg')
  })

  it('strips path traversal sequences', () => {
    expect(sanitizeFilename('../../../etc/passwd')).not.toContain('..')
    expect(sanitizeFilename('../../etc/passwd')).not.toContain('/')
  })

  it('strips path separators on all platforms', () => {
    const result = sanitizeFilename('path/to/file.pdf')
    expect(result).not.toContain('/')
    expect(result).not.toContain('\\')
  })

  it('strips XSS-dangerous characters', () => {
    const dangerous = '<script>alert(1)</script>.jpg'
    const safe = sanitizeFilename(dangerous)
    expect(safe).not.toContain('<')
    expect(safe).not.toContain('>')
    expect(safe).not.toContain('"')
  })

  it('strips null bytes and control characters', () => {
    const withNull = 'file\x00.jpg'
    expect(sanitizeFilename(withNull)).not.toContain('\x00')
  })

  it('strips leading dots', () => {
    expect(sanitizeFilename('.hidden-file.pdf')).not.toMatch(/^\./)
  })

  it('truncates to 200 characters', () => {
    const long = 'a'.repeat(300) + '.pdf'
    expect(sanitizeFilename(long).length).toBeLessThanOrEqual(200)
  })

  it('returns empty string for a filename that is all special chars', () => {
    expect(sanitizeFilename('<>"/\\...')).toBe('')
  })
})

// ─── validateUpload ──────────────────────────────────────────────────────────

describe('validateUpload — basic checks', () => {
  it('passes a valid JPEG without header bytes', () => {
    const result = validateUpload('photo.jpg', 'image/jpeg', 1024)
    expect(result.ok).toBe(true)
    expect(result.sanitizedFilename).toBe('photo.jpg')
  })

  it('rejects size 0', () => {
    const result = validateUpload('empty.jpg', 'image/jpeg', 0)
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/empty/i)
  })

  it('rejects oversized files', () => {
    const result = validateUpload('big.jpg', 'image/jpeg', UPLOAD_MAX_SIZE + 1)
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/too large/i)
  })

  it('accepts file at exactly MAX_SIZE', () => {
    const result = validateUpload('edge.jpg', 'image/jpeg', UPLOAD_MAX_SIZE)
    expect(result.ok).toBe(true)
  })

  it('rejects disallowed MIME type', () => {
    const result = validateUpload('virus.exe', 'application/octet-stream', 100)
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/not allowed/i)
  })

  it('rejects text/html (XSS-via-file-serving vector)', () => {
    const result = validateUpload('xss.html', 'text/html', 100)
    expect(result.ok).toBe(false)
  })

  it('rejects empty filename (after sanitisation)', () => {
    const result = validateUpload('<>', 'image/jpeg', 100)
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/filename/i)
  })

  it('sanitizes path-traversal in the filename', () => {
    const result = validateUpload('../../../etc/passwd.jpg', 'image/jpeg', 100)
    expect(result.ok).toBe(true)
    expect(result.sanitizedFilename).not.toContain('..')
    expect(result.sanitizedFilename).not.toContain('/')
  })

  it('accepts all allowed MIME types', () => {
    for (const mime of ALLOWED_MIME_TYPES) {
      const filename = mime === 'application/pdf' ? 'doc.pdf' : 'img.jpg'
      const result = validateUpload(filename, mime, 1024)
      expect(result.ok).toBe(true)
    }
  })
})

// ─── Magic-byte (polyglot) tests ─────────────────────────────────────────────

describe('validateUpload — magic-byte / polyglot detection', () => {
  it('accepts JPEG with correct magic bytes', () => {
    const result = validateUpload('photo.jpg', 'image/jpeg', 100, makeHeader('image/jpeg'))
    expect(result.ok).toBe(true)
  })

  it('rejects JPEG magic bytes declared as PNG (polyglot)', () => {
    const result = validateUpload('trick.png', 'image/png', 100, makeHeader('image/jpeg'))
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/content does not match/i)
  })

  it('accepts PDF with correct magic bytes', () => {
    const result = validateUpload('doc.pdf', 'application/pdf', 100, makeHeader('application/pdf'))
    expect(result.ok).toBe(true)
  })

  it('rejects PDF magic bytes declared as JPEG (polyglot — PDF-as-JPEG attack)', () => {
    const result = validateUpload('evil.jpg', 'image/jpeg', 100, makeHeader('application/pdf'))
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/content does not match/i)
  })

  it('accepts PNG with correct magic bytes', () => {
    const result = validateUpload('img.png', 'image/png', 100, makeHeader('image/png'))
    expect(result.ok).toBe(true)
  })

  it('accepts GIF with correct magic bytes', () => {
    const result = validateUpload('anim.gif', 'image/gif', 100, makeHeader('image/gif'))
    expect(result.ok).toBe(true)
  })

  it('accepts WEBP with correct magic bytes', () => {
    const result = validateUpload('img.webp', 'image/webp', 100, makeHeader('image/webp'))
    expect(result.ok).toBe(true)
  })

  it('rejects zeroed header bytes for any declared type', () => {
    const zeroHeader = Buffer.alloc(16, 0)
    for (const mime of ['image/jpeg', 'image/png', 'application/pdf']) {
      const result = validateUpload('file', mime, 100, zeroHeader)
      expect(result.ok).toBe(false)
    }
  })
})
