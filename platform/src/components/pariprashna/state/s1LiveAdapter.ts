/**
 * Adapter: lane S-1's REAL SSE wire protocol → this renderer's `WireEvent`.
 *
 * This is the LIVE integration seam (PB-1/integrate). Unlike
 * `c2ProtocolAdapter.ts` (which maps lane C-2's recorded FIXTURE format for the
 * dev fixture-playback path), this module consumes S-1's canonical, Zod-typed
 * event union directly from `@/lib/pariprashna/protocol/events` — so the switch
 * below is exhaustively checked against S-1's real `PariprashnaEvent`
 * discriminated union. `useLiveStream` decodes each SSE frame with S-1's
 * `decodeEvent` and feeds the typed event here.
 *
 * ── Identity ─────────────────────────────────────────────────────────────────
 * The client mints its OWN `turnId` at submit time (optimistic `submitted`
 * state, §5.3) BEFORE the server's `turn.open` arrives with a server-side
 * `turn_id`. To keep the reducer's turn identity stable, this adapter stamps
 * EVERY emitted `WireEvent` with the client `turnId` passed to the factory,
 * ignoring the server `turn_id` for reducer routing (the server id is still
 * available on the raw event for persistence correlation if ever needed).
 *
 * ── Honest lossiness (documented, not silent) ────────────────────────────────
 * S-1's wire is deliberately minimal; several rich fields C-1 renders are NOT
 * on it and are SYNTHESIZED here from what the stream does carry:
 *   • block roles: S-1 block.open carries role 'prose'|'thinking'; C-1's
 *     ReadingRole ('verdict'|…) is a curation concern S-1 does not express, so
 *     role is left undefined (renders as a plain paragraph).
 *   • citation.grade: mapped from S-3's grade enum (primary|supporting|
 *     contextual|unverified) to C-1's Grade; source class defaults to
 *     'chart_factor' (S-1 carries `layer`, not a reader source-class).
 *   • turn.commit.grounding: S-1's turn.commit carries persistence metadata,
 *     NOT a grounding summary. The factor/classical COUNTS and the elapsed
 *     clock are synthesized here from the citations seen on the stream. The
 *     `gradeSummaryLabel` (the confident WELL-GROUNDED/SUPPORTED/CATALOG-ONLY
 *     chip) is derived HONESTLY from the actual distribution of per-citation
 *     grades (`CitationDefineEvent.grade`, S-3's pipeline) via
 *     `groundingRollup.rollUpGradeSummaryLabel` — it NEVER defaults to a
 *     confident verdict on the strength of a bare citation count. If the wire
 *     carries no grade for a citation, that citation resolves to `catalog`
 *     (unverified), so a stream with no real grade data rolls up to
 *     CATALOG-ONLY — UNVERIFIED, never WELL-GROUNDED.
 *   • `grade` and bare `flag` events do not drive C-1 reducer state (the reducer
 *     treats them as lastEventId-only), so they map to a `flag`/no-op; a `grade`
 *     event is dropped (returns []).
 */

import type {
  Citation,
  ClassifiedError,
  ClassifiedErrorKind,
  Grade,
  GroundingSummary,
  WireEvent,
} from './types'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import { RETRIEVAL_FACET_NAMES, type RetrievalFacetKey } from '@/lib/pariprashna/lexicon'
import { emptyGradeTally, rollUpGradeSummaryLabel, tallyGrade } from './groundingRollup'

/** S-3 citation grade enum → C-1 reader Grade. */
function mapGrade(grade: string | undefined): Grade {
  switch (grade) {
    case 'primary':
      return 'confirmed'
    case 'supporting':
      return 'supported'
    case 'contextual':
      return 'catalog'
    case 'unverified':
      return 'honest_gap'
    // Already-C-1 grades pass through (defensive; e.g. a future emitter).
    case 'confirmed':
    case 'supported':
    case 'catalog':
    case 'honest_gap':
      return grade
    default:
      return 'catalog'
  }
}

/** S-1 phase name → a reader band label (fallback to a generic verb). */
function phaseLabel(phase: string): string {
  switch (phase) {
    case 'plan':
      return 'Composing the approach'
    case 'retrieve':
      return 'Reading the whole chart'
    case 'synthesize':
      return 'Composing the reading'
    case 'finalize':
      return 'Sealing'
    default:
      return 'Consulting the chart'
  }
}

