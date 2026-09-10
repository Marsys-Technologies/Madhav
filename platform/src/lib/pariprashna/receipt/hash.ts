import 'server-only'
/**
 * pariprashna/receipt/hash.ts — `receipt_hash` (lane G3-A, PPR-01).
 *
 * A deterministic sha256 over the receipt's OWN content (every field except
 * `receipt_hash` itself), so the hash changes iff the content changes and is
 * stable across re-serialization of an unchanged receipt. Key order in the
 * input object must not matter — `canonicalize` sorts object keys
 * recursively before `JSON.stringify` so two structurally-identical objects
 * with different insertion order hash identically.
 *
 * Isomorphic algorithm, Node-only implementation (`node:crypto`) — this
 * module is imported only from server-side receipt code (`assemble.ts`,
 * `validate.ts`), never from client bundles.
 */

import { createHash } from 'node:crypto'

/** Recursively sort object keys so hash input is independent of field order. */
function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize)
  if (value !== null && typeof value === 'object') {
    const obj = value as Record<string, unknown>
    const sorted: Record<string, unknown> = {}
    for (const key of Object.keys(obj).sort()) sorted[key] = canonicalize(obj[key])
    return sorted
  }
  return value
}

/** sha256 hex digest of the canonical JSON serialization of `content`. */
export function computeReceiptHash(content: unknown): string {
  const json = JSON.stringify(canonicalize(content))
  return createHash('sha256').update(json, 'utf8').digest('hex')
}
