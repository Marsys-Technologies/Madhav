/**
 * pariprashna/citations/protocol_adapter.ts — PB-1 lane S-3.
 *
 * Maps this lane's RICH INTERNAL citation events (see ./types.ts) onto lane
 * S-1's shared SSE wire vocabulary (`platform/src/lib/pariprashna/protocol/
 * events.ts`, the single source of truth for the Paripraśna wire format).
 *
 * ── Why an adapter and not a direct import ───────────────────────────────────
 * S-1's `protocol/events.ts` lives on a SIBLING branch/worktree that is not yet
 * merged into `pb/1/s3`, so it cannot be imported at build time here. This file
 * therefore MIRRORS the exact field shapes of the three S-1 events this lane
 * emits (`citation.define`, `flag`, `grade`) as local interfaces. POST-MERGE
 * ACTION: delete the mirror below and re-type `toWireEvents` against S-1's
 * `PariprashnaEvent` directly.
 *
 * ── Why the internal shape differs (the S-1 reconciliation ask) ──────────────
 * The S-3 brief mandates a citation carry { n, reader_label, grade,
 * audit_detail }. S-1's `citation.define` is { index, signal_id, layer, snippet }
 * — it has no slot for a reader label, a grade, or an audit detail. Rather than
 * lose that data (it is the whole point of this lane: reader-label vs internal-id
 * separation, plus grading), the mapping is:
 *
 *   internal citation.define ─┬─→ S-1 citation.define
 *                             │     { index:n, signal_id:ref, layer, snippet:reader_label }
 *                             └─→ S-1 grade
 *                                   { subject:`citation:${n}`, grade, detail:audit_detail }
 *
 *   internal flag(malformed_sentinel)  → S-1 flag { code:'malformed_sentinel', level:'warn', detail:reason }
 *   internal flag(normalization)       → S-1 flag { code:'citation_normalization', level:'info', detail:note }
 *   internal flag(register_leak)       → S-1 flag { code:`register_leak:${verdict}`, level, detail }
 *
 * RECONCILIATION ASK FOR S-1: extend `citation.define` with optional
 * `reader_label` + `grade` (so the split-mapping to a `grade` event is not
 * required), OR bless the `grade{subject:'citation:N'}` convention above.
 *
 * ── Wire-safety invariant (load-bearing) ─────────────────────────────────────
 * Every string this adapter places on a client-visible wire field is either (a)
 * an already-clean value (reader_label, a pattern name, a normalization note, a
 * grade enum), or (b) run through `lintReaderProse` first. Specifically:
 *   • A register_leak flag's `original` (the LEAKED INTERNAL TOKEN) is NEVER
 *     emitted — only the pattern name + verdict (+ the clean reader label on a
 *     rewrite) go on the wire.
 *   • A citation's `audit_detail` DOES contain table/fact-id internals (e.g.
 *     "resolved from bodha_msr_signals where signal_id='SIG.MSR.413'"), so it is
 *     passed through `lintReaderProse` before it can reach `grade.detail`.
 * See protocol_adapter.test.ts for both proofs.
 */

import { lintReaderProse } from './register_leak_lint'
import type { PariprashnaCitationEvent } from './types'

// ── Local MIRROR of lane S-1 wire shapes (delete post-merge) ────────────────

interface S1Envelope {
  seq: number
  t: number
}

export interface S1CitationDefineWire extends S1Envelope {
  type: 'citation.define'
  index: number
  signal_id: string
  layer: string
  snippet: string
}

export interface S1FlagWire extends S1Envelope {
  type: 'flag'
  code: string
  level: 'info' | 'warn' | 'error'
  detail?: string
}

export interface S1GradeWire extends S1Envelope {
  type: 'grade'
  subject: string
  grade: string
  detail?: string
}

export type S1WireEvent = S1CitationDefineWire | S1FlagWire | S1GradeWire

export interface WireEnvelopeSource {
  /** Allocate the next monotonic per-turn sequence number. */
  nextSeq: () => number
  /** Emission timestamp (epoch ms) for this batch. */
  t: number
}

/** Default layer tag for a Paripraśna citation on the S-1 wire. */
const DEFAULT_CITATION_LAYER = 'L2.5'

/**
 * Map ONE internal citation event to zero or more S-1 wire events.
 * Pure + isomorphic (no Node/stream surface), mirroring S-1's own discipline.
 */
export function toWireEvents(
  event: PariprashnaCitationEvent,
  env: WireEnvelopeSource,
): S1WireEvent[] {
  switch (event.type) {
    case 'citation.define': {
      const define: S1CitationDefineWire = {
        type: 'citation.define',
        seq: env.nextSeq(),
        t: env.t,
        index: event.n,
        signal_id: event.ref,
        layer: DEFAULT_CITATION_LAYER,
        snippet: event.reader_label, // reader-safe label, never the raw id
      }
      // audit_detail carries table/fact-id internals — scrub before the wire.
      const grade: S1GradeWire = {
        type: 'grade',
        seq: env.nextSeq(),
        t: env.t,
        subject: `citation:${event.n}`,
        grade: event.grade,
        detail: lintReaderProse(event.audit_detail).clean,
      }
      return [define, grade]
    }

    case 'flag': {
      if (event.flag === 'malformed_sentinel') {
        return [
          {
            type: 'flag',
            seq: env.nextSeq(),
            t: env.t,
            code: 'malformed_sentinel',
            level: 'warn',
            detail: event.reason,
          },
        ]
      }
      if (event.flag === 'normalization') {
        return [
          {
            type: 'flag',
            seq: env.nextSeq(),
            t: env.t,
            code: 'citation_normalization',
            level: 'info',
            detail: event.note,
          },
        ]
      }
      // register_leak — WIRE-SAFE: never emit `original` (the leaked token).
      const level: S1FlagWire['level'] = event.verdict === 'redact' ? 'warn' : 'info'
      const detail =
        event.verdict === 'rewrite' && event.replacement
          ? `${event.pattern}→${event.replacement}` // replacement is a clean label
          : event.pattern
      return [
        {
          type: 'flag',
          seq: env.nextSeq(),
          t: env.t,
          code: `register_leak:${event.verdict}`,
          level,
          detail,
        },
      ]
    }
  }
}

/** Map a batch of internal events to a flat S-1 wire sequence. */
export function toWireBatch(
  events: PariprashnaCitationEvent[],
  env: WireEnvelopeSource,
): S1WireEvent[] {
  return events.flatMap((e) => toWireEvents(e, env))
}