/** Resolve an activity/seam label_key through S-2's closed lexicon, else a
 *  reader-safe fallback (never a raw tool/asset id — §7.8). */
function resolveActivityLabel(labelKey: string): string {
  const facet = RETRIEVAL_FACET_NAMES[labelKey as RetrievalFacetKey]
  if (facet) return `Retrieved — ${facet}`
  const bare = labelKey.replace(/^activity\.(retrieval|reasoning)\./, '')
  const facet2 = RETRIEVAL_FACET_NAMES[bare as RetrievalFacetKey]
  if (facet2) return `Retrieved — ${facet2}`
  return 'Consulting the chart'
}

/** Classify an in-stream error code into C-1's ClassifiedError bands. */
function classifyError(code: string, message: string): ClassifiedError {
  const c = code.toLowerCase()
  let kind: ClassifiedErrorKind = 'unknown'
  if (c.includes('rate') || c.includes('429')) kind = 'rate_limit'
  else if (c.includes('overload') || c.includes('capacity') || c.includes('503')) kind = 'model_overload'
  else if (c.includes('timeout') || c.includes('deadline')) kind = 'timeout'
  else if (c.includes('network') || c.includes('fetch') || c.includes('econn')) kind = 'network'
  else if (c.includes('auth') || c.includes('401') || c.includes('403')) kind = 'auth'
  const bandLabel =
    kind === 'rate_limit'
      ? 'The model is busy — retrying'
      : kind === 'model_overload'
        ? 'The model is busy — retrying'
        : kind === 'timeout'
          ? 'Taking longer than usual…'
          : kind === 'network'
            ? 'Reconnecting…'
            : kind === 'auth'
              ? 'Please sign in again'
              : 'Something went wrong'
  return {
    kind,
    bandLabel,
    sentence: message || bandLabel,
    actions: kind === 'auth' ? ['settings'] : kind === 'model_overload' ? ['switch_model', 'retry'] : ['retry'],
  }
}

export interface S1LiveAdapter {
  /** Map one decoded S-1 event to zero or more reducer WireEvents. */
  map(ev: PariprashnaEvent): WireEvent[]
}

/**
 * Build a STATEFUL adapter bound to one client turn. Statefulness is needed to
 * synthesize `turn.commit`'s grounding summary (S-1's wire does not carry it) —
 * the adapter tallies the citations it has seen + reads the client elapsed clock.
 */
