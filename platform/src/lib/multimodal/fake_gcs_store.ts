/**
 * fake_gcs_store — in-process upload store for dev/test.
 *
 * Replaces a real GCS bucket when no cloud credentials are present.
 * Stores file bytes in a Map keyed by UUID token.
 * Entries expire after 1 hour (TTL enforced on read).
 *
 * This module is intentionally simple: it holds bytes in memory and
 * loses them on process restart — acceptable for interactive dev sessions.
 *
 * MANUAL_INTERVENTION_REQUIRED (§M.1):
 *   Provision real GCS buckets (marsys-chat-uploads-{env}) for production.
 *   Once GCS_BUCKET_NAME env var is set, the sign endpoint bypasses this store.
 */

interface StoredFile {
  filename: string
  contentType: string
  bytes: Buffer
  expiresAt: number
}

const TTL_MS = 60 * 60 * 1000 // 1 hour

// Module-level Map — survives across Next.js hot-reloads in dev
// because Node modules are cached for the process lifetime.
const store = new Map<string, StoredFile>()

export function fakeGcsStore(token: string, filename: string, contentType: string, bytes: Buffer): void {
  // Evict expired entries on every write (simple GC)
  const now = Date.now()
  for (const [k, v] of store.entries()) {
    if (v.expiresAt < now) store.delete(k)
  }
  store.set(token, { filename, contentType, bytes, expiresAt: now + TTL_MS })
}

export interface FakeGcsEntry {
  filename: string
  contentType: string
  bytes: Buffer
}

export function fakeGcsRetrieve(token: string): FakeGcsEntry | null {
  const entry = store.get(token)
  if (!entry) return null
  if (entry.expiresAt < Date.now()) {
    store.delete(token)
    return null
  }
  return { filename: entry.filename, contentType: entry.contentType, bytes: entry.bytes }
}

export function fakeGcsDelete(token: string): void {
  store.delete(token)
}
