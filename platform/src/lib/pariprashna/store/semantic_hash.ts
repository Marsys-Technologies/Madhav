/**
 * Normalized semantic-hash comparator core — P2-D (PPR-10, FD-9).
 *
 * REPLACES the byte-equality invariant `replay_compare.ts` implements (kept
 * in place, unmodified, for diagnostic use — see that module's header) with
 * the invariant PARIPRASHNA_ARCHITECTURE_v1_0.md §7.4 actually requires:
 *
 *   "The replay↔persistence parity invariant MUST be a normalized semantic
 *    hash (byte equality is rejected; the PR-#927 capture apparatus is
 *    repurposed as the comparator's feed)."
 *
 * WHY BYTE EQUALITY WAS REJECTED (not a fresh claim — re-derived from the
 * record this module closes against): `REPORT_PB-2.md` / SAMĀPTI's F-33 /
 * PARIPRASHNA_V012_PHASE1_REVIEW_v0_1.md V12-F6 all independently confirmed
 * the SAME failure mode twice — a byte-for-byte comparator is a
 * FALSE-CONFIDENCE gate whenever two legitimately independent derivations of
 * the same fact format that fact differently (this codebase's own
 * `replay_compare.ts` header documents exactly this: citation snippet text is
 * derived twice, once by the write-through and once by the writer's own
 * `extractCitations`+`fetchMsrSnippets`, and "disagreement IS the finding" —
 * except a content-preserving formatting difference is NOT a finding, it is
 * noise a byte-equal gate cannot tell apart from a real content divergence).
 * A gate that cannot distinguish "the reading changed" from "the citation
 * snippet is phrased two words differently" either red-flags harmless noise
 * until someone silences it, or gets silenced first and stops meaning
 * anything — both are the false-confidence failure mode.
 *
 * WHAT "NORMALIZED" MEANS HERE — every step is a DISCLOSED, NAMED relaxation
 * of byte equality, never a silent one:
 *   1. Whitespace/newline normalization on every string field (CRLF→LF,
 *      trailing-whitespace trim per line, Unicode NFC) — formatting noise a
 *      human reader would never notice is not a content divergence.
 *   2. Citation identity vs. citation presentation: `signal_id` + `layer` +
 *      `index` are the FACT the citation is about — a real divergence there
 *      IS a finding. `snippet`/`reader_label` are presentation of that same
 *      fact and are independently re-derived on the two sides by design (see
 *      above) — a difference there alone does not fail the invariant, but IS
 *      still reported (never silently dropped — B.10) as a `presentation_only`
 *      diff, distinct from an `identity` diff.
 *   3. Everything `serializeCanonical` already excludes stays excluded (DB-
 *      assigned ids, timestamps, `metadata_json` — see serialize.ts's own
 *      determinism contract, reused here rather than re-implemented).
 *
 * The HASH itself is a deterministic, non-cryptographic fingerprint (FNV-1a)
 * of the normalized form — a compact identity for logs/receipts (PPR-20's
 * "answer+receipt hashes"), not a security primitive. The actual equivalence
 * DECISION is normalized-string equality; the hash is a cheap proxy for it
 * that is also useful as a stored fingerprint. This mirrors `serialize.ts`'s
 * own "pure, no I/O, no clock" discipline — no Node `crypto` import, so this
 * module stays usable from a client bundle if ever needed.
 */

import { canonicalizeValue } from './serialize'
import type { CanonicalMessage, MessagePartInput, PersistedMessagePart } from './schema'

// ---------------------------------------------------------------------------
// String normalization
// ---------------------------------------------------------------------------

/**
 * Normalize a string for semantic comparison: Unicode NFC, CRLF→LF, trim
 * trailing whitespace per line, collapse 3+ blank lines to exactly one blank
 * line (a paragraph-break formatting artifact, not content). Pure.
 */
export function normalizeText(s: string): string {
  return s
    .normalize('NFC')
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map((line) => line.replace(/[ \t]+$/, ''))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

// ---------------------------------------------------------------------------
// Part-body normalization
// ---------------------------------------------------------------------------

/** A part shape the normalizer accepts — mirrors serialize.ts's SerializablePart. */
type SerializablePart =
  | Pick<MessagePartInput, 'seq' | 'kind' | 'body' | 'model_visible'>
  | Pick<PersistedMessagePart, 'seq' | 'kind' | 'body' | 'model_visible'>

export type SemanticDiffClass = 'identity' | 'presentation_only'

/**
 * Normalize one part's body for the semantic hash. Kind-aware: a `text`/
 * `reasoning` body gets its prose whitespace-normalized; a `citation` body is
 * split into an IDENTITY sub-object (hashed) and a PRESENTATION sub-object
 * (reported in diffs, never hashed) per the module header's item 2; every
 * other kind falls back to whitespace-normalizing every string field one
 * level deep (adequate for `tool_call.args` / `attachment` /
 * `prediction_candidate`, none of which carry the citation-style dual-
 * derivation asymmetry).
 */
function normalizeBodyForHash(kind: string, body: unknown): unknown {
  if (body === null || typeof body !== 'object') return body
  const b = body as Record<string, unknown>

  if (kind === 'citation') {
    // Identity only — snippet/reader_label/grade are presentation, excluded
    // from the HASH (still visible in the full normalized object below for
    // diagnostic diffing).
    return canonicalizeValue({ index: b.index, signal_id: b.signal_id, layer: b.layer })
  }

  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(b)) {
    out[k] = typeof v === 'string' ? normalizeText(v) : v
  }
  return canonicalizeValue(out)
}

