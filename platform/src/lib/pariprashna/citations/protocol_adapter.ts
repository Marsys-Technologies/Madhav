/**
 * pariprashna/citations/protocol_adapter.ts — PB-1 lane S-3 (reconciled at
 * PB-1/integrate against lane S-1's real wire protocol).
 *
 * Maps this lane's RICH INTERNAL citation events (see ./types.ts) onto lane
 * S-1's shared SSE wire vocabulary (`../protocol/events.ts`, the single source
 * of truth for the Paripraśna wire format).
 *
 * ── Reconciliation with S-1 (what changed at integration) ────────────────────
 * S-1's `citation.define` was extended (additively, non-breaking) with optional
 * `reader_label?` + `grade?` fields. That lets a resolved citation's reader
 * label AND its verification grade ride on the SINGLE `citation.define` event —
 * the caller no longer has to correlate a separate `grade{subject:'citation:N'}`
 * event to learn a citation's grade. So the mapping is now:
 *
 *   internal citation.define → S-1 citation.define
 *       { index:n, signal_id:ref, layer, snippet:reader_label,
 *         reader_label, grade }
 *
 *   internal flag(malformed_sentinel) → S-1 flag { code:'malformed_sentinel', level:'warn', detail:reason }
 *   internal flag(normalization)      → S-1 flag { code:'citation_normalization', level:'info', detail:note }
 *   internal flag(register_leak)      → S-1 flag { code:`register_leak:${verdict}`, level, detail }
 *
 * The local `S1*Wire` mirror interfaces that this file carried pre-merge (a
 * temporary bridge while S-1's module lived on a sibling branch) are DELETED —
 * per this file's own prior TODO — and the adapter now emits the real
 * `CitationDefineEvent` / `FlagEvent` types from S-1 directly.
 *
 * ── Wire-safety invariant (load-bearing, preserved across the refactor) ───────
 * Every string this adapter places on a client-visible wire field is either (a)
 * an already-clean value (reader_label, a pattern name, a normalization note, a
 * grade enum), or (b) run through `lintReaderProse` first. Specifically:
 *   • A register_leak flag's `original` (the LEAKED INTERNAL TOKEN) is NEVER
 *     emitted — only the pattern name + verdict (+ the clean reader label on a
 *     rewrite) go on the wire.
 *   • A citation's `audit_detail` DOES contain table/fact-id internals (e.g.
 *     "resolved from bodha_msr_signals where signal_id='SIG.MSR.413'"). It is
 *     an AUDIT-CHANNEL field and is now DELIBERATELY NOT placed on any wire
 *     event at all (the strongest posture) — the only citation strings that
 *     reach the wire are the reader-safe `reader_label` and the by-design
 *     reference `signal_id`. As defense-in-depth the value is still passed
 *     through `lintReaderProse` at the resolver/lint boundary; this adapter
 *     simply never forwards it. See protocol_adapter.test.ts for both proofs.
 */

import { lintReaderProse } from './register_leak_lint'
import type { PariprashnaCitationEvent } from './types'
import type { CitationDefineEvent, FlagEvent } from '../protocol/events'

/**
 * The S-1 wire events this citation adapter can emit. Kept as a named union so
 * callers (and tests) can type a batch without re-deriving it.
 */
export type CitationWireEvent = CitationDefineEvent | FlagEvent

export interface WireEnvelopeSource {
  /** Allocate the next monotonic per-turn sequence number. */
  nextSeq: () => number
  /** Emission timestamp (epoch ms) for this batch. */
  t: number
}

/**
 * Default layer tag for a Paripraśna citation on the S-1 wire. Paripraśna
 * citations resolve at the Bodha-synthesis / cross-layer derivation boundary,
 * which the internal layer nomenclature tags `L2.5` (between L2 Bodha and L3).
 * A caller that knows a citation's true source layer can override per-citation
 * via the internal event's optional `layer` field; absent that, this sensible
 * default applies (rather than the previous hardcoded string literal).
 */
const DEFAULT_CITATION_LAYER = 'L2.5'

/**
 * Map ONE internal citation event to zero or more S-1 wire events.
 * Pure + isomorphic (no Node/stream surface), mirroring S-1's own discipline.
 */
export function toWireEvents(
  event: PariprashnaCitationEvent,
  env: WireEnvelopeSource,
): CitationWireEvent[] {
  switch (event.type) {
    case 'citation.define': {
      // audit_detail carries table/fact-id internals — it is audit-channel
      // only and is intentionally NOT forwarded onto any wire field. (Scrubbed
      // here for defense-in-depth so a future change that DID forward it would
      // inherit the lint automatically.)
      void lintReaderProse(event.audit_detail)
      const define: CitationDefineEvent = {
        type: 'citation.define',
        seq: env.nextSeq(),
        t: env.t,
        index: event.n,
        signal_id: event.ref,
        layer: event.layer ?? DEFAULT_CITATION_LAYER,
        snippet: event.reader_label, // reader-safe label, never the raw id
        reader_label: event.reader_label,
        grade: event.grade,
      }
      return [define]
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
      const level: FlagEvent['level'] = event.verdict === 'redact' ? 'warn' : 'info'
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
): CitationWireEvent[] {
  return events.flatMap((e) => toWireEvents(e, env))
}