export function makeS1LiveAdapter(
  clientTurnId: string,
  userText: string,
  openedAtMs: number,
): S1LiveAdapter {
  let citationsSeen = 0
  let classicalSeen = 0
  // Real per-citation grade distribution (from CitationDefineEvent.grade) — the
  // honest basis for the grounding summary chip, never the bare citation count.
  const gradeTally = emptyGradeTally()

  const map = (ev: PariprashnaEvent): WireEvent[] => {
    const eventId = `${clientTurnId}-${ev.seq}`
    const turnId = clientTurnId

    switch (ev.type) {
      case 'turn.open':
        // Reducer no-ops (the optimistic CLIENT_SUBMIT_TURN already created the
        // turn under clientTurnId) — emitted for completeness/idempotency.
        return [{ type: 'turn.open', turnId, userText, eventId }]

      case 'phase':
        if (ev.status !== 'start') return []
        return [{ type: 'phase', turnId, label: phaseLabel(ev.phase), eventId }]

      case 'activity.upsert':
        return [
          {
            type: 'activity.upsert',
            turnId,
            row: {
              id: ev.key,
              passIndex: ev.pass_id,
              label: resolveActivityLabel(ev.label_key),
              detail: ev.detail ?? (typeof ev.count === 'number' ? String(ev.count) : undefined),
              kind: 'tool',
              status: ev.status === 'done' ? 'done' : 'running',
              ms: typeof ev.ms === 'number' ? String(ev.ms) : undefined,
            },
            eventId,
          },
        ]

      case 'block.open':
        return [{ type: 'block.open', turnId, blockId: ev.block_id, kind: 'paragraph', eventId }]

      case 'block.delta':
        return [{ type: 'block.delta', turnId, blockId: ev.block_id, textDelta: ev.delta, eventId }]

      case 'block.commit':
        return [{ type: 'block.commit', turnId, blockId: ev.block_id, kind: 'paragraph', html: ev.text, eventId }]

      case 'seam.open':
        // Real PASS-BOUNDARY seam → C-1's pass-seam UI. Synthesize a stable
        // blockId keyed on the pass so seam.set can settle the same divider.
        return [
          {
            type: 'pass.seam.open',
            turnId,
            passIndex: ev.pass_id,
            liveLabel: resolveActivityLabel(ev.label_key),
            blockId: `seam-${ev.pass_id}`,
            eventId,
          },
        ]

      case 'seam.set':
        return [{ type: 'pass.seam.settle', turnId, blockId: `seam-${ev.pass_id}`, summary: ev.summary, eventId }]

      case 'citation.define': {
        citationsSeen += 1
        const sourceClass =
          ev.layer === 'L0' || ev.layer?.toLowerCase().includes('classical')
            ? ('classical_source' as const)
            : ('chart_factor' as const)
        if (sourceClass === 'classical_source') classicalSeen += 1
        const grade = mapGrade(ev.grade)
        tallyGrade(gradeTally, grade)
        const citation: Citation = {
          n: ev.index,
          title: ev.reader_label ?? ev.snippet,
          sourceClass,
          relevance: ev.snippet,
          ref: ev.signal_id,
          grade,
        }
        return [{ type: 'citation.define', turnId, citation, eventId }]
      }

      case 'flag':
        return [{ type: 'flag', turnId, flag: ev.code, eventId }]

      case 'grade':
        // Lane P2-C: the one `grade` subject the reducer DOES act on — the
        // honest depth-received disclosure (`plan_stage.ts`). Every other
        // subject (e.g. `query_class`) is not a reducer-state driver in C-1
        // (lastEventId-only) and is dropped to keep the WireEvent stream free
        // of no-op noise.
        if (ev.subject === 'reading_depth_received') {
          return [{ type: 'reading_depth.received', turnId, depth: ev.grade, eventId }]
        }
        return []

      case 'turn.commit': {
        const elapsedSeconds = Math.max(0, Math.floor((Date.now() - openedAtMs) / 1000))
        const factorCount = citationsSeen - classicalSeen
        const grounding: GroundingSummary = {
          factorCount: Math.max(0, factorCount),
          classicalCount: classicalSeen,
          elapsedLabel: `0:${String(elapsedSeconds).padStart(2, '0')}`,
          // HONEST rollup from the real per-citation grade distribution — never a
          // confident verdict on the strength of a bare count (B.1/B.10, §6.7).
          gradeSummaryLabel: rollUpGradeSummaryLabel(gradeTally),
        }
        return [{ type: 'turn.commit', turnId, grounding, eventId }]
      }

      case 'turn.close':
        return [{ type: 'turn.close', turnId, eventId }]

      case 'error':
        return [{ type: 'error', turnId, error: classifyError(ev.code, ev.message), eventId }]

      case 'snapshot.apply': {
        // PB-2/M-5: the reconnect path's gap-fallback. Citations arrive as a
        // flat array (no per-citation grade on this event by design — the
        // snapshot is a coarse "here's the current state" catch-up, not a
        // re-run of the fine-grained citation pipeline), so they round-trip
        // through the SAME grade mapping as a live citation.define with no
        // grade carried (→ 'catalog', never a fabricated confident grade).
        const citations = ev.citations.map((c) => ({
          n: c.index,
          title: c.snippet,
          sourceClass: (c.layer === 'L0' || c.layer?.toLowerCase().includes('classical')
            ? 'classical_source'
            : 'chart_factor') as Citation['sourceClass'],
          relevance: c.snippet,
          ref: c.signal_id,
          grade: mapGrade(undefined),
        }))
        return [
          {
            type: 'snapshot.apply',
            turnId,
            text: ev.text,
            citations,
            turnStatus: ev.turn_status,
            eventId,
          },
        ]
      }

      default: {
        // Exhaustiveness guard against S-1's real union — a new event type S-1
        // adds will surface here at compile time.
        const _never: never = ev
        void _never
        return []
      }
    }
  }

  return { map }
}
