/**
 * Canonical serializer — PB-2 (SMṚTI) lane M-1.
 *
 * Produces a STABLE, deterministic serialization of a canonical message + its
 * parts. This is the SHARED serialization PB-2's next lane (M-2, the
 * byte-equality gate) uses to compare two independently-produced views of the
 * same turn:
 *   (a) "replay the event stream through the reducer" (in-memory), vs
 *   (b) "read the persisted message_parts rows back from the DB".
 * If M-1's schema + writer are correct, those two must serialize BYTE-IDENTICAL.
 *
 * DETERMINISM CONTRACT — what makes the output stable:
 *   1. Object keys are recursively sorted (lexicographic) at every depth, so two
 *      logically-equal objects built with different key-insertion order collapse
 *      to the same bytes.
 *   2. Arrays preserve order (they are ordered data): parts are sorted by `seq`
 *      up front; within a body, array fields like `tool_call.args` values keep
 *      their meaningful order.
 *   3. Only DETERMINISTIC, cross-view-shared fields are included. Fields that
 *      exist in the persisted view but NOT in the replayed view — the DB-assigned
 *      part `id` (gen_random_uuid), `created_at` (now()), and the row-level
 *      `metadata_json` — are DELIBERATELY EXCLUDED, because including them would
 *      make (a) and (b) diverge on data that is not part of the turn's logical
 *      content. What IS included is exactly the shared identity + content:
 *        message: { conversation_id, id, model_id, provider, role, schema_version }
 *        parts[]: { body, kind, model_visible, seq }   (seq-ordered)
 *   4. `JSON.stringify` with NO whitespace argument — compact, single spacing
 *      rule — over the canonicalized (deep-key-sorted) structure.
 *
 * The function is PURE: no I/O, no clock, no randomness. Same logical input →
 * same string, always.
 */

import type { CanonicalMessage, MessagePartInput, PersistedMessagePart } from './schema'

/**
 * Recursively produce a value with all object keys sorted lexicographically.
 * Arrays keep their order (order is meaningful); primitives pass through.
 * `undefined` object properties are dropped (they have no JSON representation),
 * so an explicitly-`undefined` optional field and an absent one collapse to the
 * same canonical form.
 */
export function canonicalizeValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(canonicalizeValue)
  }
  if (value !== null && typeof value === 'object') {
    const src = value as Record<string, unknown>
    const out: Record<string, unknown> = {}
    for (const key of Object.keys(src).sort()) {
      const v = src[key]
      if (v === undefined) continue
      out[key] = canonicalizeValue(v)
    }
    return out
  }
  return value
}

/** The subset of message fields that participate in the canonical form. */
interface CanonicalMessageView {
  id: string
  conversation_id: string
  role: string
  schema_version: number
  model_id: string
  provider: string
}

/** The subset of part fields that participate in the canonical form. */
interface CanonicalPartView {
  seq: number
  kind: string
  model_visible: boolean
  body: unknown
}

/** A part shape the serializer accepts — either a write-input or a persisted row. */
type SerializablePart =
  | Pick<MessagePartInput, 'seq' | 'kind' | 'body' | 'model_visible'>
  | Pick<PersistedMessagePart, 'seq' | 'kind' | 'body' | 'model_visible'>

/** A message shape the serializer accepts (only the shared identity fields are read). */
type SerializableMessage = Pick<
  CanonicalMessage,
  'id' | 'conversation_id' | 'role' | 'schema_version' | 'model_id' | 'provider'
>

/**
 * Build the canonical OBJECT (deep-key-sorted, parts seq-ordered, non-shared
 * fields excluded). Useful for structured assertions; `serializeCanonical`
 * stringifies this.
 */
export function serializeCanonicalObject(
  message: SerializableMessage,
  parts: readonly SerializablePart[],
): { message: CanonicalMessageView; parts: CanonicalPartView[] } {
  const messageView: CanonicalMessageView = {
    id: message.id,
    conversation_id: message.conversation_id,
    role: message.role,
    schema_version: message.schema_version,
    model_id: message.model_id,
    provider: message.provider,
  }

  // Copy before sort so we never mutate the caller's array; sort by seq ascending.
  const partViews: CanonicalPartView[] = [...parts]
    .sort((a, b) => a.seq - b.seq)
    .map((p) => ({
      seq: p.seq,
      kind: p.kind,
      model_visible: p.model_visible,
      body: p.body,
    }))

  return canonicalizeValue({ message: messageView, parts: partViews }) as {
    message: CanonicalMessageView
    parts: CanonicalPartView[]
  }
}

/**
 * The canonical serialization as a STABLE string. Two calls with the same
 * logical content — regardless of object key-insertion order or part array
 * order — return byte-identical strings.
 */
export function serializeCanonical(
  message: SerializableMessage,
  parts: readonly SerializablePart[],
): string {
  return JSON.stringify(serializeCanonicalObject(message, parts))
}
