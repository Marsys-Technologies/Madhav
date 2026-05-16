/**
 * upload_validator — offline validation for file uploads.
 *
 * Security surface: runs server-side before any byte hits storage.
 * All checks are pure (no I/O); the caller supplies headerBytes
 * from the first 16 bytes of the actual upload body.
 */

export const UPLOAD_MAX_SIZE = 50 * 1024 * 1024 // 50 MB

export const ALLOWED_MIME_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'application/pdf',
])

/** Magic-byte signatures: { mimeType → [[byteOffset, expectedBytes]…] } */
const MAGIC: Record<string, [number, number[]][]> = {
  'image/jpeg':     [[0, [0xFF, 0xD8, 0xFF]]],
  'image/png':      [[0, [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]]],
  'image/gif':      [[0, [0x47, 0x49, 0x46, 0x38]]], // GIF8
  'image/webp':     [[8, [0x57, 0x45, 0x42, 0x50]]], // RIFF????WEBP — "WEBP" at offset 8
  'application/pdf':[[0, [0x25, 0x50, 0x44, 0x46]]], // %PDF
}

export interface UploadValidationResult {
  ok: boolean
  error?: string
  sanitizedFilename?: string
}

/**
 * Sanitize a user-supplied filename:
 * - strip null bytes and control characters
 * - strip XSS-prone HTML characters
 * - strip path traversal sequences
 * - strip path separators
 * - strip leading dots (hidden-file prevention)
 * - truncate to 200 chars
 */
export function sanitizeFilename(raw: string): string {
  return raw
    .replace(/[\x00-\x1f\x7f]/g, '')  // control characters + DEL
    .replace(/[<>"'`&;]/g, '')         // XSS-prone chars
    .replace(/\.\./g, '')              // path traversal components
    .replace(/[/\\]/g, '')             // path separators
    .replace(/^\.+/, '')               // leading dots
    .trim()
    .slice(0, 200)
}

/**
 * Validate a single upload before it is persisted.
 *
 * @param filename      Raw filename as supplied by the client.
 * @param contentType   MIME type declared by the client.
 * @param size          File size in bytes as declared by the client.
 * @param headerBytes   First ≥16 bytes of the actual file body (optional).
 *                      When supplied, magic-byte mismatch is a hard fail
 *                      (catches JPEG-renamed-as-PDF polyglot attacks).
 */
export function validateUpload(
  filename: string,
  contentType: string,
  size: number,
  headerBytes?: Buffer | Uint8Array,
): UploadValidationResult {
  // 1. Size
  if (size <= 0) {
    return { ok: false, error: 'File must not be empty' }
  }
  if (size > UPLOAD_MAX_SIZE) {
    return { ok: false, error: `File too large (max ${UPLOAD_MAX_SIZE / 1024 / 1024} MB)` }
  }

  // 2. Declared MIME type
  const normalised = contentType.split(';')[0].trim().toLowerCase()
  if (!ALLOWED_MIME_TYPES.has(normalised)) {
    return { ok: false, error: `File type not allowed: ${normalised}` }
  }

  // 3. Filename sanitisation
  const sanitizedFilename = sanitizeFilename(filename)
  if (!sanitizedFilename) {
    return { ok: false, error: 'Filename is empty after sanitisation' }
  }

  // 4. Magic-byte validation (polyglot detection)
  if (headerBytes) {
    const checks = MAGIC[normalised]
    if (checks) {
      const ok = checks.every(([offset, expected]) =>
        expected.every((byte, i) => headerBytes[offset + i] === byte),
      )
      if (!ok) {
        return { ok: false, error: `File content does not match declared type ${normalised}` }
      }
    }
  }

  return { ok: true, sanitizedFilename }
}
