/**
 * pariprashna/citations/types.ts — PB-1 (DHĀRĀ) lane S-3.
 *
 * Shared types + protocol event shapes for the Paripraśna citation pipeline.
 *
 * ── Protocol-schema alignment note (for lane S-1) ────────────────────────────
 * These are this lane's RICH INTERNAL event shapes. They intentionally carry
 * MORE than lane S-1's wire schema (`platform/src/lib/pariprashna/protocol/
 * events.ts`) expresses: a reader_label, a grade, audit_detail, and structured
 * lint verdicts — the substance of the S-3 brief (reader-label vs internal-id
 * separation + grading + leak backstop).
 *
 * S-1's wire `citation.define` is { index, signal_id, layer, snippet } and its
 * `flag` is { code, level, detail } — neither can hold this lane's fields. So
 * these internal events are NOT emitted to the wire directly; `protocol_adapter
 * .ts` maps them onto S-1's vocabulary (citation.define + grade + flag) and
 * scrubs internal tokens from the client-visible channel. The adapter carries
 * the full reconciliation ask for S-1 (extend citation.define with
 * reader_label + grade). CITATION_EVENT_CONTRACT_VERSION below tracks the
 * INTERNAL shape; bump on any change.
 */

import { z } from 'zod'

/** Bump on ANY change to the on-the-wire event shapes below. S-1 reads this. */
export const CITATION_EVENT_CONTRACT_VERSION = '0.2.0-s3'

// ── Citation grade ───────────────────────────────────────────────────────────
// The verification tier a resolved reference carries. `unverified` is the
// terminal grade for a sentinel that has no matching source (the hallucination
// case) — it is still surfaced (B.10: never silently drop), but flagged.
export const CitationGradeSchema = z.enum([
  'primary', // directly grounded in an L1 fact / firings-authoritative signal
  'supporting', // corroborating / secondary
  'contextual', // background, low-weight
  'unverified', // sentinel present, NO matching source found → hallucination
])
export type CitationGrade = z.infer<typeof CitationGradeSchema>

// ── Resolved citation ────────────────────────────────────────────────────────
// What a resolver returns for a well-formed sentinel reference. The
// `reader_label` is the ONLY citation string ever shown to the reader; `ref`
// and `audit_detail` are audit-channel only and must never reach reader prose.
export interface ResolvedCitation {
  /** The normalized reference token as it appeared in the sentinel. */
  ref: string
  /** Human, reader-facing label. Never an internal id. */
  reader_label: string
  /** Verification grade. */
  grade: CitationGrade
  /** Audit-channel detail (source table, fact ids, etc.). NOT reader-facing. */
  audit_detail: string
}

// ── Resolver interface ───────────────────────────────────────────────────────
// Supplied by the caller (the stream route). Decoupling the resolver keeps this
// module deterministically unit-testable with fixture resolvers.
export interface CitationResolver {
  /**
   * Resolve a sentinel reference to a citation, or null if no source matches.
   * A null return drives the `unverified` grade + hallucination-counter path.
   */
  resolve(ref: string): ResolvedCitation | null
  /**
   * For the register-leak lint's REWRITE verdict: given an id-shaped token that
   * leaked into prose, return its reader-facing label, or null if none exists
   * (→ the lint falls through to REDACT+FLAG).
   */
  readerLabel(idToken: string): string | null
}

// ── Protocol events (see S-1 alignment note above) ───────────────────────────

export const CitationDefineEventSchema = z.object({
  type: z.literal('citation.define'),
  /** Stable 1-based citation number; repeated refs reuse the same n. */
  n: z.number().int().positive(),
  /** Reader-facing label (safe to render). */
  reader_label: z.string(),
  grade: CitationGradeSchema,
  /** Audit-channel detail — client renders in audit view only, never inline. */
  audit_detail: z.string(),
  /** Normalized reference token (audit channel). */
  ref: z.string(),
  /**
   * Optional source-layer tag for the citation (e.g. 'L2.5', 'L1'). When a
   * resolver knows the true layer a citation is grounded in, it sets this and
   * `protocol_adapter.ts` forwards it onto the S-1 `citation.define.layer`
   * field; absent it, the adapter applies its documented default. Optional so
   * existing resolvers/fixtures stay valid.
   */
  layer: z.string().optional(),
})
export type CitationDefineEvent = z.infer<typeof CitationDefineEventSchema>

export const MalformedSentinelReasonSchema = z.enum([
  'byte_limit', // held bytes exceeded MAX_HOLDBACK without a close
  'timeout', // TIMEOUT ms elapsed while holding without a close
  'eof_unclosed', // stream ended mid-sentinel
])
export type MalformedSentinelReason = z.infer<typeof MalformedSentinelReasonSchema>

export const MalformedSentinelFlagSchema = z.object({
  type: z.literal('flag'),
  flag: z.literal('malformed_sentinel'),
  reason: MalformedSentinelReasonSchema,
  /** The held bytes that were flushed as plain text (already lint-cleaned). */
  raw: z.string(),
})
export type MalformedSentinelFlag = z.infer<typeof MalformedSentinelFlagSchema>

export const NormalizationFlagSchema = z.object({
  type: z.literal('flag'),
  flag: z.literal('normalization'),
  original: z.string(),
  normalized: z.string(),
  note: z.string(),
})
export type NormalizationFlag = z.infer<typeof NormalizationFlagSchema>

export const RegisterLeakVerdictSchema = z.enum(['rewrite', 'redact', 'telemetry'])
export type RegisterLeakVerdict = z.infer<typeof RegisterLeakVerdictSchema>

export const RegisterLeakFlagSchema = z.object({
  type: z.literal('flag'),
  flag: z.literal('register_leak'),
  verdict: RegisterLeakVerdictSchema,
  /** Which lint pattern class fired (e.g. 'signal_id', 'register_acronym'). */
  pattern: z.string(),
  /** The offending token (audit channel — this is the thing that must NOT ship). */
  original: z.string(),
  /** For REWRITE: the reader label it was replaced with. */
  replacement: z.string().optional(),
})
export type RegisterLeakFlag = z.infer<typeof RegisterLeakFlagSchema>

export const PariprashnaCitationEventSchema = z.discriminatedUnion('type', [
  CitationDefineEventSchema,
  MalformedSentinelFlagSchema,
  NormalizationFlagSchema,
  RegisterLeakFlagSchema,
])
export type PariprashnaCitationEvent = z.infer<typeof PariprashnaCitationEventSchema>

/** The unit a rewriter step returns: safe-to-emit prose + any protocol events. */
export interface RewriteChunk {
  /** Lint-cleaned text safe to write to the wire. May be ''. */
  text: string
  /** Protocol events to forward to the client stream. */
  events: PariprashnaCitationEvent[]
}