/** The full normalized body — includes presentation fields, for diagnostics
 *  (never fed to the hash; see `normalizeBodyForHash`). */
function normalizeBodyForDiagnostics(kind: string, body: unknown): unknown {
  if (body === null || typeof body !== 'object') return body
  const b = body as Record<string, unknown>
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(b)) {
    out[k] = typeof v === 'string' ? normalizeText(v) : v
  }
  return canonicalizeValue(out)
}

// ---------------------------------------------------------------------------
// Fingerprint
// ---------------------------------------------------------------------------

interface NormalizedMessageView {
  id: string
  conversation_id: string
  role: string
  schema_version: number
  model_id: string
  provider: string
}

interface NormalizedPartView {
  seq: number
  kind: string
  model_visible: boolean
  body: unknown
}

type SerializableMessage = Pick<
  CanonicalMessage,
  'id' | 'conversation_id' | 'role' | 'schema_version' | 'model_id' | 'provider'
>

/**
 * The normalized, hash-eligible form: identity fields only, whitespace-
 * normalized text, citation presentation stripped. Deterministic — same
 * logical content always normalizes to the same structure regardless of key
 * order or which of the two independent derivations produced it.
 */
export function normalizeForSemanticHash(
  message: SerializableMessage,
  parts: readonly SerializablePart[],
): { message: NormalizedMessageView; parts: NormalizedPartView[] } {
  const messageView: NormalizedMessageView = {
    id: message.id,
    conversation_id: message.conversation_id,
    role: message.role,
    schema_version: message.schema_version,
    model_id: message.model_id,
    provider: message.provider,
  }
  const partViews: NormalizedPartView[] = [...parts]
    .sort((a, b) => a.seq - b.seq)
    .map((p) => ({
      seq: p.seq,
      kind: p.kind,
      model_visible: p.model_visible,
      body: normalizeBodyForHash(p.kind, p.body),
    }))
  return canonicalizeValue({ message: messageView, parts: partViews }) as {
    message: NormalizedMessageView
    parts: NormalizedPartView[]
  }
}

/** The FULL normalized form (presentation fields included) — for diagnostics
 *  only, never for the hash. */
export function normalizeForDiagnostics(
  message: SerializableMessage,
  parts: readonly SerializablePart[],
): { message: NormalizedMessageView; parts: NormalizedPartView[] } {
  const messageView: NormalizedMessageView = {
    id: message.id,
    conversation_id: message.conversation_id,
    role: message.role,
    schema_version: message.schema_version,
    model_id: message.model_id,
    provider: message.provider,
  }
  const partViews: NormalizedPartView[] = [...parts]
    .sort((a, b) => a.seq - b.seq)
    .map((p) => ({
      seq: p.seq,
      kind: p.kind,
      model_visible: p.model_visible,
      body: normalizeBodyForDiagnostics(p.kind, p.body),
    }))
  return canonicalizeValue({ message: messageView, parts: partViews }) as {
    message: NormalizedMessageView
    parts: NormalizedPartView[]
  }
}

/**
 * FNV-1a, 32-bit, over the UTF-8 bytes of `s`, rendered as 8 lowercase hex
 * chars. Non-cryptographic by design (this is a fingerprint for equality
 * checking + log identity, not a security control — see module header).
 * Pure, dependency-free (no Node `crypto`), so `store/serialize.ts`'s
 * isomorphism discipline is preserved.
 */
export function fnv1a(s: string): string {
  let hash = 0x811c9dc5
  for (let i = 0; i < s.length; i++) {
    hash ^= s.charCodeAt(i)
    hash = Math.imul(hash, 0x01000193)
  }
  return (hash >>> 0).toString(16).padStart(8, '0')
}

/**
 * The semantic hash of a (message, parts) pair: FNV-1a of the JSON.stringify
 * of `normalizeForSemanticHash`'s output. Two logically-equivalent turns
 * (differing only in citation presentation text or incidental whitespace)
 * hash IDENTICAL; a real content divergence hashes DIFFERENT.
 */
export function computeSemanticHash(
  message: SerializableMessage,
  parts: readonly SerializablePart[],
): string {
  return fnv1a(JSON.stringify(normalizeForSemanticHash(message, parts)))
}
